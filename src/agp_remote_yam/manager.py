"""One controller/session and one coding workspace per website run."""
from dataclasses import dataclass
import hashlib
import json
from pathlib import Path
import threading
import time
from .dependency import runner_root
from .storage import RunStore, Journal
from .runtime import AgentRuntime


@dataclass
class Settings:
    data: Path
    origin: str = "https://yam-session-api.n5hthc3gj4cqy.us-east-1.cs.amazonlightsail.com"
    robot_id: str = "yam-1"
    model: str = "gpt-6-astra"
    agent_mode: str = "codex"
    demo: bool = False
    mock_robot: bool = False
    camera_source: str = "api"
    codex: str = "codex"

    @property
    def offline(self):
        return self.demo or self.mock_robot


class RunManager:
    def __init__(self, settings):
        runner_root()
        self.settings = settings
        self.store = RunStore(Path(settings.data) / "runs")
        self.lock = threading.RLock()
        self.active = {}
        # A server restart never resumes a lease or replays motion automatically.
        for run in self.store.list():
            if run["status"] in ("preparing", "queued", "running"):
                self.store.update(self.store.directory(run["id"]), status="interrupted",
                                  error="Server restarted; inspect the robot before a new run")

    def owned(self, identity, owner):
        directory = self.store.directory(identity)
        metadata = json.loads((directory / "run.json").read_text())
        if metadata.get("owner") != owner:
            raise PermissionError("This run belongs to another browser session")
        return directory

    def start(self, task, owner, *, duration=300, parent=None, goal=None):
        if not isinstance(task, str) or not 1 <= len(task.strip()) <= 4000:
            raise ValueError("Enter a task of 1–4,000 characters")
        if type(duration) is not int or not 60 <= duration <= 600:
            raise ValueError("Run duration must be 60–600 seconds")
        with self.lock:
            if any(value["owner"] == owner for value in self.active.values()):
                raise ValueError("This browser already has an active run")
            if parent:
                self.owned(parent, owner)
            metadata, directory = self.store.create(task.strip(), parent=parent)
            journal = Journal(directory)
            runtime = AgentRuntime(directory, journal, model=self.settings.model,
                mode="demo" if self.settings.demo else self.settings.agent_mode,
                timeout_s=duration, executable=self.settings.codex)
            self.store.update(directory, owner=owner, mode="offline_mock" if self.settings.offline else "physical_api",
                              duration_s=duration)
            try:
                runtime.check_available()
            except Exception as exc:
                self.store.update(directory, status="failed", error=str(exc), ended_at=time.time())
                raise
            if goal:
                (directory / "workspace/goal/reference.png").write_bytes(goal)
            context = dict(owner=owner, runtime=runtime, journal=journal, directory=directory,
                           controller=None, stopped=threading.Event())
            self.active[metadata["id"]] = context
            threading.Thread(target=self._run, args=(context, task.strip(), duration),
                             name="agp-run-" + metadata["id"][:8], daemon=True).start()
            return metadata["id"]

    def _run(self, context, task, duration):
        from remote_yam.controller import RunnerController
        from remote_yam.session import HttpSessionAPI
        from .policy import AgPPolicy
        from .backend import ApiBackend
        from .mock import MockBackend, MockStation
        directory, runtime, journal = context["directory"], context["runtime"], context["journal"]
        try:
            api = MockStation() if self.settings.offline else HttpSessionAPI(
                self.settings.origin, robot_id=self.settings.robot_id, supports_trajectories=True)
            controller = RunnerController(api, robot_id=self.settings.robot_id,
                recording_root=directory / "recording", submit_attempts=1)
            context["controller"] = controller
            if context["stopped"].is_set():
                return
            factory = (lambda policy: MockBackend(directory / "workspace", policy, journal)) if self.settings.offline else (
                lambda policy: ApiBackend(self.settings.origin, self.settings.robot_id,
                                          directory / "workspace", policy, journal))
            policy = AgPPolicy(runtime, factory, journal)
            journal.add("lifecycle", "Joining the mock queue" if self.settings.offline else "Joining the public robot queue")
            controller.update_monitor_observation(api.get_robot_observation(self.settings.robot_id))
            controller.join_and_run(policy, task, run_duration_s=duration)
            if context["stopped"].is_set():
                controller.stop("user_requested")
            previous = None
            # Pinned RunnerController exposes its lifecycle worker, rather than
            # the HostedRunner visitor wrapper's busy() convenience method.
            while controller._worker is not None and controller._worker.is_alive():
                status = controller.status()
                current = status["status"]
                if current != previous:
                    self.store.update(directory, status=current)
                    journal.add("lifecycle", "Robot session " + current)
                    previous = current
                context["stopped"].wait(.1)
            status = controller.status()
            self.store.update(directory, status="stopped" if context["stopped"].is_set() else status["status"],
                outcome=runtime.outcome, error=status.get("error"), ended_at=time.time())
        except Exception as exc:
            journal.add("error", "Run failed", detail=str(exc))
            self.store.update(directory, status="failed", error=str(exc), ended_at=time.time())
        finally:
            controller = context.get("controller")
            if controller is not None and controller.status()["status"] in ("queued", "preparing", "running"):
                try:
                    controller.stop("agent_ended")
                except Exception as exc:
                    journal.add("error", "Robot Stop could not be confirmed", error_type=type(exc).__name__)
            try:
                runtime.cancel()
                self.store.save_experience(directory)
            except Exception as exc:
                journal.add("error", "Run cleanup failed", error_type=type(exc).__name__)
            finally:
                with self.lock:
                    self.active.pop(directory.name, None)

    def stop(self, identity, owner):
        self.owned(identity, owner)
        with self.lock:
            context = self.active.get(identity)
        if context:
            context["stopped"].set()
            try:
                if context["controller"]:
                    # Revoke the robot lease before killing/waiting for the agent.
                    context["controller"].stop("user_requested")
            finally:
                context["runtime"].cancel()

    def detail(self, identity, owner, cursor=-1):
        directory = self.owned(identity, owner)
        value = json.loads((directory / "run.json").read_text())
        value.pop("owner", None)
        with self.lock:
            context = self.active.get(identity)
        if context:
            events = context["journal"].after(cursor)
        else:
            path = directory / "events.jsonl"
            rows = [json.loads(line) for line in path.read_text().splitlines()] if path.exists() else []
            events = rows[max(0, cursor + 1):]
        value["events"] = events
        value["files"] = sorted([str(path.relative_to(directory / "workspace"))
                          for path in (directory / "workspace").rglob("*")
                          if path.is_file() and not path.is_symlink() and path.suffix in (".png", ".py", ".md", ".json", ".npy", ".npz")])
        return value

    def close(self):
        with self.lock:
            active = list(self.active.items())
        for identity, context in active:
            self.stop(identity, context["owner"])

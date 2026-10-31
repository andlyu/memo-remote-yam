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
from .identity import APPROACH, runner_identity, run_timing, measured_timing
from .recording import RunRecording, replay_info

ROBOTS = {"yam-1": "YAM-1", "robot-ba8413962083809c": "RoboHouse YAM"}


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
    memory_encoder: str = "lexical"
    memo_site: bool = False

    @property
    def offline(self):
        return self.demo or self.mock_robot


class RunManager:
    def __init__(self, settings):
        runner_root()
        self.settings = settings
        if settings.agent_mode == "remote":
            # Import model/transport libraries once at service startup rather
            # than charging the first visitor for cold Python imports.
            from remote_yam.controller import RunnerController
            from .backend import ApiBackend
            from .policy import AgPPolicy
            from remote_yam import mujoco_ik
        self.store = RunStore(Path(settings.data) / "runs")
        self.skillbook = None
        if settings.memo_site:
            from .memo import Skillbook
            self.skillbook = Skillbook(Path(settings.data) / "skillbook.sqlite3", settings.memory_encoder)
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
        if not self.settings.memo_site and (metadata.get("approach") != APPROACH or metadata.get("memo_enabled")):
            raise FileNotFoundError("This record belongs to the separate legacy application")
        return directory

    def start(self, task, owner, *, duration=300, parent=None, goal=None, memo=False, memory_version=None,
              runner=None, timing=None, robot_id=None):
        robot_id = robot_id or self.settings.robot_id
        if robot_id not in {self.settings.robot_id, *ROBOTS}:
            raise ValueError("Choose a configured YAM station")
        if not isinstance(task, str) or not 1 <= len(task.strip()) <= 4000:
            raise ValueError("Enter a task of 1–4,000 characters")
        if type(duration) is not int or not 60 <= duration <= 600:
            raise ValueError("Run duration must be 60–600 seconds")
        if type(memo) is not bool:
            raise ValueError("MEMO must be on or off")
        if not self.settings.memo_site and (memo or memory_version is not None):
            raise ValueError("This website runs Agent as Policy only. MEMO belongs on its separate website.")
        runner = runner_identity(runner, automated_default=True)
        timing = run_timing(timing)
        if parent:
            self.owned(parent, owner)
        if memory_version is not None and (type(memory_version) is not int or not 0 <= memory_version <= self.skillbook.version()):
            raise ValueError("Invalid memory version")
        with self.lock:
            if any(value["owner"] == owner for value in self.active.values()):
                raise ValueError("This browser already has an active run")
            if parent:
                self.owned(parent, owner)
            metadata, directory = self.store.create(task.strip(), parent=parent, with_memo=self.settings.memo_site)
            journal = Journal(directory)
            runtime = AgentRuntime(directory, journal, model=self.settings.model,
                mode="demo" if self.settings.demo else self.settings.agent_mode,
                timeout_s=duration, executable=self.settings.codex)
            memory = None
            if self.settings.memo_site:
                from .memo import MemoryChannel
                memory = MemoryChannel(self.skillbook, owner, directory, journal, enabled=memo, version=memory_version)
            runtime.memory = memory
            self.store.update(directory, owner=owner, mode="offline_mock" if self.settings.offline else "physical_api",
                              duration_s=duration, approach="Agent as Policy + MEMO" if memo else APPROACH,
                              runner=runner, timing=timing,
                              robot_id=robot_id,
                              **(dict(memo_enabled=memo, memory_version=memory.version) if memory else {}))
            journal.add("run_requested", "Agent as Policy run requested", approach="Agent as Policy + MEMO" if memo else APPROACH,
                        runner=runner, physical=not self.settings.offline, timing=timing)
            try:
                runtime.check_available()
            except Exception as exc:
                self.store.update(directory, status="failed", error=str(exc), ended_at=time.time())
                raise
            if goal:
                (directory / "workspace/goal/reference.png").write_bytes(goal)
            context = dict(owner=owner, runtime=runtime, journal=journal, directory=directory,
                           controller=None, stopped=threading.Event(), memory=memory, runner=runner, robot_id=robot_id)
            self.active[metadata["id"]] = context
            threading.Thread(target=self._run, args=(context, task.strip(), duration),
                             name="agp-run-" + metadata["id"][:8], daemon=True).start()
            return metadata["id"]

    def _run(self, context, task, duration):
        from remote_yam.controller import RunnerController
        from .session import AttributedSessionAPI
        from .policy import AgPPolicy
        from .backend import ApiBackend
        from .mock import MockBackend, MockStation
        directory, runtime, journal = context["directory"], context["runtime"], context["journal"]
        robot_id = context["robot_id"]
        recording = RunRecording(directory, robot_id, physical=not self.settings.offline)
        try:
            runtime.prepare(task)
            recording.start()
            api = MockStation() if self.settings.offline else AttributedSessionAPI(
                self.settings.origin, robot_id=robot_id, supports_trajectories=True,
                runner=context["runner"])
            controller = RunnerController(api, robot_id=robot_id,
                recording_root=directory / "recording", submit_attempts=1)
            context["controller"] = controller
            if context["stopped"].is_set():
                return
            create_backend = (lambda policy: MockBackend(directory / "workspace", policy, journal)) if self.settings.offline else (
                lambda policy: ApiBackend(self.settings.origin, robot_id,
                                          directory / "workspace", policy, journal))
            backend, backend_lock = None, threading.Lock()
            def factory(policy):
                nonlocal backend
                with backend_lock:
                    if backend is None:
                        backend = create_backend(policy)
                    return backend
            policy = AgPPolicy(runtime, factory, journal)
            policy.physical = not self.settings.offline
            journal.add("lifecycle", "Joining the mock queue" if self.settings.offline else "Joining the public robot queue")
            monitor = api.get_robot_observation(robot_id)
            controller.update_monitor_observation(monitor)
            controller.join_and_run(policy, task, run_duration_s=duration)
            if runtime.mode == "remote":
                def prepare_backend():
                    try:
                        factory(policy)
                    except Exception as exc:
                        journal.add("worker", "Robot calibration preparation failed", error_type=type(exc).__name__)
                threading.Thread(target=prepare_backend, name="agp-calibration", daemon=True).start()
                def prime():
                    try:
                        from .observation import ScenePreview
                        preview = factory(policy) if self.settings.offline else ScenePreview(
                            self.settings.origin, robot_id, directory / "workspace", policy, journal)
                        runtime.prime(preview, monitor.get("observation", monitor.get("payload", monitor)))
                    except Exception as exc:
                        # Failed read-only priming is not replaced by stale or
                        # synthetic data. The leased startup can still report it.
                        journal.add("worker", "Read-only pre-admission observations unavailable",
                                    error_type=type(exc).__name__)
                threading.Thread(target=prime, name="agp-initial-scene", daemon=True).start()
            if context["stopped"].is_set():
                controller.stop("user_requested")
            previous = None
            # Pinned RunnerController exposes its lifecycle worker, rather than
            # the HostedRunner visitor wrapper's busy() convenience method.
            while controller._worker is not None and controller._worker.is_alive():
                if runtime.finished.is_set() and not policy._started:
                    controller.stop("agent_preparation_failed")
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
                try:
                    runtime.cancel()
                    self.store.save_experience(directory)
                finally:
                    recording.finish()
                metadata = json.loads((directory / "run.json").read_text())
                timing = metadata["timing"]
                first = next((e for e in journal.after() if e["kind"] == "physical_motion_measured"), None)
                if first:
                    timing = measured_timing(timing, first)
                else:
                    timing["outcome"] = "not_physical" if self.settings.offline else "no_measured_motion"
                self.store.update(directory, timing=timing, replay=replay_info(directory))
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

    def correct(self, identity, owner, content, request_id):
        self.owned(identity, owner)
        with self.lock:
            context = self.active.get(identity)
            if not context or context["stopped"].is_set() or context["runtime"].finished.is_set():
                raise ValueError("Select a running task to send a correction")
            return context["memory"].correct(content, request_id)

    def detail(self, identity, owner, cursor=-1):
        directory = self.owned(identity, owner)
        value = json.loads((directory / "run.json").read_text())
        value.pop("owner", None)
        with self.lock:
            context = self.active.get(identity)
        if context:
            events = context["journal"].after(cursor)
            first = next((e for e in context["journal"].after() if e["kind"] == "physical_motion_measured"), None)
            if first:
                value["timing"] = measured_timing(value["timing"], first)
        else:
            path = directory / "events.jsonl"
            rows = [json.loads(line) for line in path.read_text().splitlines()] if path.exists() else []
            events = rows[max(0, cursor + 1):]
        value["events"] = events
        value["active"] = context is not None
        value["replay"] = replay_info(directory)
        if self.skillbook:
            value["corrections"] = self.skillbook.corrections(owner, identity)
        value["files"] = sorted([str(path.relative_to(directory / "workspace"))
                          for path in (directory / "workspace").rglob("*")
                          if path.is_file() and not path.is_symlink() and path.suffix in (".jpg", ".png", ".py", ".md", ".json", ".npy", ".npz")])
        return value

    def close(self):
        with self.lock:
            active = list(self.active.items())
        for identity, context in active:
            self.stop(identity, context["owner"])

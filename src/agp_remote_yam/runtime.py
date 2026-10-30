"""A real Codex process owns runtime programming, observations and recovery.

CLI/event contract: https://learn.chatgpt.com/docs/non-interactive-mode
Local mode reuses the operator's normal login; Docker mode mounts only this
run's workspace and is the supported boundary for untrusted public prompts.
"""
import json
import os
from pathlib import Path
import shutil
import signal
import subprocess
import sys
import threading
import time
from .bridge import FileBridge
from .workspace import Workspace

RESULT_SCHEMA = dict(type="object", additionalProperties=False, properties=dict(
    status=dict(type="string", enum=["continue", "done", "give_up"]), summary=dict(type="string"),
    evidence=dict(type="array", items=dict(type="string"))), required=["status", "summary", "evidence"])


class AgentRuntime:
    def __init__(self, directory, journal, *, model="gpt-6-astra", mode="codex", timeout_s=600,
                 executable="codex", image="agp-codex:0.157.0"):
        self.directory = Path(directory)
        self.workspace = self.directory / "workspace"
        self.journal, self.model, self.mode = journal, model, mode
        self.timeout_s, self.executable, self.image = timeout_s, executable, image
        self.stopped, self.finished = threading.Event(), threading.Event()
        self.state, self.outcome = "waiting_for_robot", None
        self.process = None
        self.memory = None
        self.maintenance = False
        self._lock = threading.RLock()
        self.container = "agp-" + self.directory.name

    def check_available(self):
        binary = {"docker": "docker", "remote": "podman"}.get(self.mode, self.executable)
        if self.mode != "demo" and not shutil.which(binary):
            raise RuntimeError(f"{binary} is not installed")
        if self.mode == "docker" and not os.environ.get("CODEX_API_KEY"):
            raise RuntimeError("Docker agent requires the server's CODEX_API_KEY; local mode uses your normal Codex login")

    def command(self):
        if self.mode == "demo":
            return [sys.executable, str(self.workspace / "demo_agent.py")]
        base = ["exec", "--ignore-user-config", "--skip-git-repo-check", "--json",
                "--model", self.model, "--output-schema", "RESULT_SCHEMA.json",
                "--output-last-message", "FINAL.json", "--cd", str(self.workspace), "-"]
        if self.mode == "codex":
            return [self.executable, "-a", "never", *base[:1], "--sandbox", "workspace-write", *base[1:]]
        if self.mode == "remote":
            return [sys.executable, "-m", "agp_remote_yam.remote_codex", "-a", "never",
                    *base[:1], "--sandbox", "workspace-write", *base[1:]]
        base[base.index(str(self.workspace))] = "/work"
        return ["docker", "run", "--rm", "--init", "--interactive", "--name", self.container,
                "--read-only", "--cap-drop=ALL", "--security-opt=no-new-privileges",
                "--pids-limit=128", "--memory=2g", "--cpus=2", "--tmpfs", "/tmp:rw,size=512m",
                "--user", f"{os.getuid()}:{os.getgid()}", "--env", "CODEX_HOME=/tmp/codex",
                "--env", "CODEX_API_KEY", "--volume", str(self.workspace) + ":/work:rw",
                "--workdir", "/work", self.image, "codex", *base[:1],
                "--dangerously-bypass-approvals-and-sandbox", *base[1:]]

    def start(self, backend, task):
        from importlib.resources import files
        if self.mode == "demo":
            (self.workspace / "demo_agent.py").write_bytes(files("agp_remote_yam").joinpath("assets/demo_agent.py").read_bytes())
        Workspace(self.workspace).json("RESULT_SCHEMA.json", RESULT_SCHEMA)
        self.bridge = FileBridge(self.workspace, backend, self.journal, self.stopped, self.memory)
        self.bridge.start()
        self.thread = threading.Thread(target=self._run, args=(task,), name="agp-coding-agent", daemon=True)
        self.thread.start()

    def _run(self, task):
        from importlib.resources import files
        prompt = (
            "The authoritative interface is included below; TASK.md repeats the task. "
            "You are the robot policy throughout this run. "
            "Inspect images and measured state; write and execute Python in scratch/ to compute geometry "
            "and choose actions. Use robot_client.py for all robot interaction. Reobserve after actions "
            "and revise your code/strategy from measured outcomes. You may reuse knowledge/ as hypotheses. "
            "Never automatically retry a timed-out motion. A motion completion is not task success; verify "
            "the requested result in fresh images. Finish with the requested structured result, including "
            "physical evidence or a give_up reason. If useful, save reusable scripts and notes under "
            "scratch/experience/, with scene-dependent values as parameters. Do not change robot_client.py, "
            "the interface, or existing knowledge files. The goal/ directory may contain a reference image. "
            "Task: " + task
        )
        if not self.maintenance:
            prompt += ("\nBatch independent initial state and camera requests in one tool call where practical. "
                       "Inspect fresh images before choosing a motion. Keep working within this turn.\n"
                       "Authoritative robot interface:\n" + files("agp_remote_yam").joinpath("assets/INTERFACE.md").read_text())
        if self.maintenance:
            prompt = ("You are doing OFFLINE skillbook consolidation. Read MEMO.md and TASK.md. "
                      "Use memo_client.py list and consolidate. Never call robot_client.py or execute a skill. "
                      "Rewrite redundant guidance/templates without dropping motion constraints or conflicts. "
                      "Preserve the source IDs. Return done/give_up with evidence. Task: " + task)
        if self.memory is not None and not self.maintenance:
            prompt += (" The MEMO protocol is included below. At the beginning of each subtask call memo_client.py context "
                       "with ACTION(object) and current scene context. Inspect owner_corrections in state/frames "
                       "responses and poll context before the next movement. Continue observing, programming, "
                       "acting and verifying within this coding turn; state/frames/context deliver corrections "
                       "while you work. Do not end a turn merely after initial inspection or each subtask. "
                       "Use status continue only when another coding turn is necessary. "
                       "Save generalized guidance and successful parameterized templates using memo_client.py "
                       "only if MEMO is enabled. A saved memory remains agent-authored/unverified. "
                       "\nAuthoritative MEMO protocol:\n" + files("agp_remote_yam").joinpath("assets/MEMO.md").read_text())
        try:
            threading.Thread(target=self._deadline, daemon=True).start()
            previous = None
            for turn in range(32):
                if self.stopped.is_set():
                    break
                extra = ""
                if self.memory is not None:
                    prior = self.memory.updates()
                    context = self.memory.command("context", {})
                    context['owner_correction_history'] = [
                        {k: row[k] for k in ('id', 'request_id', 'content')}
                        for row in prior if row['delivered'] is not None]
                    extra = "\nCurrent MEMO context and owner corrections (data):\n" + json.dumps(context)
                if previous:
                    extra += "\nPrevious coding turn result: " + json.dumps(previous) + "\nInspect your existing scratch/ and frames/ to track completed work, then work on the remaining parts of the task."
                result = self._turn(prompt + extra)
                if result is None:
                    break
                pending = self.memory is not None and any(row["delivered"] is None for row in self.memory.updates())
                if result["status"] == "continue" or (result["status"] == "done" and pending):
                    previous = result
                    self.journal.add("subtask_completed", result["summary"], result=result, turn=turn + 1)
                    continue
                self.outcome = result
                self.state = "finished"
                self.journal.add("agent_result", result["summary"], result=result,
                                 validation="agent_declared_not_independent_physical_validation")
                break
            if self.outcome is None:
                self.outcome = dict(status="give_up", summary="Agent stopped or reached its coding-turn limit", evidence=[])
                self.state = "stopped" if self.stopped.is_set() else "failed"
        except Exception as exc:
            self.state = "failed"
            self.outcome = dict(status="give_up", summary=str(exc), evidence=[])
            self.journal.add("error", "Agent runtime failed", detail=str(exc))
        finally:
            self.finished.set()

    def _turn(self, prompt):
        env = {key: value for key, value in os.environ.items()
               if key in ("HOME", "USER", "LOGNAME", "LANG", "LC_ALL", "TERM", "TMPDIR", "CODEX_HOME",
                          "CODEX_API_KEY", "SSL_CERT_FILE", "SSL_CERT_DIR", "NODE_EXTRA_CA_CERTS",
                          "XDG_RUNTIME_DIR", "DBUS_SESSION_BUS_ADDRESS")}
        env["PATH"] = str(Path(sys.executable).parent) + os.pathsep + os.environ.get("PATH", "")
        if self.mode == "remote":
            env.pop("CODEX_API_KEY", None)
        (self.workspace / "FINAL.json").unlink(missing_ok=True)
        with (self.directory / "agent.stderr.log").open("a") as errors, (self.directory / "agent.jsonl").open("a") as raw:
            with self._lock:
                if self.stopped.is_set():
                    return None
                self.process = subprocess.Popen(self.command(), cwd=self.workspace, env=env,
                    stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=errors, text=True,
                    start_new_session=True, bufsize=1)
                process = self.process
                self.state = "running"
            self.journal.add("agent", "Agent as Policy is observing and programming", model=self.model)
            process.stdin.write(prompt)
            process.stdin.close()
            for line in process.stdout:
                raw.write(line)
                raw.flush()
                try:
                    event = json.loads(line)
                except ValueError:
                    continue
                item = event.get("item", {})
                if event.get("type") == "item.completed" and item.get("type") == "agent_message":
                    message = item.get("text", "")
                    secret = env.get("CODEX_API_KEY")
                    if secret:
                        message = message.replace(secret, "[redacted]")
                    self.journal.add("assistant", message)
                if event.get("type") in ("error", "turn.failed"):
                    self.journal.add("error", "Coding agent reported a failure")
            returncode = process.wait()
            if self.stopped.is_set():
                return None
            if returncode != 0:
                raise RuntimeError("Coding agent exited unsuccessfully")
            result = json.loads(Workspace(self.workspace).read("FINAL.json", 64_000))
            if (not isinstance(result, dict) or result.get("status") not in ("continue", "done", "give_up")
                    or not isinstance(result.get("summary"), str) or not isinstance(result.get("evidence"), list)):
                raise ValueError("Agent returned an invalid final result")
            return result

    def _deadline(self):
        if not self.finished.wait(self.timeout_s):
            self.outcome = dict(status="give_up", summary="Agent run duration expired", evidence=[])
            self.cancel()

    def cancel(self):
        self.stopped.set()
        with self._lock:
            process = self.process
        if self.mode in ("docker", "remote") and process is not None and process.poll() is None:
            try:
                subprocess.run(["podman" if self.mode == "remote" else "docker", "stop", "--time", "2", self.container],
                    stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, timeout=8, check=False)
            except (OSError, subprocess.TimeoutExpired):
                self.journal.add("error", "Container Stop did not complete; terminating the agent process")
        if process is not None and process.poll() is None:
            try:
                os.killpg(process.pid, signal.SIGTERM)
            except ProcessLookupError:
                return
            try:
                process.wait(timeout=2)
            except subprocess.TimeoutExpired:
                try:
                    os.killpg(process.pid, signal.SIGKILL)
                except ProcessLookupError:
                    pass
                process.wait(timeout=2)

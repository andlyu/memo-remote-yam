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
    status=dict(type="string", enum=["done", "give_up"]), summary=dict(type="string"),
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
        self._lock = threading.RLock()
        self.container = "agp-" + self.directory.name

    def check_available(self):
        binary = "docker" if self.mode == "docker" else self.executable
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
        self.bridge = FileBridge(self.workspace, backend, self.journal, self.stopped)
        self.bridge.start()
        self.thread = threading.Thread(target=self._run, args=(task,), name="agp-coding-agent", daemon=True)
        self.thread.start()

    def _run(self, task):
        prompt = (
            "Read README_interface.md and TASK.md. You are the robot policy throughout this run. "
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
        env = {key: value for key, value in os.environ.items()
               if key in ("HOME", "USER", "LOGNAME", "LANG", "LC_ALL", "TERM", "TMPDIR", "CODEX_HOME",
                          "CODEX_API_KEY", "SSL_CERT_FILE", "SSL_CERT_DIR", "NODE_EXTRA_CA_CERTS")}
        env["PATH"] = str(Path(sys.executable).parent) + os.pathsep + os.environ.get("PATH", "")
        try:
            with (self.directory / "agent.stderr.log").open("w") as errors, (self.directory / "agent.jsonl").open("w") as raw:
                with self._lock:
                    if self.stopped.is_set():
                        return
                    self.process = subprocess.Popen(self.command(), cwd=self.workspace, env=env,
                        stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=errors, text=True,
                        start_new_session=True, bufsize=1)
                    self.state = "running"
                self.journal.add("agent", "Agent as Policy is observing and programming", model=self.model)
                self.process.stdin.write(prompt)
                self.process.stdin.close()
                watchdog = threading.Thread(target=self._deadline, daemon=True)
                watchdog.start()
                for line in self.process.stdout:
                    raw.write(line)
                    raw.flush()
                    try:
                        event = json.loads(line)
                    except ValueError:
                        continue
                    # Reasoning and unfiltered process events remain private.
                    item = event.get("item", {})
                    if event.get("type") == "item.completed" and item.get("type") == "agent_message":
                        text = item.get("text", "")
                        for key in ("CODEX_API_KEY",):
                            secret = env.get(key)
                            if secret:
                                text = text.replace(secret, "[redacted]")
                        self.journal.add("assistant", text)
                    if event.get("type") in ("error", "turn.failed"):
                        self.journal.add("error", "Coding agent reported a failure")
                returncode = self.process.wait()
                if not self.stopped.is_set() and returncode == 0:
                    result = json.loads(Workspace(self.workspace).read("FINAL.json", 64_000))
                    if (not isinstance(result, dict) or result.get("status") not in ("done", "give_up")
                            or not isinstance(result.get("summary"), str) or not isinstance(result.get("evidence"), list)):
                        raise ValueError("Agent returned an invalid final result")
                    self.outcome = result
                    self.state = "finished"
                    self.journal.add("agent_result", result["summary"], result=result,
                                     validation="agent_declared_not_independent_physical_validation")
                elif self.outcome is None:
                    self.outcome = dict(status="give_up", summary="Agent stopped or exited unsuccessfully", evidence=[])
                    self.state = "stopped" if self.stopped.is_set() else "failed"
                    self.journal.add("error", self.outcome["summary"], returncode=returncode)
        except Exception as exc:
            self.state = "failed"
            self.outcome = dict(status="give_up", summary=str(exc), evidence=[])
            self.journal.add("error", "Agent runtime failed", detail=str(exc))
        finally:
            self.finished.set()

    def _deadline(self):
        if not self.finished.wait(self.timeout_s):
            self.outcome = dict(status="give_up", summary="Agent run duration expired", evidence=[])
            self.cancel()

    def cancel(self):
        self.stopped.set()
        with self._lock:
            process = self.process
        if self.mode == "docker" and process is not None and process.poll() is None:
            try:
                subprocess.run(["docker", "stop", "--time", "2", self.container],
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

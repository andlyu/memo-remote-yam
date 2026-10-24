"""Test the production container flags/IPC with a scripted agent and mock robot.

Build Dockerfile.agent first. No model credential, inference or physical robot.
"""
from importlib.resources import files
import json
from pathlib import Path
import shutil
import time
from agp_remote_yam.manager import RunManager, Settings
from agp_remote_yam.runtime import AgentRuntime

production_command = AgentRuntime.command
production_start = AgentRuntime.start


def scripted_command(runtime):
    command = production_command(runtime)
    return command[:command.index(runtime.image) + 1] + ["python3", "demo_agent.py"]


def start_scripted(runtime, backend, task):
    runtime.workspace.joinpath("demo_agent.py").write_bytes(
        files("agp_remote_yam").joinpath("assets/demo_agent.py").read_bytes())
    production_start(runtime, backend, task)


def check_docker(runtime):
    if not shutil.which("docker"):
        raise RuntimeError("Docker is not installed")


AgentRuntime.command = scripted_command
AgentRuntime.start = start_scripted
AgentRuntime.check_available = check_docker
manager = RunManager(Settings(data=Path("outputs/container-smoke"), mock_robot=True, agent_mode="docker"))
try:
    identity = manager.start("Scripted container transport smoke; offline mock robot only", "container-smoke", duration=60)
    print(json.dumps(dict(run_id=identity)), flush=True)
    deadline = time.monotonic() + 45
    while identity in manager.active and time.monotonic() < deadline:
        time.sleep(.1)
    if identity in manager.active:
        raise TimeoutError("Container smoke exceeded deadline")
    run = manager.detail(identity, "container-smoke")
    print(json.dumps(dict(status=run["status"], outcome=run["outcome"], error=run.get("error"),
                         tool_calls=[e["message"] for e in run["events"] if e["kind"] == "tool_call"]), indent=2))
    if not run["outcome"] or run["outcome"]["status"] != "done":
        raise SystemExit(1)
finally:
    manager.close()

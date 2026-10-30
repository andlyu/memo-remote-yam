import json
import sys
import time
import subprocess
import pytest
from pathlib import Path
from types import SimpleNamespace
from agp_remote_yam.runtime import AgentRuntime
from agp_remote_yam.storage import RunStore, Journal
from agp_remote_yam.manager import RunManager, Settings


def test_local_agent_uses_workspace_sandbox_without_credential_copy(tmp_path):
    _, directory = RunStore(tmp_path).create("test")
    runtime = AgentRuntime(directory, Journal(directory))
    command = runtime.command()
    assert "workspace-write" in command
    assert "--dangerously-bypass-approvals-and-sandbox" not in command
    assert "--json" in command and "--output-schema" in command
    assert not (directory / "workspace/auth.json").exists()


def test_docker_mounts_only_workspace_and_keeps_stdin_open(tmp_path):
    _, directory = RunStore(tmp_path).create("test")
    command = AgentRuntime(directory, Journal(directory), mode="docker").command()
    assert "--interactive" in command and "--read-only" in command
    assert command.count("--volume") == 1
    assert command[command.index("--volume") + 1] == str(directory / "workspace") + ":/work:rw"
    assert "--dangerously-bypass-approvals-and-sandbox" in command  # only inside the container


def test_cancel_reaps_subprocess(tmp_path):
    _, directory = RunStore(tmp_path).create("test")
    runtime = AgentRuntime(directory, Journal(directory))
    runtime.command = lambda: [sys.executable, "-u", "-c", "import time; time.sleep(60)"]
    runtime.start(SimpleNamespace(command=lambda *_: {}), "test")
    deadline = time.monotonic() + 3
    while runtime.process is None and time.monotonic() < deadline: time.sleep(.01)
    assert runtime.process is not None
    runtime.cancel()
    assert runtime.finished.wait(3)
    assert runtime.process.poll() is not None


def test_restart_marks_old_run_interrupted_without_resuming(tmp_path):
    root = tmp_path / "runs"
    store = RunStore(root)
    _, directory = store.create("previous")
    store.update(directory, status="running", owner="old")
    manager = RunManager(Settings(data=tmp_path, demo=True))
    assert manager.store.list()[0]["status"] == "interrupted"
    assert manager.active == {}


def test_real_agent_can_use_mock_robot_without_scripted_agent(tmp_path):
    settings = Settings(data=tmp_path, mock_robot=True)
    assert settings.offline is True and settings.demo is False
    assert settings.agent_mode == "codex"


def test_owner_correction_survives_fresh_coding_turns_without_repeat_delivery(tmp_path):
    from agp_remote_yam.memo import Skillbook, MemoryChannel
    _, directory = RunStore(tmp_path / 'runs').create('offline correction fixture')
    journal = Journal(directory)
    channel = MemoryChannel(Skillbook(tmp_path / 'memory.sqlite3', 'lexical'), 'owner', directory, journal)
    correction = 'Fixture constraint: clear the rim before translating laterally.'
    channel.correct(correction, 'fixture-correction')
    runtime = AgentRuntime(directory, journal)
    runtime.memory = channel
    prompts = []
    def turn(prompt):
        prompts.append(prompt)
        return dict(status='continue' if len(prompts) == 1 else 'done', summary='Offline fixture', evidence=[])
    runtime._turn = turn
    runtime._run('offline correction fixture')
    assert len(prompts) == 2 and correction in prompts[1]
    assert 'owner_correction_history' in prompts[1]
    assert channel.updates(deliver=True) == []
    assert runtime.outcome['status'] == 'done'


def test_docker_stop_timeout_still_reaps_agent(tmp_path, monkeypatch):
    _, directory = RunStore(tmp_path).create("test")
    runtime = AgentRuntime(directory, Journal(directory), mode="docker")
    runtime.command = lambda: [sys.executable, "-u", "-c", "import time; time.sleep(60)"]
    runtime.start(SimpleNamespace(command=lambda *_: {}), "test")
    deadline = time.monotonic() + 3
    while runtime.process is None and time.monotonic() < deadline: time.sleep(.01)
    assert runtime.process is not None
    def unavailable(*args, **kwargs):
        raise subprocess.TimeoutExpired("docker stop", 8)
    monkeypatch.setattr(subprocess, "run", unavailable)
    runtime.cancel()
    assert runtime.finished.wait(3)
    assert runtime.process.poll() is not None

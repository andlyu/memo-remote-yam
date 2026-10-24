from concurrent.futures import Future
import json
from pathlib import Path
import subprocess
import sys
import threading
import time
from types import SimpleNamespace
import pytest
from agp_remote_yam.bridge import FileBridge
from agp_remote_yam.storage import Journal, RunStore
from agp_remote_yam.policy import AgPPolicy


def wait_until(predicate, timeout=5):
    deadline = time.monotonic() + timeout
    while time.monotonic() < deadline:
        value = predicate()
        if value:
            return value
        time.sleep(.02)
    raise AssertionError("Timed out waiting for condition")


def test_unmodified_upstream_client_and_exactly_once_request(tmp_path):
    store = RunStore(tmp_path)
    _, directory = store.create("test")
    workspace = directory / "workspace"
    journal = Journal(directory)
    stopped = threading.Event()
    calls = []
    class Backend:
        def command(self, arm, command, arguments):
            calls.append((arm, command, arguments))
            return {"observed": "current"}
    bridge = FileBridge(workspace, Backend(), journal, stopped)
    bridge.start()
    result = subprocess.run([sys.executable, "robot_client.py", ".", "--arm", "right", "state", "{}"],
        cwd=workspace, capture_output=True, text=True, timeout=5, check=True)
    assert json.loads(result.stdout) == {"ok": True, "observed": "current"}
    request = workspace / "bridge_right/req_000001.json"
    request.write_text(request.read_text())
    time.sleep(.1)
    assert calls == [("right", "state", {})]
    stopped.set()
    bridge.thread.join(2)


def test_invalid_command_returns_error_and_server_can_continue(tmp_path):
    _, directory = RunStore(tmp_path).create("test")
    stopped = threading.Event()
    backend = SimpleNamespace(command=lambda *_: (_ for _ in ()).throw(ValueError("unsupported")))
    bridge = FileBridge(directory / "workspace", backend, Journal(directory), stopped)
    bridge.start()
    result = subprocess.run([sys.executable, "robot_client.py", ".", "bad", "{}"],
        cwd=directory / "workspace", capture_output=True, text=True, timeout=5)
    response = json.loads(result.stdout)
    assert response["ok"] is False and response["retryable"] is False
    stopped.set()


def test_mismatched_completion_never_releases_waiting_command(tmp_path):
    runtime = SimpleNamespace(stopped=threading.Event(), finished=threading.Event(), model="test", state="test", outcome=None)
    policy = AgPPolicy(runtime, None, Journal(tmp_path))
    policy._pending = dict(count=2, last=8)
    policy._future = Future()
    with pytest.raises(RuntimeError, match="does not match"):
        policy.trajectory_completed({"step_id": 10, "settled": True}, 2)
    assert not policy._future.done()


def test_motion_failure_is_terminal_and_never_replayed(tmp_path):
    stopped = threading.Event()
    runtime = SimpleNamespace(stopped=stopped, finished=threading.Event(), model="test", state="test", outcome=None,
                              cancel=stopped.set)
    policy = AgPPolicy(runtime, None, Journal(tmp_path))
    policy._future = Future()
    policy.trajectory_failed("timeout", "Unknown motion outcome", 1)
    assert policy._future.done()
    with pytest.raises(RuntimeError, match="timeout"):
        policy.execute([{"step_id": 0}])
    assert policy._packets.empty()


def test_idle_feedback_refresh_preserves_last_motion_capture_boundary(tmp_path):
    runtime = SimpleNamespace(stopped=threading.Event(), finished=threading.Event(), model="test", state="test", outcome=None)
    policy = AgPPolicy(runtime, None, Journal(tmp_path))
    policy._identity = ("episode", "lease")
    policy._observation = dict(episode_id="episode", lease_id="lease", settled=True, observed_at=100.)
    policy._settled_after = 100.
    policy.refresh_observation = lambda: dict(policy._observation, observed_at=200.)
    feedback = policy.feedback()
    assert feedback["observed_at"] == 200.
    assert feedback["settled_after"] == 100.

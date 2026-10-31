import asyncio
import json
from pathlib import Path
import time
import sys
import os
import pytest
from agp_remote_yam.manager import Settings
from agp_remote_yam.web import App
from agp_remote_yam.storage import RunStore
from agp_remote_yam.workspace import Workspace
from agp_remote_yam.runtime import AgentRuntime


def request(app, path, method="GET", value=None, *, cookie=None, csrf=None, origin=None, extra_headers=()):
    headers = [(b"host", b"localhost")]
    headers.extend(extra_headers)
    if method == "POST" and path == "/api/runs":
        value = {"runner": {"kind": "automated", "name": "Automated"}, **(value or {})}
    if cookie: headers.append((b"cookie", cookie.encode()))
    if csrf: headers.append((b"x-csrf-token", csrf.encode()))
    if origin: headers.append((b"origin", origin.encode()))
    if method == "POST": headers.append((b"content-type", b"application/json"))
    output = []
    async def receive():
        return {"type": "http.request", "body": json.dumps(value or {}).encode()}
    async def send(message):
        output.append(message)
    scope = dict(type="http", method=method, path=path.split("?",1)[0], scheme="http", headers=headers,
                 query_string=path.split("?",1)[1].encode() if "?" in path else b"")
    asyncio.run(app(scope, receive, send))
    start, body = output
    head = dict(start["headers"])
    data = json.loads(body["body"]) if head[b"content-type"] == b"application/json" else body["body"]
    return start["status"], head[b"set-cookie"].decode().split(";",1)[0], data


def wait_run(app, identity, cookie):
    deadline = time.monotonic() + 8
    while time.monotonic() < deadline:
        status, _, run = request(app, "/api/runs/" + identity, cookie=cookie)
        assert status == 200
        if run["status"] in ("failed", "stopped", "timed_out", "disconnected") and not run["active"]:
            return run
        time.sleep(.03)
    raise AssertionError(run)


def test_browser_to_client_to_controller_and_saved_experience(tmp_path):
    app = App(Settings(data=tmp_path, demo=True))
    _, cookie, config = request(app, "/api/config")
    status, _, result = request(app, "/api/runs", "POST", {"task":"Test mock transport","duration_s":60}, cookie=cookie, csrf=config["csrf"])
    assert status == 202
    run = wait_run(app, result["id"], cookie)
    assert run["outcome"]["status"] == "done", run
    calls = [e for e in run["events"] if e["kind"] == "tool_call"]
    results = [e for e in run["events"] if e["kind"] == "tool_result"]
    assert [e["message"] for e in calls] == ["state", "frames", "move_joints", "frames"]
    assert all(e["response"]["ok"] for e in results)
    assert len([f for f in run["files"] if f.endswith("_top.png")]) == 2
    status, _, image = request(app, "/api/runs/" + result["id"] + "/files/frames/0001_left_top.png", cookie=cookie)
    assert status == 200 and image.startswith(b"\x89PNG")
    status, _, second = request(app, "/api/runs", "POST", {"task":"Reuse notes","duration_s":60,"experience_run":result["id"]}, cookie=cookie, csrf=config["csrf"])
    assert status == 202
    other = wait_run(app, second["id"], cookie)
    assert "knowledge/notes.md" in other["files"]
    assert (app.manager.store.directory(result["id"]) / "workspace/scratch/experience/notes.md").is_file()
    app.manager.close()


def test_csrf_and_cross_origin_cannot_create_runs(tmp_path):
    app = App(Settings(data=tmp_path, demo=True))
    _, cookie, config = request(app, "/api/config")
    assert request(app, "/api/runs", "POST", {"task":"bad"}, cookie=cookie)[0] == 403
    assert request(app, "/api/runs", "POST", {"task":"bad"}, cookie=cookie, csrf=config["csrf"], origin="https://foreign.example")[0] == 403
    assert app.manager.store.list() == []


def test_browser_ownership_protects_history_and_files(tmp_path):
    app = App(Settings(data=tmp_path, demo=True))
    _, first, conf = request(app, "/api/config")
    _, _, result = request(app, "/api/runs", "POST", {"task":"Own run","duration_s":60}, cookie=first, csrf=conf["csrf"])
    wait_run(app, result["id"], first)
    _, other, _ = request(app, "/api/config")
    assert request(app, "/api/runs/"+result["id"], cookie=other)[0] == 403
    assert request(app, "/api/runs", cookie=other)[2]["runs"] == []
    app.manager.close()


def test_workspace_rejects_symlink_directory_and_traversal(tmp_path):
    root = tmp_path / "work"; root.mkdir()
    outside = tmp_path / "outside"; outside.mkdir()
    (outside / "secret.json").write_text('{"private":true}')
    (root / "frames").symlink_to(outside, target_is_directory=True)
    workspace = Workspace(root)
    with pytest.raises(OSError): workspace.read("frames/secret.json")
    with pytest.raises(OSError): workspace.write("frames/new.json", b"{}")
    with pytest.raises(ValueError): workspace.read("../outside/secret.json")
    assert not (outside / "new.json").exists()


def test_experience_does_not_export_symlinks_and_new_run_is_fresh(tmp_path):
    store = RunStore(tmp_path / "runs")
    metadata, directory = store.create("first")
    source = directory / "workspace/scratch/experience"; source.mkdir()
    (source / "notes.md").write_text("Measured lesson")
    secret = tmp_path / "secret.py"; secret.write_text("secret")
    (source / "leak.py").symlink_to(secret)
    snapshot = store.save_experience(directory)
    assert [f["path"] for f in snapshot["files"]] == ["notes.md"]
    _, seeded = store.create("second", parent=metadata["id"])
    _, fresh = store.create("third")
    assert (seeded / "workspace/knowledge/notes.md").read_text() == "Measured lesson"
    assert not (fresh / "workspace/knowledge/notes.md").exists()


def test_browser_stop_revokes_mock_session_and_reaps_agent(tmp_path, monkeypatch):
    monkeypatch.setattr(AgentRuntime, "command", lambda _: [sys.executable, "-u", "-c", "import time; time.sleep(60)"])
    app = App(Settings(data=tmp_path, demo=True))
    _, cookie, config = request(app, "/api/config")
    _, _, result = request(app, "/api/runs", "POST", {"task":"Wait until stopped","duration_s":60}, cookie=cookie, csrf=config["csrf"])
    identity = result["id"]
    context = app.manager.active[identity]
    deadline = time.monotonic() + 4
    while context["runtime"].process is None and time.monotonic() < deadline: time.sleep(.01)
    controller = context["controller"]
    session_id = controller.status()["session_id"]
    assert session_id and context["runtime"].process is not None
    assert request(app, "/api/runs", cookie=cookie)[2]["runs"][0]["active"] is True
    assert request(app, "/api/runs/"+identity+"/stop", "POST", {}, cookie=cookie, csrf=config["csrf"])[0] == 200
    run = wait_run(app, identity, cookie)
    assert run["status"] == "stopped"
    assert controller._session_api.get_session(session_id)["status"] == "stopped"
    assert context["runtime"].process.poll() is not None
    assert controller._session_api.trajectory_log == []
    assert request(app, "/api/runs", cookie=cookie)[2]["runs"][0]["active"] is False


def test_workspace_rejects_fifo_without_blocking(tmp_path):
    os.mkfifo(tmp_path / "trap.json")
    started = time.monotonic()
    with pytest.raises(ValueError, match="regular file"):
        Workspace(tmp_path).read("trap.json")
    assert time.monotonic() - started < 1


def test_memo_corrections_and_skillbook_keep_browser_ownership(tmp_path, monkeypatch):
    monkeypatch.setattr(AgentRuntime, "command", lambda _: [sys.executable, "-u", "-c", "import time; time.sleep(60)"])
    app = App(Settings(data=tmp_path, demo=True, memo_site=True))
    _, cookie, config = request(app, "/api/config")
    _, other, other_config = request(app, "/api/config")
    try:
        status, _, run = request(app, "/api/runs", "POST", {"task":"MEMO owner test","duration_s":60,"memo":True}, cookie=cookie, csrf=config['csrf'])
        assert status == 202
        path = "/api/runs/" + run['id'] + "/corrections"
        value = dict(text="Clear the rim first", request_id="owner-correction-test")
        assert request(app, path, "POST", value, cookie=other, csrf=other_config['csrf'])[0] == 403
        assert request(app, path, "POST", value, cookie=cookie)[0] == 403
        assert request(app, path, "POST", value, cookie=cookie, csrf=config['csrf'])[0] == 202
        context = app.manager.active[run['id']]
        context['memory'].command('remember', dict(content='Clear the rim before translating laterally.'))
        assert len(request(app, '/api/memories', cookie=cookie)[2]['memories']) == 1
        assert request(app, '/api/memories', cookie=other)[2]['memories'] == []
    finally:
        app.manager.close()

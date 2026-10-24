from types import SimpleNamespace
from unittest.mock import patch
from pathlib import Path
import subprocess
import pytest
from agp_remote_yam.manager import Settings
from agp_remote_yam.web import App
from agp_remote_yam.video import fetch_media, stream_config


def test_demo_robot_still_displays_all_four_real_api_cameras(tmp_path, monkeypatch):
    app = App(Settings(data=tmp_path, demo=True))
    _, _, config = app.route("GET", "/api/config", {}, b"", "owner", "csrf")
    assert config["mode"] == "offline_mock"
    assert config["camera_source"] == "api"
    assert config["camera_roles"] == ["observer", "top", "left", "right"]
    assert config["video_stream"]["path"] == "synchronized-hd"
    calls = []
    def fetch(self, role, url):
        calls.append((role, url))
        return SimpleNamespace(jpeg=b"unchanged API JPEG")
    monkeypatch.setattr("remote_yam.cameras.CameraFrameSource.fetch", fetch)
    for role in config["camera_roles"]:
        assert app.route("GET", "/api/cameras/"+role+".jpg", {}, b"", "owner", "csrf")[2] == b"unchanged API JPEG"
    assert [role for role, _ in calls] == config["camera_roles"]
    assert all(url == app.settings.origin+"/v1/robots/yam-1/cameras/"+role+".jpg" for role,url in calls)
    assert app.manager.store.list() == []  # viewing never takes a robot lease


def test_synthetic_camera_fixtures_require_explicit_selection(tmp_path):
    app = App(Settings(data=tmp_path, demo=True, camera_source="synthetic"))
    assert app.video_stream is None
    assert app.route("GET", "/api/cameras/observer.jpg", {}, b"", "owner", "csrf")[2].startswith(b"\xff\xd8")


def test_video_relay_preserves_bytes_and_query_without_visitor_credentials():
    class Response:
        status = 200
        headers = {"Content-Type":"application/vnd.apple.mpegurl"}
        def read(self, limit): return b"#EXTM3U\nvideo1_stream.m3u8?session=public-id\n"
        def __enter__(self): return self
        def __exit__(self, *_): pass
    seen = []
    def open_request(req, **_):
        seen.append(req)
        return Response()
    with patch("agp_remote_yam.video.request.urlopen", side_effect=open_request):
        status, kind, data = fetch_media(stream_config("yam-1"), "/synchronized-hd/video1_stream.m3u8", {"session":["public-id"]})
    assert status == 200 and data.startswith(b"#EXTM3U")
    assert seen[0].full_url == "https://playground.blupe.io/synchronized-hd/video1_stream.m3u8?session=public-id"
    assert set(k.lower() for k in seen[0].headers) == {"origin"}


@pytest.mark.parametrize("path", ["/synchronized-hd/../private", "/observer/index.m3u8", "/synchronized-hd/secret.json"])
def test_video_proxy_accepts_only_the_configured_public_stream(path):
    with pytest.raises(FileNotFoundError): fetch_media(stream_config("yam-1"), path, {})


def test_original_public_camera_atlas_mapping():
    script = Path(__file__).parents[1] / "src/agp_remote_yam/static/cameras.js"
    source = """
const assert = require('node:assert/strict');
const {crop} = require(process.argv[1]);
const order = ['top','observer','left','right'];
assert.deepEqual(crop('observer',1280,720,order),[640,0,640,360]);
assert.deepEqual(crop('top',1280,720,order),[0,0,640,360]);
assert.deepEqual(crop('left',1280,720,order),[0,360,640,360]);
assert.deepEqual(crop('right',1280,720,order),[640,360,640,360]);
assert.deepEqual(crop('observer',2560,1080,order),[0,0,1920,1080]);
assert.deepEqual(crop('top',2560,1080,order),[1920,360,640,360]);
assert.deepEqual(crop('left',2560,1080,order),[1920,0,640,360]);
assert.deepEqual(crop('right',2560,1080,order),[1920,720,640,360]);
"""
    subprocess.run(["node", "-e", source, str(script)], check=True, timeout=5)

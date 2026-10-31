"""Small ASGI website. Browser identity owns runs; CSRF protects mutations."""
import asyncio
import base64
import hashlib
import hmac
from http.cookies import SimpleCookie
from importlib.resources import files
import io
import json
import mimetypes
import os
from pathlib import Path
import secrets
from urllib.parse import parse_qs, unquote, urlsplit
from PIL import Image
from .dependency import REMOTE_YAM_COMMIT, UPSTREAM_AGP_COMMIT
from .manager import RunManager, ROBOTS
from .workspace import Workspace
from .video import CAMERA_ROLES, stream_config, fetch_media
from .identity import APPROACH, runner_identity


class App:
    def __init__(self, settings, *, public_origin=None):
        self.manager = RunManager(settings)
        self.settings = settings
        self.video_streams = {robot: stream_config(robot) if settings.camera_source == "api" else None
                              for robot in {settings.robot_id, *ROBOTS}}
        self.video_stream = self.video_streams[settings.robot_id]
        self.public_origin = public_origin.rstrip("/") if public_origin else None
        secret_file = Path(settings.data).resolve() / "web-secret"
        if not secret_file.exists():
            secret_file.write_bytes(secrets.token_bytes(32))
            secret_file.chmod(0o600)
        self.secret = secret_file.read_bytes()

    def configuration(self, robot_id, csrf):
        video_stream = self.video_streams[robot_id]
        return dict(csrf=csrf, robot_id=robot_id,
            robots=[dict(id=k, name=v) for k,v in ROBOTS.items()],
            model=self.settings.model, mode="offline_mock" if self.settings.offline else "physical_api",
            agent="scripted" if self.settings.demo else self.settings.agent_mode, remote_yam_revision=REMOTE_YAM_COMMIT,
            camera_source=self.settings.camera_source, camera_roles=list(CAMERA_ROLES), video_stream=video_stream,
            agp_reference_revision=UPSTREAM_AGP_COMMIT, approach="Agent as Policy + MEMO" if self.settings.memo_site else APPROACH,
            server_time=__import__("time").time(), source_repository="https://github.com/andlyu/agp-remote-yam",
            source_revision=os.environ.get("AGP_SOURCE_REVISION", "development"))

    def identity(self, headers):
        cookie = SimpleCookie()
        cookie.load(headers.get("cookie", ""))
        value = cookie.get("agp_visitor")
        visitor = value.value if value else ""
        if len(visitor) != 64 or any(c not in "0123456789abcdef" for c in visitor):
            visitor = secrets.token_hex(32)
        owner = hashlib.sha256(visitor.encode()).hexdigest()
        csrf = hmac.new(self.secret, visitor.encode(), hashlib.sha256).hexdigest()
        return visitor, owner, csrf

    async def __call__(self, scope, receive, send):
        if scope["type"] == "lifespan":
            while True:
                message = await receive()
                if message["type"] == "lifespan.startup":
                    await send({"type": "lifespan.startup.complete"})
                elif message["type"] == "lifespan.shutdown":
                    await asyncio.to_thread(self.manager.close)
                    await send({"type": "lifespan.shutdown.complete"})
                    return
        if scope["type"] != "http":
            return
        headers = {k.decode().lower(): v.decode() for k, v in scope["headers"]}
        visitor, owner, csrf = self.identity(headers)
        method, path = scope["method"], scope["path"]
        host = headers.get("host", "")
        try:
            hostname = urlsplit("http://" + host).hostname
            allowed = ({urlsplit(self.public_origin).hostname} if self.public_origin else {"127.0.0.1", "localhost", "::1"})
            if hostname not in allowed:
                raise PermissionError("Unexpected request host")
            body = bytearray()
            while True:
                message = await receive()
                if message["type"] == "http.disconnect":
                    return
                body.extend(message.get("body", b""))
                if len(body) > 12_000_000:
                    raise ValueError("Request exceeds 12 MB")
                if not message.get("more_body"):
                    break
            if method == "POST":
                expected_origin = self.public_origin or scope.get("scheme", "http") + "://" + host
                if headers.get("origin", expected_origin) != expected_origin:
                    raise PermissionError("Cross-origin run request refused")
                if not hmac.compare_digest(headers.get("x-csrf-token", ""), csrf):
                    raise PermissionError("Browser session token is missing")
                if not headers.get("content-type", "").startswith("application/json"):
                    raise ValueError("Send JSON")
            status, content_type, result = await asyncio.to_thread(
                self.route, method, path, parse_qs(scope.get("query_string", b"").decode()),
                bytes(body), owner, csrf)
        except PermissionError as exc:
            status, content_type, result = 403, "application/json", {"error": str(exc)}
        except FileNotFoundError:
            status, content_type, result = 404, "application/json", {"error": "Not found"}
        except (ValueError, KeyError, TypeError) as exc:
            status, content_type, result = 400, "application/json", {"error": str(exc)}
        except Exception as exc:
            status, content_type, result = 503, "application/json", {"error": "Service unavailable: " + str(exc)}
        if isinstance(result, (dict, list)):
            result = json.dumps(result, allow_nan=False).encode()
        elif isinstance(result, str):
            result = result.encode()
        media_headers = []
        if path.endswith("/replay.mp4") and status == 200:
            media_headers.append((b"accept-ranges", b"bytes"))
            if headers.get("range"):
                import re
                match = re.fullmatch(r"bytes=(\d+)-(\d*)", headers["range"])
                if not match or int(match[1]) >= len(result):
                    status, result = 416, b""
                else:
                    start = int(match[1]); end = min(int(match[2]) if match[2] else len(result)-1, len(result)-1)
                    if end < start:
                        status, result = 416, b""
                    else:
                        media_headers.append((b"content-range", f"bytes {start}-{end}/{len(result)}".encode()))
                        result, status = result[start:end+1], 206
        cookie = f"agp_visitor={visitor}; HttpOnly; SameSite=Strict; Path=/; Max-Age=31536000"
        if self.public_origin and self.public_origin.startswith("https://"):
            cookie += "; Secure"
        await send(dict(type="http.response.start", status=status, headers=[
            (b"content-type", content_type.encode()), (b"content-length", str(len(result)).encode()),
            (b"set-cookie", cookie.encode()), (b"cache-control", b"no-store"),
            (b"x-content-type-options", b"nosniff"), (b"referrer-policy", b"same-origin"),
            (b"content-security-policy", b"default-src 'self'; img-src 'self' data:; script-src 'self'; style-src 'self'; media-src 'self' blob:; connect-src 'self'; frame-ancestors 'none'")] + media_headers))
        await send(dict(type="http.response.body", body=result))

    def route(self, method, path, query, body, owner, csrf):
        robot_id = query.get("robot_id", [self.settings.robot_id])[0]
        if robot_id not in {self.settings.robot_id, *ROBOTS}:
            raise ValueError("Choose a configured YAM station")
        video_stream = self.video_streams[robot_id]
        if method == "GET" and path in ("/", "/static/app.js", "/static/style.css", "/static/cameras.js"):
            name = "index.html" if path == "/" else path.rsplit("/", 1)[-1]
            mime = {"index.html": "text/html; charset=utf-8", "app.js": "text/javascript", "cameras.js": "text/javascript", "style.css": "text/css"}[name]
            if self.settings.memo_site and name in ("index.html", "app.js"):
                name = "memo-" + name
            data = files("agp_remote_yam").joinpath("static", name).read_bytes()
            if name == "index.html":
                seed = json.dumps(self.configuration(robot_id, csrf)).replace("<", "\\u003c")
                data = data.replace(b"<!--INITIAL_CONFIG-->",
                    ('<script id="initial-config" type="application/json">'+seed+'</script>').encode())
            return 200, mime, data
        if method == "GET" and path in ("/static/hls.light.min.js", "/static/HLS-LICENSE"):
            from .dependency import runner_root
            asset = runner_root() / "static" / path.rsplit("/", 1)[-1]
            return 200, "text/javascript" if path.endswith(".js") else "text/plain", asset.read_bytes()
        if method == "GET":
            for stream in self.video_streams.values():
                if stream and path.startswith("/" + stream["path"] + "/"):
                    return fetch_media(stream, path, query)
        if method == "GET" and path == "/api/config":
            return 200, "application/json", self.configuration(robot_id, csrf)
        if method == "GET" and path == "/api/station":
            if self.settings.offline:
                return 200, "application/json", dict(connected=False, mock=True, message="Mock robot · no physical control")
            from remote_yam.session import HttpSessionAPI
            snapshot = HttpSessionAPI(self.settings.origin, robot_id=robot_id, timeout_s=5).get_queue_snapshot()
            station = next((s for s in snapshot.get("stations", []) if s.get("jetson_id") == robot_id), {})
            return 200, "application/json", dict(connected=station.get("connected") is True,
                available=station.get("available") is True, queue_ready=station.get("queue_ready") is True,
                message="Robot connected" if station.get("connected") else "Robot offline · runs will wait in the queue")
        if method == "GET" and path.startswith("/api/cameras/"):
            role = path.rsplit("/", 1)[-1].removesuffix(".jpg")
            if role not in CAMERA_ROLES:
                raise FileNotFoundError()
            if self.settings.camera_source == "synthetic":
                from .mock import preview
                data = preview(role)
            else:
                from remote_yam.cameras import CameraFrameSource
                from urllib.parse import quote
                source = CameraFrameSource(self.settings.origin, camera_names=(role,))
                data = source.fetch(role, self.settings.origin.rstrip("/") + "/v1/robots/" +
                    quote(robot_id, safe="") + "/cameras/" + role + ".jpg").jpeg
            return 200, "image/jpeg", data
        if path == "/api/runs" and method == "GET":
            with self.manager.lock:
                active = set(self.manager.active)
            rows = [dict({k: v for k, v in row.items() if k != "owner"}, active=row["id"] in active)
                    for row in self.manager.store.list() if row.get("owner") == owner and
                    (self.settings.memo_site or row.get("approach") == APPROACH and not row.get("memo_enabled"))]
            return 200, "application/json", dict(runs=rows)
        if path == "/api/memories" and method == "GET":
            if not self.settings.memo_site:
                raise FileNotFoundError()
            return 200, "application/json", dict(version=self.manager.skillbook.version(),
                encoder=self.manager.skillbook.encoder.identity, memories=self.manager.skillbook.list(owner))
        if path == "/api/runs" and method == "POST":
            value = json.loads(body)
            runner = runner_identity(value.get("runner"), automated_default=self.settings.memo_site)
            goal = None
            if value.get("goal_image"):
                encoded = value["goal_image"]
                if not isinstance(encoded, str) or not encoded.startswith("data:image/"):
                    raise ValueError("Goal must be an uploaded image")
                raw = base64.b64decode(encoded.split(",", 1)[1], validate=True)
                image = Image.open(io.BytesIO(raw))
                if image.width * image.height > 16_000_000:
                    raise ValueError("Goal image is too large")
                image.thumbnail((2048, 2048))
                target = io.BytesIO()
                image.convert("RGB").save(target, "PNG")
                goal = target.getvalue()
            identity = self.manager.start(value.get("task"), owner, duration=value.get("duration_s", 300),
                parent=value.get("experience_run") or None, goal=goal, memo=value.get("memo", False),
                memory_version=value.get("memory_version"), runner=runner, timing=value.get("timing"),
                robot_id=value.get("robot_id"))
            return 202, "application/json", dict(id=identity)
        if path.startswith("/api/runs/"):
            parts = path.split("/")
            identity = parts[3]
            if len(parts) == 4 and method == "GET":
                cursor = int(query.get("after", ["-1"])[0])
                return 200, "application/json", self.manager.detail(identity, owner, cursor)
            if len(parts) == 5 and parts[4] == "stop" and method == "POST":
                self.manager.stop(identity, owner)
                return 200, "application/json", {"status": "stop_requested"}
            if len(parts) == 5 and parts[4] == "replay.mp4" and method == "GET":
                directory = self.manager.owned(identity, owner)
                from .recording import replay_info
                if (replay_info(directory) or {}).get("status") != "ready":
                    raise FileNotFoundError()
                return 200, "video/mp4", Workspace(directory / "recording").read("physical.mp4", 256_000_000)
            if len(parts) == 5 and parts[4] == "corrections" and method == "POST":
                if not self.settings.memo_site:
                    raise FileNotFoundError()
                value = json.loads(body)
                row = self.manager.correct(identity, owner, value.get("text"), value.get("request_id"))
                return 202, "application/json", {"correction": {k:v for k,v in row.items() if k != "namespace"}}
            if len(parts) > 5 and parts[4] == "files" and method == "GET":
                directory = self.manager.owned(identity, owner)
                relative = unquote("/".join(parts[5:]))
                if Path(relative).suffix not in (".png", ".jpg", ".py", ".md", ".json", ".npy", ".npz"):
                    raise FileNotFoundError()
                data = Workspace(directory / "workspace").read(relative, 64_000_000)
                mime = mimetypes.guess_type(relative)[0] or "application/octet-stream"
                if Path(relative).suffix in (".py", ".md"):
                    mime = "text/plain; charset=utf-8"
                return 200, mime, data
        raise FileNotFoundError()

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
from pathlib import Path
import secrets
from urllib.parse import parse_qs, unquote, urlsplit
from PIL import Image
from .dependency import REMOTE_YAM_COMMIT, UPSTREAM_AGP_COMMIT
from .manager import RunManager
from .workspace import Workspace
from .video import CAMERA_ROLES, stream_config, fetch_media


class App:
    def __init__(self, settings, *, public_origin=None):
        self.manager = RunManager(settings)
        self.settings = settings
        self.video_stream = stream_config(settings.robot_id) if settings.camera_source == "api" else None
        self.public_origin = public_origin.rstrip("/") if public_origin else None
        secret_file = Path(settings.data).resolve() / "web-secret"
        if not secret_file.exists():
            secret_file.write_bytes(secrets.token_bytes(32))
            secret_file.chmod(0o600)
        self.secret = secret_file.read_bytes()

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
        cookie = f"agp_visitor={visitor}; HttpOnly; SameSite=Strict; Path=/; Max-Age=31536000"
        if self.public_origin and self.public_origin.startswith("https://"):
            cookie += "; Secure"
        await send(dict(type="http.response.start", status=status, headers=[
            (b"content-type", content_type.encode()), (b"content-length", str(len(result)).encode()),
            (b"set-cookie", cookie.encode()), (b"cache-control", b"no-store"),
            (b"x-content-type-options", b"nosniff"), (b"referrer-policy", b"same-origin"),
            (b"content-security-policy", b"default-src 'self'; img-src 'self' data:; script-src 'self'; style-src 'self'; media-src 'self' blob:; connect-src 'self'; frame-ancestors 'none'")]))
        await send(dict(type="http.response.body", body=result))

    def route(self, method, path, query, body, owner, csrf):
        if method == "GET" and path in ("/", "/static/app.js", "/static/style.css", "/static/cameras.js"):
            name = "index.html" if path == "/" else path.rsplit("/", 1)[-1]
            mime = {"index.html": "text/html; charset=utf-8", "app.js": "text/javascript", "cameras.js": "text/javascript", "style.css": "text/css"}[name]
            return 200, mime, files("agp_remote_yam").joinpath("static", name).read_bytes()
        if method == "GET" and path in ("/static/hls.light.min.js", "/static/HLS-LICENSE"):
            from .dependency import runner_root
            asset = runner_root() / "static" / path.rsplit("/", 1)[-1]
            return 200, "text/javascript" if path.endswith(".js") else "text/plain", asset.read_bytes()
        if method == "GET" and self.video_stream and path.startswith("/" + self.video_stream["path"] + "/"):
            return fetch_media(self.video_stream, path, query)
        if method == "GET" and path == "/api/config":
            return 200, "application/json", dict(csrf=csrf, robot_id=self.settings.robot_id,
                model=self.settings.model, mode="offline_mock" if self.settings.offline else "physical_api",
                agent="scripted" if self.settings.demo else self.settings.agent_mode, remote_yam_revision=REMOTE_YAM_COMMIT,
                camera_source=self.settings.camera_source, camera_roles=list(CAMERA_ROLES), video_stream=self.video_stream,
                agp_reference_revision=UPSTREAM_AGP_COMMIT)
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
                    quote(self.settings.robot_id, safe="") + "/cameras/" + role + ".jpg").jpeg
            return 200, "image/jpeg", data
        if path == "/api/runs" and method == "GET":
            rows = [{k: v for k, v in row.items() if k != "owner"}
                    for row in self.manager.store.list() if row.get("owner") == owner]
            return 200, "application/json", dict(runs=rows)
        if path == "/api/runs" and method == "POST":
            value = json.loads(body)
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
                parent=value.get("experience_run") or None, goal=goal)
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

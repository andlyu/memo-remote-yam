"""The existing public Remote YAM viewer, independent of agent execution.

Contract: pinned codex-runner/local_playground.py media proxy and
remote_yam/video_stream.py. No visitor credentials are forwarded.
"""
import re
from urllib import request, error
from urllib.parse import urlencode
from .dependency import runner_root

PUBLIC_VIEWER = "https://playground.blupe.io"
CAMERA_ROLES = ("observer", "top", "left", "right")


def stream_config(robot_id):
    runner_root()
    from remote_yam.video_stream import video_stream
    return video_stream(robot_id)


def fetch_media(stream, path, query):
    if not stream:
        raise FileNotFoundError()
    prefix = "/" + stream["path"] + "/"
    filename = path.removeprefix(prefix)
    if (not path.startswith(prefix) or not re.fullmatch(r"[A-Za-z0-9_-]+\.(?:m3u8|mp4|m4s|ts)", filename)):
        raise FileNotFoundError()
    encoded = urlencode(query, doseq=True)
    if len(encoded) > 2048:
        raise ValueError("Video query is too long")
    url = PUBLIC_VIEWER + path + ("?" + encoded if encoded else "")
    req = request.Request(url, headers={"Origin": PUBLIC_VIEWER})
    try:
        # Match LocalPlayground: the public viewer redirects retired stream
        # paths to the active feed. No browser credentials are attached.
        response = request.urlopen(req, timeout=15)
    except error.HTTPError as exc:
        response = exc
    with response:
        data = response.read(8_000_001)
        if len(data) > 8_000_000:
            raise ValueError("Video response exceeds 8 MB")
        return response.status, response.headers.get("Content-Type", "application/octet-stream"), data

"""Optional Python convenience wrapper around the unchanged upstream CLI.

No targets, motion plans, retries, hardware access or task logic live here.
Run generated programs with PYTHONPATH=. python3 scratch/program.py.
"""
import json
from pathlib import Path
import re
import subprocess
import sys

ROOT = Path(__file__).resolve().parent


def request(command, arguments=None, *, arm="left"):
    if arm not in ("left", "right"):
        raise ValueError("Choose left or right")
    process = subprocess.run([sys.executable, str(ROOT / "robot_client.py"), str(ROOT),
                              "--arm", arm, command, json.dumps(arguments or {})],
                             cwd=ROOT, capture_output=True, text=True, timeout=300)
    value = json.loads(process.stdout)
    if process.returncode or not value.get("ok"):
        raise RuntimeError(value)
    return value


def once(name, command, arguments=None, *, arm="left"):
    """Record one attempted command, including failure/timeout; never replay it."""
    if not isinstance(name, str) or not re.fullmatch(r"[A-Za-z0-9_-]{1,64}", name):
        raise ValueError("Use a simple unique action name")
    with (ROOT / "scratch" / ("attempted_" + name)).open("x") as marker:
        marker.write("One attempt; never automatically retry.\n")
    return request(command, arguments, arm=arm)

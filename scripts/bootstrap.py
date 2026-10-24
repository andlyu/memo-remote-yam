"""Install the public runner as an ignored, pinned external checkout."""
import json
from pathlib import Path
import subprocess
import sys

root = Path(__file__).resolve().parents[1]
lock = json.loads((root / "dependency.lock.json").read_text())["remote_yam"]
target = root / ".deps/blupe-remote-yam"
if not target.exists():
    target.parent.mkdir(parents=True, exist_ok=True)
    subprocess.run(["git", "clone", "--filter=blob:none", "--no-checkout", lock["repository"], str(target)], check=True)
subprocess.run(["git", "-C", str(target), "fetch", "origin", lock["commit"]], check=True)
if subprocess.check_output(["git", "-C", str(target), "status", "--porcelain", "--untracked-files=no"], text=True):
    sys.exit("Dependency has local tracked changes; preserve them before bootstrapping")
subprocess.run(["git", "-C", str(target), "checkout", "--detach", lock["commit"]], check=True)
print("Remote YAM dependency ready:", lock["commit"])

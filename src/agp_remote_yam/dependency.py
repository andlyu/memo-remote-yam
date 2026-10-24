"""Import a separately installed, immutable public runner dependency."""
from pathlib import Path
import os
import subprocess
import sys

REMOTE_YAM_COMMIT = "fb1aaa9a696ae4597d06aef41bf876bf2ec90e4d"
UPSTREAM_AGP_COMMIT = "54dd96ed97c013950816bb674cbc38a68ec19b51"
ROOT = Path(__file__).resolve().parents[2]


def runner_root():
    checkout = Path(os.environ.get("REMOTE_YAM_ROOT", ROOT / ".deps/blupe-remote-yam")).resolve()
    actual = subprocess.check_output(["git", "-C", str(checkout), "rev-parse", "HEAD"], text=True).strip()
    if actual != REMOTE_YAM_COMMIT:
        raise RuntimeError("Remote YAM dependency revision differs from dependency.lock.json")
    runner = checkout / "codex-runner"
    if not (runner / "src/remote_yam/controller.py").is_file():
        raise RuntimeError("Run scripts/bootstrap.py to install the public Remote YAM dependency")
    # Do not consume a dirty working copy through an environment override.
    if subprocess.check_output(["git", "-C", str(checkout), "status", "--porcelain", "--untracked-files=no"], text=True):
        raise RuntimeError("Remote YAM dependency has tracked edits; use a clean pinned checkout")
    for path in (runner, runner / "src"):
        if str(path) not in sys.path:
            sys.path.insert(0, str(path))
    return runner

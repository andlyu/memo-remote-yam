"""Explicit real-model smoke against a mock station. Never constructs HttpSessionAPI."""
import argparse
import json
from pathlib import Path
import time
from agp_remote_yam.manager import RunManager, Settings

parser = argparse.ArgumentParser(description=__doc__)
parser.add_argument("--model", default="gpt-6-astra")
parser.add_argument("--data", type=Path, default=Path("outputs/model-smoke"))
args = parser.parse_args()
manager = RunManager(Settings(data=args.data, mock_robot=True, model=args.model))
task = (
    "This is an OFFLINE MOCK transport smoke test, not a physical task. "
    "Read the interface. Write and execute scratch/smoke.py to use robot_client.py "
    "for left state, frames with cams [top,wrist] and depth false, then change "
    "only left joint 0 by +0.01 radians from its measured value, call move_joints, "
    "then state and frames again. Inspect one saved PNG with your image tool. "
    "Save scratch/experience/notes.md describing the mock-only result. "
    "Finish with done only if the matching command returned measured settled "
    "completion and the fresh state matches. Explicitly say no physical task was validated."
)
try:
    identity = manager.start(task, "model-smoke", duration=120)
    print(json.dumps(dict(run_id=identity, data=str(args.data.resolve())), indent=2), flush=True)
    deadline = time.monotonic() + 150
    while identity in manager.active and time.monotonic() < deadline:
        time.sleep(.2)
    if identity in manager.active:
        raise TimeoutError("Model smoke exceeded its deadline")
    run = manager.detail(identity, "model-smoke")
    print(json.dumps(dict(status=run["status"], outcome=run["outcome"], error=run.get("error"),
                         tool_calls=[e["message"] for e in run["events"] if e["kind"] == "tool_call"],
                         files=run["files"]), indent=2), flush=True)
    if not run["outcome"] or run["outcome"]["status"] != "done":
        raise SystemExit(1)
finally:
    manager.close()

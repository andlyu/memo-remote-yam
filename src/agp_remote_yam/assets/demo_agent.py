"""Explicit offline scripted agent: tests the real client/server/controller path."""
import json
from pathlib import Path
import subprocess
import sys


def call(command, arguments=None):
    result = subprocess.run([sys.executable, "robot_client.py", ".", command, json.dumps(arguments or {})],
                            check=True, capture_output=True, text=True)
    value = json.loads(result.stdout)
    if not value["ok"]:
        raise RuntimeError(value)
    return value


print(json.dumps(dict(type="item.completed", item=dict(type="agent_message",
    text="Offline scripted demo: reading mock state and cameras, then sending a small mock joint movement."))), flush=True)
state = call("state")
call("frames", {"depth": False})
target = list(state["joints"])
target[0] += .01
call("move_joints", {"joints": target})
call("frames", {"depth": False})
Path("scratch/experience").mkdir(exist_ok=True)
Path("scratch/experience/notes.md").write_text("Offline mock transport check only; no physical manipulation evidence.\n")
Path("FINAL.json").write_text(json.dumps(dict(status="done", summary="Offline protocol demonstration completed",
    evidence=["Read mock camera/state", "Correlated mock trajectory completion", "No physical robot used"])))

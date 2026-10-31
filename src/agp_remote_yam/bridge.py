"""Compatible server for the upstream AgP request/response file protocol.

Reference: agent-as-policy agp/robot_client.py at 54dd96e. Each request is
handled once, in sequence; errors and timeouts are never automatically replayed.
"""
import json
import re
import threading
import time
from .workspace import Workspace


class FileBridge:
    def __init__(self, workspace, backend, journal, stopped, memory=None, *, admitting=False, motion_ready=None):
        self.workspace = Workspace(workspace)
        self.backend, self.journal, self.stopped = backend, journal, stopped
        self.thread = None
        self.memory = memory
        self.admitting = admitting
        self.motion_ready = motion_ready

    def start(self):
        # Only read requests may wait across admission. A pre-lease action must
        # never be released later against a new robot pose or lease.
        self.before_admission = ({(arm, name) for arm, folder in (("left", "bridge"), ("right", "bridge_right"))
                                 for name in self.workspace.list(folder) if name.startswith("req_")}
                                if self.admitting else set())
        self.thread = threading.Thread(target=self.run, name="agp-file-bridge", daemon=True)
        self.thread.start()

    def run(self):
        consumed = set()
        while not self.stopped.is_set():
            progressed = False
            channels = [("left", "bridge"), ("right", "bridge_right")]
            if self.memory is not None:
                channels.append(("memo", "bridge_memo"))
            for arm, folder in channels:
                try:
                    names = sorted(self.workspace.list(folder))
                except OSError:
                    self.journal.add("error", "Agent workspace bridge directory is unavailable")
                    self.stopped.set()
                    return
                for name in names:
                    match = re.fullmatch(r"req_(\d{6,})\.json", name)
                    if not match or (arm, name) in consumed:
                        continue
                    # Mark BEFORE executing. A crash or a lost reply cannot
                    # cause another hardware submission by this server.
                    consumed.add((arm, name))
                    progressed = True
                    started = time.monotonic()
                    command = "invalid"
                    try:
                        request = json.loads(self.workspace.read(folder + "/" + name))
                        if not isinstance(request, dict) or request.get("id") != int(match[1]):
                            raise ValueError("Invalid AgP request identity")
                        command, arguments = request.get("cmd"), request.get("args", {})
                        if not isinstance(command, str) or not isinstance(arguments, dict):
                            raise ValueError("Invalid AgP command")
                        if (arm, name) in self.before_admission and command not in ("state", "frames", "status", "help"):
                            raise ValueError("Motion was requested before lease admission; command rejected and not replayed")
                        if (arm != "memo" and command in ("move_joints", "move_ee", "gripper")
                                and self.motion_ready is not None and not self.motion_ready()):
                            raise ValueError("A new coding step after the leased images is required; motion rejected and not replayed")
                        self.journal.add("tool_call", command, arm=arm, arguments=arguments)
                        if arm == "memo":
                            result = self.memory.command(command, arguments)
                        else:
                            result = self.backend.command(arm, command, arguments)
                            if self.memory is not None and command in ("state", "frames"):
                                result["owner_corrections"] = self.memory.updates(deliver=True)
                        response = dict(ok=True, **result)
                    except Exception as exc:
                        response = dict(ok=False, error_code=getattr(exc, "code", type(exc).__name__),
                                        error=str(exc), retryable=False)
                    self.journal.add("tool_result", command, arm=arm, response=response,
                                     duration_s=round(time.monotonic() - started, 3))
                    try:
                        self.workspace.json(folder + "/resp_" + match[1] + ".json", response)
                    except OSError:
                        self.stopped.set()
                        return
                    if self.stopped.is_set():
                        return
            if not progressed:
                self.stopped.wait(.025)

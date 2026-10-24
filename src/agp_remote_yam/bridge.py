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
    def __init__(self, workspace, backend, journal, stopped):
        self.workspace = Workspace(workspace)
        self.backend, self.journal, self.stopped = backend, journal, stopped
        self.thread = None

    def start(self):
        self.thread = threading.Thread(target=self.run, name="agp-file-bridge", daemon=True)
        self.thread.start()

    def run(self):
        consumed = set()
        while not self.stopped.is_set():
            progressed = False
            for arm, folder in (("left", "bridge"), ("right", "bridge_right")):
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
                        self.journal.add("tool_call", command, arm=arm, arguments=arguments)
                        result = self.backend.command(arm, command, arguments)
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

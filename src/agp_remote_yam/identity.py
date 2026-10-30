"""Method and runner attribution required by the integration harness."""
import math
import re
import time

APPROACH = "Agent as Policy"


def runner_identity(value, *, automated_default=False):
    if value is None and automated_default:
        value = {"kind": "automated", "name": "Automated"}
    if not isinstance(value, dict):
        raise ValueError("Confirm your name and email before joining")
    if value.get("kind") == "automated":
        if value.get("email"):
            raise ValueError("Automated runs must not invent a person's email")
        return {"kind": "automated", "name": "Automated", "email": None}
    name, email = value.get("name", ""), value.get("email", "")
    if not isinstance(name, str) or not 1 <= len(name.strip()) <= 160:
        raise ValueError("Enter your name")
    if not isinstance(email, str) or len(email) > 254 or not re.fullmatch(r"[^\s@]+@[^\s@]+\.[^\s@]+", email.strip()):
        raise ValueError("Enter a valid email")
    return {"kind": "human", "name": name.strip(), "email": email.strip()}


def run_timing(value):
    result = {"server_received_at": time.time(), "first_measured_motion_at": None,
              "run_to_motion_s": None, "entry_to_motion_s": None, "outcome": "unverified"}
    if value is not None:
        if not isinstance(value, dict):
            raise ValueError("Invalid browser timing")
        for key in ("page_entered_at", "run_clicked_at"):
            item = value.get(key)
            if isinstance(item, bool) or not isinstance(item, (int, float)) or not math.isfinite(item):
                raise ValueError("Invalid browser timing")
            result[key] = item
        if result["run_clicked_at"] < result["page_entered_at"]:
            raise ValueError("Run click precedes page entry")
    result["clock_basis"] = "Browser timestamps and server arrival; verify against retained visual evidence"
    return result

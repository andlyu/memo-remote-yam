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


def measured_timing(timing, first):
    result = dict(timing)
    result.update(first_measured_motion_at=first["time"],
                  server_receive_to_motion_s=first["time"]-result["server_received_at"],
                  outcome="measured_motion_visual_timing_unverified")
    if "run_clicked_at" in result:
        result.update(run_to_motion_s=first["time"]-result["run_clicked_at"],
                      entry_to_motion_s=first["time"]-result["page_entered_at"])
    home = result.get('home_completed_at')
    if home is not None:
        result['home_to_measured_completion_s'] = first['time'] - home
        run_elapsed = result.get('run_to_motion_s')
        result['measured_completion_within_limits'] = (
            0 <= result['home_to_measured_completion_s'] <= 15 and
            run_elapsed is not None and 0 <= run_elapsed <= 30)
    return result


def with_home_evidence(timing, events, directory):
    """Use startup's matched sample, including retained historical controller logs."""
    import json
    result = dict(timing)
    samples = [e.get('observed_at') for e in events if e.get('kind') == 'home_completed']
    if not samples and 'home_completed_at' not in result:
        for path in (directory / 'recording').glob('run_*/interactions.jsonl'):
            with path.open() as source:
                for line in source:
                    event = json.loads(line)
                    detail = event.get('details', {})
                    sample = detail.get('completion', {})
                    if (event.get('kind') == 'feedback_check' and detail.get('decision') == 'ready'
                            and sample.get('step_id') == 0 and sample.get('homed') is True
                            and sample.get('settled') is True):
                        samples.append(sample.get('observed_at'))
                        break
    valid = [v for v in samples if type(v) in (int, float) and math.isfinite(v) and v > 0]
    if valid:
        result['home_completed_at'] = min(valid)
        result['home_evidence'] = 'Matched settled startup Home feedback; corroborate with footage'
    return result

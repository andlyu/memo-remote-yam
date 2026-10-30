"""Standard-library client for the host's MEMO bridge. Robot client is unchanged."""
import json
from pathlib import Path
import sys
import time


def main():
    folder = Path("bridge_memo")
    command = sys.argv[1] if len(sys.argv) > 1 else "context"
    args = json.loads(sys.argv[2]) if len(sys.argv) > 2 else {}
    seq = max([0] + [int(p.stem[4:]) for p in folder.glob("req_*.json")]) + 1
    request = folder / f"req_{seq:06d}.json"
    temp = request.with_suffix(".tmp")
    temp.write_text(json.dumps(dict(id=seq, cmd=command, args=args)))
    temp.replace(request)
    deadline = time.monotonic() + 120
    response = folder / f"resp_{seq:06d}.json"
    while time.monotonic() < deadline:
        if response.exists():
            result = json.loads(response.read_text())
            print(json.dumps(result))
            return 0 if result.get("ok") else 1
        time.sleep(.05)
    print(json.dumps(dict(ok=False, error="MEMO response timed out; no robot motion was submitted")))
    return 1


if __name__ == "__main__":
    sys.exit(main())

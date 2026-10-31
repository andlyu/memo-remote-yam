# Hosting the separate MEMO website

Serve this repository on its own origin and run it under a dedicated system
user, virtual environment, rootless container storage, broker socket, operator
configuration and data directory. Do not replace the AgP or Playground service.

Production command (behind HTTPS):

```sh
python -m agp_remote_yam --memo-site --host 127.0.0.1 --port 8831 \
  --data /var/lib/memo-remote-yam --agent remote --model gpt-6-luna \
  --memory-encoder semantic --robot-id robot-ba8413962083809c
```

Check `python -m agp_remote_yam --help` for the current options. Preflight the rootless image with its production user namespace before accepting
traffic, so first-use filesystem preparation cannot occur during a visitor run.
The semantic encoder loads during server readiness. Persist the complete data directory:
owner-scoped skillbook revisions, corrections, run workspaces and recordings.
Human defaults stay in browser local storage; owner access uses a separate
HttpOnly `memo_visitor` cookie. Corrections and refinement require same-origin
ownership and are not shared between visitors.

Set `AGP_REMOTE_CODEX_CONFIG` to a trusted host-only JSON file with the rootless
engine, pinned image, model, allowed run root and private broker socket. The
executor receives only its workspace, a restricted environment and broker
connection. It never receives the normal model login or either site's data.
The broker runs as the authenticated account and accepts only the MEMO worker
UID. Pin native Codex0.159.0 and the matching public executor image. Use the
normal operator model authentication; do not copy credentials into this repo.

Give the worker write access only to its own data and rootless runtime. Permit
its public dependency path read-only and keep Remote YAM pinned and clean.
Retain queue, lease, calibration, contact, command validation and Stop behavior.
Verify actual inference against mock arms before any physical trial:

```sh
python scripts/verify_native_memo.py --data /path/to/isolated/verification-data
```

That script tests live-model correction delivery, generalized guidance and
parameterized templates, later-run semantic retrieval and offline consolidation.
It does not acquire a physical robot lease. A passing receipt is not physical
acceptance. Then verify the deployed normal UI, live cameras, physical execution,
retained replay, history, identity and both timing requirements using
[the completion checklist](COMPLETION-CHECKLIST.md).

Deploy immutable source revisions, report `AGP_SOURCE_REVISION`, validate the
new HTTPS proxy configuration before reload, and roll back only this site's
service and proxy entry. Do not restart unrelated integrations.

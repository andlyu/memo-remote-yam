# MEMO on Remote YAM

A standalone implementation of [MEMO: From Local Corrections to Generalized Skills](https://collab.me.vt.edu/memo/)
with a runtime coding policy controlling the public BluPe Remote YAM API.

- Website: https://memo.54.209.185.15.sslip.io/
- Source: https://github.com/andlyu/memo-remote-yam
- Acceptance evidence: [shared completion harness](docs/COMPLETION-CHECKLIST.md)

The coding agent observes the real scene, writes and executes Python, checks
measured results, and revises its program. Your corrections become generalized
guidance; verified subtask programs can become parameterized skill templates.
Later runs retrieve relevant lessons from the browser-owned skillbook.
Skills are agent-authored and remain unverified until independently reviewed.

The page includes editable name/email confirmation, explicit Automated test
identity, live cameras, corrections, retained physical replay, prior-run history,
generated source and measured timing. **Refine skillbook** consolidates related
lessons offline while preserving original source IDs and constraints. It creates
no robot session and rejects every robot command. Stop always targets the
active run even while you review a previous run.

## Run locally

Python3.11+ is required. Install the clean pinned public runner first:

```sh
python scripts/bootstrap.py
python -m pip install -e '.[memo,test]'
python -m agp_remote_yam --memo-site --memory-encoder semantic
```

The Python namespace `agp_remote_yam` is retained for compatibility with the
public adapter. The package, repository, website, service, visitor cookie,
robot workspaces, skillbook and broker configuration are independent of the
Agent as Policy website. This application never changes Playground.

Public hosting requires the isolated native worker. See [hosting](docs/HOSTING.md).
Model credentials stay in the broker account; generated code runs in a rootless
container with only its run workspace. No login, user home, engine socket or
server credentials are mounted into the executor.

## Explicit offline checks

```sh
python -m pytest -q
python -m agp_remote_yam --demo --synthetic-cameras --memory-encoder lexical
python -m agp_remote_yam --mock-robot --memo-site --memory-encoder semantic
```

`--demo` uses a scripted agent and mock robot. `--mock-robot` uses the actual
coding model with mock motion. Synthetic cameras need their explicit flag;
otherwise the website displays real public cameras independently of execution.
Neither mode establishes physical task success or a physical timing pass.

## Method and boundaries

[Method notes](docs/METHOD.md) describe correction delivery, semantic retrieval,
generalization, consolidation, provenance and the changes needed for YAM.
The authors' robot client is preserved unchanged with upstream attribution.
The separately installed Remote YAM dependency stays clean and pinned; its
queue, lease, calibrated geometry, contact checks and Stop remain authoritative.
A timed-out movement is never automatically replayed.

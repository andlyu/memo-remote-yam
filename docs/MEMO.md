# MEMO on Agent as Policy / Remote YAM

This independent implementation combines Agent as Policy's runtime coding loop
with MEMO's correction retrieval, successful-code generalization and offline
consolidation. It is an adaptation of the methods, not a reproduction of the
paper's Franka simulator or reported evaluation results.

References: [MEMO](https://collab.me.vt.edu/memo/),
[source revision d98cc8d](https://github.com/VT-Collab/memo/tree/d98cc8db145f429c8833a846d357395c935ddd3c).
No upstream MEMO code or pickle skillbook is vendored. The original AgP robot
client remains unmodified and attributed in NOTICE.

## Run

`./setup.sh` installs the semantic encoder. Launch `./run.sh`, select **MEMO**,
and submit a task. The default semantic encoder is MiniLM-L6-v2 at the exact
revision in dependency.lock.json. First use downloads public model weights.
For explicit offline fixtures use `--demo --synthetic-cameras --memory-encoder lexical`;
lexical hashing is labelled in every memory and is not semantic retrieval.

The agent identifies an atomic ACTION(object), observes the real scene, retrieves
guidance/templates with 0.75 action + 0.25 object/scene cosine similarity (semantic
threshold 0.8), then writes and executes Python. Owner corrections reach the
next state/camera observation or coding turn and are delivered once. Stop uses
the existing controller stop path. A correction is not an emergency stop.

After a subtask, the coding agent may save position-independent guidance and a
parameterized Python function with capture/code evidence. Templates are context
for subsequent coding, never automatically executed. Silence and packet
completion do not establish task success. All learned entries remain labelled
agent-authored/unverified; provenance records the source run, mode, hashes and
raw correction IDs. A mock lesson is not physical task evidence.

SQLite stores the append-only records and source corrections in
`data/skillbook.sqlite3`. Each run pins a retrieval revision. Consolidation adds
a new revision and supersedes source entries without deleting them; old run
snapshots remain reproducible. Standalone memory is private to its browser
capability; the shared Playground uses a separate opaque HttpOnly cookie so
memory survives visitor-session renewal without merging different browsers.
Clearing that cookie loses access to the corresponding private memory namespace.

## Offline consolidation

Find the owner namespace in the host-private run.json, then inspect clusters:

```sh
.venv/bin/python scripts/consolidate_memory.py --data data --namespace OWNER --dry-run
```

Remove `--dry-run` to ask the coding agent to rewrite redundant guidance/skills.
Candidate clusters use the same dual similarity score, threshold 0.8 and matching
memory kind. The maintenance worker has no robot backend, queue or lease. Raw
corrections and prior versions are retained. Do not accept another browser's
namespace through a public form.

## Verification

```sh
.venv/bin/python -m pytest -q
.venv/bin/python scripts/smoke_memo.py --memory-encoder semantic
```

The smoke uses real model inference against a mock robot: it learns a correction
and template, then retrieves them for a related task. It creates no physical
robot session and establishes neither manipulation success nor physical transfer.
Physical calibration, RGB-D availability and intervention performance require
their own deployment evidence.

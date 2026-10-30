# Startup latency debug report — 2026-10-30

- **Symptom:** Run did not promptly produce task-driven arm movement.
- **Root cause:** `Skillbook.retrieve` encoded queries before checking whether
  the owner/version/encoder scope had eligible memories. A fresh empty scope
  loaded the semantic encoder and took 28.856470 s. The MEMO instructions also
  forced a new native coding turn after initial inspection, discarding model
  conversation context. The reported physical run's first motion request was
  at +166.343 s and was correctly rejected by IK; no task-motion success was
  established. Queue/preparation and model/tool round trips are additional costs.
- **Fix:** Query eligible rows first and return immediately when empty. Supply
  the authoritative interface/MEMO protocols up front, and keep observation,
  programming, action and verification within the coding turn. State/frames/
  context still deliver corrections before subsequent moves. Preserve scoped
  memory retrieval, validation, queue, lease, Stop and no timeout replay.
- **Evidence:** Empty lookup on the host fell to 0.002124 s with encoder unloaded.
  Final suite: 60 passed in 10.59 s. Real Codex 0.159.0/rootless native-worker
  mock tests verified newly generated programs, measured +0.01-radian joint
  change and fresh mock images. Inline medium trial: first mock command
  completion24.376417 s; total30.829152 s. These are not physical timing passes.
- **Regression test:** `tests/test_memo.py::test_no_visible_memories_do_not_load_query_encoder`;
  three scoping cases failed before the fix and passed after it.
- **Related:** Existing native readiness/isolation and correction-history fixes.
  Lower reasoning was tested (28.267033 s first mock completion) and not adopted;
  model remains Astra medium. Do not infer a general latency comparison from
  one observation per configuration. No physical commands were sent by these
  benchmarks. The invalid physical IK target was not retried or bypassed.
- **Harness:** The shared BLUPE Remote Bots completion checklist is copied with
  a SHA-256 receipt into `docs/COMPLETION-CHECKLIST.md`, and linked by AGENTS.md
  and README.md. Review every criterion before a completion claim. Physical
  timing, join identity, retained video replay and final deployed physical
  end-to-end verification remain open requirements.
- **Status:** DONE_WITH_CONCERNS for the verified startup-bottleneck repair;
  the overall integration is incomplete and the15-second acceptance target is
  not met. This report does not declare physical task success.

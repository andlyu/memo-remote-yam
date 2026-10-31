# Standalone MEMO implementation

Status: native-model mock verification passed; deployment and physical
acceptance are pending. Do not interpret this report as completed acceptance.

Symptom: the previous combined site lacked a complete independently hosted MEMO
learning/reuse/refinement flow and physical replay/identity acceptance evidence.
The separate AgP site is now maintained independently and must be preserved.

Root causes: the old MEMO interface lagged the public identity/replay adapter;
memory requests were blocked until robot admission; a metadata read could
straddle completion; first-use rootless filesystem preparation outlasted the
leased-image handoff deadline. An incomplete copy of the public embedding cache
and overly narrow mock-service write paths also blocked deployment verification.

Fix: adapt public6e6c3ca into a separate MEMO application with its own worker UID,
rootless storage, broker/config, data, visitor cookie and origin. Keep corrections,
semantic retrieval, parameterized templates and offline consolidation; preserve
provenance and pinned revisions. Start only the memory bridge during queueing;
all robot admission/fresh-image gates remain. Refresh completed metadata after
checking active state. Preflight the rootless image and preload the semantic
encoder before public readiness. Add identity, retained replay, history and
persistent progress to the existing interface.

Regression evidence: the new tests initially failed on missing MEMO identity,
method enforcement and offline-only consolidation. The pre-admission retrieval
case failed against the base. The completed-metadata race failed before its fix.
The final99-test adapter suite passed in21.67s. JavaScript syntax and whitespace
checks passed. Local mock UI verified explicit synthetic labelling, completed
activity, history, disabled correction after completion and all four camera tiles.

Setup measurement: initial rootless container probe41.52s; identical warm
probe1.78s. These are startup measurements, not physical motion timing passes.
Native model tests use pinned Codex0.159.0, a private credential broker and a
rootless executor. The authors' client/dependency remain unchanged at
fb1aaa9a696ae4597d06aef41bf876bf2ec90e4d. No fixed movement is substituted for the
coding policy. Offline and mock runs do not establish physical task success.

Related: docs/METHOD.md, docs/HOSTING.md, docs/COMPLETION-CHECKLIST.md,
tests/test_memo_site.py, scripts/verify_native_memo.py.

Actual-model regression found the model submitting prose as template content;
syntax rejection was correct but not actionable. Clarified the literal-function
contract and safe JSON construction, retaining AST/parameter/coordinate checks.
The new rejected-template test failed before the error fix and passed after it.
The next real-model check saved both generalized guidance and a valid
parameterized Python function. Cross-run reuse and offline consolidation passed on the next actual-model check.
The proof run IDs are7d73e69efad24996954b0b06979a4f86 and
1023c8d983fc48b089aaf148edf9a66c; offline job1e8e2d69c88441c394f44f427e570483.
This was model=gpt-6-luna, semantic retrieval, mock-only execution with a10s
admission delay. First measured mock completion was19.78s and19.50s; these do
not establish a physical timing pass. No robot lease was acquired.

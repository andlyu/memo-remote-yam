# DEBUG REPORT — MEMO startup and action discovery

- Symptom: physical arm completion27s afterRun; later task failed to reuse saved lessons.
- Root cause: read-only telemetry and calibration/preview preparation were serialized around queue entry. Separately, initial GENERAL context did not reveal the action-specific lessons available to the model; it chose GENERAL and got no results.
- Fix: manager.py overlaps read-only planning/calibration with unchanged normal queue admission. memo.py context exposes only the owner's pinned-version action labels; MEMO.md directs relevant action retrieval. Original robot client/controller remain pinned and unchanged.
- Evidence: startup regression red2.26s then101 tests green22.72s. Catalog regression red0.17s then102 tests green21.61s. Actual native model mock tests passed correction learning, action-specific reuse of all saved entries and offline consolidation. Physical traces and source-linked details are in docs/COMPLETION-CHECKLIST.md.
- Regression tests: tests/test_startup_overlap.py and tests/test_memo.py::test_initial_context_exposes_owner_pinned_action_catalog.
- Related: retain fresh leased images and a new coding call after image acceptance; no fixed wiggle or action lookup. Never replay a timed-out movement. No changes to AgP/Playground services.
- Status: DONE_WITH_CONCERNS. Measured physical completion improved27.0→19.9s; both15s acceptance targets remain missed/unverified. Catalog deployment physically retrievedIDs2/1, executed one new program, learnedID3 and passed hosted offline refinement toIDs4/5. Latest measured completion29.666s afterRun; latency remains unresolved. Do not mark the integration complete.

# Research integration completion checklist

Agents and humans: read this before integrating a paper or method. Copy this
template into the integration's documentation, fill in the evidence, and check
each box only after verification. All boxes must be checked before declaring the
integration complete. Before the final handoff, review and update every item with
evidence. Report checklist status, evidence links, unmet items and explicit
exceptions; leave unfinished requirements unchecked and do not describe the
integration as complete.

## Completion requirements

- [ ] A usable website exists, with an associated repository containing the
  website's source code. Record both links and the deployed source revision.
- [x] The website and its source repository are public, unless an explicit
  public-visibility exception for either is recorded below.
- [ ] The website clearly names the actual approach/method being run. Use the
  executed method's name; Spotter is an example, not a shared hardcoded label.
- [ ] When a human joins, collect or confirm their name and email. Prefill known
  identity/default values where available and let the runner edit both fields
  before joining.
- [ ] Run context includes the actual approach and confirmed runner identity;
  the website makes clear which method is running and whose run it is.
- [ ] Automated test runs retain the actual approach name and explicitly label
  their runner as `Automated` or an equivalent clearly automated identity.
  They require no interactive human signup. Do not invent a person's email
  address for automated runs.
- [ ] A person can use the website to run the integrated paper's method on
  physical YAM robots/arms. Record a verified physical execution of that method.
- [ ] The actual physical arms are visible live on the website while the method
  runs, so a visitor can see that it is executing on real hardware.
- [ ] Immediately after a run finishes, the person can replay that just-completed
  physical YAM execution through the website, with retained footage showing the
  actual arms executing the integrated method.
- [ ] The person can browse/select previous runs on the website and replay their
  retained physical arm footage, associated with the executed method and run.
  Mock animations do not satisfy either replay requirement.
- [ ] The website is intuitive: a new visitor, without coaching, can find how to
  run the method and have the physical YAM arms actually executing it within
  **15 seconds of entering the website**, verified as described below.
- [ ] **Mandatory for every run:** after the person clicks Run, the physical YAM
  arms start actual method-driven motion within **15 seconds**, verified and
  recorded per run as described below. A sampled demonstration is insufficient.
- [ ] Before marking the integration complete or reporting it done, open the
  deployed website and perform a final end-to-end physical YAM run through its
  normal user interface. Verify every completion requirement against that
  deployment and record evidence; unmet or unverified requirements block
  completion.

## Verify the 15-second path

Time a visitor's full path. Start at initial navigation to the website (`t0`);
stop at the first observed physical arm motion executing the integrated method
(`t1`). Require `t1 - t0 <= 15 seconds`. Include page loading, finding the controls,
login/setup, queue/readiness waits and inference in the elapsed time; do not
restart the clock at Run. Queued, submitted, accepted or a UI "running" status
alone does not pass, nor does backend latency alone.

Include join-time name/email entry or confirmation in this same measurement.

Record the visitor's starting state and test conditions. Keep a timed screen
recording showing site entry, the visitor's actions and the live arms beginning
the method, linked to the matching physical run. If the elapsed time exceeds
15 seconds or physical motion is unverified, leave the box unchecked.

## Verify every Run click

This is an additional per-run measure; keep the site-entry test above. For every
run, start at the Run click (`t_run`) and stop at the first observed actual
method-driven physical arm motion (`t_motion`). Require
`t_motion - t_run <= 15 seconds`. An acknowledgement, accepted request, queued
status, submitted action or inference starting is insufficient.

Record every run below (add rows), including visual evidence of the click and
motion. Mark the outcome as pass, missed target, unverified or exception.
Exceptions are not fulfilled <=15-second runs. Each exception requires a specific
justification grounded in the integrated paper/research, explaining why it
applies to that run, plus a supporting source citation/link and relevant
section/page. Slow loading, queueing, setup or infrastructure delay is a missed
target, not in itself a paper/research-grounded exemption.

| Run reference | Run click (`t_run`) | First observed method-driven arm motion (`t_motion`) / visual evidence | Elapsed seconds | Outcome |
| --- | --- | --- | --- | --- |
| | | | | |

- Exception record (repeat for each affected run):
- Affected run reference:
- Specific paper/research-grounded reason and why it applies to this run:
- Supporting paper/research source (citation/link and relevant section/page):

## Final verification before completion

Open the deployed website and its associated source repository. Use the normal
visitor flow to join, run the integrated method on physical YAMs and watch the
actual arms live. Check both 15-second measures, approach/runner identities,
replay of the just-completed run and selection/replay of previous runs. Review
every checklist item against current evidence, including public visibility and
automated runner identity. Record the tested deployment, run and evidence below.
Leave unmet or unverified items unchecked and report gaps and explicit exceptions
before any completion claim.

## Integration and evidence

- Paper / method (link and version):
- Final verification (reviewer/date, tested website URL and deployed revision,
  physical run reference):
- Final checklist review (evidence for every item, replay links/timings, unmet
  items and explicit exceptions):
- Actual approach name / website label evidence:
- Human join evidence (name/email collection or confirmation, prefilled defaults
  and edits to both fields):
- Run context evidence (run ID, approach and runner identity; website attribution):
- Automated test evidence (run ID, approach, explicit automated runner label and
  non-interactive execution):
- Website URL:
- Website source repository URL / deployed revision:
- Public-visibility exceptions (write "none", or the affected website/repository,
  explicit exception, reason and approval reference):
- Physical execution (date, method/configuration, YAM station/arm IDs, run ID):
- Live physical arm footage (website location and evidence link):
- Just-completed replay URL / immediate availability evidence (same physical run):
- Previous-run browser URL / selected prior run and replay evidence:
- 15-second test (tester/date, browser/session/network and robot readiness):
- Visitor's starting state and entry-to-motion steps:
- `t0` / `t1` / total elapsed seconds:
- Timed screen recording / matching physical run evidence:
- Remaining gaps:


## Agent as Policy audit — 2026-10-30

The user rejected MEMO on the AgP website. This audit concerns pure **Agent as
Policy**, with explicit experience reuse and the authors' unchanged client.
MEMO remains a separate explicit application; legacy data is preserved.

- Shared template: `andlyu/blupe-remote-bots`,
  `codex-runner/integration-harness/COMPLETION-CHECKLIST.md`; copied 2026-10-30.
  Template SHA-256 `36895c5add8d81f02bd8cd42a2b213e52cd85292d76661cddd180cc0d61b9421`.
- Method: https://arxiv.org/abs/2609.12541 ; upstream source pinned in dependency.lock.json.
- Website: https://agp.54.209.185.15.sslip.io/
- Public source: https://github.com/andlyu/agp-remote-yam ; corrected deployment pending.
- Human join: editable name/email with browser autocomplete; confirmed browser
  values prefill on return. The AgP UI contains no MEMO controls.
- Attribution: run metadata and UI retain `Agent as Policy`, confirmed runner,
  station and timing. Public session creation forwards runner name and human
  email. Automated tests use `Automated`, `email:null`, no invented human identity.
- Isolation: default runtime creates no skillbook, memory channel, MEMO protocol,
  client or bridge. API rejects MEMO. Separate `--memo-site` retains that project.
- Offline tests: initial 69 passed in 13.48 s; station-selection regression pending.
- Actual model/mock station: `e1d01c1cf91344d98ad9fe9134434baa`, Codex 0.159.0,
  Astra medium, actual generated `scratch/transport_test.py`, exactly one +0.01
  rad relative joint change verified by fresh measured state and images.
  Final outcome `done`; no physical robot/session. First mock completion
  24.8987 s, observer receipt at 29.942 s. Initial receipt raced cleanup; final
  persisted run record independently verified. No physical timing pass claimed.
- Replay implementation: actual public camera atlas captured with ffmpeg;
  owner-scoped MP4 replay with byte-range support, associated with the run.
  Missing/invalid footage is explicitly unavailable, never synthesized.
  Physical capture and normal UI replay acceptance remain pending.
- Readiness at 23:02 UTC: YAM-1 public station disconnected, direct SSH timed out
  (5.014 s), existing operator tunnel status timed out (20.029 s), camera stream
  returned404 using the correct Origin header. RoboHouse station connected;
  control harness status succeeded in0.763 s, parked, torque off, queue enabled.
  RoboHouse public HLS playlist returned200. A station selector exposes both.
- Public-visibility exceptions: none. Research-based timing exceptions: none.
- Legacy combined/MEMO evidence: [historical audit](LEGACY-COMBINED-AUDIT.md).

### Per-run physical acceptance

No physical run has been submitted during this repair yet. A real model with a
mock station does not satisfy motion, live execution or replay requirements.
Browser click/server timing is recorded per run; a matched physical feedback
change is retained separately, without treating an ACK or queue state as motion.
Timed visual evidence remains necessary to check either15-second criterion.

### Final deployed review

Pending corrected release and browser verification. Unverified requirements
remain unchecked; do not call this integration complete.

### Live acceptance attempt 1

- Tested application `91f1ed2`, run `b7dabdb16c83459dbd72052a6c73bc70`,
  Agent as Policy / Automated / RoboHouse YAM. Normal browser Run clicked
  2026-10-30T23:08:30.629Z (server arrival23:08:30.698Z).
- The adapter raised `KeyError: native_joint_calibration` before agent startup
  or any method trajectory. This is a failed physical execution, never a pass.
  No timed-out motion was retried. Its actual camera footage was retained
  (14.7 s,523461 bytes); footage alone does not establish AgP execution.
- Every-click result: no verified method motion, missed/unverified target.
  Entry-to-click itself exceeded15 s; entry-to-motion cannot pass.
- Correction: support the pinned public dependency's explicit RoboHouse
  `original_i2rt_model_corrected` binding, validating its exact calibration ID,
  canonical model hash, twelve offsets and base spacing. Native and corrected
  bindings cannot be mixed. No zero-offset fallback or guard bypass.
- Read-only preflight: live RoboHouse calibration
  `40a9220259748447f0564404fbc0aa40e236786182992895cef9ee0e51f88f11`,
  maximum FK difference3.3306690738754696e-16 from its published zero pose,
  measured6-joint state and fresh top/wrist RGB capture verified. No lease/motion.
- Adapter regressions:76 passed in14.12 s, including contradictory/missing
  calibration rejection and preservation of encoder command coordinates.
- Corrected physical execution/replay acceptance still pending.

# Research integration completion checklist

Agents and humans: read this before integrating a paper or method. Copy this
template into the integration's documentation, fill in the evidence, and check
each box only after verification. All boxes must be checked before declaring the
integration complete. Before the final handoff, review and update every item with
evidence. Report checklist status, evidence links, unmet items and explicit
exceptions; leave unfinished requirements unchecked and do not describe the
integration as complete.

## Completion requirements

- [x] A usable website exists, with an associated repository containing the
  website's source code. Record both links and the deployed source revision.
- [x] The website and its source repository are public, unless an explicit
  public-visibility exception for either is recorded below.
- [x] The website clearly names the actual approach/method being run. Use the
  executed method's name; Spotter is an example, not a shared hardcoded label.
- [x] When a human joins, collect or confirm their name and email. Prefill known
  identity/default values where available and let the runner edit both fields
  before joining.
- [x] Run context includes the actual approach and confirmed runner identity;
  the website makes clear which method is running and whose run it is.
- [x] Automated test runs retain the actual approach name and explicitly label
  their runner as `Automated` or an equivalent clearly automated identity.
  They require no interactive human signup. Do not invent a person's email
  address for automated runs.
- [x] A person can use the website to run the integrated paper's method on
  physical YAM robots/arms. Record a verified physical execution of that method.
- [x] The actual physical arms are visible live on the website while the method
  runs, so a visitor can see that it is executing on real hardware.
- [x] Immediately after a run finishes, the person can replay that just-completed
  physical YAM execution through the website, with retained footage showing the
  actual arms executing the integrated method.
- [x] The person can browse/select previous runs on the website and replay their
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
- Public source: https://github.com/andlyu/agp-remote-yam ; physical-tested deployment `d0531e1ab59ba07db09e1740dfb38c3ca958bd47`; final serving revision is exposed by `/api/config.source_revision` and recorded in the deployment receipt.
- Human join: editable name/email with browser autocomplete; confirmed browser
  values prefill on return. The AgP UI contains no MEMO controls.
- Attribution: run metadata and UI retain `Agent as Policy`, confirmed runner,
  station and timing. Public session creation forwards runner name and human
  email. Automated tests use `Automated`, `email:null`, no invented human identity.
- Isolation: default runtime creates no skillbook, memory channel, MEMO protocol,
  client or bridge. API rejects MEMO. Separate `--memo-site` retains that project.
- Offline tests: initial69 passed in13.48 s; current candidate85 passed in15.88 s, including station, isolation, pre-admission rejection and Stop regressions.
- Actual model/mock station: `e1d01c1cf91344d98ad9fe9134434baa`, Codex 0.159.0,
  Astra medium, actual generated `scratch/transport_test.py`, exactly one +0.01
  rad relative joint change verified by fresh measured state and images.
  Final outcome `done`; no physical robot/session. First mock completion
  24.8987 s, observer receipt at 29.942 s. Initial receipt raced cleanup; final
  persisted run record independently verified. No physical timing pass claimed.
- Replay implementation: actual public camera atlas captured with ffmpeg;
  owner-scoped MP4 replay with byte-range support, associated with the run.
  Missing/invalid footage is explicitly unavailable, never synthesized.
  Physical capture and normal UI replay are verified in attempts2 and3 below.
- Readiness at 23:02 UTC: YAM-1 public station disconnected, direct SSH timed out
  (5.014 s), existing operator tunnel status timed out (20.029 s), camera stream
  returned404 using the correct Origin header. RoboHouse station connected;
  control harness status succeeded in0.763 s, parked, torque off, queue enabled.
  RoboHouse public HLS playlist returned200. A station selector exposes both.
- Public-visibility exceptions: none. Research-based timing exceptions: none.
- Legacy combined/MEMO evidence: [historical audit](LEGACY-COMBINED-AUDIT.md).

### Per-run physical acceptance

The original pre-acceptance checkpoint had no physical run. That checkpoint is
superseded by the dated attempts below. A real model with a mock station does
not satisfy motion, live execution or replay requirements.
Browser click/server timing is recorded per run; a matched physical feedback
change is retained separately, without treating an ACK or queue state as motion.
Timed visual evidence remains necessary to check either15-second criterion.

### Final deployed review

Physical execution and replay are verified below. Both timing targets remain
missed on0616bcf; final all-gates verification of the next candidate is pending.
Unverified requirements remain unchecked; do not call this integration complete.

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

### Physical acceptance attempt 2 — verified execution, timing missed

- Normal deployed UI run `0090e3128d6c47718f0b9915b7240a4f`, source
  `d0531e1ab59ba07db09e1740dfb38c3ca958bd47`, RoboHouse YAM, actual Astra medium
  coding agent, runner `Automated`, email null. No MEMO workspace or runtime.
- Browser page entry23:11:23.3304Z; Run click23:11:34.516Z; server receipt
  23:11:34.586Z; generated trajectory requested23:12:25.422Z; matched measured
  physical completion23:12:26.961Z. The timestamp records completion, not
  independently annotated visual motion onset. Clock alignment is not claimed.
- Actual agent-generated `scratch/adjust_once.py` performed one +0.04 rad left
  joint-0 request from fresh state, preserving other targets and grippers.
  Measured joint0 changed−0.022698 to0.015068 rad (+0.037766 rad); measured
  other-joint drift≤0.000382 rad. Fresh post-motion RGB images were retained.
  This verifies a small physical AgP program-execution test, not manipulation
  benchmark performance or the paper's reported success rates.
- Run-to-measured-completion52.445 s; entry-to-completion63.631 s. No method
  trajectory was requested until≈50.835 s after server creation, so the15-second
  requirements are missed. No research-grounded exception is claimed.
- Timeline: queue/preparation≈11.2 s; coding agent started13.7 s; initial state
  and camera calls27.6–35.2 s; generated movement50.8 s; final agent result67.0 s.
  Model reasoning/observation and robot setup are measured contributors, not
  research-based exemptions. Medium reasoning is retained; official guidance
  recommends evaluating quality/latency before changing effort for code:
  https://developers.openai.com/api/docs/guides/deployment-checklist#set-up-reasoningeffort .
- Actual retained camera replay:67.7 s,2238628 bytes, same run/robot. Owner-scoped
  path `/api/runs/0090e3128d6c47718f0b9915b7240a4f/replay.mp4`. Normal website
  replay played successfully (0:34/1:07 visibly advancing). After reloading the
  website, the completed run can be selected from Your runs and replayed again.
- Evidence bundle from the repair chat: `physical-run-receipt.json`,
  `physical-attempt-2.mp4`, timestamped screen evidence and `replay-playing.png`.
  Local evidence is operator-owned; repository links do not publish room footage.
- Human interface: name/email are required, editable native fields; browser
  autocomplete plus confirmed local saved values provide known defaults. No
  identity is guessed for a new visitor. Automated UI bypasses human signup
  explicitly via `?automated=1`; metadata and the queue retain Automated.

| Run | Click | Actual method motion / evidence | Elapsed | Outcome |
| --- | --- | --- | --- | --- |
| `b7dabdb16c83459dbd72052a6c73bc70` |23:08:30.629Z|No agent trajectory; calibration adapter failed; real footage retained|No motion|Missed/unverified|
| `0090e3128d6c47718f0b9915b7240a4f` |23:11:34.516Z|Generated trajectory≈50.835 s after creation; measured completion52.445 s after click; actual live/replay footage|>15 s; visual onset not independently annotated|Missed target; physical execution verified|

### Current gate review

Website/source, method isolation, join identity, automated attribution, genuine
physical coding-agent execution, live actual arms and immediate/historical
retained replay have evidence. Both15-second requirements remain unchecked.
The final all-gates completion requirement remains unchecked because those
requirements failed; this integration is functional but **not harness-complete**.
No visibility exception or research-based timing exemption is asserted.

### Final UI/control review

- Completed runs say Agent finished; failed initialization says Failed. Elapsed
  waiting and measured movement-completion timing are explicit. The UI never
  represents queue admission, inference or camera playback as method motion.
- Direct selection: `/?run=0090e3128d6c47718f0b9915b7240a4f` within the owning
  browser. Replay is protected by the same ownership cookie.
- Run history does not detach Stop from an active robot session. Stop targets
  the actual active run even while reviewing an older completed run; it is
  labelled Stop active run in that state. Mock-only browser verification
  started a waiting run, selected older history, then stopped the active run;
  controls returned to idle and the worker was reaped.
- Focused identity/ownership/active-state regressions:18 passed in8.57 s. The
  full adapter suite previously passed76 tests in14.12 s after the calibration
  correction. Actual model/mock and physical receipts remain distinct.
- Design review preserved BluPe colors/layout and corrected small low-contrast
  support text. The hidden upload preview has no image until the user selects
  a file; it is not a shipped broken image. Existing font identity is retained.

Remaining: both15-second physical-motion targets, with no research-grounded
exemption; the all-gates completion box therefore remains unchecked. A usable
physical AgP integration and passing software tests do not erase those misses.

- Legacy method isolation: old MEMO/unknown-method records are rejected by AgP detail, file/replay and experience-seeding ownership checks, while preserved on disk for their separate application. This prevents direct legacy links from mislabelling a MEMO run as AgP.

- Final full adapter suite:77 passed in14.24 s, including strict legacy-method isolation, identity, Stop ownership, real-client protocol, calibrated geometry and replay access/ranges.

### Latency acceptance attempt 3 — execution verified, target missed

- Source0616bcf986150ab00f134ea3ce07d15681657b89, normal deployed UI,
  RoboHouse, Automated/no email, genuine Astra low/Fast coding agent.
  Run `e41fab37c2074200b01f604523cf8827`.
- Browser entry00:49:37.3591 UTC October31 (October30 PDT), click00:49:37.843.
  Host screen recording marks differ by≤31 ms from page event timestamps and
  retain actual frame-capture bounds. Entry-to-click0.484 s.
- First generated trajectory requested25.398 s after server creation; matched
  physical completion27.303 s after click,27.787 s after entry. Both15-second
  targets are missed; Home/queue activity is not counted as AgP movement.
- The agent observed the pre-admission images, read fresh leased state and
  requested fresh views when homing changed the pose. Its generated
  `scratch/execute_step.py` made one +0.04 rad left-joint-0 request, never retried.
  Fresh measured delta+0.038148 rad; other left drift≤0.000382 rad, right
  drift≤0.000763 rad. Targets and grippers were preserved, with measured right
  gripper variation−0.000716. Fresh post-motion RGB was inspected.
- Timing stages: initial observations6.591 s; native thread ready9.421 s;
  robot running10.362 s; fresh views16.944 s; new generated move25.398 s.
  This remains a missed target, not a research exception.
- Actual replay37.0 s/1173669 bytes; normal UI playback verified visibly
  advancing at0:12/0:37. New run is selectable in history. Evidence:
  physical-1-receipt.json, physical-1-entry-and-run.mp4 and timestamp sidecar,
  physical-1-robot-replay.mp4, physical-1-replay-playing.png in this chat's bundle.
- Subsequent candidate work removes recorder re-encoding (source H.264 copy
  validated at2560×1080/8 fps), decouples uncalibrated read-only scene previews
  from fresh robot geometry preparation, and supplies a concise Python wrapper
  around the unchanged authors' CLI. A new physical acceptance is still needed.

### Latency acceptance attempt 4 — further improvement, target still missed

- Sourceedb6554b3f6516de4b25428da352d470cd2bc1d3; normal UI run
  `71f3ea8c3b2b4955a10bbde4a7573b0f`, Agent as Policy / Automated / RoboHouse.
- Entry01:06:01.7479 UTC October31; Run01:06:03.693. First generated trajectory
  requested19.357 s after server creation; measured physical completion21.187 s
  after click and23.132 s after entry. Both targets missed; no exception claimed.
- The runtime agent's generated `scratch/step.py` made one relative+0.04 rad
  request. Fresh measured delta+0.03815 rad; other joint variation≤0.000763 rad;
  no gripper commands. Fresh RGB was inspected before and after movement.
- Read-only preparation images3.224 s, native thread5.970 s, leased running
  11.105 s, fresh post-homing views13.142 s, generated trajectory19.357 s.
- Source-copy physical replay retained28.125 s/2318234 bytes. Source video
  preserved rather than re-encoded. Timed browser recording includes entry,
  click and the full actual execution; receipts, programs and footage retained.
- A preceding recording-script attempt misread an accessibility diff and stopped
  before clicking Run. No run/session was submitted by that attempt; it is an
  instrumentation failure, not a physical pass or a hidden motion retry.
- Next candidate uses explicit post-homing image inspection, drafts candidate
  programs during admission, and exposes image-tool completion evidence. Human
  entry timing remains pending confirmed name/email; automation never invents it.

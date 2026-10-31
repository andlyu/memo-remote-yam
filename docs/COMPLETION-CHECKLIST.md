# Research integration completion checklist

Agents and humans: read this before integrating a paper or method. Copy this
template into the integration's documentation, fill in the evidence, and check
each box only after verification. All boxes must be checked before declaring the
integration complete. Before the final handoff, review and update every item with
evidence. Report checklist status, evidence links, unmet items and explicit
exceptions; leave unfinished requirements unchecked and do not describe the
integration as complete.

## Purpose and public visibility by default

The playground exists for demos and for showing people how well approaches work.
Everything in the playground demo is **public by default**: the website, source
repository, approach/configuration descriptions, runs and results, live demos,
recordings, replays/history, simulation outputs, and supporting demo evidence.

Publish these demo materials so people can inspect the actual behavior and
results. This is the standing visibility default; an additional routine
confirmation is not required. Only an explicit user instruction or user visibility
change overrides it, for the scope the user specifies. Respect that change and
record the affected materials and instruction below. An existing private setting
alone does not establish a user-requested exception.

Keep credentials, access tokens and private contact details out of public demo
materials.

## Standing authorization for physical playground tests

### Authorization granted by using this harness

The owner defines use of this harness as a task-scoped authorization grant.
When the user requests a research integration, playground fix or verification
through this harness, that invocation authorizes the agent to carry out the
covered workflow below. A task requested under user-adopted instructions that
select this harness also counts: retain the task request and the selecting
instruction as the invocation evidence. Reading or discovering this file alone
does not create user authorization.

For that requested task, using the harness authorizes:

- Joining the normal robot queue and submitting the runner's already-confirmed
  name and email to the task's integration website and its existing BluPe
  queue/run backend for queue admission, run attribution and normal run
  notifications.
- Starting the selected method on the task's physical robots/arms and performing
  bounded actual arm movement within the existing run limits.
- Capturing and retaining camera recordings, checking live footage and
  replay/history, and using Stop and normal parking/lease release.

These actions are part of the invoked workflow. Do not ask for separate
permission for each covered identity submission, run, movement or recording.
Reuse confirmed identity/defaults; ask only for missing or ambiguous identity
or scope outside this contract. Keep execution mode separate from human
identity. The grant covers the task's integration and existing queue/run
destinations, not unrelated recipients or publication of private email.
Do not invent a person's name or email. Preserve any explicit user limits or
revocation and copy this contract into the integration's checklist.

### Make the invocation and scope visible before approval review

At task start, read the target repository's `AGENTS.md` and its integration copy
of this checklist, even when the chat starts outside the repository. Repository
and global `AGENTS.md` entries should route the workflow to this contract; keep
the permission grant here rather than adding an independent global permission.
A checklist link alone does not load the instructions. Verify that changed
global discovery instructions have loaded into the chat; start a fresh session
if needed.

Before a physical test, give a brief progress notice citing the user's harness
invocation and this contract. Name the website and queue/run backend origins,
robot/station and arms, method/task, run duration, expected motion,
recording/replay destination and confirmed identity fields being submitted.
State that the invocation covers these scoped side effects. This is a notice,
not a new confirmation step; proceed without waiting for a reply.

For an action requiring tool approval, repeat the invocation, contract and
concrete scope in the escalation justification or the tool's supported approval
context. Include the user request/selecting instruction and the contract's source
path/heading or commit URL with the applicable wording; do not supply only a link.
The reviewer sees a compact transcript and the exact request, so do not rely on
hidden reasoning, an earlier chat, or an unread repository file. Fill this example
with the actual scope before the first approval request:

```text
User invocation: <task request; adopted instruction selecting the harness, if used>.
Harness contract: <source path/heading or commit URL and applicable wording>.
That invocation authorizes this task's queue entry and confirmed runner
name/email submission, bounded physical motion, and camera recording/replay.
Action: <UI control or supported API operation>; site <origin>;
queue/run backend <origin>; station/arms <IDs>; method/task <name>;
duration <seconds>; motion <bounded behavior>; recording/replay <destination>.
Identity: <confirmed fields submitted to those operational destinations>.
Execution mode: <mode>, separate from human identity.
Safeguards: existing queue/lease, readiness, validation, hardware limits, Stop
and normal parking/release remain enabled; no automatic timed-out-motion retry.
```

Use the normal playground UI or its supported run API with existing queue/lease,
readiness, command validation, hardware limits and Stop behavior intact. Keep
tests within the task's robots, method and existing run limits, respect other
users' active runs, and never automatically retry a timed-out movement. This
contract does not authorize unrelated robots or disabling safeguards.

Harness invocation does not override enforced sandbox, managed-policy or tool
permissions. Use the normal permission mechanism when required. If automatic
approval review explicitly denies an action, do not retry it through another
route. Report the exact denied action and stated reason, acknowledge the
invocation and contract already present, and leave physical verification
unverified. Continue independent work or a materially safer alternative;
otherwise request only the specific unblock. A documentation update alone does
not authorize retrying an already-denied action. Keep sandbox and reviewer
policy intact.

References: [Codex instruction discovery](https://learn.chatgpt.com/docs/agent-configuration/agents-md#how-codex-discovers-guidance)
and [Auto-review context and denials](https://learn.chatgpt.com/docs/sandboxing/auto-review).

## Completion requirements

- [x] A usable website exists, with an associated repository containing the
  website's source code. Record both links and the deployed source revision.
- [x] Everything in the playground demo is public by default, including the
  website, source repository, runs/results, live demos, recordings, replays/history,
  simulation outputs and supporting evidence. Any nonpublic exception reflects
  an explicit user instruction or visibility change, recorded below.
- [x] The website clearly names the actual approach/method being run. Use the
  executed method's name; Spotter is an example, not a shared hardcoded label.
  The **Model** field identifies the approach being tested, as specified below.
- [x] When a human joins, collect or confirm their name and email. Prefill known
  identity/default values where available and let the runner edit both fields
  before joining.
- [x] Run context includes the actual approach and confirmed runner identity;
  the website makes clear which method is running and whose run it is.
- [x] Policy/model tests initiated by a person retain that actual user's
  confirmed name as runner. Use available identity and editable name/email
  defaults; require the real name to be provided/confirmed if missing before
  testing or running. Do not substitute `Anonymous`, `Autonomous` or `Automated`
  for that person. Record execution mode (such as `automated test`) and actual
  approach separately from human identity. Genuinely unattended/system activity
  has an explicit system identity; never fabricate a person's name or email.
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
- [x] If the integrated method executes anything in simulation, those executions
  are reviewable within the integration website and tied to the corresponding
  run. A reviewer can inspect what ran and its results using suitable
  replay/visualization and relevant outputs, as appropriate to the simulation.
  Clearly label simulation content to distinguish it from physical-arm footage.
  If nothing executes in simulation, record an explicit not-applicable
  explanation instead of claiming simulation review.
- [x] The website is intuitive: a new visitor, without coaching, can find how to
  run the method. Record the visitor path and starting conditions; site entry
  has no separate 15-second pass/fail deadline.
- [ ] **Mandatory for every run:** first observed actual method-driven physical
  YAM motion occurs both within **15 seconds after the startup move to Home
  completes** and within **30 seconds after the Run click**, using the boundaries
  below (including a documented readiness timestamp when Home is unnecessary).
  Homing/preparation motion does not count. Verify and record both full elapsed
  times for every run; a sampled demonstration is insufficient. Apply only the
  documented GPU-launch or research-grounded exceptions below.
- [x] Every meaningful wait after a website action is immediately explained in
  a persistent inline status/progress area at that action (below Run in the run
  panel for launches). Show the current stage, a plain-language reason and real
  stage completion, with honest failure/stall status and available recovery.
  Verify the detailed wait-stage behavior below.
- [x] Every advertised control primitive passes the real parser/generator/serializer/canonical-validator command contract, including measured fractional starts, numeric endpoints, invalid input and zero-dispatch tests; required CI/release evidence retained.
- [ ] Representative physical task matches advertised manipulation: approach/grasp/lift/place/release/withdrawal and fresh object-result evidence on the tested deployment; smoke motion alone is insufficient.
- [ ] Before marking the integration complete or reporting it done, open the
  deployed website and perform a final end-to-end physical YAM run through its
  normal user interface. Verify every completion requirement against that
  deployment and record evidence; unmet or unverified requirements block
  completion.

## Model identifies the tested approach

Set the harness's **Model** field to the actual research approach/method being
tested. For example, a HarnessVLA run uses `HarnessVLA` as its Model value.
Resolve this value from the approach that actually executes and carry it
consistently through the website's model label/selection, run context and stored
run records, queue/email notifications, and replay/history attribution.

Record underlying foundation, planner or VLA model IDs and checkpoint names as
separate configuration metadata. Keep confirmed human runner identity and
execution mode in their own fields too.

Verify a run's Model value against the executed approach and retain evidence of
the website label, stored run record, notification and replay/history attribution.

## Verify the visitor path

Record initial navigation (`t_entry`), the visitor's starting state and test
conditions, including browser/session/network, identity entry or confirmation,
queue and robot readiness. Keep the website usable without coaching. Site entry
is contextual evidence, not a separate timed pass/fail gate.

Keep a timed screen recording showing the visitor's actions, the Run click,
startup Home completion (or no-Home readiness) and live physical arms beginning
the integrated method, linked to the matching run. Correlate recorded UI/physical
events with lifecycle logs on a common timeline; document any clock offset or
measurement uncertainty. Backend timing alone cannot verify physical onset.

## Verify every Run and startup Home

For every run, record these fixed boundaries:

- `t_run`: the actual Run click, including any subsequent queue, preparation,
  coding, model loading or inference time. Do not restart this clock at admission,
  acknowledgement, dispatch, GPU readiness or a later status change.
- `t_home`: completion of that run's startup move to Home, using matched
  settled/ready completion for all participating arms, corroborated by live
  footage. Starting/submitting Home or reporting it accepted is insufficient.
  If no Home movement is necessary, record why and use the earliest documented
  per-run robot-ready confirmation after Run and normal queue/lease admission,
  before method preparation/execution. If already admitted and robot-ready at
  Run, use `t_home = t_run` with that readiness evidence. Readiness here concerns
  the robot, not GPU/model/code availability. Do not choose an arbitrary later
  event, repeat Home, or delay the readiness timestamp to reset this clock.
- `t_motion`: first observed actual physical arm motion executing the integrated
  method. Home and other preparation/parking motion do not count. An accepted or
  queued request, submitted packet, UI "running" status, inference start or
  backend-only timestamp is insufficient.

Ordinary runs must satisfy **both** `t_motion - t_home <= 15 seconds` and
`t_motion - t_run <= 30 seconds`. Retain full Run-to-motion and post-Home-to-motion
elapsed times even for failures and exceptions. Missing visual evidence or an
unmatched Home/readiness boundary makes the timing unverified.

Record every run below (add rows), with visual evidence of Run and physical
onset plus matched Home/readiness evidence. Mark each timing outcome as pass,
missed target, unverified or exception. A normal pass requires both full elapsed
times within target; an exception is never a passed normal 30-second run.

### GPU-launch exception

A run genuinely requiring new GPU launch/provisioning (for example on RunPod)
may claim an exception only for the evidenced time that launch blocks progress.
Show the **entire launch period** in persistent inline UI: actual launch start,
ongoing launch reason/stage and actual GPU-ready completion, with matching
provider/instance/job lifecycle evidence. If launch starts before Run, retain its
full start/ready interval and show its ongoing state when the run panel opens.
Warm/already available GPUs do not qualify. Record why a new GPU was necessary.

Keep the original clocks and full elapsed times. Record `t_gpu_start`,
`t_gpu_ready`, the full launch duration, and the evidenced GPU-launch blocking
seconds overlapping each measured interval (`B_run` and `B_home`). Only blocking
time inside both the actual launch interval and the relevant Run/Home-to-motion
interval can be excused; do not deduct concurrent time spent on unrelated work.
For a GPU exception, require `t_motion - t_run - B_run <= 30 seconds` and
`t_motion - t_home - B_home <= 15 seconds`, while labeling any full-time target
miss caused by launch as **exception**, not normal pass. If GPU readiness
precedes Home completion, `B_home = 0`: the full 15-second post-Home target still
applies. If Home completes during launch, only its evidenced remaining launch
blocking time can be excused; do not silently restart either clock at GPU ready.
Missing lifecycle or persistent UI evidence leaves the exception unverified.

Queueing, coding, model loading, inference, setup and other infrastructure delays
outside actual GPU provisioning remain in their respective clocks. A warm GPU,
a generic "loading" message or a slow model call is not a launch exception.
Unrelated delays remain missed targets if they exceed the remaining limits.

Other exceptions require a specific justification grounded in the integrated
paper/research, explaining why it applies to that run and which target it affects,
plus a supporting source citation/link and relevant section/page. Slow coding,
loading, queueing, setup or infrastructure delay is not in itself a
paper/research-grounded exemption; there is no permanent coding exemption.

| Run reference | Run click (`t_run`) | Startup Home settled completion / no-Home readiness (`t_home`) and evidence | First observed method motion (`t_motion`) / visual evidence | Full Run-to-motion seconds | Full post-Home-to-motion seconds | Run / post-Home outcomes |
| --- | --- | --- | --- | --- | --- | --- |
| | | | | | | |

- Exception record (repeat for each affected run):
- Exception category (GPU launch or paper/research-grounded):
- Affected run reference and timing target(s):
- Specific reason and why it applies to this run:
- GPU-launch evidence (if applicable: provider, instance/job reference,
  `t_gpu_start`, `t_gpu_ready`, full launch seconds, lifecycle log/link and
  persistent inline UI evidence covering the entire launch period):
- GPU-launch blocking overlap evidence (`B_run`, `B_home`, non-launch elapsed
  times for both clocks and separate outcome for each target):
- Supporting paper/research source (for other exceptions: citation/link and
  relevant section/page):

## Visible progress while waiting

Use a compact persistent inline status area directly below Run in the existing
run panel; keep other meaningful waits beside their initiating control. Show the
current stage and why it is taking time immediately, keep it readable throughout
the wait, and visibly mark completed stages as actual lifecycle state advances.
A transient toast alone or a generic spinner is insufficient.

When a model requires a new GPU, show only the stages that actually exist:
`Starting GPU` / "We're launching a GPU on RunPod for this model" -> `GPU ready`
-> `Loading model` -> `Running`. GPU startup must be explicit from its actual
launch start and throughout the launch period (immediately after Run when Run
initiates it); visibly confirm actual GPU readiness before subsequent
loading/running and retain completed-stage confirmation with start/ready
timestamps tied to lifecycle evidence. Use the applicable provider/model wording.
On failure or a stalled stage, state the known condition honestly and show an
available recovery action, such as retry or cancel where supported. Do not invent
percentages, ETA or completion, or expose irrelevant infrastructure internals.
UI transparency alone grants no exemption; only the documented GPU-launch
blocking interval qualifies under the exception above, with neither clock reset.

## Final verification before completion

Open the deployed website and its associated source repository. Use the normal
visitor flow to join, run the integrated method on physical YAMs and watch the
actual arms live. Check the 15-second post-Home and 30-second Run-to-motion
measures with fixed boundaries, full elapsed times and any evidenced GPU-launch
exception; site entry remains context only. Check approach/runner identities,
replay of the just-completed run and selection/replay of previous runs. Review
every checklist item against current evidence, including public visibility and
actual user attribution in policy/model tests, with execution mode separate.
Check the website, repository and each demo artifact type as a logged-out visitor;
record working public links or the explicit user-directed visibility exception.
Verify that Model identifies the executed approach consistently in the website,
run records, notifications and replay/history, with underlying model/checkpoint
configuration recorded separately.
Verify wait status appears immediately, keeps a readable reason, and visibly
confirms real stage completion (GPU ready before subsequent loading/running).
Check failure/stall status and available recovery evidence too. Record the
tested deployment, run and evidence below.
Leave unmet or unverified items unchecked and report gaps and explicit exceptions
before any completion claim.

## Integration and evidence

- Paper / method (link and version):
- Final verification (reviewer/date, tested website URL and deployed revision,
  physical run reference):
- Final checklist review (evidence for every item, replay links/timings, unmet
  items and explicit exceptions):
- Actual approach name / website label evidence:
- Model-as-approach evidence (executed approach, website Model value, stored run
  record, queue/email notification and replay/history attribution; separate
  underlying model/checkpoint configuration):
- Human join evidence (name/email collection or confirmation, prefilled defaults
  and edits to both fields):
- Run context evidence (run ID, approach and runner identity; website attribution):
- User-initiated test evidence (run ID, confirmed human runner, actual approach,
  separate execution mode; editable defaults and missing-name confirmation):
- Unattended/system activity evidence (explicit system identity, execution mode
  and actual approach; no fabricated person):
- Wait-status evidence (action/run reference, immediate inline visibility,
  ongoing stage/reason and real completion transitions):
- GPU-startup UI evidence (startup shown after Run, actual readiness confirmed
  before loading/running, completed stages and matching lifecycle evidence):
- Failure/stall status and available recovery evidence:
- Website URL:
- Website source repository URL / deployed revision:
- Public-default evidence (logged-out access checks and links for website,
  repository, runs/results, live demos, recordings, replay/history, simulation
  outputs and supporting demo evidence; explain any artifact type not produced):
- User-directed visibility exceptions (write "none", or affected materials/scope,
  current visibility, explicit user instruction/change, date and reference):
- Physical-test authorization/scope (source path/heading or commit URL, website
  and queue/run backend origins, station/arms, confirmed runner identity fields,
  method/task, duration, expected motion and recording/replay destination):
- Approval-context evidence (surfaced notice and escalation wording, applicable
  user invocation/selecting instruction and harness contract version/scope,
  review decision/rationale if required; redact private email from public evidence):
- Physical execution (date, method/configuration, YAM station/arm IDs, run ID):
- Live physical arm footage (website location and evidence link):
- Just-completed replay URL / immediate availability evidence (same physical run):
- Previous-run browser URL / selected prior run and replay evidence:
- Simulation review (corresponding run reference, website review link, what ran
  and its results, suitable replay/visualization/outputs, clear simulation label;
  or explicit not-applicable explanation if nothing executes in simulation):
- Per-run timing verification (tester/date, browser/session/network and robot
  readiness; evidence for every run in the timing table above):
- Visitor's starting state, `t_entry` and entry-to-motion steps (context only):
- `t_run` / `t_home` / `t_motion`, full Run-to-motion and post-Home-to-motion
  seconds, and separate target outcomes:
- Matched settled Home completion evidence for participating arms, or no-Home
  reason and earliest robot-ready timestamp/evidence (already ready: Run time):
- GPU launch start/ready/full interval and inline UI/lifecycle evidence, blocking
  overlap per clock and exception outcome if applicable (otherwise "none"):
- Timed screen recording / matching physical run evidence and clock correlation:
- Remaining gaps:



## Current contract and proportion — October30,2026

Updated shared contract1619d7f25190ed00c37da6006b3f16c4580eb166 (PR171).
The old site-entry/15s-after-Run gate below is historical. Current ordinary
limits are15s after matched settled Home completion AND30s afterRun; site entry
is contextual. All three retained hardware completion bounds fit these limits:
12.319/8.193/9.929s postHome and26.992/19.856/29.666s afterRun. Exact visual onset
correlation remains under review; no new timing pass is claimed from backend
evidence alone. Score currently10/15 (66.7%), pending current-code public demo,
Model attribution, wait/failure/recovery, visual timing and final checks. The
previous11/15 (73.3%) counted the older contract and is preserved historically.

## Historical MEMO evidence (older contract; preserved verbatim)

## MEMO implementation evidence — October30,2026

Independent repository: https://github.com/andlyu/memo-remote-yam .
Independent website: https://memo.54.209.185.15.sslip.io/ .
Public base adapter revision:6e6c3cab5797c4dece5183feef2966b0385b7424.
The AgP website and Playground are outside this deployment.

Current software evidence:100 adapter tests passed in25.12s. Actual native-model
verification passed on mock arms: learned two corrections as generalized guidance,
saved a parameterized Python skill template, retrieved lessons on a later task,
and consolidated related guidance offline with parent provenance. Model gpt-6-luna,
pinned semantic MiniLM encoder; Codex0.159.0 private broker/rootless executor.
Runs7d73e69efad24996954b0b06979a4f86 and1023c8d983fc48b089aaf148edf9a66c;
refinement1e8e2d69c88441c394f44f427e570483. Both are explicitly mock-only and
cannot establish physical motion, live footage, replay or timing acceptance.
A local scripted UI verified identity, history, all camera tiles and honest mock
labelling at desktop and390px. Deployed physical verification is pending.
Checkboxes remain unchecked until matching deployment evidence exists.

Exceptions: none claimed for physical task timing. Offline refinement has no
physical session and is a separate job, not a physical Run. Its research basis
is the MEMO project's overview describing offline skillbook clustering:
https://collab.me.vt.edu/memo/ .


## Deployed review — October30,2026 (03:03 UTC October31)

Website: https://memo.54.209.185.15.sslip.io/ . Public source:
https://github.com/andlyu/memo-remote-yam . Deployed source:
fbd1e86817f78b010f9180ad1c033677883a80bc. HTTPS/config returned200; actual approach
MEMO, native remote coding worker, semantic retrieval, physical_api mode,
RoboHouse stationrobot-ba8413962083809c. Both MEMO services are active. This deployment did not modify the AgP service
or replace Playground source/proxy routes.
Public-visibility exceptions: none.

Reviewed every requirement: website/source/public visibility/method label are
verified. Deployed live observer, overhead and wrist cameras show actual arms
and advancing real views. The 1280x720 layout now shows Run;390px mock layout
was also inspected. Editable name/email fields, browser defaults, distinct
human identity/automated verification mode, run context, corrections, history,
Stop and retained replay have adapter/mock coverage. The actual-model mock
check verifies learned guidance, real Python templates, semantic reuse and
source-preserving offline consolidation. These do not substitute for a deployed
physical execution, human join, live method execution or physical replay check.

Simulation review: not applicable to the deployed method; it executes no physics
simulation. Offline validation uses explicitly labelled mock arms/cameras and
retains model programs, events and measured mock results in its receipt. The
public website runs physical_api mode. Offline refinement has no robot session.

Physical test scope prepared: normal deployed UI, confirmed runner Andrew,
separate automated_test execution mode,60s limit, one fresh-state-derived
+0.04rad change to left joint0, retain all other targets, live and retained
camera footage. Existing queue, lease, validation and Stop remain enabled.
Before execution, automatic approval review rejected the UI action, stating
that trusted instructions did not specifically authorize the personal email
disclosure to the deployed site and the physical robot action. No form was
submitted, no MEMO run was created, and no robot command was sent. The specific
identity/physical-motion/recording approval is pending. The rejected action was
not retried through another route.

Remaining unchecked: deployed human join/attribution verification; physical
method execution; live method-driven arm movement; immediate and historical
physical replay; both15s timing requirements; deployed launch/stall/recovery
progress; final normal-UI physical run. No timing exception is claimed. There
are no physical Run-click rows because the requested test was blocked before
submission. Acknowledgement, mock motion and other integrations' movement are
not counted as MEMO physical evidence.


## Resumed deployed physical review — October30,2026 (04:59 UTC October31)

The user adopted the harness routing instructions and said “please proceed.”
The scoped normal-UI test then passed automatic review and ran. The earlier
approval refusal above is historical; it did not trigger an alternate route.
Invocation and concrete scope were surfaced before each subsequent UI test.
Confirmed Andrew name/email were submitted only to the MEMO origin and existing
BluPe backend stated above; private email is excluded from public evidence.
Human runner attribution is separate from automated_test execution mode.

Physical run86f7556492d143cb9c7d8bd2d563318b: one generated +.04rad relative
left joint0 target, fresh leased state/images and a new post-image coding step.
Measured delta+.0370031rad; all other targets retained. The model reported the
shortfall honestly, received two corrections, and saved one generalized guidance
and one parameterized Python template (skillbook v2). Normal parking/release;
no command retry. Actual camera atlas replay was immediately ready,55.125s,
4555648bytes. The same run was selected from Your runs after reload; the native
player reached55.125s without error. Its owned replay route is
/api/runs/86f7556492d143cb9c7d8bd2d563318b/replay.mp4 .

Physical run74d4fcd586b649c9a7c3eaf3a063b7e6: ae8661b startup-overlap fix; one
new -.015rad left joint0 target computed from fresh leased state, measured
delta-.0148775rad. Normal parking, no retry. Replay immediately ready37.125s,
3069601bytes at its matching /api/runs/<id>/replay.mp4 route. Actual model
queried GENERAL and retrieved no memories despite action-specific lessons;
this run establishes physical execution, not successful memory reuse.

Both physical timing targets were missed. Entry-to-measured-completion was
110.521s on the first run (page left open for setup) and21.960s on the second
(returning browser, saved editable identity, fresh navigation and task entry).
Second run has83 timed UI PNG captures across45.677s; the narrow default viewport
clips some camera views during scrolling. These are not an exact visual-onset
measurement. No GPU was launched and no research exception is claimed.

The first trace proved serial read-only telemetry preparation delayed admission.
The overlap regression failed before the fix and all101 tests passed afterwards
(22.72s). Native model mock verification also passed learning/reuse/refinement
with confirmed Andrew attribution. The physical recheck improved measured
completion from26.992s to19.856s, still above target. The controller record
shows9.28s between joined and first homed observation, followed by reconciled
safety feedback, fresh camera handoff and a new model decision. Read-only camera
profiling:2.587s total including backend construction,1.870s initial input,
1.261s RGB fetch. No safety gate or pinned controller was changed.

The empty GENERAL retrieval exposed a separate missing-discovery defect.
0fa07ea adds an owner/version-scoped available_actions catalog and instructs
the coding agent to choose a relevant action label. Regression red0.17s;
102 tests passed21.61s. Actual native model mock check passed action-specific
learning and retrieval of all three saved entries, then offline refinement
with source provenance. Mock runs9fcad42057914b2ea6c4d6e20088cf84 and
d28449262fc046aaa7cfe30725e37412; refinement99e2700dfb0f4498b7dc54507dbf5089.
These mock checks do not satisfy physical reuse or timing acceptance.

Reviewed every checkbox again: public separate website/source/method, actual
human attribution, physical method execution, live arm visibility, immediate
and historical replay have direct deployed evidence. Simulation remains N/A
(no physics simulation in the deployed method). Both15s criteria remain open.
Inline progress persists below Run and shows actual completed queue/scene/motion
stages; terminal outcome and timing appear there. Final current-revision physical
verification and failure/stall/recovery review remain open pending final check.
No completion claim is made.


## Final current-code review — October30,2026 (05:10 UTC October31)

Deployed source0fa07ea23c82fb4839092473853061a86c8b41d6, same public MEMO
origin and separate repository; public GitHub metadata confirms private=false.
All102 tests passed21.61s. No AgP/Playground changes or robot-client edits.
Source-linked sanitized results: [acceptance receipt](evidence/2026-10-30-physical.json).

Normal-UI physical run01fc10c00cbe44308247e7b5849b1e4b used confirmed Andrew,
human runner with separate automated_test mode; editable name/email defaults
were confirmed before queue entry.60s limit, RoboHouse, one freshly generated
+.02rad left joint0 target. Retrieved prior guidance/template IDs2/1, reviewed
fresh leased images before a new coding tool call, generated scratch/draft.py,
and executed once. Measured delta+.01831rad; remaining joint targets, other arm
and gripper targets retained. Correction delivered and generalized guidanceID3
saved. This bounded joint-adjustment smoke test is not a general manipulation
benchmark or a reproduction of the paper's simulated evaluations.

Actual arms were visible in all four live views. Continuous post-Run UI samples
were retained (84frames/45.447s main batch); native scrolling restored the camera
view after correction entry. A pre-Run keyboard-scroll automation failure
made the full entry path93.602s to measured completion. Run-to-measured-completion
was29.666s, with motion request already later than15s. Both targets missed;
exact visual onset remains unverified and no exception is claimed.

Immediately available physical replay48.125s/4006296bytes at
/api/runs/01fc10c00cbe44308247e7b5849b1e4b/replay.mp4 played0.0767→2.8906s
with paused=false/error=null. On this current deployment, selecting the first
physical run from Your runs and playing its55.125s clip advanced0.085→2.3522s,
error=null and matching source URL. The final view selected the newest run.

Refine skillbook was then run through the deployed UI, with persistent offline
status and Cancel refinement available. Job e600f299f4ca4ce7bb0476f090e3a8da
completed in27.926s in offline_memory mode, without a robot controller/session.
New guidanceID4 preserves parents[1,3]; rewritten parameterized templateID5
preserves parent[2]. Old versions and raw corrections remain. The site shows
skillbook v5/two current entries; the physical run still pins v2. Rewritten
templates remain agent-authored/unverified, not new physical validation.

Every requirement was reviewed:11 checked,4 unchecked. Open requirements are
entry-to-observed-motion≤15s, every Run-to-observed-motion≤15s, comprehensive
deployed failure/stall/recovery verification, and overall final acceptance
because those requirements remain unmet. Inline submitting/queue/scene/motion
and offline-refinement progress, elapsed waits, terminal outcomes and Stop/Cancel
availability were verified; a deployed failed/stalled worker was not deliberately
created or claimed as tested. Simulation: no simulated task rollout; predictive
MuJoCo kinematics/contact validation is retained, not presented as a simulated
execution. No active physical run remains. No overall completion claim.


## Live public/recovery evidence — October30,2026 (05:54 UTC October31)

12/15 requirements verified (80.0%) under1619d7f. Public cookie-free history,
three run details, generated scratch programs and ranged physical video all
returned200/206; all contacts redacted. Offline refinement is publicly readable
with Model MEMO. Physical run mutation and skillbook controls remain owner-only
(privacy/control regression passed). Live UI SHA256
4b4e174f3ca02c84a33bc17013951484ec5c084a3db0def1d0ca3efc3ad6ea9c
exactly matches tested current source.

Failure/stall/recovery:107 tests passed21.94s. Controlled browser mock fixture
verified late Home wait status, a failed Stop that remains available, persistent
unconfirmed-Stop warning across polls/history selection, and recovery after a
second explicit Stop with Run enabled. The fixture used synthetic cameras, no
model and no physical robot; it is UI/transport evidence, not physical timing.
The same UI code is now deployed. Current runtime c073a71; actual-model mock
proof734ef5e has identical Python adapter/runtime code.

Still open: full Model attribution through the new physical run/notification
metadata, visual timing correlation (15s postHome/30s postRun), and final
current-deployment end-to-end physical review. All prior hardware completion
bounds fit the revised timing rule; the former site-entry15s failure is obsolete.


## Leased-image handoff repair — October30,2026 (UTC October31)

Physical trial `a7ce789573534fc2827ab3ab8704e77d` on c073a71 safely rejected its method move; no method motion and no replay of the rejected command. The steer acknowledgement preceded actual image delivery. A new coding command started1793426357.2547464, before the leased user message arrived at~1793426357.900; rejection at1793426357.6329622 preserved the motion gate. Home completed1793426353.522509 after Run1793426341.521. Both method-onset targets failed for this run because no method motion executed; it is retained in public history.

The repair interrupts preparation, explicitly cleans its native background terminals, verifies the terminal list is empty, then starts a fresh coding turn containing leased images. Only a new command in that same turn can satisfy the image-review gate. Native interruption alone does not guarantee a command-completion event or process termination. The pinned robot client, queue/lease, limits, closed image gate and no-automatic-retry behavior remain. Fullsuite108passed23.19s; retained-terminal regression confirms no image acceptance/motion release if cleanup fails.

The previously saved contact was flagged incorrect. The user confirmed a corrected email for future tests; old records are retained. Private contact values are excluded from this public evidence. Score remains12/15 while actual-model verification and current-deployment physical signoff are pending.

Actual native mock verification passed with the same repaired broker hash: runs `14a25bb2111049d69da1310db0729796` and `43acb730c1ab4c4e8ca49c1be0461517`, refinement `aacf70105d6e4dcb8a08be55c5b7347c`. Both runs learned/retrieved corrections and completed one mock movement; fresh-turn image review and preparation-stopped stages are retained in `docs/evidence/2026-10-30-native-handoff.json`. This establishes actual inference and handoff behavior, not physical acceptance.


## Final repaired-runtime signoff — October30,2026 (UTC October31)

15/15 current-deployment requirements verified. Tested physical runtime82fb18ad7ce76da5e8541c733b5b0ab9d7f3122f; final evidence/report updates do not alter that runtime. Normal UI run185f6b2c162441198cc5b55ea52fafd5 on RoboHouse used MEMO with confirmed Andrew identity and automated_test mode. It retrieved template5/guidance4 from pinned skillbookv5, generated one new +0.03rad leftjoint0 adjustment and measured+.0286107rad, preserving all other commanded targets. No retry. Model MEMO was verified in site config/UI, public run metadata, controller run_configuration and the backend public_run.model_name field used for run/queue attribution; foundation model remains separately gpt-6-luna.

Run1793427934.719; matched settled Home1793427946.308876. Live UI frame0329 is unchanged at1793427955.977–1793427956.074; frame0330 visibly shows the method-driven wrist-view shift at1793427956.083–1793427956.106, after the method packet and stable post-Home scene. Therefore visible method movement occurred by21.387s afterRun and9.797s afterHome. Measured completion was21.410/9.820s respectively. Retained UI samples share the browser wall clock with the actual form timestamp; run click lies within independently captured1793427934.684–1793427934.956 interval. Async camera buffering is retained, not subtracted. No GPU/research exception.

Matched controller session sess_c723f9e14fae4823 joined receipt1793427936.556543 and admission receipt1793427946.288808 reasonjetson_leased, episodeep_9b2f04c3233f493b. Full Run time already meets30s, so no queue deduction was claimed. Receipt times include network delivery and are not presented as exact backend-entry times. This also meets the newer shared rule allowing evidenced queue exclusion; stricter full wall time passes.

Immediate replay ready31.125s/2601546bytes; normal video control advanced0→25.376s, paused=false/error=null. Selecting the first prior physical run played its55.125s footage through completion/error=null, then normal history selection returned to the final run. Live observer and independent top/wrist views were visible; all658 UI samples and matching timing metadata retained. Public sanitized evidence: docs/evidence/2026-10-30-final-physical.json, plus current public run/replay. Public screenshots/recording redact contact; no visibility exception for demo materials. Synthetic/mock evidence remains explicitly labelled. No simulated task rollout; kinematics/contact validation is not a claimed simulation execution.

All15 requirements reviewed: source/sitepublic; approachModelMEMO; editable confirmed name/email and human attribution; actual physical execution/live views; immediate/historical replay; simulationexplicitN/A; discoverable Run path; both visual timing limits; persistent truthful wait/failure/Stop recovery; final normal UI physical run. This signoff covers the repaired runtime and every physical run on it (one). Older failed/unverified revision outcomes remain in their historical evidence and are not retroactively marked passed. No active MEMO run remains.

Public supporting artifacts: [timestamped UI samples](evidence/memo-physical-ui-verification.mp4) (contact redacted; sampling-batch gap after onset preserved) and [visual comparison](evidence/memo-visual-onset.png). Earliest distinct change is frame0330; the earlier summary's22.9/11.3s bounds were conservative sampled bounds, tightened by frame-by-frame review to21.387/9.797s. No events or older outcomes were rewritten. The website's reviewed timing label is restricted to this exact run ID and matching original Run/Home timestamps; other runs retain the automatic-unverified label. Presentation regression12passed5.83s; physical runtime source unchanged.


## Apple-task failure and gripper repair — October30,2026 (UTC October31)

Current status13/15, with timing and final physical signoff reopened. The15/15 entry above records a bounded joint test; later runf93ef0712ffb4d9599f0ce53258270c5 exposed a gripper defect and missed startup timing. Apple placement has not been verified. Preserve both outcomes; do not reuse the bounded test as broad task acceptance.

The retained third packet had10 gripper-close waypoints, trajectorytraj_ep_f4aa32fa1bcc4727_138. Its final left_gripper was-1.1102230246251565e-16 from interpolation of measured0.9992793312193716 to intended0.0. The canonical HttpSessionAPI._trajectory_waypoints validator rejected it while building the local payload, before HTTP submission; no packet_dispatched/accepted/completed exists for that trajectory. The first two arm-motion packets dispatched and settled. No grasp/lift/place completed. This is a floating-point packet-generation defect, not evidence of a physical boundary crossing or a gripper opening too far.

Repair: preserve the already-validated exact final gripper target rather than recomputing it with subtract/multiply/divide. Keep the upstream strict[0,1]/finite validator, all joint/workspace/contact/pacing checks, queue/lease and non-replay behavior unchanged. Regression with the actual measured start failed for both arms before repair (2failed6passed1.65s). Fullsuite116passed23.53s after repair, including invalid tiny-negative/above-one/NaN/infinite requested targets. No failed physical command is automatically replayed.


## No-motion observation repair — October31,2026

Run c8b42ed779254dd0aa95db419749e030 completed Home then declared give_up without requesting frames/depth or method motion. The source c0d31e4 included the gripper fix; this was a separate observation-discovery problem. The agent's claim of unavailable depth was unsupported by a failed sensor request. Fresh calibration remains experimental_requires_fresh_validation, with held-out estimates but unverified physical depth/extrinsics accuracy; no quality warning is removed or relabelled.

The adapter now exposes overhead and wrist numeric depth, retains fresh timestamps/calibration, provides actionable help examples and a read-only --help alias, and directs the model to obtain numeric observations before concluding geometry is unavailable. The real model loaded both mock arrays and preserved calibration caveats in run3f325e425ad14cd98096b623ee84822a,31.515s,0motion commands (docs/evidence/2026-10-31-native-observation.json). This is observation/inference proof, not physical placement proof. Complete packets are now locally validated and serialized before execution handoff; malformed packets return through the bridge without actuator submission. CI and release preflight run the command matrix and numeric/capture regressions. Current13/15 remains pending physical timing and task signoff.


## Continued-task instruction repair and current requirements — October31,2026

Current14/17 after adding the two shared control/task requirements from
[shared control contract79c4e45](https://github.com/andlyu/blupe-remote-bots/blob/79c4e454aa829814152f8ff32a1979e68e93483d/codex-runner/integration-harness/CONTROL-CONTRACT.md).
The retained15-item checklist and its authorization wording are preserved; the
command-contract gate passes, representative physical manipulation remains open.
Required CI [41182195201](https://github.com/andlyu/memo-remote-yam/actions/runs/41182195201)
passed at76e7f04; release preflight36passed5.88s, fullsuite122passed22.78s.
Pinned external validator remainsfb1aaa9a696ae4597d06aef41bf876bf2ec90e4d.

Physical runa802bc53276a425b97359de2398a1489 obtained fresh numeric top/wrist depth
and executed one clear approach; no gripper or grasp/lift/place followed. No
controller/validation failure or timeout occurred. Request66.562s afterRun and
54.433s afterHome already missed both timing targets; measured completion75.028/
63.222s is not onset. First30s UI samples retained; exact later visual onset
unverified. Replay100.125s played0→12.3004s/error=null. No motion was retried.

Conflicting terminal instructions allowed give_up merely because the requested
result was not yet proven. Instructions now distinguish unfinished work from an
evidenced blocker, allow continue for another coding turn and require a concrete
blocker/recovery description for give_up. Safety/Stop/uncertain-motion rules remain.
Fullsuite122passed23.29s. Same actual model completed mock sequence60f219662f4b40a590cefe5e0df42ec6
in29.034s: joint adjustment, gripper close, restored joints, gripper open; four
commands, physical=false. This verifies sequencing only, not physical placement.
A verifier working-directory PermissionError occurred before inference and was
resolved by using its readable candidate directory; no physical command existed.

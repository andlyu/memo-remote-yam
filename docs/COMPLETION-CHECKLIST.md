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


## Agent as Policy + MEMO audit — 2026-10-30

This integration adopts the shared BLUPE Remote Bots integration harness above.
Source template: `andlyu/blupe-remote-bots`,
`codex-runner/integration-harness/COMPLETION-CHECKLIST.md`, copied 2026-10-30.
Template SHA-256: `36895c5add8d81f02bd8cd42a2b213e52cd85292d76661cddd180cc0d61b9421`.
Unchecked criteria are not completion claims. This audit is being updated during
startup-latency repair; no physical success is claimed by mock tests.

- Method: Agent as Policy with MEMO correction/skillbook learning,
  https://collab.me.vt.edu/memo/ . The runtime coding agent writes and executes
  programs from observations; it is not a scripted demonstration.
- Website: https://agp.54.209.185.15.sslip.io/
- Public standalone repository: https://github.com/andlyu/agp-remote-yam
- Deployed source at audit start: application `e9b3389`, repository `0818f5f`.
- Approach is named in the website. Join-time editable human name/email and
  explicit automated runner attribution remain unverified/unimplemented.
- Live public physical camera feeds are present. Existing captured observation
  images and event logs do not establish retained physical footage/replay.
  Immediate and historical physical video replay remain unverified.
- Final deployed end-to-end physical verification: pending. The reported run
  below fails startup latency and did not establish task completion.
- Visibility exceptions: none. Research-based timing exceptions: none claimed.

| Run reference | Run click (`t_run`) | First observed method-driven motion / evidence | Elapsed seconds | Outcome |
| --- | --- | --- | --- | --- |
| `d15c47d21ccd475dbc1ba67aa679b29d` | Browser click timestamp not retained; server creation 2026-10-30T22:23:34.918Z | No verified method-driven motion; first motion request at +166.343 s rejected by IK validation, no trajectory sent | >15; exact click-to-motion unavailable | Missed target; physical movement unverified |

The empty owner-scoped semantic lookup took 28.856 s in a fresh process on the
host before model inference. Queue/setup delays and the model's repeated coding
turns are additional measured contributors, not research-based exemptions.
Per-run browser-click timing and retained visual motion evidence are still
required before the mandatory timing criterion can be checked.


### Current verification evidence

- On 2026-10-30, the deployed site opened successfully in the browser and showed
  Agent as Policy, the MEMO learning choice, current run events and live camera
  panels. GitHub repository metadata independently returned `private:false` and
  `visibility:public`. These support the three checked criteria above.
- All three real-inference benchmark receipts explicitly name
  `Agent as Policy + MEMO`, runner `Automated`, run ID and `physical:false`.
  The benchmark uses the same Codex 0.159.0 native environment, rootless executor
  image and authenticated broker code, with a separate mock station, socket and
  data directory. It never acquires a physical robot session. The production UI
  still needs persistent runner-identity collection and attribution.
- First measured **mock command completion** from server-side run creation:

| Mock run | Configuration | First mock completion | Total | Interpretation |
| --- | --- | --- | --- | --- |
| `4ee1b6bb33d4454398db445f99c29a50` | Empty-lookup fix; continuous turn; Astra medium | 37.487 s | 96.106 s | Functional mock; not a physical timing pass |
| `e8a527609cd0415bb3d4383973c0ef24` | Same plus protocols supplied up front; Astra medium | 24.376 s | 30.829 s | Functional mock; not a physical timing pass |
| `8dd7a32f65224df09c7fe940820d93ae` | Inline protocols; experimental Astra low | 28.267 s | 36.253 s | Functional mock; no demonstrated improvement from low |

These are single-run observations, not guarantees or a controlled statistical
comparison. Keep Astra medium; the experimental configuration was not adopted.
All verified the +0.01-radian mock joint delta through newly generated code,
measured feedback and fresh mock images. The 15-second criteria remain unchecked.
Neither a mock completion nor homing/preparation satisfies actual method-driven
physical motion. No research-grounded exception is claimed.

### Remaining completion gates

Human editable name/email on join; persistent approach and runner attribution;
verified physical method execution; live footage during that execution; retained
immediate and historical physical replay; measured visitor-entry and every-click
15-second physical motion; final deployed UI physical run and complete evidence
review. Existing logs do not retain browser click timing or continuous visual
motion footage, so those observations must not be fabricated retrospectively.

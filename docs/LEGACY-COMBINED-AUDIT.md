# Historical combined deployment evidence

Superseded by the AgP-only repair. Preserved without treating these MEMO runs as pure AgP acceptance.

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
  `visibility:public`. Public visibility and the displayed approach name support the two checked
  criteria above. The later live camera failure below leaves usability unchecked.
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


### Post-deployment live check — 2026-10-30, 3:50 p.m. PDT

- Application revision `31b604f` is installed on the standalone site. SHA-256
  checks match its runtime, memory, native broker and MEMO protocol files.
  HTTPS `/api/config` returns200 with `agent:remote`, `mode:physical_api`,
  `model:gpt-6-astra`, `robot_id:yam-1`. Both own services are active.
- The normal browser UI loads, but all camera tiles are blank. The independent
  snapshot route returns503: `top camera frame unavailable (HTTP503)`.
  Both the standalone and upstream Playground synchronized-HD playlist return
  the same404 `no stream is available on path 'synchronized-hd'` response.
  This is an upstream feed availability blocker; the startup repair does not
  modify camera code or Playground. Do not send a physical task without fresh
  visible footage. Keep site usability, live footage and final physical checks
  unchecked. No continuous motion footage is available for a final timing pass.
- No physical trial was attempted during this repair. No research-grounded
  exception is claimed for either the latency miss or camera unavailability.

# Verification — 2026-10-24

## MEMO integration — 2026-10-30

- Standalone regression suite: 49 passed in 9.15 s, Python 3.14.7.
- Real Codex 0.157.0 / gpt-6-astra smoke with mock robot: PASS in 198.42 s.
  A queued owner correction became guidance and a parameterized template; a
  second coding-agent run retrieved prior memory for a related task. This smoke
  explicitly used the lexical fixture encoder. No physical session was created.
- Semantic MiniLM encoder at revision 1110a243: PASS. PICK(cube)/wood block near
  a dish ranked the prior PICK(block)/bowl lesson at 0.9324 similarity. Initial
  setup plus fixture execution took 45.28 s. This is a retrieval fixture, not
  manipulation or physical transfer evidence.
- Packet-service integration: PASS. One host-created session, one worker
  creation and one mock packet; 1.36 s. The service never held a robot-session
  credential or opened a second robot session.
- Browser integration: PASS on localhost. The shared model picker offered both
  modes; an owner correction received a delivery receipt; the MEMO panel showed
  a learned guidance entry. This browser test used an explicitly scripted mock
  fixture and synthetic/unavailable preview video, not a physical robot.
- Source publication: public `andlyu/agp-remote-yam`; shared Playground integration
  in `andlyu/blupe-remote-yam` PR #156.
- Public physical execution, container model authentication and production
  activation remain UNVERIFIED. The current web host has no Docker executable;
  do not treat the local coding-agent smoke as public worker isolation evidence.

Earlier baseline results and camera verification follow below.

Environment: macOS arm64, Python 3.14.7, Codex CLI 0.157.0,
Remote YAM fb1aaa9a696ae4597d06aef41bf876bf2ec90e4d,
AgP client 54dd96ed97c013950816bb674cbc38a68ec19b51.

| Check | Result | Evidence / limit |
| --- | --- | --- |
| Offline tests | PASS | `python -m pytest -q`: 38 passed in 7.42 s (camera-parity update). Includes original-client round trip, completion matching, FK/IK, RGB-D files/calibration and idle-feedback timestamp boundaries, Stop/lease revocation and process reaping, workspace symlink/FIFO protection, CSRF, visitor ownership and experience reuse. |
| Real coding agent with offline station | PASS | `python scripts/smoke_model.py`: run 2c322e338323456ca974d56f6ab36f02, 59.65 s creation-to-completion. Codex generated/executed scratch/smoke.py, issued state → frames → move_joints → state → frames, inspected a fresh image and saved notes. Output explicitly says no physical task was validated. |
| Browser task/run/artifact flow | PASS | Localhost demo visibly completed, showed tool calls/results and opened saved experience notes. Preview images and outcome explicitly identify the mock. Screenshots are in ignored outputs/website-overview.png and outputs/website-outcome.png. |
| Fresh workspace / selected experience | PASS | A second offline run copied the selected snapshot into knowledge/; an unseeded run remained fresh. Snapshots are agent-authored/unverified. |
| Container build/runtime | PASS (transport); model auth UNVERIFIED | Docker daemon 20.10.13. Built image sha256:3264c4940e65d2cd9d85e8938cc0a5dffd1a198a4159ba27e80325a0bbf64c48; container reports codex-cli 0.157.0. `scripts/smoke_container.py` run 7dfe6318b1e143409dc7bc3bd6fc4fb7 completed state → frames → move_joints → frames with the production isolation/mount flags and scripted agent. No CODEX_API_KEY is configured, so container model authentication was not exercised. |
| Public API physical execution | UNVERIFIED | No physical session was created and no motor command was sent. Offline geometry/transport evidence does not validate physical calibration, live RGB-D availability or task success. |
| Public deployment / unrestricted visitors | NOT RUN | No deployment or publication. See README hosting limitations and credential/spend/abuse decisions before opening the service publicly. |

Receipts remain under ignored `outputs/model-smoke/` and
`outputs/browser-demo/`. Raw agent process events are host-private and never
served by the run workspace API. Model result declarations are recorded with
`agent_declared_not_independent_physical_validation`.

## Public camera parity — 2026-10-24

PASS: the running localhost preview now displays the actual public API sources:
main observer, overhead, left wrist and right wrist. Generated images are used
only with the explicit `--synthetic-cameras` test option. The main public video
feed's existing camera order and crop geometry are preserved. The public relay
redirects retired stream paths; the local proxy follows them exactly as the
upstream LocalPlayground does, without forwarding visitor credentials.

Browser evidence: all four canvases reported `frameSource=video` and matching
presented frame counters advancing 59 → 211; video time advanced
15.909149 → 35.410759 s with readyState 4 and paused=false. The received feed
was 1280×720, with four 640×360 tiles. This verifies advancing playback, not a
hard source-freshness or end-to-end latency guarantee. API stills are used only
while the video joins. No robot session or physical command was created.

Receipts: `outputs/api-camera-playback.json`, `outputs/api-cameras.png`.
The earlier synthetic preview screenshot documents initial offline testing;
it is superseded by this live-camera preview. Robot execution remains mocked
on the current `--demo` server, independently of the camera viewer.

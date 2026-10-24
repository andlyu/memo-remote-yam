# Verification — 2026-10-24

Environment: macOS arm64, Python 3.14.7, Codex CLI 0.157.0,
Remote YAM fb1aaa9a696ae4597d06aef41bf876bf2ec90e4d,
AgP client 54dd96ed97c013950816bb674cbc38a68ec19b51.

| Check | Result | Evidence / limit |
| --- | --- | --- |
| Offline tests | PASS | `python -m pytest -q`: 31 passed in 6.60 s (final permanent checkout). Includes original-client round trip, completion matching, FK/IK, RGB-D files/calibration and idle-feedback timestamp boundaries, Stop/lease revocation and process reaping, workspace symlink/FIFO protection, CSRF, visitor ownership and experience reuse. |
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

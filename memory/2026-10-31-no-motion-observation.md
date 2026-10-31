# No-motion apple task: observation discovery

- **Symptom:** c8b42ed779254dd0aa95db419749e030 homed and gave_up without method motion on c0d31e4. No gripper error.
- **Root cause:** the model declared depth unavailable without making any frames/depth call; it read state/context and tried --help, which previously returned an unrelated unsupported-command message. Initial previews intentionally omit numeric depth, and the adapter exported numeric depth only for wrist, although the public API also supplies overhead depth. Calibration is experimental and must stay labelled as such.
- **Fix:** make help discover both depth views and accept read-only --help; expose fresh numeric overhead and wrist arrays/bundles with per-view calibration and source-time checks; require requesting/inspecting observations before claiming them unavailable; preserve calibration uncertainty and prohibit guessed XYZ. Validate all generated packets with the unchanged canonical validator and JSON serializer before execution handoff. Improve explicit give_up and sensor-wait UI status.
- **Evidence:** new capture/discovery regressions failed3cases before repair (6passed2.02s). Actual native gpt-6-luna mock observation check3f325e425ad14cd98096b623ee84822a passed31.515s, loaded both arrays with NumPy, preserved mock calibration quality, issued0motion commands. Fullsuite result recorded below. Command-preflight matrix covers both arms/read/move/gripper operations through real packet validation and serialization, plus local error recovery with0execution calls. CI and dedicated release preflight execute these checks.
- **Regression:** tests/test_captures.py; tests/test_control_preflight.py; scripts/verify_native_observation.py.
- **Status:** software/model observation checks passed; actual physical apple task remains pending. No broad acceptance claim; current13/15 requirements remain.


Physical follow-up a802bc53276a425b97359de2398a1489 on76e7f04 requested fresh numeric top/wrist depth, deprojected the apple and executed one clear approach. No validator, execution or hardware failure occurred. It then declared give_up because no grasp had occurred, with no concrete blocker; the300s run ended after98.191s. Move request66.562s afterRun/54.433s afterHome; measured completion75.028/63.222. Both onset targets missed even before submission; the live UI capture covers first30s, so exact later visual onset unverified. Replay100.125s played0→12.3004/error=null. No timed-out or uncertain motion was replayed.

Root hypothesis confirmed by conflicting supplied text: INTERFACE said “Use give_up when the evidence cannot establish completion”; MEMO said “done only after fresh visual verification of the whole task; otherwise give_up.” These permit an intermediate approach to become a terminal failure despite the general continuation instruction. Replace this with explicit unfinished-work continuation, continue for a new coding turn when needed, and give_up only with an evidenced blocker or exhausted budget. Safety/Stop/no-repeat instructions stay active. No model, broker, command limits or geometry changes. Full122tests23.29s. Actual-model mock sequence verification follows; these instruction improvements do not independently establish physical grasp/place.


Final follow-up d75a70e11a9f4a72bfd37812b3bb4f59 on35a471e progressed through seven
physical arm/gripper commands, proving observation-discovery and premature approach
termination repairs changed actual behavior. Apple did not lift; physical task
review failed. Model nevertheless declared done while its own evidence says lifting
not confirmed. Do not treat a model declaration or final apple-on-plate state as
proof of the required lift transition. Requested50mm lift achieved22.094mm,
28.096mm target error. Offline exact request/calibration reconstruction planned
all five endpoints within0.001911mm, rejecting a planner/IK-error hypothesis.
Do not patch the solver or widen bounds based on these hardware residuals.
Canonical joint-settle feedback is not a Cartesian/object success guarantee.
Remaining concerns: accurate closed-loop grasping, model outcome assessment and
startup latency. UI now shows failed physical review for this exact run while
preserving its raw done declaration. Status: DONE_WITH_CONCERNS for the software
repairs; overall physical manipulation integration incomplete,14/17.

Final software check122passed23.13s, including reviewed-task failure presentation without mutating the model declaration or issuing control requests. The earlier35a471e CI failed its legacy15-item count assertion after acceptance expanded to17; the assertion now checks the documented checklist,14 current passes and the three unmet IDs. This presentation/test correction changes no physical runtime behavior. Latest211.125s physical replay played0.209→32.9272s with no playback error.

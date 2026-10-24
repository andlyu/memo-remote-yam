# Standalone integration

Keep this repository independent of private BluPe source and deployment state.
Remote YAM remains a clean, pinned external dependency. Preserve the authors'
robot client unchanged with its upstream attribution.

Keep the runtime coding agent's observation/program/execution/revision loop.
Do not replace it with a fixed script or pre-generated task lookup. Demo robot execution
must remain explicitly labelled scripted/mock. Camera display uses the real
public observer, overhead, left and right feeds by default, independently of
robot execution. Synthetic cameras require the explicit test-only flag.

Use the existing RunnerController queue, lease, feedback, execution checks and
Stop semantics. Never automatically retry a timed-out motion. Offline passing
tests do not establish physical task success or intervention readiness.

Run `.venv/bin/python -m pytest -q` for adapter changes. Test actual inference
with `--mock-robot` before proposing a physical trial. Do not send a robot
command or publish/deploy as part of offline verification.

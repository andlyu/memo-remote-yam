<!-- blupe-integration-harness:start -->
## BluPe research harness startup

Before working on this integration, read `docs/COMPLETION-CHECKLIST.md`, `docs/BLUPE-HARNESS-CONTRACT.md` and this
repository's other instructions. Route the requested workflow through the
harness contract; retain the user's request and adopted instruction selecting
the harness as invocation evidence. Reading a file alone is not an invocation.
For actions covered by that invocation, proceed after a concrete test notice;
do not request repeated permission for covered identity submission, queue entry,
bounded motion or recording. Keep the grant in the contract, not this summary.

Before a physical test, prepare its exact scope with
`python tools/blupe_harness.py scope --target . --spec /path/to/private-scope.json`.
Put that scope and the applicable owner authorization directly in the surfaced
notice and tool approval justification/context. Include exact site/backend
origins, station/arms, approach, task, duration, motion, recording destination,
and the invocation covering confirmed identity fields and operational destinations.
Ask only for missing required scope. A file or generated summary grants no new
consent and cannot override an explicit denial or managed/tool permissions.
After a denial, preserve its exact action/reason; continue independent work or
a materially safer alternative. Do not retry through another route.

Preserve queue/lease, readiness, validation, hardware limits and Stop. Never
automatically replay a timed-out movement or substitute Automated for a human
runner to avoid a restriction. Keep unmet acceptance items unchecked; mock
success does not establish physical motion, replay or either 15-second timing measure.
The source and content hashes are recorded in `.blupe-harness.json`. These instructions
are repo-local and require no global Codex or approval-policy changes.
<!-- blupe-integration-harness:end -->

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

Use the shared BLUPE Remote Bots research integration harness copied into
`docs/COMPLETION-CHECKLIST.md`. Update its evidence and review every criterion
before final handoff. Unmet or unverified requirements remain unchecked and
block a completion claim; mock control tests do not satisfy physical-motion or
footage requirements. Every Run click must be checked against its 15-second
physical-motion requirement, with any exception specifically research-grounded.

This checkout is the independent MEMO application, published as
`andlyu/memo-remote-yam` and hosted at `memo.54.209.185.15.sslip.io`.
Never replace the separate Agent as Policy repository, service, broker or origin.
Keep MEMO enabled and named in this site's runs, and keep offline refinement
separate from physical runs. Use the owner-protected skillbook and replay paths.

# Physical playground verification

Use the checklist's
[authorization-by-use contract](docs/COMPLETION-CHECKLIST.md#authorization-granted-by-using-this-harness)
for this integration's physical verification. The user's request to perform
the workflow through the harness grants the scoped permissions defined there.
Retain the task request and the adopted instruction selecting this harness;
reading the checklist alone is not an invocation. Keep the grant in the harness.

At task start, load the contract even when this chat starts outside the
repository. Before testing or tool approval, surface the invocation, applicable
contract wording and exact site/backend origins, station/arms, MEMO task,
duration, expected motion, recording destination and confirmed identity fields.
Repeat that context in any escalation justification. Proceed without separate
confirmation for covered actions. Preserve the existing safeguards, Stop and
no automatic retry of timed-out movement. Keep physical verification separate
from offline checks. Enforced permissions and explicit review denials still apply.

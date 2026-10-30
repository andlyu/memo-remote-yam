# Agent as Policy on Remote YAM

Now includes **MEMO**: retrieve prior corrections, learn parameterized skills
and consolidate the versioned skillbook. The standalone website has learning
selection, live corrections and a skillbook viewer. See [MEMO](docs/MEMO.md) and
the [BluPe Playground integration](docs/PLAYGROUND.md).

A standalone website that runs a coding agent against the public Remote YAM
API. Give it a task and an optional goal image. The agent observes cameras and
measured state, writes and executes Python, sends a robot command, checks the
result, and revises its program until it finishes or the run ends.

This is an integration of the [Agent as Policy method](https://arxiv.org/abs/2609.12541),
with the authors' unmodified file-protocol client. It replaces their local
CAN/camera bridge with the public API. It does not reproduce the paper's full
evaluation suite or claim its reported success rates.

## Start locally

Requires Python 3.11+, Git, and network access during setup. Real agent runs
also require Codex CLI (tested with 0.157.0) and your normal Codex login.

```sh
./setup.sh
./run.sh --demo
```

Open <http://127.0.0.1:8797>. **Demo mode uses a scripted mock robot and the real public camera streams.
It never calls a model or controls the physical robot.**

The viewer preserves main observer, overhead, left wrist and right wrist.
For fully offline camera fixtures, use `./run.sh --demo --synthetic-cameras`.
See [camera sources and mapping](docs/CAMERAS.md).

Test the real model with the mock robot:

```sh
codex login
./run.sh --mock-robot --model gpt-6-astra
```

Run the real agent through the public robot API:

```sh
./run.sh --model gpt-6-astra
```

The website connects to `yam-1` at the configured public session API. Starting
the website only serves the UI; clicking **Run Agent as Policy** joins the queue
and takes a timed robot lease. Stop revokes that lease before terminating the
agent. Use `--api`, `--robot-id`, `--port` and `--data` to select a deployment.
Local mode runs as your logged-in user with Codex's workspace sandbox and is
intended for a trusted operator.

## What is preserved

```text
Browser task + goal image
  → isolated run workspace + real Codex process
  → agent writes/runs Python and invokes upstream robot_client.py
  → request/response files (left and right arm)
  → API adapter: cameras / calibrated FK+IK / joint trajectories
  → pinned Remote YAM RunnerController
  → public queue, lease, measured completion and Stop
  → fresh observations back to the agent
```

The agent remains the policy throughout the run. There is no fixed generated
program that replaces its observe/program/act/revise loop. The UI shows agent
messages, tool calls/results, generated files and an agent-declared outcome.
Raw process events remain outside the browser workspace.

Each run starts with the client, interface documentation, task, empty scratch
folder and optional goal image. Programs and captures stay in that run. Notes
and helpers saved under `scratch/experience/` are snapshotted after completion;
select a prior run in **Experience** to seed a new run's `knowledge/` directory.
Reuse is explicit and labelled agent-authored/unverified. A server restart marks
unfinished runs interrupted and never resumes motion automatically.

## Robot contract and differences from the paper

- `state`, `frames`, `move_ee`, `move_joints`, `gripper`, `status`, `help` are
  available through the original client. Both arms are supported sequentially.
  Poses use each arm's own base; quaternions are wxyz and joints are radians.
- The API accepts 10 Hz joint waypoints. Cartesian commands use the pinned
  runner's calibrated YAM FK/IK and joint/contact checks. Existing packet,
  session, pacing, feedback and lease checks remain active.
- A command returns only after matching measured, settled completion. A timed
  out or failed execution is never automatically replayed.
- Captures include actual image sizes, intrinsics, distortion, camera-to-base
  poses, calibration identity/quality and source timestamps when available.
  Wrist depth is numeric float32 optical Z in metres. Camera and joint streams
  are **not hardware synchronized**. Missing depth produces an error.
- Timed 50 Hz throwing programs, synchronized rig captures and the authors'
  local motor bridge are not reproduced. The mock station has synthetic RGB
  only and establishes no physical performance or RGB-D readiness.

See [the agent interface](src/agp_remote_yam/assets/INTERFACE.md) and
[references](docs/refs/INDEX.md). Dependencies are exact public source revisions
in `dependency.lock.json`; the runner is a separate ignored checkout under
`.deps/`, with no dependency on the private BluPe repository.

## Hosting

Public prompts execute code, so public binding uses a separate container per
run. Build the worker image, configure the model credential on the server and
serve the app behind an HTTPS reverse proxy:

```sh
docker build -f Dockerfile.agent -t agp-codex:0.157.0 .
export CODEX_API_KEY=... # configure securely in the service environment
./run.sh --host 0.0.0.0 --agent docker --public-origin https://your-domain.example
```

Only that run's workspace is mounted; the worker has a read-only root, reduced
capabilities and process/memory/CPU limits. The browser cannot set API origins,
credentials, models or command-line options. CSRF and browser ownership protect
run operations and artifacts. Cookies provide local visitor identity, not an
account system. Raw model credentials are supplied to the worker's Codex
process; this is not a hardened credential broker.

Before an open public launch, validate container model authentication and a physical trial,
choose request/model spend limits and abuse controls, and deploy a credential
broker if arbitrary visitors must never access a worker credential. The
prototype does not include billing, analytics, moderation, account recovery,
or a production deployment. [Verification status](docs/VERIFICATION.md) records
what has actually been exercised.

## Tests

```sh
.venv/bin/python -m pip install -e '.[test]'
.venv/bin/python -m pytest -q
```

Tests use no physical robot or paid model. They cover the original client,
exactly-once bridge handling, FK/IK frames and units, completion matching,
non-replay after failure, cancellation, browser ownership/CSRF, workspace
symlinks and explicit experience reuse. `--mock-robot` additionally permits a
manual real-model smoke test without opening a robot session.
After building the worker image, run `.venv/bin/python scripts/smoke_container.py`
to check container IPC with a scripted agent and no model credential.

Upstream client attribution and licenses are in [NOTICE](NOTICE). This
integration is independently maintained; upstream authors have not endorsed it.

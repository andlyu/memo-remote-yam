# Playground packet service

The standalone website creates its own session through RunnerController. The
Playground integration instead uses a private packet service. The Playground
retains its one queue admission, lease, motor commands, measured completion,
recording and Stop. The worker receives observations and emits packets; it has
no robot-session capability and never creates another robot session.

Run the worker in its own environment:

```sh
./run.sh --worker --port 8798 --service-token-file /private/path/agp-worker-token \
  --agent docker --data /var/lib/agp-remote-yam
```

The token file must contain a random secret of at least 32 characters and stay
outside Git. The default bind is loopback. Real untrusted/public prompts use the
existing per-run Docker isolation and require server-configured model auth; the
trusted local Codex mode reuses the operator's existing login. Never copy login
credentials into run workspaces. See README's hosting limits before public use.

Configure a shared Playground version containing `remote_yam.agent_policy_service`:

```sh
export YAM_AGENT_POLICY_ORIGIN=http://127.0.0.1:8798
export YAM_AGENT_POLICY_TOKEN_FILE=/private/path/agp-worker-token
export YAM_AGENT_POLICY_MODEL=gpt-6-astra
export YAM_AGENT_POLICY_ROBOT_ID=yam-1
```

The existing launcher then advertises **Agent as Policy** and **Agent as Policy +
MEMO**. Visitors cannot choose worker origins, credentials or arbitrary models.
Use existing task-chat steering for corrections. The MEMO panel shows the pinned
retrieval version, retrieved IDs and saved guidance/templates. BluPe-hosted guest
admission belongs in apps/blupe_web and must retain its existing run allowance.
Configure only supported YAM stations; the worker checks its robot identity.

## Rootless executor with an existing subscription login

An operator can instead use `--agent remote` on the loopback worker. The generic
`agp_remote_yam.codex_broker` process runs as the account already signed into
Codex. It registers each run's rootless Podman executor as a native Codex remote
environment. Model requests retain the normal host-side login; shell, file,
patch and image tools execute in the container. No account credential, host
home directory or container-engine socket is mounted in generated code.

This transport pins **Codex 0.159.0** on both sides and uses its experimental
app-server environment protocol. Test the exact version before activation.
The harness uses Astra's catalog-default medium reasoning and a container-only
tool environment; the account's model-only tool settings are overridden only
for this isolated harness.
The worker user needs a normal rootless Podman installation and subordinate
UID/GID range, with no Docker-group or sudo access. The separate broker accepts
only that worker UID over a filesystem-protected Unix socket. Keep the existing
subscription broker and its configuration separate.

Server-only `/etc/agp-remote-codex.json`:

```json
{
  "engine": "podman",
  "image": "localhost/agp-codex:0.159.0",
  "model": "gpt-6-astra",
  "run_root": "/var/lib/agp-remote-yam/runs",
  "broker_socket": "/run/agp-codex-broker/coding.sock"
}
```

Build `Dockerfile.agent` with `--build-arg CODEX_VERSION=0.159.0` as the worker
user. Start the broker with `python -m agp_remote_yam.codex_broker --socket ...
--client-uid WORKER_UID --binary /path/to/codex --home /existing/login/home`.
The broker uses that account's normal auth cache directly. Do not copy the
cache into the worker, image or run workspace. Set `HOME`, `XDG_RUNTIME_DIR`
and the user bus for rootless Podman in the worker service environment.

## Service protocol

All endpoints require `Authorization: Bearer TOKEN`. No credential is exposed to
the browser or generated agent code. JSON bodies are bounded to 512 KB.

| Method / path | Contract |
| --- | --- |
| GET /health | Configured robot and encoder identity |
| POST /runs | Idempotent client_run_id, private namespace, task, robot_id, memo, measured observation; returns worker run ID |
| POST /runs/ID/poll | Observation, completed-packet acknowledgement, event cursor, corrections; returns one pending packet, events, delivery receipts and status |
| POST /runs/ID/stop | Idempotently cancel agent process; the host controller separately stops its robot lease |

Packets retain their IDs across lost polls. The worker unblocks a command only
after the host acknowledges the matching final cursor and settled observation.
Duplicate acknowledgements are harmless. A wrong lease/cursor or uncertain
motion fails without replay. A missing host poll cancels the agent after 15 s;
the robot gateway and host remain responsible for the physical lease/Stop.
Restarts mark unfinished workers interrupted and never resume motion.

The shared runner and this service are separate processes with separate pinned
dependencies. No private BluPe source or deployment state is needed to install
this repository. The provider, steering acknowledgement hook and UI additions
live in blupe-remote-yam/codex-runner.

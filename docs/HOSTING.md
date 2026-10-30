# Independent website hosting

Deploy `agp_remote_yam.web.App` from this repository as a separate service and
HTTPS origin. It does not require a Playground provider, changes to the
Playground website, or source from a private BluPe repository. The clean Remote
YAM revision in `dependency.lock.json` supplies the existing queue, lease,
measured execution and Stop implementation.

The live standalone site is <https://agp.54.209.185.15.sslip.io/>.
It uses real public cameras independently of robot execution. A user submits
a task only on this site; AgP programs, observations, explicit experience reuse,
runner identity and physical replay remain in its browser-scoped interface.
This origin must run without `--memo-site`; MEMO is a separate application.

## Native rootless service

Use the rootless native Codex transport described in the rootless executor
section of `docs/PLAYGROUND.md`. That transport is shared by both the standalone
app and the optional packet-service entry point. For this website **omit
`--worker`**:

```sh
python -m agp_remote_yam \
  --host 127.0.0.1 --port 8828 \
  --public-origin https://your-agent-host.example \
  --agent remote --data /var/lib/agp-remote-yam
```

Keep the model harness in the account that is already authenticated. Generated
code runs in a per-run rootless Podman container, with no host login, API key,
user home or container-engine socket mounted. Pin the CLI and executor image
to the same tested version. `run_root` in `/etc/agp-remote-codex.json` must equal
the selected data directory's `runs` subdirectory.

Start the app with its own systemd unit. A service using `ProtectHome=tmpfs`
can bind only the worker UID's `/run/user/UID` directory for rootless Podman;
all user homes remain hidden. Use a private temporary directory and permit
writes only to the app data and its own runtime directory. Never add the worker
to the Docker group. The operator supplies the exact UID, model broker account,
engine image, pinned dependency path and private model cache.

Put the service behind a separate Caddy site block:

```caddyfile
your-agent-host.example {
    encode zstd gzip
    header Strict-Transport-Security "max-age=31536000"
    reverse_proxy 127.0.0.1:8828
}
```

Configure only this new hostname. Do not add this app's menus or proxy paths to
an existing Playground origin. The `sslip.io` live hostname resolves the encoded
server address; an operator-owned DNS name can point to the same service later.

## Verification and rollback

Check HTTPS, `/api/config`, real camera playback, absence of MEMO controls and protocol files, editable
runner identity, run history/replay, and an actual-model/mock-robot test before a physical
trial. Check CSRF, ownership and Stop through the existing offline suite.
Do not submit a physical robot task just to test a deployment.

The rootless model/semantic-memory two-run mock passed in 280.94 seconds; its
container and credential boundaries were checked separately. The adapter suite
passed 57 tests on the deployed application revision. These checks do not
establish physical task success.

To withdraw this website, remove only its dedicated proxy site include,
validate and reload Caddy, then stop/disable its own web unit. Keep run-data and any legacy skillbook backups. Other websites and the public robot API are independent.


The startup repair avoids loading the semantic encoder for empty visible memory
scopes, supplies the authoritative protocols in the initial coding context and
keeps the observation/action loop within a coding turn. The deployment retains
Astra medium reasoning. Fresh native-worker mock smoke tests completed and
verified a measured relative joint change; the best observed first mock command
completion was 24.376 seconds. This is not a physical latency pass. Use the
[shared completion harness and audit](COMPLETION-CHECKLIST.md) for acceptance;
physical timing, runner identity and retained replay gates remain open.

### AgP-only deployment repair

The correction from combined application `31b604f` makes pure Agent as Policy
the default. Existing MEMO records stay on disk and are excluded from AgP history.
Use an isolated release directory, install its wheel, atomically switch only
`/opt/agp-remote-yam`, then restart only `agp-web.service` after checking for active
runs. Roll back the wheel and symlink together. Preserve the broker, authentication,
robot service and public Playground. Set `AGP_SOURCE_REVISION` to the deployed commit.

Physical replay requires host `ffmpeg`/`ffprobe` and the existing public camera
feed. The recorder is independent of the generated-code container and saves to
the run's `recording/` directory. Owner checks protect video and byte-range
playback. Missing footage is labelled unavailable, never replaced by mock video.
Use per-executor cleanup; do not remove every Podman container on web-service stop.

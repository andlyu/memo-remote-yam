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

To withdraw this website, remove only its dedicated proxy site include,
validate and reload Caddy, then stop/disable its own web unit. Keep run-data and any legacy skillbook backups. Other websites and the public robot API are independent.


The native worker uses Astra with low reasoning and supported Fast mode. It
prepares its isolated executor and plans from explicitly labelled public,
read-only observations while the existing queue prepares the robot. The arms
may home in that interval. Only a matching, active, settled lease starts the
robot bridge. A queued state read then returns fresh leased feedback;
pre-admission motion requests are rejected rather than released later.
The agent must compute motion targets from that fresh state, and request new
images/depth whenever the changed pose or uncertainty requires them. No task
script or startup movement is supplied by the host.

Initial RGB views are fetched in parallel, independently of robot geometry preparation, with original images/metadata
retained and bounded JPEG previews supplied directly to the model. The host's
initial input manifest is outside the generated-code mount. Source timestamps
preceding settlement are rejected on leased captures. Numeric depth remains
available through the unchanged interface; RGB is not labelled RGB-D.

The delayed-lease actual-model mock `32e2b9f89a1e4fdaaccaf6bc70f43f98`
completed its first generated command at11.240 seconds, including a deliberate
ten-second simulated queue wait. It made one state-relative move after
admission and verified it. This is mock evidence, not a physical timing pass.
A harder mock with a changed admission pose completed first movement in14.887 seconds with Astra; a controlled Sol comparison took19.340 seconds, so Astra is retained. The adapter suite passed85 tests in15.88 seconds. Review the
[shared completion harness](COMPLETION-CHECKLIST.md) before any completion claim.

### AgP-only deployment repair

The correction from combined application `31b604f` makes pure Agent as Policy
the default. Existing MEMO records stay on disk and are excluded from AgP history.
Use an isolated release directory, install its wheel, atomically switch only
`/opt/agp-remote-yam`, then restart the dedicated services as described below after checking for active
runs. Roll back the wheel and symlink together. Preserve authentication,
robot service and public Playground. Set `AGP_SOURCE_REVISION` to the deployed commit.

Physical replay requires host `ffmpeg`/`ffprobe` and the existing public camera
feed. The recorder is independent of the generated-code container and saves to
the run's `recording/` directory. Owner checks protect video and byte-range
playback. Missing footage is labelled unavailable, never replaced by mock video.
Use per-executor cleanup; do not remove every Podman container on web-service stop.

When the native protocol changes, deploy its matching client and broker together.
After confirming no active AgP run, stop the web unit, install the verified wheel,
switch the release link, restart `agp-codex-broker.service`, then start
`agp-web.service`. Roll back both units with the previous wheel if startup fails.
Authentication files and other services remain independent.

Physical video is remuxed with `-c:v copy` to preserve the original encoded feed
and avoid competing with worker startup for video-encoding CPU. The live source
was verified as H.264,2560×1080,8 fps; a five-second copy produced a valid MP4.
The native thread uses concise robot-policy instructions and a host-supplied
`robot_api.py` wrapper around the unchanged authors' CLI. That wrapper contains
no policy or motion targets; generated programs remain the runtime agent's work.
Uncalibrated preparation views explicitly expose no end-effector pose or camera
pose binding. Fresh geometry is prepared separately and remains mandatory for
leased commands.

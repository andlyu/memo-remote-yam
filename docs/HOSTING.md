# Independent website hosting

Deploy `agp_remote_yam.web.App` from this repository as a separate service and
HTTPS origin. It does not require a Playground provider, changes to the
Playground website, or source from a private BluPe repository. The clean Remote
YAM revision in `dependency.lock.json` supplies the existing queue, lease,
measured execution and Stop implementation.

The live standalone site is <https://agp.54.209.185.15.sslip.io/>.
It uses real public cameras independently of robot execution. A user submits
a task only on this site; MEMO learning, corrections, skillbook and run files
remain in its own browser-scoped interface.

## Native rootless service

Use the rootless native Codex transport described in the rootless executor
section of `docs/PLAYGROUND.md`. That transport is shared by both the standalone
app and the optional packet-service entry point. For this website **omit
`--worker`**:

```sh
python -m agp_remote_yam \
  --host 127.0.0.1 --port 8828 \
  --public-origin https://your-agent-host.example \
  --agent remote --memory-encoder semantic --data /var/lib/agp-remote-yam
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

Check HTTPS, `/api/config`, real camera playback, both Learning choices, the
browser-owned skillbook, and a mock-only coding-model test before a physical
trial. Check CSRF, ownership and Stop through the existing offline suite.
Do not submit a physical robot task just to test a deployment.

The rootless model/semantic-memory two-run mock passed in 280.94 seconds; its
container and credential boundaries were checked separately. The adapter suite
passed 57 tests on the deployed application revision. These checks do not
establish physical task success.

To withdraw this website, remove only its dedicated proxy site include,
validate and reload Caddy, then stop/disable its own web unit. Keep data and
skillbook backups. Other websites and the public robot API are independent.

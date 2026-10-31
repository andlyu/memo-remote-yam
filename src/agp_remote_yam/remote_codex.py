"""Codex CLI-compatible client for a private, credential-free remote executor.

The model broker owns authentication. Generated code runs in this client's
rootless container; the broker registers it as a native Codex environment.
"""
import argparse
import json
import os
from pathlib import Path
import re
import secrets
import signal
import socket
import struct
import subprocess
import sys
import threading
import time

MAX_FRAME = 8_000_000


def send(sock, value):
    raw = json.dumps(value, allow_nan=False).encode()
    if len(raw) > MAX_FRAME:
        raise ValueError("Remote coding message is too large")
    sock.sendall(struct.pack('!I', len(raw)) + raw)


def receive(sock):
    def exact(size):
        result = bytearray()
        while len(result) < size:
            chunk = sock.recv(min(size - len(result), 65536))
            if not chunk:
                raise EOFError('Remote coding broker disconnected')
            result.extend(chunk)
        return bytes(result)
    size = struct.unpack('!I', exact(4))[0]
    if not 0 < size <= MAX_FRAME:
        raise ValueError('Invalid remote coding message size')
    return json.loads(exact(size))


def workspace_path(value, run_root):
    path = Path(value).absolute()
    root = Path(run_root).resolve(strict=True)
    if (path != path.resolve(strict=True) or path.name != 'workspace'
            or path.parent.parent != root or not re.fullmatch('[a-f0-9]{32}', path.parent.name)):
        raise ValueError('Remote coding requires a single run workspace')
    return path


class Executor:
    def __init__(self, workspace, settings):
        self.workspace, self.settings = workspace, settings
        self.name = 'agp-' + workspace.parent.name
        self.engine = settings['engine']
        if self.engine != 'podman':
            raise ValueError('Unsupported container engine')
        self.token_path = workspace.parent / 'executor.token'

    def call(self, *args, timeout=90):
        return subprocess.check_output([self.engine, *args], text=True, timeout=timeout,
                                       stderr=subprocess.DEVNULL).strip()

    def start(self):
        token = secrets.token_urlsafe(32)
        fd = os.open(self.token_path, os.O_WRONLY | os.O_CREAT | os.O_TRUNC | os.O_NOFOLLOW, 0o600)
        with os.fdopen(fd, 'w') as file:
            file.write(token)
        # Use the same explicit teardown for normal completion, failed startup
        # and Stop; finally removes this named executor.
        self.call('run', '--detach', '--init', '--name', self.name,
                  '--read-only', '--cap-drop=ALL', '--security-opt=no-new-privileges',
                  '--pids-limit=128', '--memory=2g', '--cpus=2',
                  '--tmpfs', '/tmp:rw,size=512m', '--userns=keep-id',
                  '--publish', '127.0.0.1::4500',
                  '--volume', str(self.workspace) + ':/work:rw',
                  '--volume', str(self.token_path) + ':/executor.token:ro',
                  '--workdir', '/work', self.settings['image'], 'codex', 'exec-server',
                  '--listen', 'ws://0.0.0.0:4500', '--ws-auth', 'capability-token',
                  '--ws-token-file', '/executor.token', '--linux-sandbox-pid-namespace', 'inherit')
        address = self.call('port', self.name, '4500/tcp')
        if not re.fullmatch(r'127\.0\.0\.1:\d{1,5}', address):
            raise RuntimeError('Executor must expose only a loopback listener')
        # The native exec-server owns its authenticated connection lifecycle.
        # A throwaway TCP probe can consume it before the harness connects.
        # environment/add performs the real authenticated initialization.
        return 'ws://' + address, token

    def close(self):
        subprocess.run([self.engine, 'rm', '--force', self.name], timeout=15,
                       stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, check=False)
        self.token_path.unlink(missing_ok=True)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('-a', choices=['never'])
    parser.add_argument('operation', choices=['exec'])
    parser.add_argument('--sandbox', choices=['workspace-write'])
    parser.add_argument('--ignore-user-config', action='store_true')
    parser.add_argument('--skip-git-repo-check', action='store_true')
    parser.add_argument('--json', action='store_true')
    parser.add_argument('--prepare', action='store_true')
    parser.add_argument('--model', required=True)
    parser.add_argument('--output-schema', choices=['RESULT_SCHEMA.json'], required=True)
    parser.add_argument('--output-last-message', choices=['FINAL.json'], required=True)
    parser.add_argument('--cd', required=True)
    parser.add_argument('prompt_source', choices=['-'])
    args = parser.parse_args()
    settings = json.loads(Path(os.environ.get('AGP_REMOTE_CODEX_CONFIG', '/etc/agp-remote-codex.json')).read_text())
    if args.model != settings['model']:
        raise ValueError('Remote coding model is fixed by the server')
    workspace = workspace_path(args.cd, settings['run_root'])
    if workspace != Path.cwd().resolve():
        raise ValueError('Unexpected coding working directory')
    executor = Executor(workspace, settings)
    started = time.monotonic()
    def profile(stage):
        print(json.dumps(dict(type='agp.profile', stage=stage,
                              elapsed_s=round(time.monotonic()-started, 3))), flush=True)
    def stopped(signum, frame):
        raise SystemExit(128 + signum)
    signal.signal(signal.SIGTERM, stopped)
    signal.signal(signal.SIGINT, stopped)
    watching = threading.Event()
    watcher = None
    try:
        url, token = executor.start()
        profile('executor_ready')
        with socket.socket(socket.AF_UNIX) as sock:
            sock.settimeout(650)
            sock.connect(settings['broker_socket'])
            if args.prepare:
                send(sock, dict(op='prepare', protocol='agp-codex-remote-v2',
                                executor_url=url, executor_token=token))
                while True:
                    prepared = receive(sock)
                    if prepared.get('prepared') is True:
                        break
                    if 'event' not in prepared:
                        raise RuntimeError('Remote coding preparation failed')
                    print(json.dumps(prepared['event']), flush=True)
            prompt = sys.stdin.read(1_000_001)
            if not 0 < len(prompt) <= 1_000_000:
                raise ValueError('Invalid remote coding prompt')
            from .observation import load_initial_input
            snapshot = load_initial_input(workspace)
            message = dict(op='coding', protocol='agp-codex-remote-v1', prompt=prompt,
                           executor_url=url, executor_token=token)
            if snapshot is not None:
                message['images'] = snapshot['images']
            send(sock, {k: message[k] for k in ('prompt', 'images') if k in message} if args.prepare else message)
            def leased_input():
                # This sidecar is outside /work and cannot be written by model
                # code. Only the host's active leased backend supplies it.
                path = workspace.parent / 'leased-input.json'
                while not watching.wait(.025):
                    if not path.is_file():
                        continue
                    from .workspace import Workspace
                    update = json.loads(Workspace(workspace.parent).read(path.name, 5_000_000))
                    text = ('[LEASED_OBSERVATION] Fresh settled post-homing scene and measured state. '
                            'Inspect these supplied images now, then choose to execute or revise your candidate '
                            'program in a new coding tool call. Read fresh state inside the movement program. '
                            'Do not duplicate captures unless changed conditions require it.\n'
                            + json.dumps(update['context']))
                    send(sock, dict(op='observation', prompt=text, images=update['images']))
                    return
            if snapshot is not None and snapshot['context'].get('phase') == 'monitor_before_admission':
                watcher = threading.Thread(target=leased_input, name='agp-leased-images', daemon=True)
                watcher.start()
            while True:
                value = receive(sock)
                if 'event' in value:
                    print(json.dumps(value['event']), flush=True)
                elif 'result' in value:
                    from .workspace import Workspace
                    Workspace(workspace).json('FINAL.json', value['result'])
                    break
                elif value.get('observation_accepted') is True:
                    from .workspace import Workspace
                    Workspace(workspace.parent).json('leased-input-accepted.json', dict(accepted_at=time.time()))
                else:
                    raise RuntimeError('Remote coding broker did not complete the turn')
    finally:
        watching.set()
        if watcher is not None:
            watcher.join(.5)
        executor.close()


if __name__ == '__main__':
    main()

"""Private subscription harness for native Codex remote container environments.

No login cache, host path, model selection or CLI option is exported to clients.
The only permitted client is the configured rootless AgP service UID.
Codex contract is pinned to 0.159.0, including experimental environment APIs.
"""
import argparse
import json
import os
from pathlib import Path
import re
import selectors
import signal
import socket
import socketserver
import struct
import subprocess
import tempfile
import threading
import time
import uuid

MAX_FRAME = 8_000_000
RESULT_SCHEMA = dict(type='object', additionalProperties=False, properties=dict(
    status=dict(type='string', enum=['continue', 'done', 'give_up']), summary=dict(type='string'),
    evidence=dict(type='array', items=dict(type='string'))), required=['status', 'summary', 'evidence'])


def send(sock, value):
    raw = json.dumps(value, allow_nan=False).encode()
    if len(raw) > MAX_FRAME:
        raise ValueError('Frame too large')
    sock.sendall(struct.pack('!I', len(raw)) + raw)


def receive(sock):
    def exact(size):
        value = bytearray()
        while len(value) < size:
            part = sock.recv(min(size-len(value), 65536))
            if not part:
                raise EOFError()
            value.extend(part)
        return bytes(value)
    size = struct.unpack('!I', exact(4))[0]
    if not 0 < size <= MAX_FRAME:
        raise ValueError('Invalid frame size')
    return json.loads(exact(size))


def validate(value):
    if (not isinstance(value, dict) or set(value) != {'op', 'protocol', 'prompt', 'executor_url', 'executor_token'}
            or value['op'] != 'coding' or value['protocol'] != 'agp-codex-remote-v1'
            or not isinstance(value['prompt'], str) or not 0 < len(value['prompt']) <= 1_000_000
            or not isinstance(value['executor_url'], str)
            or not re.fullmatch(r'ws://127\.0\.0\.1:[1-9][0-9]{3,4}', value['executor_url'])
            or int(value['executor_url'].rsplit(':', 1)[1]) > 65535
            or not isinstance(value['executor_token'], str)
            or not re.fullmatch(r'[A-Za-z0-9_-]{40,100}', value['executor_token'])):
        raise ValueError('Invalid coding request')
    return value


def result(value):
    if (not isinstance(value, dict) or set(value) != {'status', 'summary', 'evidence'}
            or value.get('status') not in ('continue', 'done', 'give_up')
            or not isinstance(value.get('summary'), str) or not isinstance(value.get('evidence'), list)
            or any(not isinstance(v, str) for v in value['evidence'])):
        raise ValueError('Invalid coding result')
    return value


def execute(sock, value, *, binary, home, timeout=610):
    env = dict(HOME=str(home), CODEX_HOME=str(home / '.codex'),
               PATH='/usr/local/bin:/usr/bin:/bin', LANG='C.UTF-8')
    # A selected native remote environment routes shell, file, patch and image
    # tools to its exec-server. There is no local-execution fallback.
    config = ['forced_login_method="chatgpt"', 'model_provider="openai"',
              'model="gpt-6-astra"', 'approval_policy="never"', 'web_search="disabled"',
              'features.apps=false', 'features.plugins=false', 'features.hooks=false',
              'features.multi_agent=false', 'features.memories=false',
              'features.skip_host_skill_discovery=true', 'features.remote_control=false',
              'features.browser_use=false', 'features.computer_use=false',
              'features.js_repl=false', 'features.code_mode=false',
              'mcp_servers={}', 'notify=[]', 'model_reasoning_effort="high"',
              'features.shell_tool=true', 'features.unified_exec=true',
              'features.apply_patch_freeform=true', 'features.view_image=true',
              'features.shell_snapshot=false', 'features.shell_snapshot_v2=false']
    command = [binary, 'app-server']
    for option in config:
        command += ['-c', option]
    with tempfile.TemporaryDirectory(prefix='agp-harness-', dir=home/'workspace') as directory:
        with tempfile.TemporaryFile() as errors:
            process = subprocess.Popen(command, cwd=directory, env=env, stdin=subprocess.PIPE,
                                       stdout=subprocess.PIPE, stderr=errors, start_new_session=True)
            def request(identity, method, params):
                process.stdin.write((json.dumps(dict(id=identity, method=method, params=params))+'\n').encode())
                process.stdin.flush()
            environment = 'agp-' + uuid.uuid4().hex
            pending = b'';final = None;deadline = time.monotonic()+timeout;ready_deadline = 0
            request(1, 'initialize', dict(clientInfo=dict(name='agp_remote_yam', version='0.2.0'),
                                         capabilities=dict(experimentalApi=True)))
            try:
                with selectors.DefaultSelector() as poll:
                    poll.register(process.stdout, selectors.EVENT_READ, 'codex')
                    poll.register(sock, selectors.EVENT_READ, 'client')
                    while time.monotonic() < deadline:
                        if os.fstat(errors.fileno()).st_size > MAX_FRAME:
                            raise RuntimeError('Harness diagnostic limit')
                        for key, _ in poll.select(.2):
                            if key.data == 'client':
                                raise EOFError('Client disconnected or sent unexpected data')
                            data = os.read(process.stdout.fileno(), 65536)
                            if not data:
                                raise RuntimeError('Codex harness stopped')
                            pending += data
                            if len(pending) > MAX_FRAME:
                                raise RuntimeError('Harness event limit')
                            lines = pending.split(b'\n');pending = lines.pop()
                            for line in lines:
                                message = json.loads(line)
                                if 'error' in message and message.get('id') == 5 and time.monotonic() < ready_deadline:
                                    # Retry only authenticated executor initialization,
                                    # before any model turn or robot command exists.
                                    time.sleep(.1)
                                    request(5, 'environment/info', dict(environmentId=environment))
                                    continue
                                if 'error' in message:
                                    raise RuntimeError('Codex remote environment request failed')
                                identity = message.get('id')
                                if 'method' in message and identity is not None:
                                    # No approval, authentication or other server request may
                                    # be approved by a public coding prompt.
                                    process.stdin.write((json.dumps(dict(id=identity, error=dict(code=-32601, message='Not available')))+'\n').encode())
                                    process.stdin.flush()
                                elif identity == 1:
                                    process.stdin.write(b'{"method":"initialized","params":{}}\n');process.stdin.flush()
                                    request(2, 'environment/add', dict(environmentId=environment,
                                        execServerUrl=value['executor_url'], authBearerToken=value['executor_token'], connectTimeoutMs=15000))
                                elif identity == 2:
                                    ready_deadline = time.monotonic()+15
                                    request(5, 'environment/info', dict(environmentId=environment))
                                elif identity == 5:
                                    if message.get('result', {}).get('cwd') != 'file:///work':
                                        raise RuntimeError('Executor did not confirm the isolated workspace')
                                    request(3, 'thread/start', dict(model='gpt-6-astra', approvalPolicy='never',
                                        sandbox='danger-full-access', ephemeral=True,
                                        environments=[dict(environmentId=environment, cwd='/work')],
                                        developerInstructions='All coding tools execute in the selected isolated /work environment. Read and write the task workspace there. No physical success is established by the harness.'))
                                elif identity == 3:
                                    thread = message['result']['thread']['id']
                                    request(4, 'turn/start', dict(threadId=thread,
                                        input=[dict(type='text', text=value['prompt'])], outputSchema=RESULT_SCHEMA))
                                method = message.get('method');params = message.get('params', {})
                                if method == 'item/completed' and params.get('item', {}).get('type') == 'agentMessage':
                                    text = params['item']['text']
                                    send(sock, dict(event=dict(type='item.completed', item=dict(type='agent_message', text=text))))
                                    try:
                                        final = result(json.loads(text))
                                    except (ValueError, TypeError):
                                        pass
                                elif method == 'turn/completed':
                                    if params['turn']['status'] != 'completed' or final is None:
                                        raise RuntimeError('Codex did not complete a valid coding result')
                                    send(sock, dict(result=final))
                                    return
                        if process.poll() is not None:
                            raise RuntimeError('Codex harness exited')
                    raise TimeoutError('Coding turn exceeded its deadline')
            finally:
                if process.poll() is None:
                    os.killpg(process.pid, signal.SIGTERM)
                    try:
                        process.wait(timeout=3)
                    except subprocess.TimeoutExpired:
                        os.killpg(process.pid, signal.SIGKILL);process.wait()


class Server(socketserver.ThreadingMixIn, socketserver.UnixStreamServer):
    daemon_threads = True
    def __init__(self, path, *, uid, binary, home):
        self.uid,self.binary,self.home=uid,binary,Path(home)
        self.slot=threading.BoundedSemaphore(1)
        super().__init__(path, Handler)
        Path(path).chmod(0o660)

    def verify_request(self, request, address):
        _, uid, _ = struct.unpack('3i', request.getsockopt(socket.SOL_SOCKET, socket.SO_PEERCRED, 12))
        return uid == self.uid

    def handle_error(self, request, address):
        print('agp coding request failed', flush=True)


class Handler(socketserver.BaseRequestHandler):
    def handle(self):
        self.request.settimeout(10)
        if not self.server.slot.acquire(blocking=False):
            send(self.request, dict(error='Coding worker busy'));return
        try:
            value=validate(receive(self.request));self.request.settimeout(650)
            execute(self.request,value,binary=self.server.binary,home=self.server.home)
        except Exception as exc:
            print('agp coding failure:',type(exc).__name__,flush=True)
            try:send(self.request,dict(error='Isolated coding turn failed'))
            except OSError:pass
        finally:self.server.slot.release()


if __name__ == '__main__':
    p=argparse.ArgumentParser();p.add_argument('--socket',required=True);p.add_argument('--client-uid',required=True,type=int)
    p.add_argument('--binary',required=True);p.add_argument('--home',type=Path,required=True);a=p.parse_args()
    if subprocess.check_output([a.binary, '--version'], text=True).strip() != 'codex-cli 0.159.0':
        raise SystemExit('This broker requires tested Codex 0.159.0')
    path=Path(a.socket)
    if path.exists():path.unlink()
    with Server(str(path),uid=a.client_uid,binary=a.binary,home=a.home) as server:server.serve_forever()

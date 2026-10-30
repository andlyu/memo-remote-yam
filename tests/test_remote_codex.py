from pathlib import Path
import socket
import struct
import pytest
from agp_remote_yam.remote_codex import Executor, receive, send, workspace_path


def test_workspace_mount_cannot_escape_or_follow_symlinks(tmp_path):
    root=tmp_path/'runs';workspace=root/('a'*32)/'workspace';workspace.mkdir(parents=True)
    assert workspace_path(workspace,root)==workspace
    alias=root/('b'*32);alias.symlink_to(workspace.parent,target_is_directory=True)
    with pytest.raises(ValueError):workspace_path(alias/'workspace',root)
    with pytest.raises(ValueError):workspace_path(tmp_path,root)


def test_framing_rejects_oversized_untrusted_response():
    left,right=socket.socketpair()
    try:
        send(left,{'result':'fixture'});assert receive(right)=={'result':'fixture'}
        left.sendall(struct.pack('!I',8_000_001))
        with pytest.raises(ValueError):receive(right)
    finally:left.close();right.close()


def test_executor_mounts_only_this_workspace_and_ephemeral_capability(tmp_path,monkeypatch):
    workspace=tmp_path/('a'*32)/'workspace';workspace.mkdir(parents=True)
    executor=Executor(workspace,dict(engine='podman',image='agp-codex:0.159.0'))
    commands=[]
    def call(*args,**kwargs):
        commands.append(args)
        return '127.0.0.1:32123' if args[0]=='port' else 'container'
    monkeypatch.setattr(executor,'call',call)
    def unwanted_probe(*args,**kwargs):raise AssertionError('Only the native harness may initialize the executor')
    monkeypatch.setattr(socket,'create_connection',unwanted_probe)
    url,token=executor.start()
    assert url=='ws://127.0.0.1:32123' and len(token)>40
    run=commands[0]
    mounts=[run[i+1] for i,v in enumerate(run) if v=='--volume']
    assert mounts==[str(workspace)+':/work:rw',str(workspace.parent/'executor.token')+':/executor.token:ro']
    assert '--userns=keep-id' in run and '--cap-drop=ALL' in run and '--read-only' in run
    assert not any('auth.json' in v or 'CODEX_API_KEY' in v or 'docker.sock' in v for v in run)
    cleanup=[]
    monkeypatch.setattr('agp_remote_yam.remote_codex.subprocess.run',lambda command,**kw:cleanup.append(command))
    executor.close()
    assert cleanup==[['podman','rm','--force',executor.name]]
    assert not executor.token_path.exists()

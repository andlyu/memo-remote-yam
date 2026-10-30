import asyncio
from concurrent.futures import ThreadPoolExecutor
from copy import deepcopy
import json
import threading
import time
import pytest
from agp_remote_yam.service import PacketBridge, Worker, WorkerApp
from agp_remote_yam.manager import Settings


def observation(step=0, **changes):
    return dict(episode_id='episode', lease_id='lease', step_id=step,
                observed_at=time.time(), settled=True, **changes)


def test_lost_poll_and_duplicate_ack_never_duplicate_execution():
    bridge = PacketBridge(observation(), threading.Event())
    with ThreadPoolExecutor() as pool:
        future = pool.submit(bridge.execute, [dict(step_id=0)])
        deadline = time.monotonic() + 1
        while bridge.pending is None and time.monotonic() < deadline: time.sleep(.01)
        packet = bridge.poll(observation())
        assert bridge.poll(observation()) == packet  # lost HTTP response
        bridge.poll(observation(1), packet['id'])
        assert future.result(1)['step_id'] == 1
        assert bridge.poll(observation(1), packet['id']) is None
        with pytest.raises(ValueError, match='cursor'):
            bridge.poll(observation(2))


def test_completion_rejects_wrong_lease_or_cursor_and_stop_does_not_retry():
    bridge = PacketBridge(observation(), threading.Event())
    with ThreadPoolExecutor() as pool:
        future = pool.submit(bridge.execute, [dict(step_id=0)])
        while bridge.pending is None: time.sleep(.01)
        with pytest.raises(ValueError, match='match'):
            bridge.poll(observation(3), '1')
        changed = observation(); changed['lease_id'] = 'new'
        with pytest.raises(ValueError, match='lease'):
            bridge.poll(changed, '1')
        bridge.stopped.set()
        with pytest.raises(RuntimeError, match='not replayed'):
            future.result(1)


def test_worker_authentication_precedes_run_creation(tmp_path):
    app = WorkerApp(Settings(data=tmp_path, demo=True), 's' * 32)
    sent = []
    async def receive():
        raise AssertionError('Unauthenticated body must not be consumed')
    async def send(value): sent.append(value)
    asyncio.run(app(dict(type='http', method='POST', path='/runs', headers=[]), receive, send))
    assert sent[0]['status'] == 403
    assert app.worker.store.list() == []


def test_worker_only_returns_packets_never_opens_a_robot_session(tmp_path, monkeypatch):
    from agp_remote_yam.mock import MockStation
    from remote_yam.session import HttpSessionAPI
    monkeypatch.setattr(HttpSessionAPI, 'create_session', lambda *a, **k: pytest.fail('Worker created a physical session'))
    station = MockStation()
    created = station.create_session('offline')
    state = station.get_robot_observation('yam-1')
    lease = station.get_session(created['session_id'])
    state.update(episode_id=lease['episode_id'], lease_id=lease['lease_id'], step_id=0)
    worker = Worker(Settings(data=tmp_path, demo=True))
    value = dict(client_run_id='a'*32, namespace='b'*64, robot_id='yam-1', task='Offline packet bridge demo', memo=False, observation=state)
    run = worker.start(value)
    assert worker.start(value)['id'] == run['id']
    changed = dict(value, task='changed task')
    with pytest.raises(ValueError, match='already used'):
        worker.start(changed)
    deadline = time.monotonic() + 6
    packet = None
    try:
        while time.monotonic() < deadline:
            result = worker.poll(run['id'], dict(observation=state))
            if result['packet']:
                packet = result['packet']; break
            time.sleep(.03)
        assert packet is not None
        last = packet['points'][-1]
        state.update({k:v for k,v in last.items() if k != 'step_id'})
        state.update(step_id=last['step_id']+1, observed_at=time.time())
        while time.monotonic() < deadline:
            result = worker.poll(run['id'], dict(observation=state, acknowledgement=packet['id']))
            if result['status'] == 'completed': break
            time.sleep(.03)
        assert result['outcome']['status'] == 'done', result
        assert station.trajectory_log == []  # no controller/physical command inside worker
    finally:
        worker.close()


def test_fresh_worker_process_loads_pinned_remote_yam(tmp_path):
    import os, subprocess, sys
    from pathlib import Path
    env = dict(os.environ, PYTHONPATH=str(Path(__file__).resolve().parents[1] / 'src'))
    code = "from pathlib import Path; from agp_remote_yam.service import Worker; from agp_remote_yam.manager import Settings; w=Worker(Settings(data=Path(__import__('sys').argv[1]), demo=True)); import remote_yam.api_depth; w.close()"
    subprocess.run([sys.executable, '-c', code, str(tmp_path)], env=env, check=True, timeout=30)

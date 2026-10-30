"""Acceptance boundaries: method isolation, attribution, replay, honest timing."""
import json
import threading
from types import SimpleNamespace
from unittest.mock import patch
import pytest
from agp_remote_yam.identity import runner_identity, run_timing
from agp_remote_yam.manager import Settings
from agp_remote_yam.policy import AgPPolicy
from agp_remote_yam.recording import RunRecording, replay_info
from agp_remote_yam.runtime import AgentRuntime
from agp_remote_yam.session import AttributedSessionAPI
from agp_remote_yam.storage import RunStore, Journal, atomic_json
from agp_remote_yam.web import App
from test_web_and_storage import request, wait_run


def test_agp_never_loads_skillbook_or_supplies_memo_protocol(tmp_path):
    with patch('agp_remote_yam.memo.Skillbook', side_effect=AssertionError('MEMO must stay separate')):
        app = App(Settings(data=tmp_path, demo=True, memory_encoder='semantic'))
        assert app.manager.skillbook is None
        assert b'MEMO' not in request(app, '/')[2]
        assert request(app, '/api/memories')[0] == 404
        _, cookie, config = request(app, '/api/config')
        status, _, run = request(app, '/api/runs', 'POST', dict(task='Mock acceptance', duration_s=60), cookie=cookie, csrf=config['csrf'])
        assert status == 202
        result = wait_run(app, run['id'], cookie)
        assert result['approach'] == 'Agent as Policy'
        assert result['runner'] == dict(kind='automated', name='Automated', email=None)
        assert result['timing']['outcome'] == 'not_physical'
        assert result['replay']['status'] == 'not_physical'
        assert result['replay']['url'] is None
        assert not any('memo' in name.lower() for name in result['files'])
        directory = app.manager.store.directory(run['id'])
        assert not (directory / 'workspace/bridge_memo').exists()
        prompts = []
        runtime = AgentRuntime(directory, Journal(directory))
        runtime._turn = lambda prompt: (prompts.append(prompt) or dict(status='done', summary='Fixture', evidence=[]))
        runtime._run('Fixture')
        assert 'MEMO' not in prompts[0] and 'memo_client' not in prompts[0]
        assert request(app, '/api/runs', 'POST', dict(task='Rejected MEMO', memo=True), cookie=cookie, csrf=config['csrf'])[0] == 400
        assert request(app, '/api/runs/'+run['id']+'/corrections', 'POST', {}, cookie=cookie, csrf=config['csrf'])[0] == 404
        app.manager.close()


def test_explicit_separate_memo_application_is_preserved(tmp_path):
    app = App(Settings(data=tmp_path, demo=True, memo_site=True))
    assert b'MEMO' in request(app, '/')[2]
    assert app.manager.skillbook is not None
    _, pure = RunStore(tmp_path/'pure').create('No learning')
    _, memo = RunStore(tmp_path/'memo').create('Separate learning', with_memo=True)
    assert not (pure/'workspace/MEMO.md').exists()
    assert (memo/'workspace/MEMO.md').is_file()


def test_human_confirmation_and_automated_identity_are_distinct(tmp_path):
    app = App(Settings(data=tmp_path, demo=True))
    _, cookie, config = request(app, '/api/config')
    for runner in (None, {'name':'Andrew'}, {'kind':'automated','email':'invented@example.test'}):
        assert request(app, '/api/runs', 'POST', dict(task='Invalid signup', runner=runner), cookie=cookie, csrf=config['csrf'])[0] == 400
    confirmed = runner_identity(dict(name=' Runner ', email=' runner@example.test '))
    assert confirmed == dict(kind='human', name='Runner', email='runner@example.test')
    # Synthetic address is a validation fixture, never attributed to a real run.
    assert runner_identity(dict(kind='automated')) == dict(kind='automated', name='Automated', email=None)
    with pytest.raises(ValueError): run_timing(dict(page_entered_at=2, run_clicked_at=1))
    with pytest.raises(ValueError): run_timing(dict(page_entered_at=True, run_clicked_at=2))


def test_confirmed_runner_is_forwarded_to_public_session_without_fake_email():
    calls = []
    api = AttributedSessionAPI('https://example.test', runner=runner_identity(dict(kind='automated')))
    api._request = lambda *args: (calls.append(args) or dict(session_id='fixture', session_capability='test-only'))
    api.create_session('Observe then program', 60)
    assert calls[0][2]['runner_name'] == 'Automated'
    assert 'email' not in calls[0][2]


def test_replay_is_owned_seekable_and_available_only_when_ready(tmp_path):
    app = App(Settings(data=tmp_path, demo=True))
    _, cookie, config = request(app, '/api/config')
    visitor = cookie.split('=',1)[1]
    _, owner, _ = app.identity({'cookie':cookie})
    meta, directory = app.manager.store.create('Replay access fixture')
    app.manager.store.update(directory, owner=owner, approach='Agent as Policy')
    root = directory/'recording'; root.mkdir()
    data = b'fixture bytes for testing access and ranges; not a physical video'
    (root/'physical.mp4').write_bytes(data)
    atomic_json(root/'replay.json', dict(status='ready', physical=True, note='Test fixture only'))
    path = '/api/runs/'+meta['id']+'/replay.mp4'
    assert request(app, path, cookie=cookie)[2] == data
    assert request(app, path, cookie=cookie, extra_headers=[(b'range',b'bytes=2-7')])[0::2] == (206, data[2:8])
    assert request(app, path, cookie=cookie, extra_headers=[(b'range',b'bytes=999-')])[0] == 416
    assert request(app, path)[0] == 403
    atomic_json(root/'replay.json', dict(status='recording'))
    assert request(app, path, cookie=cookie)[0] == 404


def test_unavailable_camera_never_becomes_physical_replay(tmp_path):
    _, directory = RunStore(tmp_path).create('No camera')
    with patch('agp_remote_yam.recording.shutil.which', return_value=None):
        recording = RunRecording(directory, 'yam-1', physical=True)
        recording.start(); recording.finish()
    assert replay_info(directory)['status'] == 'unavailable'
    assert replay_info(directory)['url'] is None


@pytest.mark.parametrize('physical,delta,expected', [(False,1,False),(True,0,False),(True,1,True)])
def test_only_measured_changed_physical_joints_create_motion_evidence(tmp_path, physical, delta, expected):
    journal = Journal(tmp_path)
    runtime = SimpleNamespace(stopped=threading.Event(), finished=threading.Event(), model='fixture', state='test', outcome=None)
    policy = AgPPolicy(runtime, None, journal)
    policy.physical = physical
    policy._observation = dict(left_joints_deg=[0]*6, right_joints_deg=[0]*6)
    policy._pending = dict(count=1, last=0)
    policy.trajectory_completed(dict(step_id=1, settled=True, left_joints_deg=[delta]*6, right_joints_deg=[0]*6, observed_at=1), 1)
    assert bool(journal.after()) is expected
    if expected:
        assert journal.after()[0]['kind'] == 'physical_motion_measured'


def test_selected_station_controls_camera_and_readiness_contract(tmp_path, monkeypatch):
    app=App(Settings(data=tmp_path))
    robot='robot-ba8413962083809c'
    status, _, config=request(app,'/api/config?robot_id='+robot)
    assert status==200 and config['robot_id']==robot
    assert config['video_stream']['path']=='robo-house'
    assert len(config['robots'])==2
    monkeypatch.setattr('remote_yam.session.HttpSessionAPI.get_queue_snapshot', lambda self: dict(stations=[dict(jetson_id=robot,connected=True,available=False,queue_ready=True)]))
    assert request(app,'/api/station?robot_id='+robot)[2]['connected'] is True
    assert request(app,'/api/config?robot_id=unconfigured')[0]==400
    _, cookie, csrf=request(app,'/api/config')
    assert request(app,'/api/runs','POST',dict(task='Rejected station',robot_id='unconfigured'),cookie=cookie,csrf=csrf['csrf'])[0]==400


def test_legacy_memo_cannot_be_relabelled_or_seed_a_pure_agp_run(tmp_path):
    app=App(Settings(data=tmp_path,demo=True))
    _,cookie,config=request(app,'/api/config')
    _,owner,_=app.identity({'cookie':cookie})
    meta,directory=app.manager.store.create('Preserved legacy MEMO',with_memo=True)
    app.manager.store.update(directory,owner=owner,approach='Agent as Policy + MEMO',memo_enabled=True,status='stopped')
    path='/api/runs/'+meta['id']
    assert request(app,'/api/runs',cookie=cookie)[2]['runs']==[]
    assert request(app,path,cookie=cookie)[0]==404
    assert request(app,path+'/files/MEMO.md',cookie=cookie)[0]==404
    assert request(app,'/api/runs','POST',dict(task='Rejected legacy seed',experience_run=meta['id']),cookie=cookie,csrf=config['csrf'])[0]==404
    assert len(app.manager.store.list())==1
    assert (directory/'workspace/MEMO.md').is_file()

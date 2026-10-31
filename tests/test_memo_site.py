"""The independent MEMO site retains identity, replay and correction behavior."""
import json
import pytest
from agp_remote_yam.manager import Settings
from agp_remote_yam.web import App
from test_web_and_storage import request, wait_run


def test_memo_run_requires_identity_and_retains_method_context(tmp_path):
    app = App(Settings(data=tmp_path, demo=True, memo_site=True))
    _, cookie, config = request(app, '/api/config')
    assert config['approach'] == 'MEMO'
    assert config['source_repository'] == 'https://github.com/andlyu/memo-remote-yam'
    assert cookie.startswith('memo_visitor=')
    assert request(app, '/api/runs', 'POST', {'task':'Missing identity', 'runner':None}, cookie=cookie, csrf=config['csrf'])[0] == 400
    status, _, result = request(app, '/api/runs', 'POST', {
        'task':'Mock MEMO transport', 'duration_s':60,
        'runner':{'kind':'automated','name':'Automated'}}, cookie=cookie, csrf=config['csrf'])
    assert status == 202
    run = wait_run(app, result['id'], cookie)
    assert run['approach'] == 'MEMO' and run['memo_enabled'] is True
    assert run['runner'] == {'kind':'automated','name':'Automated','email':None}
    assert run['replay']['status'] == 'not_physical'
    assert 'MEMO.md' in run['files']
    app.manager.close()


def test_memo_page_combines_learning_identity_and_replay(tmp_path):
    app = App(Settings(data=tmp_path, demo=True, memo_site=True))
    html = request(app, '/')[2].decode()
    for item in ('Run MEMO', 'runner-name', 'runner-email', 'run-replay', 'correction-form', 'skillbook', 'initial-config'):
        assert item in html
    assert 'collab.me.vt.edu/memo/' in html
    script = request(app, '/static/app.js')[2].decode()
    assert 'activeRun' in script and 'renderReplay' in script and 'memo-runner' in script
    assert 'memory()' in script and 'pendingCorrection' in script


def test_memo_cannot_be_disabled_silently(tmp_path):
    app = App(Settings(data=tmp_path, demo=True, memo_site=True))
    _, cookie, config = request(app, '/api/config')
    assert request(app, '/api/runs', 'POST', {
        'task':'Wrong method', 'memo':False, 'runner':{'kind':'automated'}},
        cookie=cookie, csrf=config['csrf'])[0] == 400


def test_offline_refinement_never_has_robot_commands():
    from agp_remote_yam.refinement import NoRobotBackend
    for command in ('state','frames','move_joints','move_ee','gripper'):
        with pytest.raises(ValueError, match='offline'):
            NoRobotBackend().command('left', command, {})


def test_refinement_preserves_sources_and_owner_without_a_robot_session(tmp_path, monkeypatch):
    import sys
    import time
    from agp_remote_yam.runtime import AgentRuntime
    from agp_remote_yam.session import AttributedSessionAPI
    app = App(Settings(data=tmp_path, demo=True, memo_site=True))
    _, cookie, config = request(app, '/api/config')
    _, owner, _ = app.identity({'cookie':cookie})
    for content in ('Clear the rim first.', 'Raise above the rim before translating.'):
        app.manager.skillbook.add(owner, action='MOVE(block)', scene='rim', kind='guidance', content=content, run_id='fixture')
    program = '''import json, subprocess, sys
from pathlib import Path
def call(command, value):
    return json.loads(subprocess.check_output([sys.executable, 'memo_client.py', command, json.dumps(value)], text=True))
rows=call('list', {})['memories']
assert len(rows)==2
call('consolidate', {'action':'MOVE(block)', 'scene':'rim', 'kind':'guidance',
    'content':'Clear the rim before translating; preserve all motion constraints.',
    'source_ids':[r['id'] for r in rows]})
Path('FINAL.json').write_text(json.dumps({'status':'done','summary':'Offline fixture merged two related lessons.','evidence':[]}))
'''
    monkeypatch.setattr(AgentRuntime, 'check_available', lambda _:None)
    monkeypatch.setattr(AgentRuntime, 'command', lambda _:[sys.executable, '-c', program])
    monkeypatch.setattr(AttributedSessionAPI, 'create_session', lambda *_:pytest.fail('Offline refinement must never join a robot queue'))
    path='/api/skillbook/jobs'
    assert request(app, path, 'POST', {'runner':{'kind':'automated'}}, cookie=cookie)[0] == 403
    status, _, job=request(app, path, 'POST', {'runner':{'kind':'automated'}}, cookie=cookie, csrf=config['csrf'])
    assert status==202
    for _ in range(100):
        result=request(app, path+'/'+job['id'], cookie=cookie)[2]
        if not result['active']:break
        time.sleep(.05)
    assert not result['active'] and result['outcome']['status']=='done', result
    assert result['mode']=='offline_memory' and result['approach']=='MEMO'
    rows=app.manager.skillbook.list(owner)
    assert len(rows)==1 and len(rows[0]['parents'])==2
    assert request(app, '/api/runs', cookie=cookie)[2]['runs']==[]
    assert request(app, path+'/'+job['id'])[0]==403
    app.manager.close()


def test_memory_retrieval_can_complete_before_robot_admission(tmp_path):
    import sys
    import time
    from agp_remote_yam.memo import Skillbook, MemoryChannel
    from agp_remote_yam.runtime import AgentRuntime
    from agp_remote_yam.storage import RunStore, Journal, atomic_json
    _, directory = RunStore(tmp_path/'runs').create('Queue memory fixture', with_memo=True)
    journal = Journal(directory)
    runtime = AgentRuntime(directory, journal, mode='remote')
    runtime.command = lambda:[sys.executable, '-c', 'import time; time.sleep(30)']
    runtime.memory = MemoryChannel(Skillbook(tmp_path/'memory.sqlite3', 'lexical'), 'owner', directory, journal)
    try:
        runtime.prepare('Offline admission fixture')
        atomic_json(directory/'workspace/bridge_memo/req_000001.json',
                    dict(id=1,cmd='context',args=dict(action='GENERAL')))
        response=directory/'workspace/bridge_memo/resp_000001.json'
        deadline=time.monotonic()+2
        while not response.exists() and time.monotonic()<deadline:time.sleep(.01)
        assert json.loads(response.read_text())['ok'] is True
        assert not runtime.backend_ready.is_set()
        # Early robot requests are not scanned or released by the memory bridge.
        atomic_json(directory/'workspace/bridge/req_000001.json',dict(id=1,cmd='move_joints',args={}))
        time.sleep(.05)
        assert not (directory/'workspace/bridge/resp_000001.json').exists()
    finally:
        runtime.cancel()
        assert runtime.finished.wait(3)


def test_completed_metadata_cannot_be_paired_with_stale_outcome(tmp_path, monkeypatch):
    from pathlib import Path
    app=App(Settings(data=tmp_path, demo=True, memo_site=True))
    metadata, directory=app.manager.store.create('Completion race fixture',with_memo=True)
    completed=app.manager.store.update(directory,owner='owner',approach='MEMO',status='completed',
        outcome=dict(status='done',summary='Fixture complete',evidence=[]))
    stale=json.dumps(dict(completed,status='running',outcome=None))
    read=Path.read_text
    calls=0
    def racing(path,*args,**kwargs):
        nonlocal calls
        if path==directory/'run.json':
            calls+=1
            if calls==2:return stale
        return read(path,*args,**kwargs)
    monkeypatch.setattr(Path,'read_text',racing)
    result=app.manager.detail(metadata['id'],'owner')
    assert result['active'] is False and result['outcome']['status']=='done'


def test_template_rejection_explains_the_required_code_and_preserves_memory(tmp_path):
    from agp_remote_yam.memo import Skillbook
    book=Skillbook(tmp_path/'book.sqlite3','lexical')
    with pytest.raises(ValueError,match='literal Python source'):
        book.add('owner',action='MOVE(joint)',scene='',kind='template',
                 content='Parameterized MOVE(joint) template: add delta to joint0=0.02.',run_id='fixture')
    assert book.version()==0 and book.list('owner')==[]


def test_verification_mode_retains_the_confirmed_human_identity(tmp_path):
    app=App(Settings(data=tmp_path,demo=True,memo_site=True))
    _,cookie,config=request(app,'/api/config')
    body={'task':'Mock verification attribution','duration_s':60,
          'runner':{'kind':'human','name':'Confirmed Tester','email':'tester@example.com'},
          'execution_mode':'automated_test'}
    status,_,result=request(app,'/api/runs','POST',body,cookie=cookie,csrf=config['csrf'])
    assert status==202
    value=wait_run(app,result['id'],cookie)
    assert value['runner']['kind']=='human' and value['runner']['name']=='Confirmed Tester'
    assert value['execution_mode']=='automated_test' and value['approach']=='MEMO'
    body['execution_mode']='unrecognised'
    assert request(app,'/api/runs','POST',body,cookie=cookie,csrf=config['csrf'])[0]==400
    app.manager.close()

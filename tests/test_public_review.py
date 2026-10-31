import json
from agp_remote_yam.web import App
from agp_remote_yam.manager import Settings
from agp_remote_yam.storage import atomic_json
from test_web_and_storage import request


def test_public_demo_review_redacts_contacts_and_never_grants_controls(tmp_path):
    app = App(Settings(data=tmp_path, demo=True, memo_site=True))
    _, cookie, config = request(app, '/api/config')
    _, owner, _ = app.identity({'cookie':cookie})
    meta, directory = app.manager.store.create('Public demo; private person@example.test', with_memo=True)
    app.manager.store.update(directory, owner=owner, approach='MEMO', status='stopped', mode='physical_api',
        runner=dict(kind='human',name='Confirmed Tester',email='person@example.test'),
        outcome=dict(status='done',summary='Demo result',evidence=[]))
    atomic_json(directory/'workspace/scratch/program.json', {'owner':owner, 'email':'person@example.test', 'result':'demo'})
    recording=directory/'recording';recording.mkdir()
    (recording/'physical.mp4').write_bytes(b'demo video fixture; not physical evidence')
    atomic_json(recording/'replay.json',dict(status='ready',physical=True))
    rid=meta['id'];_, stranger, theirs=request(app,'/api/config')
    status,_,value=request(app,'/api/runs/'+rid,cookie=stranger)
    assert status==200
    assert value['owned'] is False and value['model']=='MEMO'
    assert owner not in json.dumps(value) and 'person@example.test' not in json.dumps(value)
    assert request(app,'/api/runs',cookie=stranger)[2]['runs'][0]['id']==rid
    assert request(app,'/api/runs/'+rid+'/replay.mp4',cookie=stranger)[0]==200
    assert request(app,'/api/runs/'+rid+'/files/scratch/program.json',cookie=stranger)[2]=={'result':'demo'}
    assert request(app,'/api/runs/'+rid+'/files/robot_client.py',cookie=stranger)[0]==404
    for suffix in ('stop','corrections'):
        assert request(app,'/api/runs/'+rid+'/'+suffix,'POST',{},cookie=stranger,csrf=theirs['csrf'])[0]==403
    assert request(app,'/api/memories',cookie=stranger)[2]['memories']==[]
    app.manager.close()


def test_visible_acceptance_fraction_counts_only_verified_requirements(tmp_path):
    app=App(Settings(data=tmp_path,demo=True,memo_site=True))
    status,_,value=request(app,'/api/acceptance')
    assert status==200 and value['total']==15
    assert value['passed']==sum(row['passed'] for row in value['requirements'])
    assert value['percentage']==round(100*value['passed']/value['total'],1)
    config=request(app,'/api/config')[2]
    assert config['model']=='MEMO' and config['foundation_model'] is None

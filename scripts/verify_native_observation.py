"""Actual model observation discovery on explicit mock RGB-D; never moves hardware."""
import argparse
import json
import os
from pathlib import Path
import time
import uuid
import numpy as np
from agp_remote_yam.manager import RunManager, Settings

p=argparse.ArgumentParser(description=__doc__)
p.add_argument('--data',type=Path,required=True)
p.add_argument('--config',type=Path,required=True)
p.add_argument('--runner-name',required=True)
p.add_argument('--runner-email',required=True)
a=p.parse_args();a.data.mkdir(parents=True,exist_ok=True)
config=json.loads(a.config.read_text());config['run_root']=str(a.data.resolve()/'runs')
private=a.data/'native-config.json';private.write_text(json.dumps(config));private.chmod(0o600)
os.environ['AGP_REMOTE_CODEX_CONFIG']=str(private)
manager=RunManager(Settings(data=a.data,mock_robot=True,memo_site=True,agent_mode='remote',
    model=config['model'],memory_encoder='semantic'))
try:
    manager.skillbook.encoder.encode('GENERAL')
    owner='native-sensors-'+uuid.uuid4().hex
    rid=manager.start('MOCK ONLY observation preflight for apple-to-plate planning. Initial RGB previews '
        'omit numeric depth. Establish whether fresh numeric overhead and wrist depth plus calibration '
        'can be obtained using the documented interface. Inspect the actual arrays with Python/NumPy '
        'and write scratch/depth_check.json with top_shape, wrist_shape, top_min_m and wrist_min_m. '
        'Do not issue any arm/gripper movement. This fixture does not verify physical accuracy or '
        'apple placement. Return done only for the observation check, or report the actual sensor error.',
        owner,duration=120,runner=dict(kind='human',name=a.runner_name,email=a.runner_email),
        memo=True,execution_mode='automated_test')
    print(json.dumps(dict(run_id=rid,physical=False,scope='Actual model, mock RGB-D, read-only')),flush=True)
    start=time.monotonic()
    while rid in manager.active:
        if time.monotonic()-start>150:
            manager.stop(rid,owner);raise TimeoutError('Observation verification deadline')
        time.sleep(.2)
    result=manager.detail(rid,owner,-1)
    assert result['outcome']['status']=='done',result
    assert not any(e['kind']=='tool_call' and e['message'] in ('move_joints','move_ee','gripper') for e in result['events'])
    captures=[e['response']['files'] for e in result['events'] if e['kind']=='tool_result'
        and e['message']=='frames' and e['response'].get('ok') and 'top_depth' in e['response'].get('files',{})]
    assert captures,'Model did not request actual numeric top/wrist depth'
    workspace=manager.store.directory(rid)/'workspace'
    saved=json.loads((workspace/'scratch/depth_check.json').read_text())
    for role in ('top','wrist'):
        depth=np.load(workspace/captures[-1][role+'_depth'],allow_pickle=False)
        assert saved[role+'_shape']==list(depth.shape)
        assert saved[role+'_min_m']==float(depth.min())
    receipt=dict(status='passed',run_id=rid,physical=False,motion_commands=0,
        model=config['model'],elapsed_s=time.monotonic()-start,depth_check=saved,
        outcome=result['outcome'],scope='Actual inference and numeric mock-depth inspection only; no physical task proof')
    (a.data/'verification.json').write_text(json.dumps(receipt,indent=2)+'\n')
    print(json.dumps(receipt),flush=True)
finally:manager.close()

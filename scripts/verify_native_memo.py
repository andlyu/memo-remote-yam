"""Actual model and semantic MEMO with mock arms; never acquires a physical lease."""
import argparse
import json
import os
from pathlib import Path
import threading
import time
import uuid
from agp_remote_yam.manager import RunManager, Settings
from agp_remote_yam.refinement import start_refinement, detail
from agp_remote_yam import mock

p = argparse.ArgumentParser(description=__doc__)
p.add_argument('--data', type=Path, required=True)
p.add_argument('--config', type=Path, default=Path('/etc/memo-remote-codex.json'))
a = p.parse_args()
a.data.mkdir(parents=True, exist_ok=True)
config = json.loads(a.config.read_text())
config['run_root'] = str(a.data.resolve()/'runs')
private = a.data/'native-config.json'
private.write_text(json.dumps(config)); private.chmod(0o600)
os.environ['AGP_REMOTE_CODEX_CONFIG'] = str(private.resolve())
manager = RunManager(Settings(data=a.data, mock_robot=True, memo_site=True,
    agent_mode='remote', model=config['model'], memory_encoder='semantic'))
boot = time.monotonic()
manager.skillbook.encoder.encode('GENERAL')
print(json.dumps(dict(phase='semantic_readiness', elapsed_s=time.monotonic()-boot,
                     encoder=manager.skillbook.encoder.identity)), flush=True)
original = mock.MockStation


class DelayedStation(original):
    def activate(self, session_id):
        scheduled = getattr(self, '_memo_activation_scheduled', set())
        if session_id in scheduled:
            return
        scheduled.add(session_id)
        self._memo_activation_scheduled = scheduled
        def admitted():
            if self._record(session_id)['status'] == 'queued':
                super(DelayedStation, self).activate(session_id)
        timer = threading.Timer(10, admitted)
        timer.daemon = True
        timer.start()


mock.MockStation = DelayedStation
owner = 'automated-native-'+uuid.uuid4().hex
runner = dict(kind='automated', name='Automated')
receipts = []


def execute(task, corrections=()):
    started = time.monotonic()
    rid = manager.start(task, owner, duration=180, runner=runner, memo=True)
    for i, content in enumerate(corrections):
        manager.correct(rid, owner, content, 'native-fixture-'+str(i))
    print(json.dumps(dict(phase='run', run_id=rid, approach='MEMO', runner=runner, physical=False)), flush=True)
    seen = -1
    while rid in manager.active:
        value = manager.detail(rid, owner, seen)
        for event in value['events']:
            seen = event['id']
            if event['kind'] in ('agent', 'assistant', 'memory_saved', 'error', 'tool_call'):
                print(json.dumps(dict(phase=event['kind'], elapsed_s=round(time.monotonic()-started, 3),
                                      message=event['message'][:200])), flush=True)
        if time.monotonic()-started > 210:
            manager.stop(rid, owner)
            raise TimeoutError('Actual-model mock run deadline')
        time.sleep(.2)
    value = manager.detail(rid, owner, -1)
    motions = [e for e in value['events'] if e['kind'] == 'tool_result'
               and e['response'].get('execution') == 'measured_completed_and_settled']
    assert value['outcome']['status'] == 'done', value['outcome']
    assert len(motions) == 1 and motions[0]['response']['physical'] is False
    receipt = dict(run_id=rid, approach='MEMO', runner=runner, physical=False,
        elapsed_s=time.monotonic()-started, first_mock_completion_s=motions[0]['time']-value['created_at'],
        outcome=value['outcome'], memory_version=value['memory_version'], events=value['events'])
    receipts.append(receipt)
    print(json.dumps({k:v for k,v in receipt.items() if k != 'events'}), flush=True)
    return value


try:
    first = execute(
        'MOCK ONLY: from fresh measured left-arm state and supplied mock RGB, generate and execute '
        'one program changing left joint0 by +0.02 radians once. Retain all other measured targets. '
        'Read fresh state inside the movement program; inspect supplied post-admission images before '
        'deciding to execute. Verify measured delta and fresh mock images afterwards. Receive the owner '
        'corrections and paraphrase each into separate related GENERAL guidance; save one successful '
        'parameterized MOVE(LEFT_JOINT_0) template with source and verification evidence. '
        'No physical success is claimed.', [
            'Change only the selected joint; keep the other measured joints unchanged.',
            'Keep the other arm and both measured gripper targets unchanged.'])
    assert all(row['delivered'] is not None for row in first['corrections'])
    learned = manager.skillbook.list(owner)
    assert any(row['kind'] == 'template' for row in learned), learned
    assert sum(row['kind'] == 'guidance' for row in learned) >= 2, learned
    saved = {row['id'] for row in learned}
    second = execute(
        'MOCK ONLY: retrieve the saved MEMO lessons, inspect supplied fresh mock images and state, '
        'then generate a new program for exactly one -0.015-radian relative change to left joint0. '
        'Retain all other measured joints, the other arm and both grippers. Recompute from this run, '
        'never replay previous absolute targets. Verify fresh state and RGB; report no physical robot '
        'moved. Use prior guidance/templates only as hypotheses.')
    retrieved = {i for e in second['events'] if e['kind'] == 'memory_retrieved'
                 for i in e.get('memory_ids', [])}
    assert saved & retrieved, (saved, retrieved)
    jid = start_refinement(manager, owner, runner)
    started = time.monotonic()
    while jid in manager.active:
        if time.monotonic()-started > 210:
            manager.stop(jid, owner)
            raise TimeoutError('Offline refinement deadline')
        time.sleep(.3)
    job = detail(manager, jid, owner)
    assert job['outcome']['status'] == 'done', job
    assert not any(e['kind'] == 'tool_call' and e.get('arm') in ('left', 'right') for e in job['events'])
    after = manager.skillbook.list(owner)
    assert any(row['parents'] for row in after), after
    report = dict(status='passed', model=config['model'], approach='MEMO', runner=runner,
        physical=False, admission_wait_s=10, runs=receipts, learned=learned,
        retrieved_memory_ids=sorted(retrieved), refinement=dict(id=jid, outcome=job['outcome'],
        mode=job['mode'], events=job['events']), final_memories=after, physical_motion_verified=False)
    (a.data/'verification.json').write_text(json.dumps(report, indent=2)+'\n')
    print(json.dumps(dict(status='passed', run_ids=[r['run_id'] for r in receipts],
                         refinement_job=jid, physical=False)), flush=True)
finally:
    manager.close()

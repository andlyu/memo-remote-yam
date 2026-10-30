"""Real coding agent learns and retrieves MEMO against a mock robot only."""
import argparse,json,time
from pathlib import Path
from agp_remote_yam.manager import RunManager,Settings


def main():
 parser=argparse.ArgumentParser(description=__doc__)
 parser.add_argument('--data',type=Path,default=Path('outputs/memo-smoke'))
 parser.add_argument('--model',default='gpt-6-astra')
 parser.add_argument('--memory-encoder',choices=('semantic','lexical'),default='semantic')
 parser.add_argument('--agent',choices=('codex','docker','remote'),default='codex')
 parser.add_argument('--duration',type=int,default=180)
 parser.add_argument('--namespace',default='memo-smoke',help='Use a fresh namespace for independent deployment validation')
 args=parser.parse_args()
 manager=RunManager(Settings(data=args.data,mock_robot=True,model=args.model,memory_encoder=args.memory_encoder,agent_mode=args.agent))
 start=time.monotonic();owner=args.namespace;receipts=[]
 def wait(identity):
  deadline=time.monotonic()+args.duration+30
  while identity in manager.active and time.monotonic()<deadline:time.sleep(.15)
  if identity in manager.active:raise TimeoutError('MEMO mock smoke exceeded deadline')
  result=manager.detail(identity,owner)
  if not result.get('outcome') or result['outcome']['status']!='done':
   raise RuntimeError(json.dumps(dict(status=result['status'],outcome=result.get('outcome'),error=result.get('error'))))
  receipts.append(dict(id=identity,status=result['status'],outcome=result['outcome'],
                       events=[{k:v for k,v in e.items() if k not in ('time',)} for e in result['events'] if e['kind'] in ('memory_saved','memory_retrieved','correction_queued','correction_delivered')]))
  return result
 try:
  task=('This is an OFFLINE MOCK test; no physical task can be validated. Use MEMO context ACTION PICK(block), '
        'scene green block near bowl. Read the queued owner correction. Write and run scratch/smoke.py '
        'to call the original robot client for state, frames with depth false, a +0.01 rad change to '
        'only left joint 0 from its measured value, then state and frames. '
        'Save a position-independent guidance memory paraphrasing the correction, and one parameterized '
        'function template using current scratch/smoke.py as evidence (no literal XYZ triplets). '
        'The template is a mock-tested/unverified hypothesis. Finish done and explicitly say no physical success was validated.')
  identity=manager.start(task,owner,duration=args.duration,memo=True)
  manager.correct(identity,owner,'Lift above the bowl rim before moving laterally; do not drag the block across the rim.','smoke-correction-001')
  print(json.dumps(dict(phase='learn',run_id=identity)),flush=True);wait(identity)
  memories=manager.skillbook.list(owner)
  assert any(r['kind']=='guidance' for r in memories) and any(r['kind']=='template' for r in memories),memories
  task=('OFFLINE MOCK retrieval test. Call memo_client.py context with action PICK(cube), scene wood block beside dish. '
        'Read the returned guidance and template. Save scratch/retrieval.json containing their exact memory IDs and '
        'explain how the bowl-rim lesson applies to this related task. Read mock state and a fresh RGB capture with '
        'depth false. Do not move the robot. Return done only if relevant prior memory was retrieved; explicitly say '
        'this verifies retrieval, not physical transfer performance.')
  identity=manager.start(task,owner,duration=args.duration,memo=True)
  print(json.dumps(dict(phase='retrieve',run_id=identity)),flush=True);result=wait(identity)
  ids=[e.get('memory_ids') for e in result['events'] if e['kind']=='memory_retrieved']
  assert any(ids),ids
  report=dict(elapsed_s=time.monotonic()-start,encoder=manager.skillbook.encoder.identity,runs=receipts,
              memory_count=len(memories),scope='Real coding-model inference with offline mock robot; no physical robot session')
  args.data.mkdir(parents=True,exist_ok=True)
  (args.data/'receipt.json').write_text(json.dumps(report,indent=2)+'\n')
  print(json.dumps(dict(elapsed_s=report['elapsed_s'],memory_count=len(memories),result='PASS'),indent=2),flush=True)
 finally:manager.close()

if __name__=='__main__':main()

"""Offline MEMO clustering and model consolidation. No robot session or transport."""
import argparse
import json
from pathlib import Path
import time
from agp_remote_yam.memo import Skillbook, MemoryChannel
from agp_remote_yam.runtime import AgentRuntime
from agp_remote_yam.storage import RunStore, Journal


class NoRobot:
    def command(self, *_):
        raise RuntimeError("Offline consolidation has no robot access")


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--data', type=Path, default=Path('data'))
    parser.add_argument('--namespace', required=True, help='Owner namespace from local run.json; never a browser-supplied owner')
    parser.add_argument('--memory-encoder', choices=('semantic','lexical'), default='semantic')
    parser.add_argument('--model', default='gpt-6-astra')
    parser.add_argument('--dry-run', action='store_true', help='List candidate clusters without model usage or mutations')
    args = parser.parse_args()
    book = Skillbook(args.data/'skillbook.sqlite3', args.memory_encoder)
    groups = book.clusters(args.namespace)
    print(json.dumps(dict(version=book.version(), candidate_clusters=groups),indent=2),flush=True)
    if args.dry_run or not groups:
        return
    task = ('Consolidate these candidate clusters using memo_client.py consolidate. For each group keep '
            'the same kind, choose a general action/scene key, preserve all constraints and represent '
            'conflicting guidance with its conditions. Templates must stay parameterized; save rewritten '
            'code under scratch/ as evidence. Do not make a robot request. Candidate clusters: ' + json.dumps(groups))
    _, directory = RunStore(args.data/'maintenance').create(task)
    runtime = AgentRuntime(directory, Journal(directory), model=args.model, timeout_s=300)
    runtime.memory = MemoryChannel(book,args.namespace,directory,runtime.journal)
    runtime.maintenance = True
    runtime.check_available()
    try:
        runtime.start(NoRobot(),task)
        if not runtime.finished.wait(330):
            raise TimeoutError('Consolidation exceeded its deadline')
        print(json.dumps(dict(outcome=runtime.outcome,version=book.version()),indent=2))
        if not runtime.outcome or runtime.outcome['status'] != 'done':
            raise SystemExit(1)
    finally:
        runtime.cancel()


if __name__=='__main__': main()

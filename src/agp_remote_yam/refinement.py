"""Agent-authored skillbook consolidation with no robot session or command path."""
import json
import threading
import time
from .identity import runner_identity
from .memo import MemoryChannel
from .runtime import AgentRuntime
from .storage import Journal


class NoRobotBackend:
    def command(self, *_):
        raise ValueError("Skillbook refinement is offline; robot commands are unavailable")


def start_refinement(manager, owner, runner):
    if not manager.settings.memo_site:
        raise FileNotFoundError()
    runner = runner_identity(runner)
    with manager.lock:
        if any(row['owner'] == owner for row in manager.active.values()):
            raise ValueError("Finish or stop your active work before refining the skillbook")
        if len(manager.skillbook.list(owner)) < 2:
            raise ValueError("At least two saved lessons are needed for refinement")
        metadata, directory = manager.store.create('Refine related MEMO lessons', with_memo=True)
        journal = Journal(directory)
        runtime = AgentRuntime(directory, journal, model=manager.settings.model,
            mode=manager.settings.agent_mode, timeout_s=180, executable=manager.settings.codex)
        runtime.maintenance = True
        runtime.memory = MemoryChannel(manager.skillbook, owner, directory, journal, enabled=True)
        runtime.check_available()
        manager.store.update(directory, owner=owner, job_kind='skillbook_refinement',
            approach='MEMO', runner=runner, mode='offline_memory', status='running',
            memory_version=runtime.memory.version, memo_enabled=True)
        context = dict(owner=owner, runtime=runtime, journal=journal, directory=directory,
                       controller=None, stopped=threading.Event(), memory=runtime.memory)
        manager.active[metadata['id']] = context
        threading.Thread(target=_work, args=(manager, context), name='memo-refinement', daemon=True).start()
        return metadata['id']


def _work(manager, context):
    runtime, directory, journal = context['runtime'], context['directory'], context['journal']
    try:
        runtime.start(NoRobotBackend(),
            'List this owner\'s skillbook. Consolidate only genuinely related redundant guidance or '
            'templates, preserving every motion constraint, conflict and source ID. Never merge unrelated '
            'kinds. For a template rewrite, save its parameterized source in scratch/ and cite it as '
            'rewrite evidence, never as new physical validation. Do not invent outcomes. If nothing '
            'needs consolidation, explain that and finish without changes. No robot session exists.')
        runtime.finished.wait(200)
        if not runtime.finished.is_set():
            raise TimeoutError('Offline refinement exceeded its deadline')
        manager.store.update(directory, status='stopped' if context['stopped'].is_set() else 'completed',
            outcome=runtime.outcome, ended_at=time.time())
    except Exception as exc:
        journal.add('error', 'Offline refinement failed', detail=str(exc))
        manager.store.update(directory, status='failed', error=str(exc), ended_at=time.time())
    finally:
        runtime.cancel()
        with manager.lock:
            manager.active.pop(directory.name, None)


def detail(manager, identity, owner):
    directory = manager.owned(identity, owner)
    metadata = json.loads((directory/'run.json').read_text())
    if metadata.get('job_kind') != 'skillbook_refinement':
        raise FileNotFoundError()
    return manager.detail(identity, owner)

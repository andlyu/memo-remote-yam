import json
from pathlib import Path
import pytest
from agp_remote_yam.memo import Skillbook, MemoryChannel
from agp_remote_yam.storage import RunStore, Journal


def book(tmp_path):
    return Skillbook(tmp_path / 'memory.sqlite3', 'lexical')


def add(memory, owner='alice', **changes):
    value = dict(action='PICK(block)', scene='green block towel', kind='guidance',
                 content='Approach above the block before closing the fingers.', run_id='run-one')
    value.update(changes)
    return memory.add(owner, **value)


def test_retrieval_is_durable_scoped_and_ranks_action_then_scene(tmp_path):
    memory = book(tmp_path)
    first = add(memory)
    add(memory, action='OPEN(drawer)', scene='drawer handle', content='Pull along the drawer axis.')
    add(memory, owner='bob', content='Private other visitor guidance.')
    rows = Skillbook(memory.path, 'lexical').retrieve('alice', 'PICK(cube)', 'block towel')
    assert rows[0]['id'] == first['id']
    assert all('Private' not in row['content'] for row in rows)
    assert memory.retrieve('nobody', 'PICK(block)') == []


def test_consolidation_retains_sources_and_versioned_snapshots(tmp_path):
    memory = book(tmp_path)
    one = add(memory, content='Approach above the rim.')
    two = add(memory, content='Keep the fingers above the rim until aligned.')
    before = memory.version()
    merged = add(memory, content='Align above the rim before descending.', parents=[one['id'], two['id']])
    assert [r['id'] for r in memory.list('alice')] == [merged['id']]
    assert {r['id'] for r in memory.list('alice', version=before)} == {one['id'], two['id']}
    assert merged['parents'] == [one['id'], two['id']]
    assert add(memory, content=merged['content'])['id'] == merged['id']
    with pytest.raises(ValueError, match='same owner'):
        add(memory, owner='bob', parents=[merged['id']])


def test_raw_correction_is_idempotent_delivered_once_and_retained(tmp_path):
    memory = book(tmp_path)
    _, directory = RunStore(tmp_path / 'runs').create('pick a block')
    channel = MemoryChannel(memory, 'alice', directory, Journal(directory))
    channel.command('context', dict(action='PICK(block)', scene='block towel'))
    first = channel.correct('Go higher before crossing the rim.', 'request-one')
    assert channel.correct(first['content'], 'request-one')['id'] == first['id']
    assert len(channel.updates(deliver=True)) == 1
    assert channel.updates(deliver=True) == []
    assert channel.updates()[0]['content'] == first['content']
    saved = channel.command('remember', dict(content='Clear the rim before translating laterally.'))['memory']
    assert saved['evidence'][0]['correction_id'] == first['id']
    assert saved['validation'] == 'agent_authored_unverified'
    assert channel.command('context', {})['memories'] == []  # pinned before the new lesson
    with pytest.raises(ValueError, match='already used'):
        channel.correct('different text', 'request-one')


def test_disabled_memory_delivers_corrections_without_learning(tmp_path):
    memory = book(tmp_path)
    add(memory)
    _, directory = RunStore(tmp_path / 'runs').create('task')
    channel = MemoryChannel(memory, 'alice', directory, Journal(directory), enabled=False)
    channel.correct('Use the left arm.', 'one')
    result = channel.command('context', dict(action='PICK(block)'))
    assert not result['enabled'] and not result['memories'] and len(result['corrections']) == 1
    with pytest.raises(ValueError, match='disabled'):
        channel.command('remember', dict(content='something'))


def test_templates_need_parameterized_function_and_run_evidence(tmp_path):
    memory = book(tmp_path)
    _, directory = RunStore(tmp_path / 'runs').create('task')
    channel = MemoryChannel(memory, 'alice', directory, Journal(directory))
    with pytest.raises(ValueError, match='evidence'):
        channel.command('remember', dict(kind='template', content='def pick(target):\n    return target'))
    (directory / 'workspace/scratch/code.py').write_text('def pick(target):\n    return target\n')
    result = channel.command('remember', dict(kind='template', content='def pick(target):\n    return target', evidence=['scratch/code.py']))
    assert result['memory']['evidence'][0]['path'] == 'scratch/code.py'
    with pytest.raises(ValueError, match='XYZ'):
        channel.command('remember', dict(kind='template', content='def pick(target):\n    pos = [0.2, 0.3, 0.4]', evidence=['scratch/code.py']))
    (directory / 'workspace/scratch/leak.py').symlink_to(tmp_path / 'memory.sqlite3')
    with pytest.raises(OSError):
        channel.command('remember', dict(kind='template', content='def pick(target):\n    return target', evidence=['scratch/leak.py']))


def test_template_keeps_fixed_grasp_orientation_but_rejects_xyz_pose():
    from agp_remote_yam.memo import validate_template
    validate_template('def pick(target_pos):\n    orientation = [0, 0, 90]\n    return target_pos, orientation')
    with pytest.raises(ValueError, match='XYZ'):
        validate_template('def pick(target_pos):\n    return dict(x=-0.3, y=0.2, z=0.1)')

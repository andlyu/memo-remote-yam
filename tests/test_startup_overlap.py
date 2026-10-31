"""Read-only planning preparation must not postpone normal queue admission."""
import threading
import time
from agp_remote_yam.manager import RunManager, Settings
from agp_remote_yam.runtime import AgentRuntime
from agp_remote_yam import mock


def test_slow_preparation_telemetry_does_not_hold_queue_entry(tmp_path, monkeypatch):
    joined = threading.Event()
    planning_requested = threading.Event()
    original = mock.MockStation

    class DelayedMonitor(original):
        def get_robot_observation(self, robot_id):
            if threading.current_thread().name.startswith(('agp-run-', 'agp-initial-scene')):
                planning_requested.set()
                if not joined.wait(1):
                    raise RuntimeError('Read-only planning telemetry blocked queue admission')
            return super().get_robot_observation(robot_id)

        def create_session(self, *args, **kwargs):
            joined.set()
            return super().create_session(*args, **kwargs)

    def finish(self, *_):
        self.outcome = dict(status='done', summary='Offline startup ordering fixture', evidence=[])
        self.finished.set()

    monkeypatch.setattr(mock, 'MockStation', DelayedMonitor)
    monkeypatch.setattr(AgentRuntime, 'check_available', lambda _:None)
    monkeypatch.setattr(AgentRuntime, 'prepare', lambda *_:None)
    monkeypatch.setattr(AgentRuntime, 'prime', lambda *_:None)
    monkeypatch.setattr(AgentRuntime, 'start', finish)
    manager = RunManager(Settings(data=tmp_path, mock_robot=True, memo_site=True,
                                  agent_mode='remote', memory_encoder='lexical'))
    try:
        rid = manager.start('Offline startup ordering fixture', 'fixture', duration=60,
                            runner=dict(kind='automated', name='Automated'))
        deadline = time.monotonic() + 8
        while rid in manager.active and time.monotonic() < deadline:
            time.sleep(.02)
        result = manager.detail(rid, 'fixture')
        assert planning_requested.is_set()
        assert joined.is_set(), result.get('error')
        assert result.get('error') is None, result
        assert result['outcome']['status'] == 'done'
    finally:
        manager.close()

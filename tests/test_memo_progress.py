from pathlib import Path
import subprocess


def test_failure_stall_recovery_and_history_stop_use_the_deployed_script():
    root = Path(__file__).resolve().parents[1]
    result = subprocess.run(['node', str(root/'tests/memo_progress.cjs'),
                             str(root/'src/agp_remote_yam/static/memo-app.js')],
                            text=True, capture_output=True, timeout=10)
    assert result.returncode == 0, result.stdout + result.stderr

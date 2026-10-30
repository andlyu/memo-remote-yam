import json
from pathlib import Path
import subprocess
import sys


def test_fresh_checkout_and_dirty_dependency_preservation(tmp_path):
    origin = tmp_path / 'origin'
    origin.mkdir()
    def git(*args):
        return subprocess.check_output(['git', '-C', str(origin), *args], text=True).strip()
    git('init', '-q')
    (origin / 'source.txt').write_text('original\n')
    git('add', 'source.txt')
    git('-c', 'user.name=Fixture', '-c', 'user.email=fixture@example.test', 'commit', '-qm', 'fixture')
    revision = git('rev-parse', 'HEAD')
    app = tmp_path / 'app';(app / 'scripts').mkdir(parents=True)
    (app / 'scripts/bootstrap.py').write_bytes((Path(__file__).parents[1] / 'scripts/bootstrap.py').read_bytes())
    (app / 'dependency.lock.json').write_text(json.dumps({'remote_yam': {'repository': str(origin), 'commit': revision}}))
    command = [sys.executable, str(app / 'scripts/bootstrap.py')]
    subprocess.run(command, check=True, capture_output=True)
    target = app / '.deps/blupe-remote-yam/source.txt'
    assert target.read_text() == 'original\n'
    target.write_text('operator edit\n')
    failed = subprocess.run(command, capture_output=True)
    assert failed.returncode != 0
    assert b'local tracked changes' in failed.stderr
    assert target.read_text() == 'operator edit\n'

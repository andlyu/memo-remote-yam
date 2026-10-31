"""Per-run workspaces and immutable, explicitly selected experience snapshots."""
from pathlib import Path
from importlib.resources import files
import hashlib
import json
import os
import threading
import time
import uuid


def atomic_json(path, value):
    path = Path(path)
    tmp = path.with_suffix(path.suffix + ".tmp")
    tmp.write_text(json.dumps(value, indent=2, allow_nan=False) + "\n")
    os.replace(tmp, path)


class RunStore:
    def __init__(self, root):
        self.root = Path(root).resolve()
        self.root.mkdir(parents=True, exist_ok=True)
        self.lock = threading.RLock()

    def create(self, task, *, parent=None, with_memo=False):
        identity = uuid.uuid4().hex
        directory = self.root / identity
        workspace = directory / "workspace"
        for name in ("scratch", "frames", "bridge", "bridge_right", "knowledge", "goal"):
            (workspace / name).mkdir(parents=True, exist_ok=True)
        for source, target in (("robot_client.py", "robot_client.py"), ("robot_api.py", "robot_api.py"),
                               ("INTERFACE.md", "README_interface.md")):
            (workspace / target).write_bytes(files("agp_remote_yam").joinpath("assets", source).read_bytes())
        if with_memo:
            (workspace / "bridge_memo").mkdir()
            for name in ("memo_client.py", "MEMO.md"):
                (workspace / name).write_bytes(files("agp_remote_yam").joinpath("assets", name).read_bytes())
        metadata = dict(id=identity, task=task, created_at=time.time(), status="preparing", parent=parent,
                        outcome=None, mode=None)
        if parent:
            snapshot = self.directory(parent) / "experience"
            if not snapshot.is_dir():
                raise ValueError("Selected run has no saved experience")
            # Copy regular text/source files only. A prior agent cannot plant a
            # symlink that reads outside its workspace during seed/export.
            for source in snapshot.rglob("*"):
                if source.is_file() and not source.is_symlink():
                    target = workspace / "knowledge" / source.relative_to(snapshot)
                    target.parent.mkdir(parents=True, exist_ok=True)
                    target.write_bytes(source.read_bytes())
        (workspace / "TASK.md").write_text(task + "\n")
        atomic_json(directory / "run.json", metadata)
        return metadata, directory

    def directory(self, identity):
        if not isinstance(identity, str) or len(identity) != 32 or any(c not in "0123456789abcdef" for c in identity):
            raise ValueError("Invalid run")
        result = self.root / identity
        if not (result / "run.json").is_file():
            raise FileNotFoundError("Run not found")
        return result

    def update(self, directory, **changes):
        with self.lock:
            value = json.loads((directory / "run.json").read_text())
            value.update(changes)
            atomic_json(directory / "run.json", value)
            return value

    def list(self):
        with self.lock:
            rows = []
            for path in self.root.glob("*/run.json"):
                try:
                    rows.append(json.loads(path.read_text()))
                except (OSError, ValueError):
                    continue
            return sorted(rows, key=lambda x: x["created_at"], reverse=True)

    def save_experience(self, directory):
        destination = directory / "experience"
        if destination.exists():
            return json.loads((destination / "manifest.json").read_text())
        source = directory / "workspace/scratch/experience"
        destination.mkdir()
        manifest = dict(source_run=directory.name, files=[], validation="agent_authored_unverified")
        if source.is_dir() and not source.is_symlink():
            for path in sorted(source.rglob("*")):
                if (not path.is_file() or path.is_symlink() or path.suffix not in (".py", ".md", ".json")
                        or path.stat().st_size > 256_000 or any(p.is_symlink() for p in path.parents if p != source)):
                    continue
                data = path.read_bytes()
                target = destination / path.relative_to(source)
                target.parent.mkdir(parents=True, exist_ok=True)
                target.write_bytes(data)
                manifest["files"].append(dict(path=str(path.relative_to(source)), sha256=hashlib.sha256(data).hexdigest()))
        atomic_json(destination / "manifest.json", manifest)
        return manifest


class Journal:
    def __init__(self, directory):
        self.path = Path(directory) / "events.jsonl"
        self.lock = threading.RLock()
        self.rows = []

    def add(self, kind, message, **details):
        with self.lock:
            row = dict(id=len(self.rows), time=time.time(), kind=kind, message=message, **details)
            with self.path.open("a") as stream:
                stream.write(json.dumps(row, allow_nan=False) + "\n")
            self.rows.append(row)
            return row

    def after(self, cursor=-1):
        with self.lock:
            return self.rows[max(0, cursor + 1):]

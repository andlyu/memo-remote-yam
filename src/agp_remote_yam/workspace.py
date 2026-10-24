"""Host-side file access that never follows agent-created symlinks."""
import json
import os
from pathlib import Path
import secrets
import stat


class Workspace:
    def __init__(self, path):
        self.path = Path(path).resolve()

    def parent_fd(self, relative):
        parts = Path(relative).parts
        if not parts or Path(relative).is_absolute() or any(p in ("..", ".") for p in parts):
            raise ValueError("Invalid workspace path")
        fd = os.open(self.path, os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW)
        try:
            for part in parts[:-1]:
                child = os.open(part, os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW, dir_fd=fd)
                os.close(fd)
                fd = child
            return fd, parts[-1]
        except BaseException:
            os.close(fd)
            raise

    def write(self, relative, data):
        fd, name = self.parent_fd(relative)
        temporary = ".host-" + secrets.token_hex(12)
        try:
            out = os.open(temporary, os.O_WRONLY | os.O_CREAT | os.O_EXCL | os.O_NOFOLLOW, 0o600, dir_fd=fd)
            with os.fdopen(out, "wb") as stream:
                stream.write(data)
            os.rename(temporary, name, src_dir_fd=fd, dst_dir_fd=fd)
        finally:
            try:
                os.unlink(temporary, dir_fd=fd)
            except FileNotFoundError:
                pass
            os.close(fd)

    def json(self, relative, value):
        self.write(relative, (json.dumps(value, indent=2, allow_nan=False) + "\n").encode())

    def read(self, relative, limit=1_048_576):
        fd, name = self.parent_fd(relative)
        try:
            leaf = os.open(name, os.O_RDONLY | os.O_NOFOLLOW | os.O_NONBLOCK, dir_fd=fd)
            with os.fdopen(leaf, "rb") as stream:
                if not stat.S_ISREG(os.fstat(stream.fileno()).st_mode):
                    raise ValueError("Workspace reads require a regular file")
                data = stream.read(limit + 1)
            if len(data) > limit:
                raise ValueError("Workspace file exceeds size limit")
            return data
        finally:
            os.close(fd)

    def list(self, relative):
        fd, name = self.parent_fd(relative)
        try:
            child = os.open(name, os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW, dir_fd=fd)
            try:
                return os.listdir(child)
            finally:
                os.close(child)
        finally:
            os.close(fd)

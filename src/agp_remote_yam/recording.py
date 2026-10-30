"""Retain the real public camera atlas with each physical run; never synthesize footage."""
import json
from pathlib import Path
import shutil
import subprocess
import time
from .storage import atomic_json
from .video import PUBLIC_VIEWER, stream_config


class RunRecording:
    def __init__(self, directory, robot_id, *, physical):
        self.directory = Path(directory)
        self.root = self.directory / "recording"
        self.root.mkdir(exist_ok=True)
        self.process = None
        self.log = None
        self.manifest = dict(status="not_physical" if not physical else "pending", physical=physical,
                             run_id=self.directory.name, robot_id=robot_id,
                             note="Mock execution has no physical replay." if not physical else "Recording the actual public camera feed.")
        self.save()

    def save(self):
        atomic_json(self.root / "replay.json", self.manifest)

    def start(self):
        if not self.manifest["physical"]:
            return
        try:
            binary = shutil.which("ffmpeg")
            stream = stream_config(self.manifest["robot_id"])
            if not binary or not stream:
                raise RuntimeError("Physical recording needs ffmpeg and a configured public camera stream")
            # Start with the public master playlist. It supplies the media
            # session query used by child playlists; a bare child URL is 401.
            source = PUBLIC_VIEWER + "/" + stream["path"] + "/index.m3u8"
            self.log = (self.root / "ffmpeg.log").open("wb")
            self.process = subprocess.Popen([binary, "-hide_banner", "-loglevel", "warning", "-y",
                "-rw_timeout", "15000000", "-headers", "Origin: " + PUBLIC_VIEWER + "\r\n",
                "-i", source, "-t", "630", "-map", "0:v:0", "-an", "-vf", "fps=10,scale=1280:-2",
                "-c:v", "libx264", "-preset", "veryfast", "-crf", "26", "-movflags", "+faststart",
                str(self.root / "physical.mp4")], stdin=subprocess.PIPE, stdout=subprocess.DEVNULL, stderr=self.log)
            self.manifest.update(status="recording", recording_started_at=time.time(), source=source,
                                 camera_roles=stream["cameras"], note="Actual physical camera atlas; independent camera timing and public stream buffering apply.")
        except Exception as exc:
            self.manifest.update(status="unavailable", note=str(exc))
        self.save()

    def finish(self):
        if self.process is not None:
            try:
                if self.process.poll() is None:
                    self.process.communicate(input=b"q\n", timeout=12)
            except subprocess.TimeoutExpired:
                self.process.terminate()
                try:
                    self.process.wait(timeout=5)
                except subprocess.TimeoutExpired:
                    self.process.kill()
                    self.process.wait(timeout=5)
            finally:
                if self.log:
                    self.log.close()
            clip = self.root / "physical.mp4"
            valid = False
            if clip.exists() and clip.stat().st_size > 1024:
                try:
                    probe = subprocess.run(["ffprobe", "-v", "error", "-show_entries", "format=duration", "-of", "json", str(clip)], capture_output=True, text=True, timeout=8, check=True)
                    duration = float(json.loads(probe.stdout)["format"]["duration"])
                    valid = duration > 0
                    self.manifest.update(duration_s=duration, bytes=clip.stat().st_size)
                except (OSError, ValueError, KeyError, subprocess.SubprocessError):
                    pass
            self.manifest.update(status="ready" if valid else "unavailable", recording_finished_at=time.time())
            if valid:
                self.manifest["note"] = "Retained actual camera footage for this run. Review motion and outcome independently; public camera buffering affects visual timing."
            else:
                self.manifest["note"] = "No playable physical footage was retained. This run does not satisfy the replay requirement."
        self.save()


def replay_info(directory):
    path = Path(directory) / "recording/replay.json"
    if not path.is_file():
        return None
    value = json.loads(path.read_text())
    value["url"] = "/api/runs/" + Path(directory).name + "/replay.mp4" if value["status"] == "ready" else None
    return value

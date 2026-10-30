"""Authenticated packet worker. It never creates, adopts or stops a robot lease.

The Playground's RunnerController owns every robot command and acknowledges
matched settled completion. Lost polls return the same immutable pending packet;
an uncertain/failed motion terminates the worker, never retries it.
"""
import asyncio
from concurrent.futures import Future
from copy import deepcopy
import hashlib
import hmac
import json
from pathlib import Path
import re
import threading
import time
from .backend import ApiBackend
from .memo import Skillbook, MemoryChannel, text
from .runtime import AgentRuntime
from .storage import RunStore, Journal


def identifier(value, label):
    if not isinstance(value, str) or not re.fullmatch(r"[a-f0-9]{32,64}", value):
        raise ValueError("Invalid " + label)
    return value


class PacketBridge:
    def __init__(self, observation, stopped):
        self.lock = threading.RLock()
        self.stopped = stopped
        self.identity = tuple(observation.get(k) for k in ("episode_id", "lease_id"))
        if not all(self.identity) or observation.get("settled") is not True:
            raise ValueError("A worker requires an active lease and measured settled observation")
        self.observation = deepcopy(observation)
        self.pending = None
        self.sequence = 0
        self.acknowledged = set()
        self.last_poll = time.monotonic()

    @property
    def cancelled(self):
        return self.stopped.is_set

    def feedback(self):
        if self.stopped.is_set():
            raise RuntimeError("Agent worker stopped")
        with self.lock:
            return deepcopy(self.observation)

    def execute(self, points):
        with self.lock:
            if self.stopped.is_set() or self.pending is not None:
                raise RuntimeError("Worker stopped or another packet is outstanding")
            if not points or points[0]["step_id"] != self.observation["step_id"]:
                raise ValueError("Worker packet cursor does not match measured feedback")
            self.sequence += 1
            pending = dict(id=str(self.sequence), points=deepcopy(points), future=Future())
            self.pending = pending
        while not pending["future"].done():
            if self.stopped.wait(.025):
                raise RuntimeError("Agent worker stopped; packet is not replayed")
        return pending["future"].result()

    def poll(self, observation, acknowledgement=None):
        with self.lock:
            if tuple(observation.get(k) for k in ("episode_id", "lease_id")) != self.identity:
                raise ValueError("Worker episode or lease changed")
            if observation.get("settled") is not True:
                raise ValueError("Worker requires measured settled feedback")
            self.last_poll = time.monotonic()
            if acknowledgement and acknowledgement not in self.acknowledged:
                packet = self.pending
                if not packet or acknowledgement != packet["id"]:
                    raise ValueError("Unknown packet acknowledgement")
                if observation.get("step_id") != packet["points"][-1]["step_id"] + 1:
                    raise ValueError("Completion does not match the pending packet")
                self.observation = deepcopy(observation)
                self.acknowledged.add(acknowledgement)
                self.pending = None
                packet["future"].set_result(deepcopy(observation))
            elif self.pending is None:
                if observation.get("step_id") != self.observation["step_id"]:
                    raise ValueError("Observation cursor changed without a matching completion")
                self.observation = deepcopy(observation)
            packet = self.pending
            return dict(id=packet["id"], points=deepcopy(packet["points"])) if packet else None


class Worker:
    def __init__(self, settings, *, max_runs=4):
        from .dependency import runner_root
        runner_root()
        self.settings, self.max_runs = settings, max_runs
        self.store = RunStore(Path(settings.data) / "runs")
        self.book = Skillbook(Path(settings.data) / "skillbook.sqlite3", settings.memory_encoder)
        self.lock, self.active, self.clients = threading.RLock(), {}, {}
        for run in self.store.list():
            if run.get("client_run_id"):
                self.clients[run["client_run_id"]] = run["id"]
            if run["status"] in ("preparing", "running"):
                self.store.update(self.store.directory(run["id"]), status="interrupted")

    def start(self, value):
        client = identifier(value.get("client_run_id"), "client run")
        namespace = identifier(value.get("namespace"), "memory namespace")
        task = text(value.get("task"), "Task")
        if value.get("robot_id") != self.settings.robot_id:
            raise ValueError("Worker is configured for a different robot")
        if type(value.get("memo", False)) is not bool:
            raise ValueError("MEMO must be on or off")
        fingerprint = hashlib.sha256(json.dumps(value, sort_keys=True, allow_nan=False).encode()).hexdigest()
        with self.lock:
            if client in self.clients:
                directory = self.store.directory(self.clients[client])
                metadata = json.loads((directory / "run.json").read_text())
                if metadata.get("start_fingerprint") != fingerprint:
                    raise ValueError("Client run ID was already used for another request")
                return dict(id=directory.name, status=metadata["status"])
            if len(self.active) >= self.max_runs:
                raise ValueError("Agent workers are busy; try again later")
            version = value.get("memory_version")
            if version is not None and (type(version) is not int or not 0 <= version <= self.book.version()):
                raise ValueError("Invalid memory version")
            bridge = PacketBridge(value.get("observation", {}), threading.Event())
            metadata, directory = self.store.create(task)
            journal = Journal(directory)
            memory = MemoryChannel(self.book, namespace, directory, journal,
                                   enabled=value.get("memo", False), version=version)
            runtime = AgentRuntime(directory, journal, model=self.settings.model,
                                   mode="demo" if self.settings.demo else self.settings.agent_mode,
                                   timeout_s=600, executable=self.settings.codex)
            runtime.memory = memory
            runtime.check_available()
            bridge.stopped = runtime.stopped
            if self.settings.offline:
                from .mock import MockBackend
                backend = MockBackend(directory / "workspace", bridge, journal)
            else:
                backend = ApiBackend(self.settings.origin, self.settings.robot_id, directory / "workspace", bridge, journal)
            self.store.update(directory, status="running", owner=namespace, client_run_id=client,
                              start_fingerprint=fingerprint, memo_enabled=memory.enabled, memory_version=memory.version,
                              mode="offline_mock" if self.settings.offline else "physical_api")
            self.clients[client] = directory.name
            context = dict(directory=directory, journal=journal, memory=memory, runtime=runtime, bridge=bridge)
            self.active[directory.name] = context
            runtime.start(backend, task)
            threading.Thread(target=self._watch, args=(context,), daemon=True).start()
            return dict(id=directory.name, status="running")

    def _watch(self, context):
        runtime, bridge = context["runtime"], context["bridge"]
        while not runtime.finished.wait(.25):
            if time.monotonic() - bridge.last_poll > 15:
                context["journal"].add("error", "Playground disconnected; agent worker cancelled")
                runtime.cancel()
        with self.lock:
            try:
                self.store.update(context["directory"], status="completed" if runtime.state == "finished" else runtime.state,
                                  outcome=runtime.outcome, ended_at=time.time())
                self.store.save_experience(context["directory"])
            finally:
                self.active.pop(context["directory"].name, None)

    def poll(self, identity, value):
        directory = self.store.directory(identity)
        with self.lock:
            context = self.active.get(identity)
        packet = None
        if context:
            bridge, memory = context["bridge"], context["memory"]
            packet = bridge.poll(value.get("observation", {}), value.get("acknowledgement"))
            for correction in value.get("corrections", []):
                memory.correct(correction.get("text"), correction.get("request_id"))
            corrections = memory.updates()
            runtime = context["runtime"]
            status = "completed" if runtime.finished.is_set() and runtime.state == "finished" else runtime.state
            events = context["journal"].after(value.get("after", -1))[:40]
            outcome = runtime.outcome
        else:
            metadata = json.loads((directory / "run.json").read_text())
            status, outcome = metadata["status"], metadata.get("outcome")
            rows = [json.loads(line) for line in (directory / "events.jsonl").read_text().splitlines()]
            events = rows[max(0, int(value.get("after", -1)) + 1):][:40]
            corrections = self.book.corrections(metadata["owner"], identity)
        return dict(status=status, outcome=outcome, packet=packet, events=events,
                    delivered_corrections=[r["request_id"] for r in corrections if r["delivered"] is not None])

    def stop(self, identity):
        self.store.directory(identity)
        with self.lock:
            context = self.active.get(identity)
        if context:
            context["runtime"].cancel()
        return dict(status="stop_requested")

    def close(self):
        for identity in list(self.active):
            self.stop(identity)


class WorkerApp:
    def __init__(self, settings, token):
        if len(token) < 32:
            raise ValueError("Worker authentication token must contain at least 32 characters")
        self.worker, self._token = Worker(settings), token

    async def __call__(self, scope, receive, send):
        if scope["type"] == "lifespan":
            while True:
                message = await receive()
                if message["type"] == "lifespan.startup":
                    await send(dict(type="lifespan.startup.complete"))
                elif message["type"] == "lifespan.shutdown":
                    await asyncio.to_thread(self.worker.close)
                    await send(dict(type="lifespan.shutdown.complete"))
                    return
        if scope["type"] != "http":
            return
        headers = {k.decode().lower():v.decode() for k,v in scope["headers"]}
        status, result = 200, None
        try:
            if not hmac.compare_digest(headers.get("authorization", ""), "Bearer " + self._token):
                status, result = 403, dict(error="Worker authentication required")
            else:
                body = bytearray()
                while True:
                    message = await receive()
                    if message["type"] == "http.disconnect":
                        return
                    body.extend(message.get("body", b""))
                    if len(body) > 512_000:
                        raise ValueError("Worker request exceeds 512 KB")
                    if not message.get("more_body"):
                        break
                value = json.loads(body or b"{}")
                if not isinstance(value, dict):
                    raise ValueError("Send a JSON object")
                path, method = scope["path"], scope["method"]
                if path == "/health" and method == "GET":
                    result = dict(status="ok", robot_id=self.worker.settings.robot_id,
                                  encoder=self.worker.book.encoder.identity)
                elif path == "/runs" and method == "POST":
                    result = await asyncio.to_thread(self.worker.start, value)
                else:
                    match = re.fullmatch(r"/runs/([a-f0-9]{32})/(poll|stop)", path)
                    if not match or method != "POST":
                        status, result = 404, dict(error="Not found")
                    elif match[2] == "poll":
                        result = await asyncio.to_thread(self.worker.poll, match[1], value)
                    else:
                        result = await asyncio.to_thread(self.worker.stop, match[1])
        except (ValueError, KeyError, TypeError):
            status, result = 400, dict(error="Invalid worker request")
        except FileNotFoundError:
            status, result = 404, dict(error="Run not found")
        except Exception:
            status, result = 503, dict(error="Agent worker unavailable")
        raw = json.dumps(result, allow_nan=False).encode()
        await send(dict(type="http.response.start", status=status, headers=[
            (b"content-type", b"application/json"), (b"cache-control", b"no-store"),
            (b"content-length", str(len(raw)).encode()), (b"x-content-type-options", b"nosniff")]))
        await send(dict(type="http.response.body", body=raw))

"""MEMO's action/scene retrieval and generalized skillbook, implemented independently.

Reference: VT-Collab/memo d98cc8d (main.py, src/llm/rag.py, pruning.py).
SQLite retains every source record and consolidation revision. No pickle or code
from the upstream repository is loaded. Templates are context, never auto-run.
"""
import ast
from contextlib import contextmanager
import hashlib
import json
import re
import sqlite3
import threading
import time
import numpy as np
from .workspace import Workspace

MODEL_REVISION = "1110a243fdf4706b3f48f1d95db1a4f5529b4d41"


class Encoder:
    """Lazy semantic encoder; lexical mode is explicit for offline fixtures."""
    def __init__(self, mode="semantic"):
        if mode not in ("semantic", "lexical"):
            raise ValueError("Choose semantic or lexical memory encoding")
        self.mode = mode
        self.identity = "all-MiniLM-L6-v2@" + MODEL_REVISION if mode == "semantic" else "lexical-hash-v1"
        self._model = None
        self._lock = threading.RLock()

    def encode(self, text):
        with self._lock:
            if self.mode == "semantic":
                if self._model is None:
                    try:
                        from sentence_transformers import SentenceTransformer
                    except ImportError as exc:
                        raise RuntimeError("Semantic MEMO requires pip install -e '.[memo]'; use --memory-encoder lexical for offline fixtures") from exc
                    self._model = SentenceTransformer("sentence-transformers/all-MiniLM-L6-v2", revision=MODEL_REVISION)
                return self._model.encode(text or "none", normalize_embeddings=True).astype(float).tolist()
            vector = np.zeros(512)
            for word in re.findall(r"[a-z0-9]+", text.lower()):
                # Stable across processes; explicitly lexical, not semantic.
                vector[int.from_bytes(hashlib.sha256(word.encode()).digest()[:4], "big") % len(vector)] += 1
            norm = np.linalg.norm(vector)
            return (vector / norm if norm else vector).tolist()


def text(value, label, limit=4000):
    if not isinstance(value, str) or not 1 <= len(value.strip()) <= limit:
        raise ValueError(f"{label} must contain 1–{limit} characters")
    return value.strip()


def action_parts(action, scene=""):
    match = re.fullmatch(r"([A-Z_]+)\(([^)]*)\)", action.upper().strip())
    if action.upper() == "GENERAL":
        return "GENERAL", scene
    if not match:
        raise ValueError("Use ACTION(object) or GENERAL for the subtask")
    return match[1], match[2] + " " + scene


def validate_template(content):
    tree = ast.parse(content)
    if len(tree.body) != 1 or not isinstance(tree.body[0], (ast.FunctionDef, ast.AsyncFunctionDef)):
        raise ValueError("A skill template must be one parameterized Python function")
    function = tree.body[0]
    if not function.args.args:
        raise ValueError("A skill template needs scene-dependent parameters")
    for node in ast.walk(tree):
        if isinstance(node, (ast.List, ast.Tuple)) and len(node.elts) == 3 and all(
                isinstance(x, ast.Constant) and isinstance(x.value, (int, float)) for x in node.elts):
            raise ValueError("Replace literal XYZ coordinates with parameters before saving the template")


class Skillbook:
    def __init__(self, path, encoder="semantic"):
        self.path = str(path)
        self.encoder = Encoder(encoder) if isinstance(encoder, str) else encoder
        self.lock = threading.RLock()
        with self.connect() as db:
            db.executescript("""
                PRAGMA journal_mode=WAL;
                CREATE TABLE IF NOT EXISTS revisions(version INTEGER PRIMARY KEY AUTOINCREMENT, created REAL NOT NULL);
                CREATE TABLE IF NOT EXISTS memories(
                  id INTEGER PRIMARY KEY AUTOINCREMENT, namespace TEXT NOT NULL, action TEXT NOT NULL,
                  scene TEXT NOT NULL, kind TEXT NOT NULL, content TEXT NOT NULL, run_id TEXT NOT NULL,
                  evidence TEXT NOT NULL, parents TEXT NOT NULL, encoder TEXT NOT NULL,
                  action_vector TEXT NOT NULL, scene_vector TEXT NOT NULL, version INTEGER NOT NULL,
                  superseded INTEGER, created REAL NOT NULL);
                CREATE INDEX IF NOT EXISTS memory_namespace ON memories(namespace, version);
                CREATE TABLE IF NOT EXISTS corrections(
                  id INTEGER PRIMARY KEY AUTOINCREMENT, namespace TEXT NOT NULL, run_id TEXT NOT NULL,
                  request_id TEXT NOT NULL, action TEXT NOT NULL, scene TEXT NOT NULL,
                  content TEXT NOT NULL, delivered REAL, created REAL NOT NULL,
                  UNIQUE(namespace,run_id,request_id));
            """)

    @contextmanager
    def connect(self):
        with self.lock:
            db = sqlite3.connect(self.path, timeout=10)
            db.row_factory = sqlite3.Row
            try:
                yield db
                db.commit()
            except BaseException:
                db.rollback()
                raise
            finally:
                db.close()

    @staticmethod
    def row(row):
        value = dict(row)
        for key in ("evidence", "parents"):
            value[key] = json.loads(value[key])
        for key in ("action_vector", "scene_vector", "namespace"):
            value.pop(key, None)
        value["validation"] = "agent_authored_unverified"
        return value

    def version(self):
        with self.connect() as db:
            return db.execute("SELECT COALESCE(MAX(version),0) FROM revisions").fetchone()[0]

    def list(self, namespace, *, version=None, limit=100):
        version = self.version() if version is None else version
        if type(version) is not int or version < 0:
            raise ValueError("Invalid skillbook version")
        with self.connect() as db:
            return [self.row(r) for r in db.execute(
                "SELECT * FROM memories WHERE namespace=? AND version<=? AND (superseded IS NULL OR superseded>?) ORDER BY id DESC LIMIT ?",
                (namespace, version, version, min(1000, limit)))]

    def add(self, namespace, *, action, scene, kind, content, run_id, evidence=None, parents=None):
        action, scene = text(action, "Action", 200).upper(), str(scene)[:2000]
        act, objects = action_parts(action, scene)
        if kind not in ("guidance", "template"):
            raise ValueError("Memory kind must be guidance or template")
        content = text(content, "Memory", 16000)
        if kind == "template":
            validate_template(content)
        parents = parents or []
        if not isinstance(parents, list) or len(parents) > 100 or any(type(i) is not int for i in parents):
            raise ValueError("Invalid consolidation source IDs")
        vectors = (self.encoder.encode(act), self.encoder.encode(objects))
        with self.connect() as db:
            if parents:
                rows = db.execute("SELECT id,kind FROM memories WHERE namespace=? AND superseded IS NULL", (namespace,)).fetchall()
                permitted = {r["id"] for r in rows if r["kind"] == kind}
                if not set(parents).issubset(permitted):
                    raise ValueError("Consolidation sources must be current memories of the same owner and kind")
            # Exact retries add neither a duplicate memory nor another revision.
            existing = db.execute("SELECT * FROM memories WHERE namespace=? AND action=? AND scene=? AND kind=? AND content=? AND superseded IS NULL",
                                  (namespace, action, scene, kind, content)).fetchone()
            if existing and not parents:
                return self.row(existing)
            version = db.execute("INSERT INTO revisions(created) VALUES(?)", (time.time(),)).lastrowid
            identity = db.execute("INSERT INTO memories(namespace,action,scene,kind,content,run_id,evidence,parents,encoder,action_vector,scene_vector,version,created) VALUES(?,?,?,?,?,?,?,?,?,?,?,?,?)",
                (namespace, action, scene, kind, content, run_id, json.dumps(evidence or []), json.dumps(parents),
                 self.encoder.identity, json.dumps(vectors[0]), json.dumps(vectors[1]), version, time.time())).lastrowid
            for parent in parents:
                db.execute("UPDATE memories SET superseded=? WHERE id=?", (version, parent))
            return self.row(db.execute("SELECT * FROM memories WHERE id=?", (identity,)).fetchone())

    def retrieve(self, namespace, action, scene="", *, version=None, limit=8):
        act, objects = action_parts(action, scene)
        qa, qs = np.asarray(self.encoder.encode(act)), np.asarray(self.encoder.encode(objects))
        version = self.version() if version is None else version
        with self.connect() as db:
            rows = db.execute("SELECT * FROM memories WHERE namespace=? AND encoder=? AND version<=? AND (superseded IS NULL OR superseded>?)",
                              (namespace, self.encoder.identity, version, version)).fetchall()
        matches = []
        for row in rows:
            score = .75 * float(qa @ np.asarray(json.loads(row["action_vector"]))) + .25 * float(qs @ np.asarray(json.loads(row["scene_vector"])))
            if row["action"] == "GENERAL":
                score = max(score, .25)
            minimum = .8 if getattr(self.encoder, 'mode', 'semantic') == 'semantic' else .2
            if score >= minimum or row["action"] == "GENERAL":
                matches.append(dict(self.row(row), score=score))
        return sorted(matches, key=lambda r: (-r["score"], -r["id"]))[:limit]

    def clusters(self, namespace, threshold=.8):
        """Offline candidate clusters; an agent rewrites them, preserving sources."""
        with self.connect() as db:
            rows = db.execute("SELECT * FROM memories WHERE namespace=? AND encoder=? AND superseded IS NULL",
                              (namespace, self.encoder.identity)).fetchall()
        groups = []
        for row in rows:
            for group in groups:
                other = group[0]
                score = .75 * float(np.asarray(json.loads(row['action_vector'])) @ np.asarray(json.loads(other['action_vector'])))
                score += .25 * float(np.asarray(json.loads(row['scene_vector'])) @ np.asarray(json.loads(other['scene_vector'])))
                if row['kind'] == other['kind'] and score >= threshold:
                    group.append(row)
                    break
            else:
                groups.append([row])
        return [[self.row(row) for row in group] for group in groups if len(group) > 1]

    def correct(self, namespace, run_id, request_id, action, scene, content):
        content = text(content, "Correction", 2000)
        request_id = text(request_id, "Correction request ID", 80)
        with self.connect() as db:
            row = db.execute("SELECT * FROM corrections WHERE namespace=? AND run_id=? AND request_id=?", (namespace, run_id, request_id)).fetchone()
            if row:
                if row["content"] != content:
                    raise ValueError("Correction request ID was already used for different text")
                return dict(row)
            count = db.execute("SELECT COUNT(*) FROM corrections WHERE namespace=? AND run_id=?", (namespace, run_id)).fetchone()[0]
            if count >= 32:
                raise ValueError("This run reached its 32-correction limit")
            identity = db.execute("INSERT INTO corrections(namespace,run_id,request_id,action,scene,content,created) VALUES(?,?,?,?,?,?,?)",
                                  (namespace, run_id, request_id, action, scene, content, time.time())).lastrowid
            return dict(db.execute("SELECT * FROM corrections WHERE id=?", (identity,)).fetchone())

    def corrections(self, namespace, run_id, *, deliver=False):
        with self.connect() as db:
            rows = [dict(r) for r in db.execute("SELECT * FROM corrections WHERE namespace=? AND run_id=? ORDER BY id", (namespace, run_id))]
            if deliver:
                db.execute("UPDATE corrections SET delivered=? WHERE namespace=? AND run_id=? AND delivered IS NULL", (time.time(), namespace, run_id))
            return [{k:v for k,v in r.items() if k != "namespace"} for r in rows
                    if not deliver or r["delivered"] is None]


class MemoryChannel:
    """Host-owned provenance and the running agent's bounded memory commands."""
    def __init__(self, book, namespace, directory, journal, *, enabled=True, version=None):
        self.book, self.namespace, self.directory, self.journal = book, namespace, directory, journal
        self.enabled, self.version = enabled, book.version() if version is None else version
        self.workspace = Workspace(directory / "workspace")
        self.action, self.scene = "GENERAL", ""
        self.retrieved = []
        self.lock = threading.RLock()
        self._queued = set()

    def correct(self, content, request_id):
        with self.lock:
            row = self.book.correct(self.namespace, self.directory.name, request_id, self.action, self.scene, content)
            if row["id"] not in self._queued:
                self._queued.add(row["id"])
                self.journal.add("correction_queued", row["content"], correction_id=row["id"], action=row["action"])
            return row

    def updates(self, *, deliver=False):
        rows = self.book.corrections(self.namespace, self.directory.name, deliver=deliver)
        if deliver:
            for row in rows:
                if row["delivered"] is None:
                    self.journal.add("correction_delivered", "Correction delivered in the agent's observation", correction_id=row["id"])
        return rows

    def command(self, command, arguments):
        with self.lock:
            if command == "context":
                self.action = text(arguments.get("action", self.action), "Action", 200).upper()
                self.scene = str(arguments.get("scene", self.scene))[:2000]
                action_parts(self.action, self.scene)
                self.retrieved = self.book.retrieve(self.namespace, self.action, self.scene, version=self.version) if self.enabled else []
                result = dict(enabled=self.enabled, version=self.version, encoder=self.book.encoder.identity,
                              action=self.action, scene=self.scene, memories=self.retrieved, corrections=self.updates(deliver=True))
                self.workspace.json("MEMO_CONTEXT.json", result)
                self.journal.add("memory_retrieved", f"Retrieved {len(self.retrieved)} memories for {self.action}",
                                 memory_ids=[r["id"] for r in self.retrieved], version=self.version, action=self.action)
                return result
            if command == "list":
                return dict(version=self.version, memories=self.book.list(self.namespace, version=self.version) if self.enabled else [])
            if command not in ("remember", "consolidate") or not self.enabled:
                raise ValueError("MEMO is disabled or this memory command is unsupported")
            evidence = []
            for correction in self.updates():
                evidence.append(dict(correction_id=correction["id"], request_id=correction["request_id"]))
            for path in arguments.get("evidence", []):
                if not isinstance(path, str) or not path.startswith(("frames/", "scratch/")):
                    raise ValueError("Evidence must reference this run's captures or scratch files")
                raw = self.workspace.read(path, 16_000_000)
                evidence.append(dict(path=path, sha256=hashlib.sha256(raw).hexdigest()))
            kind = arguments.get("kind", "guidance")
            if kind == "template" and not any("path" in item for item in evidence):
                raise ValueError("A template needs code or capture evidence from this run")
            parents = arguments.get("source_ids", []) if command == "consolidate" else []
            if command == "consolidate" and not parents:
                raise ValueError("Consolidation requires source IDs")
            metadata = json.loads((self.directory / "run.json").read_text())
            evidence.append(dict(source_run=self.directory.name, source_mode=metadata.get("mode", "unrecorded")))
            row = self.book.add(self.namespace, action=arguments.get("action", self.action), scene=arguments.get("scene", self.scene),
                                kind=kind, content=arguments.get("content"), run_id=self.directory.name, evidence=evidence, parents=parents)
            self.journal.add("memory_saved", "Saved a generalized " + kind, memory=row)
            return dict(memory=row, active_version=self.book.version(), retrieval_version=self.version)

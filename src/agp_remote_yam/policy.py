"""Runtime coding agent → synchronous robot commands → RunnerController packets."""
from concurrent.futures import Future
from copy import deepcopy
from queue import Queue, Empty
import threading
import time
from .dependency import runner_root

runner_root()
from remote_yam.providers import PolicyComplete


class AgPPolicy:
    provider_name = "agent_as_policy"
    model = "agent-as-policy"

    def __init__(self, runtime, backend_factory, journal):
        self.runtime, self.backend_factory, self.journal = runtime, backend_factory, journal
        self.cancelled = lambda: False
        self.refresh_observation = None
        self.interaction_sink = None
        self._observation = None
        self._identity = None
        self._packets = Queue(maxsize=1)
        self._pending = None
        self._completed = None
        self._future = None
        self._failure = None
        self._started = False
        self._last_feedback = 0.
        self._settled_after = None
        self._lock = threading.RLock()
        self.last_step_model_s = 0.
        self.physical = False
        self._motion_recorded = False

    def public_config(self):
        return dict(provider=self.provider_name,
                    model="MEMO" if self.runtime.memory is not None else self.runtime.model,
                    foundation_model=self.runtime.model,
                    display_name="MEMO" if self.runtime.memory is not None else "Agent as Policy", runtime=self.runtime.state,
                    agent_declared_outcome=self.runtime.outcome)

    def infer(self, *_):
        raise RuntimeError("AgP uses the packet provider interface")

    def _check(self):
        if self._failure:
            raise RuntimeError(self._failure)
        if self.cancelled() or self.runtime.stopped.is_set():
            raise RuntimeError("AgP run cancelled")

    def feedback(self):
        self._check()
        with self._lock:
            observation = deepcopy(self._observation)
        if not observation:
            raise RuntimeError("No active robot observation")
        if time.monotonic() - self._last_feedback > .25 and callable(self.refresh_observation):
            observation = self.refresh_observation()
            with self._lock:
                self._observation = deepcopy(observation)
                self._last_feedback = time.monotonic()
        if tuple(observation.get(k) for k in ("episode_id", "lease_id")) != self._identity:
            raise RuntimeError("Observation changed episode or lease")
        if observation.get("settled") is not True:
            raise RuntimeError("Robot feedback is not settled")
        # Refreshing an idle arm's telemetry must not move the capture boundary
        # forward. The boundary belongs to matched motion completion (or the
        # initial settled pose), rather than every later state read.
        observation["settled_after"] = self._settled_after
        return observation

    def execute(self, points):
        self._check()
        self.journal.add("motion_requested", "The coding agent submitted a generated trajectory",
                         physical=self.physical, waypoint_count=len(points))
        future = Future()
        self._packets.put_nowait((points, future))
        while not future.done():
            self._check()
            time.sleep(.025)
        return future.result()

    def build_trajectory(self, prompt, observation, first_step_id):
        self._check()
        identity = tuple(observation.get(k) for k in ("episode_id", "lease_id"))
        if self._identity is not None and identity != self._identity:
            raise RuntimeError("A new episode or lease requires a new AgP run")
        self._identity = identity
        if observation.get("step_id") != first_step_id or observation.get("settled") is not True:
            raise RuntimeError("AgP requires matching measured settled feedback")
        with self._lock:
            if self._settled_after is None or self._completed is not None:
                self._settled_after = observation["observed_at"]
            self._observation = deepcopy(observation)
            self._last_feedback = time.monotonic()
        if self._completed is not None:
            if observation["step_id"] != self._completed["step_id"]:
                raise RuntimeError("Packet completion cursor changed")
            self._future.set_result(deepcopy(observation))
            self._future, self._completed = None, None
        if not self._started:
            if self.physical and observation.get('homed') is True:
                self.journal.add('home_completed', 'Startup Home completed with matched settled feedback',
                                 observed_at=observation['observed_at'], physical=True,
                                 evidence='Controller-confirmed Home; not method-driven motion')
            backend = self.backend_factory(self)
            self.runtime.start(backend, prompt)
            self._started = True
        while True:
            self._check()
            if self.runtime.finished.is_set() and self._packets.empty():
                raise PolicyComplete((self.runtime.outcome or {}).get("status", "give_up"))
            try:
                points, future = self._packets.get(timeout=.05)
            except Empty:
                continue
            if not points or points[0]["step_id"] != first_step_id:
                future.set_exception(RuntimeError("AgP packet cursor mismatch"))
                raise RuntimeError("AgP packet cursor mismatch")
            self._future = future
            self._pending = dict(count=len(points), last=points[-1]["step_id"])
            return points

    def trajectory_completed(self, observation, waypoint_count):
        if (not self._pending or waypoint_count != self._pending["count"]
                or observation.get("step_id") != self._pending["last"] + 1
                or observation.get("settled") is not True):
            raise RuntimeError("AgP completion does not match its submitted packet")
        baseline = self._observation or {}
        changed = any(abs(float(a)-float(b)) > .2
                      for arm in ("left", "right")
                      for a, b in zip(baseline.get(arm+"_joints_deg", []), observation.get(arm+"_joints_deg", [])))
        if self.physical and changed and not self._motion_recorded:
            self.journal.add("physical_motion_measured", "Measured physical arm movement after the generated command",
                             observed_at=observation.get("observed_at"), physical=True,
                             evidence="Matched settled feedback; visually verify against retained footage")
            self._motion_recorded = True
        self._pending = None
        self._completed = deepcopy(observation)

    def trajectory_failed(self, code, message, waypoint_count, **_):
        self._failure = f"{code}: {message}"
        if self._future and not self._future.done():
            self._future.set_exception(RuntimeError(self._failure))
        self.journal.add("error", "Robot execution failed; command was not replayed", code=code)
        self.runtime.cancel()

    def close_transport(self):
        self.runtime.cancel()

    request_stop = close_transport

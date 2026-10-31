"""Fresh initial observations, with bounded inline previews for native Codex."""
import base64
import io
import json
from PIL import Image
from .workspace import Workspace


def initial_input(backend, observation=None):
    phase = "leased" if observation is None else "monitor_before_admission"
    observation = backend.policy.feedback() if observation is None else observation
    states = {arm: backend.state(arm, observation) for arm in ("left", "right")}
    captures = backend.initial_frames(observation)
    images, views = [], []
    for arm, capture in captures.items():
        for role in ("top", "wrist"):
            path = capture["files"].get(role)
            if not path:
                continue
            with Image.open(io.BytesIO(backend.workspace.read(path, 8_000_000))) as source:
                preview = source.convert("RGB")
                preview.thumbnail((960, 960))
                out = io.BytesIO()
                preview.save(out, "JPEG", quality=85)
            images.append("data:image/jpeg;base64," + base64.b64encode(out.getvalue()).decode("ascii"))
            views.append(dict(arm=arm, camera=role, file=path, calibration=capture["files"]["calibration"]))
    context = dict(states=states, views=views, physical=bool(backend.policy.physical),
                   synchronized=False, depth_included=False, phase=phase,
                   camera_poses_valid_for_motion=phase == "leased")
    backend.workspace.json("INITIAL_OBSERVATION.json", context)
    return dict(context=context, images=images)


def load_initial_input(workspace):
    path = "initial-input.json"
    try:
        return json.loads(Workspace(workspace.parent).read(path, 5_000_000))
    except FileNotFoundError:
        return None

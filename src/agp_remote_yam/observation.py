"""Fresh initial observations, with bounded inline previews for native Codex."""
import base64
import io
import json
import math
from PIL import Image
from .workspace import Workspace


class ScenePreview:
    """Public RGB and raw telemetry only; never used as a robot command backend."""
    def __init__(self, origin, robot_id, workspace, policy, journal):
        from remote_yam.cameras import CameraFrameSource
        self.origin, self.robot_id = origin.rstrip('/'), robot_id
        self.workspace, self.policy, self.journal = Workspace(workspace), policy, journal
        self.rgb = CameraFrameSource(self.origin, camera_names=('top', 'left', 'right'))

    def state(self, arm, observation):
        return dict(joints=[math.radians(v) for v in observation[arm+'_joints_deg']],
                    gripper_fraction=observation[arm+'_gripper'], observed_at=observation['observed_at'],
                    health=observation.get('safety', {}), ee_pose=None, calibration_id=None,
                    note='Pre-admission telemetry; fresh leased state and calibration are required for motion.')

    def initial_frames(self, observation):
        from .backend import ApiBackend
        frames = ApiBackend.rgb_frames(self, ('top', 'left', 'right'))
        captures = {}
        for arm in ('left', 'right'):
            paths, metadata = {}, dict(phase='monitor_before_admission', physical=True,
                                      camera_poses_valid_for_motion=False, synchronized=False,
                                      note='Unbound preparation views; obtain leased calibration before geometric use.')
            for name in (('top', 'wrist') if arm == 'left' else ('wrist',)):
                role = arm if name == 'wrist' else 'top'
                frame = frames[role]
                path = 'frames/initial_' + role + '.jpg'
                self.workspace.write(path, frame.jpeg)
                paths[name] = path
                metadata[name] = dict(received_at=frame.received_at, source_captured_at=frame.source_captured_at)
            paths['calibration'] = 'frames/initial_'+arm+'_metadata.json'
            self.workspace.json(paths['calibration'], metadata)
            captures[arm] = dict(files=paths)
        self.journal.add('capture', 'Saved public read-only preparation views; no pose calibration assumed')
        return captures


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

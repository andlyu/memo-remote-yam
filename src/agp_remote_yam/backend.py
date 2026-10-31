"""AgP command surface; session admission and motor ownership stay upstream."""
from copy import deepcopy
from concurrent.futures import ThreadPoolExecutor
import io
import json
import time
from urllib.parse import quote
import numpy as np
from PIL import Image
from scipy.spatial.transform import Rotation
from .geometry import YamGeometry
from .workspace import Workspace

COMMANDS = ("status", "help", "state", "frames", "move_ee", "move_joints", "gripper")


def transform_pose(transform):
    matrix = np.asarray(transform)
    quat = Rotation.from_matrix(matrix[:3, :3]).as_quat()
    return dict(position=dict(zip("xyz", matrix[:3, 3].tolist())),
                rotation=dict(zip(("w", "x", "y", "z"), [float(quat[3]), *quat[:3].tolist()])))


class ApiBackend:
    def __init__(self, origin, robot_id, workspace, policy, journal):
        self.origin, self.robot_id = origin.rstrip("/"), robot_id
        self.workspace, self.policy, self.journal = Workspace(workspace), policy, journal
        from remote_yam.api_depth import ApiDepth
        from remote_yam.cameras import CameraFrameSource
        self.depth = {role: ApiDepth(self.origin, robot_id, camera=role) for role in ("top", "left", "right")}
        self.rgb = CameraFrameSource(self.origin, camera_names=("top", "left", "right"))
        self.report = json.loads(self.depth["top"].read("/calibration", 256_000))
        if self.report.get("robot_id", robot_id) != robot_id:
            raise ValueError("Calibration robot does not match the selected robot")
        self.geometry = YamGeometry(self.report)
        self.capture_id = 0

    def state(self, arm, observation):
        return dict(joints=np.deg2rad(observation[arm + "_joints_deg"]).tolist(),
                    ee_pose=self.geometry.state(arm, observation),
                    gripper_fraction=observation[arm + "_gripper"],
                    observed_at=observation["observed_at"], calibration_id=self.report["calibration_id"],
                    health=deepcopy(observation.get("safety", {})), coordinate_frame=arm + "_base")

    def command(self, arm, command, arguments):
        if command == '--help':
            command = 'help'
        if command not in COMMANDS:
            raise ValueError("Unsupported command " + repr(command) + "; use request('help', {}) for commands and examples")
        if command == "help":
            return dict(commands=list(COMMANDS), interface="README_interface.md",
                depth_cameras=['top','wrist'],
                examples=dict(frames=dict(cams=['top','wrist'],depth=True)),
                depth_files='Each requested view returns <view>_depth (.npy optical Z metres), <view>_rgbd and calibration.',
                calibration_quality=deepcopy(self.report.get('quality', {})),
                observation_note='Initial RGB previews omit numeric depth; request frames with depth=true before declaring depth unavailable. Calibration quality remains unverified where labelled.')
        if command == "status":
            return dict(robot_id=self.robot_id, frame=arm + "_base", cadence_hz=10,
                        commands=list(COMMANDS), synchronized_cameras=False, physical=True,
                        calibration_id=self.report["calibration_id"])
        observation = self.policy.feedback()
        if command == "state":
            return self.state(arm, observation)
        if command == "frames":
            return self.frames(arm, arguments, observation)
        if command == "move_ee":
            points = self.geometry.cartesian(arm, arguments, observation, observation["step_id"])
        elif command == "move_joints":
            points = self.geometry.joints(arm, arguments["joints"], observation, observation["step_id"])
        else:
            action = arguments.get("action")
            fraction = {"open": 1., "close": 0.}.get(action) if isinstance(action, str) else action
            if isinstance(fraction, bool) or not isinstance(fraction, (int, float)):
                raise ValueError("gripper action must be open, close, or a fraction")
            points = self.geometry.joints(arm, np.deg2rad(observation[arm + "_joints_deg"]).tolist(),
                observation, observation["step_id"], {arm: float(fraction)})
        # Reject malformed generated values while the bridge can return a local
        # tool error, before the controller/execution worker owns the packet.
        from remote_yam.session import _trajectory_waypoints
        points = _trajectory_waypoints(points)
        json.dumps(points, allow_nan=False)
        measured = self.policy.execute(points)
        result = self.state(arm, measured)
        if command == "move_ee":
            actual = np.array(list(result["ee_pose"]["position"].values()))
            target = np.array([arguments["position"][key] for key in "xyz"])
            result["target_error_mm"] = float(np.linalg.norm(actual - target) * 1000)
        result["execution"] = "measured_completed_and_settled"
        return result

    def rgb_frames(self, roles):
        with ThreadPoolExecutor(max_workers=len(roles)) as pool:
            pending = {role: pool.submit(self.rgb.fetch, role,
                self.origin + "/v1/robots/" + quote(self.robot_id, safe="") + "/cameras/" + role + ".jpg")
                for role in roles}
            return {role: future.result() for role, future in pending.items()}

    def initial_frames(self, observation):
        # Fetch independent cameras together, then compute transforms serially:
        # the canonical FK engine has mutable state and is not thread safe.
        frames = self.rgb_frames(("top", "left", "right"))
        return {arm: self.frames(arm, dict(cams=["top", "wrist"] if arm == "left" else ["wrist"],
                                         depth=False), observation, rgb_frames=frames)
                for arm in ("left", "right")}

    def frames(self, arm, arguments, observation, *, rgb_frames=None):
        cameras = arguments.get("cams", ["wrist", "top"])
        depth = arguments.get("depth", True)
        if (not isinstance(cameras, list) or not cameras or len(set(cameras)) != len(cameras)
                or any(c not in ("top", "wrist") for c in cameras) or type(depth) is not bool):
            raise ValueError("cams must contain top/wrist, and depth must be boolean")
        self.capture_id += 1
        prefix = f"frames/{self.capture_id:04d}_{arm}"
        calibration = {"_meta": dict(robot_id=self.robot_id, calibration_id=self.report["calibration_id"],
            measured_state=self.state(arm, observation), synchronized_with_images=False,
            calibration_quality=self.report.get("quality"))}
        paths = {}
        roles = [] if depth else [arm if name == 'wrist' else 'top' for name in cameras]
        if roles and rgb_frames is None:
            rgb_frames = self.rgb_frames(roles)
        snapshots = {}
        if depth:
            # Camera IO is independent. FK-derived camera transforms below stay
            # serial because the canonical kinematics object is mutable.
            with ThreadPoolExecutor(max_workers=len(cameras)) as pool:
                pending = {name: pool.submit(self.depth[arm if name == 'wrist' else 'top'].capture,
                    report=self.report, stopped=True, cancelled=self.policy.cancelled) for name in cameras}
                snapshots = {name: future.result() for name, future in pending.items()}
        for name in cameras:
            role = arm if name == "wrist" else "top"
            camera = self.report["cameras"][role]
            if depth:
                snapshot = snapshots[name]
                raw, captured = snapshot.image(), snapshot.metadata["captured_at"]
                if captured <= observation.get("settled_after", observation["observed_at"]):
                    raise ValueError(name + " depth precedes the settled pose; request a fresh capture")
                out = io.BytesIO()
                np.save(out, snapshot.depth.astype(np.float32), allow_pickle=False)
                path = prefix + '_' + name + '_depth.npy'
                self.workspace.write(path, out.getvalue())
                paths[name + '_depth'] = path
                self.workspace.write(prefix + '_' + name + '_rgbd.npz', snapshot.recording_bundle())
                paths[name + '_rgbd'] = prefix + '_' + name + '_rgbd.npz'
                camera = snapshot.calibration["cameras"][role] if "cameras" in snapshot.calibration else camera
            else:
                frame = rgb_frames[role]
                captured = frame.source_captured_at
                if captured is not None and captured <= observation.get("settled_after", observation["observed_at"]):
                    raise ValueError("RGB image precedes the settled pose; request a fresh capture")
                image = Image.open(io.BytesIO(frame.jpeg)).convert("RGB")
                if list(image.size) != camera["image_size"]:
                    raise ValueError("RGB image dimensions differ from this run's calibration")
                out = io.BytesIO()
                image.save(out, format="PNG")
                raw = out.getvalue()
            transform = (camera["T_base_camera"][arm] if name == "top" else
                self.geometry.camera_transform(arm, observation, camera["T_grasp_camera"]))
            path = prefix + "_" + name + ".png"
            self.workspace.write(path, raw)
            paths[name] = path
            calibration[name] = dict(intrinsics=camera.get("depth_intrinsics", {}).get("K", camera["K"]),
                image_size=camera["image_size"], pose=transform_pose(transform), captured_at=captured,
                distortion_model=camera.get("distortion_model"),
                distortion_coefficients=camera.get("distortion", []),
                factory_intrinsics=camera.get("depth_intrinsics"),
                source_time_available=captured is not None,
                received_at=(getattr(rgb_frames[role], "received_at", None)
                             if not depth else None),
                rectified=camera.get("rectified", False), synchronized_with_state=False)
        calibration_path = prefix + "_calib.json"
        self.workspace.json(calibration_path, calibration)
        paths["calibration"] = calibration_path
        self.journal.add("capture", "Saved fresh camera observations", files=paths)
        return dict(capture=self.capture_id, files=paths, synchronized=False)

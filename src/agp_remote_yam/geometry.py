"""AgP base-frame wxyz/radian commands → the pinned runner's YAM model.

Uses Remote YAM's canonical FK/IK, joint/contact checks and 0.035 rad/10 Hz
pacing. AgP command semantics: upstream agp/README_interface_bare.md.
"""
import math
import numpy as np
from scipy.spatial.transform import Rotation, Slerp
from .dependency import runner_root


def finite_vector(value, size, label):
    if not isinstance(value, (list, tuple)) or len(value) != size or any(isinstance(v, bool) for v in value):
        raise ValueError(f"{label} needs {size} finite numbers")
    result = np.asarray(value, dtype=float)
    if not np.isfinite(result).all():
        raise ValueError(f"{label} needs {size} finite numbers")
    return result


class YamGeometry:
    def __init__(self, report):
        runner_root()
        from remote_yam.mujoco_ik import BimanualRelativeIK, ROBOT_SHA256
        if report.get("kinematics", {}).get("robot_model_sha256") != ROBOT_SHA256:
            raise ValueError("Calibration does not identify the dependency's canonical YAM model")
        native = report["native_joint_calibration"]
        if native["coordinate_convention"] != "native_i2rt_updated":
            raise ValueError("Unsupported native joint coordinate convention")
        offsets = native["additional_offsets_rad"]
        self.ik = BimanualRelativeIK(base_spacing_m=report["base_geometry"]["spacing_m"],
            joint_offsets_rad=offsets["left"] + offsets["right"],
            joint_limits=report.get("joint_limits"))
        self.bases = (np.array([0., self.ik.base_spacing_m / 2, 0.]),
                      np.array([0., -self.ik.base_spacing_m / 2, 0.]))

    def measured(self, observation):
        self.ik._safe_baseline(observation["left_joints_deg"], observation["right_joints_deg"])
        return np.deg2rad(np.r_[observation["left_joints_deg"], observation["right_joints_deg"]])

    def poses(self, observation):
        self.ik._forward(self.measured(observation))
        return self.ik._poses()

    def state(self, arm, observation):
        index = ("left", "right").index(arm)
        position, rotation = self.poses(observation)[index]
        q = Rotation.from_matrix(rotation).as_quat()
        return dict(position=dict(zip("xyz", (position - self.bases[index]).tolist())),
                    rotation=dict(zip(("w", "x", "y", "z"), [float(q[3]), *q[:3].tolist()])))

    def camera_transform(self, arm, observation, mount):
        index = ("left", "right").index(arm)
        position, rotation = self.poses(observation)[index]
        transform = np.eye(4)
        transform[:3, :3] = rotation
        transform[:3, 3] = position - self.bases[index]
        return transform @ np.asarray(mount, dtype=float)

    def _points(self, pairs, observation, first_step, grips=None):
        if not 1 <= len(pairs) <= 300 or first_step + len(pairs) > 3000:
            raise ValueError("Move exceeds the existing trajectory/session waypoint budget; request an intermediate target")
        before = self.measured(observation)
        points = []
        for index, q in enumerate(pairs):
            if np.any(q < self.ik.low) or np.any(q > self.ik.high) or not np.isfinite(q).all():
                raise ValueError("Target exceeds existing YAM joint limits")
            if np.max(np.abs(q - before)) > .035 + 1e-9:
                raise ValueError("Path exceeds existing YAM joint pacing")
            point = dict(step_id=first_step + index, left_joints_deg=np.rad2deg(q[:6]).tolist(),
                         right_joints_deg=np.rad2deg(q[6:]).tolist())
            for arm in ("left", "right"):
                start = float(observation[arm + "_gripper"])
                target = (grips or {}).get(arm, start)
                point[arm + "_gripper"] = start + (target - start) * (index + 1) / len(pairs)
            points.append(point)
            before = q
        return points

    def joints(self, arm, joints, observation, first_step, grips=None):
        target = self.measured(observation)
        index = ("left", "right").index(arm)
        target[index * 6:index * 6 + 6] = finite_vector(joints, 6, "joints (radians)")
        start = self.measured(observation)
        count = max(1, math.ceil(float(np.max(np.abs(target - start))) / .035))
        for side, grip in (grips or {}).items():
            if not math.isfinite(grip) or not 0 <= grip <= 1:
                raise ValueError("Gripper fraction must be in [0,1]")
            count = max(count, math.ceil(abs(grip - observation[side + "_gripper"]) / .1))
        if count > 300:
            raise ValueError("Move exceeds the existing packet budget; request an intermediate target")
        pairs = [start + (target - start) * (i + 1) / count for i in range(count)]
        # Preserve the canonical model's predictive contact check for every joint target.
        for q in pairs:
            self.ik._forward(q)
            if self.ik.data.ncon:
                raise ValueError("Predictive YAM model contact detected")
        return self._points(pairs, observation, first_step, grips)

    def cartesian(self, arm, arguments, observation, first_step):
        index = ("left", "right").index(arm)
        p = finite_vector([arguments["position"][k] for k in "xyz"], 3, "position (metres)")
        raw = finite_vector([arguments["rotation"][k] for k in ("x", "y", "z", "w")], 4, "quaternion")
        if not np.isclose(np.linalg.norm(raw), 1., atol=1e-4):
            raise ValueError("Orientation must be a unit quaternion")
        rotation = Rotation.from_quat(raw).as_matrix()
        initial = self.poses(observation)
        goal = (p + self.bases[index], rotation)
        targets = list(initial)
        targets[index] = goal
        seed = self.measured(observation)
        mode = arguments.get("mode", "linear")
        if mode == "plan":
            solved = self.ik._solve(seed, tuple(targets))
            return self.joints(arm, solved[index * 6:index * 6 + 6].tolist(), observation, first_step)
        if mode != "linear":
            raise ValueError("move_ee mode must be linear or plan")
        position, before_rotation = initial[index]
        distance = float(np.linalg.norm(goal[0] - position))
        angle = float(Rotation.from_matrix(rotation @ before_rotation.T).magnitude())
        count = max(1, math.ceil(distance / .003), math.ceil(angle / math.radians(1)))
        if count > 300:
            raise ValueError("Cartesian move exceeds the existing packet budget")
        interpolation = Slerp([0., 1.], Rotation.from_matrix([before_rotation, rotation]))
        pairs = []

        def extend(a, b, previous, depth=0):
            poses = list(initial)
            poses[index] = (position + b * (goal[0] - position), interpolation(b).as_matrix())
            solved = self.ik._solve(previous, tuple(poses))
            if np.max(np.abs(solved - previous)) > .035 + 1e-9:
                if depth >= 12:
                    raise ValueError("Cartesian path cannot meet existing joint pacing")
                middle = (a + b) / 2
                return extend(middle, b, extend(a, middle, previous, depth + 1), depth + 1)
            if len(pairs) >= 300:
                raise ValueError("Cartesian move exceeds the existing packet budget")
            pairs.append(solved)
            return solved

        for i in range(count):
            seed = extend(i / count, (i + 1) / count, seed)
        return self._points(pairs, observation, first_step)

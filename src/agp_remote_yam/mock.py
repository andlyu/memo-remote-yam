"""Explicit mock station for offline transport/UI validation; no network or motors."""
import io
import time
import numpy as np
from PIL import Image, ImageDraw
from .geometry import YamGeometry
from .backend import ApiBackend
from .workspace import Workspace
from .dependency import runner_root

runner_root()
from remote_yam.session import MockSessionAPI


class MockStation(MockSessionAPI):
    """Add the deployed refresh fields to the upstream deterministic mock."""
    def get_session(self, session_id):
        result = super().get_session(session_id)
        record = self._record(session_id)
        result.update(latest_observation_step=record["next_command_step"],
                      active_trajectory=record["active_trajectory"], lease_id=record["lease_id"])
        return result

    def get_robot_observation(self, robot_id):
        result = super().get_robot_observation(robot_id)
        result.update(settled=True, homed=True)
        if self.trajectory_log:
            final = self.trajectory_log[-1]["waypoints"][-1]
            result.update({key: final[key] for key in ("left_joints_deg", "right_joints_deg", "left_gripper", "right_gripper")})
        return result


def preview(role="top"):
    image = Image.new("RGB", (960, 540), "#e7e5df")
    draw = ImageDraw.Draw(image)
    draw.rounded_rectangle((95, 95, 865, 485), 25, fill="#c2b49c")
    draw.polygon([(250, 230), (320, 215), (350, 255), (275, 270)], fill="#486a58")
    draw.rounded_rectangle((580, 285, 690, 340), 12, fill="#5a738e")
    draw.line([(140, 475), (230, 360), (295, 300)], fill="#ef8e45", width=28)
    draw.line([(810, 475), (730, 365), (710, 290)], fill="#ef8e45", width=28)
    draw.text((35, 25), "OFFLINE MOCK / " + role.upper() + " / NO PHYSICAL ROBOT", fill="#303a3b")
    out = io.BytesIO()
    image.save(out, "JPEG")
    return out.getvalue()


class MockBackend(ApiBackend):
    def __init__(self, workspace, policy, journal):
        from remote_yam.mujoco_ik import ROBOT_SHA256
        self.workspace, self.policy, self.journal = Workspace(workspace), policy, journal
        self.robot_id, self.capture_id = "yam-1", 0
        self.report = dict(robot_id="yam-1", calibration_id="offline-mock-not-physical",
            kinematics=dict(robot_model_sha256=ROBOT_SHA256), base_geometry=dict(spacing_m=.70),
            native_joint_calibration=dict(coordinate_convention="native_i2rt_updated",
                additional_offsets_rad=dict(left=[0.] * 6, right=[0.] * 6)))
        self.geometry = YamGeometry(self.report)

    def command(self, arm, command, arguments):
        result = super().command(arm, command, arguments)
        result["physical"] = False
        return result

    def initial_frames(self, observation):
        return {arm: self.frames(arm, dict(cams=["top", "wrist"] if arm == "left" else ["wrist"],
                                          depth=False), observation) for arm in ("left", "right")}

    def frames(self, arm, arguments, observation):
        self.capture_id += 1
        paths = {}
        calibration_data = dict(mock=True, physical=False, observed_at=time.time(),
            calibration_id='offline-mock-not-physical',
            _meta=dict(calibration_quality=dict(status='mock_no_physical_validation')))
        for camera in arguments.get("cams", ["top", "wrist"]):
            if camera not in ("top", "wrist"):
                raise ValueError("Unknown mock camera")
            image = Image.open(io.BytesIO(preview(camera)))
            out = io.BytesIO()
            image.save(out, "PNG")
            path = f"frames/{self.capture_id:04d}_{arm}_{camera}.png"
            self.workspace.write(path, out.getvalue())
            paths[camera] = path
            calibration_data[camera] = dict(image_size=list(image.size),
                intrinsics=[[500.,0.,480.],[0.,500.,270.],[0.,0.,1.]],
                pose=self.geometry.state(arm,observation),captured_at=time.time(),mock=True)
            if arguments.get('depth',True):
                depth=np.full((image.height,image.width),.25,np.float32)
                raw=io.BytesIO();np.save(raw,depth,allow_pickle=False)
                depth_path=f'frames/{self.capture_id:04d}_{arm}_{camera}_depth.npy'
                self.workspace.write(depth_path,raw.getvalue());paths[camera+'_depth']=depth_path
                raw=io.BytesIO();np.savez(raw,rgb=np.asarray(image),depth_m=depth,
                    metadata=np.array('{"mock":true,"physical":false}'))
                bundle=f'frames/{self.capture_id:04d}_{arm}_{camera}_rgbd.npz'
                self.workspace.write(bundle,raw.getvalue());paths[camera+'_rgbd']=bundle
        calibration = f"frames/{self.capture_id:04d}_{arm}_calib.json"
        self.workspace.json(calibration, calibration_data)
        paths["calibration"] = calibration
        self.journal.add("capture", "Saved mock camera frames", files=paths)
        return dict(capture=self.capture_id, files=paths, physical=False)

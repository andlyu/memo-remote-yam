import io
import json
import time
from types import SimpleNamespace
import numpy as np
from PIL import Image
import pytest
from agp_remote_yam.backend import ApiBackend
from agp_remote_yam.mock import MockBackend
from agp_remote_yam.storage import RunStore, Journal
from remote_yam.api_depth import DepthSnapshot


def backend_for_capture(tmp_path, station, *, rgb_size=(64, 48)):
    _, directory = RunStore(tmp_path).create("capture")
    observation = station.get_robot_observation("yam-1")
    observation["observed_at"] = time.time() - 1
    policy = SimpleNamespace(cancelled=lambda: False)
    mock = MockBackend(directory / "workspace", policy, Journal(directory))
    backend = ApiBackend.__new__(ApiBackend)
    backend.__dict__.update(mock.__dict__)
    backend.origin = "https://station.example"
    camera = dict(K=[[50, 0, 32], [0, 50, 24], [0, 0, 1]], image_size=[64, 48],
        distortion_model="opencv_brown_conrady", distortion=[0.] * 5, rectified=False,
        T_grasp_camera=np.eye(4).tolist(),
        T_base_camera={side: np.eye(4).tolist() for side in ("left", "right")})
    backend.report["cameras"] = {side: dict(camera) for side in ("left", "right", "top")}
    backend.report["quality"] = dict(status="experimental")
    rgb, depth = np.zeros((48, 64, 3), np.uint8), np.full((48, 64), .25, np.float32)
    bundle = io.BytesIO()
    np.savez(bundle, rgb=rgb, depth_m=depth, metadata=np.array('{}'))
    snapshot = DepthSnapshot(rgb, depth, dict(captured_at=time.time()), backend.report, bundle.getvalue())
    backend.depth = {"left": SimpleNamespace(capture=lambda **_: snapshot)}
    jpeg = io.BytesIO()
    Image.new("RGB", rgb_size).save(jpeg, "JPEG")
    backend.rgb = SimpleNamespace(fetch=lambda *_: SimpleNamespace(jpeg=jpeg.getvalue(), source_captured_at=None))
    return backend, observation, directory, snapshot


def test_numeric_depth_and_arm_base_calibration_are_saved(tmp_path, station):
    backend, observation, directory, _ = backend_for_capture(tmp_path, station)
    result = backend.frames("left", {"cams": ["wrist", "top"], "depth": True}, observation)
    root = directory / "workspace"
    depth = np.load(root / result["files"]["wrist_depth"], allow_pickle=False)
    assert depth.dtype == np.float32 and np.allclose(depth, .25)
    assert (root / result["files"]["wrist_rgbd"]).is_file()
    calibration = json.loads((root / result["files"]["calibration"]).read_text())
    assert calibration["wrist"]["image_size"] == [64, 48]
    assert calibration["wrist"]["synchronized_with_state"] is False
    assert calibration["top"]["source_time_available"] is False
    assert calibration["_meta"]["calibration_quality"]["status"] == "experimental"
    expected = backend.geometry.state("left", observation)["position"]
    assert np.allclose(list(calibration["wrist"]["pose"]["position"].values()), list(expected.values()))


def test_stale_wrist_depth_does_not_return_a_capture(tmp_path, station):
    backend, observation, _, snapshot = backend_for_capture(tmp_path, station)
    snapshot.metadata["captured_at"] = observation["observed_at"] - 1
    with pytest.raises(ValueError, match="precedes the settled"):
        backend.frames("left", {"cams": ["wrist"], "depth": True}, observation)


def test_rgb_dimensions_must_match_calibration(tmp_path, station):
    backend, observation, _, _ = backend_for_capture(tmp_path, station, rgb_size=(32, 24))
    with pytest.raises(ValueError, match="dimensions differ"):
        backend.frames("left", {"cams": ["top"], "depth": False}, observation)


def test_frame_after_motion_is_valid_even_if_before_later_idle_telemetry(tmp_path, station):
    backend, observation, _, snapshot = backend_for_capture(tmp_path, station)
    observation["settled_after"] = observation["observed_at"] - 1.
    snapshot.metadata["captured_at"] = observation["observed_at"] - .5
    result = backend.frames("left", {"cams": ["wrist"], "depth": True}, observation)
    assert "wrist_depth" in result["files"]


def test_stale_rgb_is_rejected_without_a_motion(tmp_path, station):
    backend, observation, _, _=backend_for_capture(tmp_path, station)
    original=backend.rgb.fetch
    def stale(*args):
        frame=original(*args);frame.source_captured_at=observation['observed_at']-1
        return frame
    backend.rgb.fetch=stale
    with pytest.raises(ValueError,match='precedes the settled'):
        backend.frames('left',dict(cams=['top'],depth=False),observation)


def test_initial_input_has_both_measured_arms_and_three_labelled_images(tmp_path, station):
    from agp_remote_yam.observation import initial_input,load_initial_input
    from agp_remote_yam.workspace import Workspace
    _,directory=RunStore(tmp_path).create('initial observation')
    observation=station.get_robot_observation('yam-1')
    policy=SimpleNamespace(feedback=lambda:observation,physical=False)
    backend=MockBackend(directory/'workspace',policy,Journal(directory))
    snapshot=initial_input(backend)
    assert set(snapshot['context']['states'])=={'left','right'}
    assert [(v['arm'],v['camera']) for v in snapshot['context']['views']]==[
        ('left','top'),('left','wrist'),('right','wrist')]
    assert len(snapshot['images'])==3
    assert snapshot['context']['physical'] is False and snapshot['context']['depth_included'] is False
    Workspace(directory).json('initial-input.json',snapshot)
    assert load_initial_input(directory/'workspace')==snapshot
    assert not (directory/'workspace/initial-input.json').exists()


def test_readonly_preview_does_not_construct_geometry_or_claim_pose_calibration(tmp_path,station,monkeypatch):
    from agp_remote_yam.observation import ScenePreview,initial_input
    from agp_remote_yam.mock import preview
    from remote_yam.cameras import CameraFrameSource
    from agp_remote_yam.geometry import YamGeometry
    _,directory=RunStore(tmp_path).create('read-only scene')
    monkeypatch.setattr(YamGeometry,'__init__',lambda *_:pytest.fail('Scene preview constructed robot geometry'))
    monkeypatch.setattr(CameraFrameSource,'fetch',lambda _,name,url:SimpleNamespace(
        jpeg=preview(name),received_at=time.time(),source_captured_at=None))
    policy=SimpleNamespace(physical=True)
    scene=ScenePreview('https://example.test','yam-1',directory/'workspace',policy,Journal(directory))
    result=initial_input(scene,station.get_robot_observation('yam-1'))
    assert result['context']['phase']=='monitor_before_admission'
    assert result['context']['camera_poses_valid_for_motion'] is False
    assert result['context']['states']['left']['ee_pose'] is None
    assert len(result['images'])==3

from copy import deepcopy
import math
import numpy as np
import pytest
from agp_remote_yam.geometry import finite_vector


def test_joint_units_and_idle_arm_preserved(geometry, station):
    observation = station.get_robot_observation("yam-1")
    target = np.deg2rad(observation["left_joints_deg"])
    target[0] += .08
    points = geometry.joints("left", target.tolist(), observation, 17)
    assert points[0]["step_id"] == 17
    assert np.allclose(points[-1]["left_joints_deg"], np.rad2deg(target))
    assert all(p["right_joints_deg"] == observation["right_joints_deg"] for p in points)
    assert all(p["right_gripper"] == observation["right_gripper"] for p in points)
    baseline = np.array(observation["left_joints_deg"])
    for point in points:
        assert np.max(np.abs(np.deg2rad(np.array(point["left_joints_deg"]) - baseline))) <= .035 + 1e-9
        baseline = np.array(point["left_joints_deg"])


def test_gripper_preserves_both_measured_arm_positions(geometry, station):
    observation = station.get_robot_observation("yam-1")
    points = geometry.joints("right", np.deg2rad(observation["right_joints_deg"]).tolist(), observation, 0, {"right": 1.})
    assert points[-1]["right_gripper"] == 1.
    assert all(np.allclose(p["left_joints_deg"], observation["left_joints_deg"]) for p in points)
    assert all(np.allclose(p["right_joints_deg"], observation["right_joints_deg"]) for p in points)


@pytest.mark.parametrize('side', ['left', 'right'])
@pytest.mark.parametrize('start,target', [
    (0.9992793312193716, 0.0),  # Measured start of the rejected apple-task close.
    (0.123456789, 1.0),
])
def test_gripper_endpoints_pass_the_unchanged_packet_validator(geometry, station, side, start, target):
    from remote_yam.session import _trajectory_waypoints
    observation = station.get_robot_observation('yam-1')
    observation[side + '_gripper'] = start
    points = geometry.joints(side, np.deg2rad(observation[side + '_joints_deg']).tolist(),
                             observation, 0, {side: target})
    # Exercise the actual validator which rejected the retained physical packet.
    assert _trajectory_waypoints(points) == points
    assert points[-1][side + '_gripper'] == target
    assert all(0 <= p[side + '_gripper'] <= 1 for p in points)
    other = 'right' if side == 'left' else 'left'
    assert all(p[other + '_gripper'] == observation[other + '_gripper'] for p in points)
    for arm in ('left', 'right'):
        assert all(np.allclose(p[arm + '_joints_deg'], observation[arm + '_joints_deg']) for p in points)


@pytest.mark.parametrize('target', [-1e-16, 1.000000000000001, float('nan'), float('inf')])
def test_gripper_repair_does_not_accept_invalid_requested_targets(geometry, station, target):
    observation = station.get_robot_observation('yam-1')
    with pytest.raises(ValueError, match='Gripper fraction'):
        geometry.joints('left', np.deg2rad(observation['left_joints_deg']).tolist(),
                        observation, 0, {'left': target})


@pytest.mark.parametrize("side", ["left", "right"])
def test_cartesian_base_frame_and_orientation_round_trip(geometry, station, side):
    observation = station.get_robot_observation("yam-1")
    pose = geometry.state(side, observation)
    index = ("left", "right").index(side)
    world = geometry.poses(observation)[index][0]
    assert np.allclose(list(pose["position"].values()), world - geometry.bases[index])
    points = geometry.cartesian(side, pose, observation, 0)
    assert np.allclose(points[-1][side + "_joints_deg"], observation[side + "_joints_deg"], atol=.01)
    pose["position"]["z"] += .002
    points = geometry.cartesian(side, pose, observation, 0)
    final = {**observation, **points[-1]}
    measured = geometry.state(side, final)
    assert abs(measured["position"]["z"] - pose["position"]["z"]) < .002


def test_budget_and_limits_reject_without_returning_packet(geometry, station):
    observation = station.get_robot_observation("yam-1")
    target = np.deg2rad(observation["left_joints_deg"]).tolist()
    target[0] += .1
    with pytest.raises(ValueError, match="budget"):
        geometry.joints("left", target, observation, 2999)
    target[0] = 10
    with pytest.raises(ValueError, match="limits|budget"):
        geometry.joints("left", target, observation, 0)


@pytest.mark.parametrize("value", [[True] * 6, [float("nan")] * 6, [float("inf")] * 6, [0] * 5])
def test_invalid_numeric_targets(value):
    with pytest.raises(ValueError):
        finite_vector(value, 6, "joints")


def robohouse_report():
    from remote_yam.controller_workspace import workspace_for_robot
    from remote_yam.mujoco_ik import ROBOT_SHA256
    profile=workspace_for_robot('robot-ba8413962083809c')
    return dict(robot_id=profile.robot_id,base_geometry=dict(spacing_m=.62),
        kinematics=dict(robot_model_sha256=ROBOT_SHA256),
        model_joint_calibration=dict(calibration_id=profile.calibration_id,
            coordinate_convention='original_i2rt_model_corrected',canonical_model_sha256=ROBOT_SHA256,
            offsets_rad=dict(left=list(profile.joint_offsets_rad[:6]),right=list(profile.joint_offsets_rad[6:]))))


def test_robohouse_original_encoder_binding_preserves_command_coordinates(station):
    from agp_remote_yam.geometry import YamGeometry
    from remote_yam.controller_workspace import workspace_for_robot
    report=robohouse_report(); geometry=YamGeometry(report)
    profile=workspace_for_robot(report['robot_id'])
    assert np.allclose(geometry.ik.joint_offsets_rad,profile.joint_offsets_rad)
    observation=station.get_robot_observation('yam-1')
    target=np.deg2rad(observation['left_joints_deg']);target[0]+=.01
    points=geometry.joints('left',target.tolist(),observation,0)
    assert np.allclose(points[-1]['left_joints_deg'],np.rad2deg(target))
    assert points[-1]['right_joints_deg']==observation['right_joints_deg']


@pytest.mark.parametrize('change', ['offset','identity','spacing','native','missing'])
def test_robohouse_rejects_contradictory_or_missing_calibration(change):
    from agp_remote_yam.geometry import YamGeometry
    report=robohouse_report()
    if change=='offset':report['model_joint_calibration']['offsets_rad']['left'][1]+=.01
    if change=='identity':report['model_joint_calibration']['calibration_id']='unverified'
    if change=='spacing':report['base_geometry']['spacing_m']=.7
    if change=='native':report['native_joint_calibration']=dict(coordinate_convention='native_i2rt_updated')
    if change=='missing':report.pop('model_joint_calibration')
    with pytest.raises(ValueError):YamGeometry(report)

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

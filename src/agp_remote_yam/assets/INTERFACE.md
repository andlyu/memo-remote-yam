# Agent as Policy — Remote YAM robot interface

Use `python3 robot_client.py . <command> '<JSON arguments>'`.
For the right arm use `python3 robot_client.py . --arm right <command> '<JSON arguments>'`.
Each call blocks until a matching measured completion or an error. Commands are
sequential. Never automatically retry a timed-out motion. A timeout can mean
that physical execution occurred. Inspect fresh state and report the failure.

| Command | Arguments | Result |
| --- | --- | --- |
| status | {} | Selected robot, calibration, supported commands and cadence |
| help | {} | Command list |
| state | {} | Six joints in radians, base-frame end-effector pose, measured gripper fraction, source timestamp |
| frames | {"cams":["wrist","top"],"depth":true} | Local PNGs, numeric wrist depth .npy in metres, and capture calibration JSON |
| move_ee | {"position":{"x":0.3,"y":0.0,"z":0.2},"rotation":{"w":1,"x":0,"y":0,"z":0},"mode":"linear"} | Achieved measured pose and target error, or failure |
| move_joints | {"joints":[six radians]} | Achieved measured joints and pose |
| gripper | {"action":"open"} or {"action":"close"} or {"action":0.5} | Achieved measured opening fraction |

Examples above illustrate field shapes, not suitable targets for the current scene.
Every response contains `ok`; failed responses include `error_code`, `error`, and
`retryable:false`. Invalid targets send no trajectory. Execution failures terminate
this run's motion path and are never automatically replayed.

Positions are in metres in the selected arm's own base, Z up. Quaternions use
scalar-first `{w,x,y,z}`. The left and right bases are different. Both arms are
available, and each command retains the other arm's measured targets. Tool +Z
points out through the fingers; opening is along tool Y. Gripper 0 is closed,
1 is open. Measured opening does not prove object retention.

`move_ee` defaults to a straight Cartesian path with smoothly interpolated
orientation. `mode:"plan"` requests joint interpolation to the IK endpoint.
The existing runner's YAM model, joint/contact checks, pacing, queue and lease
validation remain active. The API accepts 10 Hz joint waypoints. Timed 50 Hz
throwing programs are not supported by this adapter.

`frames` saves files beneath frames/. Inspect the returned paths. Wrist depth is
float32 optical Z in metres, 0 invalid. Intrinsics, distortion, camera-to-selected-
base pose, calibration identity/quality, and timestamps are in the calibration
file. Our images can be distorted and have different resolutions from the
authors' rig. Read the actual image dimensions and calibration. Camera images
and measured joints are not hardware synchronized; per-camera timestamps are
retained. Depth absence is an error, never replaced by a saved/synthetic image.
Use `depth:false` only when RGB evidence is sufficient for your chosen method.

You may use Python, NumPy, SciPy, Pillow and OpenCV to inspect observations and
write geometry/helpers in scratch/. Robot interaction goes through the client.
Do not infer physical contact from joint angles or motion acceptance. Verify
task outcomes in fresh observations after release and withdrawal.

Read TASK.md and any goal/reference.png. knowledge/ contains optional prior-run
experience. Treat old poses and scene assumptions as historical hypotheses;
recompute from this run's observations. Save reusable, parameterized helpers and
notes to scratch/experience/. The host snapshots these after the run, labels
them agent-authored/unverified, and offers explicit reuse on a later run.

Finish with the structured final result: status done/give_up, summary, evidence.
Use give_up when the evidence cannot establish completion. An agent declaration
is stored separately from independent physical validation.

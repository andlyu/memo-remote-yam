"""Actual adapter generation and pinned packet validation; no robot transport."""
import json
from types import SimpleNamespace
import numpy as np
import pytest
from agp_remote_yam.mock import MockBackend
from agp_remote_yam.storage import Journal, RunStore
from remote_yam.session import _trajectory_waypoints


@pytest.mark.parametrize('side',['left','right'])
def test_advertised_command_path_and_serializer(side,station,tmp_path):
    observation=station.get_robot_observation('yam-1')
    observation['step_id']=0
    _,directory=RunStore(tmp_path).create('control preflight')
    observation[side+'_gripper']=0.9992793312193716
    packets=[]
    def execute(points):
        assert _trajectory_waypoints(json.loads(json.dumps(points,allow_nan=False)))==points
        packets.append(points)
        return dict(observation,**points[-1])
    backend=MockBackend(directory/'workspace',SimpleNamespace(feedback=lambda:observation,execute=execute,
        cancelled=lambda:False),Journal(directory))
    for command in ('state','status','help','--help'):
        assert backend.command(side,command,{})['physical'] is False
    captures=backend.command(side,'frames',dict(cams=['top','wrist'],depth=True))
    assert all(k in captures['files'] for k in ['top_depth','wrist_depth'])
    joints=np.deg2rad(observation[side+'_joints_deg']).tolist()
    backend.command(side,'move_joints',dict(joints=joints))
    pose=backend.geometry.state(side,observation)
    backend.command(side,'move_ee',dict(pose,mode='linear'))
    for action in ('close','open',.5):backend.command(side,'gripper',dict(action=action))
    assert len(packets)==5
    assert packets[2][-1][side+'_gripper']==0
    assert packets[3][-1][side+'_gripper']==1
    other='right' if side=='left' else 'left'
    assert all(p[other+'_gripper']==observation[other+'_gripper'] for packet in packets for p in packet)


def test_invalid_generated_packet_never_reaches_execution(station,tmp_path):
    observation=station.get_robot_observation('yam-1');calls=[]
    observation['step_id']=0
    _,directory=RunStore(tmp_path).create('invalid packet preflight')
    backend=MockBackend(directory/'workspace',SimpleNamespace(feedback=lambda:observation,
        execute=lambda points:calls.append(points)),Journal(directory))
    invalid=dict(step_id=0,left_joints_deg=observation['left_joints_deg'],
        right_joints_deg=observation['right_joints_deg'],left_gripper=-1e-16)
    backend.geometry.joints=lambda *args:[invalid]
    with pytest.raises(ValueError,match='left_gripper'):
        backend.command('left','gripper',dict(action='close'))
    assert calls==[]


def test_local_packet_rejection_keeps_bridge_available(station,tmp_path):
    import threading,time
    from agp_remote_yam.bridge import FileBridge
    observation=station.get_robot_observation('yam-1');observation['step_id']=0
    _,directory=RunStore(tmp_path).create('local failure recovery');workspace=directory/'workspace'
    journal=Journal(directory);calls=[];stopped=threading.Event()
    backend=MockBackend(workspace,SimpleNamespace(feedback=lambda:observation,
        execute=lambda points:calls.append(points)),journal)
    backend.geometry.joints=lambda *args:[dict(step_id=0,
        left_joints_deg=observation['left_joints_deg'],right_joints_deg=observation['right_joints_deg'],
        left_gripper=-1e-16)]
    bridge=FileBridge(workspace,backend,journal,stopped);bridge.start()
    def call(identity,cmd,args):
        path=workspace/'bridge'/f'req_{identity:06}.json'
        path.write_text(json.dumps(dict(id=identity,cmd=cmd,args=args)))
        response=workspace/'bridge'/f'resp_{identity:06}.json';deadline=time.monotonic()+2
        while not response.exists() and time.monotonic()<deadline:time.sleep(.01)
        return json.loads(response.read_text())
    try:
        response=call(1,'gripper',dict(action='close'))
        assert response['ok'] is False and 'left_gripper' in response['error']
        assert calls==[] and not stopped.is_set()
        assert call(2,'help',{})['ok'] is True
    finally:stopped.set();bridge.thread.join(2)

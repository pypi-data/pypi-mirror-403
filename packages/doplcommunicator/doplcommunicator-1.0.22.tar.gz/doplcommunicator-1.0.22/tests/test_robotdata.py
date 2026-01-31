from doplcommunicator import Vector3, Quaternion, RobotData, Pose
import numpy as np

def test_robotdata():
    # Setup
    enabled = True
    emergency = 0
    position = Vector3(1, 2, 3)
    rotation = Quaternion(0.1, 0.2, 0.3, 1)
    robot_pose = Pose(position, rotation)
    flange_pose = Pose(position, rotation)
    pressure = Vector3(0, 0, 1)
    robot_data = RobotData(enabled, emergency, robot_pose, flange_pose, pressure)
    

    # Test
    assert robot_data.enabled == enabled
    assert robot_data.emergency == emergency
    assert robot_data.robot_pose == robot_pose
    assert robot_data.flange_pose == flange_pose
    assert robot_data.pressure == pressure

def test_fromDict():
    # Setup
    enabled = True
    emergency = 0
    position = Vector3(1, 2, 3)
    rotation = Quaternion(0.1, 0.2, 0.3, 1)
    robot_pose = Pose(position, rotation)
    flange_pose = Pose(position, rotation)
    pressure = Vector3(0, 0, 1)
    robot_data = {
        "enabled": enabled,
        "emergency": emergency,
        "robot_pose": {
            "position": {
                "x": 1,
                "y": 2,
                "z": 3
            }, 
            "orientation": {
                "x": 0.1,
                "y": 0.2,
                "z": 0.3,
                "w": 1
            }
        },
        "flange_pose": {
            "position": {
                "x": 1,
                "y": 2,
                "z": 3
            }, 
            "orientation": {
                "x": 0.1,
                "y": 0.2,
                "z": 0.3,
                "w": 1
            }
        },
        "pressure": {
            "x": 0,
            "y": 0,
            "z": 1
        }
    }
    robot_data = RobotData.fromDict(robot_data)

    # Test
    assert robot_data.enabled == enabled
    assert robot_data.emergency == emergency
    assert robot_data.robot_pose == robot_pose
    assert robot_data.flange_pose == flange_pose
    assert robot_data.pressure == pressure

def test_toDict():
    # Setup
    # Setup
    enabled = True
    emergency = 0
    position = Vector3(1, 2, 3)
    rotation = Quaternion(0.1, 0.2, 0.3, 1)
    robot_pose = Pose(position, rotation)
    flange_pose = Pose(position, rotation)
    pressure = Vector3(0, 0, 1)
    robot_data = RobotData(enabled, emergency, robot_pose, flange_pose, pressure)
    robot_data_dict = RobotData.toDict(robot_data)
    robot_data_test_dict = {
        "enabled": enabled,
        "emergency": emergency,
        "robot_pose": {
            "position": {
                "x": 1,
                "y": 2,
                "z": 3
            }, 
            "orientation": {
                "x": 0.1,
                "y": 0.2,
                "z": 0.3,
                "w": 1
            }
        },
        "flange_pose": {
            "position": {
                "x": 1,
                "y": 2,
                "z": 3
            }, 
            "orientation": {
                "x": 0.1,
                "y": 0.2,
                "z": 0.3,
                "w": 1
            }
        },
        "pressure": {
            "x": 0,
            "y": 0,
            "z": 1
        }
    }

    # Test
    assert robot_data_dict["enabled"] == robot_data_test_dict["enabled"]
    assert robot_data_dict["emergency"] == robot_data_test_dict["emergency"]
    assert robot_data_dict["robot_pose"] == robot_data_test_dict["robot_pose"]
    assert robot_data_dict["flange_pose"] == robot_data_test_dict["flange_pose"]
    assert robot_data_dict["pressure"] == robot_data_test_dict["pressure"]
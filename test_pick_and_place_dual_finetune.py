import math
from time import sleep

import numpy as np
import scipy
from scipy.spatial.transform import Rotation
from scipy.special import euler

from franky import Robot, JointVelocityMotion, CartesianVelocityMotion, Duration, JointMotion, Twist

from franky import JointWaypointMotion, JointWaypoint, CartesianMotion, \
    CartesianWaypointMotion, CartesianWaypoint, Affine, Twist, RobotPose, ReferenceType, \
    CartesianState, JointState, RelativeDynamicsFactor
import json
import frankz
import franky

import numpy as np

robotip_0 = "172.16.0.3"
robotip_1 = "172.16.1.3"
robotips = [robotip_0, robotip_1]
gripper_1 = franky.Gripper(robotip_1)
gripper_0 = franky.Gripper(robotip_0)


def home(robot):
    if robot == 0:
        home0 = data[10]["joint_states"][0]
        robot0 = Robot(robotip_0)
        robot0.relative_dynamics_factor = RelativeDynamicsFactor(0.5, 0.5, 0.5)
        home0_place_motion = JointWaypointMotion([JointWaypoint(home0)])
        print(f"Robot_0 going to home position.")
        robot0.move(home0_place_motion)
    elif robot == 1:
        home1 = data[2]["joint_states"][0]
        robot1 = Robot(robotip_1)
        robot1.relative_dynamics_factor = RelativeDynamicsFactor(0.5, 0.5, 0.5)
        home1_place_motion = JointWaypointMotion([JointWaypoint(home1)])
        print(f"Robot_1 going to home position.")
        robot1.move(home1_place_motion)


def map_to_current(traj, current):
    gap = traj[0] - current
    new_traj = []
    for t in traj:
        new_traj.append(t - gap)
    return new_traj


with open("Dual-robots/saved_plan_print_dual_offsetxy.json", "r") as f:
    data = json.load(f)

speed = 0.1  # [m/s]
force = 60.0  # [N]
traj_factor = 3
safe = True

for i, command in enumerate(data):
    if i >= 0:
        if i == 0:
            home(1)
            home(0)
        print(i)
        print(command["type"])
        # print("Press Enter to continue...")
        # input()
        # print("The program has resumed.")
        # if command["robot_id"] == 0:
        #     continue
        if command["type"] == "pick_station":
            continue
        elif command["type"] == "gripper":
            robotid = command["robot_id"]
            robotip = robotips[int(robotid)]
            gripper = franky.Gripper(robotip)
            if command["activate"] == False:
                print(f"Gripper_{robotid} opening.")
                gripper.open(speed)
            elif command["activate"] == True:
                print(f"Gripper_{robotid} grasping.")
                gripper.grasp(0.0, speed, force, epsilon_outer=1.0)
        elif command["type"] == "move_j":
            traj = command["joint_states"]
            robotid = command["robot_id"]
            robotip = robotips[int(robotid)]
            robot = Robot(robotip)
            robot.relative_dynamics_factor = RelativeDynamicsFactor(0.3, 0.3, 0.3)
            waypoint = np.array(command["joint_states"][0]).reshape(-1)
            waypoint_motion = JointWaypointMotion([JointWaypoint(waypoint)])

            print(f"Robot_{robotid} motion executing.")
            robot.move(waypoint_motion)
            new_traj = map_to_current(traj, robot.current_joint_state.position)
            status = frankz.run(new_traj, robotip, traj_factor, 0.05, safe)


        elif command["type"] == "move_l":
            robotid = command["robot_id"]
            robotip = robotips[int(robotid)]
            robot = Robot(robotip)
            robot.relative_dynamics_factor = RelativeDynamicsFactor(0.3, 0.3, 0.3)
            if data[i - 1]["type"] == "gripper" and data[i - 1]["activate"] == True:
                # pick transfer
                if i == 13:
                    pass
                else:
                    cartesian_state = robot.current_cartesian_state
                    robot_pose = cartesian_state.pose  # Contains end-effector pose and elbow position
                    ee_pose_trans = robot_pose.end_effector_pose.translation
                    ee_pose_quat = robot_pose.end_effector_pose.quaternion
                    print(ee_pose_trans)
                    pick_safe_pose = [ee_pose_trans[0], ee_pose_trans[1], ee_pose_trans[2] + 0.015]
                    print(pick_safe_pose)
                    cartesian_pick_motion = CartesianMotion(
                        RobotPose(Affine(pick_safe_pose, ee_pose_quat)))  # With target elbow angle
                    robot.move(cartesian_pick_motion)

                waypoint_place = np.array(command["joint_states"]).reshape(-1)
                waypoint_place_motion = JointWaypointMotion([JointWaypoint(waypoint_place)])
                print(f"Robot_{robotid} pick transfer executing.")
                robot.move(waypoint_place_motion)
            else:
                # pick and place
                waypoint_place = np.array(command["joint_states"]).reshape(-1)
                waypoint_place_motion = JointWaypointMotion([JointWaypoint(waypoint_place)])
                print(f"Robot_{robotid} pick/place executing.")
                robot = Robot(robotip)
                robot.relative_dynamics_factor = RelativeDynamicsFactor(0.5, 0.5, 0.5)
                if i == 96:
                    # place
                    cartesian_state = robot.current_cartesian_state
                    robot_pose = cartesian_state.pose  # Contains end-effector pose and elbow position
                    ee_pose_trans = robot_pose.end_effector_pose.translation
                    ee_pose_quat = robot_pose.end_effector_pose.quaternion
                    print(ee_pose_trans)
                    pick_safe_pose = [ee_pose_trans[0] - 0.004, ee_pose_trans[1], ee_pose_trans[2] - 0.02]
                    cartesian_pick_motion = CartesianMotion(
                        RobotPose(Affine(pick_safe_pose, ee_pose_quat)))  # With target elbow angle
                    robot.move(cartesian_pick_motion)
                elif i == 56:
                    robot.move(waypoint_place_motion)
                    cartesian_state = robot.current_cartesian_state
                    robot_pose = cartesian_state.pose  # Contains end-effector pose and elbow position
                    ee_pose_trans = robot_pose.end_effector_pose.translation
                    ee_pose_quat = robot_pose.end_effector_pose.quaternion
                    print(ee_pose_trans)
                    pick_safe_pose = [ee_pose_trans[0] + 0.000, ee_pose_trans[1] + 0.000, ee_pose_trans[2] + 0.002]
                    cartesian_pick_motion = CartesianMotion(
                        RobotPose(Affine(pick_safe_pose, ee_pose_quat)))  # With target elbow angle
                    robot.move(cartesian_pick_motion)
                else:
                    robot.move(waypoint_place_motion)

# home(0)
# home(1)
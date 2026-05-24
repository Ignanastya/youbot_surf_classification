#!/usr/bin/env python3
import os
import csv
import math
import time
import rospy
import argparse
from pathlib import Path
from geometry_msgs.msg import Twist, Pose2D
from nav_msgs.msg import Odometry
from sensor_msgs.msg import JointState
from enum import Enum

class MotionType(Enum):
    WITH_ANGLE = "with_angle"
    STRAIGHT = "straight"
    SQUARE = "square"
    HOURGLASS = "hourglass"
    CIRCLE = "circle"
    FIGURE_EIGHT = "figure_eight"
    # SPIN = "spin"
    # CIRCLE_WITH_SPIN = "circle_with_spin"

def parse_args():
    parser = argparse.ArgumentParser()

    parser.add_argument('--motion_type', type=str, required=True, help='Type of movement')
    parser.add_argument('--surface', type=str, required=True, help='Surface name')
    parser.add_argument('--csv', type=str, required=True, help='CSV file name')
    parser.add_argument('--angle', type=float, default=0, help='Target movement angle (degrees)')
    parser.add_argument('--velocity', type=float, default=0.1, help="Robot velocity")
    parser.add_argument('--moving_time', type=float, default=5.0, help="Robot movement time")
    parser.add_argument('--reverse', action='store_true', help="Reverse movement")
    
    return parser.parse_args()

BASE_DIR = Path(__file__).resolve().parent

def create_csv():
    with open(f"{BASE_DIR}/data/raw/{csv_name}", 'w', newline='') as csvfile:
        writer = csv.writer(csvfile)
        header = ['motion_type',
                  'surface',
                  'velocity',
                  'target_angle',
                  'time',
                  'aruco_x', 'aruco_y', 'aruco_theta', 
                  'odom_x', 'odom_y', 'odom_theta',
                  'wheel_joint_fl', 'wheel_joint_fr',
                  'wheel_joint_bl', 'wheel_joint_br']
        writer.writerow(header)

def write_in_csv(data):
    with open(f"{BASE_DIR}/data/raw/{csv_name}", 'a', newline='') as csvfile:
        writer = csv.writer(csvfile)
        writer.writerow(data)

class RobotControl:
    def __init__(self):
        rospy.init_node('youbot_control_script')
        self.pubTwist = rospy.Publisher('/youbot_base/mecanum_drive_controller/cmd_vel', Twist, queue_size=1)
        self.cmd = Twist()
        self.pubPose = rospy.Publisher('/local_pose', Pose2D, queue_size=1)
        self.subOdom = rospy.Subscriber("/youbot_base/mecanum_drive_controller/odom", Odometry, self.callbackOdom)
        self.odom = Odometry()
        self.startOdom = Odometry()
        self.subPose = rospy.Subscriber('/coordinates', Pose2D, self.callbackPose)
        self.pose = Pose2D()
        self.startPose = Pose2D()
        self.local_pose = Pose2D()

        self.subJoints = rospy.Subscriber("/joint_states", JointState, self.callbackJointStates)
        self.wheel_efforts = {
            "caster_joint_bl": 0.0,
            "caster_joint_br": 0.0,
            "caster_joint_fl": 0.0,
            "caster_joint_fr": 0.0,
        }

        self.rate = rospy.Rate(5)

        self.ANGLE = 0

    def callbackOdom(self, msg):
        self.odom = msg

    def callbackPose(self, msg):
        self.pose = msg

    def callbackJointStates(self, msg):
        for name, effort in zip(msg.name, msg.effort):
            if name in self.wheel_efforts:
                self.wheel_efforts[name] = effort

    def get_pose(self):
       return self.pose
    
    def get_odom(self):
       return self.odom

    def go(self, vx, vy, omega):
        self.cmd.linear.x = vx
        self.cmd.linear.y = vy
        self.cmd.linear.z = 0
        self.cmd.angular.x = 0
        self.cmd.angular.y = 0
        self.cmd.angular.z = omega
        self.pubTwist.publish(self.cmd)
        # self.rate.sleep()

    def stop(self):
        self.cmd.linear.x = 0
        self.cmd.linear.y = 0
        self.cmd.linear.z = 0
        self.cmd.angular.x = 0
        self.cmd.angular.y = 0
        self.cmd.angular.z = 0
        self.pubTwist.publish(self.cmd)
        self.rate.sleep()

    def publish_local_pose(self):
        self.local_pose.x = self.pose.x - self.startPose.x
        self.local_pose.y = self.pose.y - self.startPose.y
        self.local_pose.theta = self.pose.theta - self.startPose.theta
        botCtrl.pubPose.publish(self.local_pose)
        self.rate.sleep()

    def move_with_angle(self, curr_time, angle, velocity, mov_time):
        if(curr_time <= mov_time):
            vx = math.cos(angle) * velocity
            vy = math.sin(angle) * velocity
            self.go(vx, vy, 0)
            return 0
        else:
            return -1
        
    def move_straight(self, curr_time, velocity, mov_time, reverse):
        # if reverse is False move forward first else backward first
        if(curr_time <= mov_time):
            botCtrl.ANGLE = math.radians(-180) if reverse else 0
        elif(curr_time <= mov_time*2):
            botCtrl.ANGLE = 0 if reverse else math.radians(-180)
        else:
            return -1
        vx = math.cos(botCtrl.ANGLE) * velocity
        self.go(vx, 0, 0)
        return 0
        
        
    def move_square(self, curr_time, velocity, mov_time, reverse):
        # if reverse is True move clockwise else counter-clockwise
        if(curr_time <= mov_time):
            botCtrl.ANGLE = 0
        elif(curr_time <= mov_time*2):
            botCtrl.ANGLE = math.radians(-90) if reverse else math.radians(90)
        elif(curr_time <= mov_time*3):
            botCtrl.ANGLE = math.radians(-180)
        elif(curr_time <= mov_time*4):
            botCtrl.ANGLE = math.radians(90) if reverse else math.radians(-90)
        else:
            return -1
        vx = math.cos(botCtrl.ANGLE) * velocity
        vy = math.sin(botCtrl.ANGLE) * velocity
        self.go(vx, vy, 0)
        return 0
        
        
    def move_hourglass(self, curr_time, velocity, mov_time, reverse):
        # if reverse is True move clockwise else counter-clockwise
        if(curr_time <= mov_time):
            botCtrl.ANGLE = math.radians(30) if reverse else math.radians(-30)
        elif(curr_time <= mov_time*2):
            botCtrl.ANGLE = math.radians(-90) if reverse else math.radians(90)
        elif(curr_time <= mov_time*3):
            botCtrl.ANGLE = math.radians(150) if reverse else math.radians(-150)
        elif(curr_time <= mov_time*4):
            botCtrl.ANGLE = math.radians(-150) if reverse else math.radians(150)
        elif(curr_time <= mov_time*5):
            botCtrl.ANGLE = math.radians(90) if reverse else math.radians(-90)
        elif(curr_time <= mov_time*6):
            botCtrl.ANGLE = math.radians(-30) if reverse else math.radians(30)
        else:
            return -1
        vx = math.cos(botCtrl.ANGLE) * velocity
        vy = math.sin(botCtrl.ANGLE) * velocity
        self.go(vx, vy, 0)
        return 0
    
    def move_circle(self, curr_time, velocity, radius, reverse):
        # if reverse is True move clockwise else counter-clockwise
        angle = curr_time * velocity / radius
        if (angle < 2 * math.pi):
            vx = math.cos(angle) * velocity * (-1 if reverse else 1)
            vy = math.sin(angle) * velocity
            self.go(vx, vy, 0)
            botCtrl.ANGLE = math.atan2(vy, vx)
            return 0
        else:
            return -1
        
    def move_eight(self, curr_time, velocity, radius, reverse):
        # if reverse is True move clockwise else counter-clockwise
        angle = curr_time * velocity / radius
        if (angle < 2 * math.pi):
            vx = math.cos(angle) * velocity * (-1 if reverse else 1)
            vy = math.cos(2*angle) * velocity
            self.go(vx, vy, 0)
            botCtrl.ANGLE = math.atan2(vy, vx)
            return 0
        else:
            return -1
        
    def move_spin(self, curr_time, velocity, mov_time, reverse):
        if(curr_time <= mov_time):
            if (reverse):
                self.go(0, 0, -velocity)
            else:
                self.go(0, 0, velocity)
            return 0
        else:
            return -1
        
    def move_circle_spin(self, curr_time, velocity, radius, reverse):
        # if reverse is True move clockwise else counter-clockwise
        angle = curr_time * velocity / radius
        direction = -1 if reverse else 1
        if (angle < 2 * math.pi):
            vx = velocity * direction
            wz = (velocity / radius) * direction
            self.go(vx, 0, wz)
            botCtrl.ANGLE = math.radians(-180) if reverse else 0
            return 0
        else:
            return -1
        
        

if __name__ == '__main__':

    botCtrl = RobotControl()
    botCtrl.rate.sleep()

    args = parse_args()

    MOTION_TYPE = args.motion_type

    if (MOTION_TYPE == "with_angle"):
        botCtrl.ANGLE = math.radians(args.angle)
        REVERSE = False
    else:
        botCtrl.ANGLE = 0.0
        REVERSE = args.reverse
    SURFACE = args.surface
    csv_name = args.csv
    VELOCITY = args.velocity
    MOV_TIME = args.moving_time

    if not os.path.exists(f"{BASE_DIR}/data/raw/{csv_name}"):
        create_csv()

    print(f"DEBUG: MOTION_TYPE={MOTION_TYPE}, ANGLE={botCtrl.ANGLE}, REVERSE={REVERSE}, MOV_TIME={MOV_TIME}")

    botCtrl = RobotControl()
    botCtrl.rate.sleep()
    start_time = time.time()
    botCtrl.startPose = botCtrl.get_pose()
    botCtrl.startOdom = botCtrl.get_odom()
    while(not rospy.is_shutdown()):

        botCtrl.publish_local_pose()
        curr_time = time.time()-start_time

        if (MOTION_TYPE == "with_angle"):
            res = botCtrl.move_with_angle(curr_time, botCtrl.ANGLE, VELOCITY, MOV_TIME)
        elif (MOTION_TYPE == "straight"):
            res = botCtrl.move_straight(curr_time, VELOCITY, MOV_TIME, REVERSE)
        elif (MOTION_TYPE == "square"):
            res = botCtrl.move_square(curr_time, VELOCITY, MOV_TIME, REVERSE)
        elif (MOTION_TYPE == "hourglass"):
            res = botCtrl.move_hourglass(curr_time, VELOCITY, MOV_TIME, REVERSE)
        elif (MOTION_TYPE == "circle"):
            res = botCtrl.move_circle(curr_time, VELOCITY, MOV_TIME, REVERSE)
        elif (MOTION_TYPE == "figure_eight"):
            res = botCtrl.move_eight(curr_time, VELOCITY, MOV_TIME, REVERSE)
        elif (MOTION_TYPE == "spin"):
            res = botCtrl.move_spin(curr_time, VELOCITY, MOV_TIME, REVERSE)
        elif (MOTION_TYPE == "circle_spin"):
            res = botCtrl.move_circle_spin(curr_time, VELOCITY, MOV_TIME, REVERSE)
        else:
            print("Cannot find suitable motion_type!")
            break
        if(res == -1):
            break

        data = [MOTION_TYPE,
                SURFACE,
                VELOCITY,
                botCtrl.ANGLE,
                curr_time,
                botCtrl.pose.x-botCtrl.startPose.x, 
                botCtrl.pose.y-botCtrl.startPose.y, 
                botCtrl.pose.theta-botCtrl.startPose.theta,
                botCtrl.odom.pose.pose.position.x - botCtrl.startOdom.pose.pose.position.x,
                botCtrl.odom.pose.pose.position.y - botCtrl.startOdom.pose.pose.position.y,
                botCtrl.odom.pose.pose.orientation.z - botCtrl.startOdom.pose.pose.orientation.z,
                botCtrl.wheel_efforts["caster_joint_fl"],
                botCtrl.wheel_efforts["caster_joint_fr"],
                botCtrl.wheel_efforts["caster_joint_bl"],
                botCtrl.wheel_efforts["caster_joint_br"] ]
        write_in_csv(data=data)

    botCtrl.stop()


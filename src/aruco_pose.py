#!/usr/bin/env python3

import rospy
from geometry_msgs.msg import Pose2D
import cv2 as cv
import numpy as np
import yaml
from pathlib import Path
from sensor_msgs.msg import Image
from cv_bridge import CvBridge

aruco_dict = cv.aruco.getPredefinedDictionary(cv.aruco.DICT_4X4_250)
parameters = cv.aruco.DetectorParameters()
Aruco_ID = int(5)

class Aruco_Coord:
    def __init__(self):
        rospy.init_node('aruco_pose_script')
        rospy.loginfo("Run aruco_pose node")
        self.pub = rospy.Publisher('/coordinates', Pose2D, queue_size=10)
        self.rate = rospy.Rate(5) # 5hz

        self.bridge = CvBridge()

        self.image_pub = rospy.Publisher(
            "/aruco_image",
            Image,
            queue_size=1
        )

        self.cap = cv.VideoCapture(2)
        self.cap.set(3, width)
        self.cap.set(4, height)

        rospy.on_shutdown(self.shutdown)

    def publisher(self, x, y, theta):
        pose = Pose2D()
        pose.x = x
        pose.y = y
        pose.theta = theta
        self.pub.publish(pose)
        self.rate.sleep()

    def publish_image(self, frame):
        try:
            msg = self.bridge.cv2_to_imgmsg(
                frame,
                encoding="bgr8"
            )
            msg.header.stamp = rospy.Time.now()
            self.image_pub.publish(msg)
        except Exception as e:
            rospy.logwarn(f"Image publish error: {e}")

    def shutdown(self):
        rospy.loginfo("Shutting down aruco_pose node")
        if self.cap.isOpened():
            self.cap.release()

def read_yaml_config(file_path):
    try:
        with open(file_path, 'r') as file:
            data = yaml.safe_load(file)
        return data
    except FileNotFoundError:
        print(f"Файл {file_path} не найден.")
        return None
    except yaml.YAMLError as e:
        print(f"Ошибка при чтении YAML: {e}")
        return None

def get_array_from_yaml(file_path, array_key):
       with open(file_path, 'r') as file:
           yaml_data = yaml.safe_load(file)
           return yaml_data.get(array_key)
       
def my_estimatePoseSingleMarkers(corners, marker_size, mtx, distortion):
    marker_points = np.array([[-marker_size / 2, marker_size / 2, 0],
                              [marker_size / 2, marker_size / 2, 0],
                              [marker_size / 2, -marker_size / 2, 0],
                              [-marker_size / 2, -marker_size / 2, 0]], dtype=np.float32)
    trash = []
    rvecs = []
    tvecs = []
    for c in corners:
        nada, R, t = cv.solvePnP(marker_points, c, mtx, distortion, False, cv.SOLVEPNP_IPPE_SQUARE)
        rvecs.append(R)
        tvecs.append(t)
        trash.append(nada)
    return rvecs, tvecs, trash

BASE_DIR = Path(__file__).resolve().parent
file_path = BASE_DIR / "params" / "camera_params_v2.yaml"
config_data = read_yaml_config(file_path)

if config_data:
    # Теперь config_data - это словарь, содержащий данные из YAML
    # print(config_data)
    name = config_data.get("camera_name")
    width = config_data.get("image_width")
    height = config_data.get("image_height")
    mtx = np.array(config_data['camera_matrix'])
    dist = np.array(config_data['distortion_coefficients'])
    rvecs = np.array(config_data['rotation_vector'])
    tvecs = np.array(config_data['translation_vector'])


if __name__ == '__main__':
 
    coord = Aruco_Coord()

    if not coord.cap.isOpened():
        print("Cannot open camera")
        exit()
    while not rospy.is_shutdown():
        # Capture frame-by-frame
        ret, frame = coord.cap.read()
    
        # if frame is read correctly ret is True
        if not ret:
            print("Can't receive frame (stream end?). Exiting ...")
            break
        h,  w = frame.shape[:2]
        newcameramtx, roi = cv.getOptimalNewCameraMatrix(mtx, dist, (w,h), 1, (w,h))
        # undistort
        dst = cv.undistort(frame, mtx, dist, None, newcameramtx)
        # crop the image
        x, y, w, h = roi
        dst = dst[y:y+h, x:x+w]
        
        detector = cv.aruco.ArucoDetector(aruco_dict, parameters)
        corners, ids, rejected = detector.detectMarkers(dst)
        
        if not ids is None:
            
            rvecs, tvecs, trash = my_estimatePoseSingleMarkers(corners, 0.19, mtx, dist)
            #cv::drawFrameAxes(outputImage, cameraMatrix, distCoeffs, rvec, tvec, 0.1);
            for idx in range(len(ids)):
                # if (idx == Aruco_ID):
                cv.drawFrameAxes(dst, mtx, dist, rvecs[idx], tvecs[idx], 0.2)
                print('marker id:%d, pos_x = %f,pos_y = %f, pos_theta = %f' % (ids[idx],tvecs[idx][0],tvecs[idx][1],rvecs[idx][2]))
                coord.publisher(tvecs[idx][0], tvecs[idx][1], rvecs[idx][2])
        cv.aruco.drawDetectedMarkers(dst, corners, ids)

        coord.publish_image(dst)

        # # Display the resulting frame
        # cv.imshow(name, dst)
        # if cv.waitKey(1) == ord('q'):
        #     break
    
    # When everything done, release the capture
    coord.cap.release()
    cv.destroyAllWindows()
#!/usr/bin/env python3
import sys
import subprocess
import signal
import cv2 as cv
import rospy
import numpy as np

from sensor_msgs.msg import Image
from cv_bridge import CvBridge

from PyQt5.QtWidgets import (
    QApplication, QMainWindow, QWidget,
    QLabel, QPushButton, QLineEdit,
    QDoubleSpinBox, QVBoxLayout, QHBoxLayout,
    QGridLayout, QMessageBox, QComboBox, QCheckBox
)
from PyQt5.QtCore import Qt, QObject, pyqtSignal, QTimer, QProcess
from PyQt5.QtGui import QImage, QPixmap


# ======================================================
# Video + ArUco thread
# ======================================================
class ArucoImageSubscriber(QObject):
    image_signal = pyqtSignal(QImage)

    def __init__(self):
        super().__init__()
        self.bridge = CvBridge()
        self.sub = rospy.Subscriber(
            "/aruco_image",
            Image,
            self.callback,
            queue_size=1
        )

    def callback(self, msg):
        try:
            frame = self.bridge.imgmsg_to_cv2(msg, "bgr8")
            rgb = cv.cvtColor(frame, cv.COLOR_BGR2RGB)
            h, w, ch = rgb.shape
            qt_img = QImage(
                rgb.data, w, h, ch * w,
                QImage.Format_RGB888
            )
            self.image_signal.emit(qt_img)
        except Exception as e:
            rospy.logwarn(f"Image convert error: {e}")

class ArucoManager:
    def __init__(self):
        self.proc = None

    def start(self):
        if self.proc is None:
            self.proc = subprocess.Popen(
                ['rosrun', 'nirs', 'aruco_pose.py'],
                preexec_fn=lambda: signal.signal(signal.SIGINT, signal.SIG_IGN)
            )

    def stop(self):
        if self.proc:
            self.proc.terminate()
            self.proc = None

    def __del__(self):
        try:
            self.stop()
        except Exception:
            pass


# ======================================================
# Teleop process manager
# ======================================================
# class TeleopManager:
#     def __init__(self):
#         self.proc = None

#     def start(self):
#         if self.proc is None:
#             self.proc = subprocess.Popen(
#                 [
#                     'rosrun',
#                     'teleop_twist_keyboard',
#                     'teleop_twist_keyboard.py'
#                 ],
#                 stdin=subprocess.PIPE
#             )

#     def stop(self):
#         if self.proc:
#             self.proc.terminate()
#             self.proc = None

#     def __del__(self):
#         try:
#             self.stop()
#         except Exception:
#             pass


class Mode:
    NONE = "NONE"
    RUNNING = "RUNNING"
    FINISHED = "FINISHED"
    STOPPED = "STOPPED"

# ======================================================
# Main GUI
# ======================================================
class YoubotGUI(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("youBot Experiment GUI")
        self.setGeometry(50, 50, 1000, 600)

        rospy.init_node('youbot_gui', anonymous=True)

        self.control_proc = None
        self.aruco = ArucoManager()
        self.aruco_sub = ArucoImageSubscriber()
        self.aruco.start()
        self.aruco_sub.image_signal.connect(self.update_video)

        self._init_ui()
        self.set_mode(Mode.NONE)

    # --------------------------------------------------
    # UI
    # --------------------------------------------------
    def _init_ui(self):
        central = QWidget()
        self.setCentralWidget(central)

        main_layout = QHBoxLayout()

        # ================= LEFT: controls =================
        left = QVBoxLayout()

        grid = QGridLayout()

        grid.addWidget(QLabel("Surface name:"), 0, 0)
        self.surface_edit = QLineEdit("linoleum")
        grid.addWidget(self.surface_edit, 0, 1)

        grid.addWidget(QLabel("Motion type:"), 1, 0)
        self.motion_combo = QComboBox()
        self.motion_combo.addItems([
            "with_angle",
            "straight",
            "square",
            "hourglass",
            # "With angle",
            # "Straight/Back",
            # "Square",
            # "Hourglass",
            # "Круг",
            # "Восьмерка",
            # "Вращение на месте",
            # "Дуга",
            # "Круг с вращением"
        ])
        # self.motion_combo.currentIndexChanged.connect(self.update_motion_params)

        grid.addWidget(self.motion_combo, 1, 1)

        grid.addWidget(QLabel("Reverse movement:"), 2, 0)
        self.reverse = QCheckBox()
        self.reverse.setChecked(False)
        grid.addWidget(self.reverse, 2, 1)

        grid.addWidget(QLabel("Target angle (degrees):"), 3, 0)
        self.angle_spin = QDoubleSpinBox()
        self.angle_spin.setRange(-180, 180)
        self.angle_spin.setSingleStep(5)
        self.angle_spin.setValue(0.0)
        grid.addWidget(self.angle_spin, 3, 1)

        grid.addWidget(QLabel("Velocity (m/s):"), 4, 0)
        self.vel_spin = QDoubleSpinBox()
        self.vel_spin.setRange(0.01, 1.0)
        self.vel_spin.setSingleStep(0.01)
        self.vel_spin.setValue(0.1)
        grid.addWidget(self.vel_spin, 4, 1)

        grid.addWidget(QLabel("Move time (s):"), 5, 0)
        self.time_spin = QDoubleSpinBox()
        self.time_spin.setRange(1, 10)
        self.time_spin.setSingleStep(1)
        self.time_spin.setValue(5)
        grid.addWidget(self.time_spin, 5, 1)

        grid.addWidget(QLabel("CSV file:"), 6, 0)
        self.csv_edit = QLineEdit("experiment.csv")
        self.csv_edit.setMinimumWidth(150)
        grid.addWidget(self.csv_edit, 6, 1)

        left.addLayout(grid)

        # ----- buttons -----
        self.start_btn = QPushButton("▶ Start experiment")
        self.stop_btn = QPushButton("■ Stop experiment")
        # self.teleop_start_btn = QPushButton("▶ Start keyboard control")
        # self.teleop_stop_btn = QPushButton("■ Stop keyboard control")

        left.addWidget(self.start_btn)
        left.addWidget(self.stop_btn)
        # left.addWidget(self.teleop_start_btn)
        # left.addWidget(self.teleop_stop_btn)
        left.addStretch()

        self.start_btn.clicked.connect(self.start_experiment)
        self.stop_btn.clicked.connect(self.stop_experiment)
        # self.teleop_start_btn.clicked.connect(self.start_teleop)
        # self.teleop_stop_btn.clicked.connect(self.stop_teleop)

        # ----- mode indicator -----
        self.mode_label = QLabel("● NONE")
        self.mode_label.setAlignment(Qt.AlignCenter)
        self.mode_label.setStyleSheet(
            "font-size: 16px; font-weight: bold; color: gray;"
        )

        left.addWidget(self.mode_label)

        # self.experiment_timer = QTimer(self)
        # self.experiment_timer.setSingleShot(True)
        # self.experiment_timer.timeout.connect(self.finish_experiment)

        # ================= RIGHT: video =================
        right = QVBoxLayout()
        self.video_label = QLabel("Camera not started")
        self.video_label.setAlignment(Qt.AlignCenter)
        self.video_label.setFixedSize(1024, 768)
        right.addWidget(self.video_label)

        main_layout.addLayout(left, 1)
        main_layout.addLayout(right, 2)

        central.setLayout(main_layout)

    

    # --------------------------------------------------
    # Video
    # --------------------------------------------------
    def update_video(self, img):
        self.video_label.setPixmap(QPixmap.fromImage(img))

    def set_mode(self, mode):
        if mode == Mode.NONE:
            self.mode_label.setText("● NONE")
            self.mode_label.setStyleSheet(
                "font-size: 16px; font-weight: bold; color: gray;"
            )

        elif mode == Mode.RUNNING:
            self.mode_label.setText("● RUNNING")
            self.mode_label.setStyleSheet(
                "font-size: 16px; font-weight: bold; color: orange;"
            )

        elif mode == Mode.FINISHED:
            self.mode_label.setText("● FINISHED")
            self.mode_label.setStyleSheet(
                "font-size: 16px; font-weight: bold; color: green;"
            )

        elif mode == Mode.STOPPED:
            self.mode_label.setText("● STOPPED")
            self.mode_label.setStyleSheet(
                "font-size: 16px; font-weight: bold; color: red;"
            )

    # --------------------------------------------------
    # Experiment control
    # --------------------------------------------------
    def start_experiment(self):
        if self.control_proc:
            QMessageBox.warning(self, "Warning", "Experiment already running")
            return

        # self.stop_teleop()

        cmd = [
            'rosrun', 'nirs', 'youbot_control.py',
            '--motion_type', self.motion_combo.currentText(),
            '--motion_type', self.motion_combo.currentText(),
            '--angle', str(self.angle_spin.value()),
            '--surface', self.surface_edit.text(),
            '--velocity', str(self.vel_spin.value()),
            '--moving_time', str(self.time_spin.value()),
            '--csv', self.csv_edit.text()
        ]
        if self.reverse.isChecked():
            cmd.append('--reverse')

        self.control_proc = QProcess()
        self.control_proc.setProcessChannelMode(QProcess.ForwardedChannels) 
        self.control_proc.finished.connect(self.finish_experiment)
        self.control_proc.start(cmd[0], cmd[1:])
        self.set_mode(Mode.RUNNING)

    def stop_experiment(self):
        if self.control_proc:
            self.control_proc.finished.disconnect(self.finish_experiment)
            self.control_proc.terminate()
            if not self.control_proc.waitForFinished(500):
                self.control_proc.kill()
            self.control_proc = None
            self.set_mode(Mode.STOPPED)

    def finish_experiment(self):
        self.control_proc = None
        self.set_mode(Mode.FINISHED)


    # --------------------------------------------------
    # Teleop
    # --------------------------------------------------
    # def start_teleop(self):
    #     if self.control_proc:
    #         QMessageBox.warning(
    #             self, "Warning",
    #             "Stop experiment before teleop"
    #         )
    #         return
    #     self.teleop.start()
    #     self.set_mode(Mode.TELEOP)

    # def stop_teleop(self):
    #     self.teleop.stop()
    #     self.set_mode(Mode.IDLE)

    # --------------------------------------------------
    # Close
    # --------------------------------------------------
    def closeEvent(self, event):
        self.stop_experiment()
        # self.stop_teleop()
        # self.video_thread.stop()
        self.aruco.stop()
        self.set_mode(Mode.NONE)
        event.accept()

    # def __del__(self):
    #     try:
    #         self.closeEvent()
    #     except Exception:
    #         pass


# ======================================================
# Main
# ======================================================
if __name__ == '__main__':
    app = QApplication(sys.argv)
    gui = YoubotGUI()
    gui.show()
    sys.exit(app.exec_())
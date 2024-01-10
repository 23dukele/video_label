import cv2
import numpy as np
from PyQt5.QtWidgets import QApplication, QLabel, QMainWindow, QVBoxLayout, QWidget, QStatusBar
from PyQt5.QtGui import QImage, QPixmap
from PyQt5.QtCore import Qt, QTimer
import argparse

class VideoLabelingApp(QMainWindow):
    def __init__(self, video_path):
        super(VideoLabelingApp, self).__init__()

        self.video_path = video_path

        if not self.is_valid_video():
            print("Error: Unable to open video file.")
            return

        self.init_ui()

        self.capture = cv2.VideoCapture(self.video_path)
        self.frame_counter = 0

        self.annotations = []  # Store drawn annotations for each frame
        self.quad = np.zeros((4, 2), dtype=int)
        self.point_num = 0

        self.timer = QTimer(self)
        self.timer.timeout.connect(self.update_frame)
        self.timer.start(30)

        # Flag to control whether to update the frame or not
        self.update_frame_flag = False

        # Resize variables
        self.resize_ratio = 1.0

    def is_valid_video(self):
        return cv2.VideoCapture(self.video_path).isOpened()

    def init_ui(self):
        self.central_widget = QWidget(self)
        self.setCentralWidget(self.central_widget)

        self.video_label = QLabel(self)
        self.video_label.setAlignment(Qt.AlignCenter)

        layout = QVBoxLayout(self.central_widget)
        layout.addWidget(self.video_label)

        self.setMouseTracking(True)

        # Create and set up the status bar
        self.status_bar = QStatusBar()
        self.setStatusBar(self.status_bar)
        self.status_bar.showMessage("Press 'N' to show the next frame, 'R' to clear annotations, 'Q' to exit" )

    def resize_to_720p(self, frame):
        target_height = 900
        height, _, _ = frame.shape
        self.resize_ratio = target_height / height
        resized_frame = cv2.resize(frame, (int(frame.shape[1] * self.resize_ratio), int(frame.shape[0] * self.resize_ratio)))
        return resized_frame

    def mousePressEvent(self, event):
        if event.button() == Qt.LeftButton:
            # If it's the second click, draw a line and save coordinates
            x, y = event.x(), event.y()
            _x = x / self.resize_ratio
            _y = y / self.resize_ratio
            self.quad[self.point_num % 4] = [int(x), int(y)]
            print(f"Point {self.point_num % 4+1} - x = {int(_x)}, y = {int(_y)}")
            self.draw_quad()
            self.display_frame()
            self.point_num += 1



    def keyPressEvent(self, event):
        if event.key() == Qt.Key_N:
            self.update_frame_flag = True
        elif event.key() == Qt.Key_R:
            self.clear_quad()
        elif event.key() == Qt.Key_Q:
            self.close()

    def draw_quad(self):
        if self.point_num <= 3:
            for i in range(4):
                cv2.circle(self.img_drawing, tuple(self.quad[i]), 3, (0, 255, 0), -1, cv2.LINE_AA)
        if self.point_num == 3:
            # Four points, draw a green quadrilateral
            for i in range(4):
                cv2.line(self.img_drawing, tuple(self.quad[i]), tuple(self.quad[(i + 1) % 4]), (0, 255, 0), 1, cv2.LINE_AA)
            # Save the drawn quadrilateral to annotations list
            self.annotations = [self.quad.copy()]

    def clear_quad(self):
        self.quad = np.zeros((4, 2), dtype=int)
        self.point_num = 0
        self.img_drawing = self.img_original.copy()  # Reset img_drawing to the original frame
        self.update_frame_flag = False  # Set update_frame_flag to False to avoid immediate update of the frame
        self.display_frame()

    def update_frame(self):
        if not self.update_frame_flag:
            return

        ret, frame = self.capture.read()
        if not ret:
            print("Video Finished!")
            self.timer.stop()
            return

        self.frame_counter += 1
        self.img_original = self.resize_to_720p(frame)
        self.img_drawing = self.img_original.copy()

        # Draw annotations for all frames
        for idx in range(len(self.annotations)):
            annotations = self.annotations[idx]
            self.draw_annotations(annotations)

        if np.any(self.quad):
            self.draw_quad()

        self.display_frame()
        self.update_frame_flag = False

    def draw_annotations(self, annotations):
        # Draw annotations for the current frame
        for i in range(4):
            cv2.circle(self.img_drawing, tuple(annotations[i]), 3, (0, 255, 0), -1, cv2.LINE_AA)
        for i in range(4):
            cv2.line(self.img_drawing, tuple(annotations[i]), tuple(annotations[(i + 1) % 4]), (0, 255, 0), 1, cv2.LINE_AA)

    def display_frame(self):
        if np.any(self.quad):
            self.draw_quad()

        height, width, channel = self.img_original.shape
        bytes_per_line = 3 * width
        # Convert the image from BGR to RGB
        q_image = QImage(cv2.cvtColor(self.img_drawing, cv2.COLOR_BGR2RGB).data, width, height, bytes_per_line, QImage.Format_RGB888)
        pixmap = QPixmap.fromImage(q_image)
        self.video_label.setPixmap(pixmap)

def main(video_path):
    app = QApplication([])
    video_labeling_app = VideoLabelingApp(video_path)
    if video_labeling_app.is_valid_video():
        video_labeling_app.setGeometry(100, 100, 800, 600)
        video_labeling_app.show()
        app.exec_()
    else:
        print("Error: Unable to open video file.")

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Video Labeling App')
    parser.add_argument('-v','--video_path', type=str, default='./test.mp4', help='Path to the video file')
    args = parser.parse_args()
    main(args.video_path)

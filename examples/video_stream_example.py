from PyQt4 import QtCore, QtGui
import sys
sys.path.append('../')
from utility import ConvertImageBase64, placeholder_image
from threading import Thread
import numpy as np
import cv2
import random
import imutils
import pyqtgraph as pg
import time

"""Video Window Widget Example"""
class VideoWindowWidget(QtGui.QWidget):
    def __init__(self, parent=None):
        super(VideoWindowWidget, self).__init__(parent)

        self.capture = None
        self.video_file = None
        self.is_video_file_or_stream_loaded = False
        self.pause = True
        self.MIN_WINDOW_WIDTH = 400
        self.MIN_WINDOW_HEIGHT = 400


        self.FREQUENCY = .002
        self.TIMER_FREQUENCY = self.FREQUENCY * 1000

        # Ensure video frame is created before overlay
        # since overlay with invisible crosshair plot is place above
        self.video_frame = QtGui.QLabel()
        
        self.layout = QtGui.QGridLayout()
        self.layout.addWidget(self.video_frame,0,0)

        self.init_placeholder_image()
        self.setLayout(self.layout)

        self.timer = QtCore.QTimer()
        self.timer.timeout.connect(self.set_frame)
        self.get_frame_thread = Thread(target=self.get_frame, args=())
        self.get_frame_thread.daemon = True
        self.get_frame_thread.start()
        self.start_capture()

    def init_placeholder_image(self):
        """Set placeholder image when video is stopped"""
        self.convert_image = ConvertImageBase64()
        self.placeholder_image = self.convert_image.decode_image_from_base64(placeholder_image)
        
        # Maintain aspect ratio
        #self.placeholder_image = imutils.resize(self.placeholder_image, width=self.MIN_WINDOW_WIDTH)
        self.placeholder_image = cv2.resize(self.placeholder_image, (self.MIN_WINDOW_WIDTH, self.MIN_WINDOW_HEIGHT))

        self.placeholder = QtGui.QImage(self.placeholder_image, self.placeholder_image.shape[1], self.placeholder_image.shape[0], QtGui.QImage.Format_RGB888).rgbSwapped()
        self.placeholder_image = QtGui.QPixmap.fromImage(self.placeholder)
        self.video_frame.setPixmap(self.placeholder_image)

    def start_capture(self):
        self.pause = False
        self.timer.start(self.TIMER_FREQUENCY)

    def pause_capture(self):
        if not self.pause:
            self.pause = True
            self.timer.stop()

    def stop_capture(self):
        self.pause_capture()
        self.capture = cv2.VideoCapture(str(self.video_file))

    def load_video_file(self):
        """Open file explorer to select media file"""

        try:
            self.video_file = QtGui.QFileDialog.getOpenFileName(self, 'Select .h264 Video File')
            if self.video_file:
                self.is_video_file_or_stream_loaded = True
                self.pause = False
                self.capture = cv2.VideoCapture(str(self.video_file))
        except:
            print("Please select a .h264 file")

    def open_network_stream(self):
        """Opens popup dialog to enter IP network stream"""

        text, pressed_status = QtGui.QInputDialog.getText(self, "Open Media", "Please enter a network URL:")
        link = str(text)
        if pressed_status and self.verify_network_stream(link):
            self.is_video_file_or_stream_loaded = True
            self.pause = False
            self.video_file = link
            self.capture = cv2.VideoCapture(link)
            
    def verify_network_stream(self, link):
        """Attempts to receive a frame from given link"""

        cap = cv2.VideoCapture(link)
        if cap is None or not cap.isOpened():
            return False
        return True

    def get_frame(self):
        """Reads frame, resizes, and converts image to pixmap"""

        while True:
            try:
                if not self.pause and self.capture.isOpened():
                    status, self.frame = self.capture.read()
                    if self.frame is not None:
                        self.frame = imutils.resize(self.frame, width=self.MIN_WINDOW_WIDTH)
                        self.img = QtGui.QImage(self.frame, self.frame.shape[1], self.frame.shape[0], QtGui.QImage.Format_RGB888).rgbSwapped()
                        self.pix = QtGui.QPixmap.fromImage(self.img)
            except:
                pass
            time.sleep(self.FREQUENCY)

    def set_frame(self):
        """Sets pixmap image to video frame"""

        try:
            self.video_frame.setPixmap(self.pix)
        except:
            pass

    def get_video_window_layout(self):
        return self.layout
    
class VideoStreamWidget(QtGui.QWidget):
    def __init__(self, parent=None):
        super(VideoStreamWidget, self).__init__(parent)
        
        self.video_window = VideoWindowWidget()

        self.start_button = QtGui.QPushButton('Start')
        self.start_button.clicked.connect(self.video_window.start_capture)
        self.pause_button = QtGui.QPushButton('Pause')
        self.pause_button.clicked.connect(self.video_window.pause_capture)
        self.stop_button = QtGui.QPushButton('Stop')
        self.stop_button.clicked.connect(self.video_window.stop_capture)

        self.layout = QtGui.QGridLayout()
        self.button_layout = QtGui.QHBoxLayout()
        self.button_layout.addWidget(self.start_button)
        self.button_layout.addWidget(self.pause_button)
        self.button_layout.addWidget(self.stop_button)

        self.layout.addLayout(self.button_layout,0,0)
        self.layout.addWidget(self.video_window,1,0)

    def get_video_display_layout(self):
        return self.layout

    def open_network_stream(self):
        self.video_window.open_network_stream()

    def load_video_file(self):
        self.video_window.load_video_file()

if __name__ == '__main__':
    # Create main application window
    app = QtGui.QApplication([])
    app.setStyle(QtGui.QStyleFactory.create("Cleanlooks"))
    mw = QtGui.QMainWindow()
    mw.setWindowTitle('Video Stream Widget')

    # Create and set widget layout
    # Main widget container
    cw = QtGui.QWidget()
    ml = QtGui.QGridLayout()
    cw.setLayout(ml)
    mw.setCentralWidget(cw)

    # Create Video Stream Widget
    video_stream_widget = VideoStreamWidget()

    mb = mw.menuBar()
    media_menu = mb.addMenu('&Media')

    open_network_stream_action = QtGui.QAction('Open Network Stream', mw)
    open_network_stream_action.setShortcut('Ctrl+N')
    open_network_stream_action.setStatusTip('Input video stream link')
    open_network_stream_action.triggered.connect(video_stream_widget.open_network_stream)
    media_menu.addAction(open_network_stream_action)

    open_media_file_action = QtGui.QAction('Open Media File', mw)
    open_media_file_action.setShortcut('Ctrl+O')
    open_media_file_action.setStatusTip('Open media file')
    open_media_file_action.triggered.connect(video_stream_widget.load_video_file)
    media_menu.addAction(open_media_file_action)

    ml.addLayout(video_stream_widget.get_video_display_layout(),0,0)

    mw.show()
    if(sys.flags.interactive != 1) or not hasattr(QtCore, 'PYQT_VERSION'):
        QtGui.QApplication.instance().exec_()


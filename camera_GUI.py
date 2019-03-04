from PyQt4 import QtCore, QtGui
import sys
from utility import video_placeholder_image
from utility import ConvertImageBase64
from threading import Thread
import numpy as np
import cv2
import random
import imutils
import pyqtgraph as pg
import time

"""Video Window Widget Example"""
class VideoWindowWidget(QtGui.QWidget):
    def __init__(self, width, height, aspect_ratio, parent=None):
        super(VideoWindowWidget, self).__init__(parent)
        
        self.convert_image = ConvertImageBase64()

        self.screen_width = width
        self.screen_height = height
        self.maintain_aspect_ratio = aspect_ratio

        self.capture = None
        self.video_file = None
        self.is_video_file_or_stream_loaded = False
        self.pause = True

        self.video_frame = QtGui.QLabel()
        
        self.layout = QtGui.QGridLayout()
        self.layout.addWidget(self.video_frame,0,0)
        
        self.init_placeholder_image()
        '''
        self.timer = QtCore.QTimer()
        self.timer.timeout.connect(self.set_frame)
        self.get_frame_thread = Thread(target=self.get_frame, args=())
        self.get_frame_thread.daemon = True
        self.get_frame_thread.start()
        self.start_capture()
        '''

    def init_placeholder_image(self):
        """Set placeholder image when video is stopped"""

        self.placeholder_image = self.convert_image.decode_image_from_base64(video_placeholder_image)
        
        if self.maintain_aspect_ratio:
            # Maintain aspect ratio
            self.placeholder_image = imutils.resize(self.placeholder_image, width=self.screen_width)
        else:
            self.placeholder_image = cv2.resize(self.placeholder_image, (self.screen_width, self.screen_height))
        print(len(self.placeholder_image[1]), len(self.placeholder_image[0]))
        self.placeholder = QtGui.QImage(self.placeholder_image, self.placeholder_image.shape[1], self.placeholder_image.shape[0], QtGui.QImage.Format_RGB888).rgbSwapped()
        self.placeholder_image = QtGui.QPixmap.fromImage(self.placeholder)
        self.video_frame.setPixmap(self.placeholder_image)

    def start_capture(self):
        self.pause = False
        self.timer.start(0)

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
                        if self.maintain_aspect_ratio:
                            self.frame = imutils.resize(self.frame, width=self.screen_width)
                        else:
                            self.frame = cv2.resize(self.frame, (self.screen_width, self.screen_height))
                        self.img = QtGui.QImage(self.frame, self.frame.shape[1], self.frame.shape[0], QtGui.QImage.Format_RGB888).rgbSwapped()
                        self.pix = QtGui.QPixmap.fromImage(self.img)
            except:
                pass

    def set_frame(self):
        """Sets pixmap image to video frame"""

        try:
            self.video_frame.setPixmap(self.pix)
        except:
            pass

    def get_video_window_layout(self):
        return self.layout
    
if __name__ == '__main__':

    # Create main application window
    app = QtGui.QApplication([])
    app.setStyle(QtGui.QStyleFactory.create("Cleanlooks"))
    mw = QtGui.QMainWindow()
    mw.setWindowTitle('Camera GUI')

    # Create and set widget layout
    # Main widget container
    cw = QtGui.QWidget()
    ml = QtGui.QGridLayout()
    cw.setLayout(ml)
    mw.setCentralWidget(cw)
    mw.showMaximized()
    # mw.showFullScreen()

    screen_width = QtGui.QApplication.desktop().screenGeometry().width()
    screen_height = QtGui.QApplication.desktop().screenGeometry().height()
    
    # Create Video Window Widget
    parking_lot  = VideoWindowWidget(screen_width, screen_height/2, True)
    bottom_left = VideoWindowWidget(screen_width/3, screen_height/2, False)
    bottom_middle = VideoWindowWidget(screen_width/3, screen_height/2, False)
    bottom_right = VideoWindowWidget(screen_width/3, screen_height/2, False)

    mb = mw.menuBar()
    media_menu = mb.addMenu('&Media')

    open_network_stream_action = QtGui.QAction('Open Network Stream', mw)
    open_network_stream_action.setShortcut('Ctrl+N')
    open_network_stream_action.setStatusTip('Input video stream link')
    open_network_stream_action.triggered.connect(parking_lot .open_network_stream)
    media_menu.addAction(open_network_stream_action)

    open_media_file_action = QtGui.QAction('Open Media File', mw)
    open_media_file_action.setShortcut('Ctrl+O')
    open_media_file_action.setStatusTip('Open media file')
    open_media_file_action.triggered.connect(parking_lot .load_video_file)
    media_menu.addAction(open_media_file_action)

    ml.addLayout(parking_lot.get_video_window_layout(),0,0,1,3)
    ml.addLayout(bottom_left.get_video_window_layout(),1,0,1,1)
    ml.addLayout(bottom_middle.get_video_window_layout(),1,1,1,1)
    ml.addLayout(bottom_right.get_video_window_layout(),1,2,1,1)

    mw.show()

    if(sys.flags.interactive != 1) or not hasattr(QtCore, 'PYQT_VERSION'):
        QtGui.QApplication.instance().exec_()



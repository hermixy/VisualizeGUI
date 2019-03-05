from PyQt4 import QtCore, QtGui
from utility import ConvertImageBase64, video_placeholder_image
from threading import Thread, RLock
from load_CSS import load_CSS
import sys
import cv2
import imutils
import pyqtgraph as pg

class VideoWindowWidget(QtGui.QWidget):
    def __init__(self, width, height, aspect_ratio, default_camera_number,  parent=None):
        super(VideoWindowWidget, self).__init__(parent)

        # Lock to prevent treads from accessing shared resource
        self.lock = RLock()
        self.screen_width = width
        self.screen_height = height
        self.maintain_aspect_ratio = aspect_ratio
        self.capture = None

        self.camera_number = default_camera_number
        
        self.camera_number_table = {'Driveway': 47,
                                    'Lot UUXO': 40,
                                    'Back Young': 44,
                                    'Back King': 42,
                                    'Parking Lot': 43,
                                    'Front Young': 46,
                                    'Front King': 41}

        self.camera_stream_link = 'rtsp://admin:sagnac808@192.168.1.{}:554/cam/realmonitor?channel=1&subtype=0'.format(self.camera_number)

        print(self.camera_stream_link)
        self.video_frame = QtGui.QLabel()

        self.layout = QtGui.QGridLayout()
        self.layout.addWidget(self.video_frame,0,0)
        
        self.init_placeholder_image()

        self.load_network_stream()
        self.get_frame_thread = Thread(target=self.get_frame, args=())
        self.get_frame_thread.daemon = True
        self.get_frame_thread.start()
        self.timer = QtCore.QTimer()
        self.timer.timeout.connect(self.set_frame)
        self.timer.start(0)

    def init_placeholder_image(self):
        """Set placeholder image when video is stopped"""

        self.convert_image = ConvertImageBase64()
        self.placeholder_image = self.convert_image.decode_image_from_base64(video_placeholder_image)
        
        # Maintain aspect ratio
        if self.maintain_aspect_ratio:
            self.placeholder_image = imutils.resize(self.placeholder_image, width=self.screen_width)
        # Force resize image
        else:
            self.placeholder_image = cv2.resize(self.placeholder_image, (self.screen_width, self.screen_height))

        # Convert into QPixmap format
        self.placeholder = QtGui.QImage(self.placeholder_image, self.placeholder_image.shape[1], self.placeholder_image.shape[0], QtGui.QImage.Format_RGB888).rgbSwapped()
        self.placeholder_image = QtGui.QPixmap.fromImage(self.placeholder)
        self.video_frame.setPixmap(self.placeholder_image)

    def load_network_stream(self):
        if self.verify_network_stream(self.camera_stream_link):
            self.capture = cv2.VideoCapture(self.camera_stream_link)

    def change_network_stream(self):
        """Opens popup dialog to enter IP network stream"""

        text, pressed_status = QtGui.QInputDialog.getText(self, "Open Media", "Please enter a network URL:")
        link = str(text)
        if pressed_status and self.verify_network_stream(link):
            self.capture = cv2.VideoCapture(link)
            
    def verify_network_stream(self, link):
        """Attempts to receive a frame from given link"""

        cap = cv2.VideoCapture(link)
        if cap is None or not cap.isOpened():
            return False
        cap.release()
        return True

    def get_frame(self):
        """Reads frame, resizes, and converts image to pixmap"""

        while True:
            if self.capture.isOpened():
                status, frame = self.capture.read()
                if frame is not None:
                    self.lock.acquire()
                    if self.maintain_aspect_ratio:
                        self.frame = imutils.resize(frame, width=self.screen_width)
                    else:
                        self.frame = cv2.resize(frame, (self.screen_width, self.screen_height))
                    self.img = QtGui.QImage(self.frame, self.frame.shape[1], self.frame.shape[0], QtGui.QImage.Format_RGB888).rgbSwapped()
                    self.pix = QtGui.QPixmap.fromImage(self.img)
                self.lock.release()

    def set_frame(self):
        """Sets pixmap image to video frame"""

        try:
            self.video_frame.setPixmap(self.pix)
        # No frame yet so can't set image
        except AttributeError:
            pass

    def get_video_window_layout(self):
        return self.layout
    
def exit_application():
    """Exit program event handler"""
    exit(1)

if __name__ == '__main__':

    # Create main application window
    app = QtGui.QApplication([])
    app.setStyleSheet(load_CSS(1))
    app.setStyle(QtGui.QStyleFactory.create("Cleanlooks"))
    mw = QtGui.QMainWindow()
    mw.setWindowTitle('Camera GUI')
    mw.setWindowFlags(QtCore.Qt.FramelessWindowHint)

    cw = QtGui.QWidget()
    ml = QtGui.QGridLayout()
    cw.setLayout(ml)
    mw.setCentralWidget(cw)
    mw.showMaximized()

    screen_width = QtGui.QApplication.desktop().screenGeometry().width()
    screen_height = QtGui.QApplication.desktop().screenGeometry().height()
    
    # Create Video Window Widget
    parking_lot  = VideoWindowWidget(screen_width, screen_height/2, False, 43)
    bottom_left = VideoWindowWidget(screen_width/3, screen_height/2, False, 47)
    bottom_middle = VideoWindowWidget(screen_width/3, screen_height/2, False, 44)
    bottom_right = VideoWindowWidget(screen_width/3, screen_height/2, False, 41)

    QtGui.QShortcut(QtGui.QKeySequence('Ctrl+Q'), mw, exit_application)

    ml.addLayout(parking_lot.get_video_window_layout(),0,0,1,3)
    ml.addLayout(bottom_left.get_video_window_layout(),1,0,1,1)
    ml.addLayout(bottom_middle.get_video_window_layout(),1,1,1,1)
    ml.addLayout(bottom_right.get_video_window_layout(),1,2,1,1)

    mw.show()

    if(sys.flags.interactive != 1) or not hasattr(QtCore, 'PYQT_VERSION'):
        QtGui.QApplication.instance().exec_()

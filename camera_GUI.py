from PyQt4 import QtCore, QtGui
from utility import ConvertImageBase64, video_placeholder_image
from threading import Thread
from load_CSS import load_CSS
from collections import deque
from datetime import datetime
from Queue import Queue
import time
import sys
import cv2
import imutils

class CameraSettingPopUpWidget(QtGui.QWidget):
    """Popup to select new camera"""

    def __init__(self, window_title, queue, parent=None):
        super(CameraSettingPopUpWidget, self).__init__(parent)
        self.queue = queue
        self.camera_number_table = {'Driveway': 47,
                                    'Lot UUXO': 40,
                                    'Back Young': 44,
                                    'Back King': 42,
                                    'Parking Lot': 43,
                                    'Front Young': 46,
                                    'Front King': 41}
        self.POPUP_WIDTH = 300
        self.POPUP_HEIGHT = 225
        self.setFixedSize(self.POPUP_WIDTH, self.POPUP_HEIGHT)
        self.setWindowTitle(window_title)
        self.setWindowModality(QtCore.Qt.ApplicationModal)

        self.layout = QtGui.QGridLayout()

        self.parking_lot_button = QtGui.QPushButton('Parking Lot')
        self.driveway_button = QtGui.QPushButton('Driveway')
        self.lot_UUXO_button = QtGui.QPushButton('Lot UUXO')
        self.back_young_button = QtGui.QPushButton('Back Young')
        self.back_king_button = QtGui.QPushButton('Back King')
        self.front_young_button = QtGui.QPushButton('Front Young')
        self.front_king_button = QtGui.QPushButton('Front King')

        self.parking_lot_button.clicked.connect(self.select_camera)
        self.driveway_button.clicked.connect(self.select_camera)
        self.lot_UUXO_button.clicked.connect(self.select_camera)
        self.back_young_button.clicked.connect(self.select_camera)
        self.back_king_button.clicked.connect(self.select_camera)
        self.front_young_button.clicked.connect(self.select_camera)
        self.front_king_button.clicked.connect(self.select_camera)

        self.layout.addWidget(self.parking_lot_button)
        self.layout.addWidget(self.driveway_button)
        self.layout.addWidget(self.lot_UUXO_button)
        self.layout.addWidget(self.back_young_button)
        self.layout.addWidget(self.back_king_button)
        self.layout.addWidget(self.front_young_button)
        self.layout.addWidget(self.front_king_button)

        self.setLayout(self.layout)
        self.show()

    def select_camera(self):
        """Returns selected camera number to main program"""

        camera_number = str(self.camera_number_table[str(self.sender().text())])
        self.queue.put(camera_number)
        self.close()

class CameraWidget(QtGui.QWidget):
    def __init__(self, width, height, aspect_ratio, default_camera_number, parent=None, deque_size=1):
        super(CameraWidget, self).__init__(parent)

        # Initialize deque used to store frames read from the stream
        self.deque = deque(maxlen=deque_size)

        # Initialize queue used for returning camera number when switching camera feeds
        self.camera_settings_queue = Queue()

        self.screen_width = width
        self.screen_height = height
        self.maintain_aspect_ratio = aspect_ratio
        self.online = False
        self.capture = None
        self.update_camera_stream_link(default_camera_number)

        self.video_frame = QtGui.QLabel()
        self.video_frame.mousePressEvent = self.change_network_stream

        self.layout = QtGui.QGridLayout()
        self.layout.addWidget(self.video_frame,0,0)

        self.init_placeholder_image()

        self.load_network_stream()
        self.get_frame_thread = Thread(target=self.get_frame, args=())
        self.get_frame_thread.daemon = True
        self.get_frame_thread.start()
        self.timer = QtCore.QTimer()
        self.timer.timeout.connect(self.set_frame)
        self.timer.start(1)

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

    def update_camera_stream_link(self, camera_number):
        """Assign new camera stream link"""

        self.camera_number = camera_number
        self.camera_stream_link = 'rtsp://admin:sagnac808@192.168.1.{}:554/cam/realmonitor?channel=1&subtype=0'.format(self.camera_number)

        print(self.camera_stream_link)

    def load_network_stream(self):
        """Verifies new stream link and open new stream if valid"""

        def load_network_stream_thread():
            if self.verify_network_stream(self.camera_stream_link):
                self.capture = cv2.VideoCapture(self.camera_stream_link)
                self.online = True
        self.load_stream_thread = Thread(target=load_network_stream_thread, args=())
        self.load_stream_thread.daemon = True
        self.load_stream_thread.start()

    def change_network_stream(self, event):
        """Opens popup dialog to enter IP network stream"""

        self.popup = CameraSettingPopUpWidget("Choose Camera", self.camera_settings_queue)
        while not self.popup.visibleRegion().isEmpty():
            self.spin(.1)

        if self.camera_settings_queue.qsize() > 0:
            self.update_camera_stream_link(self.camera_settings_queue.get())
            self.load_network_stream()
            
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
            try:
                if self.capture.isOpened() and self.online:
                    # Read next frame from stream and insert into deque
                    status, frame = self.capture.read()
                    if status:
                        self.deque.append(frame)
                    else:
                        self.capture.release()
                        self.online = False
                else:
                    # Attempt to reconnect
                    print('attempting to reconnect', self.camera_number)
                    self.load_network_stream()
                    self.spin(2)
                self.spin(.001)
            except AttributeError:
                pass

    def spin(self, seconds):
        """Pause for set amount of seconds, replaces time.sleep so program doesnt stall"""

        time_end = time.time() + seconds
        while time.time() < time_end:
            QtGui.QApplication.processEvents()

    def set_frame(self):
        """Sets pixmap image to video frame"""

        if not self.online:
            self.video_frame.setPixmap(self.placeholder_image)
            self.spin(1)
            return

        if self.deque and self.online:
            # Grab latest frame
            frame = self.deque[-1]

            # Keep frame aspect ratio
            if self.maintain_aspect_ratio:
                self.frame = imutils.resize(frame, width=self.screen_width)
            # Force resize
            else:
                self.frame = cv2.resize(frame, (self.screen_width, self.screen_height))

            # Add timestamp to parking lot camera
            if self.camera_number == 43:
                cv2.rectangle(self.frame, (self.screen_width-190,0), (self.screen_width,50), color=(0,0,0), thickness=-1)
                cv2.putText(self.frame, datetime.now().strftime('%H:%M:%S'), (self.screen_width-185,37), cv2.FONT_HERSHEY_SIMPLEX, 1.2, (255,255,255), lineType=cv2.LINE_AA)

            # Convert to pixmap and set to video frame
            self.img = QtGui.QImage(self.frame, self.frame.shape[1], self.frame.shape[0], QtGui.QImage.Format_RGB888).rgbSwapped()
            self.pix = QtGui.QPixmap.fromImage(self.img)
            self.video_frame.setPixmap(self.pix)

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
    parking_lot  = CameraWidget(screen_width, screen_height/2, False, 43)
    bottom_left = CameraWidget(screen_width/3, screen_height/2, False, 47)
    bottom_middle = CameraWidget(screen_width/3, screen_height/2, False, 44)
    bottom_right = CameraWidget(screen_width/3, screen_height/2, False, 41)

    QtGui.QShortcut(QtGui.QKeySequence('Ctrl+Q'), mw, exit_application)

    ml.addLayout(parking_lot.get_video_window_layout(),0,0,1,3)
    ml.addLayout(bottom_left.get_video_window_layout(),1,0,1,1)
    ml.addLayout(bottom_middle.get_video_window_layout(),1,1,1,1)
    ml.addLayout(bottom_right.get_video_window_layout(),1,2,1,1)

    mw.show()

    if(sys.flags.interactive != 1) or not hasattr(QtCore, 'PYQT_VERSION'):
        QtGui.QApplication.instance().exec_()

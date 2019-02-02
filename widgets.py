from PyQt4 import QtCore, QtGui
import imutils
import pyqtgraph as pg
import random
import zmq
import numpy as np
import sys
import time
from threading import Thread
import cv2

"""Modular widget classes 

ZMQPlotWidget: Scrolling plot with data input from ZMQ socket
RotationalControllerPlotWidget: Scrolling plot with data input from ZMQ socket
PlotColorWidget: Changes plot color
CrosshairPlotWidget: Scrolling plot with crosshair
VideoStreamWidget: Video player capable of loading in media and opening network streams
    VideoWindowWidget: Main container for video frame
    OverlayWidget: Invisible overlay container on top of video frame
    CrosshairWidget: Invisbile plot with crosshair on top of overlay
"""

class ZMQPlotWidget(QtGui.QWidget):
    """Plot with fixed data moving right to left

    Adjustable fixed x-axis, dynamic y-axis, data does not shrink
    """

    def __init__(self, ZMQ_address, ZMQ_topic, ZMQ_frequency, parent=None):
        super(ZMQPlotWidget, self).__init__(parent)
        
        self.verified = False
        # FREQUENCY HAS TO BE SAME AS SERVER'S FREQUENCY
        # USE FOR TIME.SLEEP (s)
        # self.ZMQ_FREQUENCY = 1 / Desired Frequency (Hz)
        self.ZMQ_FREQUENCY = ZMQ_frequency

        # Screen refresh rate to update plot (ms)
        # USE FOR TIMER.TIMER (ms)
        # self.ZMQ_PLOT_REFRESH_RATE = 1 / Desired Frequency (Hz) * 1000
        self.ZMQ_PLOT_REFRESH_RATE = 7

        self.DATA_TIMEOUT = 1

        # Set X Axis range. If desired is [-10,0] then set LEFT_X = -10 and RIGHT_X = 0
        self.ZMQ_LEFT_X = -10
        self.ZMQ_RIGHT_X = 0
        self.ZMQ_x_axis = np.arange(self.ZMQ_LEFT_X, self.ZMQ_RIGHT_X, self.ZMQ_FREQUENCY)
        self.ZMQ_buffer_size = int((abs(self.ZMQ_LEFT_X) + abs(self.ZMQ_RIGHT_X))/self.ZMQ_FREQUENCY)

        self.ZMQ_data = [] 
        
        # Create ZMQ Plot Widget
        self.ZMQ_plot_widget = pg.PlotWidget()
        self.ZMQ_plot_widget.plotItem.setMouseEnabled(x=False, y=False)
        self.ZMQ_plot_widget.setXRange(self.ZMQ_LEFT_X, self.ZMQ_RIGHT_X)
        self.ZMQ_plot_widget.setTitle('ZMQ Plot')
        self.ZMQ_plot_widget.setLabel('left', 'Value')
        self.ZMQ_plot_widget.setLabel('bottom', 'Time (s)')

        self.ZMQ_plot = self.ZMQ_plot_widget.plot()
        self.ZMQ_plot.setPen(32,201,151)
        
        self.layout = QtGui.QGridLayout()
        self.layout.addWidget(self.ZMQ_plot_widget)
        
        # Setup socket port and topic using pub/sub system
        self.ZMQ_TCP_address = ZMQ_address
        self.ZMQ_topic = ZMQ_topic

        self.initial_check_valid_port()
        self.start()
        
    def initial_check_valid_port(self):
        """Attempts to establish initial ZMQ socket connection"""

        try:
            context = zmq.Context()
            socket = context.socket(zmq.SUB)
            socket.connect(self.ZMQ_TCP_address)
            socket.setsockopt(zmq.SUBSCRIBE, self.ZMQ_topic)
            # Check for valid data within time interval in seconds (s)
            time_end = time.time() + self.DATA_TIMEOUT
            while time.time() < time_end:
                try:
                    topic, data = socket.recv(zmq.NOBLOCK).split()
                    self.update_ZMQ_plot_address(self.ZMQ_TCP_address, self.ZMQ_topic)
                    self.verified = True
                    return
                except zmq.ZMQError, e:
                    # No data arrived
                    if e.errno == zmq.EAGAIN:
                        pass
        # Invalid argument
        except zmq.ZMQError, e:
            self.verified = False

    def update_ZMQ_plot_address(self, address, topic):
        """Sets ZMQ socket connection with given address and topic"""

        self.ZMQ_TCP_address = address 
        self.ZMQ_topic = topic
        self.ZMQ_context = zmq.Context()
        self.ZMQ_socket = self.ZMQ_context.socket(zmq.SUB)
        self.ZMQ_socket.connect(self.ZMQ_TCP_address)
        self.ZMQ_socket.setsockopt(zmq.SUBSCRIBE, self.ZMQ_topic)
        
    def ZMQ_plot_updater(self):
        """Reads position value from device and updates plot buffer"""

        if self.verified:
            while(True):
                # Read data from buffer until empty
                try:
                    self.topic, self.ZMQ_data_point = self.ZMQ_socket.recv(zmq.NOBLOCK).split()
                    if len(self.ZMQ_data) >= self.ZMQ_buffer_size:
                        self.ZMQ_data.pop(0)
                    self.ZMQ_data.append(float(self.ZMQ_data_point))
                # No data arrived, buffer empty
                except zmq.ZMQError, e:
                    if e.errno == zmq.EAGAIN:
                        self.ZMQ_plot.setData(self.ZMQ_x_axis[len(self.ZMQ_x_axis) - len(self.ZMQ_data):], self.ZMQ_data)
                    break

    def clear_ZMQ_plot(self):
        self.ZMQ_data = []

    def change_plot_color(self, color):
        self.ZMQ_plot.setPen(color)
    
    def get_ZMQ_plot_address(self):
        return self.ZMQ_TCP_address

    def get_ZMQ_topic(self):
        return self.ZMQ_topic
    
    def get_ZMQ_plot_widget(self):
        return self.ZMQ_plot_widget

    # Version with QTimer (ms)
    def get_ZMQ_plot_refresh_rate(self):
        return self.ZMQ_PLOT_REFRESH_RATE

    # Version with time.sleep (s) 
    def get_ZMQ_frequency(self):
        return self.ZMQ_FREQUENCY

    def get_ZMQ_plot_layout(self):
        return self.layout

    def get_verified(self):
        return self.verified

    def set_verified(self, value):
        self.verified = value

    def start(self):
        self.ZMQ_plot_timer = QtCore.QTimer()
        self.ZMQ_plot_timer.timeout.connect(self.ZMQ_plot_updater)
        self.ZMQ_plot_timer.start(self.get_ZMQ_plot_refresh_rate())

class RotationalControllerPlotWidget(QtGui.QWidget):
    """Plot with fixed data moving right to left

    Adjustable fixed x-axis, dynamic y-axis, data does not shrink
    """

    def __init__(self, position_address, position_topic, position_frequency, parameter_address, parent=None):
        super(RotationalControllerPlotWidget, self).__init__(parent)
        
        self.DATA_TIMEOUT = 1
        self.position_verified = False
        self.parameter_verified = False
        # FREQUENCY HAS TO BE SAME AS SERVER'S FREQUENCY
        # USE FOR TIME.SLEEP (s)
        # self.FREQUENCY = 1 / Desired Frequency (Hz)
        self.FREQUENCY = position_frequency

        # Screen refresh rate to update plot (ms)
        # USE FOR TIMER.TIMER (ms)
        # self.ROTATIONAL_CONTROLLER_PLOT_REFRESH_RATE = 1 / Desired Frequency (Hz) * 1000
        self.ROTATIONAL_CONTROLLER_PLOT_REFRESH_RATE = 7

        # Set X Axis range. If desired is [-10,0] then set LEFT_X = -10 and RIGHT_X = 0
        self.LEFT_X = -10
        self.RIGHT_X = 0
        self.x_axis = np.arange(self.LEFT_X, self.RIGHT_X, self.FREQUENCY)
        self.buffer = int((abs(self.LEFT_X) + abs(self.RIGHT_X))/self.FREQUENCY)
        self.data = [] 

        # Create Plot Widget 
        self.rotational_plot_widget = pg.PlotWidget()
        self.rotational_plot_widget.plotItem.setMouseEnabled(x=False, y=False)
        self.rotational_plot_widget.setXRange(self.LEFT_X, self.RIGHT_X)
        self.rotational_plot_widget.setTitle('Rotational Controller Position')
        self.rotational_plot_widget.setLabel('left', 'Value')
        self.rotational_plot_widget.setLabel('bottom', 'Time (s)')

        self.rotational_plot = self.rotational_plot_widget.plot()
        self.rotational_plot.setPen(232,234,246)

        self.layout = QtGui.QGridLayout()
        self.layout.addWidget(self.rotational_plot_widget)

        self.position_address = position_address
        self.position_topic = position_topic
        self.parameter_address = parameter_address

        self.initial_check_valid_position_port()
        self.initial_check_valid_parameter_port()
        self.start()

    def initial_check_valid_position_port(self):
        """Attempts to establish ZMQ connection with initial position port settings"""

        try:
            context = zmq.Context()
            socket = context.socket(zmq.SUB)
            socket.connect(self.position_address)
            socket.setsockopt(zmq.SUBSCRIBE, self.position_topic)
            # Check for valid data within time interval in seconds (s)
            time_end = time.time() + self.DATA_TIMEOUT
            while time.time() < time_end:
                try:
                    topic, data = socket.recv(zmq.NOBLOCK).split()
                    self.update_position_plot_address(self.position_address, self.position_topic)
                    self.position_verified = True
                    return
                except zmq.ZMQError, e:
                    # No data arrived
                    if e.errno == zmq.EAGAIN:
                        pass
        # Invalid argument
        except zmq.ZMQError, e:
            self.position_verified = False

    def initial_check_valid_parameter_port(self):
        """Attempts to establish ZMQ connection with initial parameter port settings"""

        try:
            context = zmq.Context()
            socket = context.socket(zmq.REQ)
            # Prevent program from hanging after closing
            socket.setsockopt(zmq.LINGER, 0)
            socket.connect(self.parameter_address)
            socket.send("info?")
            # Check for valid data within time interval in seconds (s)
            time_end = time.time() + self.DATA_TIMEOUT
            while time.time() < time_end:
                try:
                    parameter_information = [x.strip() for x in socket.recv(zmq.NOBLOCK).split(',')]
                    self.velocity_min, self.velocity_max, self.acceleration_min, self.acceleration_max, self.position_min, self.position_max, self.home_flag, self.units = parameter_information
                    self.update_parameter_plot_address(self.parameter_address)
                    self.parameter_verified = True
                    return
                except zmq.ZMQError, e:
                    # No data arrived
                    if e.errno == zmq.EAGAIN:
                        pass
        # Invalid argument
        except zmq.ZMQError, e:
            self.parameter_verified = False

    def update_position_plot_address(self, address, topic): 
        """Establishes ZMQ connection with given port settings"""
        
        self.position_address = address
        self.position_topic = topic
        self.position_context = zmq.Context()
        self.position_socket = self.position_context.socket(zmq.SUB)
        self.position_socket.connect(self.position_address)
        self.position_socket.setsockopt(zmq.SUBSCRIBE, self.position_topic)
        return (self.position_context, self.position_socket, self.position_topic)

    def update_parameter_plot_address(self, address): 
        """Establishes ZMQ connection with given port settings"""

        self.parameter_address = address
        self.parameter_context = zmq.Context()
        self.parameter_socket = self.parameter_context.socket(zmq.REQ)
        # Prevent program from hanging after closing
        self.parameter_socket.setsockopt(zmq.LINGER, 0)
        self.parameter_socket.connect(self.parameter_address)
        self.parameter_socket.send('info?')
        parameter_information = [x.strip() for x in self.parameter_socket.recv().split(',')]
        self.velocity_min, self.velocity_max, self.acceleration_min, self.acceleration_max, self.position_min, self.position_max, self.home_flag, self.units = parameter_information
        return (self.parameter_context, self.parameter_socket)

    def start(self):
        """Initiates timer to update plot"""

        self.position_update_timer = QtCore.QTimer()
        self.position_update_timer.timeout.connect(self.rotational_controller_plot_updater)
        self.position_update_timer.start(self.get_rotational_controller_plot_refresh_rate())

    def rotational_controller_plot_updater(self):
        """Read position from device socket and updates data buffer with current position value"""
        
        if self.position_verified:
            while(True):
                # Read data from buffer until empty
                try:
                    topic, self.current_position_value = self.position_socket.recv(zmq.NOBLOCK).split()
                    # Change to 0 since Rotational controller reports 0 as -0
                    if self.current_position_value == '-0.00':
                        self.current_position_value = '0.00'
                    if len(self.data) >= self.buffer:
                        self.data.pop(0)
                    self.data.append(float(self.current_position_value))
                # No data arrived, buffer empty
                except zmq.ZMQError, e:
                    if e.errno == zmq.EAGAIN:
                        self.rotational_plot.setData(self.x_axis[len(self.x_axis) - len(self.data):], self.data)
                    break

    def clear_rotational_controller_plot(self):
        self.data = []

    def change_plot_color(self, color):
        self.rotational_plot.setPen(color)

    def get_parameter_socket(self):
        if self.parameter_verified:
            return self.parameter_socket
        else: 
            return None

    def get_position_socket(self):
        if self.position_verified:
            return self.position_socket
        else:
            return None

    def get_rotational_controller_frequency(self):
        return self.FREQUENCY
    
    def get_rotational_controller_plot_refresh_rate(self):
        return self.ROTATIONAL_CONTROLLER_PLOT_REFRESH_RATE

    def get_rotational_controller_layout(self):
        return self.layout

    def get_rotational_controller_plot_widget(self):
        return self.rotational_plot_widget

    def get_parameter_information(self):
        return (self.velocity_min, self.velocity_max, self.acceleration_min, self.acceleration_max, self.position_min, self.position_max, self.home_flag, self.units)

    def get_current_position_value(self):
        try:
            return self.current_position_value
        except AttributeError:
            return 0

    def get_position_verified(self):
        return self.position_verified

    def get_parameter_verified(self):
        return self.parameter_verified

    def set_position_verified(self, value):
        self.position_verified = value

    def set_parameter_verified(self, value):
        self.parameter_verified = value

    def get_position_topic(self):
        return self.position_topic

class PlotColorWidget(QtGui.QColorDialog):
    """Opens color palette to change plot color"""

    def __init__(self, plot_object, parent=None):
        super(PlotColorWidget, self).__init__(parent)
        # Opens color palette selector
        self.palette = self.getColor()
        self.color = str(self.palette.name())
        if self.color != '#000000':
            plot_object.change_plot_color(self.color)

class CrosshairPlotWidget(QtGui.QWidget):
    """Scrolling plot with crosshair"""

    def __init__(self, parent=None):
        super(CrosshairPlotWidget, self).__init__(parent)
        
        # Use for time.sleep (s)
        self.FREQUENCY = .025
        # Use for timer.timer (ms)
        self.TIMER_FREQUENCY = self.FREQUENCY * 1000

        self.LEFT_X = -10
        self.RIGHT_X = 0
        self.x_axis = np.arange(self.LEFT_X, self.RIGHT_X, self.FREQUENCY)
        self.buffer = int((abs(self.LEFT_X) + abs(self.RIGHT_X))/self.FREQUENCY)
        self.data = []
        
        self.crosshair_plot_widget = pg.PlotWidget()
        self.crosshair_plot_widget.setXRange(self.LEFT_X, self.RIGHT_X)
        self.crosshair_plot_widget.setLabel('left', 'Value')
        self.crosshair_plot_widget.setLabel('bottom', 'Time (s)')
        self.crosshair_color = (196,220,255)

        self.crosshair_plot = self.crosshair_plot_widget.plot()

        self.layout = QtGui.QGridLayout()
        self.layout.addWidget(self.crosshair_plot_widget)
        
        self.crosshair_plot_widget.plotItem.setAutoVisible(y=True)
        self.vertical_line = pg.InfiniteLine(angle=90)
        self.horizontal_line = pg.InfiniteLine(angle=0, movable=False)
        self.vertical_line.setPen(self.crosshair_color)
        self.horizontal_line.setPen(self.crosshair_color)
        self.crosshair_plot_widget.setAutoVisible(y=True)
        self.crosshair_plot_widget.addItem(self.vertical_line, ignoreBounds=True)
        self.crosshair_plot_widget.addItem(self.horizontal_line, ignoreBounds=True)
        
        self.crosshair_update = pg.SignalProxy(self.crosshair_plot_widget.scene().sigMouseMoved, rateLimit=60, slot=self.update_crosshair)

        self.start()

    def plot_updater(self):
        """Updates data buffer with data value"""

        self.data_point = random.randint(1,101)
        if len(self.data) >= self.buffer:
            self.data.pop(0)
        self.data.append(float(self.data_point))
        self.crosshair_plot.setData(self.x_axis[len(self.x_axis) - len(self.data):], self.data)

    def update_crosshair(self, event):
        """Paint crosshair on mouse"""

        coordinates = event[0]  
        if self.crosshair_plot_widget.sceneBoundingRect().contains(coordinates):
            mouse_point = self.crosshair_plot_widget.plotItem.vb.mapSceneToView(coordinates)
            index = mouse_point.x()
            if index > self.LEFT_X and index <= self.RIGHT_X:
                self.crosshair_plot_widget.setTitle("<span style='font-size: 12pt'>x=%0.1f,   <span style='color: red'>y=%0.1f</span>" % (mouse_point.x(), mouse_point.y()))
            self.vertical_line.setPos(mouse_point.x())
            self.horizontal_line.setPos(mouse_point.y())

    def start(self):
        self.timer = QtCore.QTimer()
        self.timer.timeout.connect(self.plot_updater)
        self.timer.start(self.get_timer_frequency())

    def get_crosshair_plot_layout(self):
        return self.layout

    def get_timer_frequency(self):
        return self.TIMER_FREQUENCY

class VideoWindowWidget(QtGui.QWidget):
    """Video Window widget with crosshair enable/disable"""

    def __init__(self, parent=None):
        super(VideoWindowWidget, self).__init__(parent)

        self.capture = None
        self.video_file_name = None
        self.is_video_file_or_stream_loaded = False
        self.pause = True
        self.MIN_WINDOW_WIDTH = 600
        self.MIN_WINDOW_HEIGHT = 600
        
        # Overlay and plot difference so translate by offset
        self.OFFSET = 9
        self.placeholder_image_file = 'doc/placeholder5.PNG'
        self.video_filter_formats = self.tr("Video files(*.mp4 *.gif *.mov *.flv *.avi *.wmv)")

        self.FREQUENCY = .002
        self.TIMER_FREQUENCY = self.FREQUENCY * 1000
        
        # Ensure video frame is created before overlay
        # since overlay with invisible crosshair plot is place above
        self.video_frame = QtGui.QLabel()
        
        self.layout = QtGui.QGridLayout()
        self.layout.addWidget(self.video_frame,0,0)

        self.init_placeholder_image()
        self.setLayout(self.layout)
        self.crosshair_overlay = OverlayWidget(self)
        self.display_crosshair = True

        self.timer = QtCore.QTimer()
        self.timer.timeout.connect(self.set_frame)
        self.get_frame_thread = Thread(target=self.get_frame, args=())
        self.get_frame_thread.daemon = True
        self.get_frame_thread.start()
        self.start_capture()

    def init_placeholder_image(self):
        """Set placeholder image when video is stopped"""

        self.placeholder_image = cv2.imread(self.placeholder_image_file)
        
        # Maintain aspect ratio
        #self.placeholder_image = imutils.resize(self.placeholder_image, width=self.MIN_WINDOW_WIDTH)
        self.placeholder_image = cv2.resize(self.placeholder_image, (self.MIN_WINDOW_WIDTH, self.MIN_WINDOW_HEIGHT))

        self.placeholder = QtGui.QImage(self.placeholder_image, self.placeholder_image.shape[1], self.placeholder_image.shape[0], QtGui.QImage.Format_RGB888).rgbSwapped()
        self.placeholder_image = QtGui.QPixmap.fromImage(self.placeholder)
        self.video_frame.setPixmap(self.placeholder_image)

    def align_crosshair(self):
        """Align crosshair with new loaded frame dimension"""

        capture = cv2.VideoCapture(str(self.video_file_name))
        status, frame = capture.read()
        frame = imutils.resize(frame, width=self.MIN_WINDOW_WIDTH)
        self.resized_image_height = frame.shape[0]
        frame_height = self.size().height()
        self.translate = (frame_height - self.resized_image_height - (2 * self.OFFSET))/2
    
    def start_capture(self):
        self.pause = False
        self.timer.start(self.TIMER_FREQUENCY)

    def pause_capture(self):
        if not self.pause:
            self.pause = True
            self.timer.stop()

    def stop_capture(self):
        self.pause_capture()
        self.capture = cv2.VideoCapture(str(self.video_file_name))

    def load_video_file(self):
        """Open file explorer to select media file"""

        self.video_file_name = QtGui.QFileDialog.getOpenFileName(self, 'Select .h264 Video File', '', self.video_filter_formats)
        if self.video_file_name:
            self.is_video_file_or_stream_loaded = True
            self.pause = False
            self.capture = cv2.VideoCapture(str(self.video_file_name))
            self.align_crosshair()

    def open_network_stream(self):
        """Opens popup dialog to enter IP network stream"""

        text, pressed_status = QtGui.QInputDialog.getText(self, "Open Media", "Please enter a network URL:")
        link = str(text)
        if pressed_status and self.verify_network_stream(link):
            self.is_video_file_or_stream_loaded = True
            self.pause = False
            self.video_file_name = link
            self.capture = cv2.VideoCapture(link)
            self.align_crosshair()
            
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
            # No frame in buffer so skip
            except AttributeError:
                pass
            time.sleep(self.FREQUENCY)

    def set_frame(self):
        """Sets pixmap image to video frame"""

        try:
            self.video_frame.setPixmap(self.pix)
        # No frame in buffer so skip
        except AttributeError:
            pass

    def get_video_window_layout(self):
        return self.layout
    
    def show_crosshair(self):
        self.display_crosshair = True
        self.crosshair_overlay.show()

    def hide_crosshair(self):
        self.display_crosshair = False 
        self.crosshair_overlay.hide()

    def resizeEvent(self, event):
        """GUI auto redraws environment"""

        self.crosshair_overlay.resize(event.size())
        event.accept()
    
    def mousePressEvent(self, QMouseEvent):
        """Automatically handles mouseclick input"""

        if self.is_video_file_or_stream_loaded and self.display_crosshair:
            self.x = self.crosshair_overlay.get_x() 
            self.y = self.crosshair_overlay.get_y() - self.translate
            
            if self.x > 0 and self.x < self.MIN_WINDOW_WIDTH and self.y > 0 and self.y < self.resized_image_height:
                c = self.img.pixel(self.x,self.y)
                print(QtGui.QColor(c).getRgb())
                self.crosshair_overlay.set_update_dot_flag(True)
                # Calling update automatically calls paintEvent()
                self.update()

class VideoStreamWidget(QtGui.QWidget):
    """Widget capable of streaming video with RBG detection crosshair"""

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

    def show_crosshair(self):
        self.video_window.show_crosshair()

    def hide_crosshair(self):
        self.video_window.hide_crosshair()
    
class CrosshairWidget(QtGui.QWidget):
    """Widget to draw crosshair on the screen
    
    Draws an invisible plot with a visible crosshair
    """

    def __init__(self, parent=None):
        super(CrosshairWidget, self).__init__(parent)
        
        # Create the invisible plot
        self.crosshair_plot = pg.PlotWidget()
        self.crosshair_plot.setBackground(background=None)

        self.crosshair_plot.plotItem.hideAxis('bottom') 
        self.crosshair_plot.plotItem.hideAxis('left') 
        self.crosshair_plot.plotItem.hideAxis('right') 
        self.crosshair_plot.plotItem.hideAxis('top')
        self.crosshair_plot.plotItem.setMouseEnabled(x=False, y=False)

        self.crosshair_color = (196,220,255)

        self.layout = QtGui.QGridLayout()
        self.layout.addWidget(self.crosshair_plot)
       
        # Create the crosshair 
        self.crosshair_plot.plotItem.setAutoVisible(y=True)
        self.vertical_line = pg.InfiniteLine(angle=90)
        self.horizontal_line = pg.InfiniteLine(angle=0, movable=False)
        self.vertical_line.setPen(self.crosshair_color)
        self.horizontal_line.setPen(self.crosshair_color)
        self.crosshair_plot.setAutoVisible(y=True)
        self.crosshair_plot.addItem(self.vertical_line, ignoreBounds=True)
        self.crosshair_plot.addItem(self.horizontal_line, ignoreBounds=True)
        
        # Update crosshair
        self.crosshair_update = pg.SignalProxy(self.crosshair_plot.scene().sigMouseMoved, rateLimit=1500, slot=self.update_crosshair)

    def update_crosshair(self, event):
        """Obtains mouse coordinates and moves crosshair"""

        self.coordinates = event[0]  
        self.x = self.coordinates.x()
        self.y = self.coordinates.y()
        if self.crosshair_plot.sceneBoundingRect().contains(self.coordinates):
            self.mouse_point = self.crosshair_plot.plotItem.vb.mapSceneToView(self.coordinates)
            self.vertical_line.setPos(self.mouse_point.x())
            self.horizontal_line.setPos(self.mouse_point.y())

    def get_crosshair_layout(self):
        return self.layout

    def get_x(self):
        return self.x

    def get_y(self):
        return self.y
    
class OverlayWidget(QtGui.QWidget):
    """Creates a overlay platform to place widgets on
    
    Overlay is placed on the video frame which allows the crosshair to 
    freely move
    """

    def __init__(self, parent):
        super(OverlayWidget, self).__init__(parent)

        # Make any widgets in the container have a transparent background
        self.palette = QtGui.QPalette(self.palette())
        self.palette.setColor(self.palette.Background, QtCore.Qt.transparent)
        self.setPalette(self.palette)
        self.CROSSHAIR_OFFSET = 9
       
        self.setWindowFlags(QtCore.Qt.WindowStaysOnTopHint)
        self.crosshair = CrosshairWidget()
        self.painter = QtGui.QPainter()
        self.update_dot_flag = False
        self.crosshair_pen = QtGui.QPen(QtCore.Qt.green, 1.5)
        
        # Set initial dot outside paint window
        # Top left is (0,0)
        self.DOT_X = -100
        self.DOT_Y = -100

        # Crosshair distance from dot and length of each side
        self.CROSSHAIR_LENGTH = 7
        self.CROSSHAIR_DIFFERENCE = 5

        self.layout = QtGui.QGridLayout()
        self.layout.addLayout(self.crosshair.get_crosshair_layout(),1,0)
        self.setLayout(self.layout)
    
    def paintEvent(self, event):
        """Screen is automatically refreshed on mouse movement or frame change"""
    
        # Make overlay transparent but keep widgets
        self.painter.begin(self)
        self.painter.setRenderHint(QtGui.QPainter.Antialiasing)
        # Transparency settings for overlay (r,g,b,a)
        self.painter.fillRect(event.rect(), QtGui.QBrush(QtGui.QColor(0, 0, 0, 0)))
        if self.update_dot_flag:
            self.update_dot()
            self.set_update_dot_flag(False)
        self.painter.setPen(self.crosshair_pen)
        self.draw_crosshair()
        self.painter.end()

    def draw_crosshair(self):
        """Paint the crosshair on the screen"""

        # Middle point
        self.painter.drawPoint(self.DOT_X, self.DOT_Y)
        # Top
        self.painter.drawLine(self.DOT_X, self.DOT_Y - self.CROSSHAIR_DIFFERENCE, self.DOT_X, self.DOT_Y - self.CROSSHAIR_DIFFERENCE - self.CROSSHAIR_LENGTH)
        # Right
        self.painter.drawLine(self.DOT_X + self.CROSSHAIR_DIFFERENCE, self.DOT_Y, self.DOT_X + self.CROSSHAIR_DIFFERENCE + self.CROSSHAIR_LENGTH, self.DOT_Y)
        # Bottom
        self.painter.drawLine(self.DOT_X, self.DOT_Y + self.CROSSHAIR_DIFFERENCE, self.DOT_X, self.DOT_Y + self.CROSSHAIR_DIFFERENCE + self.CROSSHAIR_LENGTH)
        # Left
        self.painter.drawLine(self.DOT_X - self.CROSSHAIR_DIFFERENCE, self.DOT_Y, self.DOT_X - self.CROSSHAIR_DIFFERENCE - self.CROSSHAIR_LENGTH, self.DOT_Y)

    def update_dot(self):
        self.DOT_X = self.get_x() + self.CROSSHAIR_OFFSET
        self.DOT_Y = self.get_y() + self.CROSSHAIR_OFFSET

    def set_update_dot_flag(self, boolean):
        self.update_dot_flag = boolean

    def get_x(self):
        return self.crosshair.get_x()

    def get_y(self):
        return self.crosshair.get_y()

class UniversalPlotWidget(QtGui.QWidget):
    def __init__(self, parent=None):
        super(UniversalPlotWidget, self).__init__(parent)
        
        self.verified = False
        self.DATA_TIMEOUT = 1
        self.SPACING = 1
        self.plot_address = 'tcp://192.168.1.143:6020'
        self.plot_topic = '20000'
        
        self.DATA_POINTS_TO_DISPLAY = 1000

        # Screen refresh rate to update plot (ms)
        # self.UNIVERSAL_PLOT_REFRESH_RATE  = 1 / Desired Frequency (Hz) * 1000
        self.UNIVERSAL_PLOT_REFRESH_RATE  = 20

        # Set X Axis range. If desired is [-10,0] then set LEFT_X = -10 and RIGHT_X = 0
        self.LEFT_X = 0
        self.RIGHT_X = self.DATA_POINTS_TO_DISPLAY
        self.x_axis = np.arange(self.LEFT_X, self.RIGHT_X, self.SPACING)
        self.buffer_size = int((abs(self.LEFT_X) + abs(self.RIGHT_X))/self.SPACING)

        # Create Universal Plot Widget
        self.universal_plot_widget = pg.PlotWidget()
        self.universal_plot_widget.plotItem.setMouseEnabled(x=False, y=False)
        self.universal_plot_widget.setXRange(self.LEFT_X, self.RIGHT_X)
        self.universal_plot_widget.setTitle('Universal Plot')
        self.universal_plot_widget.setLabel('left', 'Value')
        self.universal_plot_widget.setLabel('bottom', 'Data Points')

        self.layout = QtGui.QGridLayout()
        self.layout.addWidget(self.universal_plot_widget)

        self.initial_check_valid_port()
        self.universal_plot_timer = QtCore.QTimer()
        self.universal_plot_timer.timeout.connect(self.universal_plot_updater)
        self.universal_plot_timer.start(self.get_universal_plot_refresh_rate())
        '''
        self.get_frame_thread = Thread(target=self.read_data, args=())
        self.get_frame_thread.daemon = True
        self.get_frame_thread.start()
        '''
    
    def initial_check_valid_port(self):
        """Attempts to establish initial ZMQ socket connection"""

        try:
            context = zmq.Context()
            socket = context.socket(zmq.SUB)
            socket.connect(self.plot_address)
            socket.setsockopt(zmq.SUBSCRIBE, self.plot_topic)
            # Check for valid data within time interval in seconds (s)
            time_end = time.time() + self.DATA_TIMEOUT
            while time.time() < time_end:
                try:
                    topic, data = socket.recv(zmq.NOBLOCK).split()
                    self.update_universal_plot_address(self.plot_address, self.plot_topic)
                    self.initialize_plot()
                    self.verified = True
                    return
                except zmq.ZMQError, e:
                    # No data arrived
                    if e.errno == zmq.EAGAIN:
                        pass
        # Invalid argument
        except zmq.ZMQError, e:
            self.verified = False

    def update_universal_plot_address(self, address, topic):
        """Sets ZMQ socket connection with given address and topic"""

        self.plot_address = address 
        self.plot_topic = topic
        self.plot_context = zmq.Context()
        self.plot_socket = self.plot_context.socket(zmq.SUB)
        self.plot_socket.connect(self.plot_address)
        self.plot_socket.setsockopt(zmq.SUBSCRIBE, self.plot_topic)

    def initialize_plot(self):

        # Confirmed valid ZMQ plot settings so can use blocking recv
        topic, self.plot_data = self.plot_socket.recv().split()
        
        # Obtain header information
        self.plot_data = self.plot_data.split(',')
        print(self.plot_data[3::2][1:])
        self.traces = int(self.plot_data[0])
        self.y_scales = int(self.plot_data[1])
        self.y_axis_left = list(self.plot_data[2].split(':'))
        self.y_axis_right = list(self.plot_data[3].split(':'))

        self.data_buffers = []
        self.universal_plots = []

        self.initialize_data_buffers()
        self.create_plots()

    def initialize_data_buffers(self):
        # Initialize data buffers
        for trace in range(self.traces):
            self.data_buffers.append([])

    def create_plots(self):
        alpha = 150
        self.color_table = {0: (212,240,255, alpha),
                            1: (248,255,208, alpha),
                            2: (242,215,255, alpha),
                            3: (255,232,205, alpha),
                            4: (255,239,243, alpha),
                            5: (51,194,255, alpha),
                            6: (255,146,92, alpha),
                            7: (32,201,151, alpha),
                            8: (10,10,124, alpha),
                            9: (67,24,22, alpha)}

        # Create plots
        for trace in range(self.traces):
            new_plot = self.universal_plot_widget.plot()
            new_plot.setPen(self.color_table[trace], width=1.5)
            self.universal_plots.append(new_plot)
    
    def universal_plot_updater(self):
        """Reads data point from socket and updates plot buffers"""

        if self.verified:
            while(True):
                # Read data from buffer until empty
                try:
                    self.topic, self.plot_data = self.plot_socket.recv(zmq.NOBLOCK).split()
                    self.plot_data = self.plot_data.split(',')[3::2][1:]
                    for trace in range(self.traces):
                        if len(self.data_buffers[trace]) >= self.buffer_size:
                            self.data_buffers[trace].pop(0)
                        self.data_buffers[trace].append(float(self.plot_data[trace]))
                # No data arrived, buffer empty
                except zmq.ZMQError, e:
                    if e.errno == zmq.EAGAIN:
                        for trace in range(self.traces):
                            self.universal_plots[trace].setData(self.x_axis[len(self.x_axis) - len(self.data_buffers[trace]):], self.data_buffers[trace])
                    break

    def get_universal_plot_refresh_rate(self):
        return self.UNIVERSAL_PLOT_REFRESH_RATE

    def get_universal_plot_layout(self):
        return self.layout



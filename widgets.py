from PyQt4 import QtCore, QtGui
import pyqtgraph as pg
import random
import zmq
import numpy as np
import sys
import time
from threading import Thread
import cv2

# ==================================================================
# Plot with fixed data moving right to left
# Adjustable fixed x-axis, dynamic y-axis, data does not shrink
# ==================================================================
class ZMQPlotWidget(QtGui.QWidget):
    def __init__(self, ZMQ_address, ZMQ_topic, ZMQ_frequency, parent=None):
        super(ZMQPlotWidget, self).__init__(parent)
        
        self.verified = False
        # FREQUENCY HAS TO BE SAME AS SERVER'S FREQUENCY
        # Desired Frequency (Hz) = 1 / self.ZMQ_FREQUENCY
        # USE FOR TIME.SLEEP (s)
        self.ZMQ_FREQUENCY = ZMQ_frequency

        # Frequency to update plot (ms)
        # USE FOR TIMER.TIMER (ms)
        self.ZMQ_TIMER_FREQUENCY = self.ZMQ_FREQUENCY * 1000
        self.dataTimeout = 1

        # Set X Axis range. If desired is [-10,0] then set LEFT_X = -10 and RIGHT_X = 0
        self.ZMQ_LEFT_X = -10
        self.ZMQ_RIGHT_X = 0
        self.ZMQ_X_Axis = np.arange(self.ZMQ_LEFT_X, self.ZMQ_RIGHT_X, self.ZMQ_FREQUENCY)
        self.ZMQBuffer = int((abs(self.ZMQ_LEFT_X) + abs(self.ZMQ_RIGHT_X))/self.ZMQ_FREQUENCY)
        self.ZMQData = [] 
        self.oldZMQDataPoint = 0
        
        # Create ZMQ Plot Widget
        self.ZMQPlot = pg.PlotWidget()
        self.ZMQPlot.plotItem.setMouseEnabled(x=False, y=False)
        self.ZMQPlot.setXRange(self.ZMQ_LEFT_X, self.ZMQ_RIGHT_X)
        self.ZMQPlot.setTitle('ZMQ Plot')
        self.ZMQPlot.setLabel('left', 'Value')
        self.ZMQPlot.setLabel('bottom', 'Time (s)')

        self.ZMQPlotter = self.ZMQPlot.plot()
        self.ZMQPlotter.setPen(32,201,151)
        
        self.layout = QtGui.QGridLayout()
        self.layout.addWidget(self.ZMQPlot)
        
        # Setup socket port and topic using pub/sub system
        self.ZMQ_TCP_Port = ZMQ_address
        self.ZMQ_Topic = ZMQ_topic

        self.initialCheckValidPort()
        self.start()
        
    def initialCheckValidPort(self):
        try:
            context = zmq.Context()
            socket = context.socket(zmq.SUB)
            socket.connect(self.ZMQ_TCP_Port)
            socket.setsockopt(zmq.SUBSCRIBE, self.ZMQ_Topic)
            # Check for valid data within time interval in seconds (s)
            time_end = time.time() + self.dataTimeout
            while time.time() < time_end:
                try:
                    topic, data = socket.recv(zmq.NOBLOCK).split()
                    self.updateZMQPlotAddress(self.ZMQ_TCP_Port, self.ZMQ_Topic)
                    self.verified = True
                    return
                except zmq.ZMQError, e:
                    # No data arrived
                    if e.errno == zmq.EAGAIN:
                        pass
                    else:
                        print("real error")
        except:
            self.verified = False

    def updateZMQPlotAddress(self, address, topic):
        self.ZMQ_TCP_Port = address 
        self.ZMQ_Topic = topic
        self.ZMQContext = zmq.Context()
        self.ZMQSocket = self.ZMQContext.socket(zmq.SUB)
        self.ZMQSocket.connect(self.ZMQ_TCP_Port)
        self.ZMQSocket.setsockopt(zmq.SUBSCRIBE, self.ZMQ_Topic)
        
    def ZMQPlotUpdater(self):
        if self.verified:
            # Receives (topic, data)
            try:
                self.topic, self.ZMQDataPoint = self.ZMQSocket.recv().split()
                self.oldZMQDataPoint = self.ZMQDataPoint
            except zmq.ZMQError, e:
                # No data arrived
                if e.errno == zmq.EAGAIN:
                    self.ZMQDataPoint = self.oldZMQDataPoint

            if len(self.ZMQData) >= self.ZMQBuffer:
                self.ZMQData.pop(0)
            
            self.ZMQData.append(float(self.ZMQDataPoint))
            self.ZMQPlotter.setData(self.ZMQ_X_Axis[len(self.ZMQ_X_Axis) - len(self.ZMQData):], self.ZMQData)

    def clearZMQPlot(self):
        self.ZMQData = []

    def changePlotColor(self, color):
        self.ZMQPlotter.setPen(color)
    
    def getZMQPlotAddress(self):
        return self.ZMQ_TCP_Port

    def getZMQTopic(self):
        return self.ZMQ_Topic
    
    def getZMQPlotWidget(self):
        return self.ZMQPlot

    # Version with QTimer (ms)
    def getZMQTimerFrequency(self):
        return self.ZMQ_TIMER_FREQUENCY

    # Version with time.sleep (s) 
    def getZMQFrequency(self):
        return self.ZMQ_FREQUENCY

    def getZMQPlotLayout(self):
        return self.layout

    def getVerified(self):
        return self.verified

    def setVerified(self, value):
        self.verified = value

    def start(self):
        self.ZMQPlotTimer = QtCore.QTimer()
        self.ZMQPlotTimer.timeout.connect(self.ZMQPlotUpdater)
        self.ZMQPlotTimer.start(self.getZMQTimerFrequency())

# ==================================================================
# Plot with fixed data moving right to left
# Adjustable fixed x-axis, dynamic y-axis, data does not shrink
# ==================================================================
class RotationalControllerPlotWidget(QtGui.QWidget):
    def __init__(self, position_address, position_topic, position_frequency, parameter_address, parent=None):
        super(RotationalControllerPlotWidget, self).__init__(parent)
        
        self.dataTimeout = 1
        self.positionVerified = False
        self.parameterVerified = False
        # FREQUENCY HAS TO BE SAME AS SERVER'S FREQUENCY
        # Desired Frequency (Hz) = 1 / self.FREQUENCY
        # USE FOR TIME.SLEEP (s)
        self.FREQUENCY = position_frequency

        # Frequency to update plot (ms)
        # USE FOR TIMER.TIMER (ms)
        self.TIMER_FREQUENCY = self.FREQUENCY * 1000

        # Set X Axis range. If desired is [-10,0] then set LEFT_X = -10 and RIGHT_X = 0
        self.LEFT_X = -10
        self.RIGHT_X = 0
        self.X_Axis = np.arange(self.LEFT_X, self.RIGHT_X, self.FREQUENCY)
        self.buffer = int((abs(self.LEFT_X) + abs(self.RIGHT_X))/self.FREQUENCY)
        self.data = [] 

        # Create Plot Widget 
        self.plot = pg.PlotWidget()
        self.plot.plotItem.setMouseEnabled(x=False, y=False)
        self.plot.setXRange(self.LEFT_X, self.RIGHT_X)
        self.plot.setTitle('Rotational Controller Position')
        self.plot.setLabel('left', 'Value')
        self.plot.setLabel('bottom', 'Time (s)')

        self.plotter = self.plot.plot()
        self.plotter.setPen(232,234,246)

        self.layout = QtGui.QGridLayout()
        self.layout.addWidget(self.plot)

        self.positionAddress = position_address
        self.positionTopic = position_topic
        self.parameterAddress = parameter_address

        self.initialCheckValidPositionPort()
        self.initialCheckValidParameterPort()
        self.readPositionThread()
        self.start()

    def initialCheckValidPositionPort(self):
        try:
            context = zmq.Context()
            socket = context.socket(zmq.SUB)
            socket.connect(self.positionAddress)
            socket.setsockopt(zmq.SUBSCRIBE, self.positionTopic)
            # Check for valid data within time interval in seconds (s)
            time_end = time.time() + self.dataTimeout
            while time.time() < time_end:
                try:
                    topic, data = socket.recv(zmq.NOBLOCK).split()
                    self.updatePositionPlotAddress(self.positionAddress, self.positionTopic)
                    self.positionVerified = True
                    return
                except zmq.ZMQError, e:
                    # No data arrived
                    if e.errno == zmq.EAGAIN:
                        pass
                    else:
                        print("real error")
        except:
            self.positionVerified = False

    def initialCheckValidParameterPort(self):
        try:
            context = zmq.Context()
            socket = context.socket(zmq.REQ)
            # Prevent program from hanging after closing
            socket.setsockopt(zmq.LINGER, 0)
            socket.connect(self.parameterAddress)
            socket.send("info?")
            # Check for valid data within time interval in seconds (s)
            time_end = time.time() + self.dataTimeout
            while time.time() < time_end:
                try:
                    parameter_information = [x.strip() for x in socket.recv(zmq.NOBLOCK).split(',')]
                    self.velocityMin, self.velocityMax, self.accelerationMin, self.accelerationMax, self.positionMin, self.positionMax, self.homeFlag, self.units = parameter_information
                    self.updateParameterPlotAddress(self.parameterAddress)
                    self.parameterVerified = True
                    return
                except zmq.ZMQError, e:
                    # No data arrived
                    if e.errno == zmq.EAGAIN:
                        pass
                    else:
                        print("real error")
        except:
            self.parameterVerified = False

    def updatePositionPlotAddress(self, address, topic): 
        self.positionAddress = address
        self.positionTopic = topic
        self.positionContext = zmq.Context()
        self.positionSocket = self.positionContext.socket(zmq.SUB)
        self.positionSocket.connect(self.positionAddress)
        self.positionSocket.setsockopt(zmq.SUBSCRIBE, self.positionTopic)
        return (self.positionContext, self.positionSocket, self.positionTopic)

    def updateParameterPlotAddress(self, address): 
        self.parameterAddress = address
        self.parameterContext = zmq.Context()
        self.parameterSocket = self.parameterContext.socket(zmq.REQ)
        # Prevent program from hanging after closing
        self.parameterSocket.setsockopt(zmq.LINGER, 0)
        self.parameterSocket.connect(self.parameterAddress)
        self.parameterSocket.send('info?')
        parameter_information = [x.strip() for x in self.parameterSocket.recv().split(',')]
        self.velocityMin, self.velocityMax, self.accelerationMin, self.accelerationMax, self.positionMin, self.positionMax, self.homeFlag, self.units = parameter_information
        return (self.parameterContext, self.parameterSocket)

    def start(self):
        self.positionUpdateTimer = QtCore.QTimer()
        self.positionUpdateTimer.timeout.connect(self.plotUpdater)
        self.positionUpdateTimer.start(self.getRotationalControllerTimerFrequency())

    def readPositionThread(self):
        self.currentPositionValue = 0
        self.oldCurrentPositionValue = 0
        self.positionUpdateThread = Thread(target=self.readPosition, args=())
        self.positionUpdateThread.daemon = True
        self.positionUpdateThread.start()

    def readPosition(self):
        frequency = self.getRotationalControllerFrequency()
        while True:
            try:
                topic, self.currentPositionValue = self.positionSocket.recv().split()
                # Change to 0 since Rotational controller reports 0 as -0
                if self.currentPositionValue == '-0.00':
                    self.currentPositionValue = '0.00'
                self.oldCurrentPositionValue = self.currentPositionValue
            except:
                self.currentPositionValue = self.oldCurrentPositionValue
            time.sleep(frequency)

    def plotUpdater(self):
        if self.positionVerified:
            self.dataPoint = float(self.currentPositionValue)

            if len(self.data) >= self.buffer:
                self.data.pop(0)
            self.data.append(self.dataPoint)
            self.plotter.setData(self.X_Axis[len(self.X_Axis) - len(self.data):], self.data)

    def clearRotationalControllerPlot(self):
        self.data = []

    def changePlotColor(self, color):
        self.plotter.setPen(color)

    def getParameterSocket(self):
        if self.parameterVerified:
            return self.parameterSocket
        else: 
            return None

    def getPositionSocket(self):
        if self.positionVerified:
            return self.positionSocket
        else:
            return None

    def getRotationalControllerFrequency(self):
        return self.FREQUENCY
    
    def getRotationalControllerTimerFrequency(self):
        return self.TIMER_FREQUENCY

    def getRotationalControllerLayout(self):
        return self.layout

    def getRotationalControllerPlotWidget(self):
        return self.plot

    def getParameterInformation(self):
        return (self.velocityMin, self.velocityMax, self.accelerationMin, self.accelerationMax, self.positionMin, self.positionMax, self.homeFlag, self.units)

    def getCurrentPositionValue(self):
        return self.currentPositionValue

    def getPositionVerified(self):
        return self.positionVerified

    def getParameterVerified(self):
        return self.parameterVerified

    def setPositionVerified(self, value):
        self.positionVerified = value

    def setParameterVerified(self, value):
        self.parameterVerified = value

    def getPositionTopic(self):
        return self.positionTopic

class PlotColorWidget(QtGui.QColorDialog):
    def __init__(self, plotObject, parent=None):
        super(PlotColorWidget, self).__init__(parent)
        # Opens color palette selector
        self.palette = self.getColor()
        self.color = str(self.palette.name())
        if self.color != '#000000':
            plotObject.changePlotColor(self.color)

# ==================================================================
# Plot with crosshair
# ==================================================================
class CrosshairPlotWidget(QtGui.QWidget):
    def __init__(self, parent=None):
        super(CrosshairPlotWidget, self).__init__(parent)
        
        # Use for time.sleep (s)
        self.frequency = .025
        # Use for timer.timer (ms)
        self.timer_frequency = self.frequency * 1000

        self.left_x = -10
        self.right_x = 0
        self.x_axis = np.arange(self.left_x, self.right_x, self.frequency)
        self.buffer = int((abs(self.left_x) + abs(self.right_x))/self.frequency)
        self.data = []
        
        self.crosshairPlot = pg.PlotWidget()
        self.crosshairPlot.setXRange(self.left_x, self.right_x)
        self.crosshairPlot.setLabel('left', 'Value')
        self.crosshairPlot.setLabel('bottom', 'Time (s)')
        self.crosshairColor = (196,220,255)

        self.plot = self.crosshairPlot.plot()

        self.layout = QtGui.QGridLayout()
        self.layout.addWidget(self.crosshairPlot)
        
        self.crosshairPlot.plotItem.setAutoVisible(y=True)
        self.vLine = pg.InfiniteLine(angle=90)
        self.hLine = pg.InfiniteLine(angle=0, movable=False)
        self.vLine.setPen(self.crosshairColor)
        self.hLine.setPen(self.crosshairColor)
        self.crosshairPlot.setAutoVisible(y=True)
        self.crosshairPlot.addItem(self.vLine, ignoreBounds=True)
        self.crosshairPlot.addItem(self.hLine, ignoreBounds=True)
        
        self.crosshairUpdate = pg.SignalProxy(self.crosshairPlot.scene().sigMouseMoved, rateLimit=60, slot=self.updateCrosshair)

        self.start()

    def plotUpdater(self):
        self.dataPoint = random.randint(1,101)
        if len(self.data) >= self.buffer:
            self.data.pop(0)
        self.data.append(float(self.dataPoint))
        self.plot.setData(self.x_axis[len(self.x_axis) - len(self.data):], self.data)

    def updateCrosshair(self, event):
        coordinates = event[0]  
        if self.crosshairPlot.sceneBoundingRect().contains(coordinates):
            mousePoint = self.crosshairPlot.plotItem.vb.mapSceneToView(coordinates)
            index = mousePoint.x()
            if index > self.left_x and index <= self.right_x:
                self.crosshairPlot.setTitle("<span style='font-size: 12pt'>x=%0.1f,   <span style='color: red'>y=%0.1f</span>" % (mousePoint.x(), mousePoint.y()))
            self.vLine.setPos(mousePoint.x())
            self.hLine.setPos(mousePoint.y())

    def start(self):
        self.timer = QtCore.QTimer()
        self.timer.timeout.connect(self.plotUpdater)
        self.timer.start(self.getTimerFrequency())

    def getCrosshairPlotLayout(self):
        return self.layout

    def getTimerFrequency(self):
        return self.timer_frequency

# ==================================================================
# Video Stream widget with crosshair enable/disable
# ==================================================================
class VideoWindow(QtGui.QWidget):
    def __init__(self, parent=None):
        super(VideoWindow, self).__init__(parent)

        self.capture = None
        self.videoFileName = None
        self.isVideoFileOrStreamLoaded = False
        self.pause = True
        self.minWindowWidth = 400
        self.minWindowHeight = 400

        self.offset = 9
        self.placeholder_image_file = 'placeholder1.PNG'

        self.frequency = .002
        self.timer_frequency = self.frequency * 1000

        self.videoFrame = QtGui.QLabel()
        
        self.layout = QtGui.QGridLayout()
        self.layout.addWidget(self.videoFrame,0,0)

        self.initPlaceholderImage()
        self.setLayout(self.layout)
        self.crosshairOverlay = Overlay(self)
        self.displayCrosshair = True

        self.timer = QtCore.QTimer()
        self.timer.timeout.connect(self.setFrame)
        self.getFrameThread = Thread(target=self.getFrame, args=())
        self.getFrameThread.daemon = True
        self.getFrameThread.start()
        self.startCapture()

    def initPlaceholderImage(self):
        self.placeholder_image = cv2.imread(self.placeholder_image_file)
        
        # Maintain aspect ratio
        #self.placeholder_image = imutils.resize(self.placeholder_image, width=self.minWindowWidth)
        self.placeholder_image = cv2.resize(self.placeholder_image, (self.minWindowWidth, self.minWindowHeight))

        self.placeholder = QtGui.QImage(self.placeholder_image, self.placeholder_image.shape[1], self.placeholder_image.shape[0], QtGui.QImage.Format_RGB888).rgbSwapped()
        self.placeholder_image = QtGui.QPixmap.fromImage(self.placeholder)
        self.videoFrame.setPixmap(self.placeholder_image)

    def alignCrosshair(self):
        capture = cv2.VideoCapture(str(self.videoFileName))
        status, frame = capture.read()
        frame = imutils.resize(frame, width=self.minWindowWidth)
        self.resizedImageHeight = frame.shape[0]
        frameHeight = self.size().height()
        self.translate = (frameHeight - self.resizedImageHeight - (2 * self.offset))/2
    
    def startCapture(self):
        self.pause = False
        self.timer.start(self.timer_frequency)

    def pauseCapture(self):
        if not self.pause:
            self.pause = True
            self.timer.stop()

    def stopCapture(self):
        self.pauseCapture()
        self.capture = cv2.VideoCapture(str(self.videoFileName))

    def loadVideoFile(self):
        try:
            self.videoFileName = QtGui.QFileDialog.getOpenFileName(self, 'Select .h264 Video File')
            if self.videoFileName:
                self.isVideoFileOrStreamLoaded = True
                self.pause = False
                self.capture = cv2.VideoCapture(str(self.videoFileName))
                self.alignCrosshair()
        except:
            print("Please select a .h264 file")

    def openNetworkStream(self):
        text, okPressed = QtGui.QInputDialog.getText(self, "Open Media", "Please enter a network URL:")
        link = str(text)
        if okPressed and self.verifyNetworkStream(link):
            self.isVideoFileOrStreamLoaded = True
            self.pause = False
            self.videoFileName = link
            self.capture = cv2.VideoCapture(link)
            self.alignCrosshair()
            
    def verifyNetworkStream(self, link):
        cap = cv2.VideoCapture(link)
        if cap is None or not cap.isOpened():
            print('Warning: unable to open video link')
            return False
        return True

    def getFrame(self):
        while True:
            try:
                if not self.pause and self.capture.isOpened():
                    status, self.frame = self.capture.read()
                    if self.frame is not None:
                        self.frame = imutils.resize(self.frame, width=self.minWindowWidth)
                        self.img = QtGui.QImage(self.frame, self.frame.shape[1], self.frame.shape[0], QtGui.QImage.Format_RGB888).rgbSwapped()
                        self.pix = QtGui.QPixmap.fromImage(self.img)
            except:
                pass
            time.sleep(self.frequency)

    def setFrame(self):
        try:
            self.videoFrame.setPixmap(self.pix)
        except:
            pass

    def getVideoWindowLayout(self):
        return self.layout
    
    def showCrosshair(self):
        self.displayCrosshair = True
        self.crosshairOverlay.show()

    def hideCrosshair(self):
        self.displayCrosshair = False 
        self.crosshairOverlay.hide()

    def resizeEvent(self, event):
        self.crosshairOverlay.resize(event.size())
        event.accept()
        
    def mousePressEvent(self, QMouseEvent):
        if self.isVideoFileOrStreamLoaded and self.displayCrosshair:
            x = self.crosshairOverlay.getX() 
            y = self.crosshairOverlay.getY() - self.translate
            
            if x > 0 and x < self.minWindowWidth and y > 0 and y < self.resizedImageHeight:
                c = self.img.pixel(x,y)
                print(QtGui.QColor(c).getRgb())
        
class VideoStreamWidget(QtGui.QWidget):
    def __init__(self, parent=None):
        super(VideoStreamWidget, self).__init__(parent)
        
        self.videoWindow = VideoWindow()

        self.startButton = QtGui.QPushButton('Start')
        self.startButton.clicked.connect(self.videoWindow.startCapture)
        self.pauseButton = QtGui.QPushButton('Pause')
        self.pauseButton.clicked.connect(self.videoWindow.pauseCapture)
        self.stopButton = QtGui.QPushButton('Stop')
        self.stopButton.clicked.connect(self.videoWindow.stopCapture)

        self.layout = QtGui.QGridLayout()
        self.buttonLayout = QtGui.QHBoxLayout()
        self.buttonLayout.addWidget(self.startButton)
        self.buttonLayout.addWidget(self.pauseButton)
        self.buttonLayout.addWidget(self.stopButton)

        self.layout.addLayout(self.buttonLayout,0,0)
        self.layout.addWidget(self.videoWindow,1,0)

    def getVideoDisplayLayout(self):
        return self.layout

    def openNetworkStream(self):
        self.videoWindow.openNetworkStream()

    def loadVideoFile(self):
        self.videoWindow.loadVideoFile()

    def showCrosshair(self):
        self.videoWindow.showCrosshair()

    def hideCrosshair(self):
        self.videoWindow.hideCrosshair()
    
class CrosshairWidget(QtGui.QWidget):
    def __init__(self, parent=None):
        super(CrosshairWidget, self).__init__(parent)
        
        # Create the crosshair (invisible plot)
        self.crosshairPlot = pg.PlotWidget()
        self.crosshairPlot.setBackground(background=None)

        self.crosshairPlot.plotItem.hideAxis('bottom') 
        self.crosshairPlot.plotItem.hideAxis('left') 
        self.crosshairPlot.plotItem.hideAxis('right') 
        self.crosshairPlot.plotItem.hideAxis('top')
        self.crosshairPlot.plotItem.setMouseEnabled(x=False, y=False)

        self.crosshairColor = (196,220,255)

        self.layout = QtGui.QGridLayout()
        self.layout.addWidget(self.crosshairPlot)
       
        # Create the crosshair
        self.crosshairPlot.plotItem.setAutoVisible(y=True)
        self.vLine = pg.InfiniteLine(angle=90)
        self.hLine = pg.InfiniteLine(angle=0, movable=False)
        self.vLine.setPen(self.crosshairColor)
        self.hLine.setPen(self.crosshairColor)
        self.crosshairPlot.setAutoVisible(y=True)
        self.crosshairPlot.addItem(self.vLine, ignoreBounds=True)
        self.crosshairPlot.addItem(self.hLine, ignoreBounds=True)
        
        # Update crosshair
        self.crosshairUpdate = pg.SignalProxy(self.crosshairPlot.scene().sigMouseMoved, rateLimit=300, slot=self.updateCrosshair)
        
    def updateCrosshair(self, event):
        coordinates = event[0]  
        self.x = coordinates.x()
        self.y = coordinates.y()
        if self.crosshairPlot.sceneBoundingRect().contains(coordinates):
            mousePoint = self.crosshairPlot.plotItem.vb.mapSceneToView(coordinates)
            index = mousePoint.x()
            self.vLine.setPos(mousePoint.x())
            self.hLine.setPos(mousePoint.y())

    def getCrosshairLayout(self):
        return self.layout

    def getX(self):
        return self.x

    def getY(self):
        return self.y

class Overlay(QtGui.QWidget):
    def __init__(self, parent):
        super(Overlay, self).__init__(parent)

        # Make any widgets in the container have a transparent background
        self.palette = QtGui.QPalette(self.palette())
        self.palette.setColor(self.palette.Background, QtCore.Qt.transparent)
        self.setPalette(self.palette)
        
        self.crosshair = CrosshairWidget()

        self.layout = QtGui.QGridLayout()
        self.layout.addLayout(self.crosshair.getCrosshairLayout(),1,0)
        self.setLayout(self.layout)

    # Make overlay transparent but keep widgets
    def paintEvent(self, event):
        self.painter = QtGui.QPainter()
        self.painter.begin(self)
        self.painter.setRenderHint(QtGui.QPainter.Antialiasing)
        # Transparency settings for overlay (r,g,b,a)
        self.painter.fillRect(event.rect(), QtGui.QBrush(QtGui.QColor(0, 0, 0, 0)))
        self.painter.end()

    def getX(self):
        return self.crosshair.getX()

    def getY(self):
        return self.crosshair.getY()


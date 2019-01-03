from PyQt4 import QtCore, QtGui
import pyqtgraph as pg
import random
import zmq
import numpy as np
import sys
import time
from threading import Thread
import cv2

# Plot with fixed data moving right to left
# Adjustable fixed x-axis, dynamic y-axis, data does not shrink
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

class RotationalControllerPlotWidget(QtGui.QWidget):
    def __init__(self, position_address, position_topic, position_frequency, parameter_address, parent=None):
        super(RotationalControllerPlotWidget, self).__init__(parent)
        
        self.dataTimeout = 1
        self.positionVerified = False
        self.parameterVerified = False
        self.fail = False
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
            self.fail = True
        except:
            self.parameterVerified = False
        if self.fail:
            QtGui.QMessageBox.about(QtGui.QWidget(), 'Error', 'Initial handshake failed: Invalid parameterAddress value. Check motor.ini')
            exit(1)

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

    def plotUpdater(self):
        if self.positionVerified:
            self.dataPoint = float(self.currentPositionValue)

            if len(self.data) >= self.buffer:
                self.data.pop(0)
            self.data.append(self.dataPoint)
            self.plotter.setData(self.X_Axis[len(self.X_Axis) - len(self.data):], self.data)
    
    def getRotationalControllerFrequency(self):
        return self.FREQUENCY
    
    def getRotationalControllerTimerFrequency(self):
        return self.TIMER_FREQUENCY

    def getRotationalControllerLayout(self):
        return self.layout

    def getRotationalControllerPlotWidget(self):
        return self.plot

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

class VideoDisplayWidget(QtGui.QWidget):
    def __init__(self, parent=None):
        super(VideoDisplayWidget, self).__init__(parent)

        self.capture = None
        self.videoFileName = None
        self.isVideoFileLoaded = False

        self.layout = QtGui.QFormLayout()
        self.loadButton = QtGui.QPushButton('Select Video')
        self.loadButton.clicked.connect(self.loadVideoFile)
        self.loadButton.setFixedWidth(50)
        self.startButton = QtGui.QPushButton('Start')
        self.startButton.clicked.connect(self.startCapture)
        self.startButton.setFixedWidth(50)
        self.pauseButton = QtGui.QPushButton('Pause')
        self.pauseButton.clicked.connect(self.pauseCapture)
        self.pauseButton.setFixedWidth(50)

        #self.layout.addRow(self.loadButton, self.startButton, self.pauseButton)
        self.layout.addRow(self.loadButton)
        self.layout.addRow(self.startButton)
        self.layout.addRow(self.pauseButton)

        self.videoFrame = QtGui.QLabel()
        self.layout.addWidget(self.videoFrame)
    def getVideoDisplayLayout(self):
        return self.layout

    def startCapture(self):
        if not self.capture:
            self.capture = cv2.VideoCapture(str(self.videoFileName))
        else:
            self.start()
    def loadVideoFile(self):
        try:
            self.videoFileName = QtGui.QFileDialog.getOpenFileName(self, 'Select .h264 Video File')
            self.isVideoFileLoaded = True
        except:
            print("Please select a .h264 file")
    def nextFrameSlot(self):
        status, frame = self.capture.read()
        img = QtGui.QImage(frame, frame.shape[1], frame.shape[0], QtGui.QImage.Format_RGB888).rgbSwapped()
        pix = QtGui.QPixmap.fromImage(img)
        self.videoFrame.setPixmap(pix)

    def start(self):
        self.timer = QtCore.QTimer()
        self.timer.timeout.connect(self.nextFrameSlot)
        self.timer.start(.1)

    def pauseCapture(self):
        self.timer.stop()


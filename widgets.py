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
    def __init__(self, parent=None):
        super(ZMQPlotWidget, self).__init__(parent)

        # FREQUENCY HAS TO BE SAME AS SERVER'S FREQUENCY
        # Desired Frequency (Hz) = 1 / self.ZMQ_FREQUENCY
        # USE FOR TIME.SLEEP (s)
        self.ZMQ_FREQUENCY = .025

        # Frequency to update plot (ms)
        # USE FOR TIMER.TIMER (ms)
        self.ZMQ_TIMER_FREQUENCY = self.ZMQ_FREQUENCY * 1000

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
        self.ZMQ_TCP_Port = "tcp://192.168.1.134:6002"
        self.ZMQ_Topic = "10001"
        self.ZMQContext = zmq.Context()
        self.ZMQSocket = self.ZMQContext.socket(zmq.SUB)
        self.ZMQSocket.connect(self.ZMQ_TCP_Port)
        self.ZMQSocket.setsockopt(zmq.SUBSCRIBE, self.ZMQ_Topic)
        
    def updateZMQPlotAddress(self, address, topic):
        self.ZMQ_TCP_Port = address 
        self.ZMQ_Topic = topic
        self.ZMQContext = zmq.Context()
        self.ZMQSocket = self.ZMQContext.socket(zmq.SUB)
        self.ZMQSocket.connect(self.ZMQ_TCP_Port)
        self.ZMQSocket.setsockopt(zmq.SUBSCRIBE, self.ZMQ_Topic)
        
    def ZMQPlotUpdater(self):
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

    def start(self):
        self.ZMQPlotTimer = QtCore.QTimer()
        self.ZMQPlotTimer.timeout.connect(self.ZMQPlotUpdater)
        self.ZMQPlotTimer.start(self.getZMQTimerFrequency())
          
class RotationalControllerPlotWidget(QtGui.QWidget):
    def __init__(self, parent=None):
        super(RotationalControllerPlotWidget, self).__init__(parent)

        # FREQUENCY HAS TO BE SAME AS SERVER'S FREQUENCY
        # Desired Frequency (Hz) = 1 / self.FREQUENCY
        # USE FOR TIME.SLEEP (s)
        self.FREQUENCY = .025

        # Frequency to update plot (ms)
        # USE FOR TIMER.TIMER (ms)
        self.TIMER_FREQUENCY = self.FREQUENCY * 1000

        # Set X Axis range. If desired is [-10,0] then set LEFT_X = -10 and RIGHT_X = 0
        self.LEFT_X = -10
        self.RIGHT_X = 0
        self.X_Axis = np.arange(self.LEFT_X, self.RIGHT_X, self.FREQUENCY)
        self.buffer = int((abs(self.LEFT_X) + abs(self.RIGHT_X))/self.FREQUENCY)
        self.data = [] 

        # Create ZMQ Plot Widget 
        self.plot = pg.PlotWidget()
        self.plot.setXRange(self.LEFT_X, self.RIGHT_X)
        self.plot.setTitle('Rotational Controller Position')
        self.plot.setLabel('left', 'Value')
        self.plot.setLabel('bottom', 'Time (s)')

        self.plotter = self.plot.plot()
        self.plotter.setPen(232,234,246)

        self.layout = QtGui.QGridLayout()
        self.layout.addWidget(self.plot)

    def plotUpdater(self, data):
        self.dataPoint = float(data)

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



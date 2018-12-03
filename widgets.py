from PyQt4 import QtCore, QtGui
import pyqtgraph as pg
import random
import zmq
import numpy as np
import sys
import time
from threading import Thread
import cv2

class ZMQPlotWidget(QtGui.QWidget):
    def __init__(self, parent=None):
        super(ZMQPlotWidget, self).__init__(parent)

        self.layout = QtGui.QGridLayout()

        # Set X Axis range. If desired is [-10,0] then set LEFT_X = -10 and RIGHT_X = 0
        self.ZMQ_LEFT_X = -10
        self.ZMQ_RIGHT_X = 0
        
        # Desired Frequency (Hz) = 1 / self.ZMQ_FREQUENCY
        # USE FOR TIME.SLEEP (s)
        self.ZMQ_FREQUENCY = .025

        # Frequency to update plot (ms)
        # USE FOR TIMER.TIMER (ms)
        self.ZMQ_TIMER_FREQUENCY = self.ZMQ_FREQUENCY * 1000
        self.ZMQPlot = pg.PlotWidget()
        self.ZMQPlot.setXRange(self.ZMQ_LEFT_X, self.ZMQ_RIGHT_X)
        self.layout.addWidget(self.ZMQPlot)
        self.ZMQPlot.setTitle('ZMQ Plot')
        self.ZMQPlot.setLabel('left', 'Value')
        self.ZMQPlot.setLabel('bottom', 'Time (s)')

        self.ZMQPlotter = self.ZMQPlot.plot()
        #self.ZMQPlotLegend = self.ZMQPlot.addLegend()
        #self.ZMQPlotLegend.addItem(self.ZMQPlotter, 'A')
        
        self.ZMQ_X_Axis = np.arange(self.ZMQ_LEFT_X, self.ZMQ_RIGHT_X, self.ZMQ_FREQUENCY)
        self.ZMQBuffer = int((abs(self.ZMQ_LEFT_X) + abs(self.ZMQ_RIGHT_X))/self.ZMQ_FREQUENCY)
        self.ZMQData = [] 
        
        # Create ZMQ Plot Widget
        # Setup socket port and topic using pub/sub system
        self.ZMQ_TCP_Port = "tcp://192.168.1.125:6002"
        self.ZMQ_Topic = "10001"
        self.ZMQContext = zmq.Context()
        self.ZMQSocket = self.ZMQContext.socket(zmq.SUB)
        self.ZMQSocket.connect(self.ZMQ_TCP_Port)
        self.ZMQSocket.setsockopt(zmq.SUBSCRIBE, self.ZMQ_Topic)
        
        self.oldZMQDataPoint = 0

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
            self.topic, self.ZMQDataPoint = self.ZMQSocket.recv(zmq.NOBLOCK).split()
            self.oldZMQDataPoint = self.ZMQDataPoint
        except zmq.ZMQError, e:
            # No data arrived
            if e.errno == zmq.EAGAIN:
                self.ZMQDataPoint = self.oldZMQDataPoint

        if len(self.ZMQData) >= self.ZMQBuffer:
            self.ZMQData.pop(0)
        
        #self.ZMQData.append(random.randint(1,101))        
        self.ZMQData.append(float(self.ZMQDataPoint))
        self.ZMQPlotter.setData(self.ZMQ_X_Axis[len(self.ZMQ_X_Axis) - len(self.ZMQData):], self.ZMQData)
    
    def getZMQPlotAddress(self):
        return self.ZMQ_TCP_Port

    # Version with QTimer (ms)
    def getZMQTimerFrequency(self):
        return self.ZMQ_TIMER_FREQUENCY

    # Version with time.sleep (s) 
    def getZMQFrequency(self):
        return self.ZMQ_FREQUENCY

    def start(self):
        self.ZMQPlotTimer = QtCore.QTimer()
        self.ZMQPlotTimer.timeout.connect(self.ZMQPlotUpdater)
        self.ZMQPlotTimer.start(self.getZMQTimerFrequency())
          
    def getZMQLayout(self):
        return self.layout

class RotationalControllerPlotWidget(QtGui.QWidget):
    def __init__(self, parent=None):
        super(RotationalControllerPlotWidget, self).__init__(parent)

        self.layout = QtGui.QGridLayout()

        # Set X Axis range. If desired is [-10,0] then set LEFT_X = -10 and RIGHT_X = 0
        self.LEFT_X = -10
        self.RIGHT_X = 0
        
        # Desired Frequency (Hz) = 1 / self.FREQUENCY
        # USE FOR TIME.SLEEP (s)
        # FREQUENCY HAS TO BE SAME AS SERVER'S FREQUENCY
        self.FREQUENCY = .025

        # Frequency to update plot (ms)
        # USE FOR TIMER.TIMER (ms)
        self.TIMER_FREQUENCY = self.FREQUENCY * 1000
        self.plot = pg.PlotWidget()
        self.plot.setXRange(self.LEFT_X, self.RIGHT_X)
        self.layout.addWidget(self.plot)
        self.plot.setTitle('Rotational Controller Position')
        self.plot.setLabel('left', 'Value')
        self.plot.setLabel('bottom', 'Time (s)')

        self.plotter = self.plot.plot()
        
        self.X_Axis = np.arange(self.LEFT_X, self.RIGHT_X, self.FREQUENCY)
        self.buffer = int((abs(self.LEFT_X) + abs(self.RIGHT_X))/self.FREQUENCY)
        self.data = [] 
        
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

class PortSettingPopUpWidget(QtGui.QWidget):
    def __init__(self, windowTitle, parent=None):
        super(PortSettingPopUpWidget, self).__init__(parent)
        self.popUpWidth = 195
        self.popUpHeight = 150
        self.setFixedSize(self.popUpWidth, self.popUpHeight)

        self.setWindowTitle(windowTitle)
        self.position_address = ()
        self.parameter_address = ()
        self.plot_address = ()
        self.tabs = QtGui.QTabWidget(self)
        self.positionTab = QtGui.QWidget()
        self.parameterTab = QtGui.QWidget()
        self.plotTab = QtGui.QWidget()

        # Position
        self.positionLayout = QtGui.QFormLayout()
        self.position_TCPAddress = QtGui.QLineEdit()
        self.position_TCPAddress.setMaxLength(15)
        self.position_TCPPort = QtGui.QLineEdit()
        self.position_TCPPort.setValidator(QtGui.QIntValidator())
        self.position_TCPTopic = QtGui.QLineEdit()
        self.position_TCPTopic.setValidator(QtGui.QIntValidator())
        self.positionButtonLayout = QtGui.QHBoxLayout()
        self.positionConnectButton = QtGui.QPushButton('Connect')
        self.positionConnectButton.setStyleSheet('background-color: #3CB371')
        self.positionConnectButton.clicked.connect(self.position_saveButton)
        self.positionCancelButton = QtGui.QPushButton('Cancel')
        self.positionCancelButton.clicked.connect(self.position_cancelButton)
        self.positionButtonLayout.addWidget(self.positionConnectButton)
        self.positionButtonLayout.addWidget(self.positionCancelButton)

        self.positionLayout.addRow("TCP Address", self.position_TCPAddress)
        self.positionLayout.addRow("Port", self.position_TCPPort)
        self.positionLayout.addRow("Topic", self.position_TCPTopic)
        self.positionLayout.addRow(self.positionButtonLayout)
        self.positionTab.setLayout(self.positionLayout)

        # Parameter
        self.parameterLayout = QtGui.QFormLayout() 
        self.parameter_TCPAddress = QtGui.QLineEdit()
        self.parameter_TCPAddress.setMaxLength(15)
        self.parameter_TCPPort = QtGui.QLineEdit()
        self.parameter_TCPPort.setValidator(QtGui.QIntValidator())
        self.parameterButtonLayout = QtGui.QHBoxLayout()
        self.parameterConnectButton = QtGui.QPushButton('Save')
        self.parameterConnectButton.setStyleSheet('background-color: #3CB371')
        self.parameterConnectButton.clicked.connect(self.parameter_saveButton)
        self.parameterCancelButton = QtGui.QPushButton('Cancel')
        self.parameterCancelButton.clicked.connect(self.parameter_cancelButton)
        self.parameterButtonLayout.addWidget(self.parameterConnectButton)
        self.parameterButtonLayout.addWidget(self.parameterCancelButton)

        self.parameterLayout.addRow("TCP Address", self.parameter_TCPAddress)
        self.parameterLayout.addRow("Port", self.parameter_TCPPort)
        self.parameterLayout.addRow(self.parameterButtonLayout)
        self.parameterTab.setLayout(self.parameterLayout)

        # Plot
        self.plotLayout = QtGui.QFormLayout()
        self.plot_TCPAddress = QtGui.QLineEdit()
        self.plot_TCPAddress.setMaxLength(15)
        self.plot_TCPPort = QtGui.QLineEdit()
        self.plot_TCPPort.setValidator(QtGui.QIntValidator())
        self.plot_TCPTopic = QtGui.QLineEdit()
        self.plot_TCPTopic.setValidator(QtGui.QIntValidator())
        self.plotButtonLayout = QtGui.QHBoxLayout()
        self.plotConnectButton = QtGui.QPushButton('Connect')
        self.plotConnectButton.setStyleSheet('background-color: #3CB371')
        self.plotConnectButton.clicked.connect(self.plot_saveButton)
        self.plotCancelButton = QtGui.QPushButton('Cancel')
        self.plotCancelButton.clicked.connect(self.plot_cancelButton)
        self.plotButtonLayout.addWidget(self.plotConnectButton)
        self.plotButtonLayout.addWidget(self.plotCancelButton)

        self.plotLayout.addRow("TCP Address", self.plot_TCPAddress)
        self.plotLayout.addRow("Port", self.plot_TCPPort)
        self.plotLayout.addRow("Topic", self.plot_TCPTopic)
        self.plotLayout.addRow(self.plotButtonLayout)
        self.plotTab.setLayout(self.plotLayout)

        self.tabs.addTab(self.positionTab, 'Position')
        self.tabs.addTab(self.parameterTab, 'Parameters')
        self.tabs.addTab(self.plotTab, 'Plot')
         
        self.setWindowModality(QtCore.Qt.ApplicationModal)
        self.show()

    def keyPressEvent(self, event):
        if event.key() == QtCore.Qt.Key_Escape:
            self.close()

    def position_saveButton(self):
        address = str(self.position_TCPAddress.text())
        port = str(self.position_TCPPort.text())
        topic = str(self.position_TCPTopic.text())
        Thread(target=self.positionCheckValidPort, args=(address,port,topic)).start()
        self.close()
        
    def position_cancelButton(self):
        self.close()

    def getPositionAddress(self):
        return self.position_address
    
    def setPositionAddress(self, s):
        self.position_address = s

    def positionCheckValidPort(self, address, port, topic):
        if address and port and topic:
            position_address = "tcp://" + address + ":" + port
            context = zmq.Context()
            socket = context.socket(zmq.SUB)
            socket.connect(position_address)
            socket.setsockopt(zmq.SUBSCRIBE, topic)
            # Check for valid data within 1 second
            time_end = time.time() + 1
            valid_flag = False
            while time.time() < time_end:
                try:
                    topic, data = socket.recv(zmq.NOBLOCK).split()
                    self.position_address = (address, port, topic)
                    valid_flag = True
                    break
                except zmq.ZMQError, e:
                    # No data arrived
                    if e.errno == zmq.EAGAIN:
                        pass
                    else:
                        print("real error")
            if valid_flag == False:
                self.position_address = (False)
        else:
            self.position_address = (False)

    def parameter_saveButton(self):
        address = str(self.parameter_TCPAddress.text())
        port = str(self.parameter_TCPPort.text())
        Thread(target=self.parameterCheckValidPort, args=(address,port)).start()
        self.close()
        
    def parameter_cancelButton(self):
        self.close()

    def getParameterAddress(self):
        return self.parameter_address
    
    def setParameterAddress(self, s):
        self.parameter_address = s

    def parameterCheckValidPort(self, address, port):
        if address and port:
            parameter_address = "tcp://" + address + ":" + port
            context = zmq.Context()
            socket = context.socket(zmq.REQ)
            # Prevent program from hanging after closing
            socket.setsockopt(zmq.LINGER, 0)
            socket.connect(parameter_address)
            socket.send("info?")
            # Check for valid data within 1 second
            time_end = time.time() + 1
            valid_flag = False
            while time.time() < time_end:
                try:
                    result = socket.recv(zmq.NOBLOCK).split(',')
                    print(result)
                    self.parameter_address = (address, port)
                    valid_flag = True
                    break
                except zmq.ZMQError, e:
                    # No data arrived
                    if e.errno == zmq.EAGAIN:
                        pass
                    else:
                        print("real error")
            if valid_flag == False:
                self.parameter_address = (False)
        else:
            self.parameter_address = (False)

    def plot_saveButton(self):
        address = str(self.plot_TCPAddress.text())
        port = str(self.plot_TCPPort.text())
        topic = str(self.plot_TCPTopic.text())
        Thread(target=self.plotCheckValidPort, args=(address,port,topic)).start()
        self.close()
        
    def plot_cancelButton(self):
        self.close()

    def getPlotAddress(self):
        return self.plot_address
    
    def setPlotAddress(self, s):
        self.plot_address = s

    def plotCheckValidPort(self, address, port, topic):
        if address and port and topic:
            port_address = "tcp://" + address + ":" + port
            context = zmq.Context()
            socket = context.socket(zmq.SUB)
            socket.connect(port_address)
            socket.setsockopt(zmq.SUBSCRIBE, topic)
            # Check for valid data within 1 second
            time_end = time.time() + 1
            valid_flag = False
            while time.time() < time_end:
                try:
                    topic, data = socket.recv(zmq.NOBLOCK).split()
                    self.plot_address = (address, port, topic)
                    valid_flag = True
                    break
                except zmq.ZMQError, e:
                    # No data arrived
                    if e.errno == zmq.EAGAIN:
                        pass
                    else:
                        print("real error")
            if valid_flag == False:
                self.plot_address = (False)
        else:
            self.plot_address = (False)

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



from PyQt4 import QtCore, QtGui
import pyqtgraph as pg
import random
import zmq
import numpy as np
import sys
import time
from threading import Thread

class ZMQPlotWidget(QtGui.QWidget):
    def __init__(self, parent=None):
        super(ZMQPlotWidget, self).__init__(parent)

        self.layout = QtGui.QGridLayout()
        # Set X Axis range. If desired is [-10,0] then set LEFT_X = -10 and RIGHT_X = 1
        self.ZMQ_LEFT_X = -10
        self.ZMQ_RIGHT_X = 1

        # Data frequency (Hz) 
        # Formula = 1 / # (s/Hz)
        self.ZMQ_FREQUENCY = 1
        #self.ZMQ_FREQUENCY = .1

        # Frequency to update plot (ms)
        self.ZMQ_TIMER_FREQUENCY = self.ZMQ_FREQUENCY * 1000

        self.ZMQPlot = pg.PlotWidget()
        self.ZMQPlot.setXRange(self.ZMQ_LEFT_X, self.ZMQ_RIGHT_X - 1)
        self.layout.addWidget(self.ZMQPlot)
        self.ZMQPlot.setTitle('ZMQ Plot')
        self.ZMQPlot.setLabel('left', 'Value')
        self.ZMQPlot.setLabel('bottom', 'Time (s)')

        self.ZMQPlotter = self.ZMQPlot.plot()
        self.ZMQPlotLegend = self.ZMQPlot.addLegend()
        self.ZMQPlotLegend.addItem(self.ZMQPlotter, 'A')
        
        self.ZMQ_X_Axis = np.arange(self.ZMQ_LEFT_X, self.ZMQ_RIGHT_X, self.ZMQ_FREQUENCY)

        self.ZMQBuffer = (abs(self.ZMQ_LEFT_X) + abs(self.ZMQ_RIGHT_X))/self.ZMQ_FREQUENCY
        self.ZMQData = [] 
        
        # Create ZMQ Plot Widget
        # Setup socket port and topic using pub/sub system
        self.ZMQ_TCP_Port = "tcp://*:6002"
        self.ZMQ_Topic = "10001"
        #self.ZMQ_TCP_Port = "tcp://192.168.30.30:6003"
        #self.ZMQ_Topic = "10002"
        self.ZMQContext = zmq.Context()
        self.ZMQSocket = self.ZMQContext.socket(zmq.SUB)
        self.ZMQSocket.connect(self.ZMQ_TCP_Port)
        self.ZMQSocket.setsockopt(zmq.SUBSCRIBE, self.ZMQ_Topic)

    def ZMQPlotUpdater(self):
        # Receives (topic, data)
        self.topic, self.ZMQDataPoint = self.ZMQSocket.recv().split()
        if not self.ZMQData:
            self.ZMQData.append(random.randint(1,101))        
            #self.ZMQData.append(int(self.ZMQDataPoint))
            pass
        if len(self.ZMQData) == self.ZMQBuffer:
            self.ZMQData.pop(0)
        
        self.ZMQData.append(random.randint(1,101))        
        #self.ZMQData.append(int(self.ZMQDataPoint))
        self.ZMQPlotter.setData(self.ZMQ_X_Axis[len(self.ZMQ_X_Axis) - len(self.ZMQData):], self.ZMQData)

    def getZMQTimerFrequency(self):
        return self.ZMQ_TIMER_FREQUENCY

    def getZMQLayout(self):
        return self.layout

class PortSettingPopUpWidget(QtGui.QWidget):
    def __init__(self, parent=None):
        super(PortSettingPopUpWidget, self).__init__(parent)
        
        self.position_address = ()
        self.parameter_address = ()
        self.tabs = QtGui.QTabWidget(self)
        self.positionTab = QtGui.QWidget()
        self.parameterTab = QtGui.QWidget()

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
        self.parameterConnectButton.clicked.connect(self.parameter_saveButton)
        self.parameterCancelButton = QtGui.QPushButton('Cancel')
        self.parameterCancelButton.clicked.connect(self.parameter_cancelButton)
        self.parameterButtonLayout.addWidget(self.parameterConnectButton)
        self.parameterButtonLayout.addWidget(self.parameterCancelButton)

        self.parameterLayout.addRow("TCP Address", self.parameter_TCPAddress)
        self.parameterLayout.addRow("Port", self.parameter_TCPPort)
        self.parameterLayout.addRow(self.parameterButtonLayout)
        self.parameterTab.setLayout(self.parameterLayout)
        
        self.tabs.addTab(self.positionTab, 'Position')
        self.tabs.addTab(self.parameterTab, 'Parameters')
         
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
        address = self.parameter_TCPAddress.text()
        port = self.parameter_TCPPort.text()
        Thread(target=self.parameterCheckValidPort, args=(address,port)).start()
        self.close()
        
    def parameter_cancelButton(self):
        self.close()

    def getParameterAddress(self):
        return self.parameter_address
    
    def setParameterAddress(self, s):
        self.parameter_address = s


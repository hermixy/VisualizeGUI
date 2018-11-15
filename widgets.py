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
        self.tabs = QtGui.QTabWidget(self)
        self.publishSubscribeTab = QtGui.QWidget()
        self.clientServerTab = QtGui.QWidget()

        # Publisher/subscriber tab
        self.publishSubscribeLayout = QtGui.QFormLayout()
        self.PS_TCPAddress = QtGui.QLineEdit()
        self.PS_TCPAddress.setMaxLength(15)
        self.PS_TCPPort = QtGui.QLineEdit()
        self.PS_TCPPort.setValidator(QtGui.QIntValidator())
        self.PS_TCPTopic = QtGui.QLineEdit()
        self.PS_TCPTopic.setValidator(QtGui.QIntValidator())
        self.publishSubscribeButtonLayout = QtGui.QHBoxLayout()
        self.publishSubscribeSaveButton = QtGui.QPushButton('Save')
        self.publishSubscribeSaveButton.clicked.connect(self.PS_saveButton)
        self.publishSubscribeCancelButton = QtGui.QPushButton('Cancel')
        self.publishSubscribeCancelButton.clicked.connect(self.PS_cancelButton)
        self.publishSubscribeButtonLayout.addWidget(self.publishSubscribeSaveButton)
        self.publishSubscribeButtonLayout.addWidget(self.publishSubscribeCancelButton)

        self.publishSubscribeLayout.addRow("TCP Address", self.PS_TCPAddress)
        self.publishSubscribeLayout.addRow("Port", self.PS_TCPPort)
        self.publishSubscribeLayout.addRow("Topic", self.PS_TCPTopic)
        self.publishSubscribeLayout.addRow(self.publishSubscribeButtonLayout)
        self.publishSubscribeTab.setLayout(self.publishSubscribeLayout)

        # Client/server tab
        self.clientServerLayout = QtGui.QFormLayout() 
        self.CS_TCPAddress = QtGui.QLineEdit()
        self.CS_TCPAddress.setMaxLength(15)
        self.CS_TCPPort = QtGui.QLineEdit()
        self.CS_TCPPort.setValidator(QtGui.QIntValidator())
        self.clientServerButtonLayout = QtGui.QHBoxLayout()
        self.clientServerSaveButton = QtGui.QPushButton('Save')
        self.clientServerSaveButton.clicked.connect(self.CS_saveButton)
        self.clientServerCancelButton = QtGui.QPushButton('Cancel')
        self.clientServerCancelButton.clicked.connect(self.CS_cancelButton)
        self.clientServerButtonLayout.addWidget(self.clientServerSaveButton)
        self.clientServerButtonLayout.addWidget(self.clientServerCancelButton)

        self.clientServerLayout.addRow("TCP Address", self.CS_TCPAddress)
        self.clientServerLayout.addRow("Port", self.CS_TCPPort)
        self.clientServerLayout.addRow(self.clientServerButtonLayout)
        self.clientServerTab.setLayout(self.clientServerLayout)
        
        self.tabs.addTab(self.publishSubscribeTab, 'Publish/Subscribe')
        self.tabs.addTab(self.clientServerTab, 'Client/Server')
         
        self.setWindowModality(QtCore.Qt.ApplicationModal)
        self.show()

    def keyPressEvent(self, event):
        if event.key() == QtCore.Qt.Key_Escape:
            self.close()

    def PS_saveButton(self):
        address = str(self.PS_TCPAddress.text())
        port = str(self.PS_TCPPort.text())
        topic = str(self.PS_TCPTopic.text())
        Thread(target=self.checkValidPort, args=(address,port,topic)).start()
        self.close()
        
    def PS_cancelButton(self):
        self.close()

    def CS_saveButton(self):
        print(self.CS_TCPAddress.text())
        print(self.CS_TCPPort.text())
        
    def CS_cancelButton(self):
        self.close()

    def getPositionAddress(self):
        return self.position_address

    def checkValidPort(self, address, port, topic):
        if address and port and topic:
            position_address = "tcp://" + address + ":" + port
            context = zmq.Context()
            socket = context.socket(zmq.SUB)
            socket.connect(position_address)
            socket.setsockopt(zmq.SUBSCRIBE, topic)
            # Check for valid data within 2 seconds
            time_end = time.time() + 2
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
                self.position_address = ()
        else:
            self.position_address = ()

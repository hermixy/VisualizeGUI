from PyQt4 import QtCore, QtGui
import pyqtgraph as pg
import random
import zmq
import numpy as np
import sys

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
        self.ZMQ_TCP_Port = "tcp://192.168.30.30:6002"
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

class PortSettingPopUp(QtGui.QWidget):
    def __init__(self,parent=None):
        super(PortSettingPopUp, self).__init__(parent)
        self.popUpLayout = QtGui.QFormLayout(self)
        self.TCPAddress = QtGui.QLineEdit()
        self.TCPAddress.setMaxLength(15)
        self.TCPPort = QtGui.QLineEdit()
        self.TCPPort.setValidator(QtGui.QIntValidator())
        self.TCPTopic = QtGui.QLineEdit()
        self.TCPTopic.setValidator(QtGui.QIntValidator())
        self.popUpButtonLayout = QtGui.QHBoxLayout()
        self.popUpConfirmButton = QtGui.QPushButton('Save')
        self.popUpConfirmButton.clicked.connect(self.confirmButton)
        self.popUpCancelButton = QtGui.QPushButton('Cancel')
        self.popUpCancelButton.clicked.connect(self.cancelButton)
        self.popUpButtonLayout.addWidget(self.popUpConfirmButton)
        self.popUpButtonLayout.addWidget(self.popUpCancelButton)

        self.popUpLayout.addRow("TCP Address", self.TCPAddress)
        self.popUpLayout.addRow("Port", self.TCPPort)
        self.popUpLayout.addRow("Topic", self.TCPTopic)
        self.popUpLayout.addRow(self.popUpButtonLayout)
        self.setWindowModality(QtCore.Qt.ApplicationModal)
        self.show()
    def getPortSettingPopUpLayout(self):
        return self.popUpLayout
    def confirmButton(self):
        pass
        
    def cancelButton(self):
        print('pass')
        self.close()




#!/bin/env python
# coding: utf-8

import sys
from PyQt4 import QtGui, QtCore
import pyqtgraph as pg
import zmq
import random
import numpy as np

class Window(QtGui.QMainWindow):
    def __init__(self, parent=None):
        # mw (self) is QtGui.QMainWindow
        super(Window, self).__init__(parent)
        self.setGeometry(50, 50, 500, 300)
        self.setWindowTitle("GUI")
        self.setWindowIcon(QtGui.QIcon('pythonlogo.png'))

        self.initLayout()
        self.initMenuBar()
        self.initZMQPlotter()
        #self.initToolBar()

        # Start timer to upgrade plots
        self.startUpdaters()

        # Show the widgets onto the GUI, must be at the end
        self.statusBar()
        self.show()

    # ------------------------------------------------------------------------
    # GUI Setup
    # ------------------------------------------------------------------------
    def initLayout(self):
        # cw (self.centralWidget) is QtGui.QStackedWidget
        # l (self.layout) is QtGui.QGridLayout
        self.centralWidget = QtGui.QWidget()
        self.layout = QtGui.QGridLayout()
        self.setCentralWidget(self.centralWidget)
        self.centralWidget.setLayout(self.layout)

    def initMenuBar(self):
        self.menuBar = self.menuBar()
        self.fileMenu = self.menuBar.addMenu('&File')
        # Close program
        self.exitAction = QtGui.QAction('Exit', self)
        self.exitAction.setShortcut('Ctrl+Q')
        self.exitAction.setStatusTip('Exit application')
        self.exitAction.triggered.connect(QtGui.qApp.quit)
        self.fileMenu.addAction(self.exitAction)

    def initToolBar(self):
        self.toolBar = self.addToolBar('Exit')
        self.toolBar.addAction(self.exitAction)

    def initZMQPlotter(self):
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

    # ------------------------------------------------------------------------
    # Menu Option functions
    # ------------------------------------------------------------------------

    # ------------------------------------------------------------------------
    # GUI Function Elements
    # ------------------------------------------------------------------------
    def startUpdaters(self):
        self.ZMQTimer = QtCore.QTimer()
        self.ZMQTimer.timeout.connect(self.ZMQPlotUpdater)
        self.ZMQTimer.start(self.ZMQ_TIMER_FREQUENCY)

    def ZMQPlotUpdater(self):
        # Receives (topic, data)
        topic, self.ZMQDataPoint = self.ZMQSocket.recv().split()
        if not self.ZMQData:
            self.ZMQData.append(random.randint(1,101))        
            #self.ZMQData.append(int(self.ZMQDataPoint))
            pass
        if len(self.ZMQData) == self.ZMQBuffer:
            self.ZMQData.pop(0)
        
        self.ZMQData.append(random.randint(1,101))        
        #self.ZMQData.append(int(self.ZMQDataPoint))
        self.ZMQPlotter.setData(self.ZMQ_X_Axis[len(self.ZMQ_X_Axis) - len(self.ZMQData):], self.ZMQData)

def run():
    app = QtGui.QApplication([])
    GUI = Window()
    sys.exit(app.exec_())

run()

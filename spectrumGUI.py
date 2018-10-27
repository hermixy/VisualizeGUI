#!/bin/env python
# coding: utf-8

import sys
from PyQt4 import QtGui, QtCore
import pyqtgraph as pg
import random

class Window(QtGui.QMainWindow):

    def __init__(self, parent=None):
        super(Window, self).__init__(parent)
        self.setGeometry(50, 50, 500, 300)
        self.setWindowTitle("GUI")
        self.setWindowIcon(QtGui.QIcon('pythonlogo.png'))

        self.initLayout()
        self.initMenuBar()
        #self.initToolBar()


        # Show the widgets onto the GUI, must be at the end
        self.statusBar()
        self.show()

    # ------------------------------------------------------------------------
    # GUI Setup
    # ------------------------------------------------------------------------
    def initLayout(self):
        self.centralWidget = QtGui.QStackedWidget()
        self.setCentralWidget(self.centralWidget)

        # Create ZMQ Plot Widget
        self.ZMQStreamWidget = ZMQStreamWidget(self)
        self.ZMQStreamWidget.saveButton.clicked.connect(self.ZMQPlotter)
        self.centralWidget.addWidget(self.ZMQStreamWidget)

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


    # ------------------------------------------------------------------------
    # Menu Option functions
    # ------------------------------------------------------------------------

    # ------------------------------------------------------------------------
    # GUI Function Elements
    # ------------------------------------------------------------------------
    def ZMQPlotter(self):
        self.ZMQData =[0]
        self.curve = self.ZMQStreamWidget.plot.getPlotItem().plot()

        self.timer = QtCore.QTimer()
        self.timer.timeout.connect(self.ZMQPlotUpdater)
        self.timer.start(0)

    def ZMQPlotUpdater(self):
        self.ZMQData.append(self.ZMQData[-1]+0.2*(0.5-random.random()) )
        #num = input('number')
        #self.ZMQData.append(int(num))
        self.curve.setData(self.ZMQData)

class ZMQStreamWidget(QtGui.QWidget):
    def __init__(self, parent=None):
        super(ZMQStreamWidget, self).__init__(parent)
        self.layout = QtGui.QGridLayout()
        #self.layout = QtGui.QHBoxLayout()
        self.saveButton = QtGui.QPushButton('Save')
        self.layout.addWidget(self.saveButton)
        self.plot = pg.PlotWidget()
        self.layout.addWidget(self.plot)
        self.setLayout(self.layout)

def run():
    app = QtGui.QApplication([])
    GUI = Window()
    sys.exit(app.exec_())

run()


from PyQt4 import QtCore, QtGui
from widgets import ZMQPlotWidget
import pyqtgraph as pg
import random
import zmq
import numpy as np
import sys

class Window(QtGui.QMainWindow):
    def __init__(self, parent=None):
        super(Window, self).__init__(parent)
        self.setGeometry(50, 50, 500, 300)
        self.setWindowTitle("ZMQ Motor")
        self.setWindowIcon(QtGui.QIcon('pythonlogo.png'))

        self.ZMQPlotter = ZMQPlotWidget(self)
        self.initLayout()
        self.initMenuBar()

        # Start timer to upgrade plots
        self.startUpdaters()

        # Show the widgets onto the GUI, must be at the end
        self.statusBar()
        self.show()

    # ------------------------------------------------------------------------
    # GUI Setup
    # ------------------------------------------------------------------------
    def initLayout(self):
        self.centralWidget = QtGui.QWidget()
        self.setCentralWidget(self.centralWidget)
        self.centralWidget.setLayout(self.ZMQPlotter.getZMQLayout())

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
    # GUI Function Elements
    # ------------------------------------------------------------------------
    def startUpdaters(self):
        self.ZMQTimer = QtCore.QTimer()
        self.ZMQTimer.timeout.connect(self.ZMQPlotter.ZMQPlotUpdater)
        self.ZMQTimer.start(self.ZMQPlotter.getZMQTimerFrequency())

def run():
    app = QtGui.QApplication([])
    GUI = Window()
    sys.exit(app.exec_())

run()

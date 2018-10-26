#!/bin/env python
# coding: utf-8

import sys
from PyQt4 import QtGui, QtCore
import pyqtgraph as pg

class Window(QtGui.QMainWindow):

    def __init__(self):
        super(Window, self).__init__()
        self.setGeometry(50, 50, 500, 300)
        self.setWindowTitle("GUI")
        self.setWindowIcon(QtGui.QIcon('pythonlogo.png'))

        self.initMenuBar()
        #self.initToolBar()

        self.statusBar()

        # Show the widgets onto the GUI, must be at the end
        self.show()

    # ------------------------------------------------------------------------
    # GUI Setup
    # ------------------------------------------------------------------------
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


def run():
    app = QtGui.QApplication([])
    GUI = Window()
    sys.exit(app.exec_())

run()


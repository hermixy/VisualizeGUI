from PyQt4 import QtCore, QtGui
from threading import Thread
import numpy as np
import cv2
import random
import imutils
import pyqtgraph as pg
import sys
import time

class VideoWindow(QtGui.QWidget):
    def __init__(self, parent=None):
        super(VideoWindow, self).__init__(parent)

        self.capture = None
        self.videoFileName = None
        self.isVideoFileOrStreamLoaded = False
        self.pause = True
        self.minWindowWidth = 400
        self.minWindowHeight = 400

        self.placeholder_image_file = '../doc/placeholder5.PNG'

        self.frequency = .002
        self.timer_frequency = self.frequency * 1000

        self.videoFrame = QtGui.QLabel()
        
        self.layout = QtGui.QGridLayout()
        self.layout.addWidget(self.videoFrame,0,0)

        self.initPlaceholderImage()
        self.setLayout(self.layout)

        self.timer = QtCore.QTimer()
        self.timer.timeout.connect(self.setFrame)
        self.getFrameThread = Thread(target=self.getFrame, args=())
        self.getFrameThread.daemon = True
        self.getFrameThread.start()
        self.startCapture()

    def initPlaceholderImage(self):
        self.placeholder_image = cv2.imread(self.placeholder_image_file)
        
        # Maintain aspect ratio
        #self.placeholder_image = imutils.resize(self.placeholder_image, width=self.minWindowWidth)
        self.placeholder_image = cv2.resize(self.placeholder_image, (self.minWindowWidth, self.minWindowHeight))

        self.placeholder = QtGui.QImage(self.placeholder_image, self.placeholder_image.shape[1], self.placeholder_image.shape[0], QtGui.QImage.Format_RGB888).rgbSwapped()
        self.placeholder_image = QtGui.QPixmap.fromImage(self.placeholder)
        self.videoFrame.setPixmap(self.placeholder_image)

    def startCapture(self):
        self.pause = False
        self.timer.start(self.timer_frequency)

    def pauseCapture(self):
        if not self.pause:
            self.pause = True
            self.timer.stop()

    def stopCapture(self):
        self.pauseCapture()
        self.capture = cv2.VideoCapture(str(self.videoFileName))

    def loadVideoFile(self):
        try:
            self.videoFileName = QtGui.QFileDialog.getOpenFileName(self, 'Select .h264 Video File')
            if self.videoFileName:
                self.isVideoFileOrStreamLoaded = True
                self.pause = False
                self.capture = cv2.VideoCapture(str(self.videoFileName))
        except:
            print("Please select a .h264 file")

    def openNetworkStream(self):
        text, okPressed = QtGui.QInputDialog.getText(self, "Open Media", "Please enter a network URL:")
        link = str(text)
        if okPressed and self.verifyNetworkStream(link):
            self.isVideoFileOrStreamLoaded = True
            self.pause = False
            self.videoFileName = link
            self.capture = cv2.VideoCapture(link)
            
    def verifyNetworkStream(self, link):
        cap = cv2.VideoCapture(link)
        if cap is None or not cap.isOpened():
            print('Warning: unable to open video link')
            return False
        return True

    def getFrame(self):
        while True:
            try:
                if not self.pause and self.capture.isOpened():
                    status, self.frame = self.capture.read()
                    if self.frame is not None:
                        self.frame = imutils.resize(self.frame, width=self.minWindowWidth)
                        self.img = QtGui.QImage(self.frame, self.frame.shape[1], self.frame.shape[0], QtGui.QImage.Format_RGB888).rgbSwapped()
                        self.pix = QtGui.QPixmap.fromImage(self.img)
            except:
                pass
            time.sleep(self.frequency)

    def setFrame(self):
        try:
            self.videoFrame.setPixmap(self.pix)
        except:
            pass

    def getVideoWindowLayout(self):
        return self.layout
    
class VideoStreamWidget(QtGui.QWidget):
    def __init__(self, parent=None):
        super(VideoStreamWidget, self).__init__(parent)
        
        self.videoWindow = VideoWindow()

        self.startButton = QtGui.QPushButton('Start')
        self.startButton.clicked.connect(self.videoWindow.startCapture)
        self.pauseButton = QtGui.QPushButton('Pause')
        self.pauseButton.clicked.connect(self.videoWindow.pauseCapture)
        self.stopButton = QtGui.QPushButton('Stop')
        self.stopButton.clicked.connect(self.videoWindow.stopCapture)

        self.layout = QtGui.QGridLayout()
        self.buttonLayout = QtGui.QHBoxLayout()
        self.buttonLayout.addWidget(self.startButton)
        self.buttonLayout.addWidget(self.pauseButton)
        self.buttonLayout.addWidget(self.stopButton)

        self.layout.addLayout(self.buttonLayout,0,0)
        self.layout.addWidget(self.videoWindow,1,0)

    def getVideoDisplayLayout(self):
        return self.layout

    def openNetworkStream(self):
        self.videoWindow.openNetworkStream()

    def loadVideoFile(self):
        self.videoWindow.loadVideoFile()

app = QtGui.QApplication([])
app.setStyle(QtGui.QStyleFactory.create("Cleanlooks"))
mw = QtGui.QMainWindow()
mw.setWindowTitle('Video Stream Widget')

cw = QtGui.QWidget()
ml = QtGui.QGridLayout()
cw.setLayout(ml)
mw.setCentralWidget(cw)

videoStreamWidget = VideoStreamWidget()

mb = mw.menuBar()
mediaMenu = mb.addMenu('&Media')

openNetworkStreamAction = QtGui.QAction('Open Network Stream', mw)
openNetworkStreamAction.setShortcut('Ctrl+N')
openNetworkStreamAction.setStatusTip('Input video stream link')
openNetworkStreamAction.triggered.connect(videoStreamWidget.openNetworkStream)
mediaMenu.addAction(openNetworkStreamAction)

openMediaFileAction = QtGui.QAction('Open Media File', mw)
openMediaFileAction.setShortcut('Ctrl+O')
openMediaFileAction.setStatusTip('Open media file')
openMediaFileAction.triggered.connect(videoStreamWidget.loadVideoFile)
mediaMenu.addAction(openMediaFileAction)

ml.addLayout(videoStreamWidget.getVideoDisplayLayout(),0,0)

mw.show()

if __name__ == '__main__':
    if(sys.flags.interactive != 1) or not hasattr(QtCore, 'PYQT_VERSION'):
        QtGui.QApplication.instance().exec_()

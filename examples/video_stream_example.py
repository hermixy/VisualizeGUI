import numpy as np
from PyQt4 import QtCore, QtGui 
import cv2
import argparse
import imutils
from threading import Thread
from time import sleep
import sys
import pyqtgraph as pg

class VideoStreamWidget(QtGui.QWidget):
    def __init__(self, parent=None):
        super(VideoStreamWidget, self).__init__(parent)

        self.capture = None
        self.videoFileName = None
        self.isVideoFileOrStreamLoaded = False
        self.buttonSize = 75
        self.pause = True
        self.image_width = 400
        self.image_height = 400
        
        self.layout = QtGui.QGridLayout()
        self.startButton = QtGui.QPushButton('Start')
        self.startButton.clicked.connect(self.startCapture)
        self.startButton.setFixedWidth(self.buttonSize)
        self.pauseButton = QtGui.QPushButton('Pause')
        self.pauseButton.clicked.connect(self.pauseCapture)
        self.pauseButton.setFixedWidth(self.buttonSize)
        self.stopButton = QtGui.QPushButton('Stop')
        self.stopButton.clicked.connect(self.stopCapture)
        self.stopButton.setFixedWidth(self.buttonSize)

        self.buttonLayout = QtGui.QHBoxLayout()
        self.buttonLayout.addWidget(self.startButton)
        self.buttonLayout.addWidget(self.pauseButton)
        self.buttonLayout.addWidget(self.stopButton)

        self.layout.addLayout(self.buttonLayout,0,0)

        self.videoFrame = QtGui.QLabel()
        self.layout.addWidget(self.videoFrame,1,0)
        
        self.placeholder_image = cv2.imread('placeholder.PNG')

        self.placeholder_image = imutils.resize(self.placeholder_image, width=min(self.image_width, self.placeholder_image.shape[1]))
        #self.placeholder_image = imutils.resize(self.placeholder_image, width=self.image_width, height=self.image_height)
        #self.placeholder_image = cv2.resize(self.placeholder_image, (self.image_width, self.image_height))
        self.placeholder_image = QtGui.QImage(self.placeholder_image, self.placeholder_image.shape[1], self.placeholder_image.shape[0], QtGui.QImage.Format_RGB888).rgbSwapped()
        self.placeholder_image = QtGui.QPixmap.fromImage(self.placeholder_image)
        self.videoFrame.setPixmap(self.placeholder_image)

        self.timer = QtCore.QTimer()
        self.timer.timeout.connect(self.getFrame)

    def getVideoDisplayLayout(self):
        return self.layout
    
    def loadVideoFile(self):
        try:
            self.videoFileName = QtGui.QFileDialog.getOpenFileName(self, 'Select .h264 Video File')
            if self.videoFileName:
                self.isVideoFileOrStreamLoaded = True
                self.pause = False
                self.capture = cv2.VideoCapture(str(self.videoFileName))
        except:
            print("Please select a .h264 file")

    def startCapture(self):
        if self.isVideoFileOrStreamLoaded:
            self.pause = False
            self.timer.start(10)

    def getFrame(self):
        if not self.pause and self.capture.isOpened():
            status, frame = self.capture.read()
            if frame is not None:
                frame = imutils.resize(frame, width=min(self.image_width, frame.shape[1]))
                #frame = imutils.resize(frame, width=self.image_width, height=self.image_height)
                #frame = cv2.resize(frame, (self.image_width, self.image_height))
                img = QtGui.QImage(frame, frame.shape[1], frame.shape[0], QtGui.QImage.Format_RGB888).rgbSwapped()
                pix = QtGui.QPixmap.fromImage(img)
                self.videoFrame.setPixmap(pix)
            # Reached end of file so stop timer and pause video
            else:
                self.pauseCapture()

    def pauseCapture(self):
        if not self.pause:
            self.pause = True
            self.timer.stop()

    def stopCapture(self):
        self.pauseCapture()
        self.capture = cv2.VideoCapture(str(self.videoFileName))
        self.videoFrame.setPixmap(self.placeholder_image)

    def verifyNetworkStream(self, link):
        cap = cv2.VideoCapture(link)
        if cap is None or not cap.isOpened():
            print('Warning: unable to open video link')
            return False
        return True

    def openNetworkStream(self):
        text, okPressed = QtGui.QInputDialog.getText(self, "Open Media", "Please enter a network URL:")
        link = str(text)
        if okPressed and self.verifyNetworkStream(link):
            self.isVideoFileOrStreamLoaded = True
            self.pause = False
            self.capture = cv2.VideoCapture(link)

app = QtGui.QApplication([])
app.setStyle(QtGui.QStyleFactory.create("Cleanlooks"))
mw = QtGui.QMainWindow()
mw.setWindowTitle('Stream')

videoStream = VideoStreamWidget()
mb = mw.menuBar()
mediaMenu = mb.addMenu('&Media')

#QtGui.QApplication.setOverrideCursor(QtCore.Qt.CrossCursor)
openNetworkStreamAction = QtGui.QAction('Open Network Stream', mw)
openNetworkStreamAction.setShortcut('Ctrl+N')
openNetworkStreamAction.setStatusTip('Input video stream link')
openNetworkStreamAction.triggered.connect(videoStream.openNetworkStream)
mediaMenu.addAction(openNetworkStreamAction)

openMediaFileAction = QtGui.QAction('Open Media File', mw)
openMediaFileAction.setShortcut('Ctrl+O')
openMediaFileAction.setStatusTip('Open media file')
openMediaFileAction.triggered.connect(videoStream.loadVideoFile)
mediaMenu.addAction(openMediaFileAction)

cw = QtGui.QWidget()
ml = QtGui.QGridLayout()
cw.setLayout(ml)
mw.setCentralWidget(cw)

ml.addLayout(videoStream.getVideoDisplayLayout(),0,0)

mw.show()

if __name__ == '__main__':
    if(sys.flags.interactive != 1) or not hasattr(QtCore, 'PYQT_VERSION'):
        QtGui.QApplication.instance().exec_()


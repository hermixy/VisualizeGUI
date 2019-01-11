from PyQt4 import QtCore, QtGui
import numpy as np
import cv2
import random
import imutils
import pyqtgraph as pg
import sys

class VideoWindow(QtGui.QWidget):
    def __init__(self, parent=None):
        super(VideoWindow, self).__init__(parent)

        self.capture = None
        self.videoFileName = None
        self.isVideoFileOrStreamLoaded = False
        self.pause = True
        self.minWindowWidth = 300 

        self.videoFrame = QtGui.QLabel()
        
        self.layout = QtGui.QGridLayout()
        self.layout.addWidget(self.videoFrame,0,0)

        self.initPlaceholderImage()
        self.setLayout(self.layout)

        self.timer = QtCore.QTimer()
        self.timer.timeout.connect(self.getFrame)
    
    def initPlaceholderImage(self):
        self.placeholder_image = cv2.imread('placeholder.PNG')
        # Maintain aspect ratio
        self.placeholder_image = imutils.resize(self.placeholder_image, width=self.minWindowWidth)
        self.image_width = self.placeholder_image.shape[1]
        self.image_height = self.placeholder_image.shape[0]

        self.placeholder_image = QtGui.QImage(self.placeholder_image, self.placeholder_image.shape[1], self.placeholder_image.shape[0], QtGui.QImage.Format_RGB888).rgbSwapped()
        self.placeholder_image = QtGui.QPixmap.fromImage(self.placeholder_image)
        self.videoFrame.setPixmap(self.placeholder_image)

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
                frame = imutils.resize(frame, width=self.image_width)
                #print(frame.shape[1], frame.shape[0])
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

cw = QtGui.QWidget()
ml = QtGui.QGridLayout()
cw.setLayout(ml)
mw.setCentralWidget(cw)

ml.addLayout(videoStreamWidget.getVideoDisplayLayout(),0,0)

mw.show()

if __name__ == '__main__':
    if(sys.flags.interactive != 1) or not hasattr(QtCore, 'PYQT_VERSION'):
        QtGui.QApplication.instance().exec_()

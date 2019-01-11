from PyQt4 import QtCore, QtGui
import numpy as np
import cv2
import random
import imutils
import pyqtgraph as pg
import sys

class CrosshairWidget(QtGui.QWidget):
    def __init__(self, parent=None):
        super(CrosshairWidget, self).__init__(parent)
        
        # Create the crosshair (invisible plot)
        self.crosshairPlot = pg.PlotWidget()
        self.crosshairPlot.setBackground(background=None)

        self.crosshairPlot.plotItem.hideAxis('bottom') 
        self.crosshairPlot.plotItem.hideAxis('left') 
        self.crosshairPlot.plotItem.hideAxis('right') 
        self.crosshairPlot.plotItem.hideAxis('top')
        self.crosshairPlot.plotItem.setMouseEnabled(x=False, y=False)

        self.crosshairColor = (196,220,255)

        self.layout = QtGui.QGridLayout()
        self.layout.addWidget(self.crosshairPlot)
       
        # Create the crosshair
        self.crosshairPlot.plotItem.setAutoVisible(y=True)
        self.vLine = pg.InfiniteLine(angle=90)
        self.hLine = pg.InfiniteLine(angle=0, movable=False)
        self.vLine.setPen(self.crosshairColor)
        self.hLine.setPen(self.crosshairColor)
        self.crosshairPlot.setAutoVisible(y=True)
        self.crosshairPlot.addItem(self.vLine, ignoreBounds=True)
        self.crosshairPlot.addItem(self.hLine, ignoreBounds=True)
        
        # Update crosshair
        self.crosshairUpdate = pg.SignalProxy(self.crosshairPlot.scene().sigMouseMoved, rateLimit=60, slot=self.updateCrosshair)
        
    def updateCrosshair(self, event):
        coordinates = event[0]  
        if self.crosshairPlot.sceneBoundingRect().contains(coordinates):
            mousePoint = self.crosshairPlot.plotItem.vb.mapSceneToView(coordinates)
            index = mousePoint.x()
            print(mousePoint.x(), mousePoint.y())
            #self.crosshairPlot.setTitle("<span style='font-size: 12pt'>x=%0.1f,   <span style='color: red'>y=%0.1f</span>" % (mousePoint.x(), mousePoint.y()))
            #print(mousePoint.x(), mousePoint.y())
            self.vLine.setPos(mousePoint.x())
            self.hLine.setPos(mousePoint.y())

    def getCrosshairLayout(self):
        return self.layout

class Overlay(QtGui.QWidget):
    def __init__(self, parent):
        super(Overlay, self).__init__(parent)
        # Make any widgets in the container have a transparent background
        palette = QtGui.QPalette(self.palette())
        palette.setColor(palette.Background, QtCore.Qt.transparent)
        self.setPalette(palette)
        
        self.crosshair = CrosshairWidget()

        self.layout = QtGui.QGridLayout()
        self.layout.addLayout(self.crosshair.getCrosshairLayout(),1,0)
        self.setLayout(self.layout)

    # Make overlay transparent but keep widgets
    def paintEvent(self, event):
        painter = QtGui.QPainter()
        painter.begin(self)
        painter.setRenderHint(QtGui.QPainter.Antialiasing)
        # Transparency settings for overlay (r,g,b,a)
        painter.fillRect(event.rect(), QtGui.QBrush(QtGui.QColor(0, 0, 0, 0)))
        painter.end()

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
        self.crosshairOverlay = Overlay(self)

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

    def showCrosshair(self):
        self.crosshairOverlay.show()

    def hideCrosshair(self):
        self.crosshairOverlay.hide()

    def resizeEvent(self, event):
        self.crosshairOverlay.resize(event.size())
        event.accept()

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
    def showCrosshair(self):
        self.videoWindow.showCrosshair()
    def hideCrosshair(self):
        self.videoWindow.hideCrosshair()
    
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

showCrosshairAction = QtGui.QAction('Show Crosshair', mw)
showCrosshairAction.setShortcut('Ctrl+S')
showCrosshairAction.setStatusTip('Show crosshair')
showCrosshairAction.triggered.connect(videoStreamWidget.showCrosshair)
mediaMenu.addAction(showCrosshairAction)

hideCrosshairAction = QtGui.QAction('Hide Crosshair', mw)
hideCrosshairAction.setShortcut('Ctrl+H')
hideCrosshairAction.setStatusTip('Hide crosshair')
hideCrosshairAction.triggered.connect(videoStreamWidget.hideCrosshair)
mediaMenu.addAction(hideCrosshairAction)

cw = QtGui.QWidget()
ml = QtGui.QGridLayout()
cw.setLayout(ml)
mw.setCentralWidget(cw)

ml.addLayout(videoStreamWidget.getVideoDisplayLayout(),0,0)

mw.show()

if __name__ == '__main__':
    if(sys.flags.interactive != 1) or not hasattr(QtCore, 'PYQT_VERSION'):
        QtGui.QApplication.instance().exec_()

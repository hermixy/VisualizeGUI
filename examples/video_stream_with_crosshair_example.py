from PyQt4 import QtCore, QtGui
from threading import Thread
import numpy as np
import cv2
import random
import imutils
import pyqtgraph as pg
import sys
import time

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
        self.crosshairUpdate = pg.SignalProxy(self.crosshairPlot.scene().sigMouseMoved, rateLimit=300, slot=self.updateCrosshair)
        
    def updateCrosshair(self, event):
        coordinates = event[0]  
        self.x = coordinates.x()
        self.y = coordinates.y()
        if self.crosshairPlot.sceneBoundingRect().contains(coordinates):
            mousePoint = self.crosshairPlot.plotItem.vb.mapSceneToView(coordinates)
            index = mousePoint.x()
            self.vLine.setPos(mousePoint.x())
            self.hLine.setPos(mousePoint.y())

    def getCrosshairLayout(self):
        return self.layout

    def getX(self):
        return self.x

    def getY(self):
        return self.y

class Overlay(QtGui.QWidget):
    def __init__(self, parent):
        super(Overlay, self).__init__(parent)

        # Make any widgets in the container have a transparent background
        self.palette = QtGui.QPalette(self.palette())
        self.palette.setColor(self.palette.Background, QtCore.Qt.transparent)
        self.setPalette(self.palette)
        
        self.crosshair = CrosshairWidget()

        self.layout = QtGui.QGridLayout()
        self.layout.addLayout(self.crosshair.getCrosshairLayout(),1,0)
        self.setLayout(self.layout)

    # Make overlay transparent but keep widgets
    def paintEvent(self, event):
        self.painter = QtGui.QPainter()
        self.painter.begin(self)
        self.painter.setRenderHint(QtGui.QPainter.Antialiasing)
        # Transparency settings for overlay (r,g,b,a)
        self.painter.fillRect(event.rect(), QtGui.QBrush(QtGui.QColor(0, 0, 0, 0)))
        self.painter.end()

    def getX(self):
        return self.crosshair.getX()

    def getY(self):
        return self.crosshair.getY()
        
class VideoWindow(QtGui.QWidget):
    def __init__(self, parent=None):
        super(VideoWindow, self).__init__(parent)

        self.capture = None
        self.videoFileName = None
        self.isVideoFileOrStreamLoaded = False
        self.pause = True
        self.minWindowWidth = 400
        self.minWindowHeight = 400

        self.offset = 9
        self.placeholder_image_file = 'placeholder1.PNG'

        self.frequency = .002
        self.timer_frequency = self.frequency * 1000

        self.videoFrame = QtGui.QLabel()
        
        self.layout = QtGui.QGridLayout()
        self.layout.addWidget(self.videoFrame,0,0)

        self.initPlaceholderImage()
        self.setLayout(self.layout)
        self.crosshairOverlay = Overlay(self)
        self.displayCrosshair = True

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

    def alignCrosshair(self):
        capture = cv2.VideoCapture(str(self.videoFileName))
        status, frame = capture.read()
        frame = imutils.resize(frame, width=self.minWindowWidth)
        self.resizedImageHeight = frame.shape[0]
        frameHeight = self.size().height()
        self.translate = (frameHeight - self.resizedImageHeight - (2 * self.offset))/2
    
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
                self.alignCrosshair()
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
            self.alignCrosshair()
            
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
    
    def showCrosshair(self):
        self.displayCrosshair = True
        self.crosshairOverlay.show()

    def hideCrosshair(self):
        self.displayCrosshair = False 
        self.crosshairOverlay.hide()

    def resizeEvent(self, event):
        self.crosshairOverlay.resize(event.size())
        event.accept()
        
    def mousePressEvent(self, QMouseEvent):
        if self.isVideoFileOrStreamLoaded and self.displayCrosshair:
            x = self.crosshairOverlay.getX() 
            y = self.crosshairOverlay.getY() - self.translate
            
            if x > 0 and x < self.minWindowWidth and y > 0 and y < self.resizedImageHeight:
                c = self.img.pixel(x,y)
                print(QtGui.QColor(c).getRgb())
        
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

ml.addLayout(videoStreamWidget.getVideoDisplayLayout(),0,0)

mw.show()

if __name__ == '__main__':
    if(sys.flags.interactive != 1) or not hasattr(QtCore, 'PYQT_VERSION'):
        QtGui.QApplication.instance().exec_()

import numpy as np
import pyqtgraph as pg
from PyQt4 import QtCore, QtGui
import random

# Example to create a PlotWidget graph with a crosshair
class CrosshairPlotWidget(QtGui.QWidget):
    def __init__(self, parent=None):
        super(CrosshairPlotWidget, self).__init__(parent)
        
        # Use for time.sleep (s)
        self.frequency = .025
        # Use for timer.timer (ms)
        self.timer_frequency = self.frequency * 1000

        self.left_x = -10
        self.right_x = 0
        self.x_axis = np.arange(self.left_x, self.right_x, self.frequency)
        self.buffer = int((abs(self.left_x) + abs(self.right_x))/self.frequency)
        self.data = []
       
        # Create the plot
        self.crosshairPlot = pg.PlotWidget()
        self.crosshairPlot.setXRange(self.left_x, self.right_x)
        self.crosshairPlot.setLabel('left', 'Value')
        self.crosshairPlot.setLabel('bottom', 'Time (s)')
        self.crosshairColor = (196,220,255)

        self.plot = self.crosshairPlot.plot()

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
        
        # Update plot
        self.start()

    def plotUpdater(self):
        # Change for desired data
        self.dataPoint = random.randint(1,101)
        if len(self.data) >= self.buffer:
            self.data.pop(0)
        self.data.append(float(self.dataPoint))
        self.plot.setData(self.x_axis[len(self.x_axis) - len(self.data):], self.data)

    def updateCrosshair(self, event):
        coordinates = event[0]  
        if self.crosshairPlot.sceneBoundingRect().contains(coordinates):
            mousePoint = self.crosshairPlot.plotItem.vb.mapSceneToView(coordinates)
            index = mousePoint.x()
            if index > self.left_x and index <= self.right_x:
                self.crosshairPlot.setTitle("<span style='font-size: 12pt'>x=%0.1f,   <span style='color: red'>y=%0.1f</span>" % (mousePoint.x(), mousePoint.y()))
            self.vLine.setPos(mousePoint.x())
            self.hLine.setPos(mousePoint.y())

    def start(self):
        self.timer = QtCore.QTimer()
        self.timer.timeout.connect(self.plotUpdater)
        self.timer.start(self.getTimerFrequency())

    def getCrosshairPlotLayout(self):
        return self.layout

    def getTimerFrequency(self):
        return self.timer_frequency

app = QtGui.QApplication([])
app.setStyle(QtGui.QStyleFactory.create("Cleanlooks"))
mw = QtGui.QMainWindow()
mw.setWindowTitle('Crosshair plot')

crosshairPlot = CrosshairPlotWidget()

cw = QtGui.QWidget()
ml = QtGui.QGridLayout()
cw.setLayout(ml)
mw.setCentralWidget(cw)

ml.addLayout(crosshairPlot.getCrosshairPlotLayout(),0,0)
mw.show()

## Start Qt event loop unless running in interactive mode or using pyside.
if __name__ == '__main__':
    import sys
    if (sys.flags.interactive != 1) or not hasattr(QtCore, 'PYQT_VERSION'):
        QtGui.QApplication.instance().exec_()


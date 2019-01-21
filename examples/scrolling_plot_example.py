from PyQt4 import QtCore, QtGui
import pyqtgraph as pg
import random
import numpy as np
import sys
import time
from threading import Thread

# Scrolling plot widget with adjustable X-axis and dynamic Y-axis
class ScrollingPlot(QtGui.QWidget):
    def __init__(self, parent=None):
        super(ScrollingPlot, self).__init__(parent)
        
        # Desired Frequency (Hz) = 1 / self.FREQUENCY
        # USE FOR TIME.SLEEP (s)
        self.FREQUENCY = .004

        # Frequency to update plot (ms)
        # USE FOR TIMER.TIMER (ms)
        self.TIMER_FREQUENCY = self.FREQUENCY * 1000

        # Set X Axis range. If desired is [-10,0] then set LEFT_X = -10 and RIGHT_X = 0
        self.LEFT_X = -10
        self.RIGHT_X = 0
        self.X_Axis = np.arange(self.LEFT_X, self.RIGHT_X, self.FREQUENCY)
        self.buffer = int((abs(self.LEFT_X) + abs(self.RIGHT_X))/self.FREQUENCY)
        self.data = [] 

        # Create Plot Widget 
        self.plot = pg.PlotWidget()

        # Enable/disable plot squeeze (Fixed axis movement)
        self.plot.plotItem.setMouseEnabled(x=False, y=False)
        self.plot.setXRange(self.LEFT_X, self.RIGHT_X)
        self.plot.setTitle('Scrolling Plot Example')
        self.plot.setLabel('left', 'Value')
        self.plot.setLabel('bottom', 'Time (s)')

        self.plotter = self.plot.plot()
        self.plotter.setPen(197,235,255)

        self.layout = QtGui.QGridLayout()
        self.layout.addWidget(self.plot)

        self.readPositionThread()
        self.start()

    # Update plot
    def start(self):
        self.positionUpdateTimer = QtCore.QTimer()
        self.positionUpdateTimer.timeout.connect(self.plotUpdater)
        self.positionUpdateTimer.start(self.getScrollingPlotTimerFrequency())
    
    # Read in data using a thread
    def readPositionThread(self):
        self.currentPositionValue = 0
        self.oldCurrentPositionValue = 0
        self.positionUpdateThread = Thread(target=self.readPosition, args=())
        self.positionUpdateThread.daemon = True
        self.positionUpdateThread.start()

    def readPosition(self):
        frequency = self.getScrollingPlotFrequency()
        while True:
            try:
                # Add data
                self.currentPositionValue = random.randint(1,101) 
                self.oldCurrentPositionValue = self.currentPositionValue
                time.sleep(frequency)
            except:
                self.currentPositionValue = self.oldCurrentPositionValue

    def plotUpdater(self):
        self.dataPoint = float(self.currentPositionValue)

        if len(self.data) >= self.buffer:
            self.data.pop(0)
        self.data.append(self.dataPoint)
        self.plotter.setData(self.X_Axis[len(self.X_Axis) - len(self.data):], self.data)

    def clearScrollingPlot(self):
        self.data = []

    def getScrollingPlotFrequency(self):
        return self.FREQUENCY
    
    def getScrollingPlotTimerFrequency(self):
        return self.TIMER_FREQUENCY

    def getScrollingPlotLayout(self):
        return self.layout

    def getCurrentPositionValue(self):
        return self.currentPositionValue

    def getScrollingPlotWidget(self):
        return self.plot

# Create main application window
app = QtGui.QApplication([])
app.setStyle(QtGui.QStyleFactory.create("Cleanlooks"))
mw = QtGui.QMainWindow()
mw.setWindowTitle('Scrolling Plot Example')

# Create scrolling plot
plot = ScrollingPlot()

# Create and set widget layout
# Main widget container
cw = QtGui.QWidget()
ml = QtGui.QGridLayout()
cw.setLayout(ml)
mw.setCentralWidget(cw)

# Can use either to add plot to main layout
#ml.addWidget(plot.getScrollingPlotWidget(),0,0)
ml.addLayout(plot.getScrollingPlotLayout(),0,0)
mw.show()

## Start Qt event loop unless running in interactive mode or using pyside.
if __name__ == '__main__':
    import sys
    if (sys.flags.interactive != 1) or not hasattr(QtCore, 'PYQT_VERSION'):
        QtGui.QApplication.instance().exec_()


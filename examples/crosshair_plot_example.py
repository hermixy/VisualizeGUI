from PyQt4 import QtCore, QtGui
import sys
sys.path.append('../')
from widgets import CrosshairPlotWidget 

"""Crosshair Plot Widget Example"""

# Create main application window
app = QtGui.QApplication([])
app.setStyle(QtGui.QStyleFactory.create("Cleanlooks"))
mw = QtGui.QMainWindow()
mw.setWindowTitle('Crosshair Plot Example')

# Create and set widget layout
# Main widget container
cw = QtGui.QWidget()
ml = QtGui.QGridLayout()
cw.setLayout(ml)
mw.setCentralWidget(cw)

# Create crosshair plot
crosshair_plot = CrosshairPlotWidget()

ml.addLayout(crosshair_plot.get_crosshair_plot_layout(),0,0)

mw.show()

## Start Qt event loop unless running in interactive mode or using pyside.
if __name__ == '__main__':
    import sys
    if (sys.flags.interactive != 1) or not hasattr(QtCore, 'PYQT_VERSION'):
        QtGui.QApplication.instance().exec_()


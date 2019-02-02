from PyQt4 import QtCore, QtGui 
from widgets import UniversalPlotWidget
import sys

if __name__ == '__main__':

    # Create main application window
    app = QtGui.QApplication([])
    app.setStyle(QtGui.QStyleFactory.create("Cleanlooks"))
    mw = QtGui.QMainWindow()
    mw.setWindowTitle('Universal Plot GUI')

    # Initialize status_bar
    status_bar = QtGui.QStatusBar()
    mw.setStatusBar(status_bar)
    status_bar.setSizeGripEnabled(False)
    
    # Create universal plot widget
    universal_plot_widget = UniversalPlotWidget()

    # Create and set widget layout
    # Main widget container
    cw = QtGui.QWidget()
    ml = QtGui.QGridLayout()
    cw.setLayout(ml)
    mw.setCentralWidget(cw)

    ml.addLayout(universal_plot_widget.get_universal_plot_layout(),0,0)

    mw.statusBar()
    mw.show()

    if(sys.flags.interactive != 1) or not hasattr(QtCore, 'PYQT_VERSION'):
        QtGui.QApplication.instance().exec_()

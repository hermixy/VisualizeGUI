import sys
from PyQt4 import QtGui, QtCore

class LCDDisplayWidget(QtGui.QWidget):
    def __init__(self, parent=None):
        super(LCDDisplayWidget, self).__init__(parent)
        
        self.setWindowTitle('LCD Display w/ Slider Example')

        self.LCD = QtGui.QLCDNumber(self)
        self.LCD.setFixedSize(400,250)
        self.slider = QtGui.QSlider(QtCore.Qt.Horizontal, self)

        self.layout = QtGui.QVBoxLayout()
        self.layout.addWidget(self.LCD)
        self.layout.addWidget(self.slider)

        self.slider.valueChanged.connect(self.LCD.display)
        
    def getLCDDisplayLayout(self):
        return self.layout

app = QtGui.QApplication([])
app.setStyle(QtGui.QStyleFactory.create("Cleanlooks"))
mw = QtGui.QMainWindow()
mw.setWindowTitle('LCD Display w/ Slider Example')

cw = QtGui.QWidget()
ml = QtGui.QGridLayout()
cw.setLayout(ml)
mw.setCentralWidget(cw)

LCDDisplay = LCDDisplayWidget()

ml.addLayout(LCDDisplay.getLCDDisplayLayout(),0,0)

mw.show()

if __name__ == '__main__':
    if(sys.flags.interactive != 1) or not hasattr(QtCore, 'PYQT_VERSION'):
        QtGui.QApplication.instance().exec_()


from PyQt4 import QtGui, QtCore
import sys
sys.path.append('../')
from load_CSS import load_CSS

"""LCD Display Widget"""

class LCDDisplayWidget(QtGui.QWidget):
    def __init__(self, parent=None):
        super(LCDDisplayWidget, self).__init__(parent)
        
        self.setWindowTitle('LCD Display w/ Slider Example')

        self.LCD = QtGui.QLCDNumber(self)
        self.LCD.setFixedSize(400,250)
        self.slider = QtGui.QSlider(QtCore.Qt.Horizontal, self)
        self.slider.setMinimum(10)
        self.slider.setMaximum(200)
        self.slider.setValue(100)
        self.slider.setTickPosition(QtGui.QSlider.TicksBelow)
        self.slider.setSingleStep(5)

        self.layout = QtGui.QVBoxLayout()
        self.layout.addWidget(self.LCD)
        self.layout.addWidget(self.slider)

        self.slider.valueChanged.connect(self.LCD.display)
        
    def get_LCD_display_layout(self):
        return self.layout

# Create main application window
app = QtGui.QApplication([])
app.setStyleSheet(load_CSS(0))
app.setStyle(QtGui.QStyleFactory.create("Cleanlooks"))
mw = QtGui.QMainWindow()
mw.setWindowTitle('LCD Display w/ Slider Example')

# Create and set widget layout
# Main widget container
cw = QtGui.QWidget()
ml = QtGui.QGridLayout()
cw.setLayout(ml)
mw.setCentralWidget(cw)

# Create LCD Display Widget
LCD_display = LCDDisplayWidget()

ml.addLayout(LCD_display.get_LCD_display_layout(),0,0)

mw.show()

if __name__ == '__main__':
    if(sys.flags.interactive != 1) or not hasattr(QtCore, 'PYQT_VERSION'):
        QtGui.QApplication.instance().exec_()


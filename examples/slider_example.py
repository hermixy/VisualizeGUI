import sys
from PyQt4 import QtGui, QtCore

class SliderWidget(QtGui.QWidget):
    def __init__(self, parent=None):
        super(SliderWidget, self).__init__(parent)
        
        self.slider = QtGui.QSlider(QtCore.Qt.Horizontal, self)
        self.slider.setFocusPolicy(QtCore.Qt.NoFocus)
        self.slider.valueChanged[int].connect(self.changeValue)
        
    def changeValue(self, value):
        if value == 0:
            print('Zero')
        elif value > 0 and value <= 30:
            print('Small')
        elif value > 30 and value < 80:
            print('Medium')
        else:
            print('Large')
 
app = QtGui.QApplication([])
app.setStyle(QtGui.QStyleFactory.create("Cleanlooks"))
mw = QtGui.QMainWindow()
mw.setWindowTitle('Slider Example')

cw = QtGui.QWidget()
ml = QtGui.QGridLayout()
cw.setLayout(ml)
mw.setCentralWidget(cw)

slider = SliderWidget()

ml.addWidget(slider,0,0)

mw.show()

if __name__ == '__main__':
    if(sys.flags.interactive != 1) or not hasattr(QtCore, 'PYQT_VERSION'):
        QtGui.QApplication.instance().exec_()


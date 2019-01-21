import sys
from PyQt4 import QtGui, QtCore

class displayImageWidget(QtGui.QWidget):
    def __init__(self, parent=None):
        super(displayImageWidget, self).__init__(parent)
        
        self.image = QtGui.QPixmap("../doc/placeholder5.PNG")
        self.label = QtGui.QLabel(self)
        self.label.setPixmap(self.image)

        self.layout = QtGui.QHBoxLayout(self)
        self.layout.addWidget(self.label)

app = QtGui.QApplication([])
app.setStyle(QtGui.QStyleFactory.create("Cleanlooks"))
mw = QtGui.QMainWindow()
mw.setWindowTitle('Display Image Example')

cw = QtGui.QWidget()
ml = QtGui.QGridLayout()
cw.setLayout(ml)
mw.setCentralWidget(cw)

displayImage = displayImageWidget()

ml.addWidget(displayImage,0,0)

mw.show()

if __name__ == '__main__':
    if(sys.flags.interactive != 1) or not hasattr(QtCore, 'PYQT_VERSION'):
        QtGui.QApplication.instance().exec_()


import sys
from PyQt4 import QtGui, QtCore

class ProgessbarWidget(QtGui.QWidget):
    def __init__(self, parent=None):
        super(ProgessbarWidget, self).__init__(parent)
        
        self.progressBar = QtGui.QProgressBar(self)
        self.progressBar.setGeometry(30, 40, 200, 25)

        self.button = QtGui.QPushButton('Start', self)
        self.button.clicked.connect(self.toggleProgressbar)

        self.timer = QtCore.QBasicTimer()
        self.step = 0
        
        self.layout = QtGui.QGridLayout()
        self.layout.addWidget(self.progressBar,0,0)
        self.layout.addWidget(self.button,1,0)

    def timerEvent(self, e):
        if self.step >= 100:
            self.timer.stop()
            self.button.setText('Finished')
            return
            
        self.step = self.step + 1
        self.progressBar.setValue(self.step)

    def toggleProgressbar(self):
        if self.timer.isActive():
            self.timer.stop()
            self.button.setText('Start')
        else:
            self.timer.start(50,self)
            self.button.setText('Stop')
    def getProgressbarWidgetLayout(self):
        return self.layout

app = QtGui.QApplication([])
app.setStyle(QtGui.QStyleFactory.create("Cleanlooks"))
mw = QtGui.QMainWindow()
mw.setWindowTitle('LCD Display w/ Slider Example')

cw = QtGui.QWidget()
ml = QtGui.QGridLayout()
cw.setLayout(ml)
mw.setCentralWidget(cw)

progressBar = ProgessbarWidget()

ml.addLayout(progressBar.getProgressbarWidgetLayout(),0,0)

mw.show()

if __name__ == '__main__':
    if(sys.flags.interactive != 1) or not hasattr(QtCore, 'PYQT_VERSION'):
        QtGui.QApplication.instance().exec_()


from PyQt4 import QtGui, QtCore
import sys
sys.path.append('../')
from load_CSS import load_CSS

"""Progressbar Widget Example"""

class ProgessbarWidget(QtGui.QWidget):
    def __init__(self, parent=None):
        super(ProgessbarWidget, self).__init__(parent)
        
        self.progressbar = QtGui.QProgressBar(self)
        self.progressbar.setGeometry(30, 40, 200, 25)

        self.button = QtGui.QPushButton('Start', self)
        self.button.clicked.connect(self.toggle_progressbar)

        self.timer = QtCore.QBasicTimer()
        self.step = 0
        
        self.layout = QtGui.QGridLayout()
        self.layout.addWidget(self.progressbar,0,0)
        self.layout.addWidget(self.button,1,0)

    def timerEvent(self, e):
        if self.step >= 100:
            self.timer.stop()
            self.button.setText('Finished')
            return
            
        self.step = self.step + 1
        self.progressbar.setValue(self.step)

    def toggle_progressbar(self):
        if self.timer.isActive():
            self.timer.stop()
            self.button.setText('Start')
        else:
            self.timer.start(50,self)
            self.button.setText('Stop')

    def get_progressbar_widget_layout(self):
        return self.layout

if __name__ == '__main__':
    # Create main application window
    app = QtGui.QApplication([])
    app.setStyleSheet(load_CSS(0))
    app.setStyle(QtGui.QStyleFactory.create("Cleanlooks"))
    mw = QtGui.QMainWindow()
    mw.setWindowTitle('Progressbar Example')

    # Create and set widget layout
    # Main widget container
    cw = QtGui.QWidget()
    ml = QtGui.QGridLayout()
    cw.setLayout(ml)
    mw.setCentralWidget(cw)

    # Create progressbar Widget
    progressbar = ProgessbarWidget()

    ml.addLayout(progressbar.get_progressbar_widget_layout(),0,0)

    mw.show()

    if(sys.flags.interactive != 1) or not hasattr(QtCore, 'PYQT_VERSION'):
        QtGui.QApplication.instance().exec_()


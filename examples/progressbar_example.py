from PyQt4 import QtGui, QtCore
import sys

progressbar_style = """
    QProgressBar {
	border: 2px solid grey;
	border-radius: 5px;
	text-align: center;
    }

    QProgressBar::chunk{
        background-color: #05B8CC;
    }
"""
pushbutton_style = """
    QPushButton {
	border: 2px solid #8f8f91;
	border-radius: 6px;
	background-color: #5d84ae;
	min-width: 80px;
    }

    QPushButton:pressed {
	background-color: qlineargradient(x1: 0, y1: 0, x2: 0, y2: 1,stop: 0 #dadbde, stop: 1 #f6f7fa);
    }

    QPushButton:default {
	border-color: navy; /* make the default button prominent */
    }
"""

"""Progressbar Widget Example"""

class ProgessbarWidget(QtGui.QWidget):
    def __init__(self, parent=None):
        super(ProgessbarWidget, self).__init__(parent)
        
        self.progressbar = QtGui.QProgressBar(self)
        self.progressbar.setGeometry(30, 40, 200, 25)
        self.progressbar.setStyleSheet(progressbar_style)

        self.button = QtGui.QPushButton('Start', self)
	self.button.setStyleSheet(pushbutton_style)
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


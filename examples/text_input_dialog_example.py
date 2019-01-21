import sys
from PyQt4 import QtGui

class TextInputDialogWidget(QtGui.QWidget):
    def __init__(self, parent=None):
        super(TextInputDialogWidget, self).__init__(parent=None)
        
        self.button = QtGui.QPushButton('Open Dialog', self)
        self.button.clicked.connect(self.showDialog)
        self.button.setFixedSize(300,30)
        
        self.textWindow = QtGui.QLineEdit(self)

        self.layout = QtGui.QGridLayout()
        self.layout.addWidget(self.button,0,0,1,1)
        self.layout.addWidget(self.textWindow,1,0,1,1)
        
    def showDialog(self):
        text, ok = QtGui.QInputDialog.getText(self, 'Input Dialog', 
                'Enter text:')
        if ok:
            self.textWindow.setText(str(text))

    def getTextInputDialogWidgetLayout(self):
        return self.layout

app = QtGui.QApplication([])
app.setStyle(QtGui.QStyleFactory.create("Cleanlooks"))
mw = QtGui.QMainWindow()
mw.setWindowTitle('Text Input Dialog Example')

cw = QtGui.QWidget()
ml = QtGui.QGridLayout()
cw.setLayout(ml)
mw.setCentralWidget(cw)

textInputDialog = TextInputDialogWidget()

ml.addLayout(textInputDialog.getTextInputDialogWidgetLayout(),0,0)

mw.show()

if __name__ == '__main__':
    if(sys.flags.interactive != 1) or not hasattr(QtCore, 'PYQT_VERSION'):
        QtGui.QApplication.instance().exec_()


from PyQt4 import QtGui
import sys

"""Text Input Dialog Widget"""

class TextInputDialogWidget(QtGui.QWidget):
    def __init__(self, parent=None):
        super(TextInputDialogWidget, self).__init__(parent=None)
        
        self.button = QtGui.QPushButton('Open Dialog', self)
        self.button.clicked.connect(self.show_dialog)
        self.button.setFixedSize(300,30)
        
        self.text_window = QtGui.QLineEdit(self)

        self.layout = QtGui.QGridLayout()
        self.layout.addWidget(self.button,0,0,1,1)
        self.layout.addWidget(self.text_window,1,0,1,1)
        
    def show_dialog(self):
        text, ok = QtGui.QInputDialog.getText(self, 'Input Dialog', 
                'Enter text:')
        if ok:
            self.text_window.setText(str(text))

    def get_text_input_dialog_widget_layout(self):
        return self.layout

# Create main application window
app = QtGui.QApplication([])
app.setStyle(QtGui.QStyleFactory.create("Cleanlooks"))
mw = QtGui.QMainWindow()
mw.setWindowTitle('Text Input Dialog Example')

# Create and set widget layout
# Main widget container
cw = QtGui.QWidget()
ml = QtGui.QGridLayout()
cw.setLayout(ml)
mw.setCentralWidget(cw)

# Create text input widget
textInputDialog = TextInputDialogWidget()

ml.addLayout(textInputDialog.get_text_input_dialog_widget_layout(),0,0)

mw.show()

if __name__ == '__main__':
    if(sys.flags.interactive != 1) or not hasattr(QtCore, 'PYQT_VERSION'):
        QtGui.QApplication.instance().exec_()


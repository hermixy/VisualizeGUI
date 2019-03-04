from PyQt4 import QtGui, QtCore
import sys
sys.path.append('../')
from utility import ConvertImageBase64, placeholder_image

"""Display Image Widget"""

class DisplayImageWidget(QtGui.QWidget):
    def __init__(self, parent=None):
        super (DisplayImageWidget, self).__init__(parent)
        self.convert_image = ConvertImageBase64()

        self.placeholder = self.convert_image.decode_image_from_base64(placeholder_image)
        self.placeholder = QtGui.QImage(self.placeholder, 400, 400, QtGui.QImage.Format_RGB888).rgbSwapped()
        self.image = QtGui.QPixmap.fromImage(self.placeholder)
        self.label = QtGui.QLabel(self)
        self.label.setPixmap(self.image)

        self.layout = QtGui.QHBoxLayout(self)
        self.layout.addWidget(self.label)

if __name__ == '__main__':
    # Create main application window
    app = QtGui.QApplication([])
    app.setStyle(QtGui.QStyleFactory.create("Cleanlooks"))
    mw = QtGui.QMainWindow()
    mw.setWindowTitle('Display Image Example')

    # Create and set widget layout
    # Main widget container
    cw = QtGui.QWidget()
    ml = QtGui.QGridLayout()
    cw.setLayout(ml)
    mw.setCentralWidget(cw)

    # Create display image widget
    display_image_widget = DisplayImageWidget()

    ml.addWidget(display_image_widget,0,0)

    mw.show()

    if(sys.flags.interactive != 1) or not hasattr(QtCore, 'PYQT_VERSION'):
        QtGui.QApplication.instance().exec_()


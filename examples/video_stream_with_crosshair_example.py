from PyQt4 import QtCore, QtGui
import sys
sys.path.append('../')
from widgets import VideoStreamWidget

"""Video Stream Widget Example"""

# Create main application window
app = QtGui.QApplication([])
app.setStyle(QtGui.QStyleFactory.create("Cleanlooks"))
mw = QtGui.QMainWindow()
mw.setWindowTitle('Video Stream Widget')

# Create and set widget layout
# Main widget container
cw = QtGui.QWidget()
ml = QtGui.QGridLayout()
cw.setLayout(ml)
mw.setCentralWidget(cw)

# Create video widget
video_stream_widget = VideoStreamWidget()

# Create menubar
mb = mw.menuBar()
media_menu = mb.addMenu('&Media')

# Create toolbar
open_network_stream_action = QtGui.QAction('Open Network Stream', mw)
open_network_stream_action.setShortcut('Ctrl+N')
open_network_stream_action.setStatusTip('Input video stream link')
open_network_stream_action.triggered.connect(video_stream_widget.open_network_stream)
media_menu.addAction(open_network_stream_action)

open_media_file_action = QtGui.QAction('Open Media File', mw)
open_media_file_action.setShortcut('Ctrl+O')
open_media_file_action.setStatusTip('Open media file')
open_media_file_action.triggered.connect(video_stream_widget.load_video_file)
media_menu.addAction(open_media_file_action)

show_crosshair_action = QtGui.QAction('Show Crosshair', mw)
show_crosshair_action.setShortcut('Ctrl+S')
show_crosshair_action.setStatusTip('Show crosshair')
show_crosshair_action.triggered.connect(video_stream_widget.show_crosshair)
media_menu.addAction(show_crosshair_action)

hide_crosshair_action = QtGui.QAction('Hide Crosshair', mw)
hide_crosshair_action.setShortcut('Ctrl+H')
hide_crosshair_action.setStatusTip('Hide crosshair')
hide_crosshair_action.triggered.connect(video_stream_widget.hide_crosshair)
media_menu.addAction(hide_crosshair_action)

ml.addLayout(video_stream_widget.get_video_display_layout(),0,0)

mw.show()

if __name__ == '__main__':
    if(sys.flags.interactive != 1) or not hasattr(QtCore, 'PYQT_VERSION'):
        QtGui.QApplication.instance().exec_()


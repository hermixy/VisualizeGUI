from PyQt4 import QtCore, QtGui 
from widgets import PortSettingPopUpWidget
from widgets import ZMQPlotWidget 
import pyqtgraph as pg
import random
import zmq
import numpy as np
import sys

# Request/reply
parameter_limit_address = "tcp://192.168.30.125:6010"
# Pub/sub
position_address = "tcp://192.168.30.125:6011"
def positionUpdate():
    global currentPositionValue
    topic, currentPositionValue = position_socket.recv().split()
    currentPosition.setText(currentPositionValue)

def moveButtonPressed():
    global parameter_socket
    parameter_socket.send("move 1 2 3")
    result = parameter_socket.recv()
    print("Move response is " + result)

def homeButtonPressed():
    global parameter_socket
    parameter_socket.send("home")
    result = parameter_socket.recv()
    print("Home response is " + result)

def addPresetSettings():
    name = str(presetName.text())
    p = str(position.text())
    v = str(velocity.text())
    a = str(acceleration.text())
    if not name:
        return
    if not p or not v or not a:
        return
    if name not in presetTable:
        presets.addItem(name)
    presetTable[name] = {
            "position": p,
            "velocity": v,
            "acceleration": a 
            }
    index = presets.findText(name)
    presets.setCurrentIndex(index)
    presetName.clear()

# Update fields with choosen preset setting
def updatePresetSettings():
    name = str(presets.currentText()) 
    position.setText(presetTable[name]["position"])
    velocity.setText(presetTable[name]["velocity"])
    acceleration.setText(presetTable[name]["acceleration"])

def closeProgram():
    exit(1)

def changeIPPortSettings():
    global portIPAddress
    portIPAddress = PortSettingPopUpWidget()
    portIPAddress.setWindowTitle("IP/Port Settings")
    portIPAddress.setFixedSize(195,150)

    # Center popup relative to original GUI position
    point = portIPAddress.rect().center()
    globalPoint = portIPAddress.mapToGlobal(point)
    portIPAddress.move(globalPoint)

def initZMQHandshake():
    global velocityMin
    global velocityMax
    global accelerationMin
    global accelerationMax
    global positionMin
    global positionMax
    global homeFlag
    global units
    global parameter_socket
    global position_socket
    global parameter_limit_address
    global position_address

    parameter_context = zmq.Context()
    parameter_socket = parameter_context.socket(zmq.REQ)
    parameter_socket.connect(parameter_limit_address)
    parameter_socket.send("info?")
    parameter_information = [x.strip() for x in parameter_socket.recv().split(',')]

    print(parameter_information)
    velocityMin, velocityMax, accelerationMin, accelerationMax, positionMin, positionMax, homeFlag, units = parameter_information
    
    global currentPositionValue
    position_context = zmq.Context()
    position_socket = position_context.socket(zmq.SUB)
    position_socket.connect(position_address)
    position_socket.setsockopt(zmq.SUBSCRIBE, "10000")
    topic, currentPositionValue = position_socket.recv().split()

# Create main application window
app = QtGui.QApplication([])
app.setStyle(QtGui.QStyleFactory.create("Cleanlooks"))
mw = QtGui.QMainWindow()
mw.setWindowTitle('ZMQ Motor GUI')
initZMQHandshake()

# Create and set widget layout
cw = QtGui.QWidget()
mainLayout = QtGui.QVBoxLayout()
l = QtGui.QFormLayout()
mainLayout.addLayout(l)
mw.setCentralWidget(cw)
cw.setLayout(mainLayout)

# Menubar/Toolbar
mb = mw.menuBar()
fm = mb.addMenu('&File')

exitAction = QtGui.QAction('Exit', mw)
exitAction.setShortcut('Ctrl+Q')
exitAction.setStatusTip('Exit application')
exitAction.triggered.connect(QtGui.qApp.quit)
fm.addAction(exitAction)

moveAction = QtGui.QAction('Move', mw)
moveAction.setShortcut('Ctrl+M')
moveAction.setStatusTip('Move')
moveAction.triggered.connect(moveButtonPressed)
fm.addAction(moveAction)

homeAction = QtGui.QAction('Home', mw)
homeAction.setShortcut('Ctrl+H')
homeAction.setStatusTip('Home')
homeAction.triggered.connect(homeButtonPressed)
fm.addAction(homeAction)

addPresetAction = QtGui.QAction('Add Preset', mw)
addPresetAction.setShortcut('Ctrl+A')
addPresetAction.setStatusTip('Save current values into a preset setting')
addPresetAction.triggered.connect(addPresetSettings)
fm.addAction(addPresetAction)

# GUI elements
portSettings = QtGui.QPushButton('IP/Port Settings')
portSettings.clicked.connect(changeIPPortSettings)

position = QtGui.QLineEdit()
position.setValidator(QtGui.QIntValidator(int(positionMin), int(positionMax)))
position.setAlignment(QtCore.Qt.AlignLeft)

velocity = QtGui.QLineEdit()
velocity.setValidator(QtGui.QIntValidator(int(velocityMin), int(velocityMax)))
velocity.setAlignment(QtCore.Qt.AlignLeft)

acceleration = QtGui.QLineEdit()
acceleration.setValidator(QtGui.QIntValidator(int(accelerationMin), int(accelerationMax)))
acceleration.setAlignment(QtCore.Qt.AlignLeft)

currentPosition = QtGui.QLabel()
currentPosition.setText(currentPositionValue)

moveButton = QtGui.QPushButton('Move')
moveButton.clicked.connect(moveButtonPressed)

homeButton = QtGui.QPushButton('Home')
homeButton.clicked.connect(homeButtonPressed)

if homeFlag == 'false':
    homeButton.setEnabled(False)

presetTable = {}
presets = QtGui.QComboBox()
presets.activated.connect(updatePresetSettings)
presetName= QtGui.QLineEdit()
presetName.setPlaceholderText("Preset name")
presetButton = QtGui.QPushButton('Add Preset')
presetButton.clicked.connect(addPresetSettings)
presetLayout = QtGui.QHBoxLayout()
presetLayout.addWidget(presets)
presetLayout.addWidget(presetName)
presetLayout.addWidget(presetButton)

# Layout
l.addRow(portSettings)
l.addRow("Position (deg)", position)
l.addRow("Velocity (deg/s)", velocity)
l.addRow("Acceleration (deg/s^2)", acceleration)
l.addRow("Current Position", currentPosition)
l.addRow(moveButton)
l.addRow(homeButton)
l.addRow("Presets", presetLayout)

'''
# Shortcuts
closeProgramShortcut = QtGui.QShortcut(QtGui.QKeySequence("Ctrl+Q"), mw)
closeProgramShortcut.activated.connect(closeProgram)
homeButtonShortcut = QtGui.QShortcut(QtGui.QKeySequence("Ctrl+H"), mw)
homeButtonShortcut.activated.connect(homeButtonPressed)
moveButtonShortcut = QtGui.QShortcut(QtGui.QKeySequence("Ctrl+M"), mw)
moveButtonShortcut.activated.connect(moveButtonPressed)
'''
# Internal timers
timer = QtCore.QTimer()
timer.timeout.connect(positionUpdate)
timer.start(1000)

def updatePortIPAddress():
    global portIPAddress
    try:
        position_address = portIPAddress.getPositionAddress()
        if position_address:
            print(position_address)

        else:
            pass
    except NameError:
        pass
    
t = QtCore.QTimer()
t.timeout.connect(updatePortIPAddress)
t.start(1000)

mw.statusBar()
mw.show()

if __name__ == '__main__':
    if(sys.flags.interactive != 1) or not hasattr(QtCore, 'PYQT_VERSION'):
        QtGui.QApplication.instance().exec_()


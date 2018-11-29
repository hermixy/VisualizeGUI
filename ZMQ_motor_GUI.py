from PyQt4 import QtCore, QtGui 
from PyQt4.QtGui import QSizePolicy
from widgets import PortSettingPopUpWidget
from widgets import ZMQPlotWidget 
import pyqtgraph as pg
import random
import zmq
import numpy as np
import sys
from threading import Thread
import threading
import time

# Pub/sub
position_address = "tcp://192.168.1.125:6011"
position_topic = "10000"
old_position_address = position_address

# Request/reply
parameter_address = "tcp://192.168.1.125:6010"
old_parameter_address = parameter_address

# =====================================================================
# Update timer functions
# =====================================================================
def positionUpdate():
    global currentPositionValue
    global position_socket
    while True:
        try:
            topic, currentPositionValue = position_socket.recv(zmq.NOBLOCK).split()
            currentPosition.setText(currentPositionValue)
        except:
            pass
        time.sleep(.05)

# =====================================================================
# Button action functions
# =====================================================================
def moveButton():
    def threadMoveButton():
        global parameter_socket
        try:
            v = str(velocity.text())
            a = str(acceleration.text())
            p = str(position.text())
            if p and v and a:
                command = "move {} {} {}".format(v,a,p)
                parameter_socket.send(command)
                result = parameter_socket.recv()
                print("Move response is " + result)
            else:
                pass
        except zmq.ZMQError:
            # No data arrived
            pass
    Thread(target=threadMoveButton, args=()).start()

def homeButton():
    def threadHomeButton():
        global parameter_socket
        try:
            parameter_socket.send("home")
            result = parameter_socket.recv()
            print("Home response is " + result)
        except zmq.ZMQError:
            # No data arrived
            pass
    Thread(target=threadHomeButton, args=()).start()

def addPresetSettingsButton():
    name = str(presetName.text())
    v = str(velocity.text())
    a = str(acceleration.text())
    p = str(position.text())
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

def updateParameters(velocityMin, velocityMax, accelerationMin, accelerationMax, positionMin, positionMax):
    global position
    global velocity
    global acceleration
    position.clear()
    velocity.clear()
    acceleration.clear()
    position.setValidator(QtGui.QIntValidator(int(positionMin), int(positionMax)))
    velocity.setValidator(QtGui.QIntValidator(int(velocityMin), int(velocityMax)))
    acceleration.setValidator(QtGui.QIntValidator(int(accelerationMin), int(accelerationMax)))

def closeProgram():
    exit(1)

def changeIPPortSettings():
    global portAddress
    global statusBar
    
    statusBar.clearMessage()
    portAddress = PortSettingPopUpWidget("IP/Port Settings")

def initZMQHandshake():
    global velocityMin
    global velocityMax
    global accelerationMin
    global accelerationMax
    global positionMin
    global positionMax
    global homeFlag
    global units

    global position_socket
    global position_address
    global position_context

    global parameter_socket
    global parameter_address
    global parameter_context

    global currentPositionValue
    position_context = zmq.Context()
    position_socket = position_context.socket(zmq.SUB)
    position_socket.connect(position_address)
    position_socket.setsockopt(zmq.SUBSCRIBE, position_topic)
    topic, currentPositionValue = position_socket.recv().split()

    parameter_context = zmq.Context()
    parameter_socket = parameter_context.socket(zmq.REQ)
    parameter_socket.connect(parameter_address)
    parameter_socket.send("info?")
    parameter_information = [x.strip() for x in parameter_socket.recv().split(',')]

    print(parameter_information)
    velocityMin, velocityMax, accelerationMin, accelerationMax, positionMin, positionMax, homeFlag, units = parameter_information
    
# Create main application window
app = QtGui.QApplication([])
app.setStyle(QtGui.QStyleFactory.create("Cleanlooks"))
mw = QtGui.QMainWindow()
mw.setWindowTitle('ZMQ Motor GUI')
initZMQHandshake()
statusBar = QtGui.QStatusBar()
mw.setStatusBar(statusBar)
plot = ZMQPlotWidget()
plot.start()


# Create and set widget layout
cw = QtGui.QWidget()
mainLayout = QtGui.QHBoxLayout()
l = QtGui.QFormLayout()
mainLayout.addLayout(l)
mainLayout.addLayout(plot.getZMQLayout())
mw.setCentralWidget(cw)
cw.setLayout(mainLayout)
statusBar.setSizeGripEnabled(False)
#mw.setFixedSize(350, 275)
mw.setSizePolicy(QtGui.QSizePolicy.Fixed, QtGui.QSizePolicy.Fixed)
mw.setFixedSize(800,300)

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
moveAction.triggered.connect(moveButton)
fm.addAction(moveAction)

homeAction = QtGui.QAction('Home', mw)
homeAction.setShortcut('Ctrl+H')
homeAction.setStatusTip('Home')
homeAction.triggered.connect(homeButton)
fm.addAction(homeAction)

addPresetAction = QtGui.QAction('Add Preset', mw)
addPresetAction.setShortcut('Ctrl+A')
addPresetAction.setStatusTip('Save current values into a preset setting')
addPresetAction.triggered.connect(addPresetSettingsButton)
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

move = QtGui.QPushButton('Move')
move.clicked.connect(moveButton)

home = QtGui.QPushButton('Home')
home.clicked.connect(homeButton)

if homeFlag == 'false':
    home.setEnabled(False)

presetTable = {}
presets = QtGui.QComboBox()
presets.activated.connect(updatePresetSettings)
presetName = QtGui.QLineEdit()
presetName.setFixedWidth(80)
presetName.setPlaceholderText("Preset name")
presetButton = QtGui.QPushButton('Add Preset')
presetButton.clicked.connect(addPresetSettingsButton)
presetLayout = QtGui.QHBoxLayout()
presetLayout.addWidget(presets)
presetLayout.addWidget(presetName)
presetLayout.addWidget(presetButton)

# Layout
l.addRow(portSettings)
l.addRow("Velocity (deg/s)", velocity)
l.addRow("Acceleration (deg/s^2)", acceleration)
l.addRow("Position (deg)", position)
l.addRow("Current Position", currentPosition)
l.addRow(move)
l.addRow(home)
l.addRow("Presets", presetLayout)

# Internal timers
positionUpdateThread = Thread(target=positionUpdate, args=())
positionUpdateThread.setDaemon(True)
positionUpdateThread.start()

def positionPortAddressUpdate():
    global portAddress
    global position_address
    global position_context
    global position_topic
    global position_socket
    global old_position_address
    global statusBar
    try:
        raw_position_address = portAddress.getPositionAddress()
        # Already verified working address
        if raw_position_address and raw_position_address != '()':
            address, port, topic = raw_position_address
            position_address = "tcp://" + address + ":" + port
            # Different address from current settings
            if old_position_address != position_address:
                old_position_address = position_address
                position_topic = topic
                position_context = zmq.Context()
                position_socket = position_context.socket(zmq.SUB)
                position_socket.connect(position_address)
                position_socket.setsockopt(zmq.SUBSCRIBE, position_topic)
                statusBar.showMessage('Successfully connected to ' + position_address, 8000)
                portAddress.setPositionAddress("()")
            elif old_position_address == position_address:
                statusBar.showMessage('Already connected to ' + position_address, 8000)
        elif not raw_position_address and type(raw_position_address) is bool: 
            portAddress.setPositionAddress("()")
            statusBar.showMessage('Invalid position IP/Port settings!', 8000) 
        else:
            pass
    except NameError:
        pass

positionPortTimer = QtCore.QTimer()
positionPortTimer.timeout.connect(positionPortAddressUpdate)
positionPortTimer.start(1000)

def parameterPortAddressUpdate():
    global portAddress
    global parameter_address
    global parameter_context
    global parameter_socket
    global old_parameter_address
    global statusBar
    global velocityMin
    global velocityMax
    global accelerationMin
    global accelerationMax
    global positionMin
    global positionMax
    global homeFlag
    global units

    try:
        raw_parameter_address = portAddress.getParameterAddress()
        # Already verified working address
        if raw_parameter_address and raw_parameter_address != '()':
            address, port = raw_parameter_address
            parameter_address = "tcp://" + address + ":" + port
            # Different address from current settings
            if old_parameter_address != parameter_address:
                old_parameter_address = parameter_address
                parameter_context = zmq.Context()
                parameter_socket = parameter_context.socket(zmq.REQ)
                parameter_socket.connect(parameter_address)
                parameter_socket.send('info?')
                parameter_information = [x.strip() for x in parameter_socket.recv().split(',')]
                velocityMin, velocityMax, accelerationMin, accelerationMax, positionMin, positionMax, homeFlag, units = parameter_information
                updateParameters(velocityMin, velocityMax, accelerationMin, accelerationMax, positionMin, positionMax)

                statusBar.showMessage('Successfully connected to ' + parameter_address, 8000)
                portAddress.setParameterAddress("()")
            elif old_parameter_address == parameter_address:
                statusBar.showMessage('Already connected to ' + parameter_address, 8000)

        elif not raw_parameter_address and type(raw_parameter_address) is bool: 
            portAddress.setParameterAddress("()")
            statusBar.showMessage('Invalid parameter IP/Port settings!', 8000) 
        else:
            pass
    except NameError:
        pass

parameterPortTimer = QtCore.QTimer()
parameterPortTimer.timeout.connect(parameterPortAddressUpdate)
parameterPortTimer.start(1000)

def plotPortAddressUpdate():
    global portAddress
    global plot
    global statusBar
    try:
        raw_plot_address = portAddress.getPlotAddress()
        # Already verified working address
        if raw_plot_address and raw_plot_address != '()':
            address, port, topic = raw_plot_address
            plot_address = "tcp://" + address + ":" + port
            # Different address from current settings
            if plot.getZMQPlotAddress() != plot_address:
                plot.updateZMQPlotAddress(plot_address, topic)
                statusBar.showMessage('Successfully connected to ' + plot_address, 8000)
                portAddress.setPlotAddress("()")
            elif plot.getZMQPlotAddress() == plot_address:
                statusBar.showMessage('Already connected to ' + plot_address, 8000)
        elif not raw_plot_address and type(raw_plot_address) is bool: 
            portAddress.setPlotAddress("()")
            statusBar.showMessage('Invalid plot IP/Port settings!', 8000) 
        else:
            pass
    except NameError:
        pass

plotPortTimer = QtCore.QTimer()
plotPortTimer.timeout.connect(plotPortAddressUpdate)
plotPortTimer.start(plot.getZMQTimerFrequency())
mw.statusBar()
mw.show()

if __name__ == '__main__':
    if(sys.flags.interactive != 1) or not hasattr(QtCore, 'PYQT_VERSION'):
        QtGui.QApplication.instance().exec_()


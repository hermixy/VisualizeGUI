'''
Run servers: pubsub_server2.py for parameter/position changes (OPTIONAL)
             reqrep_server1.py for initial ZMQ Plot (REQUIRED)
             reqrep_server2.py for change ZMQ Plot ability (OPTIONAL)
             server1.py for rotational controller (REQUIRED)
'''
from PyQt4 import QtCore, QtGui 
from PyQt4.QtGui import QSizePolicy
from widgets import PortSettingPopUpWidget
from widgets import ZMQPlotWidget 
from widgets import RotationalControllerPlotWidget 
import pyqtgraph as pg
import random
import zmq
import numpy as np
import sys
from threading import Thread
import time

# Pub/sub
position_address = "tcp://192.168.1.125:6011"
position_topic = "10000"
old_position_address = position_address

# Request/reply
parameter_address = "tcp://192.168.1.125:6010"
old_parameter_address = parameter_address

# =====================================================================
# Button action functions
# =====================================================================

# Move rotational controller with selected values
def moveButton():
    def moveButtonThread():
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
    Thread(target=moveButtonThread, args=()).start()

# Resets rotational controller to default
def homeButton():
    def homeButtonThread():
        global parameter_socket
        try:
            parameter_socket.send("home")
            result = parameter_socket.recv()
            print("Home response is " + result)
        except zmq.ZMQError:
            # No data arrived
            pass
    Thread(target=homeButtonThread, args=()).start()

# Save current field values into a saved preset
def addPresetSettingsButton():
    def addPresetSettingsButtonThread():
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
    Thread(target=addPresetSettingsButtonThread, args=()).start()

# Change position, parameters, and plot IP/Port settings (TCP Address, Port, Topic)
def changeIPPortSettingsButton():
    global portAddress
    global statusBar
    
    statusBar.clearMessage()
    portAddress = PortSettingPopUpWidget("IP/Port Settings")

# =====================================================================
# Update timer and thread functions
# =====================================================================

# Current position update
def positionUpdate():
    global currentPositionValue
    global motorPlot

    currentPosition.setText(currentPositionValue)
    motorPlot.plotUpdater(currentPositionValue)

# Reads motor socket for current position 
def readPositionThread():
    global position_socket
    global currentPositionValue, oldCurrentPositionValue
    global motorPlot
    frequency = motorPlot.getRotationalControllerFrequency()
    while True:
        try:
            topic, currentPositionValue = position_socket.recv().split()
            # Change to 0 since Rotational controller reports 0 as -0
            if currentPositionValue == '-0.00':
                currentPositionValue = '0.00'
            oldCurrentPositionValue = currentPositionValue
        except:
            currentPositionValue = oldCurrentPositionValue
        time.sleep(frequency)

def positionPortAddressUpdate():
    global portAddress
    global position_address, position_context, position_topic, position_socket
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

def parameterPortAddressUpdate():
    global portAddress
    global parameter_address, parameter_context, parameter_socket
    global velocityMin, velocityMax, accelerationMin, accelerationMax, positionMin, positionMax, homeFlag, units
    global old_parameter_address
    global statusBar
    
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
                parametersUpdate(velocityMin, velocityMax, accelerationMin, accelerationMax, positionMin, positionMax)

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

# Update fields with selected preset setting
def presetSettingsUpdate():
    name = str(presets.currentText()) 
    position.setText(presetTable[name]["position"])
    velocity.setText(presetTable[name]["velocity"])
    acceleration.setText(presetTable[name]["acceleration"])

# Update the velocity, acceleration, and position min/max range (low,high) of input
def parametersUpdate(velocityMin, velocityMax, accelerationMin, accelerationMax, positionMin, positionMax):
    global position
    global velocity
    global acceleration
    position.clear()
    velocity.clear()
    acceleration.clear()
    position.setValidator(QtGui.QIntValidator(int(positionMin), int(positionMax)))
    velocity.setValidator(QtGui.QIntValidator(int(velocityMin), int(velocityMax)))
    acceleration.setValidator(QtGui.QIntValidator(int(accelerationMin), int(accelerationMax)))

# Initialize position and parameter ZMQ connections
def initZMQHandshake():
    global velocityMin, velocityMax, accelerationMin, accelerationMax, positionMin, positionMax, homeFlag, units
    global position_socket, position_address, position_context
    global parameter_socket, parameter_address, parameter_context
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

    velocityMin, velocityMax, accelerationMin, accelerationMax, positionMin, positionMax, homeFlag, units = parameter_information
   
# =====================================================================
# Main GUI Application
# =====================================================================

# Create main application window
app = QtGui.QApplication([])
app.setStyle(QtGui.QStyleFactory.create("Cleanlooks"))
mw = QtGui.QMainWindow()
mw.setWindowTitle('ZMQ Motor GUI')

# Initialize statusbar
statusBar = QtGui.QStatusBar()
mw.setStatusBar(statusBar)
statusBar.setSizeGripEnabled(False)

# Establish ZMQ socket connections 
initZMQHandshake()

# Create plots
#plot = ZMQPlotWidget()
#plot.start()
motorPlot = RotationalControllerPlotWidget()

# Create and set widget layout
# Main widget container
cw = QtGui.QWidget()
ml = QtGui.QGridLayout()
cw.setLayout(ml)
mw.setCentralWidget(cw)
l = QtGui.QGridLayout()

# Prevent window from being maximized
#mw.setFixedSize(cw.size())

# Enable zoom in for selected box region
pg.setConfigOption('leftButtonPan', False)

ml.addLayout(l,0,0)
#ml.addWidget(plot.getZMQPlotWidget(),1,0)
ml.addWidget(motorPlot.getRotationalControllerPlotWidget(),0,1)
mw.setSizePolicy(QtGui.QSizePolicy.Fixed, QtGui.QSizePolicy.Fixed)

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
portSettings.clicked.connect(changeIPPortSettingsButton)

velocityLabel = QtGui.QLabel()
velocityLabel.setText('Velocity (deg/s)')
velocity = QtGui.QLineEdit()
velocity.setValidator(QtGui.QIntValidator(int(velocityMin), int(velocityMax)))
velocity.setAlignment(QtCore.Qt.AlignLeft)

accelerationLabel = QtGui.QLabel()
accelerationLabel.setText('Acceleration (deg/s^2)')
acceleration = QtGui.QLineEdit()
acceleration.setValidator(QtGui.QIntValidator(int(accelerationMin), int(accelerationMax)))
acceleration.setAlignment(QtCore.Qt.AlignLeft)

positionLabel = QtGui.QLabel()
positionLabel.setText('Position (deg)')
position = QtGui.QLineEdit()
position.setValidator(QtGui.QIntValidator(int(positionMin), int(positionMax)))
position.setAlignment(QtCore.Qt.AlignLeft)

currentPositionLabel = QtGui.QLabel()
currentPositionLabel.setText('Current Position')
currentPosition = QtGui.QLabel()
currentPosition.setText(currentPositionValue)

move = QtGui.QPushButton('Move')
move.clicked.connect(moveButton)

home = QtGui.QPushButton('Home')
home.clicked.connect(homeButton)

# Disable home button if unavailable
if homeFlag == 'false':
    home.setEnabled(False)

presetTable = {}
presetLabel = QtGui.QLabel()
presetLabel.setText('Presets')
presets = QtGui.QComboBox()
presets.activated.connect(presetSettingsUpdate)
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
l.addWidget(portSettings,0,0,1,4)
l.addWidget(velocityLabel,1,0,1,2)
l.addWidget(velocity,1,2,1,2)
l.addWidget(accelerationLabel,2,0,1,2)
l.addWidget(acceleration,2,2,1,2)
l.addWidget(positionLabel,3,0,1,2)
l.addWidget(position,3,2,1,2)
l.addWidget(currentPositionLabel,4,0,1,2)

l.addWidget(currentPosition,4,2,1,2)
l.addWidget(move,5,0,1,4)
l.addWidget(home,6,0,1,4)
l.addWidget(presetLabel,7,0,1,1)
l.addWidget(presets,7,1,1,1)
l.addWidget(presetName,7,2,1,1)
l.addWidget(presetButton,7,3,1,1)

# Start internal timers and threads 
positionUpdateThread = Thread(target=readPositionThread, args=())
positionUpdateThread.daemon = True
positionUpdateThread.start() 

positionUpdateTimer = QtCore.QTimer()
positionUpdateTimer.timeout.connect(positionUpdate)
positionUpdateTimer.start(motorPlot.getRotationalControllerTimerFrequency())

positionPortAddressUpdateTimer = QtCore.QTimer()
positionPortAddressUpdateTimer.timeout.connect(positionPortAddressUpdate)
positionPortAddressUpdateTimer.start(1000)

parameterPortAddressUpdateTimer = QtCore.QTimer()
parameterPortAddressUpdateTimer.timeout.connect(parameterPortAddressUpdate)
parameterPortAddressUpdateTimer.start(1000)

plotPortAddressUpdateTimer = QtCore.QTimer()
plotPortAddressUpdateTimer.timeout.connect(plotPortAddressUpdate)
plotPortAddressUpdateTimer.start(1000)

mw.statusBar()
mw.show()

if __name__ == '__main__':
    if(sys.flags.interactive != 1) or not hasattr(QtCore, 'PYQT_VERSION'):
        QtGui.QApplication.instance().exec_()


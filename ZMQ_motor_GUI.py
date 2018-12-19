'''
Run servers: pubsub_server2.py for parameter/position changes (OPTIONAL)
             reqrep_server1.py for initial ZMQ Plot (REQUIRED)
             reqrep_server2.py for change ZMQ Plot ability (OPTIONAL)
             server1.py for rotational controller (REQUIRED) (switch for pubsub_server1.py)
'''
from PyQt4 import QtCore, QtGui 
from PyQt4.QtGui import QSizePolicy
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
position_address = "tcp://192.168.1.134:6011"
position_topic = "10000"
old_position_address = position_address

# Request/reply
parameter_address = "tcp://192.168.1.134:6010"
old_parameter_address = parameter_address

class PortSettingPopUpWidget(QtGui.QWidget):
    def __init__(self, windowTitle, parent=None):
        super(PortSettingPopUpWidget, self).__init__(parent)

        self.popUpWidth = 195
        self.popUpHeight = 150
        self.setFixedSize(self.popUpWidth, self.popUpHeight)

        self.setWindowTitle(windowTitle)
        self.parameter_address = ()
        self.plot_address = ()
        self.tabs = QtGui.QTabWidget(self)
        self.positionTab = QtGui.QWidget()
        self.parameterTab = QtGui.QWidget()
        self.plotTab = QtGui.QWidget()

        # Position
        self.positionLayout = QtGui.QFormLayout()
        self.position_TCPAddress = QtGui.QLineEdit()
        self.position_TCPAddress.setMaxLength(15)
        self.position_TCPPort = QtGui.QLineEdit()
        self.position_TCPPort.setValidator(QtGui.QIntValidator())
        self.position_TCPTopic = QtGui.QLineEdit()
        self.position_TCPTopic.setValidator(QtGui.QIntValidator())
        self.positionButtonLayout = QtGui.QHBoxLayout()
        self.positionConnectButton = QtGui.QPushButton('Connect')
        self.positionConnectButton.setStyleSheet('background-color: #3CB371')
        self.positionConnectButton.clicked.connect(self.position_saveButton)
        self.positionCancelButton = QtGui.QPushButton('Cancel')
        self.positionCancelButton.clicked.connect(self.position_cancelButton)
        self.positionButtonLayout.addWidget(self.positionConnectButton)
        self.positionButtonLayout.addWidget(self.positionCancelButton)

        self.positionLayout.addRow("TCP Address", self.position_TCPAddress)
        self.positionLayout.addRow("Port", self.position_TCPPort)
        self.positionLayout.addRow("Topic", self.position_TCPTopic)
        self.positionLayout.addRow(self.positionButtonLayout)
        self.positionTab.setLayout(self.positionLayout)

        # Parameter
        self.parameterLayout = QtGui.QFormLayout() 
        self.parameter_TCPAddress = QtGui.QLineEdit()
        self.parameter_TCPAddress.setMaxLength(15)
        self.parameter_TCPPort = QtGui.QLineEdit()
        self.parameter_TCPPort.setValidator(QtGui.QIntValidator())
        self.parameterButtonLayout = QtGui.QHBoxLayout()
        self.parameterConnectButton = QtGui.QPushButton('Save')
        self.parameterConnectButton.setStyleSheet('background-color: #3CB371')
        self.parameterConnectButton.clicked.connect(self.parameter_saveButton)
        self.parameterCancelButton = QtGui.QPushButton('Cancel')
        self.parameterCancelButton.clicked.connect(self.parameter_cancelButton)
        self.parameterButtonLayout.addWidget(self.parameterConnectButton)
        self.parameterButtonLayout.addWidget(self.parameterCancelButton)

        self.parameterLayout.addRow("TCP Address", self.parameter_TCPAddress)
        self.parameterLayout.addRow("Port", self.parameter_TCPPort)
        self.parameterLayout.addRow(self.parameterButtonLayout)
        self.parameterTab.setLayout(self.parameterLayout)

        # Plot
        self.plotLayout = QtGui.QFormLayout()
        self.plot_TCPAddress = QtGui.QLineEdit()
        self.plot_TCPAddress.setMaxLength(15)
        self.plot_TCPPort = QtGui.QLineEdit()
        self.plot_TCPPort.setValidator(QtGui.QIntValidator())
        self.plot_TCPTopic = QtGui.QLineEdit()
        self.plot_TCPTopic.setValidator(QtGui.QIntValidator())
        self.plotButtonLayout = QtGui.QHBoxLayout()
        self.plotConnectButton = QtGui.QPushButton('Connect')
        self.plotConnectButton.setStyleSheet('background-color: #3CB371')
        self.plotConnectButton.clicked.connect(self.plot_saveButton)
        self.plotCancelButton = QtGui.QPushButton('Cancel')
        self.plotCancelButton.clicked.connect(self.plot_cancelButton)
        self.plotButtonLayout.addWidget(self.plotConnectButton)
        self.plotButtonLayout.addWidget(self.plotCancelButton)

        self.plotLayout.addRow("TCP Address", self.plot_TCPAddress)
        self.plotLayout.addRow("Port", self.plot_TCPPort)
        self.plotLayout.addRow("Topic", self.plot_TCPTopic)
        self.plotLayout.addRow(self.plotButtonLayout)
        self.plotTab.setLayout(self.plotLayout)

        self.tabs.addTab(self.positionTab, 'Position')
        self.tabs.addTab(self.parameterTab, 'Parameters')
        self.tabs.addTab(self.plotTab, 'Plot')
         
        self.setWindowModality(QtCore.Qt.ApplicationModal)
        self.show()

    def keyPressEvent(self, event):
        if event.key() == QtCore.Qt.Key_Escape:
            self.close()

    def position_saveButton(self):
        address = str(self.position_TCPAddress.text())
        port = str(self.position_TCPPort.text())
        topic = str(self.position_TCPTopic.text())
        Thread(target=self.positionCheckValidPort, args=(address,port,topic)).start()
        self.close()
        
    def position_cancelButton(self):
        self.close()

    def positionCheckValidPort(self, address, port, topic):
        global position_address
        global statusBar

        if address and port and topic:
            new_position_address = "tcp://" + address + ":" + port
            if new_position_address != position_address:
                context = zmq.Context()
                socket = context.socket(zmq.SUB)
                socket.connect(new_position_address)
                socket.setsockopt(zmq.SUBSCRIBE, topic)
                # Check for valid data within 1 second
                time_end = time.time() + 1
                while time.time() < time_end:
                    try:
                        topic, data = socket.recv(zmq.NOBLOCK).split()
                        position_address = new_position_address
                        self.changePositionPort(new_position_address, topic)
                        # Put success statusbar here
                        #statusBar.showMessage('Successfully connected to ' + position_address, 8000)
                        return
                    except zmq.ZMQError, e:
                        # No data arrived
                        if e.errno == zmq.EAGAIN:
                            pass
                        else:
                            print("real error")
        # Put failed statusbar here

    def changePositionPort(self, address, topic):
        global position_context, position_socket, position_topic

        position_context = zmq.Context()
        position_socket = position_context.socket(zmq.SUB)
        position_socket.connect(address)
        position_socket.setsockopt(zmq.SUBSCRIBE, topic)
        position_topic = topic

    def parameter_saveButton(self):
        address = str(self.parameter_TCPAddress.text())
        port = str(self.parameter_TCPPort.text())
        Thread(target=self.parameterCheckValidPort, args=(address,port)).start()
        self.close()
        print('close popup')
        
    def parameter_cancelButton(self):
        self.close()

    def parameterCheckValidPort(self, address, port):
        global parameter_address
        
        if address and port:
            new_parameter_address = "tcp://" + address + ":" + port
            if new_parameter_address != parameter_address:
                context = zmq.Context()
                socket = context.socket(zmq.REQ)
                # Prevent program from hanging after closing
                socket.setsockopt(zmq.LINGER, 0)
                socket.connect(new_parameter_address)
                socket.send("info?")
                # Check for valid data within 1 second
                time_end = time.time() + 1
                while time.time() < time_end:
                    try:
                        result = socket.recv(zmq.NOBLOCK).split(',')
                        parameter_address = new_parameter_address
                        self.changeParameterPort(new_parameter_address)
                        #statusBar.showMessage('Successfully connected to ' + parameter_address, 8000)
                        return
                    except zmq.ZMQError, e:
                        # No data arrived
                        if e.errno == zmq.EAGAIN:
                            pass
                        else:
                            print("real error")
        #statusBar.showMessage('Invalid parameter IP/Port settings!', 8000) 

    def changeParameterPort(self, address):
        global parameter_context, parameter_socket
        global velocityMin, velocityMax, accelerationMin, accelerationMax, positionMin, positionMax, homeFlag, units
        parameter_context = zmq.Context()
        parameter_socket = parameter_context.socket(zmq.REQ)
        parameter_socket.connect(address)
        parameter_socket.send('info?')
        parameter_information = [x.strip() for x in parameter_socket.recv().split(',')]
        velocityMin, velocityMax, accelerationMin, accelerationMax, positionMin, positionMax, homeFlag, units = parameter_information
        parametersUpdate(velocityMin, velocityMax, accelerationMin, accelerationMax, positionMin, positionMax)

    def plot_saveButton(self):
        address = str(self.plot_TCPAddress.text())
        port = str(self.plot_TCPPort.text())
        topic = str(self.plot_TCPTopic.text())
        Thread(target=self.plotCheckValidPort, args=(address,port,topic)).start()
        self.close()
        
    def plot_cancelButton(self):
        self.close()

    def plotCheckValidPort(self, address, port, topic):
        global plot
        
        if address and port and topic:
            new_plot_address = "tcp://" + address + ":" + port
            if plot.getZMQPlotAddress() != new_plot_address:
                context = zmq.Context()
                socket = context.socket(zmq.SUB)
                socket.connect(new_plot_address)
                socket.setsockopt(zmq.SUBSCRIBE, topic)
                # Check for valid data within 1 second
                time_end = time.time() + 1
                while time.time() < time_end:
                    try:
                        topic, data = socket.recv(zmq.NOBLOCK).split()
                        plot.updateZMQPlotAddress(new_plot_address, topic)
                        return
                    except zmq.ZMQError, e:
                        # No data arrived
                        if e.errno == zmq.EAGAIN:
                            pass
                        else:
                            print("real error")

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
plot = ZMQPlotWidget()
plot.start()
motorPlot = RotationalControllerPlotWidget()

# Create and set widget layout
# Main widget container
cw = QtGui.QWidget()
ml = QtGui.QGridLayout()
cw.setLayout(ml)
mw.setCentralWidget(cw)
l = QtGui.QGridLayout()

# Prevent window from being maximized
mw.setFixedSize(cw.size())

# Enable zoom in for selected box region
pg.setConfigOption('leftButtonPan', False)

ml.addLayout(l,0,0)
ml.addWidget(plot.getZMQPlotWidget(),1,0)
ml.addWidget(motorPlot.getRotationalControllerPlotWidget(),0,1,2,1)
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

mw.statusBar()
mw.show()

if __name__ == '__main__':
    if(sys.flags.interactive != 1) or not hasattr(QtCore, 'PYQT_VERSION'):
        QtGui.QApplication.instance().exec_()


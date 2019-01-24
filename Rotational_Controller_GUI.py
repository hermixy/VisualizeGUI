'''
Run servers: pubsub_server2.py for parameter/position changes (OPTIONAL)
             reqrep_server1.py for ZMQ Plot (OPTIONAL)
             reqrep_server2.py for change ZMQ Plot ability (OPTIONAL)
             server1.py for rotational controller (REQUIRED) (switch for pubsub_server1.py)
'''
from PyQt4 import QtCore, QtGui 
from PyQt4.QtGui import QSizePolicy
from widgets import ZMQPlotWidget 
from widgets import RotationalControllerPlotWidget 
from widgets import PlotColorWidget 
import pyqtgraph as pg
import zmq
import numpy as np
import sys
from threading import Thread
import time
import configparser

# =====================================================================
# Configuration file settings 
# =====================================================================

# Read in plot settings from motor.ini file, creates file if doesn't exist
def readSettings():
    global position_address, position_topic, position_frequency, parameter_address
    global ZMQ_address, ZMQ_topic, ZMQ_frequency
    global saveSettingsFlag
    
    saveSettingsFlag = False
    # Read in each section and parse information
    try:
        config = configparser.ConfigParser()
        config.read('motor.ini')
        position_address = str(config['ROTATIONAL_CONTROLLER']['positionAddress'])
        position_topic = str(config['ROTATIONAL_CONTROLLER']['positionTopic'])
        parameter_address = str(config['ROTATIONAL_CONTROLLER']['parameterAddress'])
        try:
            position_frequency = float(config['ROTATIONAL_CONTROLLER']['positionFrequency'])
            if position_frequency <= 0:
                QtGui.QMessageBox.about(QtGui.QWidget(), 'Error',
                        'positionFrequency value cannot be zero or negative. Check motor.ini')
                exit(1)
        # Input was not a valid number 
        except ValueError:
            QtGui.QMessageBox.about(QtGui.QWidget(), 'Error', 'Invalid positionFrequency value. Check motor.ini')
            exit(1)

        ZMQ_address = str(config['ZMQ_PLOT']['ZMQAddress']) 
        ZMQ_topic = str(config['ZMQ_PLOT']['ZMQTopic'])
        try:
            ZMQ_frequency = float(config['ZMQ_PLOT']['ZMQFrequency'])
            if ZMQ_frequency <= 0:
                QtGui.QMessageBox.about(QtGui.QWidget(), 'Error', 'ZMQFrequency value cannot be zero or negative. Check motor.ini')
                exit(1)
        # Input was not a valid number 
        except ValueError:
            QtGui.QMessageBox.about(QtGui.QWidget(), 'Error', 'Invalid ZMQFrequency value. Check motor.ini')
            exit(1)
    
    # Create empty default motor.ini file if doesn't exist
    except KeyError:
        createEmptySettingsFile()
        QtGui.QMessageBox.about(QtGui.QWidget(), 'Error', 'motor.ini created, add settings into file')
        exit(1)

# Write port settings into motor.ini file with any new connection
def writeSettings(key, table):
    global saveSettingsFlag
    
    if saveSettingsFlag:
        parser = configparser.SafeConfigParser()
        parser.read('motor.ini')
        for k in table:
            parser.set(key, k, table[k])
        with open('motor.ini', 'w+') as configfile:
            parser.write(configfile)

# Create empty motor.ini file if doesn't exist
def createEmptySettingsFile():
    config = configparser.ConfigParser()
    config['ROTATIONAL_CONTROLLER'] = {'positionAddress': '',
                                       'positionTopic': '',
                                       'positionFrequency': '',
                                       'parameterAddress': '' }
    config['ZMQ_PLOT'] = {'ZMQAddress': '',
                          'ZMQTopic': '',
                          'ZMQFrequency': '' }
    with open('motor.ini', 'w') as configfile:
        config.write(configfile)

# Toggle save or discard saving port settings to motor.ini
def writePortSettingsToggle():
    global saveSettingsFlag
    global statusBar

    if saveSettingsFlag:
        saveSettingsFlag = False
        statusBar.showMessage('Write to motor.ini disabled', 4000)
    else: 
        saveSettingsFlag = True
        statusBar.showMessage('Write to motor.ini enabled', 4000)

# =====================================================================
# Port connection popup widget  
# =====================================================================

# Widget to control position, parameters, and plot connection settings (TCP address, port, topic)
class PortSettingPopUpWidget(QtGui.QWidget):
    def __init__(self, windowTitle, parent=None):
        super(PortSettingPopUpWidget, self).__init__(parent)

        self.popUpWidth = 195
        self.popUpHeight = 150
        self.setFixedSize(self.popUpWidth, self.popUpHeight)

        self.styleSettingValid = "border-radius: 6px; padding:5px; background-color: #5fba7d"
        self.styleSettingInvalid = "border-radius: 6px; padding:5px; background-color: #f78380"

        self.setWindowTitle(windowTitle)
        self.tabs = QtGui.QTabWidget(self)
        self.positionTab = QtGui.QWidget()
        self.parameterTab = QtGui.QWidget()
        self.plotTab = QtGui.QWidget()
        
        # Status bar message data and data wait time in seconds
        self.status = ()
        self.dataTimeout = 1

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
        self.parameterConnectButton = QtGui.QPushButton('Connect')
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

        # Popup Layout
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
    
    # Returns status of successful, same, or failed connection attempt
    def getStatus(self):
        return self.status

    def position_saveButton(self):
        address = str(self.position_TCPAddress.text())
        port = str(self.position_TCPPort.text())
        topic = str(self.position_TCPTopic.text())
        Thread(target=self.positionCheckValidPort, args=(address,port,topic)).start()
        self.close()
        
    def position_cancelButton(self):
        self.status = ()
        self.close()

    def positionCheckValidPort(self, address, port, topic):
        global position_address
        global statusBar
        global motorPlot
        global position_context, position_socket, position_topic
        global positionStatus

        if address and port and topic:
            new_position_address = "tcp://" + address + ":" + port
            if new_position_address != position_address or motorPlot.getPositionTopic() != topic:
                context = zmq.Context()
                socket = context.socket(zmq.SUB)
                socket.connect(new_position_address)
                socket.setsockopt(zmq.SUBSCRIBE, topic)
                # Check for valid data within time interval in seconds (s)
                time_end = time.time() + self.dataTimeout
                while time.time() < time_end:
                    try:
                        topic, data = socket.recv(zmq.NOBLOCK).split()
                        position_address = new_position_address
                        position_context, position_socket, position_topic = motorPlot.updatePositionPlotAddress(new_position_address, topic)
                        settings = {'positionAddress': new_position_address, 'positionTopic': position_topic}
                        writeSettings('ROTATIONAL_CONTROLLER', settings) 
                        self.status = ('success', position_address)
                        motorPlot.setPositionVerified(True)
                        positionStatus.setStyleSheet(self.styleSettingValid)
                        return
                    except zmq.ZMQError, e:
                        # No data arrived
                        if e.errno == zmq.EAGAIN:
                            pass
                        else:
                            print("real error")
                self.status = ('fail', position_address)
            else:
                self.status = ('same', position_address)
        else:
            self.status = ('fail', position_address)
    
    def parameter_saveButton(self):
        address = str(self.parameter_TCPAddress.text())
        port = str(self.parameter_TCPPort.text())
        Thread(target=self.parameterCheckValidPort, args=(address,port)).start()
        self.close()
        
    def parameter_cancelButton(self):
        self.status = ()
        self.close()

    def parameterCheckValidPort(self, address, port):
        global parameter_address
        global motorPlot
        global parameterStatus
        
        if address and port:
            new_parameter_address = "tcp://" + address + ":" + port
            if new_parameter_address != parameter_address:
                context = zmq.Context()
                socket = context.socket(zmq.REQ)
                # Prevent program from hanging after closing
                socket.setsockopt(zmq.LINGER, 0)
                socket.connect(new_parameter_address)
                socket.send("info?")
                # Check for valid data within time interval in seconds (s)
                time_end = time.time() + self.dataTimeout
                while time.time() < time_end:
                    try:
                        result = socket.recv(zmq.NOBLOCK).split(',')
                        parameter_address = new_parameter_address
                        motorPlot.setParameterVerified(True)
                        self.changeParameterPort(new_parameter_address)
                        settings = {'parameterAddress': new_parameter_address}
                        writeSettings('ROTATIONAL_CONTROLLER', settings) 
                        self.status = ('success', parameter_address)
                        parameterStatus.setStyleSheet(self.styleSettingValid)
                        return
                    except zmq.ZMQError, e:
                        # No data arrived
                        if e.errno == zmq.EAGAIN:
                            pass
                        else:
                            print("real error")
                self.status = ('fail', parameter_address)
            else:
                self.status = ('same', parameter_address)
        else:
            self.status = ('fail', parameter_address)

    def changeParameterPort(self, address):
        global parameter_context, parameter_socket
        global motorPlot
        parameter_context, parameter_socket = motorPlot.updateParameterPlotAddress(address)
        parametersUpdate()

    def plot_saveButton(self):
        address = str(self.plot_TCPAddress.text())
        port = str(self.plot_TCPPort.text())
        topic = str(self.plot_TCPTopic.text())
        Thread(target=self.plotCheckValidPort, args=(address,port,topic)).start()
        self.close()
        
    def plot_cancelButton(self):
        self.status = ()
        self.close()

    def plotCheckValidPort(self, address, port, topic):
        global plot
        global plotStatus
        
        if address and port and topic:
            new_plot_address = "tcp://" + address + ":" + port
            if plot.getZMQPlotAddress() != new_plot_address or plot.getZMQTopic() != topic:
                context = zmq.Context()
                socket = context.socket(zmq.SUB)
                socket.connect(new_plot_address)
                socket.setsockopt(zmq.SUBSCRIBE, topic)
                # Check for valid data within time interval in seconds (s)
                time_end = time.time() + self.dataTimeout
                while time.time() < time_end:
                    try:
                        topic, data = socket.recv(zmq.NOBLOCK).split()
                        plot.updateZMQPlotAddress(new_plot_address, topic)
                        if not plot.getVerified():
                            plot.setVerified(True)
                        settings = {'ZMQAddress': new_plot_address, 'ZMQTopic': topic}
                        writeSettings('ZMQ_PLOT', settings) 
                        self.status = ('success', new_plot_address)
                        plotStatus.setStyleSheet(self.styleSettingValid)
                        return
                    except zmq.ZMQError, e:
                        # No data arrived
                        if e.errno == zmq.EAGAIN:
                            pass
                        else:
                            print("real error")
                self.status = ('fail', new_plot_address)
            else:
                self.status = ('same', new_plot_address)
        else:
            self.status = ('fail', plot.getZMQPlotAddress())


# =====================================================================
# Thread to display connection status 
# =====================================================================

class displayStatusBarMessage(QtCore.QThread):
    global statusBar
    global portAddress
    global statusThreads
    global app

    def __init__(self, message='', parent=None):
        super(displayStatusBarMessage, self).__init__(parent)
        
        # Display statusbar message length in ms
        self.messageDuration = 8000

        # Get status message of popup connect
        self.signalThread = Thread(target=self.getSignal, args=())
        self.signalThread.daemon = True
        self.signalThread.start()

        # Add QThread object to array to detect if got signal
        self.statusThread = [] 
        self.statusThread.append(self.signalThread)
        
        self.setTerminationEnabled(True)
        self.daemon = True
        self.start()

        # Spin until get signal
        while self.statusThread:
            app.processEvents()
        
        # Display statusbar message
        self.showMessage()
        
        self.terminate()
        self.wait()
    
    def getSignal(self):
        self.status = portAddress.getStatus()
        self.visible = self.isWidgetVisible()
        while True:
            if self.visible:
                self.visible = self.isWidgetVisible()
            else:
                self.status = portAddress.getStatus()
                break
            time.sleep(.05)
        
        # Spin for extra time for the situation where it checks invalid input
        # Additional time comes from time used to verify input settings function
        time_end = time.time() + 1.25
        while time.time() < time_end:
            app.processEvents()
        self.status = portAddress.getStatus()
        
        # Pop to signal parent thread that signal was received
        self.statusThread.pop()
    
    def isWidgetVisible(self):
        return True if not portAddress.visibleRegion().isEmpty() else False

    def showMessage(self):
        if self.status:
            if self.status[0] == 'success':
                statusBar.showMessage('Successfully connected to ' + str(self.status[1]), self.messageDuration)
            elif self.status[0] == 'same':
                statusBar.showMessage('Already connected to ' + str(self.status[1]), self.messageDuration)
            elif self.status[0] == 'fail':
                statusBar.showMessage('Invalid IP/Port settings!', self.messageDuration)

# =====================================================================
# Button action functions
# =====================================================================

# Move rotational controller with selected values
def moveButton():
    global statusBar
    def moveButtonThread():
        global motorPlot
        global parameter_socket
        parameter_socket = motorPlot.getParameterSocket()
        if parameter_socket:
            try:
                v = str(velocity.text())
                a = str(acceleration.text())
                p = str(position.text())
                if p and v and a:
                    command = "move {} {} {}".format(v,a,p)
                    parameter_socket.send(command)
                    result = parameter_socket.recv()
                    #print("Move response is " + result)
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
        global motorPlot
        parameter_socket = motorPlot.getParameterSocket()
        if parameter_socket:
            try:
                parameter_socket.send("home")
                result = parameter_socket.recv()
                #print("Home response is " + result)
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
    displayStatusBarMessage()

# =====================================================================
# Update timer and thread functions
# =====================================================================

# Current position update
def positionUpdate():
    global currentPositionValue
    global motorPlot

    currentPositionValue = str(motorPlot.getCurrentPositionValue())
    currentPosition.setText(currentPositionValue)

# Update fields with selected preset setting
def presetSettingsUpdate():
    name = str(presets.currentText()) 
    position.setText(presetTable[name]["position"])
    velocity.setText(presetTable[name]["velocity"])
    acceleration.setText(presetTable[name]["acceleration"])

# Update the velocity, acceleration, and position min/max range (low,high) of input
def parametersUpdate():
    global velocityMin, velocityMax, accelerationMin, accelerationMax, positionMin, positionMax, homeFlag, units
    global position, velocity, acceleration, motorPlot, home
    
    if motorPlot.getParameterVerified():
        position.clear()
        velocity.clear()
        acceleration.clear()
        velocityMin, velocityMax, accelerationMin, accelerationMax, positionMin, positionMax, homeFlag, units = motorPlot.getParameterInformation()
        if homeFlag == 'false':
            home.setEnabled(False)
        else:
            home.setEnabled(True)
        position.setValidator(QtGui.QIntValidator(int(positionMin), int(positionMax)))
        velocity.setValidator(QtGui.QIntValidator(int(velocityMin), int(velocityMax)))
        acceleration.setValidator(QtGui.QIntValidator(int(accelerationMin), int(accelerationMax)))

# Display port connection status indicators 
def initStatusColors():
    global positionStatus, parameterStatus, plotStatus
    global plot, motorPlot

    styleSettingValid = "border-radius: 6px; padding:5px; background-color: #5fba7d"
    styleSettingInvalid = "border-radius: 6px; padding:5px; background-color: #f78380"

    plotStatus.setStyleSheet(styleSettingValid) if plot.getVerified() else plotStatus.setStyleSheet(styleSettingInvalid)
    positionStatus.setStyleSheet(styleSettingValid) if motorPlot.getPositionVerified() else positionStatus.setStyleSheet(styleSettingInvalid)
    parameterStatus.setStyleSheet(styleSettingValid) if motorPlot.getParameterVerified() else parameterStatus.setStyleSheet(styleSettingInvalid)

# Initialize socket connections and parameter settings
def initGlobalVariables():
    global velocityMin, velocityMax, accelerationMin, accelerationMax, positionMin, positionMax, homeFlag, units
    global motorPlot
    global parameter_socket, position_socket
    if motorPlot.getParameterVerified():
        velocityMin, velocityMax, accelerationMin, accelerationMax, positionMin, positionMax, homeFlag, units = motorPlot.getParameterInformation()
        parameter_socket = motorPlot.getParameterSocket()
    if motorPlot.getPositionVerified():
        position_socket = motorPlot.getPositionSocket()

# =====================================================================
# Utility Functions 
# =====================================================================

# Clear plot data 
def clearPlots():
    global plot
    global motorPlot
    global statusBar

    plot.clearZMQPlot()
    motorPlot.clearRotationalControllerPlot()
    statusBar.showMessage('Plots cleared', 4000)

# Opens color palette selector to change color
def changePlotColor(plotObject):
    def changePlotColorThread():
        plotColor = PlotColorWidget(plotObject)
    Thread(target=changePlotColorThread(), args=()).start()

# =====================================================================
# Main GUI Application
# =====================================================================

# Create main application window
app = QtGui.QApplication([])
app.setStyle(QtGui.QStyleFactory.create("Cleanlooks"))
mw = QtGui.QMainWindow()
mw.setWindowTitle('Rotational Controller GUI')

# Read in configuration settings
readSettings()

# Initialize statusbar
statusBar = QtGui.QStatusBar()
mw.setStatusBar(statusBar)
statusBar.setSizeGripEnabled(False)

# Create ZMQ plot and rotational controller plot
plot = ZMQPlotWidget(ZMQ_address, ZMQ_topic, ZMQ_frequency)
motorPlot = RotationalControllerPlotWidget(position_address, position_topic, position_frequency, parameter_address)

initGlobalVariables()

# Create and set widget layout
# Main widget container
cw = QtGui.QWidget()
ml = QtGui.QGridLayout()
cw.setLayout(ml)
mw.setCentralWidget(cw)
l = QtGui.QGridLayout()

# Prevent window from being maximized
#mw.setFixedSize(cw.size())
mw.setFixedSize(700,550)

# Enable zoom in for selected box region
pg.setConfigOption('leftButtonPan', False)

# Arrange widget layouts
ml.addLayout(l,0,0,1,1)
ml.addWidget(plot.getZMQPlotWidget(),1,0,1,1)
ml.addWidget(motorPlot.getRotationalControllerPlotWidget(),0,1,2,1)
mw.setSizePolicy(QtGui.QSizePolicy.Fixed, QtGui.QSizePolicy.Fixed)

# Menubar/Toolbar
mb = mw.menuBar()
fileMenu = mb.addMenu('&File')
displayMenu = mb.addMenu('&Display')
formatMenu = mb.addMenu('&Format')

# File menu
portChangeAction = QtGui.QAction('Change Port Settings', mw)
portChangeAction.setShortcut('Ctrl+P')
portChangeAction.setStatusTip('Change position, parameter, or plot port settings')
portChangeAction.triggered.connect(changeIPPortSettingsButton)
fileMenu.addAction(portChangeAction)

moveAction = QtGui.QAction('Move', mw)
moveAction.setShortcut('Ctrl+M')
moveAction.setStatusTip('Move to specified position')
moveAction.triggered.connect(moveButton)
fileMenu.addAction(moveAction)

homeAction = QtGui.QAction('Home', mw)
homeAction.setShortcut('Ctrl+H')
homeAction.setStatusTip('Reset rotational controller to home position')
homeAction.triggered.connect(homeButton)
fileMenu.addAction(homeAction)

addPresetAction = QtGui.QAction('Add Preset', mw)
addPresetAction.setShortcut('Ctrl+A')
addPresetAction.setStatusTip('Save current values into a preset setting')
addPresetAction.triggered.connect(addPresetSettingsButton)
fileMenu.addAction(addPresetAction)

exitAction = QtGui.QAction('Exit', mw)
exitAction.setShortcut('Ctrl+Q')
exitAction.setStatusTip('Exit application')
exitAction.triggered.connect(QtGui.qApp.quit)
fileMenu.addAction(exitAction)

# Display Menu
clearGraphAction = QtGui.QAction('Clear Plots', mw)
clearGraphAction.setShortcut('Ctrl+C')
clearGraphAction.setStatusTip('Clear current plot views')
clearGraphAction.triggered.connect(clearPlots)
displayMenu.addAction(clearGraphAction)

changeZMQPlotColorAction = QtGui.QAction('Change ZMQ Plot Color', mw)
changeZMQPlotColorAction.setStatusTip('Change ZMQ plot color')
changeZMQPlotColorAction.triggered.connect(lambda: changePlotColor(plot))
displayMenu.addAction(changeZMQPlotColorAction)

changeRotationalControllerPlotColorAction = QtGui.QAction('Change Rotational Controller Plot Color ', mw)
changeRotationalControllerPlotColorAction.setStatusTip('Change rotational controller plot color')
changeRotationalControllerPlotColorAction.triggered.connect(lambda: changePlotColor(motorPlot))
displayMenu.addAction(changeRotationalControllerPlotColorAction)

# Format Menu
writeToFileToggle = QtGui.QAction('Save Port Settings', mw, checkable=True)
writeToFileToggle.setShortcut('Ctrl+S')
writeToFileToggle.setStatusTip('Save port setting changes to motor.ini')
writeToFileToggle.triggered.connect(writePortSettingsToggle)
formatMenu.addAction(writeToFileToggle)

# GUI elements
statusLabel = QtGui.QLabel('Port Status')
positionStatus = QtGui.QLabel('Position')
positionStatus.setAlignment(QtCore.Qt.AlignCenter)
parameterStatus = QtGui.QLabel('Parameter')
parameterStatus.setAlignment(QtCore.Qt.AlignCenter)
plotStatus = QtGui.QLabel('Plot')
plotStatus.setAlignment(QtCore.Qt.AlignCenter)

portSettings = QtGui.QPushButton('IP/Port Settings')
portSettings.clicked.connect(changeIPPortSettingsButton)

velocityLabel = QtGui.QLabel()
velocityLabel.setText('Velocity (deg/s)')
velocity = QtGui.QLineEdit()
velocity.setAlignment(QtCore.Qt.AlignLeft)

accelerationLabel = QtGui.QLabel()
accelerationLabel.setText('Acceleration (deg/s^2)')
acceleration = QtGui.QLineEdit()
acceleration.setAlignment(QtCore.Qt.AlignLeft)

positionLabel = QtGui.QLabel()
positionLabel.setText('Position (deg)')
position = QtGui.QLineEdit()
position.setAlignment(QtCore.Qt.AlignLeft)

currentPositionLabel = QtGui.QLabel()
currentPositionLabel.setText('Current Position')
currentPosition = QtGui.QLabel()

move = QtGui.QPushButton('Move')
move.clicked.connect(moveButton)

home = QtGui.QPushButton('Home')
home.clicked.connect(homeButton)

# Disable home button if unavailable
if motorPlot.getParameterVerified():
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

parametersUpdate()
initStatusColors()

# Layout
l.addWidget(statusLabel,0,0,1,1)
l.addWidget(positionStatus,0,1,1,1)
l.addWidget(parameterStatus,0,2,1,1)
l.addWidget(plotStatus,0,3,1,1)

l.addWidget(portSettings,1,0,1,4)
l.addWidget(velocityLabel,2,0,1,2)
l.addWidget(velocity,2,2,1,2)
l.addWidget(accelerationLabel,3,0,1,2)
l.addWidget(acceleration,3,2,1,2)
l.addWidget(positionLabel,4,0,1,2)
l.addWidget(position,4,2,1,2)
l.addWidget(currentPositionLabel,5,0,1,2)

l.addWidget(currentPosition,5,2,1,2)
l.addWidget(move,6,0,1,4)
l.addWidget(home,7,0,1,4)
l.addWidget(presetLabel,8,0,1,1)
l.addWidget(presets,8,1,1,1)
l.addWidget(presetName,8,2,1,1)
l.addWidget(presetButton,8,3,1,1)

# Start internal timers and threads 
positionUpdateTimer = QtCore.QTimer()
positionUpdateTimer.timeout.connect(positionUpdate)
positionUpdateTimer.start(motorPlot.getRotationalControllerTimerFrequency())

mw.statusBar()
mw.show()

if __name__ == '__main__':
    if(sys.flags.interactive != 1) or not hasattr(QtCore, 'PYQT_VERSION'):
        QtGui.QApplication.instance().exec_()


from PyQt4 import QtCore, QtGui 
from PyQt4.QtGui import QSizePolicy
from widgets import ZMQPlotWidget 
from widgets import RotationalControllerPlotWidget 
from widgets import PlotColorWidget 
from load_CSS import load_CSS
import pyqtgraph as pg
import zmq
import numpy as np
import sys
from threading import Thread
import time
import configparser
import logging

"""Rotational Controller GUI

Controls rotational controller with precise movement velocity, 
acceleration, and positional accuracy. Ensure rotational controller is 
connected. rotational.ini is the configuraiton settings file.

Run servers: rotational_parameter_position_server.py for parameter/position changes (OPTIONAL)
             rotational_plot_server.py for ZMQ Plot (OPTIONAL)
             rotational_plot_server_alt.py for change ZMQ Plot ability (OPTIONAL)
             rotational_controller_server.py for rotational controller (REQUIRED) (switch for rotational_parameter_position_server_alt.py)
"""

# =====================================================================
# Configuration file settings 
# =====================================================================

def read_settings():
    """Read in plot settings from rotational.ini file, creates file if doesn't exist"""

    global position_address
    global position_topic 
    global position_frequency 
    global parameter_address 
    global ZMQ_address 
    global ZMQ_topic 
    global ZMQ_frequency 
    global save_settings
    
    save_settings = False
    
    # Read in each section and parse information
    try:
        config = configparser.ConfigParser()
        config.read('rotational.ini')
        position_address = str(config['ROTATIONAL_CONTROLLER']['position_address'])
        position_topic = str(config['ROTATIONAL_CONTROLLER']['position_topic'])
        parameter_address = str(config['ROTATIONAL_CONTROLLER']['parameter_address'])
        # Checking position and parameter settings
        try:
            position_frequency = float(config['ROTATIONAL_CONTROLLER']['position_frequency'])
            if position_frequency <= 0:
                QtGui.QMessageBox.about(QtGui.QWidget(), 'Error',
                        'position_frequency value cannot be zero or negative. Check rotational.ini')
                logging.error('position_frequency value cannot be zero or negative.')
                exit(1)
        # Input was not a valid number 
        except ValueError:
            QtGui.QMessageBox.about(QtGui.QWidget(), 'Error', 'Invalid position_frequency value. Check rotational.ini')
            logging.exception("Invalid position_frequency value.")
            exit(1)

        ZMQ_address = str(config['ZMQ_PLOT']['ZMQ_address']) 
        ZMQ_topic = str(config['ZMQ_PLOT']['ZMQ_topic'])
        # Checking ZMQ plot settings
        try:
            ZMQ_frequency = float(config['ZMQ_PLOT']['ZMQ_frequency'])
            if ZMQ_frequency <= 0:
                QtGui.QMessageBox.about(QtGui.QWidget(), 'Error', 'ZMQ_frequency value cannot be zero or negative. Check rotational.ini')
                logging.error('ZMQ_frequency value cannot be zero or negative.')
                exit(1)
        # Input was not a valid number 
        except ValueError:
            QtGui.QMessageBox.about(QtGui.QWidget(), 'Error', 'Invalid ZMQ_frequency value. Check rotational.ini')
            logging.exception("Invalid ZMQ_frequency value.")
            exit(1)
    
    # Create empty default rotational.ini file if doesn't exist
    except KeyError:
        create_empty_settings_file()
        QtGui.QMessageBox.about(QtGui.QWidget(), 'Error', 'rotational.ini created, add settings into file')
        logging.exception("rotational.ini file was not found. File has been created. Add settings into file.")
        exit(1)
    logging.info('Successfully loaded .ini configuration file')

def write_settings(key, table):
    """Write port settings into rotational.ini file with any new connection"""

    global save_settings
    
    if save_settings:
        parser = configparser.SafeConfigParser()
        parser.read('rotational.ini')
        for k in table:
            parser.set(key, k, table[k])
        with open('rotational.ini', 'w+') as config_file:
            parser.write(config_file)

def create_empty_settings_file():
    """Create empty rotational.ini file if doesn't exist"""

    config = configparser.ConfigParser()
    config['ROTATIONAL_CONTROLLER'] = {'position_address': '',
                                       'position_topic': '',
                                       'position_frequency': '',
                                       'parameter_address': '' }
    config['ZMQ_PLOT'] = {'ZMQ_address': '',
                          'ZMQ_topic': '',
                          'ZMQ_frequency': '' }
    with open('rotational.ini', 'w') as config_file:
        config.write(config_file)

def write_port_settings_toggle():
    """Toggle save or discard saving port settings to rotational.ini"""

    global save_settings
    global status_bar

    if save_settings:
        save_settings = False
        status_bar.showMessage('Write to rotational.ini disabled', 4000)
        logging.info('Write to rotational.ini disabled')
    else: 
        save_settings = True
        write_current_port_settings()
        status_bar.showMessage('Write to rotational.ini enabled', 4000)
        logging.info('Write to rotational.ini enabled')

def write_current_port_settings():
    """Save current port settings into .ini file"""

    global position_settings
    global parameter_settings
    global ZMQ_plot_settings
    
    try:
        write_settings('ROTATIONAL_CONTROLLER', position_settings)
    # Raises error since position_settings is created once user successfuly changes to new port
    # otherwise variable does not exist yet
    except NameError:
        pass
    try:
        write_settings('ROTATIONAL_CONTROLLER', parameter_settings)
    except NameError:
        pass
    try:
        write_settings('ZMQ_PLOT', ZMQ_plot_settings)
    except NameError:
        pass

def initialize_logger():
    """Logging configuration settings

    Create log files in rotational.log and log events with INFO status or higher
    """

    logging.basicConfig(filename='rotational.log', filemode='w', level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s', datefmt='%d-%b-%y %H:%M:%S')
    logging.info('Successfully loaded logger configuration settings')

# =====================================================================
# Port connection popup widget  
# =====================================================================

class PortSettingPopUpWidget(QtGui.QWidget):
    """Widget to control position, parameters, and plot connection settings (TCP address, port, topic)
    
    Includes 3 tabs: position, parameter, and plot

    position: Reads current rotational controller value
    parameter: Sets velocity, position, and acceleration limits and allows communication to GUI
    plot: ZMQ plot readings
    """

    def __init__(self, window_title, parent=None):
        super(PortSettingPopUpWidget, self).__init__(parent)

        self.POPUP_WIDTH = 220
        self.POPUP_HEIGHT = 150
        self.setFixedSize(self.POPUP_WIDTH, self.POPUP_HEIGHT)

        self.style_setting_valid = "border-radius: 6px; padding:5px; background-color: #5fba7d"
        self.style_setting_invalid  = "border-radius: 6px; padding:5px; background-color: #f78380"

        self.setWindowTitle(window_title)
        self.tabs = QtGui.QTabWidget(self)
        self.position_tab = QtGui.QWidget()
        self.parameter_tab = QtGui.QWidget()
        self.plot_tab = QtGui.QWidget()
        
        # Status bar message data and data wait time in seconds
        self.status = ()
        self.DATA_TIMEOUT = 1

        # Position
        self.position_layout = QtGui.QFormLayout()
        self.position_TCPAddress = QtGui.QLineEdit()
        self.position_TCPAddress.setMaxLength(15)
        self.position_TCPPort = QtGui.QLineEdit()
        self.position_TCPPort.setValidator(QtGui.QIntValidator())
        self.position_TCPTopic = QtGui.QLineEdit()
        self.position_TCPTopic.setValidator(QtGui.QIntValidator())
        self.position_button_layout = QtGui.QHBoxLayout()
        self.position_connect_button = QtGui.QPushButton('Connect')
        self.position_connect_button.setStyleSheet('background-color: #3CB371')
        self.position_connect_button.clicked.connect(self.position_save_button)
        self.position_stop_button = QtGui.QPushButton('Cancel')
        self.position_stop_button.clicked.connect(self.position_cancel_button)
        self.position_button_layout.addWidget(self.position_connect_button)
        self.position_button_layout.addWidget(self.position_stop_button)

        self.position_layout.addRow("TCP Address", self.position_TCPAddress)
        self.position_layout.addRow("Port", self.position_TCPPort)
        self.position_layout.addRow("Topic", self.position_TCPTopic)
        self.position_layout.addRow(self.position_button_layout)
        self.position_tab.setLayout(self.position_layout)

        # Parameter
        self.parameter_layout = QtGui.QFormLayout() 
        self.parameter_TCPAddress = QtGui.QLineEdit()
        self.parameter_TCPAddress.setMaxLength(15)
        self.parameter_TCPPort = QtGui.QLineEdit()
        self.parameter_TCPPort.setValidator(QtGui.QIntValidator())
        self.parameter_button_layout = QtGui.QHBoxLayout()
        self.parameter_connect_button = QtGui.QPushButton('Connect')
        self.parameter_connect_button.setStyleSheet('background-color: #3CB371')
        self.parameter_connect_button.clicked.connect(self.parameter_save_button)
        self.parameter_stop_button = QtGui.QPushButton('Cancel')
        self.parameter_stop_button.clicked.connect(self.parameter_cancel_button)
        self.parameter_button_layout.addWidget(self.parameter_connect_button)
        self.parameter_button_layout.addWidget(self.parameter_stop_button)

        self.parameter_layout.addRow("TCP Address", self.parameter_TCPAddress)
        self.parameter_layout.addRow("Port", self.parameter_TCPPort)
        self.parameter_layout.addRow(self.parameter_button_layout)
        self.parameter_tab.setLayout(self.parameter_layout)

        # Plot
        self.plot_layout = QtGui.QFormLayout()
        self.plot_TCPAddress = QtGui.QLineEdit()
        self.plot_TCPAddress.setMaxLength(15)
        self.plot_TCPPort = QtGui.QLineEdit()
        self.plot_TCPPort.setValidator(QtGui.QIntValidator())
        self.plot_TCPTopic = QtGui.QLineEdit()
        self.plot_TCPTopic.setValidator(QtGui.QIntValidator())
        self.plot_button_layout = QtGui.QHBoxLayout()
        self.plot_connect_button = QtGui.QPushButton('Connect')
        self.plot_connect_button.setStyleSheet('background-color: #3CB371')
        self.plot_connect_button.clicked.connect(self.plot_save_button)
        self.plot_stop_button = QtGui.QPushButton('Cancel')
        self.plot_stop_button.clicked.connect(self.plot_cancel_button)
        self.plot_button_layout.addWidget(self.plot_connect_button)
        self.plot_button_layout.addWidget(self.plot_stop_button)

        self.plot_layout.addRow("TCP Address", self.plot_TCPAddress)
        self.plot_layout.addRow("Port", self.plot_TCPPort)
        self.plot_layout.addRow("Topic", self.plot_TCPTopic)
        self.plot_layout.addRow(self.plot_button_layout)
        self.plot_tab.setLayout(self.plot_layout)

        # Popup Layout
        self.tabs.addTab(self.position_tab, 'Position')
        self.tabs.addTab(self.parameter_tab, 'Parameters')
        self.tabs.addTab(self.plot_tab, 'Plot')
         
        self.setWindowModality(QtCore.Qt.ApplicationModal)
        self.show()
    
    def get_status(self):
        """Returns status of successful, unchanged, or failed connection attempt"""

        return self.status

    def position_save_button(self):
        """Parses position input and sets port if validated"""

        address = str(self.position_TCPAddress.text())
        port = str(self.position_TCPPort.text())
        topic = str(self.position_TCPTopic.text())
        Thread(target=self.position_check_valid_port, args=(address,port,topic)).start()
        self.close()
        
    def position_cancel_button(self):
        """Cancel position port change operation"""

        self.status = ()
        self.close()

    def position_check_valid_port(self, address, port, topic):
        """Opens a ZMQ socket connection and checks if valid port"""

        global position_address
        global status_bar
        global rotational_controller_plot
        global position_context
        global position_socket 
        global position_topic
        global position_status
        global position_settings
        
        logging.info("Attempt to connect to new position port")
        if address and port and topic:
            new_position_address = "tcp://" + address + ":" + port
            if new_position_address != position_address or rotational_controller_plot.get_position_topic() != topic:
                context = zmq.Context()
                socket = context.socket(zmq.SUB)
                socket.connect(new_position_address)
                socket.setsockopt(zmq.SUBSCRIBE, topic)
                # Check for valid data within time interval in seconds (s)
                time_end = time.time() + self.DATA_TIMEOUT
                while time.time() < time_end:
                    try:
                        topic, data = socket.recv(zmq.NOBLOCK).split()
                        position_address = new_position_address
                        position_context, position_socket, position_topic = rotational_controller_plot.update_position_plot_address(new_position_address, topic)
                        position_settings = {'position_address': new_position_address, 'position_topic': position_topic}
                        write_settings('ROTATIONAL_CONTROLLER', position_settings) 
                        self.status = ('success', position_address)
                        rotational_controller_plot.set_position_verified(True)
                        position_status.setStyleSheet(self.style_setting_valid)
                        logging.info('Successfully connected to position port with address:{}, port:{}, topic:{}'.format(address, port, topic))
                        return
                    except zmq.ZMQError, e:
                        # No data arrived
                        if e.errno == zmq.EAGAIN:
                            pass
                self.status = ('fail', position_address)
                logging.info('Failed to connect to position port with address:{}, port:{}, topic:{}'.format(address, port, topic))
            else:
                self.status = ('same', position_address)
                logging.info('Already connected to position port with address:{}, port:{}, topic:{}'.format(address, port, topic))
        else:
            self.status = ('fail', position_address)
            logging.info('Failed to connect to position port. Empty settings')

    def parameter_save_button(self):
        """Parses parameter input and sets port if validated"""

        address = str(self.parameter_TCPAddress.text())
        port = str(self.parameter_TCPPort.text())
        Thread(target=self.parameter_check_valid_port, args=(address,port)).start()
        self.close()
        
    def parameter_cancel_button(self):
        """Cancel parameter port change operation"""

        self.status = ()
        self.close()

    def parameter_check_valid_port(self, address, port):
        """Opens a ZMQ socket connection and checks if valid port"""

        global parameter_address
        global rotational_controller_plot
        global parameter_status
        global parameter_settings
        
        logging.info("Attempt to connect to new parameter port")
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
                time_end = time.time() + self.DATA_TIMEOUT
                # Data will be placed into result if successful connection
                while time.time() < time_end:
                    try:
                        result = socket.recv(zmq.NOBLOCK).split(',')
                        parameter_address = new_parameter_address
                        rotational_controller_plot.set_parameter_verified(True)
                        self.change_parameter_port(new_parameter_address)
                        parameter_settings = {'parameter_address': new_parameter_address}
                        write_settings('ROTATIONAL_CONTROLLER', parameter_settings) 
                        self.status = ('success', parameter_address)
                        parameter_status.setStyleSheet(self.style_setting_valid)
                        logging.info('Successfully connected to parameter port with address:{}, port:{}'.format(address, port))
                        return
                    except zmq.ZMQError, e:
                        # No data arrived
                        if e.errno == zmq.EAGAIN:
                            pass
                self.status = ('fail', parameter_address)
                logging.info('Failed to connect to parameter port with address:{} and port:{}'.format(address, port))
            else:
                self.status = ('same', parameter_address)
                logging.info('Already connected to parameter port with address:{} and port:{}'.format(address, port))
        else:
            self.status = ('fail', parameter_address)
            logging.info('Failed to connect to parameter port. Empty settings.')

    def change_parameter_port(self, address):
        """Sets parameter port with new settings"""

        global parameter_context
        global parameter_socket
        global rotational_controller_plot
        parameter_context, parameter_socket = rotational_controller_plot.update_parameter_plot_address(address)
        parameter_update()

    def plot_save_button(self):
        """Parses plot input and sets port if validated"""

        address = str(self.plot_TCPAddress.text())
        port = str(self.plot_TCPPort.text())
        topic = str(self.plot_TCPTopic.text())
        Thread(target=self.plot_check_valid_port, args=(address,port,topic)).start()
        self.close()
        
    def plot_cancel_button(self):
        """Cancel plot port change operation"""

        self.status = ()
        self.close()

    def plot_check_valid_port(self, address, port, topic):
        """Opens a ZMQ socket connection and checks if valid port"""

        global plot
        global plot_status
        global ZMQ_plot_settings
        
        logging.info("Attempt to connect to new plot port")
        if address and port and topic:
            new_plot_address = "tcp://" + address + ":" + port
            if plot.get_ZMQ_plot_address() != new_plot_address or plot.get_ZMQ_topic() != topic:
                context = zmq.Context()
                socket = context.socket(zmq.SUB)
                socket.connect(new_plot_address)
                socket.setsockopt(zmq.SUBSCRIBE, topic)
                # Check for valid data within time interval in seconds (s)
                time_end = time.time() + self.DATA_TIMEOUT
                while time.time() < time_end:
                    try:
                        topic, data = socket.recv(zmq.NOBLOCK).split()
                        plot.update_ZMQ_plot_address(new_plot_address, topic)
                        if not plot.get_verified():
                            plot.set_verified(True)
                        ZMQ_plot_settings = {'ZMQ_address': new_plot_address, 'ZMQ_topic': topic}
                        write_settings('ZMQ_PLOT', ZMQ_plot_settings) 
                        self.status = ('success', new_plot_address)
                        plot_status.setStyleSheet(self.style_setting_valid)
                        logging.info('Successfully connected to plot port with address:{}, port:{}, topic:{}'.format(address, port, topic))
                        return
                    except zmq.ZMQError, e:
                        # No data arrived
                        if e.errno == zmq.EAGAIN:
                            pass
                self.status = ('fail', new_plot_address)
                logging.info('Failed to connect to plot port with address:{}, port:{}, topic:{}'.format(address, port, topic))
            else:
                self.status = ('same', new_plot_address)
                logging.info('Already connected to plot port with address:{}, port:{}, topic:{}'.format(address, port, topic))
        else:
            self.status = ('fail', plot.get_ZMQ_plot_address())
            logging.info('Failed to connect to plot port. Empty settings')

# =====================================================================
# Status bar message timer widget
# =====================================================================

class DisplayStatusBarMessageThread(QtCore.QThread):
    """Thread to display status bar connection status"""

    global status_bar
    global port_address
    global app

    def __init__(self, message='', parent=None):
        super(DisplayStatusBarMessageThread, self).__init__(parent)
        
        # Display status_bar message length in ms
        self.MESSAGE_DURATION = 8000

        # Duration for popup to open on GUI in s
        self.POPUP_OPEN_DELAY = .05

        # Duration for popup to verify port settings in s
        self.TIME_TO_VERIFY_SETTINGS = 1.25

        # Get status message of popup connect
        self.signal_thread = Thread(target=self.get_signal, args=())
        self.signal_thread.daemon = True
        self.signal_thread.start()

        # Add QThread object to array to detect if got signal
        self.status_threads = [] 
        self.status_threads.append(self.signal_thread)
        
        self.setTerminationEnabled(True)
        self.daemon = True
        self.start()

        # Spin until get signal
        while self.status_threads:
            app.processEvents()
        
        # Display status_bar message
        self.show_message()
        
        self.terminate()
        self.wait()
    
    def get_signal(self):
        """Obtain port connection status from popup

        Since QTimers must be run in the main GUI thread, 
        the signal must be received from the popup and transfered
        to the main thread. This function runs simultaneously 
        to the popup thread in order to bring the signal 
        out of the popup.
        """

        self.status = port_address.get_status()
        self.visible = self.is_widget_visible()
        while True:
            if self.visible:
                self.visible = self.is_widget_visible()
            else:
                self.status = port_address.get_status()
                break
            time.sleep(self.POPUP_OPEN_DELAY)
        
        # Spin for extra time for the situation where it checks invalid input
        # Additional time comes from time used to verify input settings function
        time_end = time.time() + self.TIME_TO_VERIFY_SETTINGS
        while time.time() < time_end:
            app.processEvents()
        self.status = port_address.get_status()
        
        # Pop to signal parent thread that signal was received
        self.status_threads.pop()
    
    def is_widget_visible(self):
        """Determines if popup widget is visbile"""

        return True if not port_address.visibleRegion().isEmpty() else False

    def show_message(self):
        """Display connection status on statusbar"""

        if self.status:
            if self.status[0] == 'success':
                status_bar.showMessage('Successfully connected to ' + str(self.status[1]), self.MESSAGE_DURATION)
            elif self.status[0] == 'same':
                status_bar.showMessage('Already connected to ' + str(self.status[1]), self.MESSAGE_DURATION)
            elif self.status[0] == 'fail':
                status_bar.showMessage('Invalid IP/Port settings!', self.MESSAGE_DURATION)

# =====================================================================
# Button action functions
# =====================================================================

def move_button():
    """Move rotational controller with selected values"""

    def move_button_thread():
        global rotational_controller_plot
        global parameter_socket
        parameter_socket = rotational_controller_plot.get_parameter_socket()
        if parameter_socket:
            try:
                v = str(velocity.text())
                a = str(acceleration.text())
                p = str(position.text())
                if p and v and a:
                    command = "move {} {} {}".format(v,a,p)
                    parameter_socket.send(command)
                    result = parameter_socket.recv()
                    logging.info("Moved with velocity:{}, acceleration:{}, position:{}".format(v,a,p))
                else:
                    pass
            # No data arrived
            except zmq.ZMQError:
                pass
    Thread(target=move_button_thread, args=()).start()

def home_button():
    """Resets rotational controller to default position"""

    def home_button_thread():
        global parameter_socket
        global rotational_controller_plot
        parameter_socket = rotational_controller_plot.get_parameter_socket()
        if parameter_socket:
            try:
                parameter_socket.send("home")
                result = parameter_socket.recv()
                logging.info("Home button pressed")
            # No data arrived
            except zmq.ZMQError:
                pass
    Thread(target=home_button_thread, args=()).start()

def add_preset_settings_button():
    """Save current text fields into a preset"""

    def add_preset_settings_button_thread():
        name = str(preset_name.text())
        v = str(velocity.text())
        a = str(acceleration.text())
        p = str(position.text())
        if not name:
            return
        if not p or not v or not a:
            return
        if name not in preset_table:
            presets.addItem(name)
        preset_table[name] = {
                "position": p,
                "velocity": v,
                "acceleration": a 
                }
        index = presets.findText(name)
        presets.setCurrentIndex(index)
        preset_name.clear()
        logging.info("Successfully added {} preset".format(name))
    Thread(target=add_preset_settings_button_thread, args=()).start()

def change_IP_port_settings_button():
    """Change position, parameters, and plot IP/Port settings (TCP Address, Port, Topic)"""

    global port_address
    global status_bar
    
    status_bar.clearMessage()
    port_address = PortSettingPopUpWidget("IP/Port Settings")
    DisplayStatusBarMessageThread()

# =====================================================================
# Update timer and thread functions
# =====================================================================

def position_update():
    """Current position update"""

    global current_position_value
    global rotational_controller_plot

    current_position_value = str(rotational_controller_plot.get_current_position_value())
    current_position.setText(current_position_value)

def preset_settings_update():
    """Update fields with selected preset values"""

    name = str(presets.currentText()) 
    position.setText(preset_table[name]["position"])
    velocity.setText(preset_table[name]["velocity"])
    acceleration.setText(preset_table[name]["acceleration"])

def parameter_update():
    """Update the velocity, acceleration, and position min/max range (low,high) of input"""

    global velocity_min
    global velocity_max 
    global acceleration_min 
    global acceleration_max 
    global position_min 
    global position_max 
    global home_flag 
    global units
    global position
    global velocity 
    global acceleration 
    global rotational_controller_plot 
    global home
    
    if rotational_controller_plot.get_parameter_verified():
        position.clear()
        velocity.clear()
        acceleration.clear()
        velocity_min, velocity_max, acceleration_min, acceleration_max, position_min, position_max, home_flag, units = rotational_controller_plot.get_parameter_information()
        if home_flag == 'false':
            home.setEnabled(False)
        else:
            home.setEnabled(True)
        position.setValidator(QtGui.QIntValidator(int(position_min), int(position_max)))
        velocity.setValidator(QtGui.QIntValidator(int(velocity_min), int(velocity_max)))
        acceleration.setValidator(QtGui.QIntValidator(int(acceleration_min), int(acceleration_max)))

def initialize_status_colors():
    """Display port connection status indicators"""

    global position_status
    global parameter_status 
    global plot_status
    global plot
    global rotational_controller_plot

    style_setting_valid = "border-radius: 6px; padding:5px; background-color: #5fba7d"
    style_setting_invalid  = "border-radius: 6px; padding:5px; background-color: #f78380"

    if rotational_controller_plot.get_position_verified():
        position_status.setStyleSheet(style_setting_valid) 
        logging.info('Successfully connected to position socket')
    else:
        position_status.setStyleSheet(style_setting_invalid)
        logging.info('Failed to connect to position socket')

    if rotational_controller_plot.get_parameter_verified():
        parameter_status.setStyleSheet(style_setting_valid) 
        logging.info('Successfully connected to parameter socket')
    else:
        parameter_status.setStyleSheet(style_setting_invalid)
        logging.info('Failed to connect to parameter socket')

    if plot.get_verified():
        plot_status.setStyleSheet(style_setting_valid)
        logging.info('Successfully connected to plot socket')
    else:
        plot_status.setStyleSheet(style_setting_invalid)
        logging.info('Failed to connect to plot socket')

def initialize_global_variables():
    """Initialize socket connections and parameter settings"""

    global velocity_min
    global velocity_max 
    global acceleration_min 
    global acceleration_max 
    global position_min 
    global position_max 
    global home_flag 
    global units
    global rotational_controller_plot
    global parameter_socket
    global position_socket

    if rotational_controller_plot.get_parameter_verified():
        velocity_min, velocity_max, acceleration_min, acceleration_max, position_min, position_max, home_flag, units = rotational_controller_plot.get_parameter_information()
        parameter_socket = rotational_controller_plot.get_parameter_socket()
    if rotational_controller_plot.get_position_verified():
        position_socket = rotational_controller_plot.get_position_socket()

# =====================================================================
# Utility Functions 
# =====================================================================

def clear_plots():
    """Clear plot data"""

    global plot
    global rotational_controller_plot
    global status_bar

    plot.clear_ZMQ_plot()
    rotational_controller_plot.clear_rotational_controller_plot()
    logging.info("Cleared plots")
    status_bar.showMessage('Plots cleared', 4000)

def change_to_default_theme():
    app.setStyleSheet(load_CSS(0))

def change_to_dark_theme():
    app.setStyleSheet(load_CSS(1))

def change_plot_color(plotObject):
    """Opens color palette selector to change color"""

    def change_plot_color_thread():
        plot_color = PlotColorWidget(plotObject)
    Thread(target=change_plot_color_thread(), args=()).start()
    logging.info("Changed {} plot color".format(type(plotObject)))

def exit_application():
    """Exit program event handler"""

    logging.info('Closed application')
    exit(1)

# =====================================================================
# Main GUI Application
# =====================================================================

# Create main application window
app = QtGui.QApplication([])
app.setStyleSheet(load_CSS(1))
app.setStyle(QtGui.QStyleFactory.create("Cleanlooks"))
mw = QtGui.QMainWindow()
mw.setWindowTitle('Rotational Controller GUI')

# Start logger
initialize_logger()

# Read in configuration settings
read_settings()

# Initialize status_bar
status_bar = QtGui.QStatusBar()
mw.setStatusBar(status_bar)
status_bar.setSizeGripEnabled(False)

# Create ZMQ plot and rotational controller plot
plot = ZMQPlotWidget(ZMQ_address, ZMQ_topic, ZMQ_frequency)
rotational_controller_plot = RotationalControllerPlotWidget(position_address, position_topic, position_frequency, parameter_address)

initialize_global_variables()

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
ml.addWidget(plot.get_ZMQ_plot_widget(),1,0,1,1)
ml.addWidget(rotational_controller_plot.get_rotational_controller_plot_widget(),0,1,2,1)
mw.setSizePolicy(QtGui.QSizePolicy.Fixed, QtGui.QSizePolicy.Fixed)

# Menubar/Toolbar
mb = mw.menuBar()
file_menu = mb.addMenu('&File')
display_menu = mb.addMenu('&Display')
format_menu = mb.addMenu('&Format')

# File menu
port_change_action = QtGui.QAction('Change Port Settings', mw)
port_change_action.setShortcut('Ctrl+P')
port_change_action.setStatusTip('Change position, parameter, or plot port settings')
port_change_action.triggered.connect(change_IP_port_settings_button)
file_menu.addAction(port_change_action)

move_action = QtGui.QAction('Move', mw)
move_action.setShortcut('Ctrl+M')
move_action.setStatusTip('Move to specified position')
move_action.triggered.connect(move_button)
file_menu.addAction(move_action)

home_action = QtGui.QAction('Home', mw)
home_action.setShortcut('Ctrl+H')
home_action.setStatusTip('Reset rotational controller to home position')
home_action.triggered.connect(home_button)
file_menu.addAction(home_action)

add_preset_button = QtGui.QAction('Add Preset', mw)
add_preset_button.setShortcut('Ctrl+A')
add_preset_button.setStatusTip('Save current values into a preset setting')
add_preset_button.triggered.connect(add_preset_settings_button)
file_menu.addAction(add_preset_button)

exit_action = QtGui.QAction('Exit', mw)
exit_action.setShortcut('Ctrl+Q')
exit_action.setStatusTip('Exit application')
exit_action.triggered.connect(exit_application)
file_menu.addAction(exit_action)

# Display Menu
clear_graph_action = QtGui.QAction('Clear Plots', mw)
clear_graph_action.setShortcut('Ctrl+C')
clear_graph_action.setStatusTip('Clear current plot views')
clear_graph_action.triggered.connect(clear_plots)
display_menu.addAction(clear_graph_action)

change_ZMQ_plot_color_action = QtGui.QAction('Change ZMQ Plot Color', mw)
change_ZMQ_plot_color_action.setStatusTip('Change ZMQ plot color')
change_ZMQ_plot_color_action.triggered.connect(lambda: change_plot_color(plot))
display_menu.addAction(change_ZMQ_plot_color_action)

change_rotational_controller_plot_color_action = QtGui.QAction('Change Rotational Controller Plot Color ', mw)
change_rotational_controller_plot_color_action.setStatusTip('Change rotational controller plot color')
change_rotational_controller_plot_color_action.triggered.connect(lambda: change_plot_color(rotational_controller_plot))
display_menu.addAction(change_rotational_controller_plot_color_action)

change_to_default_theme_action = QtGui.QAction('Change To Default Theme', mw)
change_to_default_theme_action.setShortcut('Ctrl+T')
change_to_default_theme_action.setStatusTip('Change Rotational Controller to default color theme')
change_to_default_theme_action.triggered.connect(change_to_default_theme)
display_menu.addAction(change_to_default_theme_action)

change_to_dark_theme_action = QtGui.QAction('Change To Dark Theme', mw)
change_to_dark_theme_action.setShortcut('Ctrl+D')
change_to_dark_theme_action.setStatusTip('Change Rotational Controller to dark color theme')
change_to_dark_theme_action.triggered.connect(change_to_dark_theme)
display_menu.addAction(change_to_dark_theme_action)

# Format Menu
write_to_file_toggle = QtGui.QAction('Save Port Settings', mw, checkable=True)
write_to_file_toggle.setShortcut('Ctrl+S')
write_to_file_toggle.setStatusTip('Save port setting changes to rotational.ini')
write_to_file_toggle.triggered.connect(write_port_settings_toggle)
format_menu.addAction(write_to_file_toggle)

# GUI elements
status_label = QtGui.QLabel('Port Status')
position_status = QtGui.QLabel('Position')
position_status.setAlignment(QtCore.Qt.AlignCenter)
parameter_status = QtGui.QLabel('Parameter')
parameter_status.setAlignment(QtCore.Qt.AlignCenter)
plot_status = QtGui.QLabel('Plot')
plot_status.setAlignment(QtCore.Qt.AlignCenter)

port_settings = QtGui.QPushButton('IP/Port Settings')
port_settings.clicked.connect(change_IP_port_settings_button)

velocity_label = QtGui.QLabel()
velocity_label.setText('Velocity (deg/s)')
velocity = QtGui.QLineEdit()
velocity.setAlignment(QtCore.Qt.AlignLeft)

acceleration_label = QtGui.QLabel()
acceleration_label.setText('Acceleration (deg/s^2)')
acceleration = QtGui.QLineEdit()
acceleration.setAlignment(QtCore.Qt.AlignLeft)

position_label = QtGui.QLabel()
position_label.setText('Position (deg)')
position = QtGui.QLineEdit()
position.setAlignment(QtCore.Qt.AlignLeft)

current_position_label = QtGui.QLabel()
current_position_label.setText('Current Position')
current_position = QtGui.QLabel()

move = QtGui.QPushButton('Move')
move.clicked.connect(move_button)

home = QtGui.QPushButton('Home')
home.clicked.connect(home_button)

# Disable home button if unavailable
if rotational_controller_plot.get_parameter_verified():
    if home_flag == 'false':
        home.setEnabled(False)

preset_table = {}
preset_label = QtGui.QLabel()
preset_label.setText('Presets')
presets = QtGui.QComboBox()
presets.activated.connect(preset_settings_update)
preset_name = QtGui.QLineEdit()
preset_name.setFixedWidth(80)
preset_name.setPlaceholderText("Preset name")
preset_button = QtGui.QPushButton('Add Preset')
preset_button.clicked.connect(add_preset_settings_button)
preset_layout = QtGui.QHBoxLayout()
preset_layout.addWidget(presets)
preset_layout.addWidget(preset_name)
preset_layout.addWidget(preset_button)

parameter_update()
initialize_status_colors()

# Layout
l.addWidget(status_label,0,0,1,1)
l.addWidget(position_status,0,1,1,1)
l.addWidget(parameter_status,0,2,1,1)
l.addWidget(plot_status,0,3,1,1)

l.addWidget(port_settings,1,0,1,4)
l.addWidget(velocity_label,2,0,1,2)
l.addWidget(velocity,2,2,1,2)
l.addWidget(acceleration_label,3,0,1,2)
l.addWidget(acceleration,3,2,1,2)
l.addWidget(position_label,4,0,1,2)
l.addWidget(position,4,2,1,2)
l.addWidget(current_position_label,5,0,1,2)

l.addWidget(current_position,5,2,1,2)
l.addWidget(move,6,0,1,4)
l.addWidget(home,7,0,1,4)
l.addWidget(preset_label,8,0,1,1)
l.addWidget(presets,8,1,1,1)
l.addWidget(preset_name,8,2,1,1)
l.addWidget(preset_button,8,3,1,1)

# Start internal timers and threads 
position_update_timer = QtCore.QTimer()
position_update_timer.timeout.connect(position_update)
# Plot refresh rate 
position_update_timer.start(rotational_controller_plot.get_rotational_controller_plot_refresh_rate())

mw.statusBar()
mw.show()

if __name__ == '__main__':
    if(sys.flags.interactive != 1) or not hasattr(QtCore, 'PYQT_VERSION'):
        QtGui.QApplication.instance().exec_()


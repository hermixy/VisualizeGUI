import zmq
import time
import json
import random
import os

class UniversalPlotServerIMULogger(object):
    """Plots dynamic amount of curves"""

    def __init__(self):
        self.initialize_server()
        self.initialize_data_file_location()
        self.get_initial_data_points()
        self.initialize_data_packet()

    def serialize(self, topic, data):
        """Transform data into json format"""

        return str(topic) + " " + json.dumps(data)

    def initialize_server(self):
        """Establish ZMQ socket connection"""
        
        # Pub/sub pattern for async connections
        self.plot_context = zmq.Context()
        self.plot_socket = self.plot_context.socket(zmq.PUB)  
        self.plot_socket.bind("tcp://*:6020")
        self.plot_topic = 20000

    def initialize_data_file_location(self):
        self.path = '../../IMU_pi_logger/logs'

        if not os.path.exists(self.path):
            print("No log files, is logger on?")
            exit(1)
        else:
            self.filename = self.get_log_file_name()
            self.file_path = self.path + '/' + self.filename
    
    def get_log_file_name(self):

        def extract_digits(filename):
            s = ''
            for char in filename:
                if char.isdigit():
                    s += char
            return int(s)

        l = [extract_digits(filename) for filename in os.listdir(self.path)]

        # Directory is empty
        if not l:
            print('No log files, is logger on?')
            exit(1)
        # Directory has files so find latest
        else:
            latest_file_number = max(l)
            return 'IMU' + '{0:04d}'.format(latest_file_number) + '.log'
    
    def initialize_data_packet(self):
        """Construct data packet information according to format:

        data_packet = {
            'x': {
                'label': string,
                'units': string,
                'value': float
                },
            'y1': {
                'label': string,
                'units': string,
                'curve': {
                    'curve0': float/int,
                    'curve1': float/int,
                    ...
                },
            'y2': {
                'label': string,
                'units': string,
                'curve': {
                    'curve2': float/int,
                    'curve3': float/int,
                    ...
                 },
            ...
        }
        """

        self.x_label = 'Time'
        self.x_units = 's'
        self.x_value = self.send_current_time()
        self.y1_label = 'IMU'
        self.y1_units = 'm/s^2'
        self.y1_curves = {
                'x': 0,
                'y': 0
        }
        self.y2_label = 'IMU1'
        self.y2_units = 'm/s^2'
        self.y2_curves = {
                'z': 0
        }

        self.data_packet = {
            'x': {
                'label': self.x_label,
                'units': self.x_units,
                'value': self.x_value
            },
            'y1': {
                'label': self.y1_label,
                'units': self.y1_units,
                'curve': self.y1_curves
            },
            'y2': {
                'label': self.y2_label,
                'units': self.y2_units,
                'curve': self.y2_curves
            }
        }
    
    def get_initial_data_points(self):
        self.inital_points = False
        while not self.inital_points:
            with open(self.file_path, 'r') as fh:
                fh.seek(-100, os.SEEK_END)
                raw_data = fh.readlines()[-1].decode().strip()
                if len(raw_data) == 56 and raw_data[23:29] == '$VNACC':
                    date, raw_timestamp, mode, x, y, z = raw_data.split(',')
                    self.seconds = self.convert_timestamp_to_seconds(str(raw_timestamp))

                    self.x = float(x)
                    self.y = float(y)
                    self.z = float(z[:-3])
                    self.inital_points = True

    def read_latest_data(self):
        with open(self.file_path, 'r') as fh:
            fh.seek(-100, os.SEEK_END)
            raw_data = fh.readlines()[-1].decode().strip()
            
            if len(raw_data) == 56 and raw_data[23:29] == '$VNACC':
                date, raw_timestamp, mode, x, y, z = raw_data.split(',')
                self.seconds = self.convert_timestamp_to_seconds(str(raw_timestamp))
                self.x = float(x)
                self.y = float(y)
                self.z = float(z[:-3])
            
    def convert_timestamp_to_seconds(self, timestamp):
        h,m,s = timestamp.split(':')
        return float(h) * 3600.0 + float(m) * 60.0 + float(s) 

    def update_data(self):
        """Update data table and generate new data string"""
        
        self.read_latest_data()
        for axis in self.data_packet:
            if axis != 'x':
                for curve in self.data_packet[axis]['curve']:
                    if curve == 'x':
                        self.data_packet[axis]['curve'][curve] = self.x
                    elif curve == 'y':
                        self.data_packet[axis]['curve'][curve] = self.y
                    elif curve == 'z':
                        self.data_packet[axis]['curve'][curve] = self.z
            else:
                self.data_packet['x']['value'] = self.send_current_time()

    def print_data(self,data):
        """Unpack and print json data"""

        print(json.dumps(data, indent=4, sort_keys=True))

    def server_loop(self):
        """Update curve data and send packet"""

        self.update_data()
        self.plot_socket.send(self.serialize(self.plot_topic, self.data_packet))
        # self.print_data(self.data_packet)

    def send_current_time(self):
        """Current timestamp"""
        return self.seconds

if __name__ == '__main__':
    universal_plot_server_IMU_logger = UniversalPlotServerIMULogger()
    while True:
        universal_plot_server_IMU_logger.server_loop()


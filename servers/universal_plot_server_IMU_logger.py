import zmq
import time
import json
import random
import os

class UniversalPlotServerIMULogger(object):
    """Plots dynamic amount of curves"""

    def __init__(self):
        self.initialize_server()
        self.initialize_data_packet()
        self.initialize_data_file_location()

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
        self.path = '/IMU_pi_logger/logs'

        if not os.path.exists(self.path):
            print('Path does not exist')
            exit(1)
        else:
            print('path exists')
            exit(1)
            self.filename = self.get_log_file_name()
            print(self.filename)
    
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
        self.y1_label = 'Pressure'
        self.y1_units = 'Pa'
        self.y1_curves = {
                'curve0': 0,
                'curve1': 0,
                'curve2': 0,
                'curve3': 0,
                'curve5': 0,
                'curve6': 0
        }
        self.y2_label = 'Temperature'
        self.y2_units = 'C'
        self.y2_curves = {
                'curve7': 2,
                'curve8': 2,
                'curve9': 2,
                'curve10': 2,
                'curve11': 2,
                'curve12': 2
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

    def update_data(self):
        """Update data table and generate new data string"""

        for axis in self.data_packet:
            if axis != 'x':
                for curve in self.data_packet[axis]['curve']:
                    self.data_packet[axis]['curve'][curve] += random.randint(low + diff, high + diff) + self.increment
                    self.increment += 10 
                    diff += 100
            else:
                self.data_packet['x']['value'] = self.send_current_time()

    def print_data(self,data):
        """Unpack and print json data"""

        print(json.dumps(data, indent=4, sort_keys=True))

    def server_loop(self):
        """Update curve data and send packet"""

        self.update_data()
        self.plot_socket.send(self.serialize(self.plot_topic, self.data_packet))
        self.print_data(self.data_packet)

    def send_current_time(self):
        """Elapsed time in (ms)"""
        pass
if __name__ == '__main__':
    universal_plot_server_IMU_logger = UniversalPlotServerIMULogger()
    while True:
        universal_plot_server_IMU_logger.server_loop()
        time.sleep(0.025)


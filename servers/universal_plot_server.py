import zmq
import time
import json
import random

class UniversalPlotServer(object):
    """Plots dynamic amount of curves"""

    def __init__(self):
        self.initialize_server()
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
        self.x_units = 'Timestamp'
        self.x_value = 10
        self.y1_label = 'Pressure'
        self.y1_units = 'Pa'
        self.y1_curves = {
                'curve0': 0,
                'curve1': 1,
                'curve2': 0,
                'curve3': 1
        }
        self.y2_label = 'Temperature'
        self.y2_units = 'C'
        self.y2_curves = {
                'curve4': 2,
                'curve5': 3,
                'curve6': 2,
                'curve7': 3,
                'curve8': 2,
                'curve9': 3
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
        low = 10
        high = 100
        diff = 0

        for axis in self.data_packet:
            if axis != 'x':
                for curve in self.data_packet[axis]['curve']:
                    self.data_packet[axis]['curve'][curve] = random.randint(low + diff, high + diff)
                    diff += 100
        
    def print_data(self,data):
        """Unpack and print json data"""

        print(json.dumps(data, indent=4, sort_keys=True))

    def server_loop(self):
        """Update curve data and send packet"""

        self.update_data()
        self.plot_socket.send(self.serialize(self.plot_topic, self.data_packet))
        self.print_data(self.data_packet)

if __name__ == '__main__':
    universal_plot_server = UniversalPlotServer()
    while True:
        universal_plot_server.server_loop()
        time.sleep(0.025)


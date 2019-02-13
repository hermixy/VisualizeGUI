import zmq
import time
import json
import random

class UniversalPlotServer(object):
    """Plots dynamic amount of traces"""

    def __init__(self):
        self.initialize_server()
        self.initialize_data_packet()
    
    def serialize(self, topic, data):
        return str(topic) + " " + json.dumps(data)

    def initialize_server(self):
        """Establish ZMQ socket connection, # of traces, and # of y scales"""
        
        self.plot_context = zmq.Context()
        # Pub/sub pattern for async connections
        self.plot_socket = self.plot_context.socket(zmq.PUB)  
        self.plot_socket.bind("tcp://*:6020")
        self.plot_topic = 20000
        
    def initialize_data_packet(self):
        """Construct data packet header information according to format"""

        self.traces = 6
        self.scales = 2
        self.right_plots = [1,3,5]
        self.left_plots = [0,2,4]

        self.right_label = 'Temperature'
        self.left_label = 'Pressure'
        self.bottom_label = 'Points'

        self.right_units = 'C'
        self.left_units = 'Pa'
        self.bottom_units = '#'

        self.data_packet = {
            'traces': self.traces,
            'scales': self.scales,
            'plots': {
                    'right': self.right_plots,
                    'left': self.left_plots
                    },
            'labels': {
                    'right': self.right_label,
                    'left': self.left_label,
                    'bottom': self.bottom_label
                    },
            'units': {
                    'right': self.right_units,
                    'left': self.left_units,
                    'bottom': self.bottom_units
                    }
        }
        
        self.plot_data = {}

    def update_data(self):
        """Update data table and generate new data string"""
        low = 10
        high = 100
        diff = 0
        for trace in range(self.traces):
            self.plot_data['trace' + str(trace)] = random.randint(low + diff, high + diff)
        self.data_packet['data'] = self.plot_data
        
    def print_data(self,data):
        print(json.dumps(data, indent=4, sort_keys=True))

    def server_loop(self):
        self.update_data()
        self.plot_socket.send(self.serialize(self.plot_topic, self.data_packet))
        print('sent')

if __name__ == '__main__':
    universal_plot_server = UniversalPlotServer()
    while True:
        universal_plot_server.server_loop()
        time.sleep(0.025)


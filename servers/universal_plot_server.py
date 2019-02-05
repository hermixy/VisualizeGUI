import zmq
import time
import random

class UniversalPlotServer(object):
    """Plots dynamic amount of traces"""

    def __init__(self):
        self.initialize_server()
        self.initialize_data_message()

    def initialize_server(self):
        """Establish ZMQ socket connection, # of traces, and # of y scales"""
        
        self.plot_context = zmq.Context()
        # Pub/sub pattern for async connections
        self.plot_socket = self.plot_context.socket(zmq.PUB)  
        self.plot_socket.bind("tcp://*:6020")
        self.plot_topic = 20000

        self.traces = 30

        # 1 y scale defaults to left side, 2 y scales means both sides
        self.y_scales = 1

        # Trace name to place on each y scale separated by :
        self.y_axis_left = '0:1:2'
        self.y_axis_right = '3:4'

    def initialize_data_message(self):
        # Number of traces, Number of Y scales, left y plots, right y plots, curve_name1, curve_data1, ...
        self.message_header = "{},{},{},{},".format(str(self.traces),
                                                  str(self.y_scales),
                                                  str(self.y_axis_left),
                                                  str(self.y_axis_right))
        self.curve_data_table = {}
    
    def update_data(self):
        """Update data table and generate new data string"""
        
        # Generate new data
        low = 10
        high = 100
        diff = 0
        for trace in range(self.traces):
            self.curve_data_table['trace' + str(trace)] = random.randint(low + diff, high + diff)
            diff += 100
        
        self.curve_message_data = ''

        # Generate new data string
        for trace in range(self.traces):

            self.curve_message_data += 'trace' + str(trace) + ',' + str(self.curve_data_table['trace' + str(trace)])
            # Prevent appending comma to last data point
            if trace < (self.traces - 1):
                self.curve_message_data += ','

        self.message_data = self.message_header +  self.curve_message_data
        #print(self.message_data)

    def server_loop(self):
        self.update_data()
        self.plot_socket.send("%d %s" % (self.plot_topic, self.message_data))

if __name__ == '__main__':
    universal_plot_server = UniversalPlotServer()
    while True:
        universal_plot_server.server_loop()
        time.sleep(0.025)


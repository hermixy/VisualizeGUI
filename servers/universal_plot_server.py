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

        self.traces = 6

        # 1 y scale defaults to left side, 2 y scales means both sides
        self.y_scales = 2

        # Trace name to place on each y scale separated by :
        # self.left_y_plots = '0:1:2:3:4:5:6:7:8:9:10:11:12:13:14'
        # self.right_y_plots = '15:16:17:18:19:20:21:22:23:24:25:26:27:28:29'
        self.left_y_plots = '0:2:4'
        self.right_y_plots = '1:3:5'

        self.left_y_label = 'left'
        self.left_y_units = 'l'
        self.right_y_label = 'right'
        self.right_y_units = 'r'
        self.x_label = 'Points'
        self.x_units = '#'

    def initialize_data_message(self):
        """Construct data packet according to format"""

        # Header format:
        # [# of traces, # Y scales, left Y plots, right Y plots, left Y label, left Y units,
        #  right Y label, right Y units, X label, X units]
        
        # Data format:
        # [curve_name1, curve_data1, curve_name2, curve_data2, ...]

        self.message_header = "{},{},{},{},{},{},{},{},{},{},".format(str(self.traces),
                                                                      str(self.y_scales),
                                                                      str(self.left_y_plots),
                                                                      str(self.right_y_plots),
                                                                      str(self.left_y_label),
                                                                      str(self.left_y_units),
                                                                      str(self.right_y_label),
                                                                      str(self.right_y_units),
                                                                      str(self.x_label),
                                                                      str(self.x_units))
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
        # print(self.message_data)

    def server_loop(self):
        self.update_data()
        self.plot_socket.send("%d %s" % (self.plot_topic, self.message_data))

if __name__ == '__main__':
    universal_plot_server = UniversalPlotServer()
    while True:
        universal_plot_server.server_loop()
        time.sleep(0.025)


import zmq
import time
import json

def print_data(data):
    print(json.dumps(data, indent=4, sort_keys=True))
plot_context = zmq.Context()
plot_socket = plot_context.socket(zmq.PUB)  
plot_socket.bind("tcp://*:6020")
plot_topic = 20000

traces = 6
scales = 2
right_plots = [1,3,5]
left_plots = [0,2,4]

right_label = 'Temperature'
left_label = 'Pressure'
bottom_label = 'Points'

right_units = 'C'
left_units = 'Pa'
bottom_units = '#'

data_packet = {
    'traces': traces,
    'scales': scales,
    'plots': {
            'right': right_plots,
            'left': left_plots 
            },
    'labels': {
            'right': right_label,
            'left': left_label,
            'bottom': bottom_label
            },
    'units': {
            'right': right_units,
            'left': left_units,
            'bottom': bottom_units
            }
}

def serialize(topic, data):
    return str(topic) + " " + json.dumps(data)
while True:
    plot_socket.send(serialize(plot_topic, data_packet))
    print('sent')
    time.sleep(.1)

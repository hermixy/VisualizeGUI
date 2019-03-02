import zmq
import time
import json

plot_address = 'tcp://192.168.1.143:6020'
plot_topic = '20000'

context = zmq.Context()
socket = context.socket(zmq.SUB)
socket.connect(plot_address)
socket.setsockopt(zmq.SUBSCRIBE, plot_topic)

def deserialize(data):
    raw_json = data.find('{')
    topic = data[0:raw_json].strip()
    msg = json.loads(data[raw_json:])
    return topic, msg

def print_data(data):
    print(json.dumps(data, indent=4, sort_keys=True))

while True:
    try:
        topic, data = deserialize(socket.recv(zmq.NOBLOCK))
        print_data(data)
    except zmq.ZMQError, e:
        print('e')
        pass
    time.sleep(.1)




import zmq
import random
import sys
import time

port = "6002"
if len(sys.argv) > 1:
   port = sys.argv[1]
   int(port)

context = zmq.Context()
socket = context.socket(zmq.PUB)
socket.bind("tcp://*:6002")

messagedata = 0

while True:
   topic = 10001
   #messagedata += 1
   messagedata = random.randint(1,101)
   print "%d %d" % (topic, messagedata)
   socket.send("%d %d" % (topic, messagedata))
   # Frequency = 1 / Time (s)
   time.sleep(.025)

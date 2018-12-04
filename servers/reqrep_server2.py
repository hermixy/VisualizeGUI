import zmq
import random
import sys
import time

port = "6009"
if len(sys.argv) > 1:
   port = sys.argv[1]
   int(port)

context = zmq.Context()
socket = context.socket(zmq.PUB)
socket.bind("tcp://*:6009")

messagedata = 0

while True:
   topic = 10009
   #messagedata += 1
   messagedata = random.randint(500,1000)
   print "%d %d" % (topic, messagedata)
   socket.send("%d %d" % (topic, messagedata))
   time.sleep(.5)

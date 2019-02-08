import zmq
import time
import random

context = zmq.Context()
rr_socket = context.socket(zmq.REP)
p_socket = context.socket(zmq.PUB)
rr_socket.bind("tcp://*:6010")
p_socket.bind("tcp://*:6011")

V_Lim = (-100, 100)
A_Lim = (-1000, 1000)
P_Lim = (-360, 360)
HOME_STATE = 'true'
UNITS = 'degrees'

topic = 10000
messagedata = 0.0

def ZMQ_Server_Loop():
   valid = True
   try:
       request_message = rr_socket.recv(zmq.NOBLOCK)
       reply_message = ''
       try:
           if 'info?' in request_message:
               reply_message += str(V_Lim[0])
               reply_message += ','+str(V_Lim[1])
               reply_message += ','+str(A_Lim[0])
               reply_message += ','+str(A_Lim[1])
               reply_message += ','+str(P_Lim[0])
               reply_message += ','+str(P_Lim[1])
               reply_message += ','+HOME_STATE
               reply_message += ','+UNITS
               print 'reply_message'
           elif 'move' in request_message:
               request_message = request_message.strip().split()
               if len(request_message) != 4:
                   reply_message += 'move_nack'
                   print 'invalid move'
               else:
                   velocity = float(request_message[1])
                   acceleration =  float(request_message[2])
                   position = float(request_message[3])
                   if not V_Lim[0] <= velocity <= V_Lim[1]:
                       valid = False
                   elif not A_Lim[0] <= acceleration <= A_Lim[1]:
                       valid = False
                   elif not P_Lim[0] <= position <= P_Lim[1]:
                       valid = False

                   if valid:
                       reply_message += 'move_ack'+','+request_message[1]+','+request_message[2]+','+request_message[3]
                   else:
                       reply_message = 'move_nack'
                   print 'move'
           elif 'home' in request_message:
               reply_message += 'home_ack'
               print 'home'
           else:
               reply_message += 'invalid'
               print 'invalid'
       except:
           pass
       rr_socket.send(reply_message)
   except zmq.Again as e:
       pass
   messagedata = random.random()
   p_socket.send("%d %.2f" % (topic, messagedata))

while True:
   ZMQ_Server_Loop()
   time.sleep(0.25)

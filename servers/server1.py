import zmq
import time
import random
import serial
import sys

ser = serial.Serial(sys.argv[1])
ser.baudrate = 57600
time.sleep(1)
ser.write('1OR\r\n')

context = zmq.Context()
rr_socket = context.socket(zmq.REP)
p_socket = context.socket(zmq.PUB)
rr_socket.bind("tcp://*:6010")
p_socket.bind("tcp://*:6011")

V_Lim = (0, 16)
A_Lim = (0, 160)
P_Lim = (-165, 165)
HOME_STATE = 'true'
UNITS = 'degrees'

topic = 10000
messagedata = 0.0

def Get_Position():
    global messagedata
    oldmessage = messagedata
    ser.write('1TP?\r\n')
    string = ser.readline().strip()
    try:
        messagedata = float(string[3:])
    except:
        messagedata = oldmessage

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
                        print(valid)
                        print(position)
                        ser.write('1VA%.2f\r\n'%velocity)
                        ser.write('1AC%.2f\r\n'%acceleration)
                        ser.write('1PA%.2f\r\n'%position)
                        reply_message += 'move_ack'+','+request_message[1]+','+request_message[2]+','+request_message[3]
                    else:
                        reply_message = 'move_nack'
                    print 'move'
            elif 'home' in request_message:
                ser.write('1PA0.0f\r\n')
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
    Get_Position()
    p_socket.send("%d %.2f" % (topic, messagedata))

while True:
    ZMQ_Server_Loop()
    time.sleep(0.025)

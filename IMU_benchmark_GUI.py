from PyQt4 import QtCore, QtGui 
from threading import Thread
import pyqtgraph as pg
import numpy as np
import zmq
import sys
import time
import configparser

def readSettings():
    global IMU_list

    try:
        config = configparser.ConfigParser()
        config.read('IMU.ini')
        # Pub/Sub 192.168.1.133:6010 10000
        reference_address = str(config['REFERENCE']['referenceAddress'])
        reference_topic = str(config['REFERENCE']['referenceTopic'])
        reference_sleep_frequency = float(config['REFERENCE']['sleepFrequency'])
        reference_timer_frequency = reference_sleep_frequency * 1000
       
        IMU_list = []
        IMU_list.append((reference_address, reference_topic, reference_sleep_frequency, reference_timer_frequency))
        numberOfIMUs = int(config['IMU']['numberOfIMUs'])
        if numberOfIMUs > 0:
            for imu in range(1, numberOfIMUs + 1):
                IMU_address = str(config['IMU']['IMU' + str(imu) + 'Address'])
                IMU_topic = str(config['IMU']['IMU' + str(imu) + 'Topic'])
                # time.sleep (s)
                IMU_sleep_frequency = float(config['IMU']['IMU' + str(imu) + 'SleepFrequency'])
                # timer.timer (ms)
                IMU_timer_frequency = IMU_sleep_frequency * 1000
                IMU_list.append((IMU_address, IMU_topic, IMU_sleep_frequency, IMU_timer_frequency))
    except KeyError:
        print('File doesnt exist')
        exit(1)

def initZMQHandshake():
    global IMU_list
    global IMU_sockets
    global IMU_position
    global IMU_timestamp 
    global IMU_topic
    global IMU_plot_buffer
    global IMU_plot_data
    
    try:
        IMU_sockets = []
        IMU_position = []
        IMU_timestamp = []
        IMU_topic = []
        IMU_plot_buffer = []
        IMU_plot_data = []
        for imu in range(len(IMU_list)):
            context = zmq.Context()
            socket = context.socket(zmq.SUB)
            socket.connect(IMU_list[imu][0])
            socket.setsockopt(zmq.SUBSCRIBE, IMU_list[imu][1])
            topic, timestamp, position = socket.recv().split()
            IMU_topic.append(topic)
            IMU_timestamp.append(timestamp)
            IMU_position.append(position)
            IMU_sockets.append(socket)

    except:
        print("no socket")

def plotBufferInit():
    reference_plot_buffer = int((abs(left_x) + abs(right_x))/sleep_frequency)
    reference_plot_data = []
    IMU1_plot_buffer = int((abs(left_x) + abs(right_x))/sleep_frequency)
    IMU1_plot_data = []
def readDataThread():
    global reference_socket
    global reference_timestamp 
    global reference_position 
    global sleep_frequency
    
    while True:
        try:
            topic, reference_timestamp, reference_position = reference_socket.recv().split()
        except:
            print('error')
        time.sleep(sleep_frequency)

def readIMU1DataThread():
    global IMU1_socket
    global IMU1_timestamp 
    global IMU1_position 
    global sleep_frequency
    
    while True:
        try:
            topic, IMU1_timestamp, IMU1_position = IMU1_socket.recv().split()
        except:
            print('error')
        time.sleep(sleep_frequency)

app = QtGui.QApplication([])
app.setStyle(QtGui.QStyleFactory.create("Cleanlooks"))
mw = QtGui.QMainWindow()
mw.setWindowTitle('IMU Benchmark GUI')

cw = QtGui.QWidget()
l = QtGui.QGridLayout()
mw.setCentralWidget(cw)
cw.setLayout(l)

readSettings()
initZMQHandshake()
print(IMU_list)

print IMU_sockets
print IMU_position
print IMU_timestamp 
print IMU_topic
exit(1)

# Initial graph ranges and view spacing (right_x has to be 0)
left_x = -15
right_x = 0
x_axis = np.arange(left_x, right_x, IMU_list[0][3])
keference_plot_buffer = int((abs(left_x) + abs(right_x))/sleep_frequency)
reference_plot_data = []
IMU1_plot_buffer = int((abs(left_x) + abs(right_x))/sleep_frequency)
IMU1_plot_data = []

plot = pg.PlotWidget()
plot.addLegend()
plot.setXRange(left_x, right_x)
plot.setTitle('IMU Benchmark')
plot.setLabel('left', 'Position')
plot.setLabel('bottom', 'Timestamp')

reference_plot = plot.plot(name="Reference")
IMU1_plot = plot.plot(name="IMU1")
l.addWidget(plot, 1, 0, 1, 6)

reference_plot.setPen('w', width=2)
IMU1_plot.setPen('r', width=2)

def update():
    global reference_timestamp, IMU1_timestamp 
    global reference_position, IMU1_position 
    global reference_plot_buffer, reference_plot_data
    global reference_plot, IMU1
    global IMU1_plot_buffer, IMU1_plot_data
    global x_axis, plot, count, left_x, right_x
    global inverted_plot

    left_x += sleep_frequency
    right_x += sleep_frequency

    # Controls proper data movement
    reference_plot.setPos(right_x, 0)
    IMU1_plot.setPos(right_x, 0)

    # Controls axis shifting
    plot.setXRange(left_x, right_x)
    
    # Remove last item and append new item to simulate data shifting over
    if len(reference_plot_data) >= reference_plot_buffer:
        reference_plot_data.pop(0)
    if len(IMU1_plot_data) >= IMU1_plot_buffer:
        IMU1_plot_data.pop(0)
    
    reference_plot_data.append(float(reference_position))
    reference_plot.setData(x_axis[len(x_axis) - len(reference_plot_data):], reference_plot_data)

    IMU1_plot_data.append(float(IMU1_position))
    IMU1_plot.setData(x_axis[len(x_axis) - len(IMU1_plot_data):], IMU1_plot_data)

readReferenceDataThread = Thread(target=readReferenceDataThread, args=())
readReferenceDataThread.daemon = True
readReferenceDataThread.start()

readIMU1DataThread = Thread(target=readIMU1DataThread, args=())
readIMU1DataThread.daemon = True
readIMU1DataThread.start()

timer = QtCore.QTimer()
timer.timeout.connect(update)
timer.start(timer_frequency)

mw.show()

if __name__ == '__main__':
    import sys
    if(sys.flags.interactive != 1) or not hasattr(QtCore, 'PYQT_VERSION'):
        QtGui.QApplication.instance().exec_()


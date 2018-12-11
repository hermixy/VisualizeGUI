from PyQt4 import QtCore, QtGui 
from threading import Thread
import pyqtgraph as pg
import numpy as np
import zmq
import sys
import time

def initZMQHandshake():
    global reference_socket
    global IMU1_socket

    reference_context = zmq.Context()
    reference_socket = reference_context.socket(zmq.SUB)
    reference_socket.connect(reference_address)
    reference_socket.setsockopt(zmq.SUBSCRIBE, reference_topic)
    topic, reference_timestamp, reference_position = reference_socket.recv().split()

    IMU1_context = zmq.Context()
    IMU1_socket = IMU1_context.socket(zmq.SUB)
    IMU1_socket.connect(IMU1_address)
    IMU1_socket.setsockopt(zmq.SUBSCRIBE, IMU1_topic)
    topic, IMU1_timestamp, IMU1_position = IMU1_socket.recv().split()
    IMU2_position = -1 * IMU1_position

def readReferenceDataThread():
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
    global IMU2_position 
    global sleep_frequency
    
    while True:
        try:
            topic, IMU1_timestamp, IMU1_position = IMU1_socket.recv().split()
            IMU2_position = float(IMU1_position) * -1
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

# Pub/Sub 192.168.3.133:6010 10000
reference_address = "tcp://192.168.1.133:6010"
reference_topic = "10000"

# Pub/Sub 192.168.3.133:6011 10000
IMU1_address = "tcp://192.168.1.133:6011"
IMU1_topic = "10000"

# time.sleep (s)
sleep_frequency = .02 

# timer.timer (ms)
timer_frequency = sleep_frequency * 1000

initZMQHandshake()

# Initial graph ranges and view spacing (right_x has to be 0)
left_x = -15
right_x = 0
x_axis = np.arange(left_x, right_x, sleep_frequency)
reference_plot_buffer = int((abs(left_x) + abs(right_x))/sleep_frequency)
reference_plot_data = []
IMU1_plot_buffer = int((abs(left_x) + abs(right_x))/sleep_frequency)
IMU1_plot_data = []
IMU2_plot_buffer = int((abs(left_x) + abs(right_x))/sleep_frequency)
IMU2_plot_data = []

plot = pg.PlotWidget()
plot.addLegend()
plot.setXRange(left_x, right_x)
plot.setTitle('IMU Benchmark')
plot.setLabel('left', 'Position')
plot.setLabel('bottom', 'Timestamp')

reference_plot = plot.plot(name="Reference")
IMU1_plot = plot.plot(name="IMU1")
IMU2_plot = plot.plot(name="IMU2")
l.addWidget(plot, 1, 0, 1, 6)

reference_plot.setPen('w', width=2)
IMU1_plot.setPen('r', width=2)
IMU2_plot.setPen(26,170,85, width=2)

def update():
    global reference_timestamp, IMU1_timestamp 
    global reference_position, IMU1_position 
    global reference_plot_buffer, reference_plot_data
    global reference_plot, IMU1, IMU2
    global IMU1_plot_buffer, IMU1_plot_data
    global IMU2_plot_buffer, IMU2_plot_data
    global x_axis, plot, count, left_x, right_x
    global inverted_plot

    left_x += sleep_frequency
    right_x += sleep_frequency

    # Controls proper data movement
    reference_plot.setPos(right_x, 0)
    IMU1_plot.setPos(right_x, 0)
    IMU2_plot.setPos(right_x, 0)

    # Controls axis shifting
    plot.setXRange(left_x, right_x)
    
    # Remove last item and append new item to simulate data shifting over
    if len(reference_plot_data) >= reference_plot_buffer:
        reference_plot_data.pop(0)
    if len(IMU1_plot_data) >= IMU1_plot_buffer:
        IMU1_plot_data.pop(0)
    if len(IMU2_plot_data) >= IMU2_plot_buffer:
        IMU2_plot_data.pop(0)
    
    reference_plot_data.append(float(reference_position))
    reference_plot.setData(x_axis[len(x_axis) - len(reference_plot_data):], reference_plot_data)

    IMU1_plot_data.append(float(IMU1_position))
    IMU1_plot.setData(x_axis[len(x_axis) - len(IMU1_plot_data):], IMU1_plot_data)

    IMU2_plot_data.append(float(IMU2_position))
    IMU2_plot.setData(x_axis[len(x_axis) - len(IMU2_plot_data):], IMU2_plot_data)

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


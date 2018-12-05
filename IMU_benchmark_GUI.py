from PyQt4 import QtCore, QtGui 
from threading import Thread
from Queue import Queue
import pyqtgraph as pg
import numpy as np
import random
import zmq
import sys
import time

app = QtGui.QApplication([])
app.setStyle(QtGui.QStyleFactory.create("Cleanlooks"))
mw = QtGui.QMainWindow()
mw.setWindowTitle('IMU Benchmark GUI')
#mw.resize(1920, 1080)

cw = QtGui.QWidget()
l = QtGui.QGridLayout()
mw.setCentralWidget(cw)
cw.setLayout(l)
#labelStyle=('color':'#AAA', 'font-size': '14pt')

# Pub/Sub 192.168.3.133:6010 10000
reference_address = "tcp://192.168.1.133:6010"
reference_topic = "10000"
qReferenceX = Queue(maxsize=0)
qReferenceY = Queue(maxsize=0)

# Pub/Sub 192.168.3.133:6011 10000
IMU1_address = "tcp://192.168.1.133:6011"
IMU1_topic = "10000"
qIMU1X = Queue(maxsize=0)
qIMU1Y = Queue(maxsize=0)

# time.sleep (s)
sleep_frequency = .02 

# timer.timer (ms)
timer_frequency = sleep_frequency * 1000

def initZMQHandshake():
    global reference_socket
    global IMU1_socket

    reference_context = zmq.Context()
    reference_socket = reference_context.socket(zmq.SUB)
    reference_socket.connect(reference_address)
    reference_socket.setsockopt(zmq.SUBSCRIBE, reference_topic)

    IMU1_context = zmq.Context()
    IMU1_socket = IMU1_context.socket(zmq.SUB)
    IMU1_socket.connect(IMU1_address)
    IMU1_socket.setsockopt(zmq.SUBSCRIBE, IMU1_topic)

def readDataThread():
    global reference_socket
    global IMU1_socket

    global reference_timestamp 
    global IMU1_timestamp 

    global reference_position 
    global IMU1_position 
    
    while True:
        try:
            topic, reference_timestamp, reference_position = reference_socket.recv().split()
            topic, IMU1_timestamp, IMU1_position = IMU1_socket.recv().split()
        except:
            print('error')
        time.sleep(sleep_frequency)

initZMQHandshake()

left_x = -10
right_x = 0
x_axis = np.arange(left_x, right_x, sleep_frequency)
reference_plot_buffer = int((abs(left_x) + abs(right_x))/sleep_frequency)
reference_plot_data = []
IMU1_plot_buffer = int((abs(left_x) + abs(right_x))/sleep_frequency)
IMU1_plot_data = []

plot = pg.PlotWidget()
plot.setXRange(left_x, right_x)
plot.setTitle('IMU Benchmark')
plot.setLabel('left', 'Position')
plot.setLabel('right', 'Timestamp')

reference_plot = plot.plot()
IMU1_plot = plot.plot()
l.addWidget(plot, 1, 0, 1, 6)

reference_plot.setPen('g')
IMU1_plot.setPen('r')

readDataThread = Thread(target=readDataThread, args=())
readDataThread.daemon = True
readDataThread.start()

def update():
    global qReferenceX, qReferenceY
    global qIMU1X, qIMU1Y
    global reference_timestamp, IMU1_timestamp 
    global reference_position, IMU1_position 
    global reference_plot_buffer, reference_plot_data
    global reference_plot, IMU1
    global IMU1_plot_buffer, IMU1_plot_data
    global x_axis

    if len(reference_plot_data) >= reference_plot_buffer:
        reference_plot_data.pop(0)
    if len(IMU1_plot_data) >= IMU1_plot_buffer:
        IMU1_plot_data.pop(0)
    
    reference_plot_data.append(float(reference_position))
    reference_plot.setData(x_axis[len(x_axis) - len(reference_plot_data):], reference_plot_data)

timer = QtCore.QTimer()
timer.timeout.connect(update)
timer.start(timer_frequency)

mw.show()

if __name__ == '__main__':
    import sys
    if(sys.flags.interactive != 1) or not hasattr(QtCore, 'PYQT_VERSION'):
        QtGui.QApplication.instance().exec_()


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
    global left_x, right_x
    
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
            IMU_plot_buffer.append(int((abs(left_x) + abs(right_x))/IMU_list[imu][2]))
    except:
        print("ERROR: Unable to connect to socket")
        exit(1)

def createIMUPlots():
    global plot
    global IMU_plots
    global IMU_list

    colorTable = {'1': 'r',
                  '2': 'g',
                  '3': 'c',
                  '4': 'm',
                  '5': 'y',
                  '6': 'k',
                  '7': 'w'}

    IMU_plots = []
    for imu in range(len(IMU_list)):
        if imu == 0:
            p = plot.plot(name="Reference")
            p.setPen('w', width=2)
        elif imu <= len(colorTable):
            p = plot.plot(name="IMU" + str(imu))
            p.setPen(colorTable[str(imu)], width=2)
        else:
            p = plot.plot(name="IMU" + str(imu))
            p.setPen('w', width=2)

        IMU_plots.append(p)

def readDataThread(n, s, f):
    global IMU_timestamp
    global IMU_topic
    global IMU_position 
    
    while True:
        try:
            IMU_topic[n], IMU_timestamp[n], IMU_position[n] = s.recv().split()
        except:
            print('ERROR: Data update thread unable to recv')
        time.sleep(f)

app = QtGui.QApplication([])
app.setStyle(QtGui.QStyleFactory.create("Cleanlooks"))
mw = QtGui.QMainWindow()
mw.setWindowTitle('IMU Benchmark GUI')

cw = QtGui.QWidget()
l = QtGui.QGridLayout()
mw.setCentralWidget(cw)
cw.setLayout(l)

# Initial graph ranges and view spacing (right_x has to be 0)
left_x = -15
right_x = 0

readSettings()
initZMQHandshake()

x_axis = np.arange(left_x, right_x, IMU_list[0][2])

plot = pg.PlotWidget()
plot.addLegend()
plot.setXRange(left_x, right_x)
plot.setTitle('IMU Benchmark')
plot.setLabel('left', 'Position')
plot.setLabel('bottom', 'Timestamp')

createIMUPlots()
l.addWidget(plot, 1, 0, 1, 6)


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

IMU_threads = []

for imu in range(len(IMU_list)):
    thread = Thread(target=readDataThread, args=(imu, IMU_sockets[imu], IMU_list[imu][2]))
    thread.daemon = True
    thread.start()
    IMU_threads.append(thread)

'''
timer = QtCore.QTimer()
timer.timeout.connect(update)
timer.start(timer_frequency)
'''

mw.show()

if __name__ == '__main__':
    import sys
    if(sys.flags.interactive != 1) or not hasattr(QtCore, 'PYQT_VERSION'):
        QtGui.QApplication.instance().exec_()


from PyQt4 import QtCore, QtGui 
import pyqtgraph as pg
import random
import zmq
import numpy as np
import sys

def positionUpdate():
    global currentPositionValue
    topic, currentPositionValue= socket2.recv().split()
    currentPosition.setText(currentPositionValue)
def moveButtonPressed():
    socket.send("move 1 2 3")
    result = socket.recv()
    print("Move response is " + result)

def homeButtonPressed():
    socket.send("home")
    result = socket.recv()
    print("Home response is " + result)

context = zmq.Context()
socket = context.socket(zmq.REQ)
socket.connect("tcp://192.168.30.30:6010")
socket.send("info?")
info = socket.recv()

context2 = zmq.Context()
socket2 = context2.socket(zmq.SUB)
socket2.connect("tcp://192.168.30.30:6011")
socket2.setsockopt(zmq.SUBSCRIBE, "10000")
topic, currentPositionValue = socket2.recv().split()

info = [x.strip() for x in info.split(',')]
print(info)
velocityMin, velocityMax, accelerationMin, accelerationMax, positionMin, positionMax, homeFlag, units = info

app = QtGui.QApplication([])
mw = QtGui.QMainWindow()
mw.setWindowTitle('ZMQ Motor GUI')
cw = QtGui.QWidget()
l = QtGui.QFormLayout()
mw.setCentralWidget(cw)
cw.setLayout(l)

position = QtGui.QLineEdit()
position.setValidator(QtGui.QIntValidator(int(positionMin), int(positionMax)))
position.setAlignment(QtCore.Qt.AlignLeft)

velocity = QtGui.QLineEdit()
velocity.setValidator(QtGui.QIntValidator(int(velocityMin), int(velocityMax)))
velocity.setAlignment(QtCore.Qt.AlignLeft)

acceleration = QtGui.QLineEdit()
acceleration.setValidator(QtGui.QIntValidator(int(accelerationMin), int(accelerationMax)))
acceleration.setAlignment(QtCore.Qt.AlignLeft)

currentPosition = QtGui.QLineEdit()
currentPosition.setReadOnly(True)
currentPosition.setText(currentPositionValue)

moveButton = QtGui.QPushButton('Move')
moveButton.clicked.connect(moveButtonPressed)
homeButton = QtGui.QPushButton('Home')
homeButton.clicked.connect(homeButtonPressed)
if homeFlag == 'false':
    homeButton.setEnabled(False)

l.addRow("Position (deg)", position)
l.addRow("Velocity (m/s)", velocity)
l.addRow("Acceleration (m/s^2)", acceleration)
l.addRow("Current Position", currentPosition)
l.addRow(moveButton)
l.addRow(homeButton)

timer = QtCore.QTimer()
timer.timeout.connect(positionUpdate)
timer.start(1000)

mw.show()

if __name__ == '__main__':
    if(sys.flags.interactive != 1) or not hasattr(QtCore, 'PYQT_VERSION'):
        QtGui.QApplication.instance().exec_()

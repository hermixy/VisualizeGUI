import pyqtgraph as pg
from pyqtgraph.Qt import QtCore, QtGui
import numpy as np
import random
import sys

"""Multiple Axis Plot Widget Example"""

class MultipleAxisPlotWidget(QtGui.QWidget):
    def __init__(self, parent=None):
        super(MultipleAxisPlotWidget, self).__init__(parent)

        self.NUMBER_OF_PLOTS = 4
        self.LEFT_X = 0 
        self.RIGHT_X = 5
        self.SPACING = 1
        self.x_axis = np.arange(self.LEFT_X, self.RIGHT_X + 1, self.SPACING)
        self.buffer_size = int((abs(self.LEFT_X) + abs(self.RIGHT_X) + 1)/self.SPACING)

        self.multiple_axis_plot_widget = pg.PlotWidget()
        self.multiple_axis_plot_widget.setLabel('left', 'left axis')
        self.multiple_axis_plot_widget.setLabel('right', 'right axis')
        
        # Create left plots
        self.left_plot1 = self.multiple_axis_plot_widget.plot()
        self.left_plot2 = self.multiple_axis_plot_widget.plot()

        self.left_plot1.setPen((173,255,129), width=1)
        self.left_plot2.setPen((172,187,255), width=1)
        
        # Create right plots
        self.right_plot1 = pg.PlotDataItem()
        self.right_plot2 = pg.PlotDataItem()

        self.right_plot1.setPen((255,174,255), width=1)
        self.right_plot2.setPen((102,255,206), width=1)

        self.create_right_axis()
        self.right_axis.addItem(self.right_plot1)
        self.right_axis.addItem(self.right_plot2)

        self.initialize_data_buffers()
        self.initialize_plot_buffers()

        self.layout = QtGui.QGridLayout()
        self.layout.addWidget(self.multiple_axis_plot_widget)

        self.start()

    def create_right_axis(self):
        """Initialize right axis viewbox and link to left coordinate system"""

        # Create a new ViewBox for the right axis and link to left coordinate system
        self.right_axis = pg.ViewBox()
        # Add all plots on right axis
        self.multiple_axis_plot_widget.plotItem.scene().addItem(self.right_axis)
        self.multiple_axis_plot_widget.plotItem.getAxis('right').linkToView(self.right_axis)
        # Connect right axis plots to same x axis
        self.right_axis.setXLink(self.multiple_axis_plot_widget.plotItem)

        self.update_views()
        self.multiple_axis_plot_widget.plotItem.vb.sigResized.connect(self.update_views)

    def update_views(self):
        """View has resized so update auxiliary views to match"""

        # Re-update linked axes
        self.right_axis.setGeometry(self.multiple_axis_plot_widget.plotItem.vb.sceneBoundingRect())
        self.right_axis.linkedViewChanged(self.multiple_axis_plot_widget.plotItem.vb, self.right_axis.XAxis)

    def initialize_data_buffers(self):
        """Create blank data buffers for each curve"""

        self.data_buffers = []
        for trace in range(self.NUMBER_OF_PLOTS):
            self.data_buffers.append([])

    def initialize_plot_buffers(self):
        """Add plots into buffer for each curve"""
        self.universal_plots = []
        self.universal_plots.append(self.left_plot1)
        self.universal_plots.append(self.left_plot2)
        self.universal_plots.append(self.right_plot1)
        self.universal_plots.append(self.right_plot2)

    def update_plot(self):
        """Generates new random value and plots curve onto plot"""

        for trace in range(self.NUMBER_OF_PLOTS):
            if len(self.data_buffers[trace]) >= self.buffer_size:
                self.data_buffers[trace].pop(0)
            if trace == 2 or trace == 3:
                data_point = random.randint(10000,30000)
            else:
                data_point = random.randint(10,300)
            self.data_buffers[trace].append(float(data_point))
            
            self.universal_plots[trace].setData(self.x_axis[len(self.x_axis) - len(self.data_buffers[trace]):], self.data_buffers[trace])

    def get_multiple_axis_plot_layout(self):
        return self.layout

    def start(self):
        self.multiple_axis_plot_timer = QtCore.QTimer()
        self.multiple_axis_plot_timer.timeout.connect(self.update_plot)
        self.multiple_axis_plot_timer.start(500)

if __name__ == '__main__':

    # Create main application window
    app = QtGui.QApplication([])
    app.setStyle(QtGui.QStyleFactory.create("Cleanlooks"))
    mw = QtGui.QMainWindow()
    mw.setWindowTitle('Multiple Axis Plot Example')

    # Create plot
    multiple_axis_plot = MultipleAxisPlotWidget()

    # Create and set widget layout
    # Main widget container
    cw = QtGui.QWidget()
    ml = QtGui.QGridLayout()
    cw.setLayout(ml)
    mw.setCentralWidget(cw)

    # Add plot to main layout
    ml.addLayout(multiple_axis_plot.get_multiple_axis_plot_layout(),0,0)

    mw.show()

    if(sys.flags.interactive != 1) or not hasattr(QtCore, 'PYQT_VERSION'):
        QtGui.QApplication.instance().exec_()

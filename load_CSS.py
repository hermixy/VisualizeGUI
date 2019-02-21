from PyQt4 import QtGui, QtCore
import os

def load_CSS(mode):
    """Loads CSS style sheet depending on mode

    0 - default 
    1 - dark theme
    """

    if mode == 0:
        style_sheet = os.path.join(os.path.split(__file__)[0], 'css/default.css')
    if mode == 1:
        style_sheet = os.path.join(os.path.split(__file__)[0], 'css/style.css')
    style_sheet_str = QtCore.QString(open(style_sheet, 'r').read())
    return style_sheet_str

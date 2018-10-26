#!c:\python27\python.exe
# EASY-INSTALL-ENTRY-SCRIPT: 'PyInstaller==3.4','console_scripts','pyinstaller'

# Usage: python create_executable.py
# Usage: python create_executable.py -f <file.py>
# Manual: python pyinstaller-script.py --onefile --windowed <file.py>

from os import system
import argparse
__requires__ = 'PyInstaller==3.4'
import re
import sys
from pkg_resources import load_entry_point

ap = argparse.ArgumentParser()
ap.add_argument("-f", "--file", required=False, help="File name to convert into executable")
args = vars(ap.parse_args())
if not args['file']:
    filename = 'spectrumGUI.py'
else:
    filename = args['file']

system('python pyinstaller-script.py --onefile --windowed ' + filename)



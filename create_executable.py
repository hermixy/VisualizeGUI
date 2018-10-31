#!c:\python27\python.exe
# EASY-INSTALL-ENTRY-SCRIPT: 'PyInstaller==3.4','console_scripts','pyinstaller'
# Generates python script into .exe file
# Built .exe file can be found in the dist/ folder
#
# Note: Use use clean.py before usage to ensure prior executables are removed
# Usage: python create_executable.py -f <file.py>
# Manual: python pyinstaller-script.py --onefile --windowed <file.py>

from os import system
import argparse
__requires__ = 'PyInstaller==3.4'
import re
import sys
from pkg_resources import load_entry_point

ap = argparse.ArgumentParser()
ap.add_argument("-f", "--file", required=True, help="File name to convert into executable")
args = vars(ap.parse_args())
system('python pyinstaller-script.py --onefile --windowed ' + args['file'])


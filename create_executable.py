# Manual: python pyinstaller-script.py --onefile --windowed <file.py>

from os import system
import argparse

ap = argparse.ArgumentParser()
ap.add_argument("-f", "--file", required=False, help="File name to convert into executable")
args = vars(ap.parse_args())
if not args['file']:
    filename = 'SpectrumGUI'
else:
    filename = args['file']
system('python executable/pyinstaller-script.py --onefile --windowed ' + filename)


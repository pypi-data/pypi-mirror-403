#!/usr/bin/env python

import sys
if sys.version_info.major > 2: 
    from PyQt5 import QtGui, QtCore
else: 
    from PyQt4 import QtGui, QtCore

#from tngGui.pyqtSelector import *

import sys, os
import HasyUtils
import tngGui.lib.chatClass
import argparse

def parseCLI():
    parser = argparse.ArgumentParser( 
        formatter_class = argparse.RawDescriptionHelpFormatter,
        description="SardanaChat", 
        epilog='''\
Example:
  SardanaChat.py 
    ''')
    #
    # notice that 'pattern' is a positional argument
    #
    #parser.add_argument( 'namePattern', nargs='*', help='pattern to match the motor names, not applied to other devices')
    #parser.add_argument( '--mca', dest='mca', action="store_true", help='start the MCA widget')
    #parser.add_argument( '-t', dest='tags', nargs='+', help='tags matching online.xml tags')
    #parser.add_argument( '-s', dest="spectra", action="store_true", help='use Spectra for graphics')
    #parser.add_argument( '--fs', dest="fontSize", action="store", default=None, help='font size')
    args = parser.parse_args()

    return args

def main():

    args = parseCLI()

    if os.getenv( "DISPLAY") != ':0':
        QtGui.QApplication.setStyle( 'Cleanlooks')

    app = QtGui.QApplication(sys.argv)


    mainW = tngGui.lib.chatClass.Chat( args, None, app)

    mainW.show()

    try:
        sys.exit( app.exec_())
    except Exception as e:
        print( repr( e))


if __name__ == "__main__":
    main()
    

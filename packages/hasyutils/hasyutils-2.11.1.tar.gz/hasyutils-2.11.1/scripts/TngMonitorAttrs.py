#!/usr/bin/env python

import sys, os, argparse
import HasyUtils
from HasyUtils.pyqtSelector import *
import pyqtgraph as pg
NP = 2000

ATTRIBUTES = [
    #'sys/tg_test/1/double_scalar',
    'petra/globals/keyword/BeamCurrent',
    ]

app = None

def parseCLI():
    parser = argparse.ArgumentParser( 
        formatter_class = argparse.RawDescriptionHelpFormatter,
        description="TngMonitorAttrs", 
        epilog='''\
Examples:
  TngMonitorAttrs.py petra/globals/keyword/beamcurrent
    monitor a single attribute

  TngMonitorAttrs.py "petra/globals/keyword/beamcurrent OptionalAlias"
    monitor a single attribute choosing an alias

  TngMonitorAttrs.py -f attr.lis
    monitor the attributes mentioned in attr.lis
    cat attr.lis
      #
      haspp99:10000/petra/globals/keyword/BeamCurrent OptionalAlias1
      haspp99:10000/sys/tg_test/1/double_scalar OptionalAlias2
      haspp99:10000/sys/tg_test/1/long_scalar OptionalAlias3
      haspp99:10000/sys/tg_test/1/short_scalar OptionaAlias4

    If an OptionalAlias is supplied, it is used as the title of the plot. 
    ''')
    parser.add_argument('attributes', nargs='*', help='a list of attributes, default petra/globals/keyword/BeamCurrent')
    parser.add_argument('-f', dest='fileName', default = None, help='file containing attributes')
    parser.add_argument('-n', dest='np', default = NP, help='the no. of points per plot, def. %d' % NP)
    parser.add_argument('-t', dest='updateTime', type=float, default=1., help='the update time [s], def. 1s')

    args = parser.parse_args()

    return args


def main():
    global NP, ATTRIBUTES, app

    args = parseCLI()
    sys.argv = []

    if os.getenv( "DISPLAY") != ':0':
        QApplication.setStyle( 'Cleanlooks')

    if len( args.attributes):
        if args.fileName:
            print( "specify either a file containing attributes OR attribute on the command line")
            sys.exit( 255)
        ATTRIBUTES = args.attributes

    if args.fileName:
        ATTRIBUTES = HasyUtils.getListFromFile( args.fileName)

    NP = int(args.np)

    app = QApplication.instance()
    if app is None: 
        app = QApplication(sys.argv)

    o = HasyUtils.tngMonitorAttrs.monitorMenu( app = app, attrs = ATTRIBUTES, updateTime = args.updateTime, np = NP)
    o.show()

    try:
        sys.exit( app.exec_())
    except Exception as e:
        print( repr( e))

if __name__ == "__main__":
    main()
    

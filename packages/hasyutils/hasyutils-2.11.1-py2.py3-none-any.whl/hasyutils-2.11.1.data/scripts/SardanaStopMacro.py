#!python 

import argparse
import PyTango
import sys
import HasyUtils

def main():

    parser = argparse.ArgumentParser( 
        formatter_class = argparse.RawDescriptionHelpFormatter,
        description="Stop a RUNNING Macro", 
        epilog='''\
Examples:
  SardanaStopMacro.py
    display state of all Doors Door

  SardanaStopMacro.py -d p14/door/haspp14eh1.02
    display the state of the specified Door

  SardanaStopMacro.py -x
    stop the Macro running in the first Door

  SardanaStopMacro.py -x -d p14/door/haspp14eh1.02
    stop Macro running in the specified Door
    ''')
    parser.add_argument('-d', dest="doorName", help='the door name, optional, default: first Door.')
    parser.add_argument('-x', dest="execute", action="store_true", help='actually stop the currently running Macro')

    args = parser.parse_args()

    if not args.doorName and not args.execute:
        for doorName in HasyUtils.getDoorNames():
            proxy = PyTango.DeviceProxy( doorName)
            print( "Door %s state %s" % (doorName, str(proxy.state())))
        sys.exit(0)

    doorName = HasyUtils.getDoorNames()[0]

    if args.doorName:
        doorName = args.doorName

            
    proxy = PyTango.DeviceProxy( doorName)
    print( "Door %s state %s" % (doorName, str(proxy.state())))

    if args.execute:
        if proxy.state() == PyTango.DevState.RUNNING:
            print( "Stopping Macro on %s" % (doorName))
            proxy.StopMacro()
        else:
            print( "Door %s in state %s, nothing to be done" % (doorName, str( proxy.state())))

if __name__ == '__main__':
    main()



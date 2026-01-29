#!python
#
# this script executes an installation verification procedure
# it is not distributed with the HasyUtils
#
import HasyUtils
import PyTango
import argparse
import time, os, sys

def doAdjust():
    #
    # if no Pool is running, return 
    #
    if len(HasyUtils.getLocalPoolNames()) == 0:
        print( "SardanaAdjustLimits: no local Pools, return")
        return

    flagTTY = os.isatty(1)
    doors = HasyUtils.getDoorNames()
    if len( doors) != 3:
        print( "SardanaAdjustLimits: error, of Doors != 3, %d" % len(doors))
        return
    door = PyTango.DeviceProxy( doors[0])
    door.runMacro( ["adjust_lim"]) 

    if flagTTY:
        sys.stdout.write( "Waiting for MacroServer to complete 'adjust_lim' ")
        sys.stdout.flush()

    count = 0
    while door.state() != PyTango.DevState.ON:
        time.sleep(0.5)
        if flagTTY:
            sys.stdout.write( '.')
            sys.stdout.flush()
        if count > 20:
            print( "SardanaAdjustLimits: error, 'adjust_lim' take more that 10s")
            return
        count += 1
            
    print( "")

    if flagTTY:
        for elm in door.Output:
            print( elm)
        
def main():
    parser = argparse.ArgumentParser( 
        formatter_class = argparse.RawDescriptionHelpFormatter,
        description="Adjusting motor unit limits") 

    parser.add_argument('-x', dest="adjust", action="store_true", help='copy limits from TS to Pool')
    args = parser.parse_args()

    if args.adjust:
        doAdjust()
        return

    parser.print_help()
    
if __name__ == "__main__":
    main()

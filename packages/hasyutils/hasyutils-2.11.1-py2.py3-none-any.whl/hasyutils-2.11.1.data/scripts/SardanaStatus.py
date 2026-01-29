#!python
#
# this script uses the local Door(s) to find the related
# MacroServer and Pools and display some Information. The Pools
# may run on a different SardanaHost
#
import sys
import HasyUtils.pooltools
import HasyUtils
import PyTango
from optparse import OptionParser

def main():

    ret = HasyUtils.checkECStatus( verbose = True)
    print( "SardansStatus: checkECStatus returns %s" % repr( ret))
    return 

    usage = "usage: %prog \n" 
    parser = OptionParser(usage=usage)
    parser.add_option( "-f", action="store_true", dest="fullListing", default = False, help="full listing")
    (options, args) = parser.parse_args()

    doorNames = HasyUtils.getLocalDoorNames()
    print( "\n Local Doors")
    for door in doorNames:
        try: 
            p = PyTango.DeviceProxy( door)
            print( "   %s, state %s" % ( door, p.state()))
        except Exception as e: 
            print( "SardanaStatus: trouble connecting to %s" % door)
            print( repr( e))
    print( "") 

    localPoolNames = HasyUtils.getLocalPoolNames()

    dmsp = HasyUtils.DMSP( doorNames[0])
    if not options.fullListing:
        print( " MacroServer     %-30.30s state %s " % (dmsp.macroserver.name(), dmsp.macroserver.state()))
        #print( " Related Pools:")
    print( "") 
    for pool in dmsp.pools:
        where = "remote"
        if pool.name() in localPoolNames:
            where = "local"
        print( " Pool (%6.6s) %-30.30s state %s " % (where, pool.name(), pool.state()))
        HasyUtils.pooltools.listPool( pool, displayController = options.fullListing)

    print( "calling checkECStatus")
    ret = HasyUtils.checkECStatus( verbose = True)
    print( "checkECStatus returns %s" % repr( ret))
    if options.fullListing:
        print( " MacroServer %-30.30s state %s " % (dmsp.macroserver.name(), dmsp.macroserver.state()))
        print( " Door        %-30.30s state %s " % (dmsp.door.name(), dmsp.door.state()))
        print( " Pools %s" % repr(dmsp.poolNames))

    if not options.fullListing:
        print( "\n  Use 'SardanaStatus.py -f' to obtain more information about the pools.")

    return 

if __name__ == "__main__":
    main()

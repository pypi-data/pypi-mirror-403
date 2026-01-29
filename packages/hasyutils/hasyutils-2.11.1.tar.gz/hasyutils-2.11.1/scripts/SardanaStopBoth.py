#!/usr/bin/python
""" stops ms and pools """
import sys
import HasyUtils.pooltools
import HasyUtils

def main():
    """ stops ms and pools """

    poolList = HasyUtils.getServerNameByClass( "Pool")
    msList = HasyUtils.getServerNameByClass( "MacroServer")

    for srv in msList:
        if not HasyUtils.pooltools.stopServer( srv):
            print( "SardanaStopBoth: failed to stop %s" % srv)
            #sys.exit(255)
            
    for srv in poolList:
        if not HasyUtils.pooltools.stopServer( srv):
            print( "SardanaStopBoth: failed to stop %s" % srv)
            #sys.exit(255)
            
    return

if __name__ == "__main__":
    main()



#!python
""" restarts the macroserver """
import sys
import HasyUtils.pooltools
import HasyUtils
from optparse import OptionParser

def main():
    """ restarts the pools """

    usage = "usage: %prog -x "
    parser = OptionParser(usage=usage)
    parser.add_option( "-x", action="store_true", dest="execute", default = False, 
                       help="restarts the local Pool")
    
    (options, args) = parser.parse_args()
    
    if options.execute is False:
        parser.print_help()
        sys.exit(255)

    srvList = HasyUtils.getLocalPoolServers()

    if len( srvList) == 0:
        print( "SardanaRestartPool.py: there are no local pools")
        sys.exit(255)

    for srv in srvList:
        if not HasyUtils.pooltools.restartServer( srv):
            print( "failed to restart %s" % srv)
            sys.exit(255)

    HasyUtils.pooltools.refreshDiffractometers()
            
    return

if __name__ == "__main__":
    main()



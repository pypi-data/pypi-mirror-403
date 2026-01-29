#!python
import sys
import HasyUtils.pooltools
import HasyUtils
from optparse import OptionParser

def main():
    """ stops the local macroserver """

    usage = "usage: %prog -x "
    parser = OptionParser(usage=usage)
    parser.add_option( "-x", action="store_true", dest="execute", default = False, 
                       help="stops the local MacroServers")
    
    (options, args) = parser.parse_args()
    
    if options.execute is False:
        parser.print_help()
        sys.exit(255)

    srvList = HasyUtils.getLocalMacroServerServers()
    if len( srvList) == 0:
        print( "SardanaStopMacroServer.py: there are no local macroServer")
        sys.exit(255)

    for srv in srvList:
        if not HasyUtils.pooltools.stopServer( srv):
            print( "failed to stop %s" % srv)
            sys.exit(255)
            
    return

if __name__ == "__main__":
    main()



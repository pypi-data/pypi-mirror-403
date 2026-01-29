#!/usr/bin/env python
import sys, os
import HasyUtils.pooltools
import HasyUtils
from optparse import OptionParser

def main():
    """ restarts the local macroserver """

    usage = "usage: %prog -x "
    parser = OptionParser(usage=usage)
    parser.add_option( "-x", action="store_true", dest="execute", default = False, 
                       help="restarts the local MacroServers")
    #parser.add_option( "-c", action="store_true", dest="nocoredump", 
    #                   default = False, help="produce no core dumps")
    
    (options, args) = parser.parse_args()
    
    if options.execute is False:
        parser.print_help()
        sys.exit(255)

#    if not options.nocoredump: 
#        if os.system( "/usr/bin/SardanaDiag.py"):
#            sys.exit( 255)
        
    srvList = HasyUtils.getLocalMacroServerServers()

    if len( srvList) == 0:
        print( "SardanaRestartMacroServer.py: there are no local macroServer")
        sys.exit(255)

    for srv in srvList:
        if not HasyUtils.pooltools.restartServer( srv):
            print( "SardanaRestartMacroserver, failed to restart %s" % srv)
            sys.exit(255)

    scriptName = HasyUtils.getEnv( "MacroServerRestartPostScript") 
    if scriptName is not None and len( scriptName) > 0: 
        if not os.path.exists( scriptName): 
            print( "SardanaRestartMacroserver, %s does not exist" % scriptName) 
            sys.exit( 255)
        os.system( "python3 %s" % scriptName)

            
    return

if __name__ == "__main__":
    main()



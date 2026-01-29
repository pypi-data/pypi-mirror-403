#!python
""" restarts the pool and the macroserver """
import sys, os
import HasyUtils.pooltools
import HasyUtils
from optparse import OptionParser

def main():
    """ restarts the pools """

    usage = "usage: %prog -x "
    parser = OptionParser(usage=usage)
    parser.add_option( "-x", action="store_true", dest="execute", default = False, 
                       help="restarts local Pools and MacroServers")
    parser.add_option( "-c", action="store_true", dest="nocoredump", 
                       default = False, help="produce no core dumps")
    
    (options, args) = parser.parse_args()
    
    if options.execute is False:
        parser.print_help()
        sys.exit(255)


    #    if not options.nocoredump: 
    #        if os.system( "/usr/bin/SardanaDiag.py"):
    #            sys.exit( 255)

    ret = HasyUtils.restartBoth()

    return ret

if __name__ == "__main__":
    main()



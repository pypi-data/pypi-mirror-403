#!/usr/bin/env python
#
import sys
from PyTango import *
from optparse import OptionParser
import HasyUtils
import HasyUtils.pooltools


def main():
    global options

    usage = "%prog -x\n" 

    parser = OptionParser(usage=usage)
    parser.add_option( "-x", action="store_true", dest="execute", default = False, help="copy limits from TS to Pools")

    (options, args) = parser.parse_args()


    if len( sys.argv) == 0 or not options.execute:
        parser.print_help()
        sys.exit(255)

    lst = HasyUtils.getPoolNames()
    for pool in lst:
        HasyUtils.pooltools.limitsFromTS2Pool( pool)

     
if __name__ == "__main__":
    main()

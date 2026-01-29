#!/usr/bin/env python
#
import PyTango
import HasyUtils
import sys, time, os
from optparse import OptionParser
flagTTY = False

if __name__ == "__main__":
    usage = "%prog -x [-t <task>] \n" + \
        "  This script is the generic frontend to HasyUtils. It executes certain tasks.\n" + \
        "  HasyUtilsMain.py -t checkMacroServerEnvironment \n" \
        "  HasyUtilsMain.py -t chckmsenv \n" \
        "  HasyUtilsMain.py -t lsMacroServerEnvironment \n" \
        "  HasyUtilsMain.py -t lsenv \n" \
    
    parser = OptionParser(usage=usage)
#    parser.add_option( "-x", action="store_true", dest="execute", 
#                       default = False, help="execute")
    parser.add_option( "-t", type="string", dest="task", 
                       default = None, help="the task to be executed")
    
    (options, args) = parser.parse_args()
#
#    if options.execute is False:
#        parser.print_help()
#        sys.exit(255)

    flagTTY = False
    if os.isatty(1):
        flagTTY = True

    if not options.task:
        parser.print_help()
        sys.exit(255)

    if options.task.lower() == "checkmacroserverenvironment" or\
            options.task.lower() == "chckmsenv":
        HasyUtils.checkMacroServerEnvironment()

    if options.task.lower() == "lsmacroserverenvironment" or\
            options.task.lower() == "lsenv":
        HasyUtils.lsMacroServerEnvironment()


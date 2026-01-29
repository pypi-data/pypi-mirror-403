#!python
#
import sys
import HasyUtils.pooltools
import HasyUtils
from optparse import OptionParser

usage = "usage: %prog [-i <instance>] \n" + \
        " e.g.: %prog -i PETRA-3 "
#parser = OptionParser(usage=usage)
#parser.add_option( "-i", action="store", type="string", dest="instance", help="the Pool instance")

#(options, args) = parser.parse_args()

#if options.instance is None:
#    options.instance = "PETRA-3"

HasyUtils.pooltools.clearSCAs()



    

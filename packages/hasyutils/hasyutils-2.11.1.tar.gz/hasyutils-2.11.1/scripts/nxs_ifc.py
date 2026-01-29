#!/usr/bin/env python
#
# -p prints the selected 
#    used by Scan.pm
#
from optparse import OptionParser
import sys
import HasyUtils.nxIO
import json
import pprint

def printProfile( selectorName):
    nxio = HasyUtils.nxIO.nxIO( selectorName)
    counters = nxio.getCounters()
    timers = nxio.getTimers()
    mcas = nxio.getMCAs()
    dct = {}
    dct['counter'] = counters
    dct['timer'] = timers
    for hsh in mcas:
        for k in hsh.keys():
            dct[ k] = { 'channel' : hsh[k]}
    dct['flags'] = ["write_to_disk", "1", "bell_on_scan_end", "1"]
    line = json.dumps( dct)
    print( line)

usage = "\n\n Print the NeXus-selected devices as a json string. \n%prog -p <-s selectorDevice> "
parser = OptionParser(usage=usage)
parser.add_option( "-p", action="store_true", dest="profile", default = False, 
                   help="print profile as json string")
parser.add_option( "-s", action="store", type="string", dest="selector", 
                   help="NXSRecSelector device, optional, e.g. p09/nxsrecselector/hastodt" )

(options, args) = parser.parse_args()


if options.selector is None:
    selector = HasyUtils.getLocalNXSelectorNames()
    if len( selector) != 1:
        print( "nxsclient: no. of selector devices != 1 %s" % len( selector)))
        print( "nxsclient: %s" % repr9selector))
        sys.exit(255)
    options.selector = selector[0]

if options.profile is True:
    printProfile( options.selector)
    sys.exit(255)

parser.print_help()
sys.exit(255)

#!/usr/bin/env python
from optparse import OptionParser
import HasyUtils.nxIO
import os, sys
import pprint

def simpleScan():
    selector = HasyUtils.getLocalNXSelectorNames()
    if len( selector) != 1:
        print( "nxsclient: no. of selector devices != 1 %d" % len( selector))
        sys.exit(255)

    nxio = HasyUtils.nxIO.nxIO( selector[0])
    nxio.openFile(HasyUtils.createScanName( os.getenv( "PWD") + "/hasylab") + ".nxs")
    
    nxio.openEntry()
    
    for el in nxio.getClientSources():
        print( "client sources %s", pprint.pformat(el, indent=1))

    ## experimental loop
    for li in range(3):
        nxio.execStep()

    nxio.closeEntry()
    nxio.closeFile()


usage = "\n\n Test scritp for the NeXus Selector. \n%prog -t "
parser = OptionParser(usage=usage)
parser.add_option( "-t", action="store_true", dest="execTest", default = False, 
                   help="execute a test")
#parser.add_option( "-s", action="store", type="string", dest="selector", 
#                   help="NXSRecSelector device, optional, e.g. p09/nxsrecselector/hastodt" )

(options, args) = parser.parse_args()


#if options.selector is None:
#    selector = HasyUtils.getDeviceNamesByClass( "NXSRecSelector")
#    if len( selector) != 1:
#        print( "nxsclient: no. of selector devices != 1 %s" % len( selector))
#        sys.exit(255)
#    options.selector = selector[0]

if options.execTest is True:
    simpleScan()
    sys.exit(255)

parser.print_help()
sys.exit(255)

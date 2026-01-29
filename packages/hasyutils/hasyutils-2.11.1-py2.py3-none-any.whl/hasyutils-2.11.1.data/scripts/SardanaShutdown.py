#!python

import sys, os, time

import HasyUtils.pooltools
import HasyUtils
import PyTango
from optparse import OptionParser
import socket

hostname = socket.gethostname()
usage = "usage: %prog -x "
parser = OptionParser(usage=usage)
parser.add_option( "-x", action="store_true", dest="execute", default = False, help="execute shutdown")

(options, args) = parser.parse_args()

if options.execute is False:
    parser.print_help()
    sys.exit(255)

print( "SardanaShutdown")

#
# clean the local pool
# 28.2.2024, not necessay? 
#if not HasyUtils.pooltools.deleteLocalPoolDevices():
#    print( "shutdown: Failed to delete the Pool devices")
#
# kill the local macroserver
#
try:
    macroServers = HasyUtils.getLocalMacroServerNames()
    for macroServer in macroServers:
        try:
            proxy = PyTango.DeviceProxy( macroServer)
            MsName = proxy.info().server_id
        except:
            continue
        print( "shutdown: killing %s" % MsName)
        HasyUtils.stopServer( MsName)
except:
    pass
# 
# kill the pool servers
#
# note: getLocalPoolNames() returns only the local pools
# that have been exported at least once. 
#
try:
    poolServers = HasyUtils.getPoolNames()
    for poolServer in poolServers:
        try:
            proxy = PyTango.DeviceProxy( poolServer)
            PlName = proxy.info().server_id
        except Exception as e:
            print( "shutdown: failed to create a proxy to %s" % poolServer)
            print( "shutdown: not trying to stop the pool, consider to kill")
            print( "the pool by hand:")
            print( "  - find Pool PID:  ps -aux | grep -i Pool ")
            print( "  - then kill pool process: kill -9 <PID> ")
            print( repr( e))
            continue
        print( "shutdown: stopping %s" % PlName)
        HasyUtils.stopServer( PlName)
except:
    pass

print( "shutdown: deleting Pools")
if not HasyUtils.pooltools.deleteLocalPools():
    sys.exit(255)

time.sleep(1.0) 
print( "shutdown: deleting MacroServer")
if not HasyUtils.pooltools.deleteMacroServers():
    sys.exit(255)

print( "shutdown: DONE")

sys.exit(0)

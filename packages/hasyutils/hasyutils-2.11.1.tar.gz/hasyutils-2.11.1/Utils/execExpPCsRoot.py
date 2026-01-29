#!/usr/bin/env python3

import HasyUtils
from optparse import OptionParser
import os

TANGO_HOSTS = "/afs/desy.de/group/hasylab/Tango/HostLists/TangoHosts.lis"
DB_HOSTS = "/afs/desy.de/group/hasylab/Tango/HostLists/dbHosts.lis"

commandDct = \
{ 
    '1': "ls /usr/local/bin/vrsn", 
    '2': "test -d /online_dir/MotorLogs && ls -ald /online_dir/MotorLogs", 
    '3': "test -d /online_dir/MotorLogs && chmod -R 777 /online_dir/MotorLogs && ls -ald /online_dir/MotorLogs", 
    '4': "pgrep -f SardanaMonitor.py", 
}

def main():

    temp = ""
    for k in commandDct.keys():
        temp += "  %s: %s\n" % (k, commandDct[ k])

    usage = "%prog -s TANGO_HOST|DB_HOSTS -c cmdNo -x\n" + \
            "  -s TANGO_HOSTS, DB_HOSTS\n" + \
            "  -c select a command\n" + \
            "  -x execute\n" + \
            "\n\n" + temp + \
            "\n\n  Example: ./execExpPCsRoot.py -x -s TANGO_HOSTS -c 6"
    
    parser = OptionParser(usage=usage)
    parser.add_option( "-x", action="store_true", dest="execute", 
                       default = False, help="execute")
    parser.add_option("-s", action="store", type="string", dest="hostList", help="TANGO_HOSTS, DB_HOSTS")
    parser.add_option("-c", action="store", type="string", dest="cmdNo", help="command number")
    
    (options, args) = parser.parse_args()

    if options.cmdNo is None:
        print( "specify a selector for the command")
        parser.print_help()
        return

    if options.hostList == 'TANGO_HOSTS': 
        nodes = HasyUtils.readHostList( TANGO_HOSTS)
    elif options.hostList == 'DB_HOSTS': 
        nodes = HasyUtils.readHostList( DB_HOSTS)
    else:
        print( "failed to identify host list")
        return 

    if options.cmdNo not in commandDct:
        print( "wrong command number")
        return
    
    sz = len( nodes) 
    count = 1
    countFailed = 0
    for host in nodes:
        if not HasyUtils.checkHostRootLogin( host):
            print( "-- checkHostRootLogin returned error %s" % host)
            countFailed += 1
            continue
        cmd = commandDct[ options.cmdNo]
        if options.execute:
            print( "%s" % (host))
            prc = os.popen( "timeout 5 ssh -n root@%s \"%s\"" % (host, cmd))
            res = prc.readlines()
            prc.close()
            print( res)
        else: 
            print( "dry-run: %s executing \"%s\"" % (host, cmd))
        count += 1

    return

if __name__ == "__main__":
    main()



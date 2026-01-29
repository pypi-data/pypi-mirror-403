#!/usr/bin/env python

import HasyUtils
from optparse import OptionParser
import os

TANGO_HOSTS = "/afs/desy.de/group/hasylab/Tango/HostLists/TangoHosts.lis"

def main():

    usage = "%prog -x\n" + \
            "  -x execute\n" + \
            "\n\n  Example: ./findSpockNodes.py -x"
    
    parser = OptionParser(usage=usage)
    parser.add_option( "-x", action="store_true", dest="execute", 
                       default = False, help="execute")
    #parser.add_option("-s", action="store", type="string", dest="hostList", help="TANGO_HOSTS, DB_HOSTS, SPYD_HOSTS")
    #parser.add_option("-c", action="store", type="string", dest="cmdNo", help="command number")
    
    (options, args) = parser.parse_args()

    if options.execute:
        parser.print_help()
        return

    nodes = HasyUtils.readHostList( TANGO_HOSTS)
    sz = len( nodes) 
    count = 1
    countFailed = 0
    for host in nodes:
        if not HasyUtils.checkHostRootLogin( host):
            print( "-- checkHostRootLogin returned error %s" % host)
            countFailed += 1
            continue
        #
        # see, if there is an ipython_log.py file newer than 7 days
        #
        cmd = "find /online_dir/ipython_log.py  -ctime -7 > /dev/null 2>&1 && echo exists"
        #print( "%s executing \"%s\"" % (host, cmd))
        prc = os.popen( "timeout 5 ssh -n root@%s \"%s\"" % (host, cmd))
        res = prc.readlines()
        prc.close()
        if len( res) == 1 and res[0] == "exists\n":
            print( "Spock host: %s" % host)
        else: 
            print( "Not Spock host: %s" % host)
        count += 1

    return

if __name__ == "__main__":
    main()



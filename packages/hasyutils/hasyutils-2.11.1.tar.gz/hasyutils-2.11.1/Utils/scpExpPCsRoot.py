#!/usr/bin/env python3
#
import HasyUtils
import os
import argparse


TANGO_HOSTS = "/afs/desy.de/group/hasylab/Tango/HostLists/TangoHosts.lis"

SPYD_HOSTS = "/afs/desy.de/group/hasylab/Tango/HostLists/spydHosts.lis"
HOST_LIST = TANGO_HOSTS

def main():
    global HOST_LIST
    parser = argparse.ArgumentParser( 
        formatter_class = argparse.RawDescriptionHelpFormatter,
        description="  distributes: vrsn, tsport-kill, GpMonitor.pl, 99-online.sh")
    
    parser.add_argument('-x', dest="execute", action="store_true", default = False, 
                        help='really execute')
    parser.add_argument( 'fileName', nargs="?", default = "None", help='fileName')
     
    args = parser.parse_args()

    if not args.execute:
        parser.print_help()
        return 

    if args.fileName == 'vrsn':
        src = '/home/kracht/tools/vrsn'
        dest = '/usr/local/bin'
    elif args.fileName == 'tsport-kill':
        src = '/home/kracht/tools/tsport-kill'
        dest = '/usr/local/bin'
    elif args.fileName == 'GpMonitor.pl':
        src = '/afs/desy.de/group/hasylab/varian/GpMonitor.pl'
        dest = '/usr/local/bin'
    elif args.fileName == '99-online.sh':
        src = '/etc/profile.d/99-online.sh'
        dest = '/etc/profile.d'
    else:
        print( "Failed to identify the fileName %s" % args.fileName)
        return
    
    nodes = HasyUtils.readHostList( HOST_LIST)

    sz = len( nodes) 
    count = 1
    countFailed = 0
    countOffline = 0
    for host in nodes:
        if not HasyUtils.checkHostRootLogin( host):
            print( "-- checkHostRootLogin returned error %s" % host)
            countOffline += 1
            continue
        cmd = "scp %s root@%s:%s" % (src, host, dest)
        print( "%s" % cmd)
        if os.system( cmd): 
            print( "Missed to update %s" % host)
            countFailed += 1
            continue
        else: 
            print( "Updated %s OK" % host)
        print( "\n scpExpPCsRoot: %d/%d (offline %d, missed %d) %s \n" % (count, sz, countOffline, countFailed, host))
        count += 1
    return

if __name__ == "__main__":
    main()


    

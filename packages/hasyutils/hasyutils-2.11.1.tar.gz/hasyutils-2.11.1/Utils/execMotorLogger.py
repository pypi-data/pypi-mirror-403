#!/usr/bin/env python3
import os, re, sys,time, datetime, math
import argparse
import HasyUtils
import subprocess

HOST_LIST =  "/home/kracht/Monitors/dbHosts.lis"

TIMEOUT = 1200 # seconds

def doSingle( host):
    '''
    '''
    #
    # is <host> online?
    #
    if not HasyUtils.checkHostOnline( host):
        print( "execMotorLogger: %s is offline " % host)
        return None
    #
    # root login ok?
    #
    if not HasyUtils.checkHostRootLogin( host):
        print( "execMotorLogger: %s no root login " % host)
        return None
    #
    # /home/etc/local_user exists"
    #
    com = [ "ssh", "root@%s" % host, "test -e /home/etc/local_user || echo NotExist"]
    try:
        lst = HasyUtils.runSubprocess( com, timeout = 3)
    except Exception as e:
        print( repr( e))
        print( "command %s timed-out \n" % com)
        return
    if str( lst[0]).find( 'NotExist') != -1:
        print( "%s has no /home/etc/local_user" % host)
        return None
    #
    # /online_dir exists
    #
    com = [ "ssh", "root@%s" % host, "test -d /online_dir || echo NotExist"]
    try:
        lst = HasyUtils.runSubprocess( com, timeout = 3)
    except Exception as e:
        print( "'ssh' on %s timed-out \n" % host)
        return
    if str( lst[0]).find( 'NotExist') != -1:
        print( "%s has no /online_dir" % host)
        return None
    #
    # /usr/bin/MotorLogger.py exists
    #

    com = [ "ssh", host, "test -e /usr/bin/MotorLogger.py || echo NotExist"]
    try:
        lst = HasyUtils.runSubprocess( com, timeout = 3)
    except Exception as e:
        print( "'ssh' on %s timed-out \n" % host)
        return
    if str( lst[0]).find( 'NotExist') != -1:
        print( "%s has no MotorLogger.py" % host)
        return None
    #
    # avoid 'su -l' because of the dconf errors
    #
    # ssh root@haspp08 "su p08user -c 'set -a; . /etc/tangorc; MotorLogger.py -x'"
    #
    com = [ "ssh", host, " test -d /online_dir/MotorLogs && (set -a; . /etc/tangorc; MotorLogger.py -x)"]
    if os.isatty(1):
        print( "execute: %s, %s" % ( host, com))

    try:
        lst = HasyUtils.runSubprocess( com, timeout = 20)
    except Exception as e:
        print( "'MotorLogger.py -x' on %s failed \n" % host)
        print( repr( e))
        return
    if os.isatty(1):
        if len( lst[0]) != 0 or len( lst[1]) != 0:
            print(  "reply: %s" % repr( lst))

    return None

def doAll():
    #
    # for all hosts
    #
    hosts = HasyUtils.getListFromFile( HOST_LIST)
    count = 1
    for host in hosts:
        if os.isatty(1):
            print( "%d/%d %s" % ( count, len( hosts), host))
            count += 1
        
        doSingle( host)

def main():
    parser = argparse.ArgumentParser( 
        formatter_class = argparse.RawDescriptionHelpFormatter,
        description="Run MotorLogger on all hosts", 
        epilog='''\
Examples:
  ./execMotorLogger.py  -x
        create /online_dir/MotorLogs/motorLog.lis, .py
    ''')

    parser.add_argument( '-x', dest="create", action="store_true", 
                         help='create /online_dir/MotorLogs/motorLog.lis, .py ')
    args = parser.parse_args()
    
    if args.create:
        doAll()
        return

    parser.print_help()
    
if __name__ == "__main__":
    main()


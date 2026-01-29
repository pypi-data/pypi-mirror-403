#!python
'''
this script creates some files which may be useful for diagnosis

  /online_dir/Diag/PoolCore.<pid> 
  /online_dir/Diag/MacroServerCore.<pid> 

  /online_dir/Diag/MacroServer.log
  /online_dir/Diag/Pool.log
    the last 1000 lines in the log files

called by: 
  $HOME/gitlabDESY/Sardana/hasyutils/scripts/SardanaAIO.py
  $HOME/gitlabDESY/Sardana/hasyutils/scripts/SardanaRestartBoth.py
  $HOME/gitlabDESY/Sardana/hasyutils/scripts/SardanaRestartMacroServer.py

'''
import os, sys

MAX_CORE_DUMPS = 10

def getPID( procName): 
    '''
    return the PID of procName as a string
    notice: there are 2 MacroServer processes, the second counts
    '''
    prc = os.popen( "pgrep %s" % procName)
    ret = prc.read()
    prc.close()
    if len( ret) == 0:
        print( "SardanaDiag: no %s running" % procName)
        return None
    lst = ret.split()
    if len( lst) == 1:
        pid = lst[0]
    elif len( lst) == 2:
        pid = lst[1]
    else: 
        print( "SardanaDiag: unexpected reply %s" % ret)
        return None
    return pid

def createCoreDump( procName): 
        
    pid = getPID( procName)
    if pid is None:
        return

    os.system( "gcore -o /online_dir/Diag/%sCore %s > /dev/null 2>&1" % (procName, pid))

    print( "SardanaDiag: created /online_dir/Diag/%sCore.%s" % ( procName, pid))

    return

def saveLogs():

    prc = os.popen( "grep TANGO_USER /etc/tangorc")
    ret = prc.read()
    prc.close()
    ret = ret.strip()
    tangoUser = ret.split( '=')[1]

    prc = os.popen( "hostname")
    ret = prc.read()
    prc.close()
    hostName = ret.strip()

    prc = os.popen( "tail -1000 /tmp/tango-%s/MacroServer/%s/log.txt" %  (tangoUser, hostName))
    ret = prc.read()
    prc.close()

    if os.path.exists( "/usr/local/bin/vrsn") and os.path.exists( "/online_dir/Diag/MacroServer.log"):
        os.system( "/usr/local/bin/vrsn -nolog -s /online_dir/Diag/MacroServer.log")

    out = open( "/online_dir/Diag/MacroServer.log", "w")
    out.write( ret)
    out.close()

    print( "SardanaDiag: created /online_dir/Diag/MacroServer.log")

    prc = os.popen( "tail -1000 /tmp/tango-%s/Pool/%s/log.txt" %  (tangoUser, hostName))
    ret = prc.read()
    prc.close()

    if os.path.exists( "/usr/local/bin/vrsn") and os.path.exists( "/online_dir/Diag/Pool.log"):
        os.system( "/usr/local/bin/vrsn -nolog -s /online_dir/Diag/Pool.log")

    out = open( "/online_dir/Diag/Pool.log", "w")
    out.write( ret)
    out.close()

    print( "SardanaDiag: created /online_dir/Diag/Pool.log")

    return 

def restrictNoOfVersions( fName): 
    from stat import S_ISREG, ST_CTIME, ST_MODE
    import os, sys, time

    dirpath = '/online_dir/Diag'
    #
    # get all files of a directory with stat
    #
    entries = (os.path.join(dirpath, fn) for fn in os.listdir(dirpath))
    entries = ((os.stat(path), path) for path in entries)
    #
    # keep regular files only
    #
    entries = ((stat[ST_CTIME], path) for stat, path in entries if S_ISREG(stat[ST_MODE]))
    #
    # keep those files only that match fName
    #
    entries = ((cdate, path) for cdate, path in entries if path.find( fName) > 0)

    lst = [ (cdate, path) for cdate, path in sorted( entries)] 

    nDel = len( lst) - MAX_CORE_DUMPS

    for cdate, path in lst:
        if nDel > 0:
            print( "deleting %s %s" % (time.ctime( cdate), path))
            os.remove( path)
        nDel -= 1

    return 
    
if __name__ == "__main__":
    try: 
        if not os.path.exists( "/online_dir/Diag"):
            os.mkdir( "/online_dir/Diag")
    except Exception as e:
        print( "diag: failed to create /online_dor/Diag")
        print( repr( e))
        sys.exit( 255)

        
    createCoreDump( "MacroServer")
    createCoreDump( "Pool")
    saveLogs()

    restrictNoOfVersions( 'MacroServerCore')
    restrictNoOfVersions( 'PoolCore')

    if os.path.exists( "/usr/local/bin/vrsn") and os.path.exists( "/online_dir/Diag/Pool.log"):
        os.system( "/usr/local/bin/vrsn -p %d -nolog /online_dir/Diag/Pool.log" % MAX_CORE_DUMPS)
    if os.path.exists( "/usr/local/bin/vrsn") and os.path.exists( "/online_dir/Diag/MacroServer.log"):
        os.system( "/usr/local/bin/vrsn -p %d -nolog /online_dir/Diag/MacroServer.log" % MAX_CORE_DUMPS)

    

#!/usr/bin/env python3
#   
from . import TgUtils
import os as _os
import sys as _sys
import importlib as _importlib
import datetime as _datetime
try: 
    import h5py as _h5py
except:
    pass
import numpy as _np
import time as _time
import time as _time
from . import TgUtils
from HasyUtils.pyqtSelector import *

#
#
#
def getHostVersionSardana( host = None):
    """
    check <host> for the sardana python version

    returns 
      2, if python-sardana is installed
      3, if python3-sardana is installed

    use HasyUtils.getVersionSardana() for the local version
    """
    isP2 = False
    isP3 = False

    if host is None: 
        raise ValueError( "OtherUtils.getHostVersionSardana: use HasyUtils.getVersionSardana() for the local version")

    prc = _os.popen('hostname')
    argout = prc.read()
    prc.close()
    localhost = argout.strip()

    if host == localhost:  
        prc = _os.popen( "dpkg --status python3-sardana 2> /dev/null || echo failedfailed")
    else: 
        #
        # disable x-forwarding because of ci-running using fake DISPLAY
        #
        prc = _os.popen('ssh -x root@%s "dpkg --status python3-sardana 2> /dev/null || echo failedfailed"' % host)

    argout = prc.read()
    prc.close()

    if len( argout) == 0: 
        return None

    if argout.find( 'failedfailed') == -1:
        isP3 = True

    if host == localhost:  
        prc = _os.popen("dpkg --status python-sardana 2> /dev/null || echo failedfailed")
    else: 
        prc = _os.popen('ssh -x root@%s "dpkg --status python-sardana 2> /dev/null || echo failedfailed"' % host)

    argout = prc.read()
    prc.close()
    if argout.find( 'failedfailed') == -1:
        isP2 = True

    if isP2 and isP3:
        raise ValueError( "OtherUtils.getHostVersionSardana: found python-sardana AND python3-sardana")
    if not isP2 and not isP3:
        raise ValueError( "OtherUtils.getHostVersionSardana: found neither python-sardana nor python3-sardana")
    if isP3: 
        argout = 3
    else: 
        argout = 2
    return argout

#
# a copy of this function is in 
#   $HOME/gitlabDESY/hasyutils/HasyUtils/TgUtils.py
#
def assertProcessRunning(processName): 
    """
    returns ( True, False), if processName is running
    returns ( False, False), if the processName (the file) does not exist
    returns ( True, True), if processName was launched successfully
    returns ( False, False), if the launch failed

    example: 
      (status, wasLaunched) = HasyUtils.assertProcessRunning( '/usr/bin/pyspMonitor.py')

  """
    #
    # see, if the pyspMonitor process exists. Otherwise launch it
    #
    if findProcessByName( processName): 
        return (True, False)

    #
    # processName can be: /usr/bin/pyspMonitor.py -p 7780
    #
    lst = processName.split( ' ')    
    processNameStripped = lst[0]
    if not _os.path.isfile( processNameStripped):
        print( "OtherUtils.assertProcessRunning: %s does not exist" % processName)
        return (False, False)
    
    if _os.system( "%s &" % processName):
        print( "OtherUtils.assertProcessRunning: failed to launch %s" % processName)
        return (False, False)

    count = 0
    while 1: 
        count += 1
        if findProcessByName( processNameStripped): 
            #
            # we need some extra time. The process appears in
            # the process list but is not active
            #
            _time.sleep( 5) # +++ 
            return (True, True)
        _time.sleep( 0.1)
        if count > 15:
            print( "OtherUtils.assertProcessRunning: %s does not start in time " % processName)
            return ( False, False)

    return (True, True)


#
# a copy of this function is in 
#   $HOME/gitlabDESY/pySpectra/PySpectra/misc/utils.py
#
def findProcessByName( cmdLinePattern):
    """
    returns True, if the process list contains a command line
    containing the pattern specified

    cmdLinePattern, e.g.: 'pyspMonitor.py' 
      which matches ['python', '/usr/bin/pyspMonitor.py']

    """
    import psutil

    for p in psutil.process_iter():
        lst = p.cmdline()
        if len( lst) == 0:
            continue
        for elm in lst: 
            if elm.find( cmdLinePattern) != -1:
                return True
    return False
#
#
#
def killProcessName( processName): 
    '''
    HasyUtils.killProcessName( "/usr/bin/pyspMonitor.py")
    HasyUtils.killProcessName( "pyspMonitor.py")
    '''
    import subprocess, signal

    prc = _os.popen( 'ps -Af')
    lst = prc.readlines()
    prc.close()
    for line in lst:
        if processName in line:
            pid = int(line.split()[1])
            _os.kill(pid, signal.SIGKILL)
    return 

def checkHostOnline( host): 
    '''
    returns True, if the host replies to ping, 
    includes checkHostExists()
    '''

    if not checkHostExists( host):
        return False

    prc = _os.popen( "ping -c 1 -w 1 -q %s 1>/dev/null 2>&1 || echo offline" % host)
    lines = prc.readlines()
    prc.close()
    if 'offline\n' in lines:
        return False
    return True

def checkHostDebian9( host): 
    '''
    executes lsb_release -c on the remote host.
    returns True, if the command returns a line containing 'stretch'

    using user root because we have a checkHostRootLogin() before anyway
    '''
    prc = _os.popen('hostname')
    argout = prc.read()
    prc.close()
    localhost = argout.strip()
    if host == localhost: 
        prc = _os.popen( "lsb_release -c")
    else: 
        prc = _os.popen( "ssh root@%s lsb_release -c" % host)
    lines = prc.readlines()
    prc.close()
    for line in lines: 
        if line.find( "stretch") != -1: 
            return True
    return False

def checkHostDebian10( host): 
    '''
    executes lsb_release -c on the remote host.
    returns True, if the command returns a line containing 'buster'
    '''
    prc = _os.popen('hostname')
    argout = prc.read()
    prc.close()
    localhost = argout.strip()
    if host == localhost: 
        prc = _os.popen( "lsb_release -c")
    else: 
        prc = _os.popen( "ssh root@%s lsb_release -c" % host)
    lines = prc.readlines()
    prc.close()
    for line in lines: 
        if line.find( "buster") != -1: 
            return True
    return False

def checkHostDebian11( host): 
    '''
    executes lsb_release -c on the remote host.
    returns True, if the command returns a line containing 'bullseye'
    '''
    prc = _os.popen('hostname')
    argout = prc.read()
    prc.close()
    localhost = argout.strip()
    if host == localhost: 
        prc = _os.popen( "lsb_release -c")
    else: 
        prc = _os.popen( "ssh root@%s lsb_release -c" % host)
    lines = prc.readlines()
    prc.close()
    for line in lines: 
        if line.find( "bullseye") != -1: 
            return True
    return False

def checkHostDebian12( host): 
    '''
    executes lsb_release -c on the remote host.
    returns True, if the command returns a line containing 'bookworm'
    '''
    prc = _os.popen('hostname')
    argout = prc.read()
    prc.close()
    localhost = argout.strip()
    if host == localhost: 
        prc = _os.popen( "lsb_release -c")
    else: 
        prc = _os.popen( "ssh root@%s lsb_release -c" % host)
    lines = prc.readlines()
    prc.close()
    for line in lines: 
        if line.find( "bookworm") != -1: 
            return True
    return False

def checkHostExists( host): 
    '''
    returns True, if the host name resolves (exist)
    '''
    import socket

    try: 
        socket.gethostbyname( host)
    except socket.error: 
        return False

    return True

class _MyAlarm(Exception):
    pass

def alarm_handler(signum, frame):
    raise _MyAlarm

def checkHostRootLogin( host): 
    '''
    - returns True, if the host replies to a root login (executing 'hostname')
    - the time-out is 3 seconds
    - includes checkHostOnline()
    '''
    import subprocess 
    import signal

    if not checkHostOnline( host): 
        #print( "OtherUtils.checkHostRootLogin: %s is not online" % host)
        return False

    signal.signal(signal.SIGALRM, alarm_handler)

    try: 
        #
        # the ssh authentication flag make this thing running also from cronjobs
        #
        p = subprocess.Popen( ['ssh', "-x", "-o", "PubkeyAuthentication=yes",  "-o", 
                               "GSSAPIAuthentication=no", "root@%s" % host,  "hostname > /dev/null" ])
    except Exception as e:
        print( "checkHostRooLogin: exception occured %s" % repr( e))
    signal.alarm( 3)

    try: 
        p.wait()
        signal.alarm(0)
    except _MyAlarm:
        p.kill()
        p.wait()
        return False

    return True

def checkHostUserLogin( host): 
    '''
    - returns True, if USER can login to the remote host 
    - includes checkHostOnline()
    - this command is used
      prc = _os.popen('ssh -x -o PubkeyAuthentication=yes \
                       -o GSSAPIAuthentication=no  -o BatchMode=yes %s hostname 2>&1' % host)

    '''
    import subprocess 
    import signal

    if not checkHostOnline( host): 
        #print( "OtherUtils.checkHostRootLogin: %s is not online" % host)
        return False

    prc = _os.popen('ssh -x -o PubkeyAuthentication=yes -o GSSAPIAuthentication=no  -o BatchMode=yes %s hostname 2>&1' % host)
    argout = prc.read().strip()
    prc.close()

    #print( "checkHostUserLogin: %s" % repr( argout))

    if argout.find( "Permission denied") != -1: 
        return False

    return True

def checkRemotePathExists( hostName, pathName): 
    '''
    returns True, if pathName exists on the remote host

    checkRemotePathExists( 'haspp99', '/home') -> True
    '''
    cmd = "ssh -x %s test -e %s || echo notExist" % (hostName, pathName)
    prc = _os.popen( cmd)
    res = prc.read()
    prc.close()

    if res.find( 'notExist') == 0: 
        return False
    else: 
        return True


def doty2datetime(doty, year = None):
    """
    Convert the fractional day-of-the-year to a datetime structure.
    The default year is the current year.

    Example: 
      a = doty2datetime( 28.12)
      m = [ 'Jan', 'Feb', 'Mar', 'Aptr', 'Jun', 'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec']
      print( "%s %d, %02d:%02d" % (m[ a.month - 1], a.day, a.hour, a.minute))
      --> Jan 29, 02:52
    """
    if year is None:
        now = _datetime.datetime.now()
        year = now.year
    dotySeconds = doty*24.*60.*60
    boy = _datetime.datetime(year, 1, 1)
    return boy + _datetime.timedelta(seconds=dotySeconds)

def readHostList( fName):
    '''
    read a host list
      - comment lines and empty lines are ignored
    '''
    if not _os.path.isfile( fName):
        raise Exception( "OtherUtils.readHostList", "%s does not exist" % fName)
    
    try:
        inp = open( fName, 'r')
    except Exception as e:
        raise Exception( "OtherUtils.readHostList", "failed to optn %s" %fName)

    hosts = []
    for line in inp.readlines():
        if line.strip().find( '#') == 0:
            continue
        if len( line.strip()) == 0:
            continue
        hosts.append( line.strip())
    inp.close()

    return hosts

def fioAddsToFile( fileName):
    '''
    creates fileName filled with a list and/or a dict from  /online_dir/fioAdds.py
    '''
    if _os.path.exists( fileName):
        raise Exception( "fioAddsToFile", " %s exists already" % fileName)

    (fioList, fioDict) = getFioAdds()

    if fioList is None and fioDict is None:
        raise Exception( "fioAddsToFile", " no list, no dict from fioAdds.py")

    fd = open( fileName, 'w')

    fd.write("!\n! Comments\n!\n%c\n")
    
    if not fioList is None:
        for elm in fioList:
            fd.write( "%s\n" % (str(elm)))
    fd.flush()
    #
    # write the parameter section, including the motor positions, if needed
    #
    fd.write("!\n! Parameter\n!\n%p\n")
    fd.flush()
    if not fioDict is None:
        for k in sorted( fioDict.keys()):
            fd.write( "%s = %s\n" % (str(k), str(fioDict[k])))
    fd.close()

    return True

def getFioAdds():
    '''
    returns fioList, fioDict from  FioAdditions (MacroServer environment variable
    '''
    fName = TgUtils.getEnv( "FioAdditions")
    if fName is None:
        raise Exception( "getFioAdds", " MacroServer environment variable FioAdditions does not exit")

    #
    # fName      /online_dir/fioAdds.py
    # dirName    /online_dir
    # baseName   fioAdds.py
    # prefixName fioAdds
    #
    dirName = _os.path.dirname( fName)
    baseName = _os.path.basename( fName)
    if baseName.find( '.py') > 0:
        prefixName = baseName.rpartition('.')[0]
    if dirName not in _sys.path:
        _sys.path.insert( 0, dirName)
    try:
        mod = _importlib.import_module( prefixName)
        fioAdds = mod.main()
    except Exception as e:
        raise Exception( "getFioAdds", " failed to import %s, %s" % (fName, repr( e)))
    fioList = None
    fioDict = None
    #
    # allowed: list, dict, [list], [dict], [list, dict], [dict, list]
    #
    if type( fioAdds) is dict:
        fioDict = fioAdds
    elif type( fioAdds) is list:
        if len(fioAdds) == 1:
            if type(fioAdds[0]) is list:
                fioList = fioAdds[0]
            elif type( fioAdds[0]) is dict:
                fioDict = fioAdds[0]
            else:
                fioList = fioAdds
        elif len( fioAdds) != 2:
            fioList = fioAdds
        else:
            if type( fioAdds[0]) is list:
                fioList = fioAdds[0]
                if not fioAdds[1] is dict:
                    raise Exception( "fioAddsToFile", " second list element expected to be a dict")
                fioDict = fioAdds[1]
            elif type( fioAdds[0]) is dict:
                fioDict = fioAdds[0]
                if not type( fioAdds[1]) is list:
                    raise Exception( "fioAddsToFile", " second list element expected to be a list")
                fioList = fioAdds[1]
            else:
                fioList = fioAdds
    else:
        raise Exception( "fioAddsToFile", " expecting list or dict")

    return fioList, fioDict

def getMetadata( envVar = "MetadataScript"): 
    """
    envVar is the Nacroserver environment variable pointing to 
    a script returning a dictionary of metadata, def: MetadataScript
    """
    fName = TgUtils.getEnv(  envVar)
    if fName is None:
        raise Exception( "getMetaData", " MacroServer environment variable %s does not exit" % envVar)

    #
    # fName      /online_dir/fioAdds.py
    # dirName    /online_dir
    # baseName   fioAdds.py
    # prefixName fioAdds
    #
    dirName = _os.path.dirname( fName)
    baseName = _os.path.basename( fName)
    if baseName.find( '.py') > 0:
        prefixName = baseName.rpartition('.')[0]
    if dirName not in _sys.path:
        _sys.path.insert( 0, dirName)
    try:
        mod = _importlib.import_module( prefixName)
        md = mod.main()
    except Exception as e:
        raise Exception( "getMetadata", " failed to import %s, %s" % (fName, repr( e)))

    return md
    
def shebang2P3( dirName = None): 
    """
    changes the shebang of all python files of the current
    direectory for dirName to 
      /usr/bin/python3 or /usr/bin/env python3 
    depending on the initial state
    """
    import glob
    if dirName is not None: 
        _os.chdir( dirName)

    for file in glob.glob( '*.py'):
        print( "changing %s " % file)
        # -n suppress default output
        _os.system( "sed -n 1p %s" % file)
        # -i in place
        _os.system( "sed -i 's/^#!\\/usr\\/bin\\/env python\\s*$/#!\\/usr\\/bin\\/env python3/g' %s" % file)
        _os.system( "sed -i 's/^#!\\/usr\\/bin\\/python\\s*$/#!\\/usr\\/bin\\/python3/g' %s " % file)
        _os.system( "sed -n 1p %s" % file)

    return 

def findEditor(): 
    '''
    retuns an editor, 

    - returns 'emacs' if the environment variable EDITOR does not exist
    - returns 'emacs' if os.getenv( 'EDITOR') does not translate to 
      an executable file
    '''
    editor = _os.getenv( "EDITOR")

    if editor is None:
        editor = "emacs"
    #
    # /bin/nano cannot be used for editing log files
    #
    elif editor == '/bin/nano': 
        editor = "emacs"
    else: 
        if _os.system( "command -v %s > /dev/null" % editor):
            editor = "emacs"
    return editor

def getShellOutput( command, tmo = 10): 
    '''
    Another name for runSubProcess()
    '''
    return runSubprocess( command, tmo)

def runSubprocess( command, timeout=10):
    '''
    uses subprocess.Popen() to execute a system command and 
    return stdout, stderr, proc.returncode
      stdout and stderr are strings, utf-8 decoded

    timeout in seconds 

    TimeoutRunProcess is raised, if a timeout occurs

    Example-1: 
        In [1]: import HasyUtils

        In [2]: HasyUtils.runSubprocess( ["uname", '-r'])
        Out[2]: ('4.19.0-24-amd64\n', '', 0)
       
    Example-2: 
       com = [ "ssh", "root@%s" % host, "test -e /online_dir/TangoDump.lis || echo 'NotExist'"]
       try:
           lst = HasyUtils.runSubprocess( com, timeout = 3)
       except Exception, e:
           print "'ssh' on %s timed-out \n" % host
           return

       if lst[0].find( 'NotExist') != -1:
           print "%s has no /online_dir/TangoDump.lis" % host
           return None
    '''
    import subprocess

    class TimeoutRunProcess(Exception): pass

    proc = subprocess.Popen(command, bufsize=0, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    poll_seconds = .250
    deadline = _time.time()+timeout
    while _time.time() < deadline and proc.poll() == None:
        _time.sleep(poll_seconds)

    if proc.poll() == None:
        if float( _sys.version[:3]) >= 2.6:
            proc.terminate()
        raise TimeoutRunProcess()

    stdout, stderr = proc.communicate()
    return stdout.decode( "utf-8") , stderr.decode( "utf-8"), proc.returncode


def toAIOLog( msg):
    """
    writes a time stamp and the msg to /online_dir/SardanaAIO.log
    """
    temp = "%s: %s" % ( TgUtils.getDateTime(), msg)

    out = open( '/online_dir/SardanaAIO.log', 'a')
    out.write( "%s\n" % temp)
    out.close()

    return
    
def pickleReadDct( fName):
    '''
    read a dictionary from a pickle file
    '''
    import pickle
    
    try: 
        with open( fName, 'rb') as f:
            loaded_dict = pickle.load(f)
        return loaded_dict
    except Exception as e: 
        print( "pickleReadDct: failed with %s" % repr( e))
        return None
        
def pickleWriteDct( fName, hsh):
    '''
    write a dictionary to a pickle file
    '''
    import pickle
    try: 
        with open( fName, 'wb') as handle:
            pickle.dump( hsh,  handle, protocol=pickle.HIGHEST_PROTOCOL)
        return True
    except Exception as e: 
        print( "pickleWriteDct: failed with %s" % repr( e))
        return False

def _extractDevFailed( i, lines, fileName): 
    """
PyTango.DevFailed: DevFailed[
DevError[
    desc = IndexError: list index out of range
           
  origin = Traceback (most recent call last):
  File "/usr/lib/python3/dist-packages/sardana/pool/poolcontroller.py", line 641, in _read_axis_value
    ctrl_value = self.ctrl.ReadOne(axis)
  File "/usr/lib/python3/dist-packages/sardana/PoolController/motor/HasyMotorCtrl.py", line 228, in ReadOne
    if self.device_available[ind - 1] == 1:
IndexError: list index out of range

  reason = PyDs_PythonError
severity = ERR]

DevError[
    desc = Failed to read_attribute on device motor/am_attr_65/1, attribute position
  origin = DeviceProxy::read_attribute()
  reason = API_AttributeFailed
severity = ERR]
]
SardanaTP.W003 DEBUG    2022-06-08 08:49:12,922 haso107d10:10000.attr_65.position: [Tango] read failed (PyDs_PythonError): IndexError: list index out of range

    """
    lst = []

    lst.append( "%06d %s" % (i, lines[i]))
    countOpen = 1
    while True: 
        i += 1
        if i >= len( lines): 
            print( "OtherUtils._extractDevFailed: reached end-of-file")
            return []
            
        countOpen += lines[i].count( '[')
        countOpen -= lines[i].count( ']')
        lst.append( "%06d %s" % (i, lines[i]))
        if countOpen == 0: 
            #
            # want to append also the next DEBUG/ERROR/INFO line
            #
            if i < (len( lines) - 1): 
                lst.append( "%06d %s" % (i, lines[i+1]))
                lst.append( "\n----------\n") 
            break
    return lst

def _extractERRORs( i, lines, fileName): 
    """

    """
    lst = []
    if lines[i].find( 'ERROR') == -1: 
        print( "OtherUtils._extractERROR: something is wrong %s" % lines[i])
        return lst

    j = i

    lst.append( "%06d %s" % (i, lines[i]))
    while True: 
        i += 1
        if i >= len( lines): 
            if (i - j) < 100: 
                lst.append( "\n*** reached end of file ***\n----------\n") 
                return lst
                
            print( "OtherUtils._extractERROR: reached end-of-file")
            print( "OtherUtils._extractERROR: fileName %s " % ( fileName))
            print( "OtherUtils._extractERROR: starting in line %d \n %s " % ( j, lines[j]))
            _sys.exit( 255)

        if (i - j) > 100:
            lst.append( "\n *** output terminated***\n----------\n") 
            return lst

        if lines[i].find( "DEBUG") != -1 or \
           lines[i].find( "ERROR") != -1 or \
           lines[i].find( "INFO") != -1:
            lst.append( "\n----------\n") 
            break
        lst.append( "%06d %s" % ( i, lines[i]))
    return lst

def analyseLogFile( fileName): 
    '''    
    fileName: name of the Macroserver/Pool log file

    returns: list of errors, each error is a list of strings
    '''
    #
    # read the log file into lines
    #
    try: 
        with open( fileName) as f:
            lines = f.read().splitlines()
    except Exception as e: 
        print( "OtherUtils.analyseLOgFile: failed to read %s" % fileName)
        print( repr( e))
        return None

    errors = []
    errorOn = False
    count = 1
    i = 0
    while i < len( lines): 
        if lines[i].find( 'PyTango.DevFailed: DevFailed[') != -1 or \
           lines[i].find( 'PyTango.ConnectionFailed DevFailed[') != -1: 
            lst = _extractDevFailed( i, lines, fileName)
            i += len( lst)
            errors.append( lst) 
            continue
        elif lines[i].find( 'ERROR') != -1: 
            lst = _extractERRORs( i, lines, fileName)
            i += len( lst)
            errors.append( lst) 
            continue
        i += 1
       
    return errors


def getNxsConfig():
    """
   return a dictionary from the NXSConfigServer containing the 
   profileNames (aka measurement group names) and the profile contents.

    Example: 
      hsh = getNxsConfig()
      for profileName in hsh.keys():
          print( profileName) # aka measurement group name
          for cont in hsh[ profileName].keys(): 
              print( "  %s -> %s" % ( repr( cont), repr( hsh[ profileName][cont])))
.
    """
    from nxstools import nxsconfig
    import json as json

    # cnfserver = tango.DeviceProxy("p09/nxsconfigserver/haso228jk")
    #    or
    cnfserver = nxsconfig.openServer(nxsconfig.checkServer())
    cnfserver.Open()

    argout = {}
    for profileName in cnfserver.AvailableSelections():

        profile  = json.loads(cnfserver.Selections([profileName])[0])
        argout[ profileName] = {}
        argout[ profileName][ 'detectorComponents'] = []
        for (key, val) in json.loads(profile["ComponentSelection"]).items():
            if val is True:
                argout[ profileName][ 'detectorComponents'].append( key)

        argout[ profileName][ 'poolDynamicDetectorComponents'] = []
        for (key, val) in json.loads(profile["DataSourceSelection"]).items():
            if val is True:
                argout[ profileName][ 'poolDynamicDetectorComponents'].append( key)

        argout[ profileName][ 'descriptiveComponents'] = []
        for (key, val) in json.loads(profile["ComponentPreselection"]).items():
            if val is True:
                argout[ profileName][ 'descriptiveComponents'].append( key)

        argout[ profileName][ 'dynamicDescriptiveComponents'] = []
        for (key, val) in json.loads(profile["DataSourcePreselection"]).items():
            if val is True:
                argout[ profileName][ 'dynamicDescriptiveComponents'].append( key)

        argout[ profileName][ 'timer'] = json.loads(profile["Timer"])
    
    return argout


import subprocess as _subprocess
class Timeout(Exception): pass

def _run( command, timeout=10):
    """
    code by flybywire, stackoverflow
    """
    proc = _subprocess.Popen(command, bufsize=0, stdout=_subprocess.PIPE, stderr=_subprocess.PIPE)
    poll_seconds = .250
    deadline = _time.time()+timeout
    while _time.time() < deadline and proc.poll() == None:
        _time.sleep(poll_seconds)

    if proc.poll() == None:
        if float(_sys.version[:3]) >= 2.6:
            proc.terminate()
        raise Timeout()

    stdout, stderr = proc.communicate()
    return stdout, stderr, proc.returncode

def getLocalUser( hostname): 
    """ 
    return the contents of /home/etc/local_user
    """ 

    if not checkHostOnline( hostname): 
        print( "OtherUtils.getLocalUser: %s is not online" % hostname)
        return None

    com = [ "ssh", hostname, "cat /home/etc/local_user"]
    try:
        lst = _run( com, timeout = 3)
    except Exception as e:
        print( "Time-out for %s" % hostname)
        print( "%s" % repr( e))
        return None
    if len( lst[0]) == 0:
        print( "%s no local_user" % hostname)
        return None
    return lst[0].decode( "utf-8")
    

def findProcessPort( portNo): 
    '''
    return information about the process connected to portNo
    '''
    com = [ 'sudo', '/home/kracht/tools/findProcessPort.py', '%d' % portNo]
    lst = runSubprocess( com)
    return lst

def notifyUser( msg, user = None): 
    """
    sends a message to all users or a single user on MacroServerHostname

    if MacroServerHostname is a remote host, ssh is used for sending the message.
    """

    hostname = TgUtils.getHostname()
    hostnameMS = TgUtils.getMacroServerHostname()

    if hostname == hostnameMS: 
        if user is None: 
            _os.system( "echo %s | wall" % msg)
        else: 
            _os.system( "echo %s | write %s" % (msg, user))
    else: 
        if user is None: 
            _os.system( "ssh %s \'echo %s | wall\'" % (hostnameMS, msg))
        else: 
            _os.system( "ssh %s \'echo %s | write %s\'" % (hostnameMS, msg, user))

    return 

def notifyUserNonsense( msg): 
    """
    opens a widget displaying a message to the user and waits 
    for the user to click 'exit'
    """
    app = QApplication( [])
    win = QWidget()
    layout = QVBoxLayout()
    win.setLayout( layout)
    label = QLabel( "\n%s\n" % msg)
    label.setMinimumWidth( 200)
    label.setMinimumHeight( 100)
    layout.addWidget( label)
    exitButton = QPushButton()
    layout.addWidget( exitButton)
    exitButton.setText("E&xit")
    exitButton.clicked.connect( win.close)
    win.setWindowTitle("Message")
    win.show()
    #sys.exit(app.exec_())
    app.exec_()
    return 

class handleVersion():
    """
    helper class handling the version of the debian package during build
    """
    def __init__( self, dirName = '.', fileName = 'version.lis'):
        """
        dirName default:  '.'
        fileName default: 'version.lis'
        """
        self.dirName = dirName
        if not _os.path.exists( self.dirName):
            raise ValueError( "handleVersion: %s does not exist" % self.dirName)

        self.fileName = fileName
        if not _os.path.exists( self.fileName):
            raise ValueError( "handleVersion: %s does not exist" % self.fileName)

        return

    def findVersion( self):
        """
        version.lis contains: version 1.3
        returns '1.3'
        """
        try: 
            print( "findVersion: opening %s/%s" % (self.dirName, self.fileName))
            inp = open( "%s/%s" % (self.dirName, self.fileName), "r")
            for line in inp.readlines():
                if line.find( "#") != -1:
                    continue
                (major, minor) = line.split()[1].split( '.')
                break
        except Exception as e:
            print( "handleVersion.findVersion: caught an exception, dir: %s " % self.dirName)
            print( repr( e))
            _sys.exit( 255)
        
        return "%d.%d" % ( int( major), int( minor))

    def incrementMinorVersion( self):
        """
        """
        version = self.findVersion()

        (versionMajor, versionMinor) = version.split( '.')
        print( "incrementVersion: opening %s/%s" % (self.dirName, self.fileName))

        versionMinor = int( versionMinor) + 1

        try: 
            out = open( "%s/%s" % (self.dirName, self.fileName), "w")
            out.write( "#\n# do not edit this file\n#\n") 
            out.write( "version %d.%d\n" % ( int( versionMajor), int( versionMinor)))
            out.close()
        except Exception as e:
            print( "handleVersion.incrementVersion: caught an exception")
            print( repr( e))
            _sys.exit( 255)
    
        return True

    def incrementMajorVersion( self):
        """
        """
        version = self.findVersion()

        (versionMajor, versionMinor) = version.split( '.')
        print( "incrementVersion: opening %s/%s" % (self.dirName, self.fileName))

        versionMajor = int( versionMajor) + 1

        try: 
            out = open( "%s/%s" % (self.dirName, self.fileName), "w")
            out.write( "#\n# do not edit this file\n#\n") 
            out.write( "version %d.%d\n" % ( int( versionMajor), int( versionMinor)))
            out.close()
        except Exception as e:
            print( "handleVersion.incrementVersion: caught an exception")
            print( repr( e))
            _sys.exit( 255)
    
        return True


def news():  
    print( "12.02.2025: added HasyUtils.isAlive( ipaddress, portno)") 
    print( "03.12.2024: python2 no longer supported") 
    print( "27.11.2024: added tngMonitorAttrs class ") 
    print( "04.09.2024: added class handleVersion, used for build Debian packages ") 
    print( "07.08.2024: added getModule(), imports a file and returns the module ") 
    print( "07.08.2024: testImport() from 'import imp' to 'import importlib.util' ") 
    print( "17.07.2024: prepareDetectorAttr (Eiger), the directories for the images and 1D data are created") 
    print( "            to avoid permission issues, if two different users create data at a beamline.") 
    print( "            See HasyUtils..prepareDetectorAttrs? for details") 
    print( "17.07.2024: runMacro/execMacro uses also change events to determine whether the macro actually started") 
    print( "25.06.2024: add 'nPts' to the dictionary created by createScanInfo()") 
    print( "18.06.2024: fix the 'conflict' bug reported by P09 and P10 (controller-names-across-hosts issue)")
    return 


def findCandidateVersion( packageName): 
    """
    packageName, e.g.: spectra-desy 
    look at the Candidate line of apt-cache policy <packageName> to find 
    the major and minor version number
      spectra-desy 1.42-1+deb12u10~fsec
      python3-hasyutils 1.725+debian~fsec

    Note that spectra-desy has deb12u10 in the package name
    because spectra is linked with specific libraries.

    return the ( major, minor) of the Candidate version
    """
    prc = _os.popen('apt-cache policy %s' % packageName)
    argout = prc.read().strip()
    prc.close()
    ( major, minor) = ( None, None)
    try: 
        for line in argout.split( '\n'): 
            line = line.strip()
            #
            # Candidate: 1.276+debian~fsec
            #
            if line.find( "Candidate") == 0:
                lst = line.split( ':')
                if line.find( "+debian") != -1: 
                    lst = lst[1].strip().split( '+')
                    (major, minor) = lst[0].split( '.')
                elif line.find( "-1+deb") != -1: 
                    lst = lst[1].strip().split( '-')
                    (major, minor) = lst[0].split( '.')

    except Exception as e: 
        print( "OtherUtils.findNewPackageName: ERROR\n response %s" % argout)
        print( "  error-msg: %s" % repr( e))
        return ( major, minor)
        

    return ( major, minor)

def findOSVersion():
    """

    reads:       /etc/debian_version
    finds, e.g.: '12.10'
    returns:     ( '12', '10')

    """
    ret = getShellOutput( ["cat", "/etc/debian_version"])
    try: 
        for elm in ret:
            elm = elm.strip()
            if elm.find( '.') != -1:
                lst = elm.split( '.')
                return ( lst[0], lst[1])
    except Exception as e: 
        print( "OtherUtils.findOSVersion: response %s" % repr( ret))
        print( "  error-msg: %s" % repr( e))
        return ( None, None)
    return ( None, None)

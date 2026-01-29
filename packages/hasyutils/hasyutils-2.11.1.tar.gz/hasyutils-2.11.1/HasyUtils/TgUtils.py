#!/usr/bin/env python
# 
#
# 20.9.2018 
#   - added tags feature '-t'
#     *** note: this is coupled with SardanaAIO
#     consider this case, SardanaMotorMenu is lauchned 
#     with a tag which is more exclusive than the
#     last SardanaAIO command. In this case the SMM 
#     would import the remaining devices via the pool      
#
# not fatal because pyspViewer.py might be called on a non-exp host
# 
try: 
    import PyTango as _PyTango
except: 
    pass
try: 
    from taurus.core.util.codecs import CodecFactory as _CodecFactory
except:
    pass
import time as _time
import sys as _sys
import os as _os
import types as _types
import socket as _socket
import select as _select
from . import pooltools
try:
    import apt as _apt
except: 
    _apt = None
    pass
import json as _json
import signal as _signal
import numpy as np
import re as _re

#
#
#
_db = None
_dbProxy = None
_petraGlobalsKeyword = None
#
# save the device list to a global data structure
# need this feature, if we run AOI with -t, e.g. remote, and
# TngGui.py sees, e.g. mot65 but no pool device has been created.
# used by: 
#   GQE.updateArrowCurrent
#   
devListGlobal = None

#
# try to avoid DB I/O, therefore store macroServerProxy
#
_doorProxy = None

def getVersionSardana():
    '''
    returns the version number of the package
      - old: 2.2.4.9-1+deb8u1~fsec
      - new: 2.4.1.1-1+deb9u4~fsec    
      - Debian-10/Python3 3.0.2.6-1+deb10u1~fsec, 16.6.2020

    see also: HasyUtils.getHostVersionSardana( <hostName>), returns 2 or 3. 

    '''
    argout = getPackageVersion( 'python3-sardana')
    if argout is None: 
        argout = getPackageVersion( 'python-sardana')
    return argout

_packageVersionDct = {}
def getPackageVersion( packageName): 
    """
    return the version of the installed package, e.g. 

      p09/door/haso107d10.01 [10]: HasyUtils.getPackageVersion( "python3-sardana")
        Result [10]: '3.0.4.11-1+deb10u1~fsec'

    """
    global _packageVersionDct
    #
    # in the virtual environment apt does not exist
    #
    if _apt is None: 
        return None

    if packageName in _packageVersionDct:
        argout = _packageVersionDct[ packageName]  
    else:
        argout = None 
        cache = _apt.Cache()
        #
        # a packged can be available ...
        #
        if packageName in cache:
            pkg = cache[ packageName]
            #
            # ... but not be installed
            #
            if pkg.installed is not None: 
                argout = pkg.installed.version
        _packageVersionDct[ packageName] = argout  

    return argout
    
def getPythonVersionSardana():
    """
    return python2 or python3 depending on the python*-sardana
    """
    temp = getVersionSardana()
    if temp is None: # fix for the apt issue in virtual environments
        return '/usr/bin/python3'

    vmajor, vminor = [int(ver) for ver in temp.split(".")[:2]]

    argout = '/usr/bin/python'
    if vmajor >= 3:
        argout = '/usr/bin/python3'

    return argout

def versionSardanaNewMg():
    '''
    returns True, if the Sardana version has no 'units' level in the
        measurement group. In this case the Pool has the attribute
        TriggerGateList

    analyses the version string, e.g.: 
      - old: 2.2.4.9-1+deb8u1~fsec 
        vs. 
      - new: 2.4.1.1-1+deb9u4~fsec

      - Debian-10/Python3 3.0.2.6-1+deb10u1~fsec' 

    Code:
      vmajor, vminor = [int(ver) for ver in versionSardana().split(".")[:2]]
      if vmajor > 2 or vminor > 3:
          return True
      else:
          return False
    '''
    if _apt is None: 
        return True

    vmajor, vminor = [int(ver) for ver in getVersionSardana().split(".")[:2]]
    if vmajor > 2 or vminor > 3:
        return True
    else:
        return False
    
def waitForServer( serverName, time_max, tangoHost = None):
    '''
    serverName, e.g.: "OmsVme58/EH" 
    return true, if the server appears in the list of 
    running servers before time_max [s] expires. Limit
    for time_max: 900s
    tangoHost: "haspp99:10000"
    '''
    #
    # first check whether the server is controlled by the starter
    #
    starter = getStarterDevice( serverName, tangoHost)
    if starter is None:
        print( "TgUtils.waitForServer: %s not controlled by Starter" % ( serverName))
        return False

    if time_max > 900:
        print( "TgUtils.waitForServer: time_max %g > max 900" % time_max)
        return False

    startTime = _time.time()
    firstLine = False
    waitTimeBeforePrint = 3
    while 1: 
        if (_time.time() - startTime > waitTimeBeforePrint):
            if _os.isatty(1):
                if not firstLine: 
                    print( "Waiting for %s (max %ds) " % (serverName, time_max), )
                    firstLine = True
                _sys.stdout.write( '.')
                _sys.stdout.flush()
        ret = serverIsRunning( serverName, tangoHost)
        if ret is None: 
            #
            # maybe the Starter is not even active.
            #
            _time.sleep(5)

        if ret:
            if _os.isatty(1):
                if (_time.time() - startTime > waitTimeBeforePrint):
                    print( "")  # because of _sys.stdout.write()
            #
            # if we don't have to wait (sleep) for the server, don't mention the wait-time
            #
            if (_time.time() - startTime) > 1.:
                print( "TgUtils.waitForServer: %s is running after %g s" % ( serverName, _time.time() - startTime))
            return True

        if (_time.time() - startTime) > time_max:
            if _os.isatty(1):
                print( "")
            print( "TgUtils.waitForServer: terminate on time %s" % serverName)
            return False
        
        _time.sleep(1)

    print( "TgUtils.waitForServer: DONE - should never reach this line" )

def serverIsRunning( serverName, tangoHost = None):
    '''
    serverName, e.g.: "OmsVme58/EH" 
    returns True, if the server is in the DevGetRunningServers list
    returns None, if something is really wrong
    tangoHost, e.g.: 'haspp99:10000"
    '''
    try:
        starter = getStarterDevice( serverName, tangoHost)
    except:
        print( "TgUtils.serverIsRunning: failed to get starterDevice\n")
        return None

    if starter is None:
        return False
    
    try:
        starterProxy = _PyTango.DeviceProxy( starter)
    except:
        print( "TgUtils.serverIsRunning: failed to create proxy to starter %s\n                         while checking server %s\n" % (starter, serverName))
        return None
    
    try:
        starterProxy.command_inout("UpdateServersInfo")
    except: 
        #
        # just return None silently because we might might for the Starter after reboot
        #
        return None
    try:
        lst = starterProxy.command_inout("DevGetRunningServers", True)
    except: 
        print( "TgUtils.serverIsRunning: command DevGetRunningServers failed on starter %s" % (starter))
        return None

    if serverName in lst: 
        return True
    return False

def serverIsStopped( serverName, tangoHost = None):
    '''
    serverName, e.g.: "OmsVme58/EH" 
    returns True, if the server is in the DevGetRunningServers list
    '''

    starter = getStarterDevice( serverName, tangoHost)
    
    try:
        starterProxy = _PyTango.DeviceProxy( starter)
    except:
        print( "TgUtils.serverisStopped: failed to create proxy to starter %s\n                         while checking server %s" % ( starter, serverName))
        return False
    
    try:
        starterProxy.command_inout("UpdateServersInfo")
    except: 
        return False
    lst = starterProxy.command_inout("DevGetStopServers", True)

    if serverName in lst: 
        return True
    return False

def lsMacroServerEnvironment(): 
    '''
    display the MS environment
    '''
    tangoHost = _os.environ[ 'TANGO_HOST'].split(':')[0]
    ms = getMacroServerProxy()
    if ms is None: 
        return False

    dct = _CodecFactory().getCodec('pickle').decode(ms.Environment)[1]['new']
    print( "MacroServer %s %s " % (tangoHost, ms.name()))
    for key in list( dct.keys()):
        a = "%s" % dct[key]
        if len(a) > 60:
            a = a[:60] + " ..."
        print( "%-30s %-8s %s" % ( key, dct[key].__class__.__name__, a))
    return True

def checkMacroServerEnvironment():
    '''
    check whether ScanDir and ScanFile are of type 'str' and
    ScanHistory is of type 'list'
    '''
    argout = True
    lst = getMacroServerNames()
    tangoHost = _os.environ[ 'TANGO_HOST'].split(':')[0]
    if not lst:
        print( "%s has no MacroServer" % ( tangoHost))
        return
    for elm in lst:
        errFlag = False
        ms = _PyTango.DeviceProxy( elm)
        dct = _CodecFactory().getCodec('pickle').decode(ms.Environment)[1]['new']
        for s in ['ScanDir', 'ScanFile']: 
            if s not in dct:
                errFlag = True
                argout = False
                print( "%s %s %s does not exist " % ( tangoHost, elm, s))
                continue
            if not type( dct[ s]) is str:
                #
                #  senv ScanFile "['unitTestFIO.fio', 'unitTestNeXus.nxs']
                #
                if s == "ScanFile" and type( dct[s]) is list: 
                    continue
                errFlag = True
                argout = False
                print( "%s %s %s is of type %s " % ( tangoHost, elm, s, dct[ s].__class__))
        for l in ['ScanHistory']: 
            if l not in dct:
                errFlag = True
                argout = False
                print( "%s %s %s does not exist " % ( tangoHost, elm, l))
                continue
            if not type( dct[ l]) is list:
                errFlag = True
                argout = False
                print( "%s %s %s is of type %s " % ( tangoHost, elm, l, dct[ l].__class__))
        if not errFlag:
            print( "%s %s: ScanDir, ScanFile and ScanHistory are ok" % ( tangoHost, elm))
    return argout

def tellBLStaff( errorMsgs, addrList):
    '''
    send the joint errorMsgs list to all recipients of addrList

    e.g.
      HasyUtils.tellBLStaff( ["back to work", "petra delivering beam"], 
                             ["some.name@desy.de", "another.name@desy.de"])
    '''
    if( len( errorMsgs) == 0 or 
        len( addrList) == 0):
            return
        
    for addr in addrList:
        if addr.find( "sms") >= 0:
            _os.system( "echo \"%s\" | mail %s" % ("\n".join( errorMsgs), addr))
        else:
            _os.system( "echo \"%s\" | mail -s ECMonitor %s" % ("\n".join( errorMsgs), addr))

def checkECStatus( errorMsgs = None, 
                   verbose = False, 
                   checkMotor = True, 
                   checkExpChan = True, 
                   checkIO = True, 
                   checkMg = True, 
                   checkDoorNotRunning = False,
                   widget = None, 
                   repair = False):
    """
    Checks the Pool to be online, not FAULT, not ALARM
      MotorList, ExpChannelList, IORegisterList, MeasurementGroupList
    Checks the MacroServer to be online, not FAULT, not ALARM
    Checks the Doors to be online, not FAULT, not ALARM (not RUNNING on condition)
    Checks the ActiveMntGrp to be online, not FAULT, not ALARM
    Checks the elements of the ActiveMntGrp to be online, not FAULT, not ALARM

    checkMotor, checkExpChan, etc: enable/disable checks for Pool devices, 
      esp. interesting is checkNotor because checking motors may take some time, a few seconds

    checkDoorNotRunning: for some applications, e.g. unit tests, you don't
      want the door to be running

    if repair: executes restatPool(), if one bad condition is met.

    returns False if one bad condition is met
    """
    argout = True
    poolOk = True
    msOk = True
    mgOk = True
    if not checkPool( errorMsgs = errorMsgs, verbose = verbose, widget = widget, 
                      checkMotor = checkMotor, 
                      checkExpChan = checkExpChan,
                      checkIO = checkIO, 
                      checkMg = checkMg):
        poolOk = False
        argout = False
    if not checkMacroServer( errorMsgs, verbose, widget): 
        msOk = False
        argout = False
    if not checkDoor( errorMsgs, verbose, widget, checkDoorNotRunning): 
        poolOk = False
        argout = False
    if not checkActiveMeasurementGroup( errorMsgs, verbose, widget):
        mgOk = False
        argout = False

    if argout is False and repair is True: 
        argout = restartPool()
    return argout

def _handleErrorMsgs( msg, errorMsgs = None, verbose = False, widget = None):
    if verbose: 
        print( "%s" % msg)
    if type( errorMsgs) is list: 
        errorMsgs.append( msg)
    if widget is not None: 
        widget.logWidget.append( msg)
    return 

def checkPool( errorMsgs = None, verbose = False, widget = None, 
               checkMotor = True, 
               checkExpChan = True, 
               checkIO = True, 
               checkMg = True): 
    '''
    check whether the local Pool is up and running.
      MotorList, ExpChannelList, IORegisterList, MeasurementGroupList
    Otherwise error messages are appended to errorMsgs

    called from ECMonitor.py

    errorMsgs: list, to be appended with error msgs

    returns True, if all local Pools as up and running
    '''    
    argout = True
    plList = getLocalPoolNames()
    if len(plList) == 0:
        if type( errorMsgs) is list: 
            errorMsgs.append( "No Pool in DB")
        return
    if len( plList) > 1: 
        if type( errorMsgs) is list: 
            errorMsgs.append( "No. of pools %d" % len( plList))
        return

    state = None

    poolName = plList[0]

    if widget is not None: 
        widget.logWidget.append( "Checking Pool %s" % poolName)
        widget.app.processEvents()
    if verbose: 
        print( "Checking Pool %s" % poolName)

    try:
        p = _PyTango.DeviceProxy( poolName)
    except Exception as e:
        temp = "  %s is offline" % ( poolName)
        _handleErrorMsgs( temp, errorMsgs = errorMsgs, verbose = verbose, widget = widget)
        return False

    try:
        state = p.state()
        if verbose: 
            print( "  %s, state %s" % ( poolName, repr( state).split( '.')[-1]))
        if widget is not None: 
            widget.logWidget.append( "  state %s" % repr( state))
        if state == _PyTango.DevState.FAULT:
            if type( errorMsgs) is list: 
                errorMsgs.append( "TgUtils.checkPool: %s in FAULT state" % (poolName))
        if state == _PyTango.DevState.ALARM:
            if type( errorMsgs) is list: 
                errorMsgs.append( "TgUtils.checkPool: %s in ALARM state" % (poolName))
    except _PyTango.DevFailed as e:
        extype, value = _sys.exc_info()[:2]
        if extype == _PyTango.ConnectionFailed:
            temp = "Pool %s not exported" % (poolName)
            _handleErrorMsgs( temp, errorMsgs = errorMsgs, verbose = verbose, widget = widget)
        else:
            if verbose:
                print( "CheckPool: %s Failed with exception %s" % (poolName, extype))
                for err in e.args:
                    print( " reason %s" % err.reason)
                    print( " desc %s " % err.desc)
                    print( " origin %s " % err.origin)
                    print( " severity %s " % err.severity)
            if type( errorMsgs) is list: 
                errorMsgs.append( "CheckPool: %s Failed with exception %s" % (poolName, extype))
                for err in e.args:
                    errorMsgs.append( " reason %s" % err.reason)
                    errorMsgs.append( " desc %s " % err.desc)
                    errorMsgs.append( " origin %s " % err.origin)
                    errorMsgs.append( " severity %s " % err.severity)
            else: 
                pass
            if widget is not None: 
                widget.logWidget.append( "CheckPool: %s Failed with exception %s" % (poolName, extype))
                for err in e.args:
                    widget.logWidget.append( " reason %s" % err.reason)
                    widget.logWidget.append( " desc %s " % err.desc)
                    widget.logWidget.append( " origin %s " % err.origin)
                    widget.logWidget.append( " severity %s " % err.severity)

        return False
    #
    # check the motors: can we connect? Can we read the position?
    #
    if checkMotor: 
        if widget is not None: 
            widget.logWidget.append( "Checking Motorlist")
            widget.app.processEvents()
        if verbose:
            print( "Checking Motorlist")
        for elm in p.motorlist: 
            hsh = _json.loads( elm)
            #print( "  checking %s" % hsh[ 'name'])
            proxy = _PyTango.DeviceProxy( hsh[ 'name'])
            if proxy.state() == _PyTango.DevState.FAULT or \
               proxy.state() == _PyTango.DevState.ALARM:
                temp = "Motor %s state %s" % ( hsh[ 'name'], repr( proxy.state()).split('.')[-1])
                _handleErrorMsgs( temp, errorMsgs = errorMsgs, verbose = verbose, widget = widget)
                argout = False
                continue
            try: 
                pos = proxy.position
            except Exception as e: 
                if type( errorMsgs) is list: 
                    errorMsgs.append( "Motor %s failed to read position" % ( hsh[ 'name']))
                    errorMsgs.append( "Motor %s %s" % ( hsh[ 'name'], repr( e)))
                if verbose: 
                    print( "Motor %s failed to read position" % ( hsh[ 'name']))
                    print( "Motor %s %s" % ( hsh[ 'name'], repr( e)))
                if widget is not None: 
                    widget.logWidget.append( "Motor %s failed to read position" % ( hsh[ 'name']))
                    widget.logWidget.append( "Motor %s %s" % ( hsh[ 'name'], repr( e)))
                argout = False

    #
    # check the experiment channels
    #
    if checkExpChan: 
        if widget is not None: 
            widget.logWidget.append( "Checking ExpChannelList")
            widget.app.processEvents()
        if verbose: 
            print( "Checking ExpChannelList")

        for elm in p.ExpChannelList:  
            hsh = _json.loads( elm)
            try: 
                proxy = _PyTango.DeviceProxy( hsh[ 'name']) 
                temp = proxy.state()
                if temp == _PyTango.DevState.FAULT or \
                   temp == _PyTango.DevState.ALARM: 
                    temp = "  ExpChannel %s state %s" % ( hsh[ 'name'], repr( proxy.state()).split('.')[-1])
                    _handleErrorMsgs( temp, errorMsgs = errorMsgs, verbose = verbose, widget = widget)
                    argout = False
                    continue
            except Exception as e: 
                temp = "ExpChannel failed to create proxy to %s" % ( hsh[ 'name'])
                _handleErrorMsgs( temp, errorMsgs = errorMsgs, verbose = verbose, widget = widget)
                argout = False
                continue
            #if hsh[ 'type'] != 'CTExpChannel': 
            #    continue
            if "TangoDevice" in list( dir( proxy)): 
                try: 
                    proxyTS = _PyTango.DeviceProxy( proxy.TangoDevice)
                except Exception as e: 
                    temp = "CTExpChannel %s failed to create proxy to TangoDevice" % ( hsh[ 'name'])
                    _handleErrorMsgs( temp, errorMsgs = errorMsgs, verbose = verbose, widget = widget)
                    argout = False
                    continue
                try: 
                    if proxyTS.state() == _PyTango.DevState.FAULT or \
                       proxyTS.state() == _PyTango.DevState.ALARM: 
                        temp = "CTExpChannel %s TS state %s" % ( hsh[ 'name'], repr( proxyTS.state()).split('.')[-1])
                        _handleErrorMsgs( temp, errorMsgs = errorMsgs, verbose = verbose, widget = widget)
                        argout = False
                        continue
                except Exception as e: 
                    temp = " CTExpChannel %s exception %s" % ( hsh[ 'name'], repr( e))
                    _handleErrorMsgs( temp, errorMsgs = errorMsgs, verbose = verbose, widget = widget)
                #
                # roi_mca01 has TangoDevice AND TangoAttribute (counts), so we don't
                # want to run into the next hasattr()
                #
                continue
            if proxyHasAttribute( proxy, "TangoAttribute"): 
                #
                # haso107d1:10000/p09/vmexecutor/eh.02/position
                #
                lst = proxy.TangoAttribute.split( "/")
                #
                # haso107d1:10000/p09/vmexecutor/eh.02
                #
                nm = "/".join( lst[:-1])
                try: 
                    proxyTS = _PyTango.DeviceProxy( nm)
                except Exception as e: 
                    temp = "CTExpChannel %s failed to create proxy to tangoattribute" % ( hsh[ 'name'])
                    _handleErrorMsgs( temp, errorMsgs = errorMsgs, verbose = verbose, widget = widget)
                    temp = "CTExpChannel %s %s" % ( hsh[ 'name'], repr( e))
                    _handleErrorMsgs( temp, errorMsgs = errorMsgs, verbose = verbose, widget = widget)
                    argout = False
                    continue

    #
    # check the IORegisterList
    #
    if checkIO:
        if widget is not None: 
            widget.logWidget.append( " Checking IORegisterList")
            widget.app.processEvents()
        if verbose: 
            print( "Checking IORegisterList")
    
        if p.IORegisterList is None: 
            lst = []
        else: 
            lst = p.IORegisterList

        for elm in lst:
            hsh = _json.loads( elm)
            # print( "checking %s" % hsh[ 'name'])
            try: 
                proxy = _PyTango.DeviceProxy( hsh[ 'name']) 
                if proxy.state() == _PyTango.DevState.FAULT or \
                   proxy.state() == _PyTango.DevState.ALARM: 
                    temp = "IORegister %s state %s" % ( hsh[ 'name'], repr( proxy.state()).split('.')[-1])
                    _handleErrorMsgs( temp, errorMsgs = errorMsgs, verbose = verbose, widget = widget)
                    argout = False
                    continue
            except Exception as e: 
                temp = "IORegister failed to create proxy to %s" % ( hsh[ 'name'])
                _handleErrorMsgs( temp, errorMsgs = errorMsgs, verbose = verbose, widget = widget)
                argout = False
                continue

            if "TangoDevice" in list( dir( proxy)): 
                try: 
                    proxyTS = _PyTango.DeviceProxy( proxy.TangoDevice)
                except Exception as e: 
                    temp = "IORegister %s failed to create proxy to TangoDevice" % ( hsh[ 'name'])
                    _handleErrorMsgs( temp, errorMsgs = errorMsgs, verbose = verbose, widget = widget)
                    argout = False
                    continue
                if proxyTS.state() == _PyTango.DevState.FAULT or \
                   proxyTS.state() == _PyTango.DevState.ALARM: 
                    temp = "IORegister %s TS state %s" % ( hsh[ 'name'], repr( proxyTS.state()).split('.')[-1])
                    _handleErrorMsgs( temp, errorMsgs = errorMsgs, verbose = verbose, widget = widget)
                    argout = False
                    continue
                #
                # roi_mca01 has TangoDevice AND TangoAttribute (counts), so we don't
                # want to run into the next hasattr()
                #
                continue
    #
    # check the MeasurementGroupList
    #
    if checkMg: 
        if widget is not None: 
            widget.logWidget.append( "Checking MeasurementGroupList")
            widget.app.processEvents()
        if verbose: 
            print( "Checking MeasurementGroupList")
        for elm in p.MeasurementGroupList:  
            hsh = _json.loads( elm)
            if verbose: 
                print( "    checking %s" % hsh[ 'name'])
            try: 
                proxy = _PyTango.DeviceProxy( hsh[ 'name']) 
                if proxy.state() == _PyTango.DevState.FAULT or \
                   proxy.state() == _PyTango.DevState.ALARM: 
                    temp = "      %s state %s" % ( hsh[ 'name'], repr( proxy.state()).split('.')[-1])
                    _handleErrorMsgs( temp, errorMsgs = errorMsgs, verbose = verbose, widget = widget)
                    argout = False
                    continue
            except Exception as e: 
                temp = "MeasurmentGroupList failed to create proxy to %s" % ( hsh[ 'name'])
                _handleErrorMsgs( temp, errorMsgs = errorMsgs, verbose = verbose, widget = widget)
                argout = False
                continue

    return argout
    
def checkMacroServer( errorMsgs = None, verbose = False, widget = None):
    '''
    check whether the local MacroServer is up and running.
    Otherwise error messages are appended to errorMsgs

    called from ECMonitor.py

    errorMsgs: list, to be appended with error msgs

    returns True, if all local MS as up and running
    '''
    msList = getLocalMacroServerNames()
    if len(msList) == 0:
        if type( errorMsgs) is list: 
            errorMsgs.append( "No MacroServer in DB")
        if verbose: 
            print( "No MacroServer in DB")
        return
    state = None
    argout = True
    if widget is not None: 
        widget.logWidget.append( "Checking Macroserver")
        widget.app.processEvents()
    if verbose: 
        print( "Checking Macroserver")
    for elm in msList:
        try:
            p = _PyTango.DeviceProxy( elm)
        except:
            argout = False
            temp = "  %s, is offline" % ( elm)
            _handleErrorMsgs( temp, errorMsgs = errorMsgs, verbose = verbose, widget = widget)
            continue
        try:
            state = p.state()
            if verbose: 
                print( "  %s, state %s" % ( elm, repr( state).split( '.')[-1]))
            if widget is not None: 
                widget.logWidget.append( "  state %s" % repr( state).split( '.')[-1])
                widget.app.processEvents()
            if state == _PyTango.DevState.FAULT or \
               state == _PyTango.DevState.ALARM:
                argout = False
                temp = "MacroServer %s in %s state" % (elm, state)
                _handleErrorMsgs( temp, errorMsgs = errorMsgs, verbose = verbose, widget = widget)
                continue

        except _PyTango.DevFailed as e:
            argout = False
            extype, value = _sys.exc_info()[:2]
            if extype == _PyTango.ConnectionFailed:
                temp = "MacroServer %s not exported" % (elm)
                _handleErrorMsgs( temp, errorMsgs = errorMsgs, verbose = verbose, widget = widget)
            else:
                if verbose:
                    print( "  MacroServer %s not exported, %s" % (elm, repr( e)))
                if type( errorMsgs) is list: 
                    errorMsgs.append( "CheckMacroServer: failed with exception %s" % (extype))
                    for err in e.args:
                        errorMsgs.append( " reason %s" % err.reason)
                        errorMsgs.append( " desc %s " % err.desc)
                        errorMsgs.append( " origin %s " % err.origin)
                        errorMsgs.append( " severity %s " % err.severity)
                if widget is not None: 
                    widget.logWidget.append( "CheckMacroServer: failed with exception %s" % (extype))
                    for err in e.args:
                        widget.logWidget.append( " reason %s" % err.reason)
                        widget.logWidget.append( " desc %s " % err.desc)
                        widget.logWidget.append( " origin %s " % err.origin)
                        widget.logWidget.append( " severity %s " % err.severity)
                        widget.app.processEvents()
                else: 
                    pass
            continue
    return argout

def checkLocalMeasurementGroups( errorMsgs = None, verbose = False, widget = None):
    '''
    check whether the local Measurement Groups are OK, exportet, not ALARM, not FAULT
    Otherwise error messages are appended to errorMsgs

    called from ECMonitor.py

    errorMsgs: list, to be appended with error msgs

    returns True, if all local MGs as up and running
    '''
    mgList = getLocalMeasurementGroupNames()

    if len(mgList) == 0:
        if type( errorMsgs) is list: 
            errorMsgs.append( "No MG in DB")
        return
    state = None
    argout = True
    for elm in mgList:
        if not checkMeasurementGroup( mgName = elm, errorMsgs = errorMsgs, verbose = verbose, widget = widget):
            argout = False
    return argout

def checkMeasurementGroup( mgName = None, errorMsgs = None, verbose = False, widget = None):
    """
    check the elements of the mgName to be exportet, not FAULT, not ALARM, not MOVING

    errorMsgs: list, to be appended with error msgs

    """
    argout = True
    if mgName is None: 
        mgName = getEnv( "ActiveMntGrp")
        
    if mgName is None:
        if type( errorMsgs) is list: 
            errorMsgs.append( "TgUtils.checkMeasurementGroup: mgName is None")
        return False

    if verbose: 
        print( "Checking MeasurementGroup, mgName: %s" % mgName)

    if widget is not None: 
        widget.logWidget.append( "Checking mgName %s" % mgName)
        widget.app.processEvents()

    try: 
        p = _PyTango.DeviceProxy( mgName)
        state = p.state()
        if verbose: 
            print( "  %s, state %s" % ( mgName, repr( state).split( '.')[-1]))
        if state == _PyTango.DevState.FAULT or \
           state == _PyTango.DevState.MOVING or \
           state == _PyTango.DevState.ALARM:
            argout = False
            temp = "TgUtils.checkMeasurementGroup: %s in %s state" % (mgName, repr( state).split( '.')[-1])
            _handleErrorMsgs( temp, errorMsgs = errorMsgs, verbose = verbose, widget = widget)
    except Exception as e: 
        argout = False
        temp = "TgUtils.checkMeasurementGroup: no proxy to %s" % ( mgName)
        _handleErrorMsgs( temp, errorMsgs = errorMsgs, verbose = verbose, widget = widget)
        
    try: 
        lst = p.ElementList
    except Exception as e:
        argout = False
        temp = " Failed to get ElementList"
        _handleErrorMsgs( temp, errorMsgs = errorMsgs, verbose = verbose, widget = widget)
        return False

    flag = True
    for elm in lst:
        #
        # look at the pool element
        #
        try: 
            p = _PyTango.DeviceProxy( elm)
        except Exception as e:
            argout = False
            temp = " %s is offline" % mgName
            _handleErrorMsgs( temp, errorMsgs = errorMsgs, verbose = verbose, widget = widget)
            flag = False
            continue
        try:
            state = p.state()
            if verbose: 
                if not "TangoDevice" in list( dir( p)): 
                    print( "  %s, state %s" % ( elm, repr( state).split('.')[-1]))
                else: 
                    print( "  %s, state %s, %s " % ( elm, repr( state).split('.')[-1], p.TangoDevice))
            if state == _PyTango.DevState.FAULT or \
               state == _PyTango.DevState.MOVING or \
               state == _PyTango.DevState.ALARM:
                argout = False
                temp = "TgUtils.checkMeasurementGroup: %s in %s state" % (elm, repr( state).split( '.')[-1])
                _handleErrorMsgs( temp, errorMsgs = errorMsgs, verbose = verbose, widget = widget)
                continue

        except _PyTango.DevFailed as e:
            argout = False
            extype, value = _sys.exc_info()[:2]
            flag = False
            if verbose:
                print( "TgUtils.checkMeasurementGroup: %s.state() failed, %s" % (elm, extype))
            if extype == _PyTango.ConnectionFailed:
                if type( errorMsgs) is list: 
                    errorMsgs.append( "TgUtils.checkMeasurementGroup: %s not exported" % (elm))
                if widget is not None: 
                    widget.logWidget.append( "TgUtils.checkMeasurementGroup: %s not exported" % (elm))
                    widget.app.processEvents()
            else:
                if type( errorMsgs) is list: 
                    errorMsgs.append( "TgUtils.checkMeasurementGroup: failed with exception %s" % (extype))
                    for err in ve.args:
                        errorMsgs.append( " reason %s" % err.reason)
                        errorMsgs.append( " desc %s " % err.desc)
                        errorMsgs.append( " origin %s " % err.origin)
                        errorMsgs.append( " severity %s " % err.severity)
                if widget is not None: 
                    widget.logWidget.append( "TgUtils.checkMeasurementGroup: failed with exception %s" % (extype))
                    for err in e.args:
                        widget.logWidget.append( " reason %s" % err.reason)
                        widget.logWidget.append( " desc %s " % err.desc)
                        widget.logWidget.append( " origin %s " % err.origin)
                        widget.logWidget.append( " severity %s " % err.severity)
                    widget.app.processEvents()
            continue
        #
        # look at the tango device
        #
        if not "TangoDevice" in list( dir( p)): 
            continue

        try: 
            tmp = p.TangoDevice
        except Exception as e:
            argout = False
            extype, value = _sys.exc_info()[:2]
            flag = False
            if verbose:
                print( "TgUtils.checkMeasurementGroup: %s failed to read TangoDevice" % (elm))
            if extype == _PyTango.ConnectionFailed:
                if type( errorMsgs) is list: 
                    errorMsgs.append( "TgUtils.checkMeasurementGroup: %s failed to read TangoDevice" % elm)
                if widget is not None: 
                    widget.logWidget.append( "TgUtils.checkMeasurementGroup: %s failed to read TangoDevice" % elm)
                    widget.app.processEvents()

            else:
                if type( errorMsgs) is list: 
                    errorMsgs.append( "TgUtils.checkMeasurementGroup: failed with exception %s" % (extype))
                    for err in e.args:
                        errorMsgs.append( " reason %s" % err.reason)
                        errorMsgs.append( " desc %s " % err.desc)
                        errorMsgs.append( " origin %s " % err.origin)
                        errorMsgs.append( " severity %s " % err.severity)
                if widget is not None: 
                    widget.logWidget.append( "TgUtils.checkMeasurementGroup: failed with exception %s" % (extype))
                    for err in e.args:
                        widget.logWidget.append( " reason %s" % err.reason)
                        widget.logWidget.append( " desc %s " % err.desc)
                        widget.logWidget.append( " origin %s " % err.origin)
                        widget.logWidget.append( " severity %s " % err.severity)
                    widget.app.processEvents()
            
            continue

        try: 
            p = _PyTango.DeviceProxy( tmp)
        except:
            argout = False
            flag = False
            temp = "TgUtils.checkMeasurementGroup: %s is offline" % tmp
            _handleErrorMsgs( temp, errorMsgs = errorMsgs, verbose = verbose, widget = widget)
            continue
        try:
            state = p.state()
            if state == _PyTango.DevState.FAULT or \
               state == _PyTango.DevState.ALARM:
                argout = False
                temp = "TgUtils.checkMeasurementGroup: %s in %s state" % (tmp, repr( state).split('.')[-1])
                _handleErrorMsgs( temp, errorMsgs = errorMsgs, verbose = verbose, widget = widget)
                argout = False
        except _PyTango.DevFailed as e:
            argout = False
            extype, value = _sys.exc_info()[:2]
            flag = False
            if extype == _PyTango.ConnectionFailed:
                if type( errorMsgs) is list: 
                    errorMsgs.append( "TgUtils.checkMeasurementGroup: %s not exported" % (tmp))
                if widget is not None: 
                    widget.logWidget.append( "TgUtils.checkMeasurementGroup: %s not exported" % (tmp))

            else:
                if type( errorMsgs) is list: 
                    errorMsgs.append( "TgUtils.checkMeasurementGroup: failed with exception %s" % (extype))
                    for err in e.args:
                        errorMsgs.append( " reason %s" % err.reason)
                        errorMsgs.append( " desc %s " % err.desc)
                        errorMsgs.append( " origin %s " % err.origin)
                        errorMsgs.append( " severity %s " % err.severity)
                else:
                    pass
                if widget is not None: 
                    widget.logWidget.append( "TgUtils.checkMeasurementGroup: failed with exception %s" % (extype))
                    for err in e.args:
                        widget.logWidget.append( " reason %s" % err.reason)
                        widget.logWidget.append( " desc %s " % err.desc)
                        widget.logWidget.append( " origin %s " % err.origin)
                        widget.logWidget.append( " severity %s " % err.severity)
                    widget.app.processEvents()
            continue

    return argout

def checkActiveMeasurementGroup( errorMsgs = None, verbose = False, widget = None):
    """
    check the elements of the ActiveMntGrp to be exportet, not FAULT, not ALARM, not MOVING

    errorMsgs: list, to be appended with error msgs

    """
    argout = True
    activeMntGrp = getEnv( "ActiveMntGrp")
    if verbose: 
        print( "Checking ActiveMntGrp %s" % activeMntGrp) 
    return checkMeasurementGroup( mgName = activeMntGrp, errorMsgs = errorMsgs, verbose = verbose, widget = widget)

def unitTestChecks( msg = "NoMsg"): 
    """
    some checks in the setUpClass and tearDownClass functions
    """
    argout = True

    buffer = []
    if not checkECStatus( errorMsgs = buffer, checkDoorNotRunning = True):
        print( "*** TgUtils.unitTestChecks: %s, checkECStatus returned False, %s" % 
               (msg, repr( buffer)))
        argout = False
        
    return argout

def checkDoor( errorMsgs = None, verbose = False, widget = None, checkDoorNotRunning = False):
    '''
    check the local doors 

    return False, if
      - one of the doors do not respond to state() call
      - one of the doors are in FAULT or ALARM
    return True otherwise

    Error messages are appended to errorMsgs

    errorMsgs: list, to be appended with error msgs

    checkDoorNotRunning is used in the setUp/tearDownClass functions 
      in general it's ok, if a door is RUNNING, in paticular, if 
      checkECStatus() is called from with a Macro (esp. a hook)
    '''
    doorList = getLocalDoorNames()
    if len(doorList) == 0:
        if type( errorMsgs) is list: 
            errorMsgs.append( "No Door in DB")
        return
    state = None
    argout = True
    if widget is not None: 
        widget.logWidget.append( "Checking Doors")
        widget.app.processEvents()
    if verbose:
        print( "Checking Doors")

    for elm in doorList:
        try:
            p = _PyTango.DeviceProxy( elm)
        except:
            if verbose: 
                print( "  %s is offline" % ( elm))
            if type( errorMsgs) is list: 
                errorMsgs.append( "Door %s is offline" % elm)
            if widget is not None: 
                widget.logWidget.append( "Door %s is offline" % elm)
                widget.app.processEvents()
            argout = False
            continue
        try:
            state = p.state()
            if verbose: 
                print( "  %s, state %s" % ( elm, repr( state).split( '.')[-1]))
            if widget is not None: 
                widget.logWidget.append( "  state %s" % ( repr( state)))
                widget.app.processEvents()
            if state == _PyTango.DevState.FAULT:
                argout = False
                if type( errorMsgs) is list: 
                    errorMsgs.append( "TgUtils.checkDoor: %s in FAULT state" % (elm))
                if widget is not None: 
                    widget.logWidget.append( "TgUtils.checkDoor: %s in FAULT state" % (elm))
            if state == _PyTango.DevState.ALARM:
                argout = False
                if type( errorMsgs) is list: 
                    errorMsgs.append( "TgUtils.checkDoor: %s in ALARM state" % (elm))
                if widget is not None: 
                    widget.logWidget.append( "TgUtils.checkDoor: %s in ALARM state" % (elm))
                    widget.app.processEvents()
            if checkDoorNotRunning and state == _PyTango.DevState.RUNNING:
                argout = False
                if type( errorMsgs) is list: 
                    errorMsgs.append( "TgUtils.checkDoor: %s in RUNNING state" % (elm))
                if widget is not None: 
                    widget.logWidget.append( "TgUtils.checkDoor: %s in RUNNING state" % (elm))
                    widget.app.processEvents()
        except _PyTango.DevFailed as e:
            if verbose: 
                print( "%s, Eception, %s" % ( elm, repr( e)))
            argout = False
            extype, value = _sys.exc_info()[:2]
            if extype == _PyTango.ConnectionFailed:
                if type( errorMsgs) is list: 
                    errorMsgs.append( "Door %s not exported" % (elm))
                else: 
                    pass
                if widget is not None: 
                    widget.logWidget.append( "Door %s not exported" % (elm))
            else:
                if type( errorMsgs) is list: 
                    errorMsgs.append( "CheckPool: %s Failed with exception %s" % (elm, extype))
                    for err in e.args:
                        errorMsgs.append( " reason %s" % err.reason)
                        errorMsgs.append( " desc %s " % err.desc)
                        errorMsgs.append( " origin %s " % err.origin)
                        errorMsgs.append( " severity %s " % err.severity)
                else: 
                    pass
                if widget is not None: 
                    widget.logWidget.append( "CheckPool: %s Failed with exception %s" % (elm, extype))
                    for err in e.args:
                        widget.logWidget.append( " reason %s" % err.reason)
                        widget.logWidget.append( " desc %s " % err.desc)
                        widget.logWidget.append( " origin %s " % err.origin)
                        widget.logWidget.append( " severity %s " % err.severity)
                    widget.app.processEvents()

            continue

    return argout

def getDoorState(): 
    '''
    returns the state of the first local door
    '''
    doorList = getLocalDoorNames()
    if len(doorList) == 0:
        print( "checkDoorState: No local door")
        return False

    try:
        p = _PyTango.DeviceProxy( doorList[0])
        argout = p.state()
    except Exception as e: 
        print( "checDoorState: caught an exception")
        print( e)
        argout = None
    
    return argout

def getClassList( tangoHost = None):
    '''
    Return list containing all classes, e.g.
    getClassList()
    getClassList( "haspp99:10000")
    '''
    db = _findDB( tangoHost)
    if not db:
        return None

    return db.get_class_list( "*").value_string

def getHostList( tangoHost = None):
    '''
    Return all host names in the local or remote TangoDb
    '''

    db = _findDB( tangoHost)
    if not db:
        return None

    tempList = db.get_host_list( "*").value_string
    hostList = []
    for hst in tempList:
        if hst.find( '.') > 0:
            hst = hst.split( '.')[0]
        if hst == 'nada':
            continue
        if not hst in hostList:
            hostList.append( hst)

    return hostList

def getHostname():
    '''Return the hostname, short form, e.g.: haspp08 '''
    return _socket.gethostname()

def getHostnameLong():
    '''return the hostname, long form, e.g.: haspp08.desy.de '''
    # ('haso107tk.desy.de', ['haso107tk'], ['131.169.221.161'])
    return _socket.gethostbyname_ex( _socket.gethostname())[0]

def getAlias( deviceName, tangoHost = None):
    '''    
    getAlias( "p99/motor/exp.99")
    getAlias(  "p99/motor/exp.99", "haspp99:10000")
    '''    
    db = _findDB( tangoHost)
    if not db:
        return None

    argout = "NoAlias"
    try:
        argout = db.get_alias( deviceName)
    except:
        pass
    return argout


def getDeviceNameByAlias( alias, tangoHost = None):
    '''
    Return the tango device which is referred to by an alias 
    e.g.: getDeviceNameBYAlias( "exp_mot99") 

    tangoHost e.g.: "haspp99:10000"
    '''
    argout = None
    
    db = _findDB( tangoHost)
    if not db:
        return None
    
    try:
        argout = db.get_device_alias( alias)
    except Exception as e:
        print( "TgUtils.getDeviceNameByAlias: alias: %s" % repr( alias))
        print( "TgUtils.getDeviceNameByAlias: %s" % repr( e))

    return argout

def _findDB( tangoHost = None):
    '''
    handle these cases:
      - tangoHost == None: use TANGO_HOST DB
      - tangoHost == "haspp99:10000" return db link
      - tangoHost == "haspp99" insert 100000 and return db link
    '''
    if tangoHost is None:
        if _db is None: 
            print( "TgUtils._findDB: _db is None")
            _sys.exit( 255)
        return _db

    #
    # unexpeccted: tango://haspe212oh.desy.de:10000/motor/dummy_mot_ctrl/1
    #
    if tangoHost.find( 'tango://') == 0:
        print( "TgUtils._fineDB: bad TANGO_HOST syntax %s" % tangoHost)
        return None
    #
    # tangHost "haspp99:10000"
    #
    lst = tangoHost.split( ':')
    if len(lst) == 2:
        return _PyTango.Database( lst[0], lst[1])
    #
    # tangHost "haspp99"
    #
    elif len(lst) == 1:
        return _PyTango.Database( lst[0], "10000")
    else:
        print( "TgUtils._fineDB: failed to return Database, %s" % tangoHost)
        return None

def getDeviceNamesByServer( serverName, tangoHost = None):
    '''
    Return the devices belonging to a server. If tangoHost is
    not supplied, TANGO_HOST is used.

      getDeviceNamesByServer( "DGG2/PETRA-3", "haspp99:10000")
        ['p99/dgg2/exp.01', 'p99/dgg2/exp.01'] 

      getDeviceNamesByServer( "DGG2/PETRA-3")
        ['p99/dgg2/exp.01', 'p99/dgg2/exp.01'] 
    '''

    db = _findDB( tangoHost)
    if not db:
        return None
    #
    # ['dserver/DGG2/PETRA-3', 'DServer', 'p09/dgg2/d1.01', 'DGG2', 'p09/dgg2/d1.02', 'DGG2']
    #
    lst = db.get_device_class_list( serverName).value_string
    if not lst:
        return None
    def pairs( lst):
        a = iter(lst)
        return list( zip( a, a))

    devList = []
    for deviceName, className in pairs( lst):
        if className == "DServer":
            continue
        devList.append( deviceName)
    return devList
    
def getDeviceNamesByClass( className, tangoHost = None):
    '''Return a list of all devices of a specified class, 
        'DGG2' -> ['p09/dgg2/exp.01', 'p09/dgg2/exp.02']
    '''
    srvs = getServerNameByClass( className, tangoHost)
    argout = []
    
    db = _findDB( tangoHost)
    if not db:
        return None

    for srv in srvs:
        lst = db.get_device_name( srv, className).value_string
        for i in range(0, len( lst)):
            argout.append( lst[i])
    return argout

def getMotorNames():
    '''
    get device names of motor classes:
    '''
    motorClassList = [
        "AbsorberController", 
        "Analyzer", 
        "AnalyzerEP01", 
        "AttoCube", 
        "AttoCubeANC300", 
        "AttributeMotor", 
        "CDCMEnergy", 
        "CoupledMonoUndMove", 
        "CubicPressVoggMotor", 
        "CubicPressCylinder", 
        "DiffracMuP09", 
        "DOOCSMotor", 
        "EcovarioServoMotor", 
        "EH2tthP10", 
        "FMBOxfDCMEnergy", 
        "FMBOxfDCMMotor", 
        "FocusingMirrorP02", 
        "GalilDMCMotor", 
        "GalilDMCSlit", 
        "HexapodMotor", 
        "HiResPostMonoP22", 
        "KohzuSCAxis", 
        "KohzuSCMultiAxis", 
        "LensesBox", 
        "LOM", 
        "LomEnergy", 
        "Lom500Energy", 
        "MetaMotor", 
        "MirrorP02", 
        "MirrorP09", 
        "MLMonoEnergy", 
        "MMC100MicosAxis", 
        "MonoP04", 
        "MonoUndSynchronMotor", 
        "MotorEncControlledP04", 
        "MultipleMotors", 
        "NewFocusPicoMotor", 
        "NewFocusPico8742", 
        "OmsVme58", 
        "OwisMMS19", 
        "PhaseRetarderP09", 
        "PIC863Mercury", 
        "PhyMotionMotor", 
        "PiezoJenaNV401CLE", 
        "PiezoPiE185", 
        "PiezoPiE710", 
        "PiezoPiE712", 
        "PiezoPiE725", 
        "PiezoPiE816", 
        "PiezoPiE861", 
        "PiezoPiE871", 
        "PiezoPiE872", 
        "PiezoPiC867Motor", 
        "PitchRollCorrection", 
        "PlcUndulator", 
        "SecondaryMonoP01", 
        "SMCHydraMotor", 
        "Slt", 
        "Spk", 
        "TangoMotor", 
        "TcpIpMotorP10", 
        "TwoThetaP07", 
        "VICIMultiPosValve", 
        "VICITwoPosValve", 
        "VmExecutor"]

    motorList = []
    for motorClass in motorClassList:
        motorList.extend( getDeviceNamesByClass( motorClass))
    return motorList

def getServerInstance( argin, tangoHost = None): 
    '''
    Return a list of Server instances matching the supplied server name.
    argin, e.g. "OmsVme58" result: ["EH"]
    tangoHost e.g.: "haspp99:10000"
    '''
    
    db = _findDB( tangoHost)
    if not db:
        return None

    lst =  db.get_server_list( "*").value_string
    argout = []
    for elm in lst:
        if elm.find( argin) >= 0:           
            argout.append(elm.split("/")[1])
    return argout
        
def getServerNameByClass( argin, tangoHost = None): 
    '''Return a list of servers containing the specified class '''

    db = _findDB( tangoHost)

    srvs = db.get_server_list( "*").value_string

    argout = []

    for srv in srvs:
        classList = db.get_server_class_list( srv).value_string
        for clss in classList:
            if clss == argin:
                argout.append( srv)
                break
    return argout

def getClassNameByDevice( devName, tangoHost = None): 
    """
    return the class name of a device
    """

    db = _findDB( tangoHost)

    if devName.find( ":10000") >= 0:
        lst = devName.split( '/')
        db = _findDB( lst[0])
        devName = "%s/%s/%s" % (lst[-3], lst[-2], lst[-1]) 
    ret = db.get_device_info( devName)

    return ret.class_name

def getServerNameByDevice( devName, tangoHost = None): 
    """
    return the server exporting a device, devName: 'p99/motor/eh.01'
    """
    db = _findDB( tangoHost)

    ret = db.get_device_info( devName)

    return ret.ds_full_name
    
def _getLocalNames( namesList):
    '''Receive  a list of devices and return those devices running locally.'''
    lst_out = []
    hostName = getHostname()
    
    for d in namesList:
        try:
            devInfo = _dbProxy.DbGetDeviceInfo( d)
        except Exception as e:
            print( "---")
            print( "TgUtils._getLocalName: can't get DeviceInfo for %s" % d)
            print( "TgUtils._getLocalName: Is the DB server running?")
            print( _sys.exc_info()[0])
            print( repr( e))
            print( "---")
            continue
            
        #print( "TgUtils._getLocalNames: %s devInfo %s" % (d, devInfo))
        srvHost = devInfo[1][4].split('.')[0]
        if srvHost == hostName:
            lst_out.append( d)
    return lst_out

def getDoorNames():
    '''Return a list of Door tango devices.'''
    return getDeviceNamesByClass( "Door")

def getLocalDoorNames():
    '''Return a list of Door tango devices running locally.'''
    return _getLocalNames( getDeviceNamesByClass( "Door"))

def getMacroServerNames():
    '''Return a list of MacroServer tango devices.'''
    return getDeviceNamesByClass( "MacroServer")

def getLocalMacroServerNames():
    '''Return a list of MacroServer tango devices running locally.'''
    return _getLocalNames( getDeviceNamesByClass( "MacroServer"))

def getLocalMeasurementGroupNames():
    '''Return a list of measurment group devices running locally.'''
    return _getLocalNames( getDeviceNamesByClass( "MeasurementGroup"))

def getLocalMacroServerServers():
    '''Return a list of local MacroServers, e.g.: MacroServer/PETRA-3 '''
    lst = _db.get_server_list("MacroServer*")
    hostName = getHostname()
    argout = []
    for srv in lst:
        a = _db.get_server_info( srv)
        if a.host.split('.')[0] == hostName:
            argout.append(srv)
    return argout

def getDoorProxies(): 
    '''
    return a list of door proxies
    return None, if there are no doors of if DeviceProxy() fails 
    '''
    doorNames = getDoorNames()
    if not doorNames:
        print( "TgUtils.getDoorProxy: no Door found")
        return None
    argout = []
    for door in doorNames: 
        try: 
            door = _PyTango.DeviceProxy( doorNames[0])
            argout.append( door)
        except Exception as e: 
            print( "TgUtils.getDoorProxy: exception from DeviceProxy %s " % doorNames[0])
            print( "TgUtils.getDoorProxy: %s" % repr( e))
            return None

    return argout

def getMacroServerProxy(): 
    '''
    returns the proxy to the MacroServer
    return None, if there are zero or more than one MacroServer or
    if the DeviceProxy() failes. 
    '''
    msNames = getMacroServerNames()
    if not msNames:
        print( "TgUtils.getMacroServerProxy: no MacroServer found")
        return None
    if len( msNames) > 1: 
        print( "TgUtils.getMacroServerProxy: more than one MacroServer %s" % repr( msNames))
        return None

    try: 
        ms = _PyTango.DeviceProxy( msNames[0])
    except Exception as e: 
        print( "TgUtils.getMacroServerProxy: exception from DeviceProxy %s " % msNames[0])
        print( "TgUtils.getMacroServerProxy: %s" % repr( e))
        return None
    return ms

def getMacroServerHostname(): 
    '''
    returns the name of the host where the Macroserver is runnig
    the information is extracted the MacroServer devkice name
    '''
    try: 
        proxy = getMacroServerProxy()
    except Exception as e: 
        print( "TgUtils.getMacroServerHostname: failed to create proxy to MS")
        return None

    #
    # p09/macroserver/haspp09.01
    #
    try: 
        hostname = proxy.name().split( '/')[-1].split( '.')[0]
    except Exception as e: 
        print( "TgUtils.getMacroServerHostname: failed decode %s" % proxy.name())
        return None

    return hostname
        
def getMacroInfo( macroName): 
    '''
    returns a dictionary
    '''
    ms = getMacroServerProxy()
    if ms is None: 
        return None

    ret = ms.command_inout("GetMacroinfo", [macroName])

    argout = _json.loads( ret[0])

    if argout[ 'name'] != macroName: 
        raise ValueError( "TgUtils.getMacroInfo: received %s" % repr( argout))

    return argout
        
def getMacroList(): 
    '''
    returns the list of macros
    '''
    ms = getMacroServerProxy()
    if ms is None: 
        return None

    ret = ms.MacroList

    argout = list( ret)
    #argout = _json.loads( ret[0])

    #if argout[ 'name'] != macroName: 
    #    raise ValueError( "TgUtils.getMacroInfo: received %s" % repr( argout))

    return argout

def getMacroServerServers():
    argout = _db.get_server_list("MacroServer*")
    return argout

def getPoolServers():
    argout = _db.get_server_list("Pool*")
    return argout

doorWasRunning = False

def _door_change_event_callback(event):
    global doorWasRunning
    if not event.err:
        if str( event.attr_value.value) == 'RUNNING':
            #print( "TgUtils.door_change_event_callback: %s" % repr( event.attr_value.value))
            doorWasRunning = True
    else:
        raise ValueError( "TgUtils.door_change_event_callback: error %s" % repr( event.errors))

def runMacro( macroString):
    '''
    macroString: "ascan exp_dmy01 0 1 10 0.1"
    
    the macro is started on getDoorNames()[0]
    the function waits for the completion.
     
    use startMacro() for an asynchronous call

    return: door.output

    Further explanations: 
      - at the beginning: an exception is thrown, if the door is not ON
      - after door.runMacro() is executed, we wait for the door to become RUNNING
          - the state is sensed in a change_event_callback
          - the state is sensed by polling with 100 Hz
      - if the door doesn not become RUNNING after 0.2s, an exception is raised
      - then the function waits for the door to become not RUNNINGG
      - eventually an exception is thrown, if the door is not ON
    '''
    global doorWasRunning

    lst = macroString.split()
    try:
        door = _PyTango.DeviceProxy( getDoorNames()[0])
    except: 
        return "No door"

    if door.state() is not _PyTango.DevState.ON:
        raise Exception( "TgUtils.runMacro:",  
                         "door.state() is %s, Debug: %s, Info %s" % 
                         (repr( door.state()), 
                          repr( door.Debug), 
                          repr( door.Info)))

    eventId = door.subscribe_event("state", _PyTango.EventType.CHANGE_EVENT, _door_change_event_callback)

    doorWasRunning = False

    door.runMacro( lst)

    # 
    # wait for the door to become running
    # 
    startTime = _time.time()
    while True:
        #print( "runMacro state %s, doorWasRunning %s" % ( repr( door.state()), repr( doorWasRunning)))
        if doorWasRunning: 
            #print( "became running after %g (eventHandler)" % (_time.time() - startTime))
            break

        wasRunning = door.state() == _PyTango.DevState.RUNNING
        if wasRunning: 
            #print( "became running after %g (polling), doorWasRunning %s " % ((_time.time() - startTime), doorWasRunning))
            break
        # 
        # if the door is not RUNNING after 0.2 s, assume that 
        # the macro has alrady been executed
        # maxTime == 0.01 for 10000 tests
        #
        if (_time.time() - startTime) > 0.2:
            raise Exception( "TgUtils.runMacro:",  
                             "door.state() is %s, does not become RUNNING after 0.2" % 
                             (repr( door.state())))
        _time.sleep( 0.01)

    while door.state() is _PyTango.DevState.RUNNING:
        _time.sleep( 0.1)

    if door.state() is not _PyTango.DevState.ON:
        raise Exception( "TgUtils.runMacro: after loop",  
                         "door.state() is %s, Debug: %s, Info %s" % 
                         (repr( door.state()), 
                          repr( door.Debug), 
                          repr( door.Info)))

    door.unsubscribe_event( eventId)
    return door.output

def execMacro( macroString):
    '''
    another name for runMacro
    '''
    return runMacro( macroString)

def startMacro( macroString):
    '''
    macroString: "ascan exp_dmy01 0 1 10 0.1"
    
    the macro is started on getDoorNames()[0]
    the function waits for the door to become RUNNING for 0.2 s
    the function does not wait for completion 
    '''
    lst = macroString.split()
    try:
        door = _PyTango.DeviceProxy( getDoorNames()[0])
    except: 
        return "No door"

    if door.state() is not _PyTango.DevState.ON:
        raise Exception( "TgUtils.startMacro:",  
                         "door.state() is %s, Debug: %s, Info %s" % 
                         (repr( door.state()), 
                          repr( door.Debug), 
                          repr( door.Info)))

    door.runMacro( lst)

    startTime = _time.time()
    while True:
        if door.state() == _PyTango.DevState.RUNNING:
            break
        # 
        # if the door is not RUNNING after 0.2 s, assume that 
        # the macro has alrady been executed
        # maxTime == 0.01 for 10000 tests
        #
        if (_time.time() - startTime) > 0.2:
            print( "became running after %g" % (_time.time() - startTime))
            break
        _time.sleep( 0.01)

    return 


def stopMacro( doorName = None):
    '''
    execute a stopMacro on a door. 

    if doorName is not supplied the first local door is used.
    '''
    
    print( "this is stopMacro") 

    if doorName is None: 
        doorName = getDoorNames()[0]

    try:
        door = _PyTango.DeviceProxy( doorName)
    except exception as e: 
        print( "TgUtils.stopMacro, exception %s" % repr( e))
        return 

    
    if door.state() != _PyTango.DevState.RUNNING:       
        return 

    print( "this is stopMacro, is RUNNING") 
        
    door.StopMacro()        

    startTime = _time.time()

    while door.state() != _PyTango.DevState.ON: 
        _time.sleep( 0.1)
        
        if (_time.time() - startTime) > 5: 
            print( "stopMacro: door.state() not ON after 5 s") 
            return False

    return True

def notifySpock( msg): 
    """
    executed stopMacro then sends sends 'msg' to Spock

    NOT WORKING PROPERLY SO FAR
    """
    
    print( "this is notifySpock") 

    if stopMacro() is False: 
        return False

    runMacro( "notifySpock '%s'" % msg)
    
    return True

    
def getMacroServerStatusInfo():
    '''
    this code is also in PySpectra.utils

    parses the MacroServer status() information; to be printed in a Label Widget

    returns e.g.:
      - "Idle"
      - "ascan"
      - "IVPmacro -> change_mg"
    '''
    global _doorProxy
    #
    # in case the macroserver is IDLE: 
    # macroStatusLst ['The device is in ON state.', 
    #                 ' Macro stack ([state] macro):', 
    #                 '    -[finish]\tIVPmacro mg']
    # 
    # macroStatusLst ['The device is in RUNNING state.', 
    #                 ' Macro stack ([state] macro):', 
    #                 '    -[start]\tIVPmacro mg', 
    #                 "    -[start]\tchange_mg [['-g', 'mg_ivptest'], ['-t', 'd1_t01'], ['-c', 'd1_c01,d1_c02']]"]
    #
    if _doorProxy is None:
        try:
            _doorProxy = _PyTango.DeviceProxy( getDoorNames()[0])
        except: 
            return "No door"

    macroStatusLst = _doorProxy.status().split( "\n")
    if macroStatusLst[0] == 'The device is in ON state.' or \
       macroStatusLst[0] == 'Door is On': # 7.8.2024
        argout = "Idle"
        return argout
    try:
        a = ""
        for elm in macroStatusLst[2:]:
            lst = elm.split("\t")
            lst1 = lst[1].split()
            a = a + lst1[0] + '->'
    except: 
        a = "unknown ->" 
    #
    # cut the trailing '->'
    #
    argout = a[:-2]
    return argout


def getPoolNames():
    '''Return a list of Pool tango devices.'''
    return getDeviceNamesByClass( "Pool")

def getLocalPoolNames():
    '''Return a list of Pool tango devices running locally.'''
    return _getLocalNames( getDeviceNamesByClass( "Pool"))

def getLocalPoolServers():
    '''Return a list of local Pool server names, e.g.: ['Pool/haspp02ch2']'''
    lst = _db.get_server_list("Pool*")
    hostName = getHostname()
    argout = []
    for srv in lst:
        a = _db.get_server_info( srv)
        if a.host.split('.')[0] == hostName:
            argout.append(srv)
    return argout

def getMgAliases():
    '''Return the list of MeasurementGroup aliases, e.g. ['mg_haso107klx'] '''
    lst = getDeviceNamesByClass( "MeasurementGroup")
    if not lst:
        return None
    argout = []
    for elm in lst:
        argout.append( _db.get_alias( elm))
    return argout

def getMgElements( mgName):
    ''' Return the list of elements (aka devices) belonging to an Mg'''
    try:
        p = _PyTango.DeviceProxy( mgName)
    except: 
        print( "TgUtils.getMgElements: proxy to %s failed" % mgName)
        return None
    return list(p.ElementList)

def getLocalMgNames():
    '''Return the list of MeasurementGroup device names running locally.'''
    return _getLocalNames( getDeviceNamesByClass( "MeasurementGroup"))

def getLocalMgAliases():
    '''Return the list of MeasurementGroup aliases running locally.'''
    lst = _getLocalNames( getDeviceNamesByClass( "MeasurementGroup"))
    if not lst:
        return None
    argout = []
    for elm in lst:
        argout.append( _db.get_alias( elm))
    return argout


def getActiveMntGrpStatus():
    '''
    Returns a list of strings containing the status info of the
    ActiveMntGrp and their elements. If this list is not empty, 
    it contains strings describing the problems.
    To be called, if checkActiveMntGrpStatus() returns False
    '''
    activeMntGrp = getEnv( "ActiveMntGrp")
    argout = []
    if activeMntGrp is None:
        argout.append( "no ActiveMntGrp")
        return argout
    try:
        p = _PyTango.DeviceProxy( activeMntGrp)
    except Exception as e:
        argout.append( "failed to create proxy to %s" %activeMntGrp)
        return argout

    if p.state() == _PyTango.DevState.FAULT:
        argout.append( "%s is in FAULT state" % activeMntGrp )

    if p.state() == _PyTango.DevState.ALARM:
        argout.append( "%s is in ALARM state" % activeMntGrp )
        
    lst = getMgElements( activeMntGrp)
    for elm in lst:
        try:
            p = _PyTango.DeviceProxy( elm)
        except Exception as e:
            argout.append( "failed to create proxy to %s" % elm)
            continue
        if p.state() == _PyTango.DevState.FAULT:
            argout.append( "%s is in FAULT state" % elm)
            continue
        if p.state() == _PyTango.DevState.ALARM:
            argout.append( "%s is in ALARM state" % elm)
            continue
        #
        # no point in looking at 
        #  - Counts or Value because if the server is off, hasattr( p, "Counts") returns False
        #  - TangoDevice because there are controller devices without TangoDevice, e.g. h, k, l

    return argout

def checkActiveMntGrpStatus():
    '''
    calls getActiveMntGrpStatus() which returns a list.
    returns True, if this list is empty, meaning no bad messages
    '''
    lst = getActiveMntGrpStatus()
    if len( lst) == 0:
        return True
    else:
        return False


def devState2String( state): 
    '''
    PyTango.DevState.ALARM -> "ALARM"
    '''
    if state == _PyTango.DevState.ALARM: 
        argout = "ALARM"
    elif state == _PyTango.DevState.CLOSE: 
        argout = "CLOSE"
    elif state == _PyTango.DevState.DISABLE: 
        argout = "DISABLE"
    elif state == _PyTango.DevState.EXTRACT: 
        argout = "EXTRACT"
    elif state == _PyTango.DevState.FAULT: 
        argout = "FAULT"
    elif state == _PyTango.DevState.INIT: 
        argout = "INIT"
    elif state == _PyTango.DevState.INSERT: 
        argout = "INSERT"
    elif state == _PyTango.DevState.MOVING: 
        argout = "MOVING"
    elif state == _PyTango.DevState.OFF: 
        argout = "OFF"
    elif state == _PyTango.DevState.ON: 
        argout = "ON"
    elif state == _PyTango.DevState.OPEN: 
        argout = "OPEN"
    elif state == _PyTango.DevState.RUNNING: 
        argout = "RUNNING"
    elif state == _PyTango.DevState.STANDBY: 
        argout = "STANDBY"
    elif state == _PyTango.DevState.UNKNOWN: 
        argout = "UNKNOWN"
    else:
        argout = "REALLY_UNKNOWN"
    return argout

def returnActiveMntGrpStatus():
    '''
    calls getActiveMntGrpStatus() which returns a list.
    returns True, if this list is empty, meaning no bad messages
    '''
    activeMntGrp = getEnv( "ActiveMntGrp")
    argout = []
    if activeMntGrp is None:
        argout.append( "no ActiveMntGrp")
        return argout
    try:
        p = _PyTango.DeviceProxy( activeMntGrp)
    except Exception as e:
        argout.append( "failed to create proxy to %s" %activeMntGrp)
        return argout

    argout.append( "%s is in %s state" % (activeMntGrp, devState2String( p.state())) )
        
    lst = getMgElements( activeMntGrp)
    for elm in lst:
        try:
            p = _PyTango.DeviceProxy( elm)
        except Exception as e:
            argout.append( "failed to create proxy to %s" % elm)
            continue
        argout.append( "%s is in %s state" % (elm, devState2String( p.state())))

    return argout
    
def getTimerAliases():
    '''Return the list of Timer aliases'''
    lst = getDeviceNamesByClass( "CTExpChannel")
    if not lst:
        return None
    argout = []
    for elm in lst:
        if elm.find( 'dgg2') == -1:
            continue
        argout.append( _db.get_alias( elm))
    return argout

def getCounterAliases():
    '''Return the list of Counter aliases'''
    lst = getDeviceNamesByClass( "CTExpChannel")
    if not lst:
        return None
    argout = []
    for elm in lst:
        if elm.find( 'sis3820') == -1:
            continue
        argout.append( _db.get_alias( elm))
    return argout

def getVfcAdcAliases():
    '''Return the list of Counter aliases'''
    lst = getDeviceNamesByClass( "CTExpChannel")
    if not lst:
        return None
    argout = []
    for elm in lst:
        if elm.find( 'vfcadc') == -1:
            continue
        argout.append( _db.get_alias( elm))
    return argout

def getAdcAliases():
    '''Return the list of ADC aliases'''
    lst = getDeviceNamesByClass( "ZeroDExpChannel")
    if not lst:
        return None
    argout = []
    for elm in lst:
        if elm.find( 'tip830') == -1:
            continue
        argout.append( _db.get_alias( elm))
    return argout

def getMcaAliases():
    '''Return the list of Counter aliases'''
    lst = getDeviceNamesByClass( "OneDExpChannel")
    if not lst:
        return None
    argout = []
    for elm in lst:
        if elm.find( 'mca8701') == -1:
            continue
        argout.append( _db.get_alias( elm))
    return argout

def getStarterHostByDevice( device): 
    '''
    return the starter host for a device
    
    HasyUtils.getStarterHostByDevice( "p99/motor/eh.01")
    HasyUtils.getStarterHostByDevice( "haspp99:10000/p99/motor/eh.01")

    '''

    try: 
        p = _PyTango.DeviceProxy( device)
    except Exception as e: 
        print( "TgUtils.getStarterHostByDevice: failed to create proxy %s" % device)
        print( "%s" % repr( e))
        return None

    return p.info().server_host

def getPoolMotors( poolName):
    ''' 
    Input:  poolName, e.g. p15/pool/haspp15

    Output: a list of full device names of pool motors, e.g.
            ['haspp67:10000/motor/omsvme58_exp/48',...]  
    '''

    try: 
        p = _PyTango.DeviceProxy( poolName)
    except:
        print( "TgUtils.getPoolMotors: failed to connect to poolName")
        return None

    lst = []
    for elm in p.MotorList:
        hsh = _json.loads( elm)
        #
        # haso107d1:10000/motor/omsvme58_d1/48"
        #
        lst.append( hsh['full_name'])

    return lst

def findPoolForMg( mgName):
    '''Return the Pool device name containing mgName.'''
    poolList = getPoolNames()
    for pool in poolList:
        try:
            proxy = _PyTango.DeviceProxy( pool)
        except: 
            continue
        mgList = proxy.MeasurementGroupList
        if not mgList:
            continue
        for elm in mgList:
            dct = _json.loads( elm)
            if mgName == dct['name']:
                return proxy.name()
    return None

def isDevice( devName):
    '''
    returns True, if the device exists 

    Code: 
      try: 
          _PyTango.DeviceProxy( devName)
          return True
      except:
          return False
    '''
    try: 
        _PyTango.DeviceProxy( devName)
        return True
    except:
        return False


def getLocalNXSelectorNames():
    '''Return the list of NXSelector device names running locally.'''
    return _getLocalNames( getDeviceNamesByClass( "NXSRecSelector"))

def getOnlineXML( xmlFile = None, cliTags = None):
    '''
    Read /online_dir/online.xml or a file of that syntax 
    and return a list of dictionaries representing the devices

    cliTags, e.g.: ['user,expert'], is a string like "standard,pilatus" most likely provided on the command line. 
    If supplied, devices have to have tags that match
    '''
    #
    #[..., {
    # {'channel': '72',
    #  'control': 'tango',
    #  'controller': 'oms58_d1',
    #  'device': 'p09/motor/d1.72',
    #  'hostname': 'haso107d1:10000',
    #  'module': 'oms58',
    #  'name': 'd1_mot72',
    #  'rootdevicename': 'p09/motor/d1',
    #  'tags': 'expert,user',
    #  'type': 'stepping_motor'}]
    #
    global devListGlobal

    from lxml import etree

    xmlFileLocal = '/online_dir/online.xml'    
    if xmlFile:
        xmlFileLocal = xmlFile

    if not _os.path.exists( xmlFileLocal):
        return None

    parser = etree.XMLParser( ns_clean=True, remove_comments=True)
    try:
        tree = etree.parse( xmlFileLocal, parser)
    except Exception as e:
        print( "---")
        print( "TgUtils.getOnlineXML: error parsing %s" % xmlFileLocal)
        print( _sys.exc_info()[0])
        print( e)
        print( "---")
        return None

    if cliTags:
        #
        # fix this error: tag-mismatch eh_mot01, rexs,core vs. ['core,rexs']
        #
        if type( cliTags) is list: 
            if len( cliTags) == 1: 
                lstCliTags = cliTags[0].split( ',')
            else: 
                lstCliTags = cliTags
        else: 
            lstCliTags = cliTags.split( ',')
        lstCliTags = [ elm.strip() for elm in lstCliTags]
    else:
        lstCliTags = None

    if lstCliTags is not None: 
        print( "TgUtils.getOnline.XML: keep devices and MGs only, if they match these CLI tags %s" % repr( lstCliTags))

    root = tree.getroot()
    devListGlobal = []
    for dev in root:
        hsh = {}
        for elm in dev:
            #
            # not so clear whether lower() is needed
            #
            try:
                if elm.tag == "pseudomotor":
                    hsh[ elm.tag] = elm.text
                else:
                    hsh[ elm.tag] = elm.text.lower()
            except Exception as e:
                print( "---")
                print( "TgUtils.getOnlineXML: error processing %s in %s" % (repr( elm), repr( hsh)))
                print( _sys.exc_info()[0])
                print( e)
                print( "---")
                return None
        
        #
        # if no cliTags are supplied, select the device
        #
        if lstCliTags is None:
            devListGlobal.append( hsh)        
        else:
            #
            # if the device has no tags field, ignore it
            #
            if "tags" not in hsh:
                continue
            devTags = hsh[ 'tags'].split( ',')
            #
            # if at least one device-tag matches a cli-tag keep it
            #
            flagKeep = False
            for cliTag in lstCliTags:
                for devTag in devTags:
                    if cliTag.strip().lower() == devTag.strip().lower():
                        flagKeep = True
            if flagKeep:
                devListGlobal.append( hsh)        
                #print( "TgUtils.getOnlineXML: tag-match    %s, %s vs. %s" % (hsh['name'], hsh[ 'tags'], str( lstCliTags)))
            else:
                #print( "TgUtils.getOnlineXML: tag-mismatch %s, %s vs. %s" % (hsh['name'], hsh[ 'tags'], str( lstCliTags)))
                pass
        #print( "TgUtils.getOnlineXML: %s" % (repr( hsh)))

    #print( "TgUtils.getOnlineXML: %s" % (repr( devList)))
    return devListGlobal
# 
# for GQE.updateArrowCurrent() 
# 
def getProxy( name): 
    """
    returns the proxy from devListGlobal or creates a new proxy
    used from 
      $HOME/gitlabDESY/pySpectra/PySpectra/GQE.py
      updateArrowCurrent()
    """
    global devListGlobal

    argout = None
    
    if devListGlobal is None: 
        devListGlobal = []

    flag = False
    for hsh in devListGlobal: 
        if name == hsh[ 'name']: 
            flag = True
            if 'proxy' in hsh: 
                argout = hsh[ 'proxy']
            else: 
                try: 
                    proxy = _PyTango.DeviceProxy( name)
                    hsh[ 'proxy'] = proxy
                except Exception as e: 
                    devName = "%s/%s" %  (hsh[ 'hostname'], hsh[ 'device'])
                    try: 
                        proxy = _PyTango.DeviceProxy( name)
                        hsh[ 'proxy'] = proxy
                    except Exception as e: 
                        print( "TgUtils.getProxy: failed with %s" % repr( e))
                        argout = None
                        break
    if not flag:
        hsh = {}
        try: 
            proxy = _PyTango.DeviceProxy( name)
            hsh[ 'name'] = name
            hsh[ 'proxy'] = proxy
            devListGlobal.append( hsh)
            argout = hsh[ 'proxy']
        except Exception as e: 
            print( "TgUtils.getProxy: caught %s" % repr( e))
            _sys.exit( 255)

    return argout
#
# Door-MacroServer-Pool
#
class DMSP:
    '''
    Class to access the pool and macroserver being behind a Door 

    the door can be fully qualified, like haspp99:10000/p99/door/haspp99.01

    Members: 
      getEnv( varName)      
      setEnv( varName, varValue)      
      unsetEnv( varName) 

    '''
    def __init__( self, doorname = None):

        if not doorname:
            _PyTango.Except.throw_exception( "n.n.",
                                            "no doorname supplied",
                                            "TgUtils.DMSP") 
        #
        # find TANGO_HOST
        # ['haspp99:10000', 'p99', 'door', 'haspp99.01']
        # ['p99', 'door', 'haspp99.01']
        #
        lst = doorname.split( '/')
        host = None
        if len( lst) == 4: 
            try: 
                lst1 = lst[0].split( ':')
                (host, port) = lst[0].split( ':')
                self.db = _PyTango.Database( host, int( port))
                # p99/door/haspp99.01
                doornameDB = '/'.join( lst[1:])
            except Exception as e: 
                raise Exception( "TgUtils.DMSP.__init__", "Failed to access Tango DB on %s, exception %s " % 
                                 (repr( lst[0]), repr( e)))
        else: 
            self.db = _db
            doornameDB = doorname

        try:
            self.door = _PyTango.DeviceProxy( doorname)
        except _PyTango.DevFailed as e:
            _PyTango.Except.re_throw_exception( e, 
                                               "from DeviceProxy",
                                               "failed to create proxy to door %s " % doorname,
                                               "TgUtils.DMSP") 
        dct = self.db.get_device_property( doornameDB, ["MacroServerName"])
        macroservername = dct['MacroServerName'][0]
        if host is not None: 
            macroservername = "%s:10000/%s" % ( host, macroservername)
        try:
            self.macroserver = _PyTango.DeviceProxy( macroservername)
        except _PyTango.DevFailed as e:
            _PyTango.Except.re_throw_exception( e, 
                                               "from DeviceProxy", 
                                               "failed to create proxy to macroserver %s " % macroservername,
                                               "TgUtils.DMSP")

        dct = self.db.get_device_property( macroservername, ["PoolNames"])
        poolnames = dct['PoolNames']
        self.pools = []
        self.poolNames = []
        for poolname in poolnames:
            try:
                pool = _PyTango.DeviceProxy( poolname)
                self.poolNames.append( poolname)
                self.pools.append( pool)
            except _PyTango.DevFailed as e:
                _PyTango.Except.re_throw_exception( e, 
                                                   "from DeviceProxy", 
                                                   "failed to create proxy to pool %s " % poolname,
                                                   "TgUtils.DMSP")

    #
    #
    #
    def getEnv( self, varName):
        '''DMSP: Return  the value of an environment variable.'''
        import pickle as _pickle
        dct = _pickle.loads( self.macroserver.environment[1])['new']
        if varName not in dct:
            return None
        return dct[varName]
    #
    #
    #
    def setEnv( self, varName, varValue):
        '''DMSP: Set an environment variable.'''
        dct = {}
        dct[varName] = varValue
        new_value = _CodecFactory().getCodec('pickle').encode(('', dict( new=dct)))
        try: 
            self.macroserver.write_attribute('Environment', new_value)
        except Exception as e: 
            print( "TgUtils.DMSP.setEnv: failed to set %s to %s \n %s" % (varName, varValue, repr( e)))
            return False
        
        return True
    #
    #
    #
    def unsetEnv( self, varName):
        '''DMSP: Un-set an environment variable.'''
        
        if self.getEnv( varName) is None: 
            print( "TgUtils.DMSP.unsetEnv: failed for find %s" % (varName))
            return False

        arr = []
        arr.append( varName) 
        dct = { 'del': arr} 
        new_value = _CodecFactory().getCodec('pickle').encode(('', dct))
        try: 
            self.macroserver.write_attribute('Environment', new_value)
        except Exception as e: 
            print( "TgUtils.DMSP.unsetEnv: failed for %s %s" % (varName, repr( e)))
            return False

        return True

_print_level = 0

def dct_print( d):
    '''
    Prints a dictionary to stdout, e.g. the configuration of the mgGroup.
    '''
    global _print_level
    if len( list( d.keys())) == 0:
        _print_level = _print_level - 2
        return

    lst = list( d.keys())
    lst.sort()
    
    print( "%s{" % ( " " * _print_level))
    _print_level  = _print_level + 2

    for key in lst:
        if type(d[key]) == dict:
            print( "%su'%s': " % (" " * _print_level, key))
            _print_level  = _print_level + 2
            dct_print(d[key])
            continue
        print( " " * _print_level, )
        if type(key) == str:
            print( "u'%s':" % key,)
        else:
            print( "%s:" % key,)
        if type(d[key]).__name__ == 'str':
            print( "'%s'," % d[key])
        elif type(d[key]).__name__ == 'unicode':
            print( "u'%s'," % d[key])
        elif type(d[key]).__name__ == 'int':
            print( "%s," % d[key])
        elif type(d[key]).__name__ == 'float':
            print( "%s," % d[key])
        elif type(d[key]).__name__ == 'bool':
            print( "%s," % d[key])
        elif type(d[key]).__name__ == 'list':
            print( "%s," % d[key])
        elif type(d[key]).__name__ == 'NoneType':
            print( "u'',")
        else:
            print( "%s," % type(d[key]))
    _print_level = _print_level - 2
    if _print_level > 0:
        print( "%s}," % (" " * _print_level))
    else:
        print( "%s}" % (" " * _print_level))
    _print_level = _print_level - 2

    return 

_print_level2str = 0

def dct_print2str( d):
    '''
    converts a dictionary into a string which is returned
    '''
    global _print_level2str

    argout = ""

    if len( list( d.keys())) == 0:
        _print_level2str = _print_level2str - 2
        return None

    lst = list( d.keys())
    lst.sort()
    
    argout += "%s{\n" % ( " " * _print_level2str)
    _print_level2str  = _print_level2str + 2

    for key in lst:
        if type(d[key]) == dict:
            #
            # taken out to help TngGui.py create a python file
            # that can be executed u'abs': 12 gave problems
            # had to be 'abc': 12
            # also see some lines beow
            #
            #argout +=  "%su'%s': \n" % (" " * _print_level2str, key)
            argout +=  "%s'%s': \n" % (" " * _print_level2str, key)
            _print_level2str  = _print_level2str + 2
            ret = dct_print2str(d[key])
            if ret is not None:
                argout += ret
            continue
        argout += " " * _print_level2str
        if type(key) == str:
            argout +=  "'%s':" % key
        else:
            argout +=  "%s:" % key
        if type(d[key]).__name__ == 'str':
            argout +=  "'%s',\n" % d[key]
        #elif type(d[key]).__name__ == 'unicode':
        #    argout +=  "u'%s',\n" % d[key]
        elif type(d[key]).__name__ == 'unicode':
            argout +=  "'%s',\n" % d[key]
        elif type(d[key]).__name__ == 'int':
            argout += "%s,\n" % d[key]
        elif type(d[key]).__name__ == 'float':
            argout += "%s,\n" % d[key]
        elif type(d[key]).__name__ == 'bool':
            argout += "%s,\n" % d[key]
        elif type(d[key]).__name__ == 'list':
            argout += "%s,\n" % d[key]
        elif type(d[key]).__name__ == 'NoneType':
            argout += "u'',\n"
        else:
            argout += "%s,\n" % type(d[key])
    _print_level2str = _print_level2str - 2
    if _print_level2str > 0:
        argout += "%s},\n" % (" " * _print_level2str)
    else:
        argout += "%s}\n" % (" " * _print_level2str)
    _print_level2str = _print_level2str - 2

    return argout

def prtc(): 
    """
    press return to continue

    returns: sys.stdin.readline()

    In [7]: HasyUtils.prtc()
    Press <return> to continue 

    Out[7]: '\n'

    In [8]: HasyUtils.prtc()
    Press <return> to continue 
    this is a test
    Out[8]: 'this is a test\n'

    """
    print( "Press <return> to continue ",)
    return _sys.stdin.readline()

_initInkey = False
_initInkeyOldTermAttr = None

def _inkeyExitHandler(): 
    global _initInkey
    global _initInkeyOldTermAttr
    import termios as _termios

    if not _initInkey:
        return
    _initInkey = False
    _termios.tcsetattr( _sys.stdin.fileno(), _termios.TCSADRAIN, _initInkeyOldTermAttr)
    return

def inkey( resetTerminal = None):
    '''
    Return the pressed key, nonblocking. Returns -1, if no key was pressed.

    while 1:
        ....
        if HasyUtils.inkey() ==  32:  # space bar
            break

    Use
      HasyUtils.inkey( True) 
    to reset the terminal characteristic explicitly. This has to be
    done in particular, if you use sys.exitfunc = yourExitHandler
    which overrides the inkey() exit handler
    '''
    global _initInkey
    global _initInkeyOldTermAttr
    import atexit as _atexit
    import termios as _termios

    if resetTerminal and _initInkey:
        _initInkey = False
        _termios.tcsetattr( _sys.stdin.fileno(), _termios.TCSADRAIN, _initInkeyOldTermAttr)
        return -1

    #
    # changing the terminal attributes takes quite some time,
    # therefore we cannot change them for every inkey() call
    #
    if not _initInkey:
        _initInkey = True
        _initInkeyOldTermAttr = _termios.tcgetattr( _sys.stdin.fileno())
        new = _termios.tcgetattr( _sys.stdin.fileno())
        new[3] = new[3] & ~_termios.ICANON & ~_termios.ECHO
        #
        # VMIN specifies the minimum number of characters to be read
        #
        new[6] [_termios.VMIN] = 0
        #
        # VTIME specifies how long the driver waits for VMIN characters.
        # the unit of VTIME is 0.1 s. 
        #
        new[6] [_termios.VTIME] = 1
        _termios.tcsetattr( _sys.stdin.fileno(), _termios.TCSADRAIN, new)
        _atexit.register( _inkeyExitHandler)
	    
    key = _sys.stdin.read(1)
    if( len( key) == 0):
        key = -1
    else:
        key = ord( key)

    return key

def createScanName( prefix, scanDir = None):
    '''
      Inputs: 
       - prefix
       - scanDir (optional)
      Output: prefix_00123 (e.g.)
        The default directory (or scanDir) is searched for files
        that match the pattern prefix*. The returned name
        contains a number which is one above the existing. 
    '''
    import re as _re
    import glob as _glob
    oldDir = _os.getcwd()
    if scanDir:
        if not _os.path.isdir( scanDir):
            print( "createScanName: %s is not a directory" % scanDir)
            _os.chdir( oldDir)    
            return None
        _os.chdir( scanDir)
    if type( prefix) is list: 
        if len( prefix) == 1:
            prefix = prefix[0]
        else: 
            print( "createScanName: len( prefix) != 1 %s" % repr( prefix))
            _os.chdir( oldDir)    
            return None
    files = _glob.glob( "%s*" % prefix)
    if scanDir:
        _os.chdir( oldDir)    
    if len(files) == 0:
        return "%s_00001" % prefix
    no = 1
    patt = _re.compile( prefix + r"_(\d+)\.*(.*)")
    for file in sorted(files):
        parts = patt.match( file)
        if not parts:
            continue
        if int( parts.group(1)) > no:
            no = int( parts.group(1))
    argout = "%s_%05d" % (prefix, no + 1)

    if scanDir:
        _os.chdir( scanDir)
    if len( _glob.glob( "%s*" % argout)) > 0:
        print( "createScanName: failed to create a scan name for %s" % prefix)
        _os.chdir( oldDir)    
        return None
    if scanDir:
        _os.chdir( oldDir)    
    return argout

def uptime():
    '''
    return system uptime in seconds as float number
    '''
    with open('/proc/uptime', 'r') as file:
        return float(file.readline().split()[0])

def configMacroServer( cmdList):
    ''' receives a list of commands which are executed
        on a MacroServer via the first door
    '''
    try:
        p = _PyTango.DeviceProxy( getDoorNames()[0])

    except:
        print( "configMacroServer.py: failed to create a proxy to %s" % getDoorNames()[0])
        return 255

    for cmd in cmdList:
        print( "TgUtils.configMS: %s" % cmd)
        try:
            p.runMacro(cmd.split())
        except: 
            print( "TgUtils.configMS: failed to execute %s" % cmd)
        #
        # make sure that the execution of a command has 
        # finished before the next command is invoked.
        #
        while p.state() != _PyTango.DevState.ON:
            _time.sleep(0.01)
    return 0

def setEnvCautious( dctIn):
    '''
    input: dictionay containing environment variables, names and values, 
    they are set, if the variable does not exist so far.
    '''
    ms = getMacroServerProxy()
    if ms is None: 
        return False

    for key in list( dctIn.keys()):
        if getEnv( key) is None: 
            setEnv( key, dctIn[ key])
        else: 
            print( "TgUtils.setEnvCautious: %s exists already: %s, not changed to %s" % (key, getEnv( key), dctIn[key]))

    return True

def setEnvDctObsoleteQuestionMark( dctIn):
    '''
    2.11.2020: remember ther ScanID issue, avoid race conditions 
               when setting the MS environment

    input: dictionary containing environment variables: names and values.

    After this function executed, dctIn will be the MacroServer environment. 
    Keys that are in the current environment, but not in dctIn are deleted 

    an error is thrown if the number of MacroServers is != 1

    the HasyUtils.getEnvDct() returns a Dct that can be modified
    and used by this function

    '''

    ms = getMacroServerProxy()
    if ms is None: 
        return False

    #
    # compare the 2 dictionaries
    #   if the a variable is not in the new dct, it is deleted
    #   with usenv from the MacroServer environment
    #
    dctOld = getEnvDct()
    for k in list( dctOld.keys()): 
        if k not in list( dctIn.keys()):
            print( "TgUtils.setEnvDct() removing %s" % k)
            unsetEnv( k)

    newDct = dict(new=dctIn)
    ms.write_attribute( "Environment", _CodecFactory().getCodec('pickle').encode(('', newDct)))

    return True

def setEnv( key, value):
    '''
    set an environment variable, returns 0, if more than one MS exist
    '''
    #
    # /usr/lib/python2.7/dist-packages/sardana/macroserver/macroserver.py
    #
    # ms.Environement is more a command table 
    # it uses { 'new': {}} and { 'del': []} to 
    # do things
    #

    ms = getMacroServerProxy()
    if ms is None: 
        return 

    dct = {}
    dct[ key] = value
    new_value = _CodecFactory().getCodec('pickle').encode(('', dict( new=dct)))
    try:
        ms.write_attribute('Environment', new_value)
    except Exception as e: 
        print( "TgUtils.setEnv: failed to set %s to %s " % (key, value))
        return False

    return True

def setEnvDct( dct):
    '''
    sets the entire environment to dct
    '''

    ms = getMacroServerProxy()
    if ms is None: 
        return 

    new_value = _CodecFactory().getCodec('pickle').encode(('', dict( new=dct)))
    try:
        ms.write_attribute('Environment', new_value)
    except Exception as e: 
        print( "TgUtils.setEnvDct: failed to set environment to %s " % ( dct_print2str( dct)))
        print( "")
        print( repr( e))
        return False

    return True

def unsetEnv( key):
    '''
    unset set an environment variable, returns 0, if move than one MS exist
    '''

    if getEnv( key) is None: 
        print( "TgUtils.unsetEnv: no variable %s" % key)
        return False

    ms = getMacroServerProxy()
    if ms is None: 
        return 
        
    arr = []
    arr.append( key) 
    dct = { 'del': arr} 
    new_value = _CodecFactory().getCodec('pickle').encode(('', dct))
    try: 
        ms.write_attribute( 'Environment', new_value)
    except Exception as e: 
        print( "TgUtils.unsetEnv: failed to write Environment, %s" % (repr( e)))
        return False

    return True

def getEnv( key):
    '''
    return the value of a macroserver environment variable
    '''
    ms = getMacroServerProxy()
    if ms is None: 
        return None

    try: 
        temp = ms.Environment
    except Exception as e: 
        print("TgUtils.getEnv: failed for %s" % repr( key))
        print("TgUtils.getEnv: %s" % repr( e))
        #for err in e.args:
        #    print( " reason %s" % err.reason)
        #    print( " desc %s " % err.desc)
        #    print( " origin %s " % err.origin)
        #    print( " severity %s " % err.severity)
        print("TgUtils.getEnv: MacroServer probably offline")
        return None
    #
    # ms.Environment (after decode): 
    #   ('', {'new': {'LogMacro': True, 
    #                 'ScanInfo': {'serialno': 6346, 'intervals': 20, 
    #                              'motors': [{'start': 0.0, 'stop': 1.0, 'name': 'exp_dmy01'}], 
    #                              'title': 'ascan exp_dmy01 0.0 1.0 20 0.1', 'sampleTime': 0.1}, 
    #                 ...
    #
    #dct = _CodecFactory().getCodec('pickle').decode(ms.Environment)[1]['new']
    try: 
        dct = _CodecFactory().getCodec('pickle').decode(temp)[1]['new']
    except Exception as e: 
        print( "TgUtils.getEnv: failed to decode the MS environment, mayby python2 - python3 issue")
        print( repr( e))
        return None
    if key not in dct:
        return None
    return dct[ key]

def storeEnv( dirName = None):
    '''
    Store the MacroServer environment in dirName
    Default dirName: ScanDir
    Full file name: ScanDir/ScanFilePrefix_ScanID.env
      ScanFilePrefix is extracted from ScanFile

    returns None, if
      - there is no MacroServer
      - there is more than 1 MacroServer
      - dirName does not exist
      - the full file name exists already

    otherwise returns full file name
    '''
    import pprint

    ms = getMacroServerProxy()
    if ms is None: 
        return 

    dct = _CodecFactory().getCodec('pickle').decode(ms.Environment)[1]['new']

    if dirName is None:
        dirName = dct[ 'ScanDir']

    scanID = dct[ 'ScanID']
    scanFile = dct[ 'ScanFile']
    if type( scanFile) == list:
        prefix = scanFile[0].split('.')[0]
    else:
        prefix = scanFile.split('.')[0]
    pathName = "%s/%s_%05d.env" % (dirName, prefix, int(scanID))
    
    if not _os.path.exists( dirName):
        print( "HasyUtils.storeEnv: %s does not exist" % dirName)
        return None
    
    if _os.path.exists( pathName):
        print( "HasyUtils.storeEnv: %s exists already" % pathName)
        return None

    envFile = open( pathName, 'w')
    pp = pprint.PrettyPrinter( indent = 4, stream=envFile)
    pp.pprint( dct)
    envFile.close()

    if _os.isatty(1):
        print( "HasyUtils.storeEnv: created %s" %pathName)

    return pathName

def getEnvVarAsDct( key):
    '''
    return the value of a macroserver environment variable as a dictionary.

    Use case: _GeneraHooks

    p99/door/haspp99.01 [17]: lsgh
      Hook place        Hook(s)
    ------------ --------------
       post-scan   gh_post_scan
       pre-scan    gh_pre_scan

    return: {'post-scan': ['gh_post_scan'], 'pre-scan': ['gh_pre_scan']}


    In [8]: ret = HasyUtils.getEnv( "_GeneralHooks")

    In [9]: ret
    Out[9]: 
    [('gh_post_scan', ['post-scan']),
     ('gh_post_step', ['post-step']),
     ('gh_post_acq', ['post-acq']),
     ('gh_post_move', ['post-move']),
     ('gh_pre_scan', ['pre-scan']),
     ('gh_pre_acq', ['pre-acq']),
     ('gh_pre_move', ['pre-move'])]

    In [10]: hsh = HasyUtils.getEnvVarAsDct( "_GeneralHooks")

    In [11]: hsh
    Out[11]: 
    {'post-acq': ['gh_post_acq'],
     'post-move': ['gh_post_move'],
     'post-scan': ['gh_post_scan'],
     'post-step': ['gh_post_step'],
     'pre-acq': ['gh_pre_acq'],
     'pre-move': ['gh_pre_move'],
     'pre-scan': ['gh_pre_scan']}

    '''

    ms = getMacroServerProxy()
    if ms is None: 
        return 
    dct = _CodecFactory().getCodec('pickle').decode(ms.Environment)[1]['new']
    if key not in dct:
        return None

    hsh = {}
    for elm in dct[ key]:
        k = elm[1][0]
        v = elm[0]
        if k not in hsh:
            hsh[k] = []
        #
        # avoid double entries
        #
        if not v in hsh[k]:
            hsh[k].append( v)
    
    return hsh

def getEnvDct():
    '''
    return the macroserver environment as a dictionary
    '''

    ms = getMacroServerProxy()
    if ms is None: 
        return 
        
    try: 
        dct = _CodecFactory().getCodec('pickle').decode( ms.Environment)[1]['new']
    except: 
        #
        # SardanaAIO is executed
        #
        dct = None

    return dct
#
#
#
class sockel( object):
    ''' 
    A socket server interface which has been created to handle connects
    from Sardana macros to the SardanaMonitor and the message window.
    The constructor checks for available ports in the range [port, port + 9]
                
    Server:
    ------

    def main(): 
       thread.start_new_thread( socketAcceptor, ())      

    def socketAcceptor():
        # waits for new accepts on the original socket, 
        # receives the newly created socket and 
        # creates a thread for the socketServer
        while True:
            s = TgUtils.sockel( TgUtils.getHostname(), PORT)
            thread.start_new_thread( socketServer, (s, ))      

    def socketServer(s):
        global msgBuf
        while True:
            msg = s.recv().strip()
            if msg is None:
                print( "received None, closing socket")
                s.close()
                break
            msgBuf.append( msg)
            s.send( "done")
    '''
    #
    # one socket for the port, accept() generates new sockets
    #
    sckt = None
    conCounter = 0

    def __init__( self, host, port):
        if sockel.sckt is None:
            try:
                sockel.sckt = _socket.socket(_socket.AF_INET, _socket.SOCK_STREAM)
            except Exception as e:
                print( "socket() failed %s" % repr( e))
                _sys.exit()

            for i in range(10):
                port += i
                try:
                    sockel.sckt.bind((host, port))
                except Exception as e:
                    print( "TgUtils.sockel: bind() failed %s,trying next port" % repr( e))
                    continue
                self.port = port
                print( "bind( %s, %d) ok" % (host, port))
                sockel.sckt.listen(5)
                break
            else:
                print( "bind() failed")
                _sys.exit()
        self.conn, addr = sockel.sckt.accept()
        self.addr = addr
        self.connNo = sockel.conCounter
        sockel.conCounter += 1

    def close( self):
        #
        # close the 'accepted' socket only, not the main socket
        # because it may still be in use by another client
        #
        if not self.conn is None:
            self.conn.close()

    def recv( self):
        argout = None
        try:
            argout = self.conn.recv(1024)
        except:
            argout = None
        return argout

    def send( self, msg):
        if self.conn is None:
            return 0
        argout = 0
        try:
            argout = self.conn.send( msg)
        except: 
            self.conn = None
            argout = 0
        return argout

def walkLevel( some_dir, level=1):
    '''
    An extension of _os.walk() allowing the specification of a search depth
    
    Usage: 

      RootDir = '/home/someUser'
      for rootDir, subDirs, files in TgUtils.walkLevel( RootDir, level=0):
          print( "the directory %s" % rootDir )
          print( "contains these files %s" % str( files))
          print( "and these sub-dirs %s" % str( subDirs))
    '''
    some_dir = some_dir.rstrip(_os.path.sep)
    if not _os.path.isdir(some_dir):
        print( "walkLevel %s not a directory" % some_dir)
            
    num_sep = some_dir.count(_os.path.sep)
    for root, dirs, files in _os.walk(some_dir):
        yield root, dirs, files
        num_sep_this = root.count(_os.path.sep)
        if num_sep + level <= num_sep_this:
            del dirs[:]

#
#
# 
def putDeviceProperty( devName, propName, props, tangoHost = None):
    '''
    devName:  'p17/macroserver/haspp17.01'
    propName: 'MacroPath'
    props:    <str> or seq<str>    
    tangoHost e.g.: "haspp99:10000"
    '''
    
    db = _findDB( tangoHost)
    if not db:
        return None

    try:
        db.put_device_property( devName, { propName : props}) 
    except _PyTango.DevFailed as e:
        _PyTango.Except.print_exception( e)
        print( "TgUtils.putDeviceProperty: %s %s" % (propName, props))
        return False
    return True
#
#
# 
def deleteDeviceProperty( devName, propName, tangoHost = None):
    '''
    devName:  'p17/macroserver/haspp17.01'
    propName: 'BadPropName'
    tangoHost: 'haspp99:10000'
    '''
    
    db = _findDB( tangoHost)
    if not db:
        return None

    try:
        db.delete_device_property( devName, [ propName]) 
    except _PyTango.DevFailed as e:
        _PyTango.Except.print_exception( e)
        print( "TgUtils.deleteDeviceProperty: %s %s" % (propName, props))
        return False
    return True
#
#
# 
def getDeviceProperty( devName, propName, tangoHost = None):
    '''
    return a list containing property values
      devName:  'p17/macroserver/haspp17.01'
      propName: 'MacroPath'
    tangoHost e.g.: "haspp99:10000"

    _db = _PyTango.Database()

    '''
    
    db = _findDB( tangoHost)
    if not db:
        return None

    #
    # haso107d10:10000/p09/motor/eh.6 -> p09/motor/eh.6
    #
    temp = devName.find( ':')
    if temp > 0:
        devName = devName[temp+7:]

    try:
        dct = db.get_device_property( devName, [ propName])
    except _PyTango.DevFailed as e:
        _PyTango.Except.print_exception( e)
        print( "TgUtils.getDeviceProperty: %s " % (propName))
        return False
    return list(dct[ propName])

def putServerInfo( name = None, host = None, mode = 1, level = None):
    '''
    add/update server information in the database
    '''
    serverInfo = _PyTango.DbServerInfo()
    serverInfo.name = name
    serverInfo.host = host
    serverInfo.level = level
    serverInfo.mode = mode
    _db.put_server_info( serverInfo)
    return True

def restartServer( serverName, tangoHost = None):
    '''
    stop server, then start server, e.g. MacroServer/haspp17
    tangoHost e.g.: "haspp99:10000"
    '''

    if not stopServer( serverName, tangoHost):
        print( "TgUtils.restartServer: failed to stopServer %s " % serverName)
        return False

    if not startServer( serverName, tangoHost):
        print( "TgUtils.restartServer: failed to startServer %s" % serverName)
        return False

    return True
        
def startServer( serverName, tangoHost = None):
    '''
    startServer( "DGG2/Clone")
    startServer( "DGG2/Clone", "haspp99:10000")
    '''
    starter = getStarterDevice( serverName, tangoHost)
    try:
        starterProxy = _PyTango.DeviceProxy( starter)
        starterProxy.command_inout( "UpdateServersInfo")
    except:
        print( "failed to create proxy to starter, server %s, tangoHost %s" % (serverName, tangoHost))
        _sys.exit( 255)

    starterProxy.DevStart( serverName)
        
    waitTime = 40  
    print( "Waiting for %s to start, max %ds " % (serverName, waitTime))
    while waitTime > 0:
        _time.sleep(0.5)
        waitTime -= 0.5
        lst = starterProxy.command_inout("DevGetRunningServers", True)
        if serverName in lst:
            break
        _sys.stdout.write( '.')
        _sys.stdout.flush()
    else:
        print( "TgUtils.startServer: %s did not start" % serverName)
        return False
        
    print( "\n%s started (wait-time left %g)" % (serverName, waitTime))
    return True

def _process_exists(srvName):
    #
    # MacroServer/haspp09 -> MacroServer, haspp09
    #
    tsName, instance = srvName.split("/")
    #
    # temp: "MacroServer haspp09"
    #
    temp = "%s %s" % (tsName, instance)
    prc= _os.popen('ps ax | grep %s' % tsName)
    inp = prc.read()
    prc.close()
    lst = inp.split('\n')
    for line in lst:
        if line.find( temp) > 0:
            return True
    return False

def _serverReallyStopped( proxy, serverName):
    '''
    use 'ps -ax' to see, if a server is really stopped
    '''
    #
    # if the server runs on another host, assume it is stopped
    #
    if getHostnameLong() != proxy.info().server_host:
        print( "TgUtils._serverReallyStopped: local host %s, starterHost %s " % \
            (getHostnameLong(), proxy.info().server_host))
        return True

    if _process_exists( serverName):
        print( "TgUtils.stopServer: hardkill(1) %s" % serverName)
        proxy.command_inout("HardKillServer", serverName)            
        count = 0
        while count < 10:
            if _process_exists( serverName):
                _time.sleep(0.2)
                print( "TgUtils._serverReallyStopped: %s still in 'ps -ax'" % serverName)
                count += 1
            else:
                #print( "TgUtils._serverReallyStopped: %s not in 'ps -ax'" % serverName)
                return True
    else:
        #print( "TgUtils._serverReallyStopped: %s not in 'ps -ax'" % serverName)
        return True


def isAlive( ipAddress, portNo): 
    """
    returns True, if we can connect to ipAddress:portNo
    e.g.: HasyUtils.isAlive( "192.168.254.999", 5001)

    """
  
    sock = _socket.socket( _socket.AF_INET, _socket.SOCK_STREAM)

    server_address = ( ipAddress, int( portNo))
    sock.settimeout( 3)
    try: 
        sock.connect(server_address)
    except Exception as e: 
        print( "TgUtils.isAlive: failed to connect to %s, %s " % ( ipAddress, portNo))
        return False

    sock.close()
    return True

def killServer( serverName): 
    '''
    send signal 9 to server and bash script, if necessary

    9046 ?        S      0:00 /bin/bash /usr/lib/tango/server/MacroServer haso107tk
    9047 ?        Sl     0:21 /usr/bin/python2 /usr/bin/MacroServer haso107tk

    serverName: MacroServer/haso107tk 

    '''
    import signal

    tsName, instance = serverName.split("/")
    temp = "%s %s" % (tsName, instance)
    prc = _os.popen('ps ax | grep %s | grep %s' % (tsName, instance))
    lines = prc.read()
    prc.close()
    flag = False
    for line in lines.split( '\n'): 
        line = line.strip()
        if len( line) == 0:
            continue
        if line.find( 'grep') != -1:
            continue
        lst = line.strip().split()
        print( "%s" % line)
        print( "kill -9 %s" % lst[0])
        _os.kill( int( lst[0]), signal.SIGKILL) 
        flag = True

    if flag is False: 
        print( "TgUtils.killServer: %s does not exist" % serverName)
        return True

    _time.sleep(1) 

    prc = _os.popen('ps ax | grep %s | grep %s' % (tsName, instance))
    lines = prc.read()
    prc.close()
    flag = False
    for line in lines.split( '\n'): 
        line = line.strip()
        if len( line) == 0:
            continue
        if line.find( 'grep') != -1:
            continue
        print( "TgUtils.killServer: still alive %s" % line)
        flag = True

    return not flag

def stopServer( serverName, tangoHost = None):
    '''
    stops a server via starter or calls killServer()

    stopServer( "DGG2/Clone")
    stopServer( "DGG2/Clone", "haspp99:10000")

    '''
    import signal

    starter = getStarterDevice( serverName, tangoHost)
    try:
        starterProxy = _PyTango.DeviceProxy( starter)
    except:
        print( "TgUtils.stopServer: failed to create proxy to Starter %s, server %s, tangoHost %s" %
               ( starter, serverName, tangoHost))
        return None

    lst = starterProxy.command_inout("DevGetStopServers", True)
    if serverName in lst: 
        if _serverReallyStopped( starterProxy, serverName):
            return True

    try: 
        starterProxy.DevStop( serverName)
    except Exception as e: 
        print( "TgUtils.stopServer: Failed to stop %s" % serverName)
        print( repr( e))
        return False
        
    waitTime = 10
    print( "Waiting for %s to stop, max. %ds " % (serverName, waitTime))
    while waitTime > 0:
        _time.sleep(0.5)
        waitTime -= 0.5
        starterProxy.command_inout("UpdateServersInfo")
        lst = starterProxy.command_inout("DevGetStopServers", True)
        if serverName in lst:
            if _serverReallyStopped( starterProxy, serverName):
                print( "\nTgUtils.stopServer: %s stopped via Starter, remaining time %g " % (serverName, waitTime))
                _time.sleep(2.)
                return True
        _sys.stdout.write( '.')
        _sys.stdout.flush()

    print( "\nTgUtils.stopServer: Starter failed to stop %s, executing 'kill -9'" % serverName)
    if not killServer( serverName):
        print( "TgUtils.stopServer: unable to kill " % serverName)
        return False
    else: 
        print( "TgUtils.stopServer: kill was successful, %s " % serverName)

    #
    # need this wait time. otherwise serverName will still be in RunningServers
    #
    _time.sleep(3)
    starterProxy.command_inout("UpdateServersInfo")
    lst = starterProxy.command_inout("DevGetRunningServers", True)
    if serverName in lst: 
        print( "TgUtils.stopServer: %s still in RunningServers, exiting" % serverName)
        _sys.exit( 255)

    return True

def restartPool( macro = None): 
    """
    fixes the issue, if Ctrl-C is pressed more that 2 times

    restart Pool
    execute refreshDiffractometers()
    sleeps 3 seconds (seems to be necessary)
    returns True, if successful, otherwise calls sys.exit()

    This function is supposed to be used in the pre_scan_hook:

    class gh_pre_scan(Macro):
        ...
        def run( self):
            self.output( "general_features.pre_scan hook")

            buffer = []
            if not HasyUtils.checkECStatus( errorMsgs = buffer):
               self.output( "general_features.pre_scan_hook: %s" % repr( buffer))
                self.output( "general_features.pre_scan_hook: restartingPool") 
                HasyUtils.restartPool( macro = self)
                if not HasyUtils.checkECStatus( errorMsgs = buffer):
                    self.output( "general_features.pre_scan_hook: %s" % repr( buffer))
                    self.output( "general_features.pre_scan_hook: restartingPool failed, restartBoth needed") 
                else: 
                    self.output( "general_features.pre_scan_hook: restartingPool DONE") 
            else: 
                self.output( "general_features.pre_scan_hook: ECStatus is OK")
    ...

    """
    poolList = getLocalPoolServers()

    if macro is not None: 
        macro.output( "TgUtils.restartPool") 

    if len( poolList) == 0:
        print( "TgUtils.restartPool: there is no local Pool")
        _sys.exit(255)

    for srv in poolList:
        if macro is not None: 
            macro.output( "TgUtils.restartPool %s" % srv) 
        if not restartServer( srv):
            print( "TgUtils.restartPool: failed to stop %s" % srv)
            _sys.exit(255)

    if macro is not None: 
        macro.output( "TgUtils.restartPool refreshing Diffs")

    pooltools.refreshDiffractometers()

    if macro is not None: 
        macro.output( "TgUtils.restartPool sleeping 3 s")
    _time.sleep( 3) 

    if macro is not None: 
        macro.output( "TgUtils.restartPool DONE")

    return True

def restartBoth(): 
    """
    stop MacroServer
    restart Pool
    start MacroServer
    execute refreshDiffractometers()
    execute HasyUtils.getEnv( "MacroServerRestartPostScript") 

    returns True, if successful, otherwise calls sys.exit()
    """
    poolList = getLocalPoolServers()

    if len( poolList) == 0:
        print( "TgUtils.restartBoth: there is no local Pool")
        _sys.exit(255)

    msList = getLocalMacroServerServers()

    if len( poolList) == 0:
        print( "TgUtils.restartBoth: there is no local MacroServer")
        _sys.exit(255)

    for srv in msList:
        if not stopServer( srv):
            print( "TgUtils.restartBoth: failed to stop %s" % srv)
            _sys.exit(255)
            
    for srv in poolList:
        if not restartServer( srv):
            print( "TgUtils.restartBoth: failed to stop %s" % srv)
            _sys.exit(255)

    for srv in msList:
        if not startServer( srv):
            print( "failed to stop %s " % srv)
            _sys.exit(255)
    
    pooltools.refreshDiffractometers()

    scriptName = getEnv( "MacroServerRestartPostScript") 
    if scriptName is not None and len( scriptName) > 0: 
        if not _os.path.exists( scriptName): 
            print( "TgUtils.restartBoth, %s does not exist" % scriptName) 
            _sys.exit( 255)
        _os.system( "python3 %s" % scriptName)
    return True

def getStarterDevice( serverName, tangoHost = None):
    '''
    return the starter device for a server, fully qualified
    tangoHost e.g.: "haspp99:10000"
    '''
    
    db = _findDB( tangoHost)
    if not db:
        return None

    try:
        srvInfo = db.get_server_info( serverName)
    except:
        print( "TgUtils.getStarterDevice: failed to get_server_info for %s" % serverName)
        return None

    if len( srvInfo.host.strip()) == 0:
        #
        # there is no host entry, if the server is not controlled by the starter
        #
        return None
    #
    # srvInfo VmExecutor/secop, DbServerInfo(host = 'null', level = 0, mode = 0, name = 'VmExecutor/secop')
    #
    lst = srvInfo.host.split( '.')
    if lst[0] == 'null': 
        argout = None
    else:
        argout = "//%s:10000/tango/admin/%s" % (db.get_db_host(), lst[0])
    return argout


def assertServerRunning( serverName, dbHost = None):
    '''

    use case: 
      to ensure that long measurements consisting of series of individualScans
      are not interrupted a Tango server crashes. 

    what the function does:
      - get a device belonging to serverName
      - create a device proxy and evaluate the state
        + if OK, return True 
        + otherwise
          o wait until the server is no longer in the list of running servers
          o wait until the server appears in the list of stopped servers
          o start the server

    implementation principle

      while True:
         try:
              individualScan()
         except:
              HasyUtils.assertServerRunning( "ServerInvolved/Instance", "haspp99:10000")

    Another example can be found in the Spock manual, section Helpers.
    '''

    devList = getDeviceNamesByServer( serverName, dbHost)
    if len( devList) == 0:
        print( "TgUtils.assertServerRunning: no devices for %s" % serverName)
        return None

    devName = devList[0]
    if not dbHost is None:
        lst = dbHost.split(':')
        if len(lst) == 2:
            devName = "%s/%s" % (dbHost, devName)
        elif len(lst) == 1:
            devName = "%s:10000/%s" % (dbHost, devName)
        else:
            print( "TgUtils.assertServerRunning: something is wrong with dbHost %s" % dbHost)
            return None
    try: 
        p = _PyTango.DeviceProxy( devName)
        sts = p.state()
        return True
    except: 
        pass

    startTime = _time.time()
    while serverIsRunning( serverName, dbHost):
        _time.sleep(0.5)
        if (_time.time() - startTime) > 10.:
            print( "TgUtils.assertServerRunning: %s remains running" % serverName)
            return False

    startTime = _time.time()
    while not serverIsStopped( serverName, dbHost):
        _time.sleep(0.5)
        if (_time.time() - startTime) > 10.:
            print( "TgUtils.assertServerRunning: %s remains running" % serverName)
            return False

    count= 0
    while True:
        try:
            startServer( serverName, dbHost)
            break
        except _PyTango.DevFailed:
            count += 1
            if count == 5:
                return False
            #extype, value = _sys.exc_info()[:2]
            #for err in value:
            #    print( " reason %s" % err.reason)
            #    print( " desc %s " % err.desc)
            #    print( " origin %s " % err.origin)
            #    print( " severity %s " % err.severity)
            #    print( "")
            _time.sleep(0.5)
    return True

def getAttribute( deviceName, attrName):
    '''
    return the attribute of a device
    '''
    try:
        p = _PyTango.DeviceProxy( deviceName)
    except Exception as e:
        print( e)
        print( "TgUtils.getAttribute: failed to create a proxy to %s" % deviceName)
        return None

    return p.read_attribute( attrName).value    

def stopMovePool( motorNamePool):
    '''
    executs the Stop command on the Pool motor
    '''
    try:
        m = _PyTango.DeviceProxy( motorNamePool)
    except Exception as e:
        print( e)
        print( "TgUtils.stopMovePool: failed to create a proxy to %s" % motorNamePool)
        return None
    try:
        m.command_inout("Stop")
    except Exception as e:
        #print( e)
        print( "TgUtils.stopMovePool: failed to execute 'Stop' on %s" % motorNamePool)
        return False
    return True

def stopMoveTS( motorName):
    '''
    executs the StopMove command on a non-Pool Tango server
    '''
    try:
        m = _PyTango.DeviceProxy( motorName)
    except Exception as e:
        #print( e)
        print( "TgUtils.stopMoveTS: failed to create a proxy to %s" % motorName)
        return None
    try:
        m.command_query( "StopMove")
        try:
            m.command_inout("StopMove")
        except Exception as e:
            #print( e)
            print( "TgUtils.stopMoveTS: failed to execute 'StopMove' on %s" % motorName)
            return False
    except Exception as e:
        print( "TgUtils.stopMoveTS: %s has no StopMove" % motorName)
        return False
    return True

def stopAllMoves():
    '''
    send StopMacro to Doors that are not ON and stop all motors (Pools and TS)
    '''
    doorList = getDoorNames()    
    for doorName in doorList:
        try:
            door = _PyTango.DeviceProxy( doorName)
        except Exception as e:
            print( "TgUtils.stopAllMoves: Failed to create a proxy to %s" % doorName)
        if door.state() != _PyTango.DevState.ON:        
            door.StopMacro()        
    #
    # sent Stop to the Pool motors ...
    #
    poolList = getPoolNames()
    for pool in poolList: 
        motorList = getPoolMotors( pool)
        for motorName in motorList:
            stopMovePool( motorName)
    #
    # and to the Tango servers
    #
    motorList = getMotorNames()
    for motorName in motorList:
        stopMoveTS( motorName)

    return True
        
def getDateTime():
    '''
    return: '15 Feb 2016 10:56:57'
    '''
    return _time.strftime("%d %b %Y %H:%M:%S", _time.localtime())
        
def getTime():
    '''
    return: '10:56:57'
    '''
    return _time.strftime("%H:%M:%S", _time.localtime())

def getDoty( dateString = None): 
    '''
    return date-of-the-year as a floating point number
    
    dateString == None
       uses the current time
    dateString != None
       converts a string like: 2016-11-17 11:41:21 to 322.4870486111111
    '''
    import datetime, time, re
    if dateString is None:
       tm = time.localtime()
       dateString = "%4d-%02d-%02d %02d:%02d:%02d" % ( tm.tm_year, tm.tm_mon, tm.tm_mday, 
                                                     tm.tm_hour, tm.tm_min, tm.tm_sec)

    patt = re.compile( r".*(\d{4})-(\d{2})-(\d{2})\s*(\d{2}):(\d{2}):(\d{2})")
    res = patt.match( dateString)
    if res is None:
        print( "TgUtils.getDoty: bad format %s" % dateString)
        return None

    lst = res.groups()
    h, m, s = lst[3], lst[4], lst[5]
    a = datetime.datetime( int( lst[0]), int( lst[1]), int( lst[2]))
    argout = float(a.timetuple().tm_yday) - 1. + (float(h)*3600. + float(m)*60 + float(s))/86400.
    return argout

def printCallStack( depth = None):    
    '''
    print the call stack, default depth is 15
    '''
    if depth is None:
        depth = 15

    for n in range( 0, depth):
        try:
            code = _sys._getframe(n).f_code
            print( "printTraceback: depth: %d function: %s file: %s line: %d" % \
                  (n, code.co_name, code.co_filename, code.co_firstlineno))
        except ValueError:
            print( "printTraceback: stopped at level %d" % n)
            break
    return

def yesno( prompt):
    '''
    Prints the prompt string and tests whether is answer is (y)es, case-insensitive
    '''
    _sys.stdout.write( prompt)
    _sys.stdout.flush()
    answer = _sys.stdin.readline().upper().strip()
    if answer.lower() == 'y' or answer.lower() == 'yes':
        return True
    else:
        return False

def match( name, pattern):
    '''
    return True, if pattern matches name
    - pattern is None matches all names

    Examples: 
    HasyUtils.match( "d1_mot01", "d1_mot01") -> True
    HasyUtils.match( "d1_mot01", "d1")       -> True
    HasyUtils.match( "d1_mot01", "d1_mot1")  -> False
    HasyUtils.match( "d1_mot01", "0")        -> True
    HasyUtils.match( "d1_mot01", "0$")       -> False ($ end-of-string)
    HasyUtils.match( "d1_mot01", "mot")      -> True
    HasyUtils.match( "d1_mot01", "^mot")     -> False (^ begin-of-string)
    '''
    import re as _re
    #
    # if no pattern is specified, return True
    #
    if pattern is None:
        return True

    pattern = pattern.lower()
    name = name.lower()

    matchObj = _re.search( pattern, name)
    if matchObj is None:
        return False

    return True

class TypeNames:
    '''
    This class is a bad hack to fake TypeName in msparameter.py  
    It is used by the macro tester
    ''' 
    def __init__( self):
        for name in ['Acquirable',
                     'Any',
                     'Boolean',
                     'CTExpChannel',
                     'Class',
                     'ComChannel',
                     'Constraint',
                     'Controller',
                     'ControllerClass',
                     'ControllerLibrary',
                     'Countable',
                     'Device',
                     'Door',
                     'Element',
                     'Env',
                     'ExpChannel',
                     'External',
                     'File',
                     'Filename',
                     'Float',
                     'Function',
                     'IORegister',
                     'Instrument',
                     'Integer',
                     'JSON',
                     'Library',
                     'Macro',
                     'MacroClass',
                     'MacroCode',
                     'MacroFunction',
                     'MacroLibrary',
                     'MacroServer',
                     'MacroServerElement',
                     'MacroServerObject',
                     'MeasurementGroup',
                     'Meta',
                     'Motor',
                     'MotorGroup',
                     'MotorParam',
                     'Moveable',
                     'Object',
                     'OneDExpChannel',
                     'ParameterType',
                     'Pool',
                     'PoolElement',
                     'PoolObject',
                     'PseudoCounter',
                     'PseudoMotor',
                     'String',
                     'TangoDevice',
                     'TriggerGate',
                     'TwoDExpChannel',
                     'User',
                     'ZeroDExpChannel']:       
            setattr( self, name, name)
        return

def getListFromFile( fileName):
    '''
    reads fileName, ignores comment lines, ignores empty lines
    and returs a list of lines
    use case: list of hosts
    '''
    try:
        fileHandle = open( fileName, 'r')
    except Exception as e:
        print( "HasyUtils.getListFromFile: Failed to open %s" % fileName)
        print( repr(e))
        return None

    lines = []
    for line in fileHandle:
        line = line.strip()
        if len( line) == 0:
            continue
        if line.find( "#") == 0:
            continue
        lines.append( line)
    fileHandle.close()
    return lines

def getHostListFromFile( fileName): 
    """
    calls getListFromFile()
    """
    return getListFromFile( fileName)

def getTraceBackList(): 
    '''
    returns a list of strings containg traceback information
    '''
    argout = []
    for n in range( 0, 50):
        try:
            code = _sys._getframe(n).f_code
            argout.append( "traceback: depth: %d function: %s file: %s line: %d" % 
                         (n, code.co_name, code.co_filename, code.co_firstlineno))
        except ValueError:
            break
    return argout

class moveLoop( object):
    '''
    - motorX, motorY, can be Tango or Pool device names
    - the inner motor executes sweeps between startX and stopX, in units. 
    - timeSweep, the sweep time of the inner motor. The slew rate is adjusted.
    - the outer motor moves from startY to stopY by delta
    '''
    def __init__( self, motorX, startX, stopX, timeSweep, 
                  motorY, startY, stopY, deltaY):

        if motorX == motorY:
            print( "moveLoop.__init__: both motors are identical %s, %s" % ( motorX, motorY))
            _sys.exit(255)

        self.findProxiesAndTangoHost( motorX, motorY)
        self.assertSameCard()
        #
        # install CtrlC handler after the proxies have been created
        #
        _signal.signal(_signal.SIGINT, self.handleCtrlC)
        #
        # stop moves, just to be sure
        #
        self.stopMoves()

        self.startX = startX
        self.stopX  = stopX
        self.startY = startY
        self.stopY  = stopY
        self.deltaY = deltaY
        if self.stopY < self.startY:
            self.deltaY = -abs( self.deltaY)
        else:
            self.deltaY = abs( self.deltaY)
        
        self.timeSweep = timeSweep

        self.makeSomeChecks()

        self.slewRateX = self.proxyX.SlewRate

        self.stepsXStart = (self.startX - self.proxyX.unitcalibration)*self.proxyX.conversion
        self.stepsXStop = (self.stopX - self.proxyX.unitcalibration)*self.proxyX.conversion

        stepsXDelta = self.stepsXStop - self.stepsXStart
        timeMove = abs(float(stepsXDelta)/float(self.proxyX.SlewRate))
        if self.timeSweep < timeMove:
            print( "Requested sweep time too short %g, less than the move time %g" % ( self.timeSweep, timeMove))
            print( "  Possible action: increase the sweep time or increase the slew rate")
            _sys.exit( 255)

        self.slewRateXSweep = float( self.slewRateX)*timeMove/self.timeSweep
        
        print( "TgUtils.moveLoop: timeMove %g, self.timeSweep %g, slewRate %g, slewRateSweeep %d" % \
            (timeMove, self.timeSweep, self.slewRateX, self.slewRateXSweep))

        if self.slewRateXSweep < self.proxyX.BaseRate:
            print( "Requested slew rate %d is less than base rate %d" % \
                (self.slewRateXSweep, self.proxyX.BaseRate))
            _sys.exit()

        self.stepsYDelta = self.deltaY*self.proxyY.conversion

        self.nLoop = abs(int((self.stopY - self.startY)/self.deltaY))
        self.commasX = ','*self.channelX
        self.commasY = ','*self.channelY

        self.paused = False

    def makeSomeChecks( self):
        '''
        make sure the input is OK
        '''
        if self.startX is None: 
            raise Exception( "TgUtils.moveLoop:",  "startX is None")
        if self.stopX is None: 
            raise Exception( "TgUtils.moveLoop:", "stopX is None")

        if self.startY is None: 
            raise Exception( "TgUtils.moveLoop:", "startY is None")
        if self.stopY is None: 
            raise Exception( "TgUtils.moveLoop:", "stopY is None")

        if self.timeSweep <= 0.: 
            raise Exception( "TgUtils.moveLoop:", "timeSweep <= 0 (%g)" % self.timeSweep)

        try:
            if self.proxyX.UnitLimitMin > self.startX or  \
               self.proxyX.UnitLimitMax < self.startX:
                print( "checkLimits: %s startX %g outside limits [%g, %g]" % \
                    (self.motorX, self.startX, 
                     self.proxyX.UnitLimitMin, self.proxyX.UnitLimitMax))
                _sys.exit( 255)
            if self.proxyX.UnitLimitMin > self.stopX or  \
               self.proxyX.UnitLimitMax < self.stopX:
                print( "checkLimits: %s stopX %g outside limits [%g, %g]" % \
                    (self.motorX, self.stopX, 
                     self.proxyX.UnitLimitMin, self.proxyX.UnitLimitMax))
                _sys.exit( 255)

            if self.proxyY.UnitLimitMin > self.startY or \
               self.proxyY.UnitLimitMax < self.startY:
                print( "checkLimits: %s startY %g outside limits [%g, %g]" % \
                    (self.motorY, self.startY, 
                     self.proxyY.UnitLimitMin, self.proxyY.UnitLimitMax))
                _sys.exit( 255)
            if self.proxyY.UnitLimitMin > self.stopY or  \
               self.proxyY.UnitLimitMax < self.stopY:
                print( "checkLimits: %s stopY %g outside limits [%g, %g]" % \
                    (self.motorY, self.stopY, self.proxyY.UnitLimitMin, self.proxyY.UnitLimitMax))
                _sys.exit( 255)
        except Exception as e:
            print( "checkLimits: exception")
            print( (repr(e)))

    def findProxiesAndTangoHost( self, motorX, motorY):
        """
        if pool device names are supplied, find the Tango devices and replace the proxies.
        Set 
          - self.motorX, e.g. p09/motor/d1.66
          - self.tangoHostX, e.g. haso107d1:10000
        """
        self.motorX = motorX
        self.motorY = motorY
        try:
            p = _PyTango.DeviceProxy( self.motorX)
            if proxyHasAttribute( p, "Velocity"):
                dName = p.TangoDevice
                self.proxyX = _PyTango.DeviceProxy( dName)
            else:
                dName = self.motorX
                self.proxyX = p

            ( mName, hName) = self.splitDeviceNameAndTangoHost( dName)
            self.motorX = mName
            self.tangoHostX = hName

            p = _PyTango.DeviceProxy( self.motorY)
            if proxyHasAttribute( p, "Velocity"):
                dName = p.TangoDevice
                self.proxyY = _PyTango.DeviceProxy( dName)
            else:
                dName = self.motorY
                self.proxyY = p

            ( mName, hName) = self.splitDeviceNameAndTangoHost( dName)
            self.motorY = mName
            self.tangoHostY = hName

            self.channelX = int( getDeviceProperty( self.motorX, 
                                                                  "Channel", 
                                                                  tangoHost = self.tangoHostX)[0])
            self.channelY = int( getDeviceProperty( self.motorY, 
                                                                  "Channel", 
                                                                  tangoHost = self.tangoHostY)[0])
        except Exception as e:
            print( "Failed to create proxies to the Tango devices")
            print( repr(e))
            _sys.exit( 255)

    def splitDeviceNameAndTangoHost( self, dName):
        """
        haso107d1:10000/p09/motor/d1.66 -> 
          - p09/motor/d1.66
          - haso107d1:10000
        """
        mName = None
        hName = None
        temp = dName.find( "10000")
        if temp > 0:
            # p09/motor/d1.66
            mName = dName[(temp + 6):]
            # haso107d1:10000
            hName = dName[:(temp + 5)]
        else:
            mName = dName
        return ( mName, hName)

    def handleCtrlC( self, par1, par2):
        print( "handleCtrlC")
        self.stopMoves()
        _sys.exit( 255)
 
    def stopMoves( self): 
        self.proxyX.stopMove()
        self.proxyY.stopMove()
        while self.proxyX.state() == _PyTango.DevState.MOVING or \
              self.proxyY.state() == _PyTango.DevState.MOVING:
            print( "stopMoves: waiting for motors to stop")
            _time.sleep( 0.1)
        #
        # stop all
        #
        self.proxyX.command_inout( "WriteRead", "SA;")

    def __del__( self):
        '''
        destructor restores the slew rate
        '''
        self.stopMoves()
        self.proxyX.SlewRate = self.slewRateX

    def assertSameCard( self):
        '''
        make sure both motors are on the same VME card
        '''
        try:
            baseX = int( getDeviceProperty( self.motorX, "Base", tangoHost = self.tangoHostX)[0])
            baseY = int( getDeviceProperty( self.motorY, "Base", tangoHost = self.tangoHostY)[0])
        except Exception as e:
            print( "assertSameCard: exception")
            print( repr(e))
            _sys.exit( 255)

        if baseX != baseY:
            print( "assertSameCard: %s and %s are not on the same card" % (self.motorX, self.motorY))
            _sys.exit( 255)
        
    def toStart( self):
        '''
        start to move both motors to the start position
        '''
        print( "")
        print( "toStart: move %s to %g, %s to %g" % (self.motorX, self.startX,
                                                     self.motorY, self.startY))
        try:
            self.proxyX.position = self.startX
            self.proxyY.position = self.startY
        except Exception as e:
            print( "toStart: failed with %s" % repr( e))
            _sys.exit( 255)
        return True

    def run( self):
        '''
        execute the mesh scan using the loop feature of the VME card
        '''
        #
        # AA: all axes
        # LS: loop
        # VL: set slew rate
        # MA: move absolute
        # GO: go
        # MR: move relative
        # LE: loop end
        # ID: set DONE
        # 
        #cmd = "AA;LS%d;VL%d;MA%s%d;GO;VL%d;MA%s%d;GO;MR%s%d;GO;LE;MA%s%d;GO;ID;VL%d" % \
        #      (self.nLoop, 
        #       self.slewRateX, 
        #       commasX, self.stepsXStart, 
        #       self.slewRateXSweep, 
        #       commasX, self.stepsXStop, 
        #       commasY, self.stepsYDelta, 
        #       commasX, self.stepsXStart,
        #       self.slewRateX)

        #
        # s-shape move
        # 
        # the loop body:
        #  - X: move to stop 
        #  - Y: rel-move
        #  - X: move to start
        #  - Y: rel-move
        #
        cmd = "AA;VL%s%d;LS%d;MA%s%d;GO;MR%s%d;GO;MA%s%d;GO;MR%s%d;GO;LE;MA%s%d;GO;ID;VL%s%d" % \
              (
                self.commasX, self.slewRateXSweep, 
                int( self.nLoop/2. + 1), 
                self.commasX, self.stepsXStop, 
                self.commasY, self.stepsYDelta, 
                self.commasX, self.stepsXStart, 
                self.commasY, self.stepsYDelta, 
                self.commasX, self.stepsXStart,
                self.commasX, self.slewRateX)

        print( "TgUtils.moveLoop.run: %s" % cmd)
        self.proxyX.command_inout( "MoveLoop", cmd)

    def pause( self): 
        '''
        pause a moveLoop, e.g. because of beam loss
        '''
        self.stopMoves()
        self.posXPaused = self.proxyX.position
        self.posYPaused = self.proxyY.position
        self.stepsXPaused = self.proxyX.StepPositionController
        print( "TgUtils: paused at %g %g " % (self.posXPaused, self.posYPaused))
        self.paused = True
        
    def resume( self):
        if not self.paused:
            raise Exception( "TgUtils.moveLoop.resume", "not in paused state")
        nLoopDone = int( (self.posYPaused - self.startY)/ self.deltaY + 0.5)
        print( "TgUtils: resume at x %g, y %g, nLoopDone %d " % (self.posXPaused, self.posYPaused, nLoopDone))

        nLoopResume = self.nLoop - nLoopDone
        #
        # resume to go right
        #
        if nLoopDone % 2 == 0:
            cmd = "AA;LS%d;VL%d;MA%s%d;GO;MR%s%d;GO;MA%s%d;GO;MR%s%d;GO;LE;MA%s%d;GO;ID;VL%d" % \
                  (int( nLoopResume/2. + 1), 
                   self.slewRateXSweep, 
                   self.commasX, self.stepsXStop, 
                   self.commasY, self.stepsYDelta, 
                   self.commasX, self.stepsXStart, 
                   self.commasY, self.stepsYDelta, 
                   self.commasX, self.stepsXStart,
                   self.slewRateX)
        #
        # resume to go left
        #
        else:
            cmd = "AA;LS%d;VL%d;MA%s%d;GO;MR%s%d;GO;MA%s%d;GO;MR%s%d;GO;LE;MA%s%d;GO;ID;VL%d" % \
                  (int( nLoopResume/2. + 1), 
                   self.slewRateXSweep, 
                   self.commasX, self.stepsXStart, 
                   self.commasY, self.stepsYDelta, 
                   self.commasX, self.stepsXStop, 
                   self.commasY, self.stepsYDelta, 
                   self.commasX, self.stepsXStart,
                   self.slewRateX)

        print( "TgUtils.moveLoop.resume: %s" % cmd)
        self.proxyX.command_inout( "MoveLoop", cmd)
        
    def runNormal( self):
        '''
        execute the mesh scan using conventional move commands
        '''
        for i in range( int(self.nLoop/2.)):
            #
            # move forth
            #
            self.proxyX.SlewRate = self.slewRateXSweep
            self.proxyX.Position = self.stopX
            while self.proxyX.state() == _PyTango.DevState.MOVING or \
                  self.proxyY.state() == _PyTango.DevState.MOVING:
                print( "(%d) normal, forth: posX %g, posY %g" % \
                    ( i, self.proxyX.Position, self.proxyY.Position))
                _time.sleep(0.5)
            #
            # rel-move outer
            #
            self.proxyY.Position = self.proxyY.Position + self.deltaY
            while self.proxyY.state() == _PyTango.DevState.MOVING:
                print( "(%d) normal, re-move:  posX %g, posY %g" % \
                    ( i, self.proxyX.Position, self.proxyY.Position))
                _time.sleep(0.5)
            #
            # move back inner and 
            #
            self.proxyX.SlewRate = self.slewRateX
            self.proxyX.Position = self.startX
            while self.proxyX.state() == _PyTango.DevState.MOVING:
                print( "(%d) normal, back:  posX %g, posY %g" % \
                    ( i, self.proxyX.Position, self.proxyY.Position))
                _time.sleep(0.5)
            #
            # rel-move outer
            #
            self.proxyY.Position = self.proxyY.Position + self.deltaY
            while self.proxyY.state() == _PyTango.DevState.MOVING:
                print( "(%d) normal, re-move:  posX %g, posY %g" % \
                    ( i, self.proxyX.Position, self.proxyY.Position))
                _time.sleep(0.5)

    def state( self):
        if self.proxyX.state() == _PyTango.DevState.MOVING or \
           self.proxyY.state() == _PyTango.DevState.MOVING:
            return _PyTango.DevState.MOVING
        else:
            return _PyTango.DevState.ON

try:
    _db = _PyTango.Database()
    _dbProxy = _PyTango.DeviceProxy( "sys/database/2")
except: 
    print( "TgUtils: failed to connect to local DB (informational)")

def petraBeamCurrent():
    '''
    returns the BeamCurrent attribute of the petra/global/keyword device
    '''
    global _petraGlobalsKeyword
    if _petraGlobalsKeyword is None:
        try:
            _petraGlobalsKeyword = _PyTango.DeviceProxy( "petra/globals/keyword")
        except Exception as e:
            print( "TgUtils.petraCurrent: failed to create proxy to petra/globals/keyword")
            print( repr(e))
            return None
    return _petraGlobalsKeyword.BeamCurrent

def petraMachineState():
    '''
    returns the MachineState attribute of the petra/global/keyword device
    '''
    global _petraGlobalsKeyword
    if _petraGlobalsKeyword is None:
        try:
            _petraGlobalsKeyword = _PyTango.DeviceProxy( "petra/globals/keyword")
        except Exception as e:
            print( "TgUtils.petraCurrent: failed to create proxy to petra/globals/keyword")
            print( repr(e))
            return None
    return _petraGlobalsKeyword.MachineState

def petraMachineStateText():
    '''
    returns the MachineStateText attribute of the petra/global/keyword device
    '''
    global _petraGlobalsKeyword
    if _petraGlobalsKeyword is None:
        try:
            _petraGlobalsKeyword = _PyTango.DeviceProxy( "petra/globals/keyword")
        except Exception as e:
            print( "TgUtils.petraCurrent: failed to create proxy to petra/globals/keyword")
            print( repr(e))
            return None
    return _petraGlobalsKeyword.MachineStateText

def petraMachineStateExt():
    '''
    returns the MachineState.ext attribute of the petra/global/keyword device
    '''
    global _petraGlobalsKeyword
    if _petraGlobalsKeyword is None:
        try:
            _petraGlobalsKeyword = _PyTango.DeviceProxy( "petra/globals/keyword")
        except Exception as e:
            print( "TgUtils.petraCurrent: failed to create proxy to petra/globals/keyword")
            print( repr(e))
            return None
    return _petraGlobalsKeyword.read_attribute( "MachineState.ext").value

def petraMachineStateTextExt():
    '''
    returns the MachineStateText.ext attribute of the petra/global/keyword device
    '''
    global _petraGlobalsKeyword
    if _petraGlobalsKeyword is None:
        try:
            _petraGlobalsKeyword = _PyTango.DeviceProxy( "petra/globals/keyword")
        except Exception as e:
            print( "TgUtils.petraCurrent: failed to create proxy to petra/globals/keyword")
            print( repr(e))
            return None
    return _petraGlobalsKeyword.read_attribute( "MachineStateText.ext").value

def petra(): 
    '''
    returns petraBeamCurrent from petra/globals/keyword
    '''
    return petraBeamCurrent()

def toSardanaMonitor( hsh, node = None):
    """
    sends a dictionary to a SardanaMonitor process, 
    returns a dictionary ...

import HasyUtils
import random
MAX = 10
pos = [float(n)/MAX for n in range( MAX)]
d1 = [random.random() for n in range( MAX)]
d2 = [random.random() for n in range( MAX)]

hsh = { 'putData': 
           {'title': "Important Data", 
            'columns': 
            [ { 'name': "d1_mot01", 'data' : pos},
              { 'name': "d1_c01", 'data' : d1},
              { 'name': "d1_c02", 'data' : d2},
           ]}}
smNode = "haso107d1"
if not HasyUtils.isSardanaMonitorAlive(): 
    return False
hsh = HasyUtils.toSardanaMonitor( hsh, node = smNode)
print hsh
if hsh[ 'result'].upper() == 'DONE':
    print( "success!")
    
print HasyUtils.toSardanaMonitor( {'gra_decode_text': "date()"}, node = smNode)
print HasyUtils.toSardanaMonitor( {'gra_decode_int': "2*3"}, node = smNode)
print HasyUtils.toSardanaMonitor( {'gra_decode_double': "sqrt(2.)"}, node = smNode)
print HasyUtils.toSardanaMonitor( {'gra_command': "cls;wait 1;display 1"}, node = smNode)
hsh = HasyUtils.toSardanaMonitor( { 'getData': True})
print repr( hsh.keys())
print repr( hsh['getData'].keys())
print repr( hsh['getData']['D1_C01']['x'])

    """
    import zmq, json, socket

    if node is None:
        node = socket.gethostbyname( socket.getfqdn())

    context = zmq.Context()
    sckt = context.socket(zmq.REQ)
    #
    # prevent context.term() from hanging, if the message
    # is not consumed by a receiver.
    # 
    sckt.setsockopt(zmq.LINGER, 1)
    try:
        sckt.connect('tcp://%s:7778' % node)
    except Exception as e:
        sckt.close()
        return { 'result': "TgUtils.toSardanaMonitor: failed to connect to %s" % node}

    hshEnc = json.dumps( hsh)
    #
    # sending bytearrays seems to work for Python2 and Python3
    #
    if _sys.version_info.major >= 1: 
        hshEnc = bytearray( hshEnc, encoding="utf-8")
    try:
        res = sckt.send( hshEnc)
    except Exception as e:
        sckt.close()
        return { 'result': "TgUtils.toSardanaMonitor: exception by send() %s" % repr(e)}
    #
    # SardanaMonitor receives the Dct, processes it and then
    # returns the message. This may take some time. To pass
    # 4 arrays, each with 10000 pts takes 2.3s
    #
    if 'isAlive' in hsh:
        lst = zmq.select([sckt], [], [], 0.5)
        if sckt in lst[0]:
            hshEnc = sckt.recv() 
            sckt.close()
            context.term()
            return json.loads( hshEnc)
        else: 
            sckt.close()
            context.term()
            return { 'result': 'notAlive'}
    else:
        lst = zmq.select([sckt], [], [], 3.0)
        if sckt in lst[0]:
            hshEnc = sckt.recv() 
            sckt.close()
            context.term()
            return json.loads( hshEnc)
        else: 
            sckt.close()
            context.term()
            return { 'result': 'TgUtils: no reply from SardanaMonitor'}

def isSardanaMonitorAlive( node = None):
    '''
    returns True, if there is a SardanaMonitor responding to the isAlive prompt
    '''
    hsh = toSardanaMonitor( { 'isAlive': True}, node = node)
    if hsh[ 'result'] == 'notAlive':
        return False
    else:
        return True

def getMgConfiguration( mgName): 
    '''   
    return a dictionary containing the configuration of the MG
    '''
    try: 
        p = _PyTango.DeviceProxy( mgName)
    except Exception as e:
        print( "TgUtils.getMgConfiguration: failed to create a proxy to %s" % mgName)
        return None

    return _json.loads( p.Configuration)

def saveAttrsAsPython( tangoHost = None, alias = None, module = None): 
    '''
    creates the versioned file: /online_dir/MotorLogs/MotorAttr<alias>.py

      tangoHost:  if None, translate TANGO_HOST
      alias:      theta
      module:     oms58, omsmaxv, spk,motor_tango

      returns:    fileName
    '''

    motorAttributes = [ 
        'Acceleration',
        'Conversion', 
        'BaseRate', 
        'StepBacklash',
        'CutOrMap', 
        'SlewRateMax',
        'StepPositionController',
        'StepPositionInternal',
        'UnitCalibration', 
        'FlagProtected', 
        'SettleTime',
        'Position', 
        'SlewRateMin',
        'SlewRate',
        'StepCalibration',
        'UnitLimitMax',
        'UnitLimitMin', 
    ]

    encoderAttributes = [ 
        'ConversionEncoder', 
        'CorrectionGain', 
        'EncoderRatio',
        'HomePosition',
        'PositionEncoder',
        'PositionEncoderRaw',
    ]


    #
    # motors are identified by module types
    #
    if( module.lower() != 'oms58' and
        module.lower() != 'omsmaxv' and
        module.lower() != 'spk' and
        module.lower() != 'motor_tango'):
        print( "TgUtils.saveAttrsAsPython: wrong module %s" % module)
        return False

    if tangoHost is None:
        tangoHost = _os.getenv( 'TANGO_HOST')
        if tangoHost is None:
            print( "TgUtils.saveAttrsAsPython: TANGO_HOST is not defined")
            return False


    if alias is None:
        print( "TgUtils.saveAttrsAsPython: alias not specified" )
        return False

    if module is None:
        print( "TgUtils.saveAttrsAsPython: module not specified" )
        return False


    if not _os.path.isdir( '/online_dir/MotorLogs'):
        try:
            _os.mkdir( '/online_dir/MotorLogs')
        except:
            print( "TgUtils.saveAttrsAsPython: Failed to create /online_dir/MotorLogs")
            return False

    try:
        p = _PyTango.DeviceProxy( alias)
    except:
        print( "TgUtils.saveAttrsAsPython: failed to create proxy to %s/%s" % (tangoHost, alias))
        return False

    if proxyHasAttribute( p, "TangoDevice"): 
        p = _PyTango.DeviceProxy( p.TangoDevice)

    attrs = motorAttributes[:]
    try:
        if( len( p.get_property('FlagEncoder')['FlagEncoder']) > 0 and
            p.get_property('FlagEncoder')['FlagEncoder'][0] == '1'): 
            attrs.extend( encoderAttributes)
    except:
        print( "TgUtils.saveAttrsAsPython: failed to get_property FlagEncoder %s/%s" % (tangoHost, deviceName))

    #
    # if the device has no position, it is not a motor
    #
    if not proxyHasAttribute( p, "position"):
        print( "TgUtils.saveAttrsAsPython: %s/%s has no attribute position" % ( tangoHost, deviceName))
        return False

    fileName = "/online_dir/MotorLogs/Attr_%s.py" % alias
    if _os.path.exists( '/usr/local/bin/vrsn'):
        _os.system( "/usr/local/bin/vrsn -s -nolog %s" % fileName)
        
    try:
        fileHandle = open( "%s" % fileName, "w")
    except Exception as e:
        print( "TgUtils.saveAttrsAsPython: failed to open %s" % fileName)
        _sys.stderr.write( "%s\n" % str( e))
        return 

    fileHandle.write( "#\n")

    tmStart = _time.localtime()
    fileHandle.write( "#\n# Created at %02d.%02d.%d %02d:%02dh\n#\n" % 
                      (tmStart[2], tmStart[1], tmStart[0], tmStart[3], tmStart[4]))
    fileHandle.write( "# Selected attributes of %s, %s ( %s) \n" % (alias, p.dev_name(), module))
    fileHandle.write( "#\n")
    fileHandle.write( "# This is a versioned file \n")
    fileHandle.write( "#\n")
    fileHandle.write( "# To restore the attributes:\n")
    fileHandle.write( "#  $ python %s\n" % fileName)
    fileHandle.write( "#\n")
    fileHandle.write( "import PyTango\n")
    fileHandle.write( "print \" restoring %s/%s (%s) \"\n" % ( tangoHost, p.dev_name(), alias))
    fileHandle.write( "proxy = PyTango.DeviceProxy( \"%s/%s\")\n" % (tangoHost, p.dev_name()))
    #
    # we log encoder attributes only, if the FlagEncoder property is '1'
    #
    attrs = motorAttributes[:]
    try:
        if( len( p.get_property('FlagEncoder')['FlagEncoder']) > 0 and
            p.get_property('FlagEncoder')['FlagEncoder'][0] == '1'): 
            attrs.extend( encoderAttributes)
    except:
        print( "TgUtils.saveAttrsAsPython: trouble getting FlagEncoder for %s" % p.dev_name())

    for attr in attrs:
        if proxyHasAttribute( p, attr.lower()):
            try:
                attrValue = p.read_attribute( attr.lower()).value
                attrInfo = p.get_attribute_config( attr.lower())
            except:
                continue
            if attr.lower() == 'position':
                fileHandle.write( "# proxy.write_attribute( \"%s\", %s) [Attr. config: %s, %s]\n" % \
                                      (attr.lower(), attrValue, str(attrInfo.min_value), str( attrInfo.max_value)))
                continue
            if attrInfo.writable == _PyTango._PyTango.AttrWriteType.READ_WRITE:
                # resultsPython.append( "print( \"  %s: %s\"\n" % (attr.lower(), attrValue)))
                fileHandle.write( "proxy.write_attribute( \"%s\", %s)\n" % (attr.lower(), attrValue))
            else:
                fileHandle.write( "# read-only attribute %s was %s\n" % (attr.lower(), attrValue))

    try:
        attrValue = p.read_attribute( "UnitCalibrationUser").value
        fileHandle.write( "proxy.write_attribute( \"UnitCalibrationUser\", 0.0)\n")
    except:
        pass

    fileHandle.close()

    return fileName


def getLivingLocalPoolNames():
    '''
    return a list poolNames that respond to state()
    '''
    lst = getLocalPoolNames()
    poolNames = []
    for poolName in lst:
        try:
            p = _PyTango.DeviceProxy( poolName)
            sts = p.state()
        except:
            print( "getLivingLocalPoolNames: no response from %s, ignore" % poolName)
            continue
        poolNames.append( poolName)
    return poolNames


def configureControllers( logLevel = None): 
    '''
    logLevel is not None
      set the controller LogLevel attribute to logLevel, Zibi: 30, def. 10
    logLevel is None
      print the controller LogLevel attribute

    Background: debug haspp08 'Measurement group ended acquisition with Fault state'
    '''
    poolNames = getLivingLocalPoolNames()
    for poolName in poolNames: 
        try: 
            pool = _PyTango.DeviceProxy( poolName)
        except:
            print( "TgUtils.configureControllers: failed to get proxy to %s" % poolName)
            return 0
        ctrlList = pool.ControllerList
        for ctrl in ctrlList: 
            hsh = _json.loads( ctrl)
            try: 
                p = _PyTango.DeviceProxy( hsh[ 'full_name'])
            except Exception as e: 
                print( "TgUtils.configureController: %s" % repr( e))
                continue
            if logLevel is not None: 
                p.LogLevel = logLevel
            print( "TgUtils.confCtrl: %s LogLevel %d" % ( p.name(), p.LogLevel))

    return 

#
def assertPyspMonitorRunning( zmqPort = 7779): 
    """
    returns (status, wasLaunched)

    it tests whether the pyspMonitor responds to isAlive. 
    If so, the function return rather quickly.

    Otherwise we call assertProcessRunning() which may take some time
    """
    res = toPyspMonitor( { 'isAlive': True}, testAlive = False, zmqPort = zmqPort, singleMonitor = True) 
    if res[ 'result'] == 'done': 
        return( True, False)
    else: 
        #
        # even if the pyspMonitor does not reply to 'isAlive', 
        # the process may exist
        #
        # we can no longer kill pyspMonitor processes because
        # there may be several processes listening to different ports
        # not easy to distinguish them and find the zombies
        #
        #    utils.killProcess( "/usr/bin/pyspMonitor.py")

        
        assertProcessRunning( "/usr/bin/pyspMonitor.py -p %d" % zmqPort)
        res = toPyspMonitor( { 'isAlive': True}, testAlive = False, zmqPort = zmqPort, singleMonitor = True) 
        startTime = _time.time()
        while res[ 'result'] != 'done': 
            _time.sleep( 0.5)
            res = toPyspMonitor( { 'isAlive': True}, testAlive = False, zmqPort = zmqPort, singleMonitor = True) 
            if (_time.time() - startTime) > 5: 
                print( "TgUtils.assertPyspMonitorRunning: no reply on port %d after 5 sec" % zmqPort)
                print( "TgUtils.assertPyspMonitorRunning: reply %s" % repr( res))
                print( "TgUtils.assertPyspMonitorRunning: sys.exit()")
                _sys.exit( 0)
                return (False, False)
        return ( True, True)
#
def assertPyspViewerRunning( zmqPort = 7879): 
    """
    returns (status, wasLaunched)

    it tests whether the pyspViewer responds to isAlive. 
    If so, the function return rather quickly.

    Otherwise we call assertProcessRunning() which may take some time
    """
    res = toPyspViewer( { 'isAlive': True}, zmqPort = zmqPort) 
    if res[ 'result'] == 'done': 
        return( True, False)
    else: 
        #
        # even if the pyspViewer does not reply to 'isAlive', 
        # the process may exist
        #
        # we can no longer kill pyspMonitor processes because
        # there may be several processes listening to different ports
        # not easy to distinguish them and find the zombies
        
        assertProcessRunning( "/usr/bin/pyspViewer.py -p %d" % zmqPort)
        res = toPyspViewer( { 'isAlive': True}, zmqPort = zmqPort) 
        startTime = _time.time()
        while res[ 'result'] != 'done': 
            _time.sleep( 0.5)
            res = toPyspViewer( { 'isAlive': True}, zmqPort = zmqPort) 
            if (_time.time() - startTime) > 5: 
                print( "TgUtils.assertPyspViewerRunning: no reply on port %d after 5 sec" % zmqPort)
                print( "TgUtils.assertPyspViewerRunning: reply %s" % repr( res))
                print( "TgUtils.assertPyspViewerRunning: sys.exit()")
                _sys.exit( 0)
                return (False, False)
        return ( True, True)
        
#
# this function is copied from 
#  $HOME/gitlabDESY/Sardana/hasyutils/HasyUtils/OtherUtils.py
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
            _time.sleep( 5) # 15.9.2021
            return (True, True)
        _time.sleep( 0.1)
        if count > 15:
            print( "OtherUtils.assertProcessRunning: %s does not start in time " % processName)
            return ( False, False)

    return (True, True)

def stopPyspMonitors(): 
    """
    sends 'exit' to all ports, 7779 + range(5), with pyspMonitor answering 'isAlive' with 'done'

    return False, if a port does not turn to 'notAlive' withing 5 sec., True otherwise
    """
    print( "TgUtils.stopPyspMonitor")
    for i in range( 5): 
        zmqPort = i + 7779
        ret = toPyspMonitor( { 'isAlive': True}, zmqPort = zmqPort)
        #print( "TgUtils.stopPyspMonitors: 'isAlive' sent to %d received %s " % (zmqPort, ret[ 'result']))
        if ret[ 'result'] == 'done': 
            #print( "TgUtils.stopPyspMonitors: sending 'exit' to %s" % zmqPort)
            hsh = toPyspMonitor( { 'command': ['exit']}, zmqPort = zmqPort)
            ret = toPyspMonitor( { 'isAlive': True}, zmqPort = zmqPort)
            #print( "TgUtils.stopPyspMonitors: %d sent: %s" % ( zmqPort, ret[ 'result']))
            startTime = _time.time()
            while ret[ 'result'] != 'notAlive': 
                _time.sleep( 0.5)
                ret = toPyspMonitor( { 'isAlive': True}, zmqPort = zmqPort)
                if (_time.time() - startTime) > 5: 
                    print( "TgUtils.stopPyspMonitors, port %d, did not turn to 'notAlive' within 5 sec" % zmqPort)
                    return False
                #print( "TgUtils.stopPyspMonitors: %d sent: %s" % ( zmqPort, ret[ 'result']))

    return True

def stopPyspViewers():  
    """
    sends 'exit' to all ports, 7879 + range(5), with pyspViewer answering 'isAlive' with 'done'

    return False, if a port does not turn to 'notAlive' withing 5 sec., True otherwise
    """
    print( "TgUtils.stopPyspViewers")
    for i in range( 5): 
        zmqPort = i + 7879
        ret = toPyspViewer( { 'isAlive': True}, zmqPort = zmqPort)
        #print( "TgUtils.stopPyspMonitors: 'isAlive' sent to %d received %s " % (zmqPort, ret[ 'result']))
        if ret[ 'result'] == 'done': 
            #print( "TgUtils.stopPyspMonitors: sending 'exit' to %s" % zmqPort)
            hsh = toPyspViewer( { 'command': ['exit']}, zmqPort = zmqPort)
            ret = toPyspViewer( { 'isAlive': True}, zmqPort = zmqPort)
            #print( "TgUtils.stopPyspMonitors: %d sent: %s" % ( zmqPort, ret[ 'result']))
            startTime = _time.time()
            while ret[ 'result'] != 'notAlive': 
                _time.sleep( 0.5)
                ret = toPyspViewer( { 'isAlive': True}, zmqPort = zmqPort)
                if (_time.time() - startTime) > 5: 
                    print( "TgUtils.stopPyspMonitors, port %d, did not turn to 'notAlive' within 5 sec" % zmqPort)
                    return False
                #print( "TgUtils.stopPyspMonitors: %d sent: %s" % ( zmqPort, ret[ 'result']))

    return True
#
# this function is copied from 
#  $HOME/gitlabDESY/Sardana/hasyutils/HasyUtils/OtherUtils.py
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


def toPyspViewer( hsh, node = None, testAlive = False, zmqPort = 7879):
    '''
    The documentation can be found by PySpectra.toPyspViewer?
    '''
    return toPyspMonitorExec( hsh, node = node, testAlive = testAlive, zmqPort = zmqPort, fromViewer = True)

_arrRegisteredMonitors = None
_timeArrRegisteredMonitors = None

def toPyspMonitor( hsh, node = None, testAlive = False, zmqPort = None, singleMonitor = False):
    '''
    The documentation can be found by PySpectra.toPyspMonitor?
    '''
    global _arrRegisteredMonitors, _timeArrRegisteredMonitors

    #print( "TgUtils.toPyspMonitor: node %s, zmqPort %s" % ( repr( node), repr( zmqPort)))
    #print( "TgUtils.toPyspMonitor: testAlice %s, singleMonitor %s" % ( repr( testAlive), repr( singleMonitor)))
    #print( "TgUtils.toPyspMonitor: hsh %s" % repr( hsh))
    #
    # the user decided that the data should go to one pyspMonitor only, no Macroserver I/O needed
    #
    if singleMonitor: 
        return toPyspMonitorExec( hsh, node = node, testAlive = testAlive, zmqPort = zmqPort)

    #
    # no macroserver is running
    #
    if not checkMacroServer(): 
        return toPyspMonitorExec( hsh, node = node, testAlive = testAlive, zmqPort = zmqPort)
    #
    # if the user makes specifications: we do not look at RegisteredPyspMonitors
    #
    if node is not None or zmqPort is not None: 
        return toPyspMonitorExec( hsh, node = node, testAlive = testAlive, zmqPort = zmqPort)
        
    if _arrRegisteredMonitors is None: 
        _timeArrRegisteredMonitors = _time.time()
        _arrRegisteredMonitors = getEnv( "RegisteredPyspMonitors") 

    if (_time.time() - _timeArrRegisteredMonitors) > 3.: 
        _timeArrRegisteredMonitors = _time.time()
        _arrRegisteredMonitors = getEnv( "RegisteredPyspMonitors") 

    #
    #  mvsa asks whether a pypMonitor is alive
    #  if no pyspMonitors are registered, return False
    if _arrRegisteredMonitors is None or _arrRegisteredMonitors == []:
        if testAlive == True: 
            ret = toPyspMonitorExec( hsh, node = node, testAlive = testAlive, zmqPort = zmqPort)
            return ret
        else: 
            return { 'result': 'notAlive'}

    lstArr = []
    ret = None
    for elm in _arrRegisteredMonitors:
        lst = elm.split( "_")
        ret = toPyspMonitorExec( hsh, node = lst[0], 
                                 testAlive = testAlive, 
                                 zmqPort = int( lst[1]))
        if ret[ 'result'] != 'TgUtils.toPyspMonitor: communication time-out':
            lstArr.append( elm)
        else: 
            print( "TgUtils.toPyspMonitorExec: disconnect %s, delete from RegisteredPyspMonitors" % elm)
    #
    # lstArr is shorter, if we had a time-out
    #
    if len( lstArr) < len( _arrRegisteredMonitors): 
        #
        # it is important to re-initialize _arrRegisteredPyspMonitors
        # otherwise 'dead' pyspMonitors are still in there which 
        # may lead to their re-initialization during next I/Os 
        #
        setEnv( "RegisteredPyspMonitors", lstArr)
        _arrRegisteredMonitors = lstArr[:]

    return ret


def _exit_handler_toPyspMonitor(): 
    global contextZmq
    global socketDctZmq
    
    #
    # key: haso107tk_7779
    #
    for key in list( socketDctZmq.keys()): 
        _closeZmqSocket( key)

    return 

socketDctZmq = {}
contextZmq = None

def _testSocket( sckt): 
    import json, zmq

    hshEnc = json.dumps( { 'isAlive': True})
    #
    # destination: $HOME/gitlabDESY/pySpectra/PySpectra/pyspMonitorClass.py, cb_timerZMQ
    #
    try:
        res = sckt.send( bytearray( hshEnc, encoding="utf-8"))
    except Exception as e:
        return False

    lst = zmq.select([sckt], [], [], 0.5)
    if sckt in lst[0]:
        hshEnc = sckt.recv() 
        argout = True
    else: 
        argout = False

    return argout
    
def _getZmqSocket( node, zmqPort): 
    global socketDctZmq, contextZmq 
    import atexit
    import zmq

    hostPort = "%s_%d" % (node, zmqPort)
 
    if hostPort in socketDctZmq: 
        sckt = socketDctZmq[ hostPort]
        if not _testSocket( sckt): 
            print( "TgUtils._getZmqSocket: testSocket failed")
            _sys.exit( 255)
        if contextZmq is None:  
            print( "TgUtils._getZmqSocket: contextZmq is None")
            _sys.exit( 255)
    else: 
        if contextZmq is None: 
            atexit.register( _exit_handler_toPyspMonitor) 
            contextZmq = zmq.Context()
            #context = zmq.Context()
            
        sckt = contextZmq.socket(zmq.REQ)
        #
        # prevent context.term() from hanging, if the message
        # is not consumed by a receiver.
        #
        sckt.setsockopt(zmq.LINGER, 1)
        try:
            sckt.connect('tcp://%s:%d' % (node, zmqPort))
        except Exception as e:
            sckt.close()
            print( "TgUtils._getZmqSocket: connect failed %s" % repr( e))
            return None 
        #
        # maybe pyspMonitor does not already exist, needs to be started
        #
        if not _testSocket( sckt): 
            print( "TgUtils._getZmqSocket: testSocket failed (2)")
            return None

        socketDctZmq[ hostPort] = sckt

    return sckt

def _closeZmqSocket( hostPort): 
    global socketDctZmq, contextZmq 

    #print( "TgUtils._closeZmqSocket closing socket for %s %s " % (hostPort, socketDctZmq[ hostPort].close()))

    #
    # the 'del' statement is vital. Otherwise a reference to the socket remains
    # and we get this error
    # Exception AttributeError: "'NoneType' object has no attribute 'ref'" in 
    # <bound method Socket.__del__ of <zmq.sugar.socket.Socket object at 0x7fb75e25bfa0>> ignored
    #
    socketDctZmq[ hostPort].close()
    del socketDctZmq[ hostPort]

    if len( list( socketDctZmq.keys())) == 0: 
        contextZmq.term()
        contextZmq = None

    return

def toPyspMonitorExec( hsh, node = None, testAlive = False, zmqPort = 7779, fromViewer = False):
    '''
    Send a dictionary to the pyspMonitor process via ZMQ. 

    Please see PySpectra.toPyspMonitor? for help.
    '''
    import json, socket, zmq
    global socketDctZmq, contextZmq 

    if zmqPort is None: 
        zmqPort = 7779
    #print( "TgUtils.toPyspMonitorExec: hsh %s node %s zmqPort %s" % ( repr( hsh), repr( node), repr( zmqPort)))
    #
    # testAlive == True reduces the rate from 625 Hz to 360 Hz
    #
    # we cannot start pyspMonitor on another host
    #
    if testAlive: 
        if fromViewer: 
            if node is not None: 
                if node.find( socket.gethostname()) == 0: 
                    (status, wasLaunched) = assertPyspViewerRunning( zmqPort = zmqPort)
                    if not status: 
                        raise ValueError( "TgUtils.toPyspMonitor: trouble with pyspMonitor")
            else: 
                (status, wasLaunched) = assertPyspViewerRunning( zmqPort = zmqPort)
        else:
            if node is not None: 
                if node.find( socket.gethostname()) == 0: 
                    (status, wasLaunched) = assertPyspMonitorRunning( zmqPort = zmqPort)
                    if not status: 
                        raise ValueError( "TgUtils.toPyspMonitor: trouble with pyspMonitor")
            else: 
                (status, wasLaunched) = assertPyspMonitorRunning( zmqPort = zmqPort)
    #
    # socketDctZmq: { 'haspp08_7779': <sckt>, 'haspp08_7780': <sckt>} 
    #
    if node is None:
        node = socket.gethostname()
    #
    # reuseSocket == False
    # real	0m37.638s
    # user	0m14.166s
    # sys	0m13.369s
    #
    # reuseSocket == True
    # real	0m13.555s
    # user	0m3.004s
    # sys	0m1.018s
    #
    reuseSocket = False
    if reuseSocket: 
        sckt = _getZmqSocket( node, zmqPort)
    else: 
        contextZmq = zmq.Context()
        sckt = contextZmq.socket(zmq.REQ)
        #
        # prevent context.term() from hanging, if the message
        # is not consumed by a receiver.
        #
        sckt.setsockopt(zmq.LINGER, 1)
        try:
            sckt.connect('tcp://%s:%d' % (node, zmqPort))
        except Exception as e:
            sckt.close()
            print( "TgUtils.toPyspMonitorExec: connected failed %s, node %s, zmqPort %s " % 
                   (repr( e), repr( node), repr( zmqPort)))
            return None 

    if sckt is None: 
        return { 'result': "TgUtils.toPyspMonitorExec: failed to connect to %s, %d" % (node, zmqPort)}    

    replaceNumpyArrays( hsh)

    #print( "TgUtils.toPyspMonitorExec: sending %s to %s %d" % (hsh, node, zmqPort))

    hshEnc = json.dumps( hsh)
    #
    # destination: $HOME/gitlabDESY/pySpectra/PySpectra/pyspMonitorClass.py, cb_timerZMQ
    #
    try:
        res = sckt.send( bytearray( hshEnc, encoding="utf-8"))
    except Exception as e:
        if reuseSocket: 
            _closeZmqSocket( "%s_%d" % ( node, zmqPort))
        else: 
            sckt.close()
            contextZmq.term()
            contextZmq = None
        #print( "TgUtils.toPyspMonitorExec: exception (%s, %d)" % (node, zmqPort))
        #print( "TgUtils.toPyspMonitorExec: %s" % repr( e))
        return { 'result': "TgUtils.toPyspMonitor: exception by send() %s" % repr(e)}
    #
    # PyspMonitor receives the Dct, processes it and then
    # returns the message. This may take some time. To pass
    # 4 arrays, each with 10000 pts takes 2.3s
    #
    if 'isAlive' in hsh:
        lst = zmq.select([sckt], [], [], 0.5)
        if sckt in lst[0]:
            hshEnc = sckt.recv() 
            argout = json.loads( hshEnc)
        else: 
            argout = { 'result': 'notAlive'}
    else:
        #
        # we also wait for a response to 'exit' although we will
        # not receive anything. This is necessary otherwise sending
        # 'exit' to pyspMonitor running on another hosts fails
        #

        tmo = 3.
        if 'command' in hsh and \
           ('exit' == hsh[ 'command'] or 'exit' in hsh[ 'command']): 
            tmo = 0.1

        lst = zmq.select([sckt], [], [], tmo)
        if sckt in lst[0]:
            hshEnc = sckt.recv() 
            argout = json.loads( hshEnc) 
        else: 
            argout = { 'result': 'TgUtils.toPyspMonitor: communication time-out'}

    if not reuseSocket: 
        sckt.close()
        contextZmq.term()
        contextZmq = None

    #print( "TgUtils.toPyspMonitorExec: return %s" % ( repr( argout)))
    return argout

def isPyspMonitorAlive( node = None, zmqPort = None):
    '''
    returns True, if there is a pyspMonitor responding to the isAlive prompt
    '''
    hsh = toPyspMonitor( { 'isAlive': True}, node = node, testAlive = False, zmqPort = None)
    if hsh[ 'result'] == 'notAlive':
        return False
    else:
        return True


def killProcess( processName):
    '''
    uses 'ps -Af' to find the process PID the kill via PID
    '''
    #processName = bytearray( processName, encoding='utf-8')
    p = subprocess.Popen(['ps', '-Af'], stdout=subprocess.PIPE)
    out, err = p.communicate()
    for line in out.splitlines():
        line = str( line)
        if processName in line:
            pid = int(line.split(None)[1])
            os.kill(pid, signal.SIGKILL)
    return 

def toMacroExecutor( hsh, node = None, timeout = 60, testAlive = False):
    '''
    Send a dictionary to the macroExecutor process via ZMQ. 

    testAlive == True: 
        it is checked whether a macroExector process responds to 
        the { 'isAlive': True} dictionary. 
          if not, SardanaMacroExecutor is launched

    timeout 
        used with 'yesno'

    Example: 
      if not HasyUtils.isMacroExecutorAlive():
          return False
      ret = HasyUtils.toMacroExecutor( { 'yesno': 'do you really want it'})
      if ret[ 'result'] != 'done': 
          print( "error" % ret[ 'result'])

    ---
    '''
    import zmq, json, socket

    #
    # testAlive == True reduces the rate from 625 Hz to 360 Hz
    #
    if testAlive: 
        (status, wasLaunched) = assertMacroExecutorRunning()
        if not status: 
            raise ValueError( "TgUtils.toMacroExecutor: trouble with SardanaMacroExecutor")

    if node is None:
        node = socket.gethostbyname( socket.getfqdn())

    context = zmq.Context()
    sckt = context.socket(zmq.REQ)
    #
    # prevent context.term() from hanging, if the message
    # is not consumed by a receiver.
    #
    sckt.setsockopt(zmq.LINGER, 1)
    try:
        sckt.connect('tcp://%s:7790' % node)
    except Exception as e:
        sckt.close()
        print( "TgUtils.toMacroExecutor: connected failed %s" % repr( e))
        return { 'result': "TgUtils.toMacroExecutor: failed to connect to %s" % node}

    
    hsh[ 'timeout'] = timeout

    replaceNumpyArrays( hsh)

    #print( "TgUtils.toMacroExecutor: sending %s" % hsh)

    hshEnc = json.dumps( hsh)
    try:
        res = sckt.send( bytearray( hshEnc, encoding="utf-8"))
    except Exception as e:
        sckt.close()
        return { 'result': "TgUtils.toMacroExecutor: exception by send() %s" % repr(e)}
    #
    # SardanaMacroExecutor receives the Dct, processes it and then
    # returns the message. This may take some time. To pass
    # 4 arrays, each with 10000 pts takes 2.3s
    #
    if 'isAlive' in hsh:
        lst = zmq.select([sckt], [], [], 0.5)
        if sckt in lst[0]:
            hshEnc = sckt.recv() 
            sckt.close()
            context.term()
            argout = json.loads( hshEnc)
        else: 
            sckt.close()
            context.term()
            argout = { 'result': 'notAlive'}
    else:
        lst = zmq.select([sckt], [], [], timeout)
        if sckt in lst[0]:
            hshEnc = sckt.recv() 
            sckt.close()
            context.term()
            argout = json.loads( hshEnc) 

        else: 
            sckt.close()
            context.term()
            argout = { 'result': 'TgUtils.toMacroExecutor: communication time-out'}

    #print( "TgUtils.toMacroExecutor: received %s" % argout)
    return argout

def toZMQ( hsh, portNo, node = None, timeout = 60, testAlive = False):
    '''
    this is just a debugging tool

    Chat: out 
    '''

    import zmq, json, socket

    if node is None:
        node = socket.gethostbyname( socket.getfqdn())

    context = zmq.Context()
    sckt = context.socket(zmq.REQ)
    #
    # prevent context.term() from hanging, if the message
    # is not consumed by a receiver.
    #
    sckt.setsockopt(zmq.LINGER, 1)
    try:
        sckt.connect('tcp://%s:%d' % (node, portNo))
    except Exception as e:
        sckt.close()
        print( "TgUtils.toMacroExecutor: connected failed %s" % repr( e))
        return { 'result': "TgUtils.toMacroExecutor: failed to connect to %s" % node}

    
    hsh[ 'timeout'] = timeout

    replaceNumpyArrays( hsh)

    #print( "TgUtils.toMacroExecutor: sending %s" % hsh)

    hshEnc = json.dumps( hsh)
    try:
        res = sckt.send( bytearray( hshEnc, encoding="utf-8"))
    except Exception as e:
        sckt.close()
        return { 'result': "TgUtils.toMacroExecutor: exception by send() %s" % repr(e)}
    if 'isAlive' in hsh:
        lst = zmq.select([sckt], [], [], 0.5)
        if sckt in lst[0]:
            hshEnc = sckt.recv() 
            sckt.close()
            context.term()
            argout = json.loads( hshEnc)
        else: 
            sckt.close()
            context.term()
            argout = { 'result': 'notAlive'}
    else:
        lst = zmq.select([sckt], [], [], timeout)
        if sckt in lst[0]:
            hshEnc = sckt.recv() 
            sckt.close()
            context.term()
            argout = json.loads( hshEnc) 

        else: 
            sckt.close()
            context.term()
            argout = { 'result': 'TgUtils.toMacroExecutor: communication time-out'}

    #print( "TgUtils.toMacroExecutor: received %s" % argout)
    return argout


def isMacroExecutorAlive( node = None):
    '''
    returns True, if there is a SardanaMacroExecutor responding to the isAlive prompt
    '''
    hsh = toMacroExecutor( { 'isAlive': True}, node = node, testAlive = False)
    if hsh[ 'result'] == 'notAlive':
        return False
    else:
        return True

def replaceNumpyArrays( hsh): 
    """
    find numpy arrays in the hsh and replace the by lists
    """
    for k in list( hsh.keys()): 
        if type( hsh[ k]) is dict:
            replaceNumpyArrays( hsh[ k])
            continue
        if type( hsh[ k]) is list:
            for elm in hsh[ k]: 
                if type( elm) is dict:
                    replaceNumpyArrays( elm)
        if type( hsh[ k]) is np.ndarray: 
            #
            # Images, that have been created by tolist() need width and height
            # if width and height are not supplied, take them from .shape
            #
            if len( hsh[ k].shape) == 2:
                if not 'width' in hsh: 
                    hsh[ 'width'] = hsh[ k].shape[0]
                if not 'height' in hsh: 
                    hsh[ 'height'] = hsh[ k].shape[1]
            hsh[ k] = hsh[ k].tolist()

    return
#
# The Eiger interface
#

import requests
import urllib

try:
    # For Python 3.0 and later
    from urllib.request import urlopen
except ImportError:
    # Fall back to Python 2's urllib2
    from urllib2 import urlopen


EIGER_DETECTORS= { 
    'p02e2x4m': { 
        'hostname': 'haspp02oh1', 
        'detector': 'p02/eiger/e4m', 
        'filewriter': 'p02/eiger_filewriter/e4m', 
        'dataURL': 'http://haspp07e4m.desy.de/data'}, 
    #
    # Eiger1, haspp021e1mw
    #
    'p021e1mw': { 
        'hostname': 'haspp021ch1', 
        'detector': 'p02/eiger/e1mw', 
        'filewriter': 'p02/eiger_filewriter/e1mw', 
        'dataURL': 'http://haspp021e1mw.desy.de/data'}, 
    #
    # Eiger1, hzgpp03e9m, Anton Davydok
    #
    'p03e9m': { 
        'hostname': 'haspp03nano', 
        'detector': 'p03nano/eigerdectris/exp.01', 
        'filewriter': 'p03nano/eigerfilewriter/lab.01', 
        'dataURL': 'http://hzgpp03e9m.desy.de/data'}, 
    #
    # Eiger1, Simplon 1.6.0
    #
    'p06p029racke4m': { 
        'hostname': 'hasp029rack', 
        'detector': 'p06/eigerdectris/exp.02', 
        'filewriter': 'p06/eigerfilewriter/exp.02', 
        'dataURL': 'http://haspp06e4m.desy.de/data'}, 
    'p07e2x4m': { 
        'hostname': 'haspp07eh2', 
        'detector': 'p07/eiger/e4m', 
        'filewriter': 'p07/eiger_filewriter/e4m', 
        'dataURL': 'http://haspp07e4m.desy.de/data'}, 
#    'p08e1m': { 
#        'hostname': 'haspp08mono', 
#        'detector': 'p08/eigerdectris/exp.01', 
#        'filewriter': 'p08/eigerfilewriter/exp.01'}, 
    'p08e2x1m_dev': { 
        'hostname': 'haspp08dev', 
        'detector': 'p08/eiger/e1m', 
        'filewriter': 'p08/eiger_filewriter/e1m', 
        'dataURL': 'http://haspp08e1m.desy.de/data'}, 
    'p08e2x1m': { 
        'hostname': 'haspp08mono', 
        'detector': 'p08/eiger/e1m', 
        'filewriter': 'p08/eiger_filewriter/e1m', 
        'dataURL': 'http://haspp08e1m.desy.de/data'}, 
    'p10e4m': { 
        'hostname': 'haspp10opt', 
        'detector': 'p10/eigerdectris/opt.01', 
        'filewriter': 'p10/eigerfilewriter/opt.01',
        'dataURL': 'http://haspp10e4m.desy.de/data'}, 
    'p10e500': { 
        'hostname': 'haspp10opt', 
        'detector': 'p10/eigerdectris/opt.02', 
        'filewriter': 'p10/eigerfilewriter/opt.02',
        'dataURL': 'http://haspp10e500.desy.de/data'}, 
#
# hostname: TANGO_HOST
#
    'p11e2x16m': { 
        'hostname': 'haspp11oh', 
        'detector': 'p11/eigerdectris/exp.01', 
        'filewriter': 'p11/eigerfilewriter/exp.01',
        'dataURL': 'http://haspp11e16m-100g.desy.de/data'}, 
#
#    'p11e2x16m': { 
#        'hostname': 'haspp11oh', 
#        'detector': 'p11/eiger/eh.01', 
#        'filewriter': 'p11/eiger_filewriter/eh.01'}, 
#    'p11e2x16ms': { 
#        'hostname': 'haspp11oh', 
#        'detector': 'p11/simplon_detector/test.01', 
#        'filewriter': 'p11/simplon_filewriter/test.01'}, 
#
    'p21e2x4m': { 
        'hostname': 'hasep21eh3', 
        'detector': 'p21/eiger/e4m', 
        'filewriter': 'p21/eiger_filewriter/e4m', 
        'dataURL': 'http://hasep21e4m-100g.desy.de/data'}, 
    'p23e2x1mw': { 
        'hostname': 'hasep23oh', 
        'detector': 'p23/eigerdectris/eh.01', 
        'filewriter': 'p23/eigerfilewriter/eh.01', 
        'dataURL': 'http://hasep23e1mw.desy.de/data'},   
    'p62e2x4m': { 
        'hostname': 'hasnp62eh', 
        'detector': 'p62/eiger/e4m', 
        'filewriter': 'p62/eiger_filewriter/e4m',
        'outputRegister': 'p62/register/eh.out01',
        'detectorBusy': 'p62/register/eh.in01',
        'dataURL': 'http://hasnp62e4m.desy.de/data'}, 
    'p62e2x9m': { 
        'hostname': 'hasnp62eh', 
        'detector': 'p62/eiger/e9m', 
        'filewriter': 'p62/eiger_filewriter/e9m',
        'dataURL': 'http://hasnp62e9m.desy.de/data'}, 
    'p64e2x9m': { 
        'hostname': 'hasnp64et', 
        'detector': 'petra3/eiger/e9m', 
        'filewriter': 'petra3/eiger_filewriter/e9m',
        'dataURL': 'http://hasnp64eiger9m.desy.de/data'}, 
}

class Eiger(): 
    def __init__( self, name, macro = None): 

        self.name = name

        if self.name not in EIGER_DETECTORS: 
            if macro: 
                macro.output( "TgUtils.Eiger: %s not in EIGER_DETECTORS" % self.name)
            else: 
                print( "TgUtils.Eiger: %s not in EIGER_DETECTORS" % self.name)
            raise ValueError( "TgUtils.Eiger: %s not in EIGER_DETECTORS" % self.name)

        self.deviceName = "%s:10000/%s" % ( EIGER_DETECTORS[ self.name][ 'hostname'],
                                                 EIGER_DETECTORS[ self.name][ 'detector'])
        self.filewriterName = "%s:10000/%s" % ( EIGER_DETECTORS[ self.name][ 'hostname'],
                                                     EIGER_DETECTORS[ self.name][ 'filewriter'])
        if 'outputRegister' in EIGER_DETECTORS[ self.name]: 
            self.outputRegisterName = "%s:10000/%s" % ( EIGER_DETECTORS[ self.name][ 'hostname'],
                                                        EIGER_DETECTORS[ self.name][ 'outputRegister'])
            self.outputRegister = _PyTango.DeviceProxy( self.outputRegisterName)
        if 'detectorBusy' in EIGER_DETECTORS[ self.name]: 
            self.detectorBusyName = "%s:10000/%s" % ( EIGER_DETECTORS[ self.name][ 'hostname'],
                                                      EIGER_DETECTORS[ self.name][ 'detectorBusy'])
            self.detectorBusy = _PyTango.DeviceProxy( self.detectorBusyName)
        self.APIVersion = getDeviceProperty( EIGER_DETECTORS[ self.name][ 'detector'], 
                                                       "APIVersion", 
                                                       EIGER_DETECTORS[ self.name][ 'hostname'])
        self.dataURL = EIGER_DETECTORS[ self.name][ 'dataURL']

        self.device    = _PyTango.DeviceProxy( self.deviceName)
        self.filewriter = _PyTango.DeviceProxy( self.filewriterName)
        try: 
            self.Description = self.device.Description
        except: 
            self.Description = "None"
        if macro: 
            self.macro = macro
        else: 
            self.macro = None
        return 

    def initDetector( self): 
        '''
        this function is executed after the server is started
        '''
        self.device.CountTime = 1.
        self.device.CountTimeInte = 1.
        self.writer( "Eiger.init: CountTime  %g" % self.device.CountTime) 
        self.device.FrameTime = self.device.CountTime + self.device.FrameTimeMin
        self.writer( "Eiger.init: FrameTime  %g" % self.device.FrameTime) 
        self.device.NbImages = 1
        self.writer( "Eiger.init: NbImages   %d" % self.device.NbImages) 
        self.device.NbTriggers = 1
        self.writer( "Eiger.init: NbTriggers %d" % self.device.NbTriggers) 
        self.device.TriggerMode = 'ints'
        self.writer( "Eiger.init: TriggerMode %s" % self.device.TriggerMode) 

        dct = getEnv( 'EigerPars_%s' % self.name) 

        if dct is None: 
            setDefaults( self.name)

        self.filewriter.FilenamePattern = "current/raw/SingleShots/%s/%s_$id" % (self.name, dct[ 'Prefix'])
        self.writer( "Eiger.init: FW FilenamePattern %s" % self.filewriter.FilenamePattern)

        self.filewriter.Mode = 'enabled'
        self.writer( "Eiger.init: FW mode %s" % self.filewriter.Mode)

        self.filewriter.ImagesPerFile = 1
        self.writer( "Eiger.init: FW ImagesPerFile %d" % self.filewriter.ImagesPerFile)

        return 

    def writer( self, msg): 

        if self.macro is not None: 
            self.macro.output( msg)
        else:
            print( msg)

        return 

    def setDefaults( self, name): 
        '''
        The dictionary EigerPars_p62e2x4m contains attribute values 
        which are written to the server when a run starts. 
        This function sets the dictionary to defaults.
        '''
        dct = {}
        dct[ 'CountTime'] = 1.321
        dct[ 'EnergyThreshold'] = 4020.
        dct[ 'PhotonEnergy'] = 8980.
        
        dct[ 'ImagesPerFile'] = 1
        dct[ 'NbImages'] = 1
        dct[ 'NbTriggers'] = 1
        
        dct[ 'TriggerMode'] = 'ints'
        dct[ 'Prefix'] = 'tst'

        varName = "EigerPars_%s" % name
        setEnv( varName, dct)
        d = getEnv( varName)
        if d is None: 
            print( "TgUtils.setDefaults: no MacroServer found")
            return 

        for k, v in d.items(): 
            self.writer( "%-20s: %s" % (k, v))

        return 

    def readDetector( self): 
        '''
        reads certain attributes from the device and the filewriter
        '''
        self.writer( "")
        self.writer( "Read selected attributed from %s " %self.name)
        self.writer( "  Device              %s " %self.deviceName)
        self.writer( "  Filewriter          %s " %self.filewriterName)
        self.writer( " ")
        self.writer( "  CountTime           %g" % self.device.CountTime) 
        self.writer( "  CountTimeInte       %g" % self.device.CountTimeInte) 
        self.writer( "  NbImages            %d" % self.device.NbImages) 
        self.writer( "  NbTriggers          %d" % self.device.NbTriggers) 
        self.writer( "  TriggerMode         %s" % self.device.TriggerMode) 
        #
        # 2.3.2021: isArmedFlag added for p08, 'try' can be out if all servers are re-started
        #
        try: 
            self.writer( "  isArmedFlag         %s" % repr( self.device.isArmedFlag))
        except: 
            pass
        self.writer( "  State               %s" % repr( self.device.state()))
        self.writer( "  Status               %s" % repr( self.device.status()))
        self.writer( "")

        self.writer( "  FW FilenamePattern  %s" % self.filewriter.FilenamePattern)
        self.writer( "  FW mode             %s" % self.filewriter.Mode)
        self.writer( "  FW ImagesPerFile    %d" % self.filewriter.ImagesPerFile)
        self.writer( "  FW State            %s" % repr( self.filewriter.state()))
        self.writer( "  FW Status            %s" % repr( self.filewriter.status()))
        self.writer( "")

        return 

    def saveCLIArgs( self, args) :
        '''
        save attributes in the EigerPar MS environment variable

        return True, if somethings changed
        '''

        argout = False

        dct = getEnv( 'EigerPars_%s' % self.name) 

        if dct is None: 
            self.setDefaults( self.name)
            dct = getEnv( 'EigerPars_%s' % self.name) 
            if dct is None: 
                print( "TgUtils.saveCLIArgs: no Macroserver found") 
                return 

        if args.Prefix is not None: 
            dct[ 'Prefix'] = args.Prefix

        #
        # the time the detector counts photons
        #
        if args.CountTime is not None: 
            dct[ 'CountTime'] = float( args.CountTime)
            argout = True
        if 'CountTime' not in dct:
            dct[ 'CountTime'] = None

        if args.ImagesPerFile is not None: 
            dct[ 'ImagesPerFile'] = args.ImagesPerFile
            argout = True
        if 'ImagesPerFile' not in dct:
            dct[ 'ImagesPerFile'] = None
        #
        # the x-ray energy of the experiment
        #
        if args.PhotonEnergy is not None: 
            dct[ 'PhotonEnergy'] = float( args.PhotonEnergy)
            argout = True
        if 'PhotonEnergy' not in dct:
            dct[ 'PhotonEnergy'] = None
        #
        # The number of images in a series of images, after a trigger
        #
        #
        if args.EnergyThreshold is not None: 
            dct[ 'EnergyThreshold'] = float( args.EnergyThreshold)
            argout = True
        if 'EnergyThreshold' not in dct:
            dct[ 'EnergyThreshold'] = None

        if args.NbImages is not None: 
            dct[ 'NbImages'] = float( args.NbImages)
            argout = True
        if 'NbImages' not in dct:
            dct[ 'NbImages'] = None
        #
        # NbTriggers > 1, several trigger commands or external trigger pulses per arm/disarm sequence. 
        # This mode allows recording several series of NbImages with the same parameters. 
        # The resulting number of frames is product of NbTrigger and NbImages. In external 
        # enable modes the parameter NbImages is ignored (i.e. always 1) and the
        # number of frames therefore has to be configured using the detector configuration parameter ntrigger.
        #
        if args.NbTriggers is not None: 
            dct[ 'NbTriggers'] = float( args.NbTriggers)
            argout = True
        if 'NbTriggers' not in dct:
            dct[ 'NbTriggers'] = None

        if args.TriggerMode is not None:
            if args.TriggerMode.lower() not in [ 'ints', 'exts']: 
                self.writer( "saveCLIArgs: wrong TriggerMode %s ('ints', 'exts')" % args.TriggerMode)
                return False
            dct[ 'TriggerMode'] = args.TriggerMode
            argout = True

        setEnv( 'EigerPars_%s' % self.name, dct)

        return argout

    def storeVar( self, varName, varValue) :
        '''
        store variables is the dictionary
        '''
        dct = getEnv( 'EigerPars_%s' % self.name) 

        if dct is None: 
            self.setDefaults( self.name)
            dct = getEnv( 'EigerPars_%s' % self.name) 

        if varName in [ 'Prefix', 'TriggerMode']: 
            dct[ varName] = varValue
        elif varName in [ 'ImagesPerFile', 'NbImages', 'NbTriggers']: 
            dct[ varName] = int( varValue)
        elif varName in [ 'EnergyThreshhold', 'CountTime', 'PhotonEnergy']: 
            dct[ varName] = float( varValue)
        else: 
            self.writer( "TgUtils.Eiger.storeVars: unknown %s" % varName)
            return False

        setEnv( 'EigerPars_%s' % self.name, dct)

        return 

    def writeAttrs( self): 

        dct = getEnv( 'EigerPars_%s' % self.name)
        #self.writer( "writeAttrs \n%s" % dct_print2str( dct)) 

        #
        # PhotonEnergy and EnergyThreshold are tricky to set.
        # Debian-9: Changing these attributes seems to take
        #           a while and the CountTime is somehow 
        #           changed.
        #
        if dct[ 'PhotonEnergy'] != self.device.PhotonEnergy: 
            self.writer( "Eiger.writeAttrs: PhotonEnergy to %g" % ( dct[ 'PhotonEnergy']))
            self.device.write_attribute("PhotonEnergy", float( dct[ 'PhotonEnergy']))
            _time.sleep(1) 

        if dct[ 'EnergyThreshold'] != self.device.EnergyThreshold: 
            self.writer( "Eiger.writeAttrs: EnergyThreshold to %g" % ( dct[ 'EnergyThreshold']))
            self.device.write_attribute("EnergyThreshold", float( dct[ 'EnergyThreshold']))
            _time.sleep(1) 

        self.device.CountTime = float( dct[ 'CountTime'])
        self.writer( "Eiger.writeAttrs: CountTime to %g" % ( self.device.CountTime))
        self.device.CountTimeInte = float( dct[ 'CountTime'])
        self.writer( "Eiger.writeAttrs: CountTimeInte to %g" % ( self.device.CountTime))
        #
        # trigger mode
        #
        self.writer( "Eiger.writeAttrs: TriggerMode to %s" % ( dct[ 'TriggerMode']))
        self.device.write_attribute("TriggerMode", dct[ 'TriggerMode'])


        #
        #  NbTriggers == nbFrames, NbImages == 1
        #    one frame per trigger, expecting nbFrames triggers, SW or HW 
        #  NbTriggers == 1, NbImages == NbFrames
        #    nbFrames for a single trigger SW or HW
        #
        self.writer( "Eiger.writeAttrs: NbTriggers to %d" % ( dct[ 'NbTriggers']))
        self.device.write_attribute("NbTriggers", dct[ 'NbTriggers'])
        self.writer( "Eiger.writeAttrs: NbImages to %d" % ( dct[ 'NbImages']))
        self.device.write_attribute("NbImages", dct[ 'NbImages'])

        #
        # define the images per file. Default is all images in one file
        #
        # be sure to enable the file writer. Must be done once after TS start
        #
        self.writer( "Eiger.writeAttrs: ImagesPerFile to %d" % ( int( dct[ 'ImagesPerFile'])))
        self.filewriter.write_attribute("ImagesPerFile", int( dct[ 'ImagesPerFile']))
        temp = "current/raw/SingleShots/%s/%s_$id" % (self.name, dct[ 'Prefix'])
        self.writer( "Eiger.writeAttrs: FilenamePattern to %s" % ( temp))
        self.filewriter.FilenamePattern = temp

        return 

    def displayEigerPars( self):

        varName = 'EigerPars_%s' % self.name
        dct = getEnv( varName)
        if dct is None: 
            return 
        self.writer( "") 
        self.writer( "The contents of EigerPars_%s" % self.name) 
        self.writer( "(MacroServer environment variable)")
        self.writer( "  Name                : %s" % (self.name))
        self.writer( "  APIVersion          : %s" % (self.APIVersion))
        self.writer( "  Description         : %s" % (self.Description))
        self.writer( "  DataURL             : %s" % (self.dataURL))
        self.writer( "  DeviceName          : %s" % (self.deviceName))
        self.writer( "  FilewriterName      : %s" % (self.filewriterName))
        self.writer( "  FilewriterMode      : %s" % (self.filewriter.mode))
        self.writer( "")

        for k, v in sorted( dct.items()): 
            self.writer( "  %-20s: %s" % (k, v))

        return 

    def crawler( self, url, execFunction): 
        '''
        crawl through the files in the DCU and execute execFunction for each of them

        execFunction
            eiger.listFunc
            eiger.deleteFunc
            eiger.deleteDirFunc
            eiger.downloadFunc
            eiger.downloadFunc_dldir (DownloadDirectory, Tango server attribute)

        '''
        self.writer( "crawler: url %s " % url)
        #
        # urlcontent is a byte array
        #
        try: 
            urlcontent = urlopen( url).read()
        except Exception as e: 
            print( "TgUtils.crawler: failed to urlopen %s" % url)
            print( repr( e))
            return

        #self.writer( "urlcontent: %s " % urlcontent)
        dirs = []
        fileNames = []
        #
        # convert byte-array to string
        #
        for line in urlcontent.decode( "utf-8").split( "\n"): 
            #self.writer( "TgUtils: line %s" % (line))
            #
            # lines are ignore, if 
            #   - 'Parent Directory' is in the line
            #   - '..' is in the line
            #   - 'a ref' is not in the line
            #
            if line.find( "Parent Directory") > 0: 
                continue
            if line.find( "..") > 0: 
                continue
            if line.find( 'a href') == -1: 
                continue

            #self.writer( "TgUtils: selected line %s" % repr( line))
            lst = _re.findall( '<a href=.*</a>',line)
            #
            # linkName can point to a file or a folder
            #
            #print( "TgUtils: lst %s" % repr( lst))
            linkName = lst[0].split( "\"")[1]
            #
            # we have this overlap between url and link name
            # url: http://hasnp62e4m.desy.de/data/current/raw 
            # /data/current/raw/kkk_382_data_000001.h5
            #
            # fName should be:
            #   http://hasnp62e4m.desy.de/data/current/raw/kkk_382_data_000001.h5
            #
            if linkName[0] == '/': 
                #
                # ['', 'data', 'current', 'kkk_384_master.h5']
                #
                lst = linkName.split( '/')
                #
                # remove empty elements
                #
                lst = [ elm for elm in lst if len( elm) > 0]
                if url[ -1] == '/':
                    linkName = url + lst[-1]
                else: 
                    linkName = url + "/" + lst[-1]

            #
            # if '.h5' is not in the line, assume that it is a folder
            #
            if linkName.find( ".h5") == -1: 
                dirs.append( linkName)
            else: 
                #
                # on haspp10opt (Debian-9, Eiger1) linkName is something
                # like tst_8_data_000007.h5
                # on hasnp62eh (Debian-10, Eiger2) it is 
                # http://hasnp62e4m.desy.de/data/current/raw/tst_00086/eiger2_4m/tst_201_data_000001.h5
                #
                if linkName.find( "http") == -1: 
                    #
                    # the next if-statement was necessary because of this case at p10: 
                    #  url http://haspp10e4m.desy.de/data linkName series_5_data_000001.h5
                    #
                    if url[-1] != '/' and linkName[0] != '/':
                        linkName = url + '/' + linkName
                    else:
                        linkName = url + linkName
                fileNames.append( linkName)
                #self.writer( "TgUtils.Eiger.crawler: fName %s %s " % (url, repr( linkName)))

        for fileName in fileNames:
            execFunction( fileName)

        for dir in dirs: 
            #
            # on eiger1 we get current/
            # instead of http://hasnp62e4m.desy.de/data/current/
            #
            if dir.find( 'data') == -1: 
                if url[-1] != '/':
                    dir = url + "/" + dir
                else: 
                    dir = url + dir
            self.crawler( dir, execFunction)

        if execFunction == self.deleteDirFunc: 
            lst = url.split( '/')
            lst = [ elm for elm in lst if len( elm) > 0]
            #
            # do not delete the toplevel folder http://hasnp62e4m.desy.de/data
            #
            if lst[-1] != 'data': 
                self.writer( "crawler: deleting %s" % url)
                requests.delete( url)
        return 

    def listFunc( self, linkName): 
        self.writer( "  listFunc: %s" % linkName)
        return 

    def deleteFunc( self, linkName): 
        self.writer( "  deleteFunc: %s" % linkName)
        try: 
            requests.delete( linkName)
        except Exception as e: 
            print( "TgUtils.Eiger.deleteFunc: Failed to delete %s" % linkName)
            print( "TgUtils.Eiger.deleteFunc: %s" % repr( e))
        return 

    def deleteDirFunc( self, linkName): 
        self.writer( "  deleteDirFunc: %s" % linkName)
        requests.delete( linkName)
        return 

    def downloadFunc_scandir( self, linkName): 
        '''
        download files. Since the 'data' directory seem to be always
        present on the DCUs, it will not be used for the destination

          http://hasnp62e4m.desy.de/data/current/raw/prefix_scanID/detName/prefix_scanID_$id_data_000001.h5 -> 
            ScanDir/current/raw/prefix_scanID/detName/prefix_scanID_$id_data_000001.h
        '''

        downloadDir = getEnv( "ScanDir")
        self.writer( "downloadFunc: ScanDir: %s" % downloadDir)
        
        return self.downloadFunc( linkName, downloadDir)


    def downloadFunc_dldir( self, linkName): 
        '''
        download files. Since the 'data' directory seem to be always
        present on the DCUs, it will not be used for the destination

          http://hasnp62e4m.desy.de/data/current/raw/prefix_scanID/detName/prefix_scanID_$id_data_000001.h5 -> 
            DownloadDirectory/current/raw/prefix_scanID/detName/prefix_scanID_$id_data_000001.h
        '''

        try: 
            downloadDir = self.device.DownloadDirectory
        except Exception as e: 
            print( "TgUtils.downloadFunc_dldir: failed")
            print( "%s" % repr( e))
            return

        self.writer( "downloadFunc_dl_dir: DownloadDirectory %s" % downloadDir)
        return self.downloadFunc( linkName, downloadDir)

    def downloadFunc( self, linkName, downloadDir): 
        '''
        download files. Since the 'data' directory seem to be always
        present on the DCUs, it will not be used for the destination

          http://hasnp62e4m.desy.de/data/current/raw/prefix_scanID/detName/prefix_scanID_$id_data_000001.h5 -> 
            ScanDir/current/raw/prefix_scanID/detName/prefix_scanID_$id_data_000001.h
        '''

        base = _os.path.basename( linkName)
        #
        # http://hasnp62e4m.desy.de/data/current/raw/kkk_388_data_000001.h5 -> 
        #   ['http:', '', 'hasnp62e4m.desy.de', 'data', 'current', 'raw', 'kkk_388_data_000001.h5']
        #
        lst = linkName.split( '/')
        lst = [ elm for elm in lst if len( elm) > 0]

        flag = False
        dirTemp = downloadDir
        for i in range( len( lst)): 
            if lst[i].find( '.h5') != -1: 
                break
            #
            # find 'data'. from then on subdirectories will be created, 
            # if necessary
            #
            if lst[i] == "data":
                flag == True
                continue

            if flag: 
                dirTemp = dirTemp + "/" + lst[i]
                if not _os.path.exists( dirTemp): 
                    self.writer( "downloadFunc: creating %s" % dirTemp)
                    try: 
                        _os.mkdir( dirTemp)
                    except Exception as e: 
                        self.writer( "downloadFunc: failed to create %s" % dirTemp)
                        self.writer( repr( e))
                        return 
                flag = True
        if dirTemp[-1] == '/':
            dest = '%s%s' % (dirTemp, base)
        else:
            dest = '%s/%s' % (dirTemp, base)
                
        self.writer( "downLoad %ss -> %s" % ( linkName, dest))
        
        if _sys.version_info.major > 2: 
            urllib.request.urlretrieve( linkName, dest, reporthook = self.dlProgress)
        else: 
            urllib.urlretrieve( linkName, dest, reporthook = self.dlProgress)
        return

    def dlProgress( self, count, blockSize, totalSize):
        percent = int(count*blockSize*100/totalSize)
        #self.writer( "count %s, blockSize %s, totalSize %s" % (count, blockSize, totalSize))
        if percent > 100:
            percent = 100
        _sys.stdout.write("\r %d%%" % percent)
        _sys.stdout.flush()
        return 

    def arm( self): 
        '''
        call arm() for the device and wait for the filewriter to become MOVING
        '''
        self.device.Arm()
        #
        # the filewriter becomes MOVING upon arm()
        #
        while self.filewriter.state() != _PyTango.DevState.MOVING: 
            _time.sleep( 0.1) 
            _sys.stdout.write(".")
            _sys.stdout.flush()
        self.writer( "")
        return 

    def disarm( self): 
        '''
        call disarm() for the device and wait for the filewriter to become MOVING
        '''
        self.device.Disarm()
        #
        # the filewriter becomes ON upon disarm()
        #
        while self.filewriter.state() != _PyTango.DevState.ON: 
            _time.sleep( 0.1) 
            _sys.stdout.write(".")
            _sys.stdout.flush()
        self.writer( "")
        return 

    def runInts( self): 
        '''
        execute a complete measurement.
        '''
        #
        # see, if the filewrite is enabled
        #
        if self.filewriter.mode == 'disabled': 
            self.writer( "runInts: filewriter mode to 'enabled'")
            self.filewriter.mode == 'enabled'

        self.disarm()

        dct = getEnv( 'EigerPars_%s' % self.name)

        self.device.write_attribute("TriggerMode", 'ints')

        self.filewriter.FilenamePattern = "current/raw/SingleShots/%s/%s_$id" % (self.name, dct[ 'Prefix'])
        self.writer( "runInts: FilenamePattern %s" % self.filewriter.FilenamePattern)

        self.device.write_attribute("CountTime", float( dct[ 'CountTime']))
        self.writer( "runInts: CountTime %g" % self.device.CountTime)

        self.device.write_attribute("FrameTime", (float( dct[ 'CountTime']) + float(self.device.FrameTimeMin)))
        self.writer( "runInts: FrameTime %g" % self.device.FrameTime)

        self.device.write_attribute("NbImages", int( dct[ 'NbImages']))
        self.writer( "runInts: NbImages %d" % self.device.NbImages)

        self.device.write_attribute("NbTriggers", int( dct[ 'NbTriggers']))
        self.writer( "runInts: NbTriggers %d" % self.device.NbTriggers)

        self.filewriter.write_attribute( "ImagesPerFile", int( dct[ 'ImagesPerFile']))
        self.writer( "runInts: ImagesPerFile %d" % int( self.filewriter.ImagesPerFile))

        setEnv( 'EigerPars_%s' % self.name, dct)

        self.writer( "runInts: arm()")
        self.arm()
        while self.device.state() != _PyTango.DevState.ON: 
            _time.sleep( 0.1)

        for i in range( int( dct[ 'NbTriggers'])): 
            self.writer( "\ntrigger %s" % i)
            self.device.trigger()
            #
            # arm(): 
            #   fw to MOVING, device: ON and status() to 'ready'
            # trigger()
            #   state() to MOVING, status() to 'acquire'
            #   goes to 'ready' until NbTriggers (idle)
            #
            startTime = _time.time()
            timeout = (self.device.CountTime + self.device.FrameTimeMin) * self.device.NbImages
            timeUpdate = 0.1
            if timeout > 2: 
                timeUpdate = 1
            while self.device.state() == _PyTango.DevState.MOVING:
                _sys.stdout.write("\r %g/%g   " % ((_time.time() - startTime), timeout))
                _sys.stdout.flush()
                if (_time.time() - startTime) > (timeout + 1): 
                    self.writer( "runInts: Time-out, device state does not become MOVING")
                    self.device.disarm()
                    self.writer( "runInts: NbImages %d" % 1)
                    self.device.write_attribute("NbImages", 1)
                    self.writer( "runInts: NbTriggers %d" % 1)
                    self.device.write_attribute("NbTriggers", 1)
                    return
                _time.sleep( timeUpdate) 
            if self.device.status() == 'idle':
                break

        self.writer( "")
        startTime = _time.time()
        while self.filewriter.state() != _PyTango.DevState.ON:
            _time.sleep( 0.1) 
            _sys.stdout.write(".")
            _sys.stdout.flush()
            #if (_time.time() - startTime) > TIMEOUT: 
            #    self.writer( "runInts: Time-out, FW state does not become ON")
            #    self.device.disarm()
            #    self.writer( "runInts: NbImages %d" % 1)
            #    self.device.write_attribute("NbImages", 1)
            #    self.writer( "runInts: NbTriggers %d" % 1)
            #    self.device.write_attribute("NbTriggers", 1)
            #    return
        self.writer( "\nFW state() ON after %g s" % (_time.time() - startTime))
        self.writer( "")
            
        #
        # Disarm the detector (to ensure files are finalized and closed).
        #
        self.writer( "runInts: disarm()")
        self.device.disarm()

        self.device.write_attribute("NbImages", 1)
        self.writer( "runInts: NbImages %d" % self.device.NbImages)

        self.device.write_attribute("NbTriggers", 1)
        self.writer( "runInts: NbTriggers %d" % self.device.NbTriggers)

        self.writer( "")
        return 

    def runExts( self, realFlag): 
        '''
        execute a complete measurement.
        '''
        #
        # see, if the filewrite is enabled
        #
        if self.filewriter.mode == 'disabled': 
            self.writer( "runInts: filewriter mode to 'enabled'")
            self.filewriter.mode == 'enabled'

        self.disarm()

        dct = getEnv( 'EigerPars_%s' % self.name)

        self.device.TriggerMode = 'exts'
        self.writer( "runExts: TriggerMode %s" % self.device.TriggerMode)

        self.filewriter.FilenamePattern = "current/raw/SingleShots/%s/%s_$id" % (self.name, dct[ 'Prefix'])
        self.writer( "runExts: FilenamePattern %s" % self.filewriter.FilenamePattern)

        self.device.write_attribute("CountTime", float( dct[ 'CountTime']))
        self.writer( "runExts: CountTime %g" % self.device.CountTime)

        self.device.write_attribute("FrameTime", (float( dct[ 'CountTime']) + float(self.device.FrameTimeMin)))
        self.writer( "runExts: FrameTime %g" % self.device.FrameTime)

        self.device.write_attribute("NbImages", dct[ 'NbImages'])
        self.writer( "runExts: NbImages %d" % self.device.NbImages)

        self.device.write_attribute("NbTriggers", int( dct[ 'NbTriggers']))
        self.writer( "runExts: NbTriggers %d" % self.device.NbTriggers)

        self.filewriter.write_attribute( "ImagesPerFile", int( dct[ 'ImagesPerFile']))
        self.writer( "runExts: ImagesPerFile %d" % int( self.filewriter.ImagesPerFile))

        setEnv( 'EigerPars_%s' % self.name, dct)

        self.writer( "runExts: arm()")
        self.arm()

        #
        # waiting for external triggers
        #
        timeUpdate = 0.5
        timeout = (self.device.CountTime + self.device.FrameTimeMin) * self.device.NbImages

        if not realFlag: 
            self.writer( "Simulating external triggers")
            for i in range( int( dct[ 'NbTriggers'])): 
                #
                # wait for the detector to become idle before
                # generating a new trigger
                #
                while self.detectorBusy == 1:
                    self.writer( "detector busy")
                    _time.sleep( 0.1)
                self.writer( "Trigger %d" % i)
                self.outputRegister.Value = 1
                _time.sleep( 0.01)
                self.outputRegister.Value = 0
                _time.sleep( timeout + 0.5)
        else: 
            self.writer( "Waiting for external triggers")

        while self.filewriter.state() != _PyTango.DevState.ON:
            _time.sleep( timeUpdate) 
        #
        # Disarm the detector (to ensure files are finalized and closed).
        #
        self.writer( "runExts: disarm()")
        self.device.disarm()

        self.device.write_attribute("NbImages", 1)
        self.writer( "runExts: NbImages %d" % self.device.NbImages)

        self.device.write_attribute("NbTriggers", 1)
        self.writer( "runExts: NbTriggers %d" % self.device.NbTriggers)

        self.device.TriggerMode = 'ints'
        self.writer( "runExts: TriggerMode %s" % self.device.TriggerMode)

        self.writer( "")
        return 

def registerPyspMonitor( hostName, zmqPort):
    '''
    store hostName, zmqPort in RegisteredPyspMonitors
    '''
    temp = "%s_%d" % ( hostName, zmqPort)

    arr = getEnv( "RegisteredPyspMonitors")
    if arr is None: 
        arr = []
        arr.append( temp)
    else: 
        if temp not in arr: 
            arr.append( temp)
            
    setEnv( "RegisteredPyspMonitors", arr)
    
    return 

def deRegisterPyspMonitor( hostName, zmqPort):
    '''
    re-register hostName, zmqPort in RegisteredPyspMonitors
    '''

    temp = "%s_%d" % ( hostName, zmqPort)

    arr = getEnv( "RegisteredPyspMonitors")
    if arr is None: 
        return 

    if temp not in arr: 
        return 

    for i in range( len( arr)): 
        if arr[i] == temp:
            del arr[i]
            break

    setEnv( "RegisteredPyspMonitors", arr)
    
    return 

def proxyHasAttribute( proxy, attr): 
    """    
    return True if the attr is in the attribute list of proxy
    the purpose of this function is to avoid hasattr() which 
    throws exceptions
    the comparison is done case-insensitive

    In [2]: import HasyUtils
    In [3]: import PyTango
    In [4]: proxy = PyTango.DeviceProxy( "p09/motor/eh.01")
    In [5]: HasyUtils.proxyHasAttribute( proxy, 'position')
    Out[5]: True
    In [6]: HasyUtils.proxyHasAttribute( proxy, 'positionn')
    Out[6]: False

    """
    #
    # also possible
    #
    #return attr.lower() in list( map( str.lower, p.get_attribute_list()))

    return attr.lower() in list( map( lambda x: x.lower(), proxy.get_attribute_list()))

    
def createPreScanSnapshotDct(): 
    '''
    return a dictionary containing the information from PreScanSnapshot

    intended to be used by FioAdditions
    '''
    hsh = {}
    devices = getEnv( "PreScanSnapshot")
    if devices is None:
        return { "status": "no PreScanSnapshot"}
    
    for elm in devices:
        lst = elm[0].split( "/")
        #
        # 'tango://haso107d10:10000/expchan/tangoattributectctrl/9'
        #
        if len( lst) == 6:
            p = _PyTango.DeviceProxy( elm[0])
            if lst[3] == 'expchan':
                a = p.read_attribute( 'Value').value
            elif lst[3] == 'motor':
                a = p.read_attribute( 'Position').value
            else:
                a = None
        #
        # 'tango://haso107d10.desy.de:10000/p09/counter/eh.01/Counts'
        #
        elif len( elm[0].split( "/")) == 7:
            #
            # 'tango://haso107d10.desy.de:10000/p09/counter/eh.01'
            #
            name = "tango://" + "/".join(lst[2:6])
            p = _PyTango.DeviceProxy( name)
            a = p.read_attribute( lst[6]).value
        if a is not None: 
            hsh[ elm[1]] = a
        else: 
            hsh[ elm[1]] = "*** error ***"

    return hsh

def _printOrOutput( msg, macro, debug): 

    if not debug:
        return 

    if macro: 
        macro.output( msg)
    else: 
        print( msg)
    return 

def checkZMX( zmxName, macro = None, debug = True): 
    """
    receives a ZMX name checks the device

      if Deactivation != 0: 
        Deactivation = 0

      if error != 'no error': 
        reset() is called then sleep(1)
        if error != 'no error': 
          return False
        else:
          return True
      return True
    """
    _printOrOutput( "TgUtils.checkZMX: %s" % zmxName, macro, debug)

    try: 
        proxyZMX = _PyTango.DeviceProxy( zmxName) 
    except Exception as e:
        _printOrOutput( "TgUtils.checkZMX: failed to connect to %s" % zmxName, macro, debug)
        return False

    try: 
        deact = proxyZMX.Deactivation
        if deact != 0:
            proxyZMX.Deactivation = 0
            _printOrOutput( "checkZMX: setting Deactivation to 0", macro, debug)
    except: 
        _printOrOutput( "TgUtils.checkZMX: failed to access deactivation, return True", macro, debug)
        return True
        
       
    err = proxyZMX.Error
    if err.lower() != 'no error': 
        _printOrOutput( "checkZMX: error %s, calling reset()" % err, macro, debug)
        proxyZMX.command_inout("Reset")
        _time.sleep(1)
        err = proxyZMX.Error
        if err.lower() != 'no error': 
            _printOrOutput( "checkZMX: error %s, after reset(), return False" % err, macro, debug)
            return False
    _printOrOutput( "TgUtils.checkZMX: return True", macro, debug)
    return True

def checkMotorZMX( motorName, macro = None, debug = True): 
    """
    Inputs: 
      - motorName is a Pool device or a Tango device
      - macro is used for macro.output()
      - debug controls the debug

    If poolDevice (eh_mot65), we connect to the related TangoDevice and read the SubDevices, 
    If Tango device (p09/motor/eh.65), we read the subDevices directly

    Loop over the subDevices and search for the ZMXDevice property and connect to the ZMX 
    and execute checkZMX()

    This function can be used in hooks, e.g.: 

class gh_pre_scan(Macro):
    def run( self):
        self.output( "general_features.pre_scan hook")
        scanInfo = HasyUtils.createScanInfo( self.getParentMacro().getCommand())
        for motRec in scanInfo[ 'motors']:
            if not HasyUtils.checkMotorZMX( motRec[ 'name'], macro = self, debug = True):
                self.abort()
        ....            
    """
    _printOrOutput( "TgUtils.checkMotorZMX: %s" % motorName, macro, debug)

    try: 
        poolDeviceProxy = _PyTango.DeviceProxy( motorName)
    except Exception as e: 
        _printOrOutput( "TgUtils.checkMotorZMX: failed to connect to %s" % motorName, macro, debug)
        return False

    #
    # in case of pool devices, we have one hop extra, tangoDevice
    #
    if hasattr( poolDeviceProxy, 'TangoDevice'):
        _printOrOutput( "TgUtils.checkMotorZMX: %s has the TangoDevice attribute, follow" % motorName, macro, debug)

        try: 
            tangoDevice = poolDeviceProxy.TangoDevice
        except Exception as e: 
            _printOrOutput( "TgUtils.checkMotorZMX: failed to connect to TangoDevice", macro, debug)
            return True

        _printOrOutput( "TgUtils.checkMotorZMX: reading subDevices from %s" % tangoDevice, macro, debug)
        subDevs = getDeviceProperty( tangoDevice, '__SubDevices')
        print( "TgUtils.checkMotorZMX tangoDevice %s subDevices %s" % (tangoDevice, repr( subDevs)))
        motorDevice = tangoDevice
    #
    # tangoDevice
    #
    else: 
        _printOrOutput( "TgUtils.checkMotorZMX: %s has no TangoDevice attr" % motorName, macro, debug)
        subDevs = getDeviceProperty( motorName, '__SubDevices')
        print( "TgUtils.checkMotorZMX device %s subDevices %s" % (motorName, repr( subDevs)))
        motorDevice = motorName

    #
    # no ZMXDevice, return true
    #
    if len( subDevs) == 0:
        _printOrOutput( "TgUtils.checkMotorZMX: %s has no SubDevices, return True" % motorDevice, macro, debug)
        return True

    _printOrOutput( "TgUtils.checkMotorZMX: subDevices %s" % repr( subDevs), macro, debug)
    for subDev in subDevs: 
        _printOrOutput( "TgUtils.checkMotorZMX: loop subDev %s" % subDev, macro, debug)

        if getClassNameByDevice( subDev) != 'OmsVme58':
            _printOrOutput( "TgUtils.checkMotorZMX:   %s not an OmsVme58, continue" % subDev, macro, debug)
            continue
        lst = getDeviceProperty( motorDevice, 'ZMXDevice')
        if len( lst) == 0: 
            _printOrOutput( "TgUtils.checkMotorZMX:   %s no prop ZMXDevice, continue" % subDev, macro, debug)
            continue
        if not checkZMX( lst[0], macro, debug):
            return False

    _printOrOutput( "TgUtils.checkMotorZMX: return True", macro, debug)

    return True

def checkPortZmqAvailable( portNo): 
    """
    returns True, if portNo is available (ready to be used) False otherwise
    """
    import socket, zmq
    hostName = socket.gethostname()                      # haso107tk
    hostNameIP = socket.gethostbyname( socket.getfqdn()) # '131.169.221.83'
    
    context = zmq.Context()
    sckt = context.socket(zmq.REP)
    try:
        sckt.bind( "tcp://%s:%d" % ( hostNameIP, portNo))
    except Exception as e:
        #print( "TgUtils.checkPortNo, %s" % repr( e))
        sckt.close()
        return False

    sckt.close()
    context.destroy()

    return True
        
def checkOnlineSardanaXml( fileName = "/online_dir/onlineSardana.xml"):
    """
    reads onlineSardana.xml and detects conflicts: 
      identical controller names with different hostnames (P10-reported bug)

      reason for this issue: controller names are not hostname-sensitive
    """
    print("TgUtils.checkOnlineSardanaXml: reading %s" % fileName)
    lst = getOnlineXML( fileName)
    dct = {}
    alreadyPrinted = []
    flagFound = False
    for hsh in lst:
        #print( "TgUtils.checkOnlineSardanaXml: %s " % hsh)
        if hsh[ 'module'].lower() == 'tangoattributectctrl':
            continue
        if 'controller' not in hsh:
            print( "TgUtils.checkOnlineXml: %s has no controller key, ignore" % hsh[ 'name'])
            continue
        try: 
            #print( "SardanaConvert.checkOnlineSardanaXml: %s controller %s" % ( hsh[ 'name'], hsh[ 'controller']))
            #
            # MGs have controllers == None
            #
            if hsh[ 'controller'].lower() == 'none': 
                continue
            #
            # the 'controller' entry of a diffractometer is used to contruct the 
            # motor names in pooltools._createDiffractometer(). this is different
            # from other 'controller' entries. so we can ignore the diffractometers
            # when we check for controller conflicts
            #
            if hsh[ 'type'].lower() == 'diffractometercontroller':
                #print( "storing controller %s, diffractometer, not stored" % ( hsh[ 'name']))
                continue

            if hsh[ 'controller'] not in dct:
                #print( "storing controller %s for %s" % ( repr( hsh[ 'controller']),hsh[ 'name']))
                dct[ hsh[ 'controller']] = ( hsh[ 'name'], hsh[ 'hostname'], hsh[ 'type'])
            else:
                #print( "%s exists already, for %s and now %s, type %s vs. %s" % 
                #       ( hsh[ 'controller'], dct[ hsh[ 'controller']][0], hsh[ 'name'], hsh[ 'type'], dct[ hsh[ 'controller']][2]))
                if dct[ hsh[ 'controller']][1] != hsh[ 'hostname']:
                    #print( "TgUtils.checkOnlineSardanaXml: controller %s, used already for a different host" % 
                    #       repr( hsh[ 'controller']))
                    flagFound = True
                    if hsh[ 'controller'] not in alreadyPrinted:
                        alreadyPrinted.append( hsh[ 'controller'])
                        print( "TgUtils.checkOnlineSardanaXml, conflict: %s, %s, %s and %s, %s" % 
                               ( hsh[ 'name'], hsh[ 'controller'], hsh[ 'hostname'], 
                                 dct[ hsh[ 'controller']][0], dct[ hsh[ 'controller']][1]))
        except Exception as e:
            pass
            print( "%s Exception %s" % ( hsh[ 'name'], repr( e)))
            print( "%s" % ( repr( hsh)))

    if flagFound:
        return False
    return True
         

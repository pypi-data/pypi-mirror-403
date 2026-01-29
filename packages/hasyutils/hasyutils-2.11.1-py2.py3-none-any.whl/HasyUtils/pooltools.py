#!/usr/bin/env python
""" this module contains functions that manage the Pool and MacroServer """
try:
    import PyTango
except:
    pass
import json
import string
import re
#import HasyUtils
import math, time, string, os, sys
import platform
from . import MgUtils
from . import TgUtils
from . import OtherUtils
#
db = None

# debug flag
debug = False

def deleteLocalPoolDevices():
    """Delete all devices in local Pools."""
    try:
        #
        # e.g. p09/pool/haso107d1
        #
        poolNames = TgUtils.getLivingLocalPoolNames()
    except:
        return 1

    if not poolNames:
        return 1

    for poolName in poolNames:
        try:
            pool = PyTango.DeviceProxy( poolName)
        except:
            print( "failed to get proxy to %s" % poolName)
            return 0
        #
        # the pool might be alive
        #
        try:
            print( "pooltools.deleteLocalPoolDevices: deleting devices on %s" % pool.name())
        except PyTango.DevFailed as e:
            print( "\npooltools.deleteLocalPoolDevices: trouble with %s continuing" % pool.dev_name())
            return 1

        flagFailed = False
        for listName in [ "MeasurementGroupList", "AcqChannelList", "ControllerList",
                          "ExpChannelList", "IORegisterList", "MotorList"]:
            try:
                elmList = pool.read_attribute( listName)
            except:
                print( "pooltools.deleteLocalPoolDevices.py:: failed to read_attribute %s on %s " % ( listName, poolName))
                continue
            #print( "pooltools.deleteLocalPoolDevices: elmList %s" % elmList)
            if elmList.dim_x == 0:
                continue
            if elmList.value is None:
                continue
            print( "pooltools.deleteLocalPoolDevices: %s" % listName)
            for elm in elmList.value:
                hsh = json.loads( elm)
                try:
                    print( "pooltools.deleteLocalPoolDevices: deleteElement %s" % str( hsh[ 'name']))
                    pool.DeleteElement( str(hsh['name']))
                except:
                    #
                    # here we arrive because devices cannot be deleted becaus of dependencies
                    #
                    print( "pooltools.deleteLocalPoolDevices:: %s failed to DeleteElement %s, dependency issue?" % (poolName, hsh[ 'name']))
                    #print( repr( sys.exc_info()))
                    flagFailed = True
        if flagFailed:
            for listName in [ "MeasurementGroupList", "AcqChannelList", "ControllerList",
                              "ExpChannelList", "IORegisterList", "MotorList"]:
                try:
                    elmList = pool.read_attribute( listName)
                except:
                    print( "pooltools.deleteLocalPoolDevices.py:: failed to read_attribute %s on %s " % ( listName, poolName))
                    continue
                #print( "pooltools.deleteLocalPoolDevices: elmList %s" % elmList)
                #if elmList.dim_x == 0:
                #    continue
                if elmList.value is None:
                    continue
                print( "pooltools.deleteLocalPoolDevices: %s" % listName)
                for elm in elmList.value:
                    hsh = json.loads( elm)
                    try:
                        pool.DeleteElement( str(hsh['name']))
                    except:
                        print( "pooltools.deleteLocalPoolDevices: %s failed to DeleteElement %s (2nd try)" % (poolName, hsh[ 'name']))
                        #print( repr( sys.exc_info()))

    print( "pooltools.deleteLocalPoolDevices DONE")
    return 1

def listPool( pool, **a):
    """Print the pool contents.

       optional: controller list and information about the devices
    """

    if 'displayController' in a and a['displayController']:
        for listName in [ "ControllerList"]:
            print( "  %s" % listName)
            elmList = pool.read_attribute( listName)
            lst = list(elmList.value)
            lst.sort()
            for elm in lst:
                hsh = json.loads( elm)
                proxy = PyTango.DeviceProxy( str(hsh['full_name']))
                sys.stdout.write( "  %25s %s" % (str(hsh['name']), proxy.state()))
                lst = proxy.ElementList
                if type(lst).__name__ == 'NoneType':
                    print( " None")
                    continue
                sys.stdout.write( ", %2d devices: " % len(lst))
                if len(lst) < 5:
                    sys.stdout.write( ", ". join( lst) + "\n")
                else:
                    sys.stdout.write( str( lst[0]) + ", " + str( lst[1]) + " ... " + str(lst[-1]) + "\n")
    #
    # the MeasurementGroupList gets a special treatment because we
    # want to see the elements
    #
    for listName in [ "MeasurementGroupList"]:
        elmList = pool.read_attribute( listName)
        if type(elmList.value).__name__ == "NoneType":
            print( "  <empty>")
            continue
        if len(elmList.value) == 1:
            hsh = json.loads( elmList.value[0])
            print( "  MG: %s" % hsh['elements'])
        else:
            for elm in elmList.value:
                hsh = json.loads( elm)
                print( "  %s %s" % (str(hsh['name']), hsh['elements']))
    return 1

def poolIsEmpty( pool):
    """Return True, if the Pool is empty."""
    for listName in [ "AcqChannelList", "ExpChannelList",
                      "IORegisterList", "MotorList", "MeasurementGroupList"]:
        try:
            elmList = pool.read_attribute( listName)
        except:
            return True
        if elmList.dim_x != 0:
            return False
    return True

def deleteLocalPools():
    """Delete the local Pools from the Tango DB"""

    for serverName in TgUtils.getLocalPoolServers():
        print( "pooltools.deleteLocalPools: " + serverName)
        db.delete_server( serverName)
        db.delete_server_info( serverName)
        #print( "pooltools.deleteLocalPools: deleted " + serverName)
    return 1

def deleteLocalMacroServers():
    """Delete all MacroServers from the Tango DB"""

    for serverName in TgUtils.getLocalMacroServerServers():
        db.delete_server( serverName)
        db.delete_server_info( serverName)
        print( "pooltools.deleteLOcalMacroServers: deleted " + serverName)
    return 1

    macroServers = TgUtils.getLocalMacroServersNames()
    for macroServer in macroServers:
        proxy = PyTango.DeviceProxy( macroServer)
        serverName = proxy.info().server_id
        db.delete_server( serverName)
        db.delete_server_info( serverName)
        print( "pooltools.deleteLocalMacroServer: deleted " + serverName)
    return 1

def deleteMacroServers():
    """Delete all MacroServers from the Tango DB"""

    for serverName in TgUtils.getMacroServerServers():
        db.delete_server( serverName)
        db.delete_server_info( serverName)
        print( "pooltools.deleteMacroServers: deleted " + serverName)
    return 1

    macroServers = TgUtils.getMacroServersNames()
    for macroServer in macroServers:
        proxy = PyTango.DeviceProxy( macroServer)
        serverName = proxy.info().server_id
        db.delete_server( serverName)
        db.delete_server_info( serverName)
        print( "pooltools.deleteMacroServer: deleted " + serverName)
    return 1

def findPoolNamesInXml( xmlFile):
    """Return a list of Pools which are in the xmlFile>"""
    hshList = TgUtils.getOnlineXML( xmlFile = xmlFile)
    pools = []
    for hsh in hshList:
        #
        # {'channel': '1',
        # 'control': 'tango',
        # 'controller': 'tangoattributectctrl',
        # 'device': 'p09/motor/d1.01',
        # 'hostname': 'haso107d1:10000',
        # 'module': 'tangoattributectctrl',
        # 'name': 'mot01_position',
        # 'pool': 'pool_haso107d1',
        # 'rootdevicename': 'p09/motor/d1.01/position',
        # 'type': 'counter'}
        #
        if 'pool' in hsh:
            if not hsh['pool'] in pools:
                pools.append( hsh['pool'])
    pools.sort()
    return pools
# Linux hastodt 3.2.0-4-amd6

poolPathPython3 = [
    '/usr/lib/python3/dist-packages/sardana/PoolController/motor',
    '/usr/lib/python3/dist-packages/sardana/PoolController/communication',
    '/usr/lib/python3/dist-packages/sardana/PoolController/countertimer',
    '/usr/lib/python3/dist-packages/sardana/PoolController/ioregister',
    '/usr/lib/python3/dist-packages/sardana/PoolController/oned',
    '/usr/lib/python3/dist-packages/sardana/PoolController/pseudocounter',
    '/usr/lib/python3/dist-packages/sardana/PoolController/pseudomotor',
    '/usr/lib/python3/dist-packages/sardana/PoolController/twod',
    '/usr/lib/python3/dist-packages/sardana/PoolController/zerod',
    # '/usr/lib/python3/dist-packages/sardana/PoolController/sardana_tango',
    '/usr/local/experiment/sardana/PoolController',
    ]

def createPools( **a):
    """
    Create one pool per experiment PC
    """

    #print( "createPools: %s" % repr( a))

    if 'beamline' not in a:
        print( "pooltools.createPool: no beamline given ")
        return 0
    if 'xmlFile' not in a:
        print( "pooltools.createPool: no xmlFile given ")
        return 0

    pools = findPoolNamesInXml( a['xmlFile'])
    if( len( pools) > 1):
        print( "pooltools.createPools: online.xml contains > 1 pools %s" % pools)
    print( "pooltools.createPools pools: %s" % pools)

    hostname = TgUtils.getHostname()

    if len(pools) == 0:
        pool =  "pool_%s" % TgUtils.getHostname()
    else:
        pool = pools[0]

    #
    # pool: pool_haspp02ch1a or pool_haso107klx_a (!! 2 underscores!!)
    #
    instance = '_'.join(pool.split('_')[1:])
    instance = instance.lower()
    if instance == "":
        print( "pooltools.createPools: wrong syntax %s" % pool)
        return 0
    serverName  = 'Pool/' + instance
    deviceName  = "%s/pool/%s" % (a['beamline'], instance)

    #
    if os.path.exists('/usr/lib/python3/dist-packages/sardana_tango/ctrl'):
        poolPathPython3.append('/usr/lib/python3/dist-packages/sardana_tango/ctrl')
    elif os.path.exists('/usr/lib/python3/dist-packages/sardana/PoolController/sardana_tango'):
        poolPathPython3.append('/usr/lib/python3/dist-packages/sardana/PoolController/sardana_tango')
    #
    if os.path.exists( '/usr/lib/python3/dist-packages/sardana_limaccd/ctrl'):
        poolPathPython3.append( '/usr/lib/python3/dist-packages/sardana_limaccd/ctrl')
    #
    # 4.2.2025: for jan kotanski
    #
    if os.path.exists( '/usr/lib/python3/dist-packages/sardana/PoolController/newportxps'):
        poolPathPython3.append( '/usr/lib/python3/dist-packages/sardana/PoolController/newportxps')
    #
    # aliasName: "e1_pool"
    #
    #
    # bugfix 7.10.2014
    # do not create the [pool, if it exists already, but make sure it's running
    #
    aliasName  = "pool_%s" % (instance)
    if serverName in db.get_server_list(serverName):
        print( "pooltools.createPools: DB contains already " + serverName)
    else:
        di = PyTango.DbDevInfo()
        di.name, di._class, di.server = deviceName, 'Pool', serverName
        db.add_device(di)
        db.put_device_property( deviceName, {'PoolPath': poolPathPython3})

        db.put_device_property( deviceName, {'Version': ['0.3.0']})
        db.put_device_alias( deviceName, aliasName)
        print( "pooltools.createPools: Created %s on %s" % (deviceName, serverName))

    serverInfo = db.get_server_info( serverName)
    TgUtils.putServerInfo( name = serverName,
                           host = TgUtils.getHostnameLong(),
                           mode = 1,
                           level =2 )
    if not TgUtils.startServer( serverName):
        print( "pooltools.createPools: failed to start %s " % serverName)
        sys.exit( 255)

    info = db.import_device( deviceName)
    for i in range(5):
        if info.exported == 1:
            print( "pooltools.createPools: %s is exported" % deviceName)
            break
        else:
            print( "pooltools.createPools: %s is NOT exported" % deviceName)
        time.sleep( 1)
        info = db.import_device( deviceName)

    print( "pooltools.createPools DONE")
    return True

#
#
#
def _createMacroServerDevice( serverName, beamline):

    hostname = TgUtils.getHostname()

    macroPath = [
        '/home/experiment/sardana/desy_macros',
        ]
    macroPath64 = [
        '/home/experiment/sardana/desy_macros',
        ]
#
# 19.7.2017
# the paths:
#   '/usr/lib/python2.7/dist-packages/sardana/macroserver',
#   '/usr/lib/python2.7/dist-packages/sardana/macroserver/macros'
# should not be in the MacroPath, the first because it contains
# only base classes, the second is respected anyway
#
    macroPathDebian = [
        '/usr/lib/python2.7/dist-packages/sardana/sardana-macros/DESY_general',
        ]
    macroPathDebianPython3 = [
        '/usr/lib/python3/dist-packages/sardana/sardana-macros/DESY_general',
        ]
    #
    # add the GPFS ro directory to the MacroPath
    #
    bl = beamline.lower()
    if bl == 'p03nano':
        bl = 'p03'
    elif hostname.lower().find( 'haspp02ch1') == 0:
        bl = 'p02.1'
    elif hostname.lower().find( 'haspp02ch2') == 0:
        bl = 'p02.2'

    #
    # 15.3.2016 removed the os.path.exists(), just to increase simpliicity
    #
    pname = "/common/" + bl + "/sardanaMacros"
    macroPathDebian.append( pname)

    pool = "pool_%s" % hostname

    msName  = "%s/macroserver/%s.01" % (beamline, hostname)

    # Add directory to PYTHONPATH for external modules used in macros
    # python_path_ext = ["/beamline/PythonPath", "/data/beamline/PythonPath"]
    python_path_ext = ["/common/" + bl + "/PythonPath", "/gpfs/local/PythonPath","/bl_documents/PythonPath"]

    #
    # add an additional path for user-specific macros: /home/p09user/sardanaMacros
    #
    if os.path.exists('/home/etc/local_user'):
        local_user = os.popen('cat /home/etc/local_user').read().strip()
        macroPath.append("/home/" + local_user + "/sardanaMacros")
        macroPath64.append("/home/" + local_user + "/sardanaMacros")
        macroPathDebian.append("/home/" + local_user + "/sardanaMacros")
        macroPathDebianPython3.append("/home/" + local_user + "/sardanaMacros")
        # Add directory to PYTHONPATH for general functions
        python_path_ext.append("/home/" + local_user + "/sardanaMacros/generalFunctions")

    macroPath.append("/gpfs/local/sardanaMacros")
    macroPath64.append("/gpfs/local/sardanaMacros")
    macroPathDebian.append("/gpfs/local/sardanaMacros")
    macroPathDebianPython3.append("/gpfs/local/sardanaMacros")

    macroPath.append("/bl_documents/sardanaMacros")
    macroPath64.append("/bl_documents/sardanaMacros")
    macroPathDebian.append("/bl_documents/sardanaMacros")
    macroPathDebianPython3.append("/bl_documents/sardanaMacros")
    #
    if os.path.exists( '/usr/lib/python3/dist-packages/sardana_limaccd/macro'):
        macroPathDebianPython3.append("/usr/lib/python3/dist-packages/sardana_limaccd/macro")

    # Add directory for external recorders
    if sys.version_info.major == 3:
        ext_recorders_path = ["/usr/lib/python3/dist-packages/sardananxsrecorder"]
        if os.path.exists(
                "/usr/lib/python3/dist-packages/sardana_blissdata/recorder"):
            ext_recorders_path.append(
                "/usr/lib/python3/dist-packages/sardana_blissdata/recorder")
    else:
        ext_recorders_path = ["/usr/lib/python2.7/dist-packages/sardananxsrecorder"]

    di = PyTango.DbDevInfo()
    di.name, di._class, di.server = msName, 'MacroServer', serverName
    db.add_device(di)

    if sys.version_info.major == 3:
        db.put_device_property( msName, {'MacroPath': macroPathDebianPython3})
    elif platform.platform().find( 'debian') > 0:
        db.put_device_property( msName, {'MacroPath': macroPathDebian})
    elif platform.platform().find( 'x86_64') > 0:
        db.put_device_property( msName, {'MacroPath': macroPath64})
    else:
        db.put_device_property( msName, {'MacroPath': macroPath})

    db.put_device_property( msName, {'PythonPath': python_path_ext})
    db.put_device_property( msName, {'RecorderPath': ext_recorders_path})
    db.put_device_property( msName, {'PoolNames': pool})
    db.put_device_property( msName, {'Version': ['0.2.0']})


    # Change default file for saving Spock environment

    env_path = "/online_dir/MacroServer"
    if not os.path.exists(env_path):
        os.makedirs(env_path)
    env_path = env_path + "/macroserver.properties"
    db.put_device_property( msName, {'EnvironmentDb': env_path})
    print( "pooltools.createMacroServerDevice: EnvironmentDB %s" % ( env_path))
    print( "pooltools.createMacroServerDevice: Created %s on %s" % ( msName, serverName))

    for i in range( 1, 4):
        doorName  = "%s/door/%s.%02d" % (beamline, hostname, i)
        di.name, di._class, di.server = doorName, 'Door', serverName
        db.add_device(di)
        db.put_device_property( doorName, {'MacroServerName': msName})
        db.put_device_property( doorName, {'Id': '%d' % i})

def createMacroServer( **a):
    """Create MacroServer, e.g. MacroServer/haspp09"""
    if 'beamline' not in a:
        print( "pooltools.createMacroServer: no beamline given ")
        return 0

    hostname = TgUtils.getHostname()

    serverName  = 'MacroServer/' + hostname

    if not serverName in db.get_server_list(serverName):
        print( "pooltools.createMacroServer: creating " + serverName)
        _createMacroServerDevice( serverName, a['beamline'])

    serverInfo = db.get_server_info( serverName)
    time.sleep(3)
    TgUtils.putServerInfo( name = serverName,
                           host = TgUtils.getHostnameLong(),
                           mode = 1,
                           level = 3)
    if not TgUtils.startServer( serverName):
        print( "pooltools.createMacroServer failed to start %s" % serverName)
        sys.exit(255)
    return True

def _getControllerList( pool):
    """Return the list of controllers."""
    try:
        controllerList = pool.ControllerList
    except PyTango.DevFailed as e:
        PyTango.Except.print_exception( e)
        return 0
    existingControllers = []
    if not controllerList is None:
        for elm in controllerList:
            dct = json.loads( elm)
            existingControllers.append( dct['name'])
    return existingControllers

def _findGenericControllerDct( ctrlName):
    """Return the dictionary belonging to a controller.

       ctrlName is e.g. tm_exp or dggs_exp_t01
    """
    #
    # the controllers dictionary has the generic controller names as keys
    #
    controllers = {
        "amptekoned": { 'type': "OneDExpChannel", 'lib': "AmptekOneDCtrl.py", 'class': "AmptekOneDCtrl"},
        "amptekroi": { 'type': "CTExpChannel", 'lib': "AmptekPX5CoTiCtrl.py", 'class': "AmptekPX5CounterTimerController"},
        "am_": { 'type': "Motor", 'lib': "HasyMotorCtrl.py", 'class': "HasyMotorCtrl"},
        "analyzer": { 'type': "Motor", 'lib': "HasyMotorCtrl.py", 'class': "HasyMotorCtrl"},
        "analyzerep01": { 'type': "Motor", 'lib': "HasyMotorCtrl.py", 'class': "HasyMotorCtrl"},
        "bscryotempcontrolp01": { 'type': "Motor", 'lib': "HasyMotorCtrl.py", 'class': "HasyMotorCtrl"},
        "atto300": { 'type': "Motor", 'lib': "HasyMotorCtrl.py", 'class': "HasyMotorCtrl"},
        "cube": { 'type': "Motor", 'lib': "HasyMotorCtrl.py", 'class': "HasyMotorCtrl"},
        "dcm_energy": { 'type': "Motor", 'lib': "HasyMotorCtrl.py", 'class': "HasyMotorCtrl"},
        "dcm_motor": { 'type': "Motor", 'lib': "HasyMotorCtrl.py", 'class': "HasyMotorCtrl"},
        "smaract": { 'type': "Motor", 'lib': "HasyMotorCtrl.py", 'class': "HasyMotorCtrl"},
        "dgg2": { 'type': "CTExpChannel", 'lib': "DGG2Ctrl.py", 'class': "DGG2Ctrl"},
        "pilctimer": { 'type': "CTExpChannel", 'lib': "pilcTimerCtrl.py", 'class': "pilcTimerCtrl"},
        "pilcgtvfctimer": { 'type': "CTExpChannel", 'lib': "PiLCGTVFCTimerCtrl.py", 'class': "PiLCGTVFCTimerCtrl"},
        "elom": { 'type': "Motor", 'lib': "HasyMotorCtrl.py", 'class': "HasyMotorCtrl"},
        "galil_dmc": { 'type': "Motor", 'lib': "HasyMotorCtrl.py", 'class': "HasyMotorCtrl"},
        "hexa": { 'type': "Motor", 'lib': "HasyMotorCtrl.py", 'class': "HasyMotorCtrl"},
        "kohzu": { 'type': "Motor", 'lib': "HasyMotorCtrl.py", 'class': "HasyMotorCtrl"},
        "phymotion": { 'type': "Motor", 'lib': "HasyMotorCtrl.py", 'class': "HasyMotorCtrl"},
        "lom": { 'type': "Motor", 'lib': "HasyMotorCtrl.py", 'class': "HasyMotorCtrl"},
        "mca8701": { 'type': "OneDExpChannel", 'lib': "HasyOneDCtrl.py", 'class': "HasyOneDCtrl"},
        "vonedexecutor": { 'type': "OneDExpChannel", 'lib': "HasyOneDCtrl.py", 'class': "HasyOneDCtrl"},
        "hydraharp400": { 'type': "OneDExpChannel", 'lib': "HasyOneDCtrl.py", 'class': "HasyOneDCtrl"},
        "kromoroi": { 'type': "CTExpChannel", 'lib': "KromoRoIsCtrl.py", 'class': "KromoRoIsCtrl"},
        "kromo_": { 'type': "OneDExpChannel", 'lib': "HasyOneDCtrl.py", 'class': "HasyOneDCtrl"},
        "avantes_": { 'type': "OneDExpChannel", 'lib': "HasyOneDCtrl.py", 'class': "HasyOneDCtrl"},
        "cobold_": { 'type': "OneDExpChannel", 'lib': "HasyOneDCtrl.py", 'class': "HasyOneDCtrl"},
        "spadq_": { 'type': "OneDExpChannel", 'lib': "SPADQOneDCtrl.py", 'class': "SPADQOneDCtrl"},
        "pscameravhrroi": { 'type': "CTExpChannel", 'lib': "PSCameraVHRRoIsCtrl.py", 'class': "PSCameraVHRRoIsCtrl"},
        "mult": { 'type': "Motor", 'lib': "HasyMotorCtrl.py", 'class': "HasyMotorCtrl"},
        "oms58": { 'type': "Motor", 'lib': "HasyMotorCtrl.py", 'class': "HasyMotorCtrl"},
        "omsvme58": { 'type': "Motor", 'lib': "HasyMotorCtrl.py", 'class': "HasyMotorCtrl"},
        "petra": { 'type': "CTExpChannel", 'lib': "SIS3820Ctrl.py", 'class': "SIS3820Ctrl"},
        "phaseretarder": { 'type': "Motor", 'lib': "HasyMotorCtrl.py", 'class': "HasyMotorCtrl"},
        "pie710": { 'type': "Motor", 'lib': "HasyMotorCtrl.py", 'class': "HasyMotorCtrl"},
        "pie712": { 'type': "Motor", 'lib': "HasyMotorCtrl.py", 'class': "HasyMotorCtrl"},
        "piezonv40": { 'type': "Motor", 'lib': "HasyMotorCtrl.py", 'class': "HasyMotorCtrl"},
        "diffracmu": { 'type': "Motor", 'lib': "HasyMotorCtrl.py", 'class': "HasyMotorCtrl"},
        "pilatus": { 'type': "TwoDExpChannel", 'lib': "Pilatus.py", 'class': "PilatusCtrl"},
        "maranax": { 'type': "TwoDExpChannel", 'lib': "MaranaX.py", 'class': "MaranaXCtrl"},
        "andorikon": { 'type': "TwoDExpChannel", 'lib': "AndorIkon.py", 'class': "AndorIkonCtrl"},
        "pco": { 'type': "TwoDExpChannel", 'lib': "PCO.py", 'class': "PCOCtrl"},
        "marccd": { 'type': "TwoDExpChannel", 'lib': "MarCCD.py", 'class': "MarCCDCtrl"},
        "perkinelmer": { 'type': "TwoDExpChannel", 'lib': "PerkinElmer.py", 'class': "PerkinElmerCtrl"},
        "hzgdcam": { 'type': "TwoDExpChannel", 'lib': "HzgDcam.py", 'class': "HzgDcamCtrl"},
        "limaccd": { 'type': "TwoDExpChannel", 'lib': "LimaCCD.py", 'class': "LimaCCDCtrl"},
        # udais limsccd controller,
        # LimaCCDTwoDController is defined in /usr/lib/python3/dist-packages/sardana_limaccd/ctrl/LimaCCDCtrl.py
        "limaccd_alba": { 'type': "TwoDExpChannel", 'lib': "LimaCCDCtrl.py", 'class': "LimaCCDTwoDController"},
        "limaroicounter": { 'type': "CTExpChannel", 'lib': "LimaRoICounterCtrl.py", 'class': "LimaRoICounterCtrl"},
        "lcxcamera": { 'type': "TwoDExpChannel", 'lib': "LCXCamera.py", 'class': "LCXCameraCtrl"},
        "tangovimba": { 'type': "TwoDExpChannel", 'lib': "TangoVimba.py", 'class': "TangoVimbaCtrl"},
        "lambda": { 'type': "TwoDExpChannel", 'lib': "Lambda.py", 'class': "LambdaCtrl"},
        "minipix": { 'type': "TwoDExpChannel", 'lib': "MiniPIX.py", 'class': "MiniPIXCtrl"},
        "eigerdectris": { 'type': "TwoDExpChannel", 'lib': "EigerDectris.py", 'class': "EigerDectrisCtrl"},
        "eigerpsi": { 'type': "TwoDExpChannel", 'lib': "EigerPSI.py", 'class': "EigerPSICtrl"},
        "pscameravhr": { 'type': "TwoDExpChannel", 'lib': "PSCameraVHR.py", 'class': "PSCameraVHRCtrl"},
        "dalsa": { 'type': "TwoDExpChannel", 'lib': "DALSA.py", 'class': "DALSACtrl"},
        "greateyes": { 'type': "TwoDExpChannel", 'lib': "GreatEyes.py", 'class': "GreatEyesCtrl"},
        "timepix": { 'type': "TwoDExpChannel", 'lib': "TimePix.py", 'class': "TimePixCtrl"},
        "newportxps": { 'type': "Motor", 'lib': "NewportXPSMotorController.py", 'class': "NewportXPSMotorController"},
        "random": { 'type': "CTExpChannel", 'lib': "SIS3820Ctrl.py", 'class': "SIS3820Ctrl"},
        "sis3302ms1d":{ 'type': "OneDExpChannel", 'lib': "SIS3302MultiScanCtrl.py", 'class': "SIS3302MultiScanCtrl"},
        "sis3302roi1d":{ 'type': "OneDExpChannel", 'lib': "SIS3302Ctrl.py", 'class': "SIS3302Ctrl"},
        # TK 22.9.2021: sis3302roi has been re-activated, works on haso107tk, haspp022ch
        "sis3302roi":{ 'type': "CTExpChannel", 'lib': "SIS3302RoisCtrl.py", 'class': "SIS3302RoisCtrl"},
        # "sis3302_": { 'type': "OneDExpChannel", 'lib': "HasyOneDCtrl.py", 'class': "HasyOneDCtrl"},
        "sis3610in": { 'type': "IORegister", 'lib': "SIS3610Ctrl.py", 'class': "SIS3610Ctrl"},
        "sis3610_labin": { 'type': "IORegister", 'lib': "SIS3610Ctrl.py", 'class': "SIS3610Ctrl"},
        "sis3610out": { 'type': "IORegister", 'lib': "SIS3610Ctrl.py", 'class': "SIS3610Ctrl"},
        "sis3610_labout": { 'type': "IORegister", 'lib': "SIS3610Ctrl.py", 'class': "SIS3610Ctrl"},
        "sis3820": { 'type': "CTExpChannel", 'lib': "SIS3820Ctrl.py", 'class': "SIS3820Ctrl"},
        "sis8800": { 'type': "CTExpChannel", 'lib': "SIS3820Ctrl.py", 'class': "SIS3820Ctrl"},
        "slt": { 'type': "Motor", 'lib': "HasyMotorCtrl.py", 'class': "HasyMotorCtrl"},
        "smarpod": { 'type': "Motor", 'lib': "HasyMotorCtrl.py", 'class': "HasyMotorCtrl"},
        "smchydra": { 'type': "Motor", 'lib': "HasyMotorCtrl.py", 'class': "HasyMotorCtrl"},
        "spk": { 'type': "Motor", 'lib': "HasyMotorCtrl.py", 'class': "HasyMotorCtrl"},
        "tcpipmotor": { 'type': "Motor", 'lib': "HasyMotorCtrl.py", 'class': "HasyMotorCtrl"},
        "nfpaxis": { 'type': "Motor", 'lib': "HasyMotorCtrl.py", 'class': "HasyMotorCtrl"},
        "tip551": { 'type': "Motor", 'lib': "HasyDACCtrl.py", 'class': "HasyDACCtrl"},
        "tip830": { 'type': "ZeroDExpChannel", 'lib': "HasyADCCtrl.py", 'class': "HasyADCCtrl"},
        "tip850adc": { 'type': "ZeroDExpChannel", 'lib': "HasyADCCtrl.py", 'class': "HasyADCCtrl"},
        "tip850dac": { 'type': "ZeroDExpChannel", 'lib': "HasyDACCtrl.py", 'class': "HasyDACCtrl"},
        "tm": { 'type': "Motor", 'lib': "HasyMotorCtrl.py", 'class': "HasyMotorCtrl"},
        "tth": { 'type': "Motor", 'lib': "HasyMotorCtrl.py", 'class': "HasyMotorCtrl"}, # hasgksspp07eh2a
        "vfcadc": { 'type': "CTExpChannel", 'lib': "VFCADCCtrl.py", 'class': "VFCADCCtrl"},
        "vc": { 'type': "CTExpChannel", 'lib': "SIS3820Ctrl.py", 'class': "SIS3820Ctrl"},
        "v260": { 'type': "CTExpChannel", 'lib': "SIS3820Ctrl.py", 'class': "SIS3820Ctrl"},
        "varex2315": { 'type': "TwoDExpChannel", 'lib': "Varex2315Controller.py", 'class': "Varex2315Ctrl"},
        "vdot32in": { 'type': "IORegister", 'lib': "SIS3610Ctrl.py", 'class': "SIS3610Ctrl"},
        "vdot32out": { 'type': "IORegister", 'lib': "SIS3610Ctrl.py", 'class': "SIS3610Ctrl"},
        "vm": { 'type': "Motor", 'lib': "HasyMotorCtrl.py", 'class': "HasyMotorCtrl"},
        "xia": { 'type': "OneDExpChannel", 'lib': "HasyOneDCtrl.py", 'class': "HasyOneDCtrl"},
        "tangoattributectctrl":{ 'type': "CTExpChannel", 'lib': "TangoAttrCTCtrl.py", 'class': "TangoAttrCTController"},
        "tangoattributezerodctrl":{ 'type': "ZeroDExpChannel", 'lib': "TangoAttrZeroDCtrl.py", 'class': "TangoAttrZeroDController"},
        "tangoattributeonedctrl":{ 'type': "OneDExpChannel", 'lib': "TangoAttrOneDCtrl.py", 'class': "TangoAttrOneDController"},
        "tangoattributeiorctrl":{ 'type': "IORegister", 'lib': "TangoAttrIORCtrl.py", 'class': "TangoAttrIORController"},
        "mca8715roi":{ 'type': "CTExpChannel", 'lib': "MCAroisCtrl.py", 'class': "MCAroisCtrl"},
        "mca8715_":{ 'type': "OneDExpChannel", 'lib': "HasyOneDCtrl.py", 'class': "HasyOneDCtrl"},
        "mythenroi":{ 'type': "CTExpChannel", 'lib': "MythenRoisCtrl.py", 'class': "MythenRoisCtrl"},
        "onedroi":{ 'type': "CTExpChannel", 'lib': "HasyRoIsCtrl.py", 'class': "HasyRoIsCtrl"},
        "xmcd":{ 'type': "CTExpChannel", 'lib': "XMCDCtrl.py", 'class': "XMCDCtrl"},
        "mhzdaqp01":{ 'type': "CTExpChannel", 'lib': "MHzDAQp01Ctrl.py", 'class': "MHzDAQp01Ctrl"},
        "pico8742": { 'type': "Motor", 'lib': "HasyMotorCtrl.py", 'class': "HasyMotorCtrl"},
        "oxfcryo700ctrl": { 'type': "Motor", 'lib': "OxfordCryostream700Ctrl.py", 'class': "OxfordCryostream700Ctrl"},
        "xspress3roi": { 'type': "CTExpChannel", 'lib': "Xspress3RoI.py", 'class': "Xspress3RoIsCtrl"},
        }

    argout = None

    if ctrlName.find( 'sis3302roi1d') == 0:
        argout = controllers[ "sis3302roi1d"]
    else:
        for key in controllers:
            #
            # "dgg2_exp_t01".find( "dgg2")
            #
            if ctrlName.find( key) == 0:
                argout = controllers[key]
                break
    # 22.9.2021
    #if ctrlName.lower().find( 'sis3302') != -1:
    #    print( "pooltools, %s argout: %s " % (ctrlName, repr( argout)))
    # pooltools, sis3302roi1deh2a01ctrl argout: {'type': 'OneDExpChannel', 'class': 'SIS3302Ctrl', 'lib': 'SIS3302Ctrl.py'}
    # pooltools, sis3302roi1deh2a01ctrl argout: {'type': 'OneDExpChannel', 'class': 'SIS3302Ctrl', 'lib': 'SIS3302Ctrl.py'}
    #
    # maybe the first part of the controller name is a hostname
    #
    # <<<
    # the following lines have been taken out because of the issue
    # reporte by P01 and P09, #1336541
    #if argout is None:
    #    pos = ctrlName.find( '_')
    #    if pos == -1:
    #        return argout
    #    ctrlName = ctrlName[ pos+1:]
    #    for key in controllers:
    #        #
    #        # "dgg2_exp_t01".find( "dgg2")
    #        #
    #        if ctrlName.find( key) == 0:
    #            argout = controllers[key]
    #            break
    # >>>
    return argout

def _printTangoException( e):
    for arg in e.args:
        print( "  Desc: %s" % (arg.desc))
        #print( "     origin: %s" % (arg.origin))
        #print( "     reason: %s" % (arg.reason))
        #print( "severity: %s" % (arg.severity))
    #PyTango.Except.print_exception( e)
    return

def _createPoolController( proxy, ctrl_lst):
    '''
    no action, if the controller does exist already

    5.9.2018 the pool did not quickly accept controllers
    '''
    retry = False
    for i in range( 3):
        existingControllers = _getControllerList( proxy)
        if ctrl_lst[3] in existingControllers:
            #
            # p09/pool/haso107tk ['CTExpChannel', 'VFCADCCtrl.py', 'VFCADCCtrl', 'vfcadc_d1',
            #                    'RootDeviceName', 'p09/vfc/d1', 'TangoHost', 'haso107tk:10000']
            #
            if retry:
                print( "pooltools.createPoolController: %s %s in existing controllerList (after retry)" %
                       (proxy.name(), ctrl_lst[3]))
                OtherUtils.toAIOLog( "pooltools.createPoolController: %s %s in existing controllerList (after retry)" %
                       (proxy.name(), ctrl_lst[3]))
            return 1
        #
        #print( "+++pooltools.createController: %s %s " %( proxy.name(), ctrl_lst))
        #
        try:
            proxy.CreateController( ctrl_lst)
            if retry:
                print( "pooltools.createPoolController: %s %s OK (after retry)" % (proxy.name(), ctrl_lst[3]))
                OtherUtils.toAIOLog( "pooltools.createPoolController: %s %s OK (after retry)" % (proxy.name(), ctrl_lst[3]))
            else:
                print( "pooltools.createPoolController: %s %s OK " % (proxy.name(), ctrl_lst[3]))
            return 1
        except PyTango.DevFailed as e:
            print( "pooltools.createPoolController: failed to create controller %s" % ctrl_lst)
            _printTangoException( e)
            #PyTango.Except.print_exception( e)
            print( "pooltools.createPoolController: re-trying, sleep(3)")
            OtherUtils.toAIOLog( "pooltools.createPoolController: failed to create controller %s" % ctrl_lst)
            OtherUtils.toAIOLog( "pooltools.createPoolController: re-trying, sleep(3)")
            retry = True
            time.sleep(3)

    print( "pooltools.createPoolController: failed after several retries %s" % ctrl_lst)
    OtherUtils.toAIOLog( "pooltools.createPoolController: failed after several retries %s" % ctrl_lst)
    return 0

def _createPoolElement( proxy, elm_lst):
    '''
    05.09.2018 the pool did not quickly accept devices
    14.10.2020 range(5) to range( 2)
    '''
    retry = 0
    for i in range( 5):
        #
        #  if a device is already in the DB, ...
        #
        try:
            db.import_device( elm_lst[3])
            print( "createPoolElement: %s %s already in DB, retry %d" % (proxy.name(), elm_lst, retry))
            OtherUtils.toAIOLog( "createPoolElement: %s %s already in DB, retry %d" % (proxy.name(), elm_lst, retry))
            return 1
        except:
            pass
        # +++
        #print( "pooltools.createPoolElement: %s %s, retry %d " % ( proxy.name(), elm_lst, retry))

        try:
            proxy.CreateElement( elm_lst)
            if retry:
                print( "createPoolElement: %s %s OK" % (proxy.name(), elm_lst))
                print( "createPoolElement: %s DONE " % ( proxy.name()))
                OtherUtils.toAIOLog( "createPoolElement: %s %s OK" % (proxy.name(), elm_lst))
                OtherUtils.toAIOLog( "createPoolElement: %s DONE " % ( proxy.name()))
            return 1
        except PyTango.DevFailed as e:
            print( "pooltools.createPoolElement: failed to createElement in %s %s " % (proxy.name(), elm_lst))
            s = repr( e)
            if s.find( "value attribute not found") != -1:
                print( "createPoolElement: %s, value attribute not found" % repr( elm_lst))
                return False
            if s.find( "Exception: Controller already contains axis") != -1:
                print( "createPoolElement: %s, value attribute not found" % repr( elm_lst))
                return False
            print( "Exception  %s" % repr( e))
            #_printTangoException( e)
            print( "pooltools.createPoolElement: re-trying, sleep(3)")
            OtherUtils.toAIOLog( "pooltools.createPoolElement: failed to createElement in %s %s " %
                                 (proxy.name(), elm_lst))
            retry += 1
            time.sleep(3)

    print( "pooltools.createPoolElement: failed after several retries %s" % (elm_lst))
    OtherUtils.toAIOLog( "pooltools.createPoolElement: failed after several retries %s" % (elm_lst))
    return 0


def insertControllerAndDevice( poolProxies, poolName, ctrl_lst, elm_lst):
    """
    This function is called with a single controller and a single device
    The controller is created, if it does not exist already

       poolName
         alias like pool_haspp02ch1a
       ctrl_lst:
         ['Motor', 'HasyMotorCtrl.py', 'HasyMotorCtrl', ctrlName, 'RootDeviceName', rootDeviceName, 'TangoHost', tangoHost]
       elm_lst
         ['Motor', 'omsvme58_eh', '64', 'eh_mot64']
    """
    # +++
    if debug:
        print( "\npooltools.insertCtrlAndDev: ctrl: %s" % repr( ctrl_lst))
        print( "pooltools.insertCtrlAndDev: elm:  %s" % repr( elm_lst))
    #
    # find the pool
    #
    flag = 0
    proxy = None
    for p in poolProxies:
        if poolName == p.alias():
            proxy = p
            flag = 1
            break
    if not flag:
        print( "insertControllerAndDevice: no pool %s" % poolName)
        return 0

    #
    # see, if the device has already been defined
    #
    try:
        acqChannelList = proxy.AcqChannelList
    except Exception as e:
        PyTango.Except.print_exception( e)
        print( "pooltools.insertCtrlAndDev: failed to get acqChannelList")
        return 0

    if not acqChannelList is None:
        for elm in acqChannelList:
            hsh = json.loads( elm)
            if hsh['name'] == elm_lst[3]:
                print( "pooltools.insertCtrlAndDev: %s already on %s" % (elm_lst[3], proxy.name()))
                return 1
    #
    # create Pool controller, if it doesn not exist already
    # +++
    # make tangohost part of the controller name
    # otherwise there are problem if exp.01 motors
    # from different host are inserted in the pool
    # because the controller is called omsvme58_exp
    # without any hostname
    #
    #if ctrl_lst[ -2] == 'TangoHost':
    #    tangoHost = ctrl_lst[-1]
    #    if tangoHost.find( ":10000"):
    #        tangoHost = tangoHost.split( ":")[0]
    #    ctrl_lst[3] = "%s_%s" % ( tangoHost, ctrl_lst[3])
    #    elm_lst[1] = "%s_%s" % ( tangoHost, elm_lst[1])

    if not _createPoolController( proxy, ctrl_lst):
        return 0

    if not _createPoolElement( proxy, elm_lst):
        return 0

    return 1

def _reportOfflineDevices( hsh):
    '''
    tell the user, if a device is offline; but continue
    '''
    #print( "pooltools.reportOfflineDevices: %s, %s" % (hsh[ 'name'], hsh[ 'device']))
    lst = hsh[ 'device'].split( "/")
    #
    # pseudomotor devices are not available at this moment
    #
    if lst[0] == "pm" and \
       (lst[1] == "e4chctrl" or
        lst[1] == "e4cctrl" or
        lst[1] == "e6cctrl" or
        lst[1] == "e6c" or
        lst[1] == "e6cctrleh1" or
        lst[1] == "e6cctrleh2" or
        lst[1] == "h4c" or
        lst[1] == "kozhue6cctrl"):
        return
    #
    # deal with e.g.: p09/vmexecutor/eh.02/position
    #
    if len( lst) > 3:
        devNameTemp = "/".join( lst[:-1])
    else:
        devNameTemp = hsh[ 'device']
    try:
        devName = "%s/%s" % ( hsh[ 'hostname'], devNameTemp)
        p = PyTango.DeviceProxy( devName)
        state = p.state()
    except Exception as e:
        print( "pooltools.reportOfflineDevices: error from %s" % (devName))
        print( "          Desc: %s" % (e.args[0].desc))
        #for arg in e.args:
        #    print "          Desc: %s" % (arg.desc)
            #print "origin: %s" % (arg.origin)
            #print "reason: %s" % (arg.reason)
            #print "severity: %s" % (arg.severity)
        return

    if state == PyTango.DevState.FAULT:
        print( "pooltools.reportOfflineDevices: %s in FAULT state" % devName)
        return

    if state == PyTango.DevState.ALARM:
        print( "pooltools.reportOfflineDevices: %s in ALARM state" % devName)
        return
    return

def _checkMotorOnline( hsh):
    '''
    5.3.2020
    fighting the ctrl-c issue:
    check whether motor is online before we create a pool device
      - return True, if hsh does not represent a motor
      - return True, if the state() is not FAULT and not ALARM
    '''

    if not _isAMotor( hsh):
        return True

    if 'ipaddress' in hsh:
        return TgUtils.isAlive( hsh[ 'ipaddress'], hsh[ 'portno'])

    try:
        devName = "%s/%s" % ( hsh[ 'hostname'], hsh[ 'device'])
        p = PyTango.DeviceProxy( devName)
        state = p.state()
    except Exception as e:
        #print( "pooltools.checkMotorOnline: error for %s" % (devName))
        #print( "pooltools.checkMotorOnline: %s" % (repr( e)))
        return False

    if state == PyTango.DevState.FAULT:
        print( "pooltools.checkMotorOnline: %s in FAULT state" % devName)
        return False

    if state == PyTango.DevState.ALARM:
        print( "pooltools.checkMotorOnline: %s in ALARM state" % devName)
        return False

    return True

def _createDevices( hshList):
    """
    Create pool devices, one controller per device.
    """
    #
    # haspp08mono:10000
    #
    # tangoHost = os.getenv('TANGO_HOST').split(':')[0]
    tangoHost = os.getenv('TANGO_HOST')

    poolProxies = getPoolProxies()

    for hsh in hshList:
        # The diffractometer has to be added at the end
        if 'type' in hsh:
            if hsh['type'] == 'diffractometercontroller':
                continue
            if hsh['type'] == 'pseudomotor':
                continue

        if 'controller' not in hsh:
            print( "pooltools.createDevices: Device %s has no controller key, ignore" % hsh['name'])
            continue
        #
        # MGs have no controller key
        #
        if hsh['controller'].lower() == 'none':
            continue
        #
        # the following function matches hsh['controller'] against
        # the keys in controllers, e.g. dgg2_exp_t01 matches dgg2. the
        # function returns a dictionary that contains the controller type,
        # the library file name and the class
        #
        dct = _findGenericControllerDct( hsh['controller'])
        if dct is None:
            print( ">>> pooltools._createDevices: controller %s not among the generic controllers" % hsh['name'])
            continue

        if 'controller' not in hsh:
            print( "pooltools.createDevices: %s %s " % (hsh['name'], "has no controller tag"))
            continue

        if 'rootdevicename' not in hsh:
            print( "pooltools.createDevices: %s %s" % (hsh['name'], "has no rootdevicename tag"))
            continue

        if 'channel' not in hsh:
            print( "pooltools.createDevices: %s %s " % (hsh['name'], "has no channel tag"))
            continue

        if 'pool' not in hsh:
            print( "pooltools.createDevices: %s %s" % (hsh['name'], "has no pool tag"))
            continue

        channel = 1
        #
        # dgg2_exp_t01
        #
        ctrlName = hsh['controller']
        #
        # rootDeviceName can be a complete device name like p09/dgg2/exp.01
        # this is for the one device per controller case and in this case
        # the channel no. is always 1 (for dgg2)
        # rootDeviceName can also be a part of the device name like p09/motor
        # this is for the many devices per controller case and in this case
        # the channel varies
        #
        rootDeviceName = hsh['rootdevicename']
        channel = hsh['channel']
        elm_lst = []
        #
        # ["Motor", "HasyMotorCtrl.py", "HasyMotorCtrl", ctrlName, 'RootDeviceName', rootDeviceName, 'TangoHost', tangoHost]
        # ["CTExpChannel", "HasyScaCtrl.py", "HasyScaCtrl", "sca_exp_mca01_100_200_ctrl", "mca", "exp_mca01", "roi1", "100", "roi2", "200"]
        #
        ctrl_lst = []
        if hsh['module'].lower() == 'amptekroi':
            if 'hostname' in hsh:
                rootDeviceName = "tango://" + hsh['hostname'] + "/" + rootDeviceName
            ctrl_lst = [ dct['type'], dct['lib'], dct['class'], ctrlName, 'deviceName', rootDeviceName]
            channel = "%d" % (int(channel) + 1) # First channel is acquisition time
        elif hsh['module'].lower() == 'limaccd_alba':
            #
            # defctrl  LimaCCDTwoDController limaSardana limaccddevicename haspp08bliss:10000/p08bliss/limaccds/simulator \
            #          latencytime 1 hardwaresavingextraprefix scan_
            # defelem limaeiger limaSardana 1
            # ['TwoDExpChannel', 'Pilatus.py', 'PilatusCtrl', 'pilatus300kpilatusctrl', 'RootDeviceName',
            #  'p09/pilatus/eh.01', 'TangoHost', 'haso107d10:10000']
            # ['TwoDExpChannel', 'pilatus300kpilatusctrl', '1', 'pilatus']
            #
            #ctrl_lst = [ 'LimaCCDTwoDController',  'limaSardana',  'limaccddevicename', 'haspp08bliss:10000/p08bliss/limaccds/simulator',
            #              'latencytime', '1',  'hardwaresavingextraprefix',  'scan_']
            ctrl_lst = [ "TwoDExpChannel",  "LimaCCDCtrl.py",  "LimaCCDTwoDController", hsh[ 'controller'],
                         "limaccddevicename", "%s/%s" % (hsh[ 'hostname'], hsh[ 'device']),
                          'latencytime', '1',  'hardwaresavingextraprefix',  'scan_']
            elm_lst = [ "TwoDExpChannel", hsh[ 'controller'], "1", hsh[ 'name']]
        else:
            ctrl_lst = [ dct['type'], dct['lib'], dct['class'], ctrlName, 'RootDeviceName', rootDeviceName]

            if 'hostname' in hsh:
                ctrl_lst.append( 'TangoHost')
                ctrl_lst.append( hsh['hostname'])
            else:
                ctrl_lst.append( 'TangoHost')
                ctrl_lst.append( tangoHost)

            if hsh['device'].find('sis3302master') != -1:
                ctrl_lst.append( 'FlagMaster')
                ctrl_lst.append( '1' )

            if hsh['module'].find('limaccd') != -1:
                if 'mode' in hsh:
                    ctrl_lst.append( 'FlagMode')
                    ctrl_lst.append( hsh['mode'])
            #
            # Udais motor
            #
            if hsh['module'].find('newportxps') != -1:
                if 'ipaddress' in hsh:
                    ctrl_lst.append( 'ipaddress')
                    ctrl_lst.append( hsh['ipaddress'])
                if 'portno' in hsh:
                    ctrl_lst.append( 'portno')
                    ctrl_lst.append( hsh['portno'])

        #
        # ['Motor', ctrlName, '1', hsh['name']]
        # "CTExpChannel","sca_exp_mca01_100_200_ctrl","1","sca_exp_mca01_100_200"
        #
        # if sardananame exists, it is taken as the tango alias and name will become an online symbol
        #
        name = hsh['name']
        if 'sardananame' in hsh and hsh['sardananame'].find( "undefined") == -1:
            name = hsh[ 'sardananame']

        if len( elm_lst) == 0:
            elm_lst = [ dct['type'], ctrlName, str(channel), name.lower()]

        #print( "pooltools.createDevices %s %s " % (ctrl_lst[3], elm_lst[3]))
        #
        # handle the ctrl-c issue, ignore motors that are offline,
        # counters, like k_position, can be created because they
        # are harmless: no stopMove after Ctrl-C
        #
        hsh[ 'flagIgnore'] = False
        if not _checkMotorOnline( hsh):
            print( "pooltools.createDevices: %s offline, ignore " % hsh[ 'name'])
            hsh[ 'flagIgnore'] = True
            continue
        #
        # Konstantins request: notify user, if a device is offline
        #
        _reportOfflineDevices( hsh)

        if not insertControllerAndDevice( poolProxies, hsh['pool'], ctrl_lst, elm_lst):
            print( "pooltools._createDevices: failed for %s %s" % (ctrl_lst, elm_lst))
            continue

    return 1

def _isAMotor( hsh):
    '''
    return True, if hsh represents a motor
    '''
    if hsh['controller'].find( 'atto300_') == 0 or \
       hsh['controller'].find( 'dmc_energy') == 0 or \
       hsh['controller'].find( 'dmc_motor') == 0 or \
       hsh['controller'].find( 'elom_') == 0 or \
       hsh['controller'].find( 'kohzu_') == 0 or \
       hsh['controller'].find( 'phymotion_') == 0 or \
       hsh['controller'].find( 'mult_') == 0 or \
       hsh['controller'].find( 'oms58_') == 0 or \
       hsh['controller'].find( 'omsvme58_') == 0 or \
       hsh['controller'].find( 'newportxps') == 0 or \
       hsh['controller'].find( 'phaseretarder_') == 0 or \
       hsh['controller'].find( 'pie710_') == 0 or \
       hsh['controller'].find( 'pie712_') == 0 or \
       hsh['controller'].find( 'slt_') == 0 or \
       hsh['controller'].find( 'smchydra') == 0 or \
       hsh['controller'].find( 'spk_') == 0 or \
       hsh['controller'].find( 'tm_') == 0 or \
       hsh['controller'].find( 'galil_') == 0 or \
       hsh['controller'].find( 'diffracmu_') == 0 or \
       hsh['controller'].find( 'vm_') == 0:
        argout = True
    else:
        argout = False

    return argout

def _configureDevices( hshList):
    """
    Configure pool devices, copy motor unit limits.
    """

    print( "pooltools._configureDevices BEGIN")

    for hsh in hshList:
        if 'controller' not in hsh:
            print( "pooltools.configureDevices: %s %s" % (hsh['name'], "has no controller key"))
            continue

        if hsh['type'].find( 'diffractometercontroller') == 0:
            continue

        if hsh['type'] == 'pseudomotor':
            continue
        #
        # invented to handle the ctrl-c issue; ignore offline motors
        #
        if 'flagIgnore' in hsh and hsh[ 'flagIgnore']:
            #print( "pooltools.configureDevices ignoring %s" % hsh[ 'name'])
            continue

        if _isAMotor( hsh):
            fullName = hsh[ 'hostname'] + "/" + hsh[ 'device']
            #print( "pooltools.configureDevices: %s (controller %s)" % (hsh['name'], hsh['controller']))
            try:
                motor = PyTango.DeviceProxy( fullName)
            except PyTango.DevFailed as e:
                PyTango.Except.print_exception( e)
                print( "configureDevices cannot create a proxy to " + fullName + " terminate configuration")
                continue

            try:
                #
                # abs has no UnitLimitMin/~Max
                #
                if TgUtils.proxyHasAttribute( motor, "UnitLimitMin"):
                    min = motor.UnitLimitMin
                    max = motor.UnitLimitMax
                #
                # p11/piezomotor/eh.1.01
                #
                elif TgUtils.proxyHasAttribute( motor, "SoftLimitMaxUnits"):
                    min = motor.SoftLimitMinUnits
                    max = motor.SoftLimitMaxUnits
                #
                # p11/piezomotor/eh.4.01
                #
                elif TgUtils.proxyHasAttribute( motor, "SoftCcwLimit"):
                    min = motor.SoftCcwLimit
                    max = motor.SoftCwLimit
                #
                # p11/servomotor/eh.1.01
                #
                elif TgUtils.proxyHasAttribute( motor, "SoftLimitCcw"):
                    min = motor.SoftLimitCcw
                    max = motor.SoftLimitCw
                #
                # DACs are also treated as motors
                #
                elif TgUtils.proxyHasAttribute( motor, "VoltageMax"):
                    min = motor.VoltageMin
                    max = motor.VoltageMax
                else:
                    print( "pooltools.configureDevices: limit names %s" % fullName)
                    continue

            except PyTango.DevFailed as e:
                PyTango.Except.print_exception( e)
                print( "configureDevices failed to read limits %s" %  fullName)
                continue

            #
            # don't set the Position limits for VmExecutors in which UnitLimitMin/~Max can not be written
            # The limits are calculated in the VmExecutor code and the limits in the configuration of
            # the attribute (Spock limits) should stay undefined
            #
            if hsh['controller'].find( 'vm_') == 0:
                try:
                    motor.UnitLimitMin = min
                    motor.UnitLimitMax = max
                except:
                    print( "VmExecutor -> UnitLimitMax/~Min only readable. Limits of attribute Position not configured")
                    continue

            if math.isnan(min) or math.isnan(max):
                min = 0
                max = 0
            if math.fabs(min) < 1.0e-35:
                min = 0
            if math.fabs(max) < 1.0e-35:
                max = 0
            #
            # name: exp_mot01
            # sardananame: table_x (used in Spock)
            #
            poolName = hsh['name']
            if 'sardananame' in hsh and hsh['sardananame'].find( "undefined") == -1:
                poolName = hsh['sardananame']

            try:
                poolMotor = PyTango.DeviceProxy( poolName)
            except PyTango.DevFailed as e:
                PyTango.Except.print_exception( e)
                print( "configureDevices cannot create a proxy to " + poolName)
                continue
            #print( "pooltools.configureDevices: %s proxy.name() %s" % (hsh['name'], poolMotor.name()))
            try:
                attrConfig = poolMotor.get_attribute_config_ex( "Position")
            except:
                print( "configureDevices: failed to get_attribute_config for %s" % poolName)
                continue

            attrConfig[0].min_value = "%g" % min
            attrConfig[0].max_value = "%g" % max
            #
            # Change abs_change for motor event configuration
            #
            attrConfig[0].events.ch_event.abs_change = '0.1'
            #
            # adjust the abs_change for slow motors, e.g.
            #  haspp10e2 ecrlz: conv: -2500000, val. 60000.
            #
            r = 1.
            try:
                if TgUtils.proxyHasAttribute( poolMotor, 'Conversion') and TgUtils.proxyHasAttribute( poolMotor, 'Velocity'):
                    if poolMotor.Velocity > 0:
                        r = math.fabs( float( poolMotor.Conversion)/float( poolMotor.Velocity))
                        if r > 10:
                            attrConfig[0].events.ch_event.abs_change = '0.01'
            #
            # this was necessary because of Debian-10/Sardana3 (?), haso107d1
            #
            except Exception as e:
                pass

            if r > 1.:
                try:
                    poolMotor.set_attribute_config( attrConfig)
                except PyTango.DevFailed as e:
                    PyTango.Except.print_exception( e)
                    print( "configureDevices failed to configure attribute Position %s" % hsh['name'])
                    continue
        #
        # Add code for setting TangoAttribute to the controllers of the TangoAttrCTCtrl and TangoAttrZeroDCtrl classes
        #
        elif hsh['controller'].find( 'tangoattributectctrl') == 0 \
                or hsh['controller'].find( 'tangoattributezerodctrl') == 0 \
                or hsh['controller'].find( 'tangoattributeonedctrl') == 0:
            if 'sardananame' in hsh and hsh['sardananame'].find( "undefined") == -1:
                elemDevice = PyTango.DeviceProxy( hsh[ 'sardananame'])
            else:
                elemDevice = PyTango.DeviceProxy( hsh[ 'name'])
            #
            # Use rootdevicename for setting the full attribute name to control
            #
            elemDevice.TangoAttribute = hsh['hostname'] + "/" + hsh[ 'rootdevicename']
        #
        # Add code for setting TangoAttribute to the controllers of the TangoAttrIORCtrl class
        #
        elif hsh['controller'].find( 'tangoattributeiorctrl') == 0:
            if 'sardananame' in hsh and hsh['sardananame'].find( "undefined") == -1:
                elemDevice = PyTango.DeviceProxy( hsh[ 'sardananame'])
            else:
                elemDevice = PyTango.DeviceProxy( hsh[ 'name'])
            #
            # Use rootdevicename for setting the full attribute name to control
            #
            elemDevice.TangoAttribute = hsh['hostname'] + "/" + hsh[ 'rootdevicename']
            # Set labels and calibration if set in online.xml file
            if 'ior_labels' in hsh:
                try:
                    elemDevice.Labels = hsh['ior_labels']
                except:
                    print( "Not able to set Labels to TangoAttrIORCtrl " +  hsh[ 'name'])
            if 'ior_calibration' in hsh:
                try:
                    elemDevice.Calibration = hsh['ior_calibration']
                except:
                    print( "Not able to set Calibration to TangoAttrIORCtrl " +  hsh[ 'name'])

        #
        # Add code for setting TangoAttribute to the controllers of the MCAroisCtrl, MythenRoisCtrl or XMCDCtrl classes
        #
        elif hsh['controller'].find( 'mca8715roi') == 0 or hsh['controller'].find( 'mythenroi') == 0 or  hsh['controller'].find( 'xmcd') == 0:
            elemDevice = PyTango.DeviceProxy( hsh['name'])
            splitnames = hsh['device'].rsplit("/",1)
            elemDevice.write_attribute("TangoAttribute",splitnames[1])
        #
        # Add code for setting RoIIndex to the controllers of the SIS3302RoisCtrl class
        #
        elif hsh['controller'].find( 'sis3302roi') == 0 and hsh['controller'].find( 'sis3302roi1d') == -1 and hsh['controller'].find( 'sis3302ms1d') == -1:
            elemDevice = PyTango.DeviceProxy( hsh['name'])
            splitnames = hsh['device'].rsplit("/",1)
            elemDevice.write_attribute("RoIIndex",int(splitnames[1]))
        #
        # Add code for setting RoIAttributeName to the controllers of the KromoRoICtrl class
        #
        elif hsh['controller'].find( 'kromoroi') == 0:
            elemDevice = PyTango.DeviceProxy( hsh['name'])
            splitnames = hsh['device'].rsplit("/",1)
            elemDevice.write_attribute("RoIAttributeName",splitnames[1])
        #
        # Add code for setting SpectrumName to the controllers of the SPADQOneD class
        #
        elif hsh['controller'].find( 'spadq') == 0:
            elemDevice = PyTango.DeviceProxy( hsh['name'])
            splitnames = hsh['device'].rsplit("/",1)
            elemDevice.write_attribute("SpectrumName",splitnames[1])
        #
        # Add code for setting RoIStart and RoIEnd to onedroi devices
        #
        elif hsh['controller'].find( 'onedroi') == 0:
           if 'roi' in hsh:
               roi_str = hsh['roi']
               roi_values = roi_str.split(",")
               elemDevice = PyTango.DeviceProxy( hsh['name'])
               elemDevice.write_attribute("RoIStart", int(roi_values[0]))
               elemDevice.write_attribute("RoIEnd", int(roi_values[1]))
        #
        # Add code for setting RoIx1, RoIx2, RoIy and RoIy2  to limaroicounter devices
        #
        elif hsh['controller'].find( 'limaroicounter') == 0:
           if 'roi' in hsh:
               roi_str = hsh['roi']
               roi_values = roi_str.split(",")
               elemDevice = PyTango.DeviceProxy( hsh['name'])
               elemDevice.write_attribute("RoIx1", int(roi_values[0]))
               elemDevice.write_attribute("RoIy1", int(roi_values[1]))
               elemDevice.write_attribute("RoIx2", int(roi_values[2]))
               elemDevice.write_attribute("RoIy2", int(roi_values[3]))

        else:
            pass
    print( "pooltools._configureDevices DONE")
    return 1

def _forceDiffractometerControllerIntoPool( proxy, params):

    # +++
    print( "pooltools.forceDiffractometerControllerIntoPool: %s " % repr( params))

    retry = False
    for i in range(1):
        existingControllers = _getControllerList( proxy)
        if len( existingControllers) > 0 and params[3] in existingControllers:
            print( "pooltools.forceDiffractometerControllerIntoPool: OK")
            return 1
        try:
            proxy.CreateController(params)
            #print( "pooltools.forceDiffractometerControllerIntoPool: %s %s " % ( params, "OK"))
            return 1
        except PyTango.DevFailed as e:
            print( "pooltools.forceDiffractometerControllerIntoPool: failed %s" % params)
            _printTangoException( e)
            PyTango.Except.print_exception( e)
            print( "pooltools.forceDiffractometerControllerIntoPool: re-trying, sleep(3)")
            time.sleep(3)
            retry = True

    print( "forceDiffractometerControllerIntoPool: failed %s" % params)
    return 0

def poolDeviceSyntax():
    """
    1: 'full_name' contains 'desy.de' (pool.MotorList)
    0: otherwise
    """
    p = getPoolProxies()[0]
    lst = p.MotorList
    argout = 0
    dct = json.loads( lst[0])
    if dct[ 'full_name'].find( 'desy.de') != -1:
        argout = 1
    return argout

def _ocheckCrystalFileNameNotUsed( fileName):
    """
    return
        True, if the fileName points to /home/<user>/crystals
        False otherwise

    In [1]: lst = "/home/p09user/crystals".split( '/')

    In [2]: lst
    Out[2]: ['', 'home', 'p09user', 'crystals']

    In [3]: lst = "/home/p09user/crystals/".split( '/')

    In [4]: lst
    Out[4]: ['', 'home', 'p09user', 'crystals', '']

    """

    return 1 # +++
    lst = fileName.split( "/")
    #
    # if /home/etc/local_user exists, use it. Otherwise ignore
    #
    if os.path.exists('/home/etc/local_user'):
        local_user = os.popen('cat /home/etc/local_user').read().strip()
        if local_user != lst[2]:
            return False

    if len( lst) == 5:
        if len( lst[0]) == 0 and lst[1] == 'home' and lst[3] == 'crystals':
            return True
        else:
            return False
    else:
        return False

def _createDiffractometer( hshList):
    """ Create PseudoMotor controller for the diffractometer.
    It has to be done after creating the motor devices"""

    poolProxies = getPoolProxies()

    dict_diff_clases = {"PETRA3 P09 EH2": "Diffrac6C",
                        "PETRA3 P08 LISA": "DiffracLISA",
                        "PETRA3 P23 6C": "Diffrac6Cp23",
                        "E6C": "DiffracE6C",
                        "PETRA3 P23 4C": "Diffrac4Cp23",
                        "E4CH": "DiffracE4C",
                        "E4CV": "DiffracE4C"}

    dict_pm_roles = {"PETRA3 P09 EH2": ["h", "k", "l"],
                     "PETRA3 P08 LISA": ["h", "k", "l", "incidence", "emergence", "sth", "stth"],
                     "PETRA3 P23 6C": ["h", "k", "l", "psi", "q", "alpha", "tth2",  "alpha_tth2", "incidence", "emergence"],
                     "E6C": ["h", "k", "l","psi","q","alpha","qper","qpar"],
                     "PETRA3 P23 4C": ["h", "k", "l", "q", "alpha", "qper", "qpar", "tth2", "alpha_tth2", "incidence", "emergence"],
                     "E4CH": ["h", "k", "l","psi","q"],
                     "E4CV": ["h", "k", "l","psi","q"]}

    for hsh in hshList:
        #<device>
        # <name>e6cdiffrac</name>
        # <hkl>mu = 1, omega = 2, chi = 3, phi = 4, gamma = 5, delta = 6, crystal = /my/dir/crystal.txt</hkl>
        # if a motor is not an axis of the controller motor/<controller>, the whole name of the motor
        # device in the pool has to be given, ex.:
        # <hkl>mu = motor/diffracmu_mag/01, th = 2, chi = 3, phi = 4, gamma = 5, delta = 6, crystal = /my/dir/crystal.txt, energydevice = computer:10000/my/energy/device</hkl>
        # <type>diffractometercontroller</type>
        # <module>E6C</module>
        # <device>p09/motor/exp.01</device>
        # <control>tango</control>
        # <hostname>haso107tk:10000</hostname>
        # <pool>pool_haso107tk</pool>
        # <controller>omsvme58_exp</controller>
        # <channel>1</channel> --> not needed, only for compatibilty
        # <rootdevicename>p09/motor/exp</rootdevicename> --> not needed, only for compatibility
        #</device>
        flag = 0
        if hsh['type'] == 'diffractometercontroller':
            poolProxies = getPoolProxies()
            proxy = None
            for p in poolProxies:
                if hsh['pool'] == p.alias():
                    proxy = p
                    flag = 1
                    break
            if not flag:
                print( "_createDiffractometer: no pool %s" % poolName)
                OtherUtils.toAIOLog( "_createDiffractometer: no pool")
                return 0
            #params = ["PseudoMotor",
            #"HklPseudoMotorController",
            #"DiffracE6C",
            #"e6cctrl",
            #"mu=haspp09mono:10000/motor/omsvme58_exp/6",
            #"th=haspp09mono:10000/motor/omsvme58_exp/5",
            #"chi=haspp09mono:10000/motor/omsvme58_exp/4",
            #"phi=haspp09mono:10000/motor/omsvme58_exp/7",
            #"gamma=haspp09mono:10000/motor/omsvme58_exp/13",
            #"delta=haspp09mono:10000/motor/omsvme58_exp/14",
            #"h=e6ch","k=e6ck","l=e6cl",
            #"psi=e6cpsi","q21=e6cq21","q22=e6cq22",
            #"qperqpar1=e6cqperqpar1","qperpar2=e6cqperpar2",
            #"DiffractometerType","E6C"]
            try:
                params = []
                params.append("PseudoMotor")
                params.append("HklPseudoMotorController")
                params.append(dict_diff_clases[hsh['module'].upper()])
                params.append(hsh['name'])
                hsh['hkl'] = hsh['hkl'].replace(" ", "")
                # Conversion for p08:
                #mu = omh
                #omega = om
                #chi = chi
                #phi = phic
                #delta = tt
                #gamma = tth
                p08_names = None
                if hsh['module'].upper() != "PETRA3 P08 LISA" and hsh['module'].upper() != "E4CH" and hsh['module'].upper() != "E4CV":
                    if hsh['hkl'].find("omh=") != -1:
                        p08_names = dict(mu="omh", omega="om", phi="phic",
                                         delta="tt", gamma="tth", chi="chi")
                    hsh['hkl'] = hsh['hkl'].replace("omh=", "mu=")
                    hsh['hkl'] = hsh['hkl'].replace("om=", "omega=")
                    hsh['hkl'] = hsh['hkl'].replace("phic=", "phi=")
                    hsh['hkl'] = hsh['hkl'].replace("tt=", "delta=")
                    hsh['hkl'] = hsh['hkl'].replace("tth=", "gamma=")
                hkl_pairs = hsh['hkl'].split(",")
                hkl_dict = {}
                for pair in hkl_pairs:
                    elems = pair.split("=")
                    elems[0] = elems[0].strip()
                    elems[1] = elems[1].strip()
                    hkl_dict[elems[0]] = elems[1]

                if TgUtils.versionSardanaNewMg():
                    hostname_split = hsh['hostname'].split(':')
                    if poolDeviceSyntax() == 1: # with desy.de
                        if hostname_split[0].find("desy.de") == -1:
                            hostname_split[0] = hostname_split[0] + ".desy.de"
                    hsh['hostname'] = hostname_split[0] + ":" + hostname_split[1]
                    root_motor_name = "tango://" + hsh['hostname'] + "/motor/" + hsh['controller'] + "/"
                else:
                    root_motor_name = hsh['hostname'] + "/motor/" + hsh['controller'] + "/"

                for key in list( hkl_dict.keys()):
                    if key != "crystal" and key != "energydevice":
                        try:
                            int(hkl_dict[key])
                            params.append(key + "=" + root_motor_name + str(hkl_dict[key]))
                        except:
                            if TgUtils.versionSardanaNewMg():
                                params.append(key + "=" + "tango://" + hsh['hostname'] + "/" + str(hkl_dict[key]))
                            else:
                                params.append(key + "=" + hsh['hostname'] + "/" + str(hkl_dict[key]))


                for pm in dict_pm_roles[hsh['module'].upper()]:
                    params.append(pm + "=" + hsh['name'] + "_" + pm)
                params.append("DiffractometerType")
                params.append(hsh['module'].upper())
            except:
                print( "pooltools._createDiffractometer: error creating parameters for CreateController %s" % sys.exc_info()[0])
                OtherUtils.toAIOLog( "pooltools._createDiffractometer: error creating parameters for CreateController %s" % sys.exc_info()[0])
                return 0
            if not _forceDiffractometerControllerIntoPool( proxy, params):
                OtherUtils.toAIOLog( "pooltools._createDiff: forceDiffCtrlIntoPool failed, %s" % repr( params))
                return 0
            #print( "+++pooltools._createDiffractometer: %s" % repr( params))

            if "crystal" in hkl_dict:
                if not os.path.exists( hkl_dict['crystal']):
                    print( "pooltools._createDiffractometer: error, crystal file %s does not exist" % hkl_dict['crystal'])
                    OtherUtils.toAIOLog( "pooltools._createDiffractometer: error, crystal file %s does not exist" %
                                         hkl_dict['crystal'])
                    return 0

                #
                # make sure the crystal file is in /home/<user>/crystals
                #
                #if not checkCrystalFileName( hkl_dict['crystal']):
                #    print( "pooltools._createDiffractometer: crystal file %s not in ~/crystals" % hkl_dict['crystal'])
                #    OtherUtils.toAIOLog( "pooltools._createDiffractometer: crystal file %s not in ~/crystals" %
                #                         hkl_dict['crystal'])
                #    return 0

                try:
                    if 'sardananame' in hsh and hsh['sardananame'].find( "undefined") == -1:
                        diff_proxy = PyTango.DeviceProxy( hsh[ 'sardananame'])
                    else:
                        diff_proxy = PyTango.DeviceProxy(hsh['name'])
                    diff_proxy.write_attribute("LoadCrystal", hkl_dict['crystal'])
                except PyTango.DevFailed as e:
                    PyTango.Except.print_exception( e)
                    print( "_createDiffractometer: unable to load crystal %s" % hkl_dict['crystal'])
                    OtherUtils.toAIOLog( "pooltools._createDiffractometer: unable to load crystal %s" % hkl_dict['crystal'])

            if "energydevice" in hkl_dict:
                try:
                    if 'sardananame' in hsh and hsh['sardananame'].find( "undefined") == -1:
                        diff_proxy = PyTango.DeviceProxy( hsh[ 'sardananame'])
                    else:
                        diff_proxy = PyTango.DeviceProxy(hsh['name'])
                    diff_proxy.write_attribute("EnergyDevice", hkl_dict['energydevice'])
                    try:
                        energy_proxy = PyTango.DeviceProxy(hkl_dict['energydevice'])
                        energy = energy_proxy.Position
                        lambda_to_e = 12398.424 # Amstrong * eV
                        wavelength = lambda_to_e/energy
                        diff_proxy.write_attribute("Wavelength", wavelength)
                    except PyTango.DevFailed as e:
                        PyTango.Except.print_exception( e)
                        print( "_createDiffractometer: unable to set Wavelength")
                        OtherUtils.toAIOLog( "_createDiffractometer: unable to set Wavelength")

                except PyTango.DevFailed as e:
                    PyTango.Except.print_exception( e)
                    print( "_createDiffractometer: unable to set EnergyDevice %s" % hkl_dict['energydevice'])
                    OtherUtils.toAIOLog( "_createDiffractometer: unable to set EnergyDevice %s" % hkl_dict['energydevice'])

    return 1

def refreshDiffractometers():
    """
    refreshDiffractometer: to be executed after a reboot or a restart of the Pool
    uses the local pool to find the diffractometers
    a diffractometer needs a refresh, if savedirectory == ' '
    the refresh is executed by
      - executing a loadCrystal (crystal name from online.xml)
      - setting the energydevice, if mentioned in online.xml
    """
    #
    # create a proxy to the pool
    #
    poolProxies = getPoolProxies()
    if len( poolProxies) != 1:
        print( "pooltools.refreshDiffractometer: no. of Pools != 1, %d" % len( poolProxies))
        return False
    poolProxy = poolProxies[0]

    diffs = getDiffractometerNamesToBeRefreshed()
    if len( diffs) == 0:
        print( "pooltools.refreshDiffs: diffractometers are ok, no need to refresh")
        return True
    #
    # read online.xml
    #
    hshList = TgUtils.getOnlineXML( xmlFile = "/online_dir/online.xml")
    poolProxies = getPoolProxies()
    for hsh in hshList:
        if hsh['type'] != 'diffractometercontroller':
            continue
        #
        # create this dictionary
        # {'mu': '10', 'omega': '11', 'chi': '12', 'phi': '13', 'delta': '15', 'gamma': '14',
        #   'crystal': '/home/kracht/crystals/haspp09dif/defaultcrystal.txt',
        #   'energydevice': 'haso107d10:10000/p09/tangomotor/eh.01'}
        #
        hkl_pairs = hsh['hkl'].split(",")
        hkl_dict = {}
        for pair in hkl_pairs:
            elems = pair.split("=")
            elems[0] = elems[0].strip()
            elems[1] = elems[1].strip()
            hkl_dict[elems[0]] = elems[1]
        #
        # if hsh[ 'name'] is is the controllerList, refresh it
        #
        if 'sardananame' in hsh and hsh['sardananame'].find( "undefined") == -1:
            name = hsh[ 'sardananame']
        else:
            name = hsh[ 'name']

        if name in diffs:
            try:
                diff_proxy = PyTango.DeviceProxy( name)
            except Exception as e:
                print( "pooltools.refreshDiffs: failed to create proxy for %s" % name)
                print( repr( e))
                continue

            if 'crystal' in hkl_dict:
                crystalFile = hkl_dict[ 'crystal']
                #
                # make sure the crystal file is in /home/<user>/crystals
                #
                #if not checkCrystalFileName( hkl_dict['crystal']):
                #    print( "pooltools.refreshDiffractometer: crystal file %s not in ~/crystals" % hkl_dict['crystal'])
                #    OtherUtils.toAIOLog( "pooltools.refreshDiffractometer: crystal file %s not in ~/crystals" %
                #                         hkl_dict['crystal'])
                #    return 0

            else:
                if os.path.exists('/home/etc/local_user'):
                    local_user = os.popen('cat /home/etc/local_user').read().strip()
                    crystalFile = "/home/%s/crystals/defaultcrystal.txt" % local_user
                else:
                    print( "pooltools.refreshDiffs: no 'crystal' in diffractometer device (online.xml) and no /home/etc/local_user")
                    OtherUtils.toAIOLog( "pooltools.refreshDiffs: no 'crystal' in diffractometer device (online.xml) and no /home/etc/local_user")
                    continue
            try:
                diff_proxy.write_attribute("LoadCrystal", crystalFile)
            except Exception as e:
                print( "pooltools.refreshDiffs: failed: %s, loadCrystal %s " % (name, crystalFile))
                OtherUtils.toAIOLog( "pooltools.refreshDiffs: failed: %s, loadCrystal %s " % (name, crystalFile))
                continue

            print( "pooltools.refreshDiffs: %s, loadCrystal %s " % (name, crystalFile))
            OtherUtils.toAIOLog( "pooltools.refreshDiffs: %s, loadCrystal %s " % (name, crystalFile))

            if "energydevice" in hkl_dict:
                diff_proxy.write_attribute("EnergyDevice", hkl_dict['energydevice'])
                try:
                    energy_proxy = PyTango.DeviceProxy(hkl_dict['energydevice'])
                    energy = energy_proxy.Position
                    lambda_to_e = 12398.424 # Amstrong * eV
                    wavelength = lambda_to_e/energy
                    diff_proxy.write_attribute("Wavelength", wavelength)
                except PyTango.DevFailed as e:
                    print( "pooltools.refreshDiff: unable to set Wavelength")
                    print( repr(e))
                    OtherUtils.toAIOLog( "pooltools.refreshDiff: unable to set Wavelength")
                    OtherUtils.toAIOLog( repr( e))
                print( "pooltools.refreshDiffs: %s, energydevice to %s " % (name, hkl_dict[ 'energydevice']))
                OtherUtils.toAIOLog( "pooltools.refreshDiffs: %s, energydevice to %s " % (name, hkl_dict[ 'energydevice']))

    return

def getDiffractometerNames():
    """
    returns the names of the diffractometers in the local pool
    the ControllerList is searched for entries with
      hsh[ 'module'] == "HklPseudoMotorController":
    """
    #
    # create a proxy to the pool
    #
    poolProxies = getPoolProxies()
    if len( poolProxies) != 1:
        print( "pooltools.refreshDiffractometer: no. of Pools != 1, %d" % len( poolProxies))
        return False
    poolProxy = poolProxies[0]
    #
    # find the diffractometers in the controller list
    #
    diffs = []
    for elm in poolProxy.ControllerList:
        hsh = json.loads( elm)
        if hsh[ 'module'] == "HklPseudoMotorController":
            diffs.append( hsh[ 'name'])

    return diffs

def getDiffractometerNamesToBeRefreshed():
    """
    returns the names of the diffractometers in the local pool
    which need to be refreshed, this condition is met, if
    savedirectory == ' '
    """
    diffs = []
    for diff in getDiffractometerNames():
        try:
            p = PyTango.DeviceProxy( diff)
        except Exception as e:
            print( "pooltools.getDiffractometerNamesToBeRefresed: failed to create proxy for %s" % diff)
            print( repr( e))
            continue
        if p.loadcrystal == ' ':
            diffs.append( diff)

    return diffs

def _createPseudoMotors( hshList):
    """ Create PseudoMotors controllers. It has to be called after
    all devices are created"""

    proxy = None
    # change requested by Lars Lottermoser, 4.12.2020
    flag = 0
    for hsh in hshList:
        # The tag pseudomotor has to be set in the following order:
        # controller lib
        # controller class
        # pseudomotor roles
        # motor roles
        # property, value
        #
        # Ex. Slit:
        #
        #<device>
        # <name>myslit</name>
        # <pseudomotor>ctrl_lib = Slit.py, ctrl_class = Slit, sl2b=haso111n:10000/pm/slitctrl05/1, sl2t=haso111n:10000/pm/slitctrl05/2, Gap=gap_new, Offset=offset_new, sign, -1>
        # <type>pseudomotorcontroller</type>
        # <module>None</module>
        # <device>None</device>
        # <control>tango</control>
        # <hostname>haso107tk:10000</hostname>
        #</device>
        #
        # change requested by Lars Lottermoser, 4.12.2020
        #  flag = 0
        if hsh['type'] == 'pseudomotor':

            if proxy is None:
                poolProxies = getPoolProxies()

                for p in poolProxies:
                    if hsh['pool'] == p.alias():

                        proxy = p
                        flag = 1
                        break

            if not flag:
                print( "_createDiffractometer: no pool %s" % poolName)
                return 0

            try:
                params = []
                params.append("PseudoMotor")
                hsh['pseudomotor'] = hsh['pseudomotor'].replace(" ", "")
                pm_pairs = hsh['pseudomotor'].split(",")
                pm_dict = {}
                pm_args = []
                for pair in pm_pairs:
                    if pair.find("ctrl_lib") != -1 or pair.find("ctrl_class") != -1:
                        elems = pair.split("=")
                        pm_dict[elems[0]] = elems[1]
                    else:
                        pm_args.append(pair)

                # To be sure the order is the right one
                params.append(pm_dict['ctrl_lib'])
                params.append(pm_dict['ctrl_class'])
                params.append(hsh['name'])
                for arg in pm_args:
                    params.append(arg)
            except:
                print( "_createPseudoMotor: error creating parameters for creating pseudomotor controller %s" % sys.exc_info()[0])

            print( params)
            if 1:
                proxy.CreateController(params)

            print( "pooltools._createPseudoMotor: %s" % params[3])

    return 1


def _createDummyMotors():
    """ Create Dummy motors"""

    #print( "_createDummyMotors")

    poolProxies = getPoolProxies()

    hostname = TgUtils.getHostname()

    for proxy in poolProxies:
        params = []
        params.append("Motor")
        params.append("DummyMotorController.py")
        params.append("DummyMotorController")
        params.append("dummy_mot_ctrl")
        try:
            proxy.CreateController(params)
        except:
            print( "_createDummyMotors: warning from CreateController for dummy motors with pars %s" % params)
            # Continue even if error

        params = []
        params.append("Motor")
        params.append("dummy_mot_ctrl")
        params.append("1")
        params.append("exp_dmy01")
        try:
            proxy.CreateElement(params)
        except:
            print( "_createDummyMotors: warning from CreateElement for dummy motor with pars %s %s " % (params, " (probably this motor is defined in the xml file)"))
            # Continue even if error


        params = []
        params.append("Motor")
        params.append("dummy_mot_ctrl")
        params.append("2")
        params.append("exp_dmy02")
        try:
            proxy.CreateElement(params)
        except:
            print( "_createDummyMotors: warning from CreateElement for dummy motor with pars %s %s " % (params, " (probably this motor is defined in the xml file)"))
            # Continue even if error

        params = []
        params.append("Motor")
        params.append("dummy_mot_ctrl")
        params.append("3")
        params.append("exp_dmy03")
        try:
            proxy.CreateElement(params)
        except:
            print( "_createDummyMotors: warning from CreateElement for dummy motor with pars %s %s " % (params, " (probably this motor is defined in the xml file)"))
            # Continue even if error

        #
        # make dummy motors fast
        #
        for m in ['exp_dmy01', 'exp_dmy02', 'exp_dmy03']:
            try:
                p = PyTango.DeviceProxy( m)
                p.velocity = 1000000000
                p.acceleration = 0.000001
                #
                attrConfig = p.get_attribute_config_ex( "Position")
                attrConfig[0].min_value = "-1000000"
                attrConfig[0].max_value = "1000000"
                p.set_attribute_config( attrConfig)
                #
            except:
                print( "_createDummyMotors: failed to create a proxy to exp_dmy01 ")

    # print( "_createDummyMotors DONE")

    return 1


def createPoolDevices( **a):
    """Create pool devices."""

    print( "pooltools.createPoolDevices %s" % a)
    if 'xmlfile' not in a:
        print( "pooltools.createPoolDevices: no xmlfile supplied")
        return 0
    if 'beamline' not in a:
        print( "pooltools.createPoolDevices: no beamline supplied")
        return 0


    hshList = TgUtils.getOnlineXML( xmlFile = a['xmlfile'])

    if not _createDevices( hshList):
         print( "pooltools.createPoolDevices: failed to create devices")
         return 0

    if not _configureDevices( hshList):
        print( "pooltools.createPoolDevices: failed to configure devices")
        return 0

    if not _createPseudoMotors( hshList):
        print( "pooltools.createPoolDevices: failed to create PseudoMotor controller")

    if not _createDiffractometer( hshList):
        print( "pooltools.createPoolDevices: failed to create diffractometer controller")
        # Continue even if error

    _createDummyMotors()

    print( "pooltools.createPoolDevices DONE")
    return 1

def _mgIsInPool( pool, mgName):
    try:
        mgList = pool.read_attribute( "MeasurementGroupList")
    except Exception as e:
        print( "pooltools.mgIsInPool return False by exception")
        PyTango.Except.print_exception( e)
        return False
    if mgList.is_empty:
        return 0
    for elm in mgList.value:
        dct = json.loads( elm)
        if mgName.lower() == dct[ 'name'].lower():
            return 1
    return 0

def _forceMgIntoPool( pool, params):

    retry = False
    for i in range( 5):
        try:
            #
            # params: ['mg_haso107d1', 'd1_t03', 'd1_c01', 'sig_gen', 'h_position', 'mod20']
            #
            if _mgIsInPool( pool, params[0]):
                print( "pooltools.forceMgIntoPool: Pool %s %s already exists" % (pool.name(), repr( params)))
                return 1
            pool.CreateMeasurementGroup(params)
            #
            # avoiding error messages when displaying attributes of MGs
            #
            #proxy = PyTango.DeviceProxy( params[0])
            #proxy.IntegrationTime = 0.12345
            #
            # check, if the mg was actually created
            #
            #temp = PyTango.DeviceProxy( hsh['name'])
            if retry:
                print( "pooltools.forceMgIntoPool: Pool", pool.name(), params, "OK")

            return 1
        except PyTango.DevFailed as e:
            print( "pooltools.forceMgIntoPool: error from CreateMeasurementGroup with pars %s" % params)
            _printTangoException( e)
            print( "re-trying, sleep(3)")
            time.sleep(3)
            retry = True
    print( "pooltools.forceMgIntoPool: failed Pool %s %s" % (pool.name(), params))
    return 0

def createMeasurementGroups( **a):
    """Create measurement groups."""

    print( "pooltools.createMeasurementGroups: %s (BEGIN)" % a)
    if 'xmlfile' not in a:
        print( "pooltools.createMeasurementGroups: no xmlfile supplied")
        return 0

    hshList = TgUtils.getOnlineXML( xmlFile = a['xmlfile'])

    for hsh in hshList:

        if hsh['type'] == 'measurement_group':
            #
            # poolTools MG: {'control': 'tango', 'name': 'mg_tk', 'tags': 'user,expert,remote',
            #                'hostname': 'haso107tk:10000', 'module': 'none', 'mgs': 'timers = eh_t01,
            #                 counters=eh_vfc01, eh_vfc02, eh_vfc03, sig_gen, pos2alias, haso107tk:10000/p09/vmexecutor/eh.03/position',
            #                 'controller': 'none', 'channel': 'none', 'device': 'none',
            #                 'type': 'measurement_group', 'rootdevicename': 'none', 'pool': 'pool_haso107tk'}
            #
            poolProxies = getPoolProxies()
            pool = None
            flag = 0
            for p in poolProxies:
                if hsh['pool'] == p.alias():
                    pool = p
                    flag = 1
                    break
            if not flag:
                print( "*** createMeasurementGroups: no pool " + hsh['pool'] + " Measurement Group " + hsh['name'] + " not created")
            else:
                hsh['mgs'] = hsh['mgs'].replace(" ", "")
                if hsh['mgs'].find("timers=") == -1 or hsh['mgs'].find("counters=") == -1:
                    print( "createMeasurementGroups: no timers and/or counters given. Ex.: <mgs>timers= t01,counters= c01, c02</mgs>")
                    print( "*** createMeasurementGroups: Measurement Group " + hsh['name'] + " not created")
                else:
                    elements = hsh['mgs'].split(",counters=")
                    timers = elements[0]
                    timers = timers.split("timers=")[1]
                    timers = timers.split(",")
                    if len( elements) < 2:
                        print( "pooltools.createMeasurementGroups: syntax error in %s" % hsh['mgs'])
                        print( "pooltools.createMeasurementGroups: missing ',' before 'counters'?")
                        return 0
                    counters = elements[1].split(",")
                    lst_ct = []
                    try:
                        lst_ct = pool.ExpChannelList
                    except:
                        print( "pooltools.createMeasurementGroups: failed to access ExpChannelList")
                    lst = []
                    for ct in lst_ct:
                        hsh_ct = json.loads( ct)
                        lst.append( hsh_ct['name'])

                    create_mg = 1
                    for timer in timers:
                        if timer not in lst:
                            create_mg = 0
                            print( "*** pooltools.createMeasurementGroups: timer " + timer + " not found. Measurement group " + hsh['name'] + " not created")
                    for counter in counters:
                        counter = counter.replace("-c", "")
                        counter = counter.replace("-d", "")
                        counter = counter.replace("-nd", "")
                        counter = counter.replace("-o", "")
                        counter = counter.replace("-no", "")
                        if counter.find("/") == -1: # External channels are not in the channel list, and the name has to contain a '/' (tango adresses)
                            if counter not in lst:
                                create_mg = 0
                                print( "*** pooltools.createMeasurementGroups: counter " + counter + " not found. Measurement group " + hsh['name'] + " not created")

                    params = []
                    params.append(hsh['name'])
                    if TgUtils.getDeviceNameByAlias( timers[0]) is None:
                        print( "pooltools.createMeasurementGroup: %s does not exist, fatal, exiting" % timers[0])
                        return 0

                    params.append(timers[0]) # for the moment only one timer is allowed
                    counters_display = []
                    counters_nodisplay = []
                    counters_output = []
                    counters_nooutput = []
                    counters_convert = []
                    counters_add_display_output = []
                    for counter in counters:
                        if counter in params:
                            print( "*** pooltools.createMeasurementGroup: %s already in the list, ignore and continue" % counter)
                            continue
                        if counter.find("/") != -1: # Skip external channels if they can not be readout
                            try:
                                PyTango.AttributeProxy(counter)
                            except: # Attibute does not exist or not running
                                print( "*** pooltools.createMeasurementGroup: %s does not exist, ignore and continue" % counter)
                                continue

                        if counter.find("-c") != -1:
                            counter = counter.replace("-c", "")
                            ccounter = counter.replace("-d", "")
                            ccounter = ccounter.replace("-nd", "")
                            ccounter = ccounter.replace("-o", "")
                            ccounter = ccounter.replace("-no", "")
                            counters_convert.append(ccounter)
                        dis_out = 0
                        if counter.find("-d") != -1:
                            counters_display.append(counter.replace("-d", "").replace("-o", "").replace("-no", ""))
                            counters_add_display_output.append(counter.replace("-d", "").replace("-o", "").replace("-no", ""))
                            dis_out = 1
                        elif counter.find("-nd") != -1:
                            counters_nodisplay.append(counter.replace("-nd", "").replace("-o", "").replace("-no", ""))
                            counters_add_display_output.append(counter.replace("-nd", "").replace("-o", "").replace("-no", ""))
                            dis_out = 1
                        if counter.find("-o") != -1:
                            counters_output.append(counter.replace("-o", "").replace("-d", "").replace("-nd", ""))
                            counters_add_display_output.append(counter.replace("-o", "").replace("-d", "").replace("-nd", ""))
                            dis_out = 1
                        elif counter.find("-no") != -1:
                            counters_nooutput.append(counter.replace("-no", "").replace("-d", "").replace("-nd", ""))
                            counters_add_display_output.append(counter.replace("-no", "").replace("-d", "").replace("-nd", ""))
                            dis_out = 1

                        if dis_out == 0 and counter.find("/") == -1: # External channels are not in the channel list, and the name has to contain a '/' (tango adresses)
                            if TgUtils.getDeviceNameByAlias( counter) is None:
                                print( "*** pooltools.createMeasurementGroup: %s does not exist, ignore and continue" % counter)
                                continue
                            params.append(counter)

                    if create_mg:
                        print( "pooltools.createMeasurementGroups: %s" % params)
                        if not _forceMgIntoPool( pool, params):
                            return 0
                        try:
                            setDisplayTrue( hsh['name'])
                        except:
                            print( "createMeasurementGroup: failed to setDisplayValue %s" % hsh['name'])

                    else:
                       print( "*** createMeasurementGroup: Measurement group " + hsh['name'] + " not created")

                    if create_mg:
                        if len(timers) > 1: # The measurement group has to be changed for adding the extra timer
                            try:
                                mgConf = MgUtils.MgConf( hsh['pool'], hsh['name'], False)
                                mgConf.addExtraTimer( timers[1])
                                mgConf.updateConfiguration()
                            except Exception as e:
                                print( "\npooltools.createMeasurementGroup: extra timer, caught an exception")
                                sys.exit( 255)
                                #raise Exception( "pooltools.createMeasurementGroup",
                                #                 "Failed to add an extra timer %s, %s" % (timers[1], hsh['name']))

                        if len(counters_add_display_output) > 0: # Set display and output options
                            try:
                                mgConf = MgUtils.MgConf( hsh['pool'], hsh['name'], False)
                            except Exception as e:
                                print( "\npooltools.createMeasurementGroups: read mgConf, caught an exception")
                                (eType, value, tracebackObject) = sys.exc_info()
                                print( "eTpye %s" % str(eType))
                                print( "value %s" % str(value))
                                print( repr( e))
                                sys.exit( 255)
                                #raise Exception( "pooltools.createMeasurementGroup",
                                #                 "MgConf failed for %s" % hsh['name'])
                            for counter in counters_add_display_output:
                                flag_display = 1
                                flag_output = 1
                                if counter in counters_nodisplay:
                                    flag_display = 0
                                if counter in counters_nooutput:
                                    flag_output = 0

                                mgConf.addCounter(counter, flag_display, flag_output)
                            try:
                                mgConf.updateConfiguration()
                            except Exception as e:
                                print( "pooltools.createMeasurementGroups: caught an exception updating the configuration %s" % hsh[ 'name'])
                                print( repr( e))
                                print( "pooltools.createMeasurementGroups: re-try")
                                time.sleep(10)
                                try:
                                    mgConf.updateConfiguration()
                                except Exception as e:
                                    print( "pooltools.createMeasurementGroups: 2nd, caught an exception")
                                    print( repr( e))
                                    raise Exception( "pooltools.createMeasurementGroup",
                                                 "Failed 2 times to set the display option for %s" % hsh['name'])

                for counter in counters_convert:
                    counter_device = PyTango.DeviceProxy(counter)
                    try:
                        counter_device.write_attribute("Conversion", -1.)
                    except:
                        print( "createMeasurementGroup: failed set conversion to -1 for counter " + counter)
    return 1

def _getTimerFromPool( pool):
    """Search the ExpChannelList of the Pool for a timer and return the first."""
    try:
        lst = pool.ExpChannelList
    except:
        print( "pooltools._getTimerFromPool: failed to access ExpChannelList")
        return None
    if lst is None:
        return None
    for elm in lst:
        hsh = json.loads( elm)
        if hsh['parent'].find( "dgg2") == 0:
            return hsh['name']
    return None

def _getCounterFromPool( pool):
    """Search the ExpChannelList of the Pool for a counter or a vfcadc and return the first."""
    ecList = pool.ExpChannelList
    if ecList is None:
        return None
    lst = []
    for elm in ecList:
        hsh = json.loads( elm)
        if hsh['parent'].find( "sis3820") == 0:
            lst.append( hsh['name'])
    if len(lst) > 0:
        lst.sort()
        return lst[0]
    lst = []
    for elm in ecList:
        hsh = json.loads( elm)
        if hsh['parent'].find( "vfcadc") == 0:
            lst.append( hsh['name'])
    if len(lst) > 0:
        lst.sort()
        return lst[0]
    return None

def setDisplayTrue( mgName):
    """Make sure that the devices are displayed"""
    try:
        mg = PyTango.DeviceProxy( mgName)
    except Exception as e:
        print( "pooltools.setDisplayTrue: caught an exception creating proxy %s" % mgName)
        PyTango.Except.print_exception( e)
        return 0

    hsh = json.loads( mg.Configuration)
    #TgUtils.TgUtils.dct_print( hsh)
    for k in list( hsh['controllers'].keys()):
        if k.find( 'dgg2ctr') > 0:
            continue
        if 'units' in hsh['controllers'][k]:
            for c in list( hsh['controllers'][k]['units']['0']['channels'].keys()):
            #print( "pooltools.setDisplayTrue:", mgName, k, c, "to True (Debian-8)")
                hsh['controllers'][k]['units']['0']['channels'][c]['output'] = True
                hsh['controllers'][k]['units']['0']['channels'][c]['plot_axes'] = ['<mov>']
                hsh['controllers'][k]['units']['0']['channels'][c]['plot_type'] = 1
        else:
            for c in list( hsh['controllers'][k]['channels'].keys()):
                # print( "pooltool.setDisplayTrue:", mgName, k, c, "to True (Debian-9)")
                hsh['controllers'][k]['channels'][c]['output'] = True
                hsh['controllers'][k]['channels'][c]['plot_axes'] = ['<mov>']
                hsh['controllers'][k]['channels'][c]['plot_type'] = 1

    try:
        mg.Configuration = json.dumps( hsh)
    except Exception as e:
        print( "pooltools.setDisplayTrue: caught an exception storing configuration %s" % mgName)
        PyTango.Except.print_exception( e)
        return 0

class BreakLoop(Exception): pass

def createDefaultMeasurementGroup( **a):
    """Create a MntGrp on each Pool and fill it with the first counter and timer."""

    hostname = TgUtils.getHostname()
    poolNames = TgUtils.getLivingLocalPoolNames()

    if not poolNames:
        raise Exception( "pooltools.createDefaultMeasurementGroup",
                         "No living local pools")

    #
    # don't create a default MG, if there is already a MG
    #
    lst = TgUtils.getMgAliases()
    if not lst is None:
        print( "pooltools.createDefaultMeasurementGroup: nothing to be done, %s %s " % (lst, "exists already"))
        return 1

    for poolName in poolNames:
        try:
            pool = PyTango.DeviceProxy( poolName)
        except PyTango.DevFailed as e:
            PyTango.Except.print_exception( e)
            return 0
        #
        # p02/pool/haspp02eh1a
        #
        mgName = "mg_" + poolName.split( '/')[2]
        try:
            lst = TgUtils.getMgAliases()
            if lst:
                for mg in lst:
                    if mgName == mg:
                        print( "pooltools.createDefaultMeasurementGroup: %s %s " % (mgName," exists already"))
                        raise BreakLoop
        except BreakLoop:
            continue

        tm = _getTimerFromPool( pool)
        if tm is None:
            continue
        if hostname == "haspp10e1" or hostname == "haspp10e1":
            tm = "e2_t01"
        ct = _getCounterFromPool( pool)
        if ct is None:
            lst = [ mgName] + [tm]
        else:
            lst = [ mgName] + [tm, ct]
        pool.CreateMeasurementGroup( lst)
        setDisplayTrue( mgName)
        print( "pooltools.createDefaultMeasurementGroup: pool %s %s " % ( pool.name(), lst))
    return 1

def fixActiveMntGrp():
    """make sure that the ActiveMntGrp is not pointing nowhere"""

    poolNames = TgUtils.getLocalPoolNames()
    try:
        activeMntGrp = TgUtils.getEnv( 'ActiveMntGrp')
    except:
    #
    # if no ActiveMntGrp exists - no problem
    #
        return 1
    #
    # if no ActiveMntGrp is None - no problem
    #
    if activeMntGrp is None:
        return 1
    #
    # if the ActiveMntGrp is in the list - ok
    #
    mgAliases = TgUtils.getMgAliases()
    if mgAliases is not None:
        if activeMntGrp in mgAliases:
            print( "pooltools.fixActiveMntGrp: %s exists" % activeMntGrp)
            return 1
    #
    # if there are no MGs, delete the ActiveMntGrp
    #
    if mgAliases is None or len( mgAliases) == 0:
        TgUtils.unsetEnv( 'ActiveMgtGrp')
        print( "pooltools.fixActiveMntGrp: %s does not exist, delete it" % activeMntGrp)
        return 1

    TgUtils.setEnv( 'ActiveMntGrp', mgAliases[0])
    print( "pooltools.fixActiveMntGrp: ActiveMntGrp set to %s" % mgAliases[0])

    return 1

def listMeasurementGroup( **a):
    """Print the MeasurementGroup"""
    if 'mntgrp' not in a:
        print( "pooltools.listMeasurementGroup: no mntgrp supplied")
        return 0

    try:
        mntgrp = PyTango.DeviceProxy( a['mntgrp'])
    except PyTango.DevFailed as e:
        PyTango.Except.print_exception( e)
        return 0

    conf = json.loads(mntgrp.Configuration)

    TgUtils.my_print(conf)

    return 1

def startMacroServer( **a):
    """Start the MacroServer, the instance is supplied by the dct."""
    if 'instance' not in a:
        print( "pooltools.startMacroServer: no instance supplied")
        return 0

    serverName = "MacroServer/" + a['instance']
    if not TgUtils.startServer( serverName):
        print( "pooltools.startMacroServer: failed to start %s" % serverName)
        return False
    return True

def stopMacroServer( **a):
    """Stop the MacroServer, the instance is supplied by the dct."""
    if 'instance' not in a:
        print( "pooltools.stopMacroServer: no instance supplied")
        return False

    serverName = "MacroServer/" + a['instance']
    if not TgUtils.stopServer( serverName):
        print( "pooltools.stopMacroServer: failed to stop %s" % serverName)
        return False
    print( "Stopped %s" % serverName)
    return True

def startServer( srvName):
    """Start a server."""
    if not TgUtils.startServer( srvName):
        print( "pooltools.startServer failed to start %s" % srvName)
        return False
    print( "Started %s" % srvName)
    return True

def stopServer( srvName):
    """Stop a server."""
    if not TgUtils.stopServer( srvName):
        print( "pooltools.stopServer failed to stop %s" % srvName)
        return False
    print( "Stopped %s" % srvName)
    return True

def restartServer( srvName):
    '''
    Stop and start a server.
    '''
    if not TgUtils.stopServer( srvName):
        print( "pooltools.restartServer failed to stop %s" % srvName)
        return False
    if not TgUtils.startServer( srvName):
        print( "pooltools.restartServer failed to start %s" % srvName)
        return False
    print( "Restarted %s" % srvName)
    return True

def startPool( **a):
    """Start the pool, the instance is supplied by the dct."""
    if 'instance' not in a:
        print( "pooltools.startPool: no instance supplied")
        return 0

    serverName = "Pool/" + a['instance']
    if not TgUtils.startServer( serverName):
        print( "pooltools.startPool: failed to start %s" % serverName)
        return False
    print( "Started %s" % serverName)
    return True

def stopPool( **a):
    """Stop the pool, the instance is supplied by the dct."""
    if 'instance' not in a:
        print( "pooltools.stopPool: no instance supplied")
        return 0

    serverName = "Pool/" + a['instance']
    if not TgUtils.stopServer( serverName):
        print( "pooltools.startPool: failed to stop %s" % serverName)
        return False
    print( "Stopped %s" % serverName)
    return True

def restartPool( **a):
    """Stop and start the Pool, the instance is supplied by the dct."""
    if 'instance' not in a:
        print( "pooltools.restartPool: no instance supplied")
        return 0
    srvName = "Pool/" + a['instance']
    if not TgUtils.stopServer( srvName):
        print( "pooltools.restartPool failed to start %s" % srvName)
        return False
    if not TgUtils.startServer( srvName):
        print( "pooltools.restartPool failed to start %s" % srvName)
        return False
    print( "Restarted %s" % srvName)
    return True


def getPoolProxies():
    """Return the pool proxies."""
    argout = []
    for srv in TgUtils.getServerNameByClass( "Pool"):
        dName = db.get_device_name( srv, "Pool").value_string[0]
        if not MgUtils.checkPoolNameValid( dName):
            #print( "pooltools.getPoolProxies: ignoring %s" % dName)
            continue
        argout.append( PyTango.DeviceProxy( dName))
    return argout

def deleteMotorGroups():
    """
    delete the pool motor groups
    this is a fix for a bug reported by P23, see notes, 22.10.2020, [rt #1002115]
    """

    try:
        pool = PyTango.DeviceProxy( TgUtils.getLocalPoolNames()[0])
    except Exception as e:
        print( " pooltools.deleteMotorGroups, error %s" % str(e))
        return

    motorGroupList = pool.MotorGroupList

    if motorGroupList is None:
        return

    for motorGroup in pool.MotorGroupList:
        hsh = json.loads( motorGroup)
        print( "pooltools.deleteMotorGroups: deleting %s" % hsh[ 'name'])
        pool.DeleteElement( hsh[ 'name'])

    return

#
# taken out: 22.9.2015
#
#def getDoorProxies():
#    """Return the door proxies."""
#    argout = []
#    for srv in TgUtils.getServerNameByClass( "Door"):
#        argout.append( PyTango.DeviceProxy( db.get_device_name( srv, "Door").value_string[0]))
#    return argout
#def getMacroServerProxies():
#    """Return a list of MacroServer proxies."""
#    argout = []
#    for srv in TgUtils.getServerNameByClass( "MacroServer"):
#        argout.append( PyTango.DeviceProxy( db.get_device_name( srv, "MacroServer").value_string[0]))
#    return argout

#def getStarterProxy():
#    """Return the Starter proxy."""
#    for srv in TgUtils.getServerNameByClass( "Starter"):
#        return PyTango.DeviceProxy( db.get_device_name( srv, "Starter").value_string[0])
#    return 0

def usedByMg( name):
    """Return True if the device is used by the mg."""
    mgLst = TgUtils.getMgNames()

    for mg in mgLst:
        proxy = PyTango.DeviceProxy(mg)
        if name in proxy.ElementList:
            return mg
    return False

def clearSCAs():
    """ Clear SCAs, if they are not used by a MeasurementGroup.

        The device to be deleted is found in the pool.ExpChannelList,
    """
    poolNames = TgUtils.getLivingLocalPoolNames()

    running_proxy = 1
    lst = None
    for pool in poolNames:
        try:
            proxy = PyTango.DeviceProxy( pool)
            lst = proxy.ExpChannelList
        except:
            running_proxy = 0
        if running_proxy:
            if lst is None:
                continue
            for elm in lst:
                hsh = json.loads( elm)
                if hsh['name'].find( "sca_") == 0:
                    mgName = usedByMg( hsh['name'])
                    if not mgName:
                        proxy.DeleteElement( str(hsh['name']))
                    else:
                        pass

    running_proxy = 1
    for pool in poolNames:
        try:
            proxy = PyTango.DeviceProxy( pool)
            lst = proxy.ControllerList
        except:
            running_proxy = 0
        if running_proxy:
            for elm in lst:
                hsh = json.loads( elm)
                if hsh['name'].find( "sca_") == 0:
                    mgName = usedByMg( hsh['name'].partition('_ctrl')[0])
                    if not mgName:
                        proxy.DeleteElement( str(hsh['name']))
                    else:
                        pass

def limitsFromTS2Pool( poolName):
    """Copy the limits from the tango servers to the Pool."""
    pool = None
    try:
        pool = PyTango.DeviceProxy( poolName)
    except:
        print( "limitsFromTS2Pool: failed to get proxy to %s" % poolName)
        print( sys.exc_info()[0])
        sys.exit()

    for elm in pool.MotorList:
        hsh = json.loads( elm)
        try:
            PD_proxy = PyTango.DeviceProxy( str(hsh['full_name']))
        except:
            print( "limitsFromTS2Pool: failed to get proxy to %s" % hsh['full_name'])
            continue
        try:
            TS_name = PD_proxy.TangoDevice
        except:
            print( "limitsFromTS2Pool: no TangoDevice attribute for %s" % hsh['full_name'])
            continue

        try:
            TS_proxy = PyTango.DeviceProxy( str(TS_name))
        except:
            print( "limitsFromTS2Pool: failed to get proxy to %s" % str(TS_name))
            continue

        #
        # abs has no UnitLimitMin/~Max
        #
        if TgUtils.proxyHasAttribute( TS_proxy, "UnitLimitMin"):
            min = TS_proxy.UnitLimitMin
            max = TS_proxy.UnitLimitMax
        #
        # p11/piezomotor/eh.1.01
        #
        elif TgUtils.proxyHasAttribute( TS_proxy, "SoftLimitMaxUnits"):
            min = TS_proxy.SoftLimitMinUnits
            max = TS_proxy.SoftLimitMaxUnits
        #
        # p11/piezomotor/eh.4.01
        #
        elif TgUtils.proxyHasAttribute( TS_proxy, "SoftCcwLimit"):
            min = TS_proxy.SoftCcwLimit
            max = TS_proxy.SoftCwLimit
        #
        # p11/servomotor/eh.1.01
        #
        elif TgUtils.proxyHasAttribute( TS_proxy, "SoftLimitCcw"):
            min = TS_proxy.SoftLimitCcw
            max = TS_proxy.SoftLimitCw
        #
        # DACs are also treated as motors
        #
        elif TgUtils.proxyHasAttribute( TS_proxy, "VoltageMax"):
            min = TS_proxy.VoltageMin
            max = TS_proxy.VoltageMax
        else:
            print( "pooltools.configureDevices: failed to read UnitLimitMin,~max, SoftLimit~ for %s" % fullName)
            continue


        #
        # don't set the Position limits for VmExecutors in which UnitLimitMin/~Max can not be written
        # The limits are calculated in the VmExecutor code and the limits in the configuration of
        # the attribute (Spock limits) should stay undefined
        #
        if hsh['controller'].find( 'vm_') == 0:
            try:
                TS_proxy.UnitLimitMin = min
                TS_proxy.UnitLimitMax = max
            except:
                print( "VmExecutor -> UnitLimitMax/~Min only readable. Limits of attribute Position not configured")
                continue

        attrConfig = PD_proxy.get_attribute_config_ex( "Position")
        attrConfig[0].min_value = "%g" % min
        attrConfig[0].max_value = "%g" % max
        try:
            PD_proxy.set_attribute_config( attrConfig)
            print( "PoolDevice %s receives min %g max %g from %s" % (PD_proxy.name(), min, max, TS_proxy.name()))
        except Exception as e:
            print( "limitsFromTS2Pool  failed for %s min %g max %g from %s" % (PD_proxy.name(), min, max, TS_proxy.name()))
            print( repr( e))

#
#
#
try:
    db = PyTango.Database()
except:
    print( "Can't connect to tango database on %s" % os.getenv('TANGO_HOST'))
    pass
    # sys.exit(255)

if __name__ == "__main__":
    pass

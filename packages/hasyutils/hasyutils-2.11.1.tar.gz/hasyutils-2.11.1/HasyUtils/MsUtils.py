#!/usr/bin/env python3
'''
this file contains the helper functions for the MacroServer
'''
#
# not fatal because pyspViewer.py might be called on a non-exp host
#
try: 
    import PyTango as _PyTango
except:
    pass
from . import TgUtils
import os as _os
import sys as _sys
import math as _math

def _findTangoDevice( macro, poolDevice): 
    '''
    return the TangoDevice belonging to a poolDevice
    '''
    try:
        poolProxy = _PyTango.DeviceProxy( poolDevice)
        temp = poolProxy.read_attribute( "TangoDevice").value 
    except Exception as e:
        macro.output( "MsUtils._findTangoDevice: failed for %s, %s" %
                      ( poolDevice, str( e)))
        macro.abort()
        return None
    #macro.output( "MsUtils._findTangoDevice: %s" % temp)
    return temp

def _findFilewriter( macro, name):
    '''
    name is the Tango device name of an EigerDectris. This 
    function returns the name of the corresponding filewriter.
    '''
    #
    # find an EigerFilewriter for the EigerDectris
    #
    deviceNameFw = None
    TangoHost = None
    if name.find( ":10000"):
        lst = name.split( ':')
        TangoHost = "%s:10000" % lst[0]

    devsFw = TgUtils.getDeviceNamesByClass( "EigerFilewriter", tangoHost = TangoHost)
    for devFw in devsFw:
        prop = TgUtils.getDeviceProperty( devFw, 'EigerDevice', tangoHost = TangoHost)
        #
        # prop[0]: p62/eiger/e4m vs. hasnp62eh:10000/p62/eiger/e4m
        #
        if name.find( prop[0]) != -1:
            deviceNameFw = devFw
            break
    if deviceNameFw is None: 
        macro.output( "MsUtils._findFilewriter: failed to find filewriter for %s" % 
                      (name))
        macro.abort()
        return None
    if TangoHost is not None: 
        deviceNameFw = "%s/%s" % (TangoHost, deviceNameFw)
    return deviceNameFw

def prepareEigerDectrisAttrs( macro, name = None, NbImages = 1, 
                              CountTime = None, TriggerMode = None, NbTriggers = 1, 
                              ArmFlag = True, ImagesPerFile = 1000):
    '''

    called from MsUtils.prepareDetectorAttrs()

    sets these detector attributes
      CountTime  
      NbImages   
      NbTriggers 
      TriggerMode 

    the Filewriter FileNamePattern ist derived from ScanFile, ScanDir, ScanID
    #
    # ScanDir == "/gpfs/commissioning/raw"
    #
    if scan_dir.find( "commissioning/raw") != -1: 
        temp = "commissioning/raw/%s_%05d/%s/%s_%05d" % ( prefix, int( scan_id), detectorName, prefix, int( scan_id))
    #
    # ScanDir == "/gpfs/local"
    #
    elif scan_dir.find( "/gpfs/local") != -1: 
        temp = "local/%s_%05d/%s/%s_%05d" % ( prefix, int( scan_id), detectorName, prefix, int( scan_id))
    #
    # ScanDir == /gpfs/current/raw
    #
    else: 
        temp = "current/raw/%s_%05d/%s/%s_%05d" % ( prefix, int( scan_id), detectorName, prefix, int( scan_id))
    eigerFw_proxy.FilenamePattern = temp

    scanNameDir = "%s/%s_%05d" % ( scan_dir, prefix, int( scan_id))
    fileDir = "%s/%s_%05d/%s" % ( scan_dir, prefix, int( scan_id), detectorName)
      *** scanNameDir and fileDir are created with 0777 
          this feature has been added to avoid permission issues for beamlines
          with two different users, e.g. p99user and p99femto

    ImagesPerFile   = 1000 by default

    Eventually execute arm()
      ArmFlag can be False, if users want to do some extra initialisations


    Here is an example (PreScan Hook)                    

        scanInfo = HasyUtils.createScanInfo( self.getParentMacro().getCommand())
        if HasyUtils.isInMg( self, detectorName):
            if not HasyUtils.prepareDetectorAttrs( self, 
                                                   name = detectorName,
                                                   trig_mode = 'ints',
                                                   nbFrames = 1, # per trigger 
                                                   acq_time = scanInfo[ 'sampleTime'], 
                                                   NbTriggers = scanInfo[ 'intervals'] + 1,
                                                   ImagesPerFile = 1000):
                self.output( "general_features.gh_pre_scan: prepareDetectors: returned error")
                return False

    '''

    detectorName = name
    if detectorName is None: 
        macro.output( "MsUtils.prepareEigerDectrisAttrs: no detectorName")
        macro.abort()
        return False
    #
    # detectorName is a pool device name, find the Tango device
    #
    tangoDevice = _findTangoDevice( macro, detectorName)
    if tangoDevice is None: 
        return
    try:
        eiger_proxy = _PyTango.DeviceProxy( tangoDevice)
        macro.output( "MsUtils.prepareEigerDectrisAttrs: Eiger %s" % tangoDevice)
        macro.debug("MsUtils.prepareEigerDectrisAttrs: %s found in active MG" % detectorName)
    except Exception as e:
        macro.output( "MsUtils.prepareEigerDectrisAttrs: failed to create proxy to %s, %s, %s" % 
                      (detectorName, controllerProxy.TangoDevice, str( e)))
        macro.abort()
        return False

    #
    # disarm the detector before setting the attributes
    #
    eiger_proxy.disarm()

    #
    # CountTime (exposure time)
    #
    if CountTime is not None: 
        eiger_proxy.CountTime    = float( CountTime)
        macro.output( "MsUtils.prepareEigerDectrisAttrs: CountTime to %g" % eiger_proxy.CountTime)
        #eiger_proxy.FrameTime = float( CountTime)*1.001
        #macro.output( "MsUtils.prepareEigerDectrisAttrs: FrameTime to %g" % eiger_proxy.CountTime)
    #
    # NbImages per Trigger
    #
    eiger_proxy.NbImages     = int( NbImages)
    macro.output( "MsUtils.prepareEigerDectrisAttrs: NbImages to %d" % eiger_proxy.NbImages)
    
    #
    # TriggerMode, usually 'ints' for internal triggers
    #
    if TriggerMode is not None: 
        eiger_proxy.TriggerMode  = TriggerMode
        macro.output( "MsUtils.prepareEigerDectrisAttrs: TriggerMode to %s" % eiger_proxy.TriggerMode)
    #
    # NbTriggers
    #
    eiger_proxy.NbTriggers = int( NbTriggers)
    macro.output( "MsUtils.prepareEigerDectrisAttrs: NbTrigger to %d" % eiger_proxy.NbTriggers)

    #
    # handle Filewriter
    #
    deviceNameFw = _findFilewriter( macro, tangoDevice)
    if deviceNameFw is None: 
        return 

    try: 
        eigerFw_proxy = _PyTango.DeviceProxy( deviceNameFw)
        macro.output( "MsUtils.prepareEigerDectrisAttrs: FileWriter %s" % deviceNameFw)
    except Exception as e:
        macro.output( "MsUtils.prepareEigerDectrisAttrs: failed to create proxy to %s, %s" % 
                      ( deviceNameFw, str( e)))
        macro.abort()
        return False

    #
    # tst.fio -> tst
    #
    scan_file = macro.getEnv("ScanFile")
    if type(scan_file).__name__ == 'list':
        scan_file = scan_file[0]

    prefix = scan_file.split( '.')[0]
    scan_id = macro.getEnv("ScanID")
    #
    # use ScanDir to select 
    #    current/raw/<prefix>_<ScanID>/<detectorName>/<prefix>_$id
    #  or 
    #    commissioning/raw/<prefix>_<ScanID>/<detectorName>/<prefix>_$id
    #
    #  $id is handled by Dectris
    #
    # on the DCU we will always have /data/current/raw
    # the download job looks at ScanDir
    #
    scan_dir = macro.getEnv( "ScanDir")
    scanNameDir = "%s/%s_%05d" % ( scan_dir, prefix, int( scan_id))
    fileDir = "%s/%s_%05d/%s" % ( scan_dir, prefix, int( scan_id), detectorName)
    try:
        _os.makedirs( fileDir, exist_ok=True)
        _os.chmod( fileDir, 0o777)
        _os.chmod( scanNameDir, 0o777)
    except Exception as e: 
        macro.output( "MsUtils.prepareDetectorAttrs: failed to create %s, %s" % (fileDir, e))
        return False
    macro.output( "MsUtils.prepareEigerDetectorAttrs: creating %s" % (fileDir))
    #+++
    #
    # 9.3.2021: taken out $id for Florian Bertram
    #
    if scan_dir.find( "commissioning/raw") != -1: 
        #temp = "commissioning/raw/%s_%05d/%s/%s_$id" % ( prefix, int( scan_id), detectorName, prefix)
        temp = "commissioning/raw/%s_%05d/%s/%s_%05d" % ( prefix, int( scan_id), detectorName, prefix, int( scan_id))
    #
    # ScanDir == "/gpfs/local"
    #
    elif scan_dir.find( "/gpfs/local") != -1: 
        #temp = "local/%s_%05d/%s/%s_$id" % ( prefix, int( scan_id), detectorName, prefix)
        temp = "local/%s_%05d/%s/%s_%05d" % ( prefix, int( scan_id), detectorName, prefix, int( scan_id))
    else: 
        #temp = "current/raw/%s_%05d/%s/%s_$id" % ( prefix, int( scan_id), detectorName, prefix)
        temp = "current/raw/%s_%05d/%s/%s_%05d" % ( prefix, int( scan_id), detectorName, prefix, int( scan_id))
    eigerFw_proxy.FilenamePattern = temp
    macro.output( "MsUtils.prepareEigerDectrisAttrs: FilenamePattern to %s" % eigerFw_proxy.FilenamePattern)
    #
    # ImagesPerFile
    #
    # eigerFw_proxy.ImagesPerFile = NbImages*NbTriggers
    # Florian like the 'fixed' 1000 better, to avoid large files
    #
    eigerFw_proxy.ImagesPerFile = ImagesPerFile
    macro.output( "MsUtils.prepareEigerDectrisAttrs: ImagesPerFile to %d" % eigerFw_proxy.ImagesPerFile)

    #
    # eventually arm() the detector
    #
    if ArmFlag: 
        macro.output( "MsUtils.prepareEigerDectrisAttrs: calling arm()")
        eiger_proxy.arm()
    else: 
        macro.output( "MsUtils.prepareEigerDectrisAttrs: NOT calling arm()")

    return True


def resetEigerDectrisAttrs( macro, name = None):
    '''
    make sure that:
     - the detector is disarmed to close the file
     - NbTriggers is set to 1 in order to allow for 'ct' 
     - ImagesPerFile is set to 1 in order to allow for 'ct' 
    '''

    import time
    detectorName = name
    if detectorName is None: 
        macro.output( "MsUtils.resetEigerDectrisAttrs: no detectorName")
        macro.abort()
        return False

    tangoDevice = _findTangoDevice( macro, detectorName)
    if tangoDevice is None: 
        return 
    try: 
        eiger_proxy = _PyTango.DeviceProxy( tangoDevice)
    except Exception as e:
        macro.output( "MsUtils.resetEigerDectrisAttrs: failed to create proxy to %s, %s" % 
                      ( tangoDevice, str( e)))
        macro.abort()
        return False


    deviceNameFw = _findFilewriter( macro, tangoDevice)
    if deviceNameFw is None: 
        return 
    try: 
        eigerFw_proxy = _PyTango.DeviceProxy( deviceNameFw)
    except Exception as e:
        macro.output( "MsUtils.resetEigerDectrisAttrs: failed to create proxy to %s, %s" % 
                      ( deviceNameFw, str( e)))
        macro.abort()
        return False

    if eigerFw_proxy.state() == _PyTango.DevState.MOVING: 
        macro.output( "MsUtils.resetEigerDectrisAttrs: FW (%s)  is MOVING -> disarm detector" % deviceNameFw)
        eiger_proxy.disarm()
        startTime = time.time()
        while eigerFw_proxy.state() != _PyTango.DevState.ON: 
            time.sleep( 0.1)
            if (time.time() - startTime) > 2: 
                macro.output( "MsUtils.resetEigerDectrisAttrs: FW %s does not become ON" % deviceNameFw)
                return False
        while eigerFw_proxy.status() != 'ready':
            time.sleep( 0.1)
            if (time.time() - startTime) > 2: 
                macro.output( "MsUtils.resetEigerDectrisAttrs: FW %s does not become 'ready'" % deviceNameFw)
                return False 

    scan_file = macro.getEnv("ScanFile")
    if type(scan_file).__name__ == 'list':
        scan_file = scan_file[0]
    lst = scan_file.split( '.')
    #
    # this creates current/raw/SingleShots
    #
    eigerFw_proxy.FilenamePattern = "current/raw/SingleShots/%s_$id" % lst[0]
    macro.output( "MsUtils.resetEigerDectrisAttrs: FilenamePattern to %s" % eigerFw_proxy.Filenamepattern)

    eigerFw_proxy.ImagesPerFile = 1
    macro.output( "MsUtils.resetEigerDectrisAttrs: ImagesPerFile to %d" % int( eigerFw_proxy.ImagesPerFile))
    eiger_proxy.NbImages = 1
    macro.output( "MsUtils.resetEigerDectrisAttrs: NbImages to %d" % int( eiger_proxy.NbImages))
    eiger_proxy.NbTriggers = 1
    macro.output( "MsUtils.resetEigerDectrisAttrs: NbTriggers to %d" % int( eiger_proxy.NbTriggers))
    eiger_proxy.TriggerMode = 'ints'
    macro.output( "MsUtils.resetEigerDectrisAttrs: TriggerMode to %s" % eiger_proxy.TriggerMode)
                
    return True

def prepareDetectorAttrs( macro, name = "pilatus", rootDir = "/ramdisk", 
                          nbFrames = 1, acq_time = None, trig_mode = None, NbTriggers = 1, 
                          ArmFlag = True, ImagesPerFile = 1000, do_check_if_detector_in_mg=True):
    '''
      prepareDetectorAttrs() uses the input arguments and the MacroServer
      environment variables ScanFile and ScanID to set these detector attributes:
        FileDir|SaveFilePath|saving_directory: /<rootDir>/<scanName>/<detectorName>
                                               /ramdisk/au_01390/pilatus
        FilePrefix|saving_prefix:  <scanName>
                                   au_01390
        NbFrames|FrameNumbers|acq_nb_frames: nbFrames

        FileStartNum|saving_next_number:     0
     
     This directory is created: 
        rootDir + "/" + scanName + "/" + detectorName
        /gpfs/current/raw/au_00001/pilatus

     As a safety measure, rootDir is compared with FileDir|SaveFilePath|saving_directory. 
     An error is thrown, if the values are incompatible. Both
     strings are compatible, if FileDir starts with rootDir

     So far Dalsa, Eiger, Pilatus, Lambda, Kromo and Lima (Andor) servers are supported

     trig_mode: FreeRunning, ExtTrigger, Snapshot, TimedSnap, TrigSequence

    for doku about the Eiger interface, see HasyUtils.prepareEigerDectrisAttrs? and
    HasyUtils.resetEigerDectrisAttrs?

    ArmFlag == True
      Eiger: ArmFlag can be False, if users want to do some extra initialisations
    ImagesPerFile, for the EigerFilewriter
    '''
    detectorName = name

    if do_check_if_detector_in_mg and not isInMg( macro, detectorName):
        macro.output( "MsUtils.prepareDetectorAttrs: MG does not contain %s " % detectorName)
        return True

    try: 
        clss = TgUtils.getClassNameByDevice( _findTangoDevice( macro, detectorName))
    except Exception as e: 
        macro.output( "MsUtils.prepareDetectorAttrs: error finding class for %s" % detectorName)
        macro.output( "MsUtils.prepareDetectorAttrs: %s" % repr( e))
        return 
    if clss == "EigerDectris": 
        return prepareEigerDectrisAttrs( macro, 
                                         name = detectorName, 
                                         NbImages = nbFrames, 
                                         CountTime = acq_time,
                                         TriggerMode = trig_mode,
                                         NbTriggers = NbTriggers, 
                                         ArmFlag = ArmFlag, 
                                         ImagesPerFile = ImagesPerFile)

    scan_file = macro.getEnv("ScanFile")
    if type(scan_file).__name__ == 'list':
        scan_file = scan_file[0]
    scan_id = macro.getEnv("ScanID")

    tangoDevice_proxy = None
    count = 0
    while True:
        try:
            controllerProxy = _PyTango.DeviceProxy(detectorName)
            temp = controllerProxy.read_attribute( "TangoDevice").value 
            tangoDevice_proxy = _PyTango.DeviceProxy( temp)
            macro.debug("MsUtils.prepareDetectorAttrs: %s found in active MG" % detectorName)
            break
        except Exception as e:
            count += 1
            if count > 5: 
                macro.output( "MsUtils.prepareDetectorAttrs: failed to create proxy to %s, %s, %s" % 
                              (detectorName, controllerProxy.TangoDevice, str( e)))
                macro.abort()
                return False
            macro.output( "MsUtils.prepareDetectorAttrs: failed to create proxy to %s, %s, retry" % 
                          (detectorName, controllerProxy.TangoDevice))

    #
    # ScanName, e.g.: au_012345
    #
    scanName = "%s_%05d" % (scan_file.split('.')[0], int( scan_id))
    fileDirName = None
    lst = ["FileDir", "SaveFilePath", "saving_directory"]
    for elm in lst:
        if TgUtils.proxyHasAttribute( tangoDevice_proxy, elm):
            fileDirName = elm
            break
    else:
        macro.output( "MsUtils.prepareDetectorAttrs: attribute %s is missing on %s" % 
                      (str(lst), tangoDevice_proxy.name()))
        return False

    try:
        rootDirSrv = tangoDevice_proxy.read_attribute( fileDirName).value
    except Exception as e:
        macro.output( "MsUtils.prepareDetectorAttrs: caught exception during reading %s of %s, %s" % 
                      (fileDirName, tangoDevice_proxy.name(), str(e)))
        return

    if rootDirSrv is None: 
        macro.output( "MsUtils.prepareDetectorAttrs: rootDirSrv is None, fileDirName %s" % (fileDirName))
        return
    # 
    # see, if rootDir is compatible with the FileDir on the server
    # 
    if rootDirSrv.find( rootDir) != 0:
        macro.output( "MsUtils.prepareDetectorAttrs:")
        macro.output( "  %s: %s which is an attr of %s " % (fileDirName, rootDirSrv, tangoDevice_proxy.name()))
        macro.output( "    and")
        macro.output( "  rootDir: %s found in general_features" % (rootDir))
        macro.output( "    are incompatible")
        macro.output( "  Please fix it, maybe by changing the %s attribute in the detector server" % fileDirName)
        macro.abort()
        return False

    macro.output( "MsUtils.prepareDetectorAttrs: device %s" % ( tangoDevice_proxy.name()))
    # 
    # it is important to create the directory before it is written to the server
    #
    if rootDir[-1] == '/':
        fileDir = rootDir + scanName + "/" + detectorName
    else: 
        fileDir = rootDir + "/" + scanName + "/" + detectorName
    macro.output( "MsUtils.prepareDetectorAttrs: creating %s %s (0o777)" % (fileDirName, fileDir))
    try:
        _os.makedirs( fileDir)
        _os.chmod( fileDir, 0o777)
    except Exception as e: 
        macro.output( "MsUtils.prepareDetectorAttrs: failed to create %s, %s" % (fileDir, e))
        return False
    macro.output( "MsUtils.prepareDetectorAttrs: setting %s to %s" % (fileDirName, fileDir))
    try:
        tangoDevice_proxy.write_attribute( fileDirName, fileDir)
    except Exception as e: 
        macro.output( "MsUtils.prepareDetectorAttrs: caught exception writing %s to %s, %s " % \
                      (fileDir, fileDirName,  tangoDevice_proxy.name()))
        macro.output( "%s" % ( repr(e)))
        return False
    #
    # FrameNumbers
    #
    set_nbframes = 1
    nbFramesName = None
    lst = ["NbFrames", "FrameNumbers", "acq_nb_frames"]
    for elm in lst:
        if TgUtils.proxyHasAttribute( tangoDevice_proxy, elm):
            nbFramesName = elm
            break
    else:
        set_nbframes = 0

    if set_nbframes:
        try:
            tangoDevice_proxy.write_attribute( nbFramesName, nbFrames)
            macro.output( "MsUtils.prepareDetectorAttrs: Number of frames set to 1")
        except Exception as e: 
            macro.output( "MsUtils.prepareDetectorAttrs: caught exception writing to %s, %s, %s" % \
                          (nbFramesName, tangoDevice_proxy.name(), str(e)))
            return False
    #
    # fileStartNum
    #
    fileStartNum = None
    lst = ["FileStartNum", "saving_next_number", "FileIndex", "FileRefNumber"]
    for elm in lst:
        if TgUtils.proxyHasAttribute( tangoDevice_proxy, elm):
            fileStartNum = elm
            break
    else:
        macro.output( "MsUtils.prepareDetectorAttrs: attribute %s is missing on %s" % 
                      (str(lst), tangoDevice_proxy.name()))
        return False

    try:
        #
        # P03, Jannik Woehnert: pscamera: FileRefNumber ist ein string
        #
        cfg = tangoDevice_proxy.get_attribute_config( fileStartNum)
        if cfg.data_type == _PyTango.CmdArgType.DevString:
            tangoDevice_proxy.write_attribute( fileStartNum, "0")
        else:
            tangoDevice_proxy.write_attribute( fileStartNum, 0)
    except Exception as e: 
        macro.output( "MsUtils.prepareDetectorAttrs: caught exception writing to %s, %s, %s" % 
                      (fileStartNum, tangoDevice_proxy.name(), str(e)))
        return False
    #
    # FilePrefix
    #
    filePrefix = None
    lst = ["FilePrefix", "saving_prefix"] 
    for elm in lst:
        if TgUtils.proxyHasAttribute( tangoDevice_proxy, elm):
            filePrefix = elm
            #
            # Lima does not provide the '_' between prefix and image number itself
            #
            if elm == "saving_prefix":
                scanName += "_"
            break
    else:
        macro.output( "MsUtils.prepareDetectorAttrs: attribute %s is missing on %s" % 
                      ( str(lst), tangoDevice_proxy.name()))
        return False

    try:
        tangoDevice_proxy.write_attribute( filePrefix, scanName)
    except Exception as e:                    
        macro.output( "MsUtils.prepareDetectorAttrs: failed to set %s %s, %s, %s" % 
                      (filePrefix, detectorName, scanName, str(e)))
        return False
    #
    # ShutterTime
    #
    if acq_time is not None: 
        actTimeName = None
        lst = ["ExtendedExposure", "ShutterTime"]
        for elm in lst:
            if TgUtils.proxyHasAttribute( tangoDevice_proxy, elm):
                actTimeName = elm
                break
        if actTimeName is None: 
            macro.output( "MsUtils.prepareDetectorAttrs: device has no %s attributes" % 
                          ( detectorName, str(lst)))
            return False
        return False
            
        try:
            tangoDevice_proxy.write_attribute( actTimeName, acq_time)
        except Exception as e:                    
            macro.output( "MsUtils.prepareDetectorAttrs: failed to set %s %s to %s, %s" % 
                          (detectorName, actTimeName, acq_time, repr( e)))
    #
    # TriggerMode: FreeRunning, ExtTrigger, Snapshot, TimedSnap, TrigSequence (Dalsa)
    #
    if trig_mode is not None: 
        lst = ["TriggerMode"]
        trigModeName = None
        for elm in lst:
            if TgUtils.proxyHasAttribute( tangoDevice_proxy, elm):
                trigModeName = elm
                break
        if trigModeName is None: 
            macro.output( "MsUtils.prepareDetectorAttrs: device has no %s attributes" % 
                          ( detectorName, str(lst)))
            return False
        try:
            tangoDevice_proxy.write_attribute( trigModeName, trig_mode)
        except Exception as e:                    
            macro.output( "MsUtils.prepareDetectorAttrs: failed to set %s %s to %s, %s" % 
                          (detectorName, trigModeName, trig_mode, repr( e)))

    return True

def resetDetectorAttrs( macro, name = "pilatus", rootDir = "/ramdisk", do_check_if_detector_in_mg=True):
    '''
      resetDetectorAttrs() is intended to be use in post-scan hooks to
      store imgages created by the 'ct' command in rootDir

        FileDir|SaveFilePath|saving_directory: to <rootDir>

     So far Pilatus, Lambda and Eiger servers are supported
    '''
    detectorName = name

    if do_check_if_detector_in_mg and not isInMg( macro, detectorName):
        macro.output( "MsUtils.resetDetectorAttrs: MG does not contain %s" % detectorName)
        return True

    clss = TgUtils.getClassNameByDevice( _findTangoDevice( macro, detectorName)) 
    if clss == "EigerDectris": 
        return resetEigerDectrisAttrs( macro, name = detectorName)

    tangoDevice_proxy = None

    count = 0
    while True:
        try:
            controllerProxy = _PyTango.DeviceProxy(detectorName)
            temp = controllerProxy.read_attribute( "TangoDevice").value 
            tangoDevice_proxy = _PyTango.DeviceProxy( temp)
            macro.debug("MsUtils.resetDetectorAttrs: %s found in active MG" % detectorName)
            break
        except:
            count += 1
            if count > 5: 
                macro.output( "MsUtils.resetDetectorAttrs: failed to create proxy to %s, %s" % 
                              (detectorName, controllerProxy.TangoDevice))
                macro.abort()
                return False
            macro.output( "MsUtils.resetDetectorAttrs: failed to create proxy to %s, %s, retry" % 
                          (detectorName, controllerProxy.TangoDevice))

    fileDirName = None
    lst = ["FileDir", "SaveFilePath", "saving_directory"]
    for elm in lst:
        if TgUtils.proxyHasAttribute( tangoDevice_proxy, elm):
            fileDirName = elm
            break
    else:
        macro.output( "MsUtils.resetDetectorAttrs: attribute %s is missing on %s" % 
                      (str(lst), tangoDevice_proxy.name()))
        return False

    try:
        rootDirSrv = tangoDevice_proxy.read_attribute( fileDirName).value
    except Exception:
        macro.output( "MsUtils.resetDetectorAttrs: caught exception during reading FileDir of %s" % 
                      tangoDevice_proxy.name())

    try:
        tangoDevice_proxy.write_attribute( fileDirName, rootDir)
    except Exception as e: 
        macro.output( "MsUtils.resetDetectorAttrs: caught exception writing %s to %s, %s " % \
                      (rootDir, fileDirName,  tangoDevice_proxy.name()))
        macro.output( "%s" % ( repr(e)))
        return False

    return True

def isInMg( macro, detectorName):
    '''
    getObj() disables Ctrl-Cs
    '''
    import sardana.macroserver.macro as _ms
    _ms.Type = TgUtils.TypeNames()

    active_mg = macro.getEnv("ActiveMntGrp")
    try:
        mg = macro.getObj(active_mg, type_class=_ms.Type.MeasurementGroup)
    except Exception as e:
        macro.output( "MsUtils.isInMg: getObj active_mg exception %s, aborting" % e)
        macro.abort()
        return False

    channels = mg.getChannelLabels()
    if detectorName in channels:
            return True
    return False

def isInMgWOgetObj( macro, detectorName):
    '''
    returns True, if detectorName in in the ActiveMntGrp
    '''
    active_mg = macro.getEnv("ActiveMntGrp")
    try:
        mg = _PyTango.DeviceProxy( active_mg)
    except Exception as e:
        macro.output( "MsUtils.isInMg: failed to create a proxy to %s,  %s, aborting" % (active_mg, e))
        macro.abort()
        return False
    channels = mg.read_attribute( "ElementList").value
    if detectorName in channels:
            return True
    return False

def testImportOld( filename): 
    """
    uses 'import importlib.util'
    returns (True, ""), if filename can be imported
    returns (False, "exception-string") otherwise
    """
    import importlib.util

    status = True
    msg = ""
    try: 
        spec = importlib.util.spec_from_file_location( '', filename)
        a = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(a)
    except Exception as e: 
        status = False
        msg = repr( e)
    finally: 
        pass

    return( status, msg)

def testImport( filename): 
    """
    uses importlib.import_module to see whether a python
      file can be importet

    returns (True, ""), if filename can be imported
    returns (False, "exception-string") otherwise
    
    Works at least on Debian-11 and Debian-12
    """
    import importlib

    dirName = _os.path.dirname( filename)
    baseName = _os.path.basename( filename)

    prefixName = baseName
    if baseName.find( '.py') > 0:
        prefixName = baseName.rpartition('.')[0]

    if dirName not in _sys.path:
        _sys.path.insert( 0, dirName)

    status = True
    msg = ""
    try: 
        mod = importlib.import_module( prefixName)
    except Exception as e: 
        msg = repr( e)
        status = False

    return (status, msg) 

def getModule( filename): 
    """
    returns the module or None
    """
    import importlib.util

    status = True
    msg = ""
    try: 
        spec = importlib.util.spec_from_file_location( '', filename)
        a = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(a)
    except Exception as e: 
        a = None

    return( a)
#
# ===
#
def _appendAbs( scanInfo, mot, start, stop, intervals = None): 
    '''
    function to append absolute scans to the scanInfo
    ascan exp_dmy01 0 10 10 0.1

    extend the motor array of scanInfo by an entry of the kind
    { name:  someName, 
      start: the start of the scan
      stop:  the stop of the scan
    }
    '''
    mDct = {}
    mDct['name'] = mot
    mDct['start'] = float( start)
    mDct['stop'] = float( stop)
    if intervals is not None:
        mDct['intervals'] = int( intervals)
    scanInfo[ 'motors'].append( mDct)
    return
#
# ===
#
def _appendRel( scanInfo, mot, left, right, intervals = None): 
    '''
    function to append relative scans to the scanInfo
    dscan exp_dmy01 -1 1 10 0.1

    extend the motor array of scanInfo by an entry of the kind
    { name:  someName, 
      start: the start of the scan
      stop:  the stop of the scan
    }
    '''
    mDct = {}
    mDct['name'] = mot
    try:
        p = _PyTango.DeviceProxy( mDct[ 'name'])
    except Exception as e:
        print( "MsUtils._appendRel: failed to create proxy to %s" % mDct['name'])
    mDct['start'] = p.position + float( left)
    mDct['stop'] = p.position + float( right)
    if intervals is not None:
        mDct['intervals'] = int( intervals)
    scanInfo[ 'motors'].append( mDct)
    return

def getScanFileName(): 
    '''
    returns the file name used by the last scan
    returns None, if the file does not exist

    uses the MacroServer environment variables: ScanDir, ScanFilem ScanID
    '''
    scanDir = TgUtils.getEnv( "ScanDir") 
    scanFile = TgUtils.getEnv( "ScanFile") 
    scanID = TgUtils.getEnv( "ScanID") 
    
    if type( scanFile) is list: 
        scanFileTemp = scanFile[0]
    else: 
        scanFileTemp = scanFile
    #
    # ['tst.fio'] -> ['tst', 'fio'] 
    #
    lst = scanFileTemp.split( ".")

    fileName = "%s/%s_%05d.%s" % ( scanDir, lst[0], int( scanID), lst[1])

    if not _os.path.exists( fileName): 
        argout = None
    else: 
        argout = fileName

    return fileName
   
#
# ===
#
def createScanInfo( title = None):
    '''
    Depending on whether createScanInfo() is called in an after-scan-scenario or
    a pre-scan-scenario the title has to be supplied or not.

    title == None (after-scan-scenario): the function takes the title from ScanHistory 
             returns None, if ScanID != serialno (history), probably because
             the last scan has been aborted (ctrl-c)

    title != None (pre-scan-scenario): if ScanHistory is not valid because createScanInfo() 
             is called from a hook, the title has to be supplied.

             pre_scan_hook example: 
               scanInfo = HasyUtils.createScanInfo( self.getParentMacro().getCommand())

    returns a data structure describing the scan, see below, used e.g. mvsa and CursorApp

    {'motors': [{'name': 'exp_dmy01', 'start': 0.0, 'stop': 10.0}], 
    'title': 'ascan exp_dmy01 0.0 10.0 10 1.0', 
    'serialno': 1502, 
    'intervals': 10, 
    'nPts': 11, 
    'sampleTime': 1.0}

   {'motors': [{'name': 'exp_dmy01', 'start': 0.0, 'stop': 10.0}, 
               {'name': 'exp_dmy02', 'start': 2.0, 'stop': 3.0}], 
    'title': 'a2scan exp_dmy01 0.0 10.0 exp_dmy02 2.0 3.0 3 1.0', 
    'serialno': 1503, 
    'intervals': 3, 
    'nPts': 4, 
    'sampleTime': 1.0}

    {'motors': [{'name': 'exp_dmy01', 'start': 0.0, 'stop': 1.0, 'intervals': 2}, 
                {'name': 'exp_dmy02', 'start': 2.0, 'stop': 3.0, 'intervals': 3}], 
    'title': 'mesh exp_dmy01 0.0 1.0 2 exp_dmy02 2.0 3.0 3 0.1 False None', 
    'serialno': 1504, 
    'nPts': 12, 
    'sampleTime': 0.1}

    serialno is taken from the environment.
    nPts is normally (intervals + 1). For mesh scans it is the
      total no. of points in the mesh
    '''
    #print( "MsUtils.createScanInfo: title %s" % repr(title))
    env = TgUtils.getEnvDct()
    scanInfo = {}
    scanInfo[ 'motors'] = []
    #
    # 1. case: after a scan, ScanHistory can be used
    #
    if title is None:
        if 'ScanHistory' not in list( env.keys()):
            return None 
        lastScan = env['ScanHistory'][-1]

        scanInfo[ 'serialno'] = lastScan['serialno']
        #
        # serialno is from ScanHistory which is created after the scan completed successfully
        # ScanID is updated when a scan starts. ScanID != sericalno may be an indication
        # that the last scan has been ctrl-c'ed
        #
        if TgUtils.getEnv( "ScanID") != scanInfo['serialno']:
            return None
        scanInfo[ 'title'] = lastScan['title']
    #
    # 2. case: from e.g. a hook
    #
    else:
        if type( title) is str:
            scanInfo[ 'title'] = title
            scanInfo[ 'serialno'] = env['ScanID']
        else:
            return None

    scanTitleToScanInfo( scanInfo[ 'title'], scanInfo)

    #print( "MsUtils.createScanInfo %s " % repr( scanInfo))
    return scanInfo
#
#
#
def scanTitleToScanInfo( title, scanInfo):
        
    #print( "MsUtils.py: this is scanTitleToScanInfo, title %s" % title) 

    #
    # if bad syntrax for fscan commands, indepvar contain spaces
    #
    if title is None:
        return 
    
    lst = title.split()
    #
    # ascan exp_dmy01 0 1 10 0.1
    #
    if lst[0] == 'ascan':
        _appendAbs( scanInfo, lst[1], lst[2], lst[3])
        scanInfo[ 'intervals'] = int( lst[4])
        scanInfo[ 'nPts'] = int( lst[4]) + 1
        scanInfo[ 'sampleTime'] = float( lst[5])
    #
    # a2scan exp_dmy01 0 1 exp_dmy02 0 2 10 0.1
    #
    elif lst[0] == 'a2scan':
        _appendAbs( scanInfo, lst[1], lst[2], lst[3])
        _appendAbs( scanInfo, lst[4], lst[5], lst[6])
        scanInfo[ 'intervals'] = int( lst[7])
        scanInfo[ 'nPts'] = int( lst[7]) + 1
        scanInfo[ 'sampleTime'] = float( lst[8])
    #
    # a3scan exp_dmy01 0 1 exp_dmy02 0 2 ... 10 0.1
    #
    elif lst[0] == 'a3scan':
        _appendAbs( scanInfo, lst[1], lst[2], lst[3])
        _appendAbs( scanInfo, lst[4], lst[5], lst[6])
        _appendAbs( scanInfo, lst[7], lst[8], lst[9])
        scanInfo[ 'intervals'] = int( lst[10])
        scanInfo[ 'nPts'] = int( lst[10]) + 1
        scanInfo[ 'sampleTime'] = float( lst[11])

    #
    # ascan_repeat exp_dmy01 0 1 10 0.1 2
    #
    elif lst[0] == 'ascan_repeat':
        _appendAbs( scanInfo, lst[1], lst[2], lst[3])
        scanInfo[ 'intervals'] = int( lst[4])
        scanInfo[ 'nPts'] = int( lst[4]) + 1
        scanInfo[ 'sampleTime'] = float( lst[5])
        scanInfo[ 'repeats'] = int( lst[6])
    #
    # hscan 1.0 1.1 20 0.1
    #
    elif lst[0] == 'hscan':
        if TgUtils.isDevice( 'e6cctrl_h'):
            _appendAbs( scanInfo, 'e6cctrl_h', lst[1], lst[2])
        elif TgUtils.isDevice( 'kozhue6cctrl_h'):
            _appendAbs( scanInfo, 'kozhue6cctrl_h', lst[1], lst[2])
        scanInfo[ 'intervals'] = int( lst[3])
        scanInfo[ 'nPts'] = int( lst[3]) + 1
        scanInfo[ 'sampleTime'] = float( lst[4])
    elif lst[0] == 'kscan':
        if TgUtils.isDevice( 'e6cctrl_k'):
            _appendAbs( scanInfo, 'e6cctrl_k', lst[1], lst[2])
        elif TgUtils.isDevice( 'kozhue6cctrl_k'):
            _appendAbs( scanInfo, 'kozhue6cctrl_k', lst[1], lst[2])
        scanInfo[ 'intervals'] = int( lst[3])
        scanInfo[ 'nPts'] = int( lst[3]) + 1
        scanInfo[ 'sampleTime'] = float( lst[4])
    elif lst[0] == 'lscan':
        if TgUtils.isDevice( 'e6cctrl_l'):
            _appendAbs( scanInfo, 'e6cctrl_l', lst[1], lst[2])
        elif TgUtils.isDevice( 'kozhue6cctrl_l'):
            _appendAbs( scanInfo, 'kozhue6cctrl_l', lst[1], lst[2])
        scanInfo[ 'intervals'] = int( lst[3])
        scanInfo[ 'nPts'] = int( lst[3]) + 1
        scanInfo[ 'sampleTime'] = float( lst[4])
        
    #
    # hklscan 1.0 1.1 2 2.2 3 3.3 20 0.1
    #
    elif lst[0] == 'hklscan':
        diffH = _math.fabs( float( lst[2]) - float( lst[1]))
        diffK = _math.fabs( float( lst[4]) - float( lst[3]))
        diffL = _math.fabs( float( lst[6]) - float( lst[5]))
        if diffH > diffK and diffH > diffL:
            if TgUtils.isDevice( 'e6cctrl_h'):
                _appendAbs( scanInfo, 'e6cctrl_h', lst[1], lst[2])
            elif TgUtils.isDevice( 'kozhue6cctrl_h'):
                _appendAbs( scanInfo, 'kozhue6cctrl_h', lst[1], lst[2])
            if TgUtils.isDevice( 'e6cctrl_k'):
                _appendAbs( scanInfo, 'e6cctrl_k', lst[3], lst[4])
            elif TgUtils.isDevice( 'kozhue6cctrl_k'):
                _appendAbs( scanInfo, 'kozhue6cctrl_k', lst[3], lst[4])
            if TgUtils.isDevice( 'e6cctrl_l'):
                _appendAbs( scanInfo, 'e6cctrl_l', lst[5], lst[6])
            elif TgUtils.isDevice( 'kozhue6cctrl_l'):
                _appendAbs( scanInfo, 'kozhue6cctrl_l', lst[5], lst[6])
        elif diffK > diffH and diffK > diffL:
            if TgUtils.isDevice( 'e6cctrl_k'):
                _appendAbs( scanInfo, 'e6cctrl_k', lst[3], lst[4])
            elif TgUtils.isDevice( 'kozhue6cctrl_k'):
                _appendAbs( scanInfo, 'kozhue6cctrl_k', lst[3], lst[4])
            if TgUtils.isDevice( 'e6cctrl_h'):
                _appendAbs( scanInfo, 'e6cctrl_h', lst[1], lst[2])
            elif TgUtils.isDevice( 'kozhue6cctrl_h'):
                _appendAbs( scanInfo, 'kozhue6cctrl_h', lst[1], lst[2])
            if TgUtils.isDevice( 'e6cctrl_l'):
                _appendAbs( scanInfo, 'e6cctrl_l', lst[5], lst[6])
            elif TgUtils.isDevice( 'kozhue6cctrl_l'):
                _appendAbs( scanInfo, 'kozhue6cctrl_l', lst[5], lst[6])
        elif diffL > diffH and diffL > diffK:
            if TgUtils.isDevice( 'e6cctrl_l'):
                _appendAbs( scanInfo, 'e6cctrl_l', lst[5], lst[6])
            elif TgUtils.isDevice( 'kozhue6cctrl_l'):
                _appendAbs( scanInfo, 'kozhue6cctrl_l', lst[5], lst[6])
            if TgUtils.isDevice( 'e6cctrl_h'):
                _appendAbs( scanInfo, 'e6cctrl_h', lst[1], lst[2])
            elif TgUtils.isDevice( 'kozhue6cctrl_h'):
                _appendAbs( scanInfo, 'kozhue6cctrl_h', lst[1], lst[2])
            if TgUtils.isDevice( 'e6cctrl_k'):
                _appendAbs( scanInfo, 'e6cctrl_k', lst[3], lst[4])
            elif TgUtils.isDevice( 'kozhue6cctrl_k'):
                _appendAbs( scanInfo, 'kozhue6cctrl_k', lst[3], lst[4])
        elif diffH > 0.:
            if TgUtils.isDevice( 'e6cctrl_h'):
                _appendAbs( scanInfo, 'e6cctrl_h', lst[1], lst[2])
            elif TgUtils.isDevice( 'kozhue6cctrl_h'):
                _appendAbs( scanInfo, 'kozhue6cctrl_h', lst[1], lst[2])
            if TgUtils.isDevice( 'e6cctrl_k'):
                _appendAbs( scanInfo, 'e6cctrl_k', lst[3], lst[4])
            elif TgUtils.isDevice( 'kozhue6cctrl_k'):
                _appendAbs( scanInfo, 'kozhue6cctrl_k', lst[3], lst[4])
            if TgUtils.isDevice( 'e6cctrl_l'):
                _appendAbs( scanInfo, 'e6cctrl_l', lst[5], lst[6])
            elif TgUtils.isDevice( 'kozhue6cctrl_l'):
                _appendAbs( scanInfo, 'kozhue6cctrl_l', lst[5], lst[6])
        elif diffK > 0.:
            if TgUtils.isDevice( 'e6cctrl_k'):
                _appendAbs( scanInfo, 'e6cctrl_k', lst[3], lst[4])
            elif TgUtils.isDevice( 'kozhue6cctrl_k'):
                _appendAbs( scanInfo, 'kozhue6cctrl_k', lst[3], lst[4])
            if TgUtils.isDevice( 'e6cctrl_h'):
                _appendAbs( scanInfo, 'e6cctrl_h', lst[1], lst[2])
            elif TgUtils.isDevice( 'kozhue6cctrl_h'):
                _appendAbs( scanInfo, 'kozhue6cctrl_h', lst[1], lst[2])
            if TgUtils.isDevice( 'e6cctrl_l'):
                _appendAbs( scanInfo, 'e6cctrl_l', lst[5], lst[6])
            elif TgUtils.isDevice( 'kozhue6cctrl_l'):
                _appendAbs( scanInfo, 'kozhue6cctrl_l', lst[5], lst[6])
        else:
            if TgUtils.isDevice( 'e6cctrl_l'):
                _appendAbs( scanInfo, 'e6cctrl_l', lst[5], lst[6])
            elif TgUtils.isDevice( 'kozhue6cctrl_l'):
                _appendAbs( scanInfo, 'kozhue6cctrl_l', lst[5], lst[6])
            if TgUtils.isDevice( 'e6cctrl_h'):
                _appendAbs( scanInfo, 'e6cctrl_h', lst[1], lst[2])
            elif TgUtils.isDevice( 'kozhue6cctrl_h'):
                _appendAbs( scanInfo, 'kozhue6cctrl_h', lst[1], lst[2])
            if TgUtils.isDevice( 'e6cctrl_k'):
                _appendAbs( scanInfo, 'e6cctrl_k', lst[3], lst[4])
            elif TgUtils.isDevice( 'kozhue6cctrl_k'):
                _appendAbs( scanInfo, 'kozhue6cctrl_k', lst[3], lst[4])
        scanInfo[ 'intervals'] = int( lst[7])
        scanInfo[ 'nPts'] = int( lst[7]) + 1
        scanInfo[ 'sampleTime'] = float( lst[8])
    #
    # dscan exp_dmy01 -1 1 10 0.1
    #
    elif lst[0] == 'dscan':
        _appendRel( scanInfo, lst[1], lst[2], lst[3])
        scanInfo[ 'intervals'] = int( lst[4])
        scanInfo[ 'nPts'] = int( lst[4]) + 1
        scanInfo[ 'sampleTime'] = float( lst[5])
    #
    # d2scan exp_dmy01 0 1 exp_dmy02 0 2 10 0.1
    #
    elif lst[0] == 'd2scan':
        _appendRel( scanInfo, lst[1], lst[2], lst[3])
        _appendRel( scanInfo, lst[4], lst[5], lst[6])
        scanInfo[ 'intervals'] = int( lst[7])
        scanInfo[ 'nPts'] = int( lst[7]) + 1
        scanInfo[ 'sampleTime'] = float( lst[8])
    #
    # d3scan exp_dmy01 0 1 exp_dmy02 0 2 ... 10 0.1
    #
    elif lst[0] == 'd3scan':
        _appendRel( scanInfo, lst[1], lst[2], lst[3])
        _appendRel( scanInfo, lst[4], lst[5], lst[6])
        _appendRel( scanInfo, lst[7], lst[8], lst[9])
        scanInfo[ 'intervals'] = int( lst[10])
        scanInfo[ 'nPts'] = int( lst[10]) + 1
        scanInfo[ 'sampleTime'] = float( lst[11])

    #
    # dscan_repeat exp_dmy01 -1 1 10 0.1 2
    #
    elif lst[0] == 'dscan_repeat':
        _appendRel( scanInfo, lst[1], lst[2], lst[3])
        scanInfo[ 'intervals'] = int( lst[4])
        scanInfo[ 'nPts'] = int( lst[4]) + 1
        scanInfo[ 'sampleTime'] = float( lst[5])
        scanInfo[ 'repeats'] = int( lst[6])
    #
    # mesh exp_dmy01 0 1 10 exp_dmy02 1 2 12 0.1
    #
    elif lst[0] == 'mesh':
        _appendAbs( scanInfo, lst[1], lst[2], lst[3], lst[4])
        _appendAbs( scanInfo, lst[5], lst[6], lst[7], lst[8])
        scanInfo[ 'nPts'] = (int( lst[4]) + 1)*(int( lst[8]) + 1)
        scanInfo[ 'sampleTime'] = float( lst[9])
    #
    # dmesh exp_dmy01 1 1 10 exp_dmy02 -1 2 12 0.1
    #
    elif lst[0] == 'dmesh':
        _appendRel( scanInfo, lst[1], lst[2], lst[3], lst[4])
        _appendRel( scanInfo, lst[5], lst[6], lst[7], lst[8])
        scanInfo[ 'nPts'] = (int( lst[4]) + 1)*(int( lst[8]) + 1)
        scanInfo[ 'sampleTime'] = float( lst[9])
    #
    # timescan 10 0.1
    #
    elif lst[0] == 'timescan':
        scanInfo[ 'intervals'] = int( lst[1])
        scanInfo[ 'nPts'] = int( lst[1]) + 1
        scanInfo[ 'sampleTime'] = float( lst[2])
    #
    # fscan np=1500 0.1 exp_dmy01 exp_dmy02, this is a fake because I do not calculate start/stop for fscans
    # the real syntax: fscan "x=[1,3,5,7,9],y=arange(5)" 0.1 exp_dmy01 x**2 exp_dmy02 sqrt(y*x+3)
    #
    elif lst[0] == 'fscan':
        #np = int( lst[1].split( '=')[1])
        np = 1500
        nPts = 1
        for mot in lst[ 3:]: 
            _appendAbs( scanInfo, mot, 0, 100, intervals = np)
            nPts = nPts*(np + 1)
        try: 
            scanInfo[ 'sampleTime'] = float( lst[2])
            scanInfo[ 'nPts'] = nPts
        except: 
            scanInfo[ 'sampleTime'] = -1
            scanInfo[ 'nPts'] = -1
    else: 
        pass
    #raise ValueError( "MsUtils.scanTitleToScanInfo: failed to identify scan type %s" % lst[0])
    
    return
#
# ===
#
def repairFscanTitle( title): 
    # 
    # u"fscan x=[0,1,2],y=[10,11,12] 0.1 \
    #    [[Motor(tango://haso107tk.desy.de:10000/motor/dummy_mot_ctrl/1), 'x'], \
    #     [Motor(tango://haso107tk.desy.de:10000/motor/dummy_mot_ctrl/2), 'y']]"
    # -> 'fscan' np=3 0.1 exp_dmy0 exp_dmy02'

    # about fscan syntax, see remark in diary 17.3.2023

    lines = title.split( ' ')

    try: 
        nameSpace = {}
        exec( "a = dict( %s)" % lines[1], nameSpace)
        lengths = []
        lenMin = 10000000000
        for elm in nameSpace[ 'a']:
            if len( nameSpace[ 'a'][ elm]) < lenMin: 
                lenMin = len( nameSpace[ 'a'][ elm]) 
    except: 
        lenMin = 1500

    cmdLine = lines[0] + " "
    cmdLine += "np=%d " % lenMin
    cmdLine += lines[2] + " "
        
    temp = ""
    for line in lines[3:]: 
        temp += line
    temp = temp.replace( 'Motor(tango://', '\'')
    temp = temp.replace( ')', '\'')
        
    try: 
        nameSpace = {}
        exec( "a = %s" % temp, nameSpace)
        for elm in nameSpace[ 'a']: 
            p = _PyTango.DeviceProxy( elm[0])
            cmdLine += " %s" % (p.alias())
    except Exception as e: 
        cmdLine = None
        #raise Exception( "MsUtils.RepairFscanTitle", "failed to parse %s" % title)
    
    return cmdLine


def dataRecordToScanInfo( dataRecord):
    '''
    creates the scanInfo dictionary from the  first dataRecord

    scanInfo: 
      {'title': u'ascan exp_dmy01 0.0 0.1 10 0.1', 
      'serialno': 1775, 
      'motors': [{'start': 0.0, 'stop': 0.1, 'name': u'exp_dmy01', 'proxy': Motor(motor/dummy_mot_ctrl/1)}], 
      'scanfile': [u'tst.fio', u'tst.nxs'],
      'filename': [u'tst_01780.fio', u'tst_01780.nxs'],
      'starttime': u'Thu Oct 13 15:35:48 2016', 
      'scandir': u'/home/kracht/Misc/IVP/temp'}
    '''
    scanInfo = {}
    scanInfo['scanfile'] = dataRecord[1]['data'][ 'scanfile']
    if scanInfo['scanfile'] is None:
        raise Exception( "MsUtils.dataRecordToScanInfo", "scanfile not defined")
    scanInfo['scandir'] = dataRecord[1]['data'][ 'scandir']
    if scanInfo['scandir'] is None:
        raise Exception( "MsUtils.dataRecordToScanInfo", "scandir not defined")
    scanInfo['serialno'] = dataRecord[1]['data'][ 'serialno']

    scanInfo['filename'] = []
    if type(scanInfo['scanfile']) is list:
        for sf in scanInfo['scanfile']:
            tpl = sf.rpartition('.')
            scanInfo['filename'].append( "%s_%05d.%s" % (tpl[0], scanInfo['serialno'], tpl[2]))
    else:
        tpl = scanInfo['scanfile'].rpartition('.')
        scanInfo['filename'].append( "%s_%05d.%s" % (tpl[0], scanInfo['serialno'], tpl[2]))

    scanInfo['starttime'] = dataRecord[1]['data']['starttime']
    if dataRecord[1]['data']['title'].find( 'fscan') == 0:
        scanInfo['title'] = repairFscanTitle( dataRecord[1]['data']['title'])
    else: 
        scanInfo['title'] = dataRecord[1]['data']['title']
    #
    # scanInfo is None for an fscan command spaces in the indepvar definition
    #
    if scanInfo is not None:
        scanInfo[ 'motors'] = []
        scanTitleToScanInfo( scanInfo[ 'title'], scanInfo)

    return scanInfo

def doorAbortMacro( doorName = None): 
    '''
    executes abortMacro() on the specified Door 
    or choses the first Door. This is more than
    executing abort()
    '''
    if doorName is None: 
        try: 
            doorName = TgUtils.getDoorNames()[0]
        except Exception as e: 
            print( "MsUtils.abortMacro: failed to get doorName")
            print( repr( e))
            return False

    p = _PyTango.DeviceProxy( doorName)
    p.abortMacro()

    return True
    

#!python
""" 
saves the motor positions to 
      /online_dir/MotorLogs/motorLog.lis 
"""
import PyTango
import os, sys, time
from optparse import OptionParser

try:
    import HasyUtils
except Exception as e: 
    print( "Failed to import HasyUtils")
    print( e)
    sys.exit(255)

motorAttributes = [ 'Acceleration',
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

servoAttributes = [ 'DerivativeGain',
                    'IntegralGain',
                    'ProportionalGain',
                    ]

encoderAttributes = [ 'ConversionEncoder', 
                      'CorrectionGain', 
                      'EncoderRatio',
                      'HomePosition',
                      'PositionEncoder',
                      'PositionEncoderRaw',
                      'StepDeadBand', 
                      'SlewRateCorrection', 
                      'SlipTolerante', 
                    ]
# DelayTime
#  Set value from 0 to 15. 
#  Read value in ms:\n0=1, 1=2,2=4,3=6,4=8,5=10,6=12,7=14,8=16,9=20,10=40,\n11=60,12=100, 13=200, 14=500, 15=1000
#

delayTimeDict = { 1: 0, 2: 1, 4: 2, 6: 3, 8: 4, 10: 5, 12: 6, 14: 7, 16: 6, 20: 9, 40: 10, 60: 11, 100: 12, 200: 13, 500: 14, 1000: 15}

zmxAttributes = [ 'AxisName', 
                  'Deactivation', 
                  'DeactivationStr', 
                  'DelayTime', 
                  'Error',
                  'InputLogicLevel',
                  'InputLogicLevelStr',
                  'IntermediateVoltage',
                  'Overdrive',
                  'OverdriveStr',
                  'PreferentialDirection',
                  'PreferentialDirectionStr',
                  'RunCurrent',
                  'StepWidth',
                  'StepWidthStr',
                  'StopCurrent',
                  'Temperature',
]
#
# --- main
#
def main():
    usage = "%prog -x [-q] [-c <progName>]\n" + \
            "Reads /online_dir/online.xml to create a new version of\n \
            /online_dir/MotorLogs/motorLog.lis\n \
            Device names are printed, if stdout is a TTY AND -q is not supplied.\n\
            <progName> is written to the log-file, if supplied.\n\
            \n\
            If a motor has the property ZMXDevice, the attributes of the ZMX \n\
            device are also stored. \n\
            \n\
            If /online_dir/online.xml does not exist, the Tango DB is queried for \n\
            motor classes"
    parser = OptionParser(usage=usage)
    parser.add_option( "-x", action="store_true", dest="execute", 
                       default = False, help="execute")
    parser.add_option( "-q", action="store_true", dest="quiet", 
                       default = False, help="quiet")
    parser.add_option( "-c", action="store", type="string", default = "unknown", 
                       dest="caller", help="name of the calling program, e.g. 'spock' or 'cron'")
    parser.add_option( "-f", action="store", type="string", default = "motorLog", 
                       dest="filename", help="file name, e.g.: motorLogShutdown (always in /online_dir/MotorLogs)")
    parser.add_option( "-z", action="store_true", dest="ignoreZMX", 
                       default = False, help="ignoreZMX")

    (options, args) = parser.parse_args()

    if options.execute is False:
        parser.print_help()
        sys.exit(255)

    flagTTY = False
    if options.quiet is False:
        if os.isatty(1):
            flagTTY = True

    if flagTTY:
        print( "MotorLogger.py starting")

    #
    # this feature is for the use case where the MotorLogger is launched from 
    # /usr/local/bin/tangodebug.sh after the PC rebooted. We have to 
    # wait for the motor servers servers to get started and also the MacroServer
    # which tells us that even Sardana is up and running
    #
    lst = []
    clssList = ['OmsVme58', 'OmsMaxV', 'Spk', 'MacroServer']
    try:
        for elm in clssList:
            lst.extend( HasyUtils.getServerNameByClass( elm))
    except Exception as e:
        print( "MotorLogger: exception")
        print( e)
        sys.exit(0)
    if len( lst) == 0:
        print( "MotorLogger: none of these motor servers are configured: %s" % str(clssList))
        sys.exit( 255)

    atLeastOneRunningServer = False
    for elm in lst:
        maxWait = 10
        #
        # if the system uptime is less than 15 minutes, wait for the servers for 15 minutes
        #
        if HasyUtils.uptime() < 900:
            maxWait = 900
        if HasyUtils.waitForServer( elm, maxWait):
            if flagTTY:
                print( "MotorLogger: server %s is running" % elm)
            atLeastOneRunningServer = True
        else:
            print( "waitForServer: %s not running %s" % (elm, repr( time.asctime())))

    if not atLeastOneRunningServer:
        print( "MotorLogger: none of these servers are running %s" % str( lst))
        sys.exit( 255)
    
    tmStart = time.localtime()
    hshList = HasyUtils.getOnlineXML( xmlFile = '/online_dir/online.xml')
    #
    # hshList == None means that there is no /online_dir/online.xml
    # if this is the case, we look at classes
    #

    if hshList is None:
        if not 'TANGO_HOST' in os.environ:
            print( "No local online.xml and TANGO_HOST not defined")
            sys.exit(255)

        hostName = os.environ[ 'TANGO_HOST'].split(':')[0]
        hshList = []    
        lst = HasyUtils.getDeviceNamesByClass( "OmsVme58")
        for elm in lst:
            dct = {}
            dct[ 'name'] = HasyUtils.getAlias( elm)
            dct[ 'device'] = elm
            dct[ 'module'] = "oms58"
            dct[ 'type'] = "stepping_motor"
            dct[ 'hostname'] = hostName + ":10000"
            hshList.append( dct)
        lst = HasyUtils.getDeviceNamesByClass( "OmsMaxV")
        for elm in lst:
            dct = {}
            print( "appending %s" % str(elm))
            dct[ 'name'] = HasyUtils.getAlias( elm)
            dct[ 'device'] = elm
            dct[ 'module'] = "omsmaxv"
            dct[ 'type'] = "stepping_motor"
            dct[ 'hostname'] = hostName + ":10000"
            hshList.append( dct)
        lst = HasyUtils.getDeviceNamesByClass( "Spk")
        for elm in lst:
            dct = {}
            print( "appending %s" % elm)
            dct[ 'name'] = HasyUtils.getAlias( elm)
            dct[ 'device'] = elm
            dct[ 'module'] = "spk"
            dct[ 'type'] = "stepping_motor"
            dct[ 'hostname'] = hostName + ":10000"
            hshList.append( dct)
    #
    # resultsLis for the .lis file
    #
    resultsLis = []
    resultsPython = []
    for hsh in hshList:
        #
        # name: d1_mot72
        # type: stepping_motor
        # module: oms58
        # device: p09/motor/d1.72
        # control: tango
        # hostname: haso107d1:10000
        # controller: oms58_d1
        # channel: 72
        # rootdevicename: p09/motor/d1
        #
        modules = []
        #
        # MGs have module == "None"
        #
        if( hsh['module'].lower() == 'none' or
            hsh['module'].lower() == 'counter_tango' or
            hsh['type'].lower() == 'adc' or
            hsh['type'].lower() == 'counter' or
            hsh['type'].lower() == 'dac' or
            hsh['type'].lower() == 'detector' or
            hsh['type'].lower() == 'input_register' or
            hsh['type'].lower() == 'output_register' or
            hsh['type'].lower() == 'timer'):
            continue

        #
        # motors are identified by module types
        #

        if( hsh['module'].lower() != 'oms58' and
            hsh['module'].lower() != 'omsmaxv' and
            hsh['module'].lower() != 'spk' and
            hsh['module'].lower() != 'motor_tango'):
            continue

        if flagTTY:
            print( "Create proxy to %s %s %s " % (hsh[ 'hostname'], hsh['name'], hsh[ 'device']))

        try:
            p = PyTango.DeviceProxy( "%s/%s" % (hsh[ 'hostname'], hsh[ 'device']))
        except:
            resultsLis.append( " failed to create proxy to %s/%s \n" % (hsh['hostname'], hsh[ 'device']))
            resultsPython.append( " failed to create proxy to %s/%s \n" % (hsh['hostname'], hsh['device']))
            continue
        try:
            sts = p.state()
        except Exception as e:
            if e.args[0].reason == 'API_DeviceNotExported':
                if options.quiet is False:
                    print( " MotorLogger: DeviceNotExported %s/%s" % (hsh['hostname'], hsh[ 'device']))
                resultsLis.append( " DeviceNotExported %s/%s \n" % (hsh['hostname'], hsh[ 'device']))
                resultsPython.append( " DeviceNotExported  %s/%s \n" % (hsh['hostname'], hsh['device']))
            elif e.args[0].desc.find( "TRANSIENT_ConnectFailed") > 0:
                if options.quiet is False:
                    print( " MotorLogger: TRANSIENT_ConnectFailed %s/%s" % (hsh['hostname'], hsh[ 'device']))
                resultsLis.append( " TRANSIENT_ConnectFailed %s/%s \n" % (hsh['hostname'], hsh[ 'device']))
                resultsPython.append( " TRANSIENT_ConnectFailed  %s/%s \n" % (hsh['hostname'], hsh['device']))
            else: 
                resultsLis.append( " failed to read state of %s/%s, %s \n" % (hsh['hostname'], hsh[ 'device'], repr( e)))
                resultsPython.append( " failed to read of  %s/%s, %s \n" % (hsh['hostname'], hsh['device'], repr( e)))
            continue

        #
        # if the device has no position, it is not a motor
        #

        try: 
            if not HasyUtils.proxyHasAttribute( p, "position"):
                continue
        except Exception as e: 
            print( "MotorLogger: proxy to %s/%s has no position attr" % (hsh[ 'hostname'], hsh[ 'device']))
            print( repr( e))
            continue

        resultsLis.append( "#\n")
        resultsPython.append( "#\n")
        resultsPython.append( "# %s \n" % hsh['name'])
        resultsPython.append( "print \" restoring %s/%s (%s) \"\n" % (hsh[ 'hostname'], hsh['device'], hsh['name']))
        resultsPython.append( "proxy = PyTango.DeviceProxy( \"%s/%s\")\n" % (hsh[ 'hostname'], hsh[ 'device']))

        #
        # we log encoder attributes only, if the FlagEncoder property is '1'
        #
        attrs = motorAttributes[:]
        try:
            if( len( p.get_property('FlagEncoder')['FlagEncoder']) > 0 and
                p.get_property('FlagEncoder')['FlagEncoder'][0] == '1'): 
                attrs.extend( encoderAttributes)
        except:
            print( "Trouble getting FlagEncoder for %s" % p.dev_name())

        for attr in attrs:
            #
            # python3-sardana issue, hasattr() crashes
            #
            flag = False
            try:
                flag = HasyUtils.proxyHasAttribute( p, attr)
            except Exception as e: 
                pass

            if flag:
                try:
                    attrValue = p.read_attribute( attr.lower()).value
                    attrInfo = p.get_attribute_config( attr.lower())
                except:
                    continue

                if attr.lower() == 'position':
                    resultsLis.append( "%s %s %s: %g [Attr. config.: %s, %s]\n" % \
                                       ( hsh['name'], p.dev_name(), attr, attrValue, 
                                         str(attrInfo.min_value), str( attrInfo.max_value)))
                else:
                    resultsLis.append( "%s %s %s: %g\n" % ( hsh['name'], p.dev_name(), attr, attrValue))

                if attr.lower() == 'position':
                    resultsPython.append( "# proxy.write_attribute( \"%s\", %s) [Attr. config: %s, %s]\n" % \
                                          (attr.lower(), attrValue, str(attrInfo.min_value), str( attrInfo.max_value)))
                    continue

                if attrInfo.writable == PyTango._PyTango.AttrWriteType.READ_WRITE:
                    # resultsPython.append( "print \"  %s: %s\"\n" % (attr.lower(), attrValue))
                    resultsPython.append( "proxy.write_attribute( \"%s\", %s)\n" % (attr.lower(), attrValue))
                else:
                    resultsPython.append( "# read-only attribute %s: %s\n" % (attr.lower(), attrValue))

        try:
            attrValue = p.read_attribute( "UnitCalibrationUser").value
            # resultsPython.append( "print \"  UnitCalibrationUser: 0.0\"\n")
            resultsPython.append( "proxy.write_attribute( \"UnitCalibrationUser\", 0.0)\n")
        except:
            pass

        if len( p.get_property('ZMXDevice')['ZMXDevice']) > 0:
            if options.ignoreZMX:
                continue
            try: 
                zmxName = p.get_property('ZMXDevice')['ZMXDevice'][0]
                proxyZMX = PyTango.DeviceProxy( zmxName) 
                state = proxyZMX.state()
            except Exception as e:
                resultsLis.append( "# ZMXDevice %s, error" % zmxName)
                resultsPython.append( "#ZMXDevice %s, error" % zmxName)
                resultsLis.append( "# %s" % repr( e))
                resultsPython.append( "# %s" % repr( e))
                if flagTTY:
                    print( "MotorLogger %s, error %s" % (zmxName, repr( e)))
                continue
            resultsLis.append( "#\n# %s uses ZMX device %s\n" % (p.name(), proxyZMX.name()))
            resultsPython.append( "#\n# %s uses ZMX device %s\n" % (p.name(), proxyZMX.name()))
            resultsPython.append( "proxyZMX = PyTango.DeviceProxy( \"%s\")\n" % zmxName)
            for attr in zmxAttributes:
                try: 
                    attrValue = proxyZMX.read_attribute( attr.lower()).value
                    attrInfo = proxyZMX.get_attribute_config( attr.lower())
                    if attr.lower() == 'delaytime': 
                        if attrValue in list( delayTimeDict.keys()): 
                            resultsLis.append( "%s %s %s: %s (notice, read-value != write-value)\n" % 
                                               ( hsh['name'], proxyZMX.dev_name(), attr, str( attrValue)))
                            resultsPython.append( "# delayTime read-value %d maps to write-value %d\n" % (attrValue, delayTimeDict[ attrValue]))
                            resultsPython.append( "proxyZMX.write_attribute( \"%s\", %s)\n" % (attr.lower(), str( delayTimeDict[ attrValue])))
                    elif attr.lower() == 'axisname': 
                        resultsLis.append( "%s %s %s: %s\n" % ( hsh['name'], proxyZMX.dev_name(), attr, str(attrValue)))
                        if attrInfo.writable == PyTango._PyTango.AttrWriteType.READ_WRITE:
                            resultsPython.append( "proxyZMX.write_attribute( \"%s\", \"%s\")\n" % (attr.lower(), str( attrValue)))
                        else:
                            resultsPython.append( "# read-only attribute %s: \"%s\"\n" % (attr.lower(), str(attrValue)))
                    else: 
                        resultsLis.append( "%s %s %s: %s\n" % ( hsh['name'], proxyZMX.dev_name(), attr, str(attrValue)))
                        if attrInfo.writable == PyTango._PyTango.AttrWriteType.READ_WRITE:
                            resultsPython.append( "proxyZMX.write_attribute( \"%s\", %s)\n" % (attr.lower(), str( attrValue)))
                        else:
                            resultsPython.append( "# read-only attribute %s: %s\n" % (attr.lower(), str(attrValue)))

                except Exception as e:
                    print( "ZMXDevice %s, error" % proxyZMX.dev_name())
                    print( "%s" % repr( e))

    if not os.path.isdir( '/online_dir/MotorLogs'):
        try:
            os.mkdir( '/online_dir/MotorLogs')
        except:
            print( "Failed to create /online_dir/MotorLogs")
            sys.exit(255)


    if os.path.exists( "/online_dir/MotorLogs/%s.lis" % options.filename):
        os.system( "vrsn -nolog -s /online_dir/MotorLogs/%s.lis" % options.filename)
    if os.path.exists( '/online_dir/MotorLogs/motorLog.py'):
        os.system( "vrsn -nolog -s /online_dir/MotorLogs/motorLog.py")


    try:
        out = open( "/online_dir/MotorLogs/%s.lis" % options.filename, 'w')
    except:
        print( "Failed to open /online_dir/MotorLogs/%s.lis" % options.filename )
        sys.exit(255)

    out.write( "#\n# Created at %02d.%02d.%d %02d:%02dh by %s \n#\n" % 
               (tmStart[2], tmStart[1], tmStart[0], tmStart[3], tmStart[4], options.caller))
    out.writelines( resultsLis)

    tmStop = time.localtime()
    out.write( "#\n# Closed at %02d.%02d.%d %02d:%02dh \n#\n" % 
               (tmStop[2], tmStop[1], tmStop[0], tmStop[3], tmStop[4]))
    out.close()

    try:
        out = open( '/online_dir/MotorLogs/motorLog.py', 'w')
    except:
        print( "Failed to open /online_dir/MotorLogs/motorLog.py")
        sys.exit(255)
                  
    out.write( "#!/usr/bin/env python\n")
    out.write( "#\n# Created at %02d.%02d.%d %02d:%02dh by %s \n" % 
               (tmStart[2], tmStart[1], tmStart[0], tmStart[3], tmStart[4], options.caller))
    out.write( "#\n")
    out.write( "# This file can be executed to restore motor attributes.\n")
    out.write( "# However, the positions are NOT touched, except through UnitCalibration.\n")
    out.write( "# \n")
    out.write( "import PyTango\n")
    out.writelines( resultsPython)

    tmStop = time.localtime()
    out.write( "#\n# Closed at %02d.%02d.%d %02d:%02dh \n#\n" % 
               (tmStop[2], tmStop[1], tmStop[0], tmStop[3], tmStop[4]))

    out.close()

    if flagTTY:
        print( "MotorLogger.py DONE")
    return 

if __name__ == "__main__": 
    main()

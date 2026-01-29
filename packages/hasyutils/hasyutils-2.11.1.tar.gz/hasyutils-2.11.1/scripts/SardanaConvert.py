#!/usr/bin/python3
import os, sys
from optparse import OptionParser
import os, time, socket
import HasyUtils
import PyTango
db = None
dbProxy = None
nb_attrctctrl = 0
nb_attriorctrl = 0
nb_attrzerodctrl = 0
nb_attronedctrl = 0
outFile = None

predefined_oms58 = [ ( 'delay/motor/exp', 'omsvme58_exp'), 
                     ( 'fmc/motor/mob', 'omsvme58_mob'), 
                     ( 'llab/motor/mot', 'omsvme58_mot'),
                     ( 'slm/motor/lab', 'omsvme58_lab'),
                     ( 'p01/motor/exp', 'omsvme58_p01exp'), # they are used at p09, can not be called omsvme58_exp
                     ( 'p01/motor/eh1', 'omsvme58_eh1'), 
                     ( 'p01/motor/eh2', 'omsvme58_eh2'), 
                     ( 'p01/motor/eh3', 'omsvme58_eh3'), 
                     ( 'p01/motor/oh1', 'omsvme58_oh1'), 
                     ( 'p01/motor/oh2', 'omsvme58_oh2'), 
                     ( 'p02/motor/oh1', 'omsvme58_oh1'), 
                     ( 'p02/motor/exp', 'omsvme58_exp'), 
                     ( 'p02/motor/eh1a', 'omsvme58_eh1a'), 
                     ( 'p02/motor/eh2a', 'omsvme58_eh2a'), 
                     ( 'p02/motor/eh1b', 'omsvme58_eh1b'), 
                     ( 'p02/motor/ecsi', 'omsvme58_ecsi'),
                     ( 'p02/motor/eh2b', 'omsvme58_eh2b'),
                     ( 'p03/motor/expmi', 'omsvme58_expmi'),
                     ( 'p03/motor/p03nano', 'omsvme58_p03nano'),
                     ( 'p04/motor/exp1', 'omsvme58_exp1'),
                     ( 'p04/motor/exp2', 'omsvme58_exp2'),
                     ( 'p06/motor/exp', 'omsvme58_exp'),
                     ( 'p06/motor/mono', 'omsvme58_mono'),
                     ( 'p06/motor/mi', 'omsvme58_mi'),
                     ( 'p06/motor/na', 'omsvme58_na'),
                     ( 'p07/motor/eh1', 'omsvme58_eh1'),
                     ( 'p07/motor/eh2', 'omsvme58_eh2'),
                     ( 'p07/motor/eh2a', 'omsvme58_eh2a'), 
                     ( 'p07/motor/eh3', 'omsvme58_eh3'),
                     ( 'p07/motor/eh4', 'omsvme58_eh4'),
                     ( 'p07/motor/oh2', 'omsvme58_oh2'), 
                     ( 'p08/motor/exp', 'omsvme58_exp'),
                     ( 'p08/motor/mono', 'omsvme58_mono'),
                     ( 'p09/motor/d1', 'omsvme58_d1'), 
                     ( 'p09/motor/eh', 'omsvme58_eh'), 
                     ( 'p09/motor/exp', 'omsvme58_exp'), 
                     ( 'p09/motor/dif', 'omsvme58_dif'), 
                     ( 'p09/omsvme58/difsimu', 'omsvme58_difsimu'),
                     ( 'p09/omsvme58/difsimueh2', 'omsvme58_difsimueh2'),
                     ( 'p09/motor/mag', 'omsvme58_mag'),
                     ( 'p09/motor/mono', 'omsvme58_mono'),
                     ( 'p09/motor/haxps', 'omsvme58_haxps'),
                     ( 'p09/motor/eh', 'omsvme58_eh'),
                     ( 'p10/motor/e1', 'omsvme58_e1'),
                     ( 'p10/motor/e2', 'omsvme58_e2'),
                     ( 'p10/motor/opt', 'omsvme58_opt'),
                     ( 'p10/motor/labsimu', 'omsvme58_labsimu'),
                     ( 'p10/motor/lab', 'omsvme58_lab'),
                     ( 'p11/motor/eh_pp1', 'omsvme58_eh_pp1'),
                     ( 'p11/motor/EH_PP2', 'omsvme58_eh_pp2'),
                     ( 'p11/motor/EH_PP3', 'omsvme58_eh_pp3'),
                     ( 'p11/motor/granite', 'omsvme58_granite'),
                     ( 'p11/motor/lab', 'omsvme58_lab'),
                     ( 'p11/motor/oh', 'omsvme58_oh'),
                     ( 'p11/motor/eh.1', 'omsvme58_eh1'),
                     ( 'p11/motor/eh.2', 'omsvme58_eh2'),
                     ( 'p11/motor/eh.3', 'omsvme58_eh3'),
                     ( 'p11/servomotor/eh', 'omsvme58_servo_eh'),
                     ( 'l136/motor/l136', 'omsvme58_l136'),
                     ( 'p23/omsvme58/dev', 'omsvme58_dev'),
                     ( 'p24/motor/exp', 'omsvme58_exp'), 
                     ( 'p64/motor/exp', 'omsvme58_exp'), 
                     ( 'p64/motor/oh', 'omsvme58_oh'), 
                     ( 'p65/motor/a2', 'omsvme58_a2'), 
                     ( 'p66/motor/exp', 'omsvme58_exp'), 
]

#
#
#
def _print( argin):
    outFile.write( argin + "\n")
#
#<device>
# <name>exp_t01</name>
# <sardananame>exp_t01</sardananame>
# <tags>expert,user</tags>
# <type>timer</type>
# <module>dgg2</module>
# <device>p09/dgg2/exp.01</device>
# <control>tango</control>
# <hostname>haso107klx:10000</hostname>
# <pool>pool_haso107klx</pool>
# <controller>dgg2_exp_01</controller>
# <channel>1</channel>
# <rootdevicename>p09/dgg2/exp.01</rootdevicename>
#</device>
#
def printDevice( a):
    """ 
    writes the xml device entry to stdout, even if the controller 
    tag is missing (because the device hasn't been converted yet)
    """    
    itemsTango =   [ 'name', 'tags', 'mgs', 'hkl', 'roi', 'type', 'module', 'device', 'control', 'hostname', 'ior_labels', 'ior_calibration', 'pseudomotor', 'mode', 'ipaddress', 'portno']
    itemsSardana = [ 'pool', 'controller', 'channel', 'rootdevicename', 'sardananame']
    #
    # check itemsTango first, the item 'tags' is optional, 'mgs' only for measurement groups, 'hkl' only for diffractometers, 'roi' is only for onedroi and limaroicounter, 'ior_labels' and 'ior_calibration' are only for ioregisters from the class TangoAttrIORController.
    #
    for k in itemsTango:
        if k not in a:
            if k == 'tags' or k == 'mgs' or k == 'hkl' or k == 'roi' or k == 'ior_labels' or \
               k == 'ior_calibration' or k == 'pseudomotor' or k == 'mode' or k == 'ipaddress' or k == 'portno': 
                continue
            _print( "printDevice: tangoKey %s is missing" % k)
            return 0
    # 1.12.2023, taken out because of problems reported by p1 and p09 #1336541
    localPool = "pool_%s" % HasyUtils.getHostname()
    #localHostName = HasyUtils.getHostname()
    #localTangoHost = os.getenv('TANGO_HOST')
    #localPool = "pool_%s" % localHostName
    #
    # if the controller item exists, the other Sardana 
    # items have to be present as well
    #
    flagSardana = False
    if 'controller' in a:
        a['pool'] = localPool

        #if options.displayStarterHosts:
        #    print( " %s runs on %s" % ( a['device'], a['pool']))
        for k in itemsSardana:
            if k not in a:
                #
                # sardananame is an optional key
                #
                if k.find('sardananame') == 0: 
                    continue
                print( "printDevice: sardanaKey %s is missing in %s " % (k, a['name']))
                return 0
        flagSardana = True

    _print( "<device>")
    for k in itemsTango + itemsSardana:
        if k not in a:
            continue
        ## 1.12.2023, taken out because of: #1336541
        ## extend the controller name by hostname to avoind conflicts
        ## like at p10, omsvme58_exp from both TANGO_HOSTs
        ## 
        ## <controller>haso107d1_omsvme58_eh</controller>
        ##
        ## this is done only, if hostName is not the local host
        ##
        ## some d'devices', e.g. measurement_groups have controller == 'None'
        ##
        ## +++
        #if k == 'controller' and a[ k].upper() != 'NONE' and localTangoHost != a[ 'hostname']:
        #    hostName = a[ 'hostname']
        #    if hostName.find( ':'):
        #        hostName = hostName.split( ':')[0]
        #    temp = "%s_%s" %  ( hostName, a[ 'controller'])
        #    _print( " <%s>" % k + temp + "</%s>" % k)
        #    if a[ 'controller'] == 'None': 
        #        print( "%s" % repr( a))
        #else: 
        #    _print( " <%s>" % k + a[ k] + "</%s>" % k)
        # +++
        _print( " <%s>" % k + a[ k] + "</%s>" % k)
        
    if not flagSardana:
        _print( " <!-- +++ not yet converted to Sardana +++ -->")
    _print( "</device>")
    return 1


def find_channel_number(hostname, rootname, device_name):
    '''
    +++
    '''
    #print( "+++SardanaConvert.find_channel_number host %s, root %s, device_name %s" % ( hostname, rootname, device_name))
    node = hostname.split(':')[0]
    port = 10000
    try: 
        db = PyTango.Database( node, port)
    except Exception as e: 
        print( "SardanaConvert.find_channel_number: exception for %s %d" % (node, port))
        print( "%s" % repr( e))
        return -1

    name_dev_ask =  rootname + "*"
    devices = db.get_device_exported(name_dev_ask)
    counter = 1
    argout = None
    if device_name.find(':') >= 0:
        device_name = device_name.split('/',1)[1]
    for name in devices.value_string:
        if device_name.lower() == name.lower():
            argout = counter
            break
        counter = counter + 1
    #print( "SardanaConvert.find_channel_number: trouble with %s, rootname %s, device_name %s NOT EXPORTED?" % (hostname, rootname, device_name))
    #print( "+++SardanaConvert.find_channel_number channel %s" % (str(argout)))
    if argout is None: 
        argout = -1
    return argout

#
#
#
def main():
    """
    If flagManyPools == True, a Pool is created for each Starter host. 
    The idea is to identify those Pools that are commonly use by
    multiple SardanaHosts and merge the other Pools
    """
    #
    # save the input .xml file - just in case
    #
    if os.path.exists( '/usr/local/bin/vrsn'):
        os.system( 'vrsn -nolog -s ' + options.xmlFileIn)
    

    if options.tags is not None:
        lst = [x.strip() for x in options.tags.split()]
    else:
        lst = None

    hshList = HasyUtils.getOnlineXML( xmlFile = options.xmlFileIn, cliTags = lst)

    #
    # if the syntax of online.xml is not ok
    #
    if hshList is None:
        sys.exit(255)

    _print( "<?xml version=\"1.0\"?>")
    _print( "<!--\n Converted from %s:%s \n" % (socket.gethostname(), options.xmlFileIn))
    _print( " Do not edit this file. All changes are overwritten")
    _print( " during the conversion step. \n--> ")
    _print( "<hw>")

    channel_mythenmcasisroi  = {}
    channel_xmcd  = {}
    channel_onedroi  = {}
    channel_limaroicounter = {}
    channel_xspress3roi = {}

    for hsh in hshList:
        #
        # attributeMotor
        #
        if hsh[ 'device'].find( 'attributemotor') >= 0:
            hsh['controller'] = 'am_' + hsh['name']
            hsh['channel'] = '1'
            hsh['rootdevicename'] = hsh['device']
        #
        # petra current
        #
        elif hsh[ 'device'].find( 'vcexecutor/petra.01') >= 0:
            hsh['controller'] = 'petra_' + hsh['name']
            hsh['channel'] = '1'
            hsh['rootdevicename'] = hsh['device']
        #
        # attributes as counters
        #
        elif hsh[ 'module'] == 'tangoattributectctrl':
            global nb_attrctctrl
            nb_attrctctrl = nb_attrctctrl + 1
            hsh['controller'] = hsh['module']
            try: 
                if ( (hsh['device'].find(':') > 0 and len(hsh['device'].split('/')) == 5) or
                     (hsh['device'].find(':') < 0 and len(hsh['device'].split('/')) == 4) ):
                    hsh['rootdevicename'] = hsh['device']
                else:   
                    hsh['rootdevicename'] = hsh['device'] +  "/" +  hsh['name'].split('_')[1]
            except Exception as e: 
                print( "SardanaConvert: error, wrong tangoattributectctrl syntax for %s" % hsh[ 'name'])
                print( "  %s" % repr( hsh))
                print( "  check /online_dir/online.xml")
                print( "  the attribute has to appear as a postfix in 'name', appended with '_'")
                print( "  or in 'device', appended with '/'")
                sys.exit( 255) 
                
            hsh['channel'] = "%d" % int(nb_attrctctrl)
        #
        # attributes as zerod
        #
        elif hsh[ 'module'] == 'tangoattributezerodctrl':
            global nb_attrzerodctrl
            nb_attrzerodctrl = nb_attrzerodctrl + 1
            hsh['controller'] = hsh['module']
            try: 
                if ( (hsh['device'].find(':') > 0 and len(hsh['device'].split('/')) == 5) or
                     (hsh['device'].find(':') < 0 and len(hsh['device'].split('/')) == 4) ):
                    hsh['rootdevicename'] = hsh['device']
                else:   
                    hsh['rootdevicename'] = hsh['device'] +  "/" +  hsh['name'].split('_')[1]
            except Exception as e: 
                print( "SardanaConvert: error, wrong tangoattributezerodctrl syntax for %s" % hsh[ 'name'])
                print( "  %s" % repr( hsh))
                print( "  check /online_dir/online.xml")
                print( "  the attribute has to appear as a postfix in 'name', appended with '_'")
                print( "  or in 'device', appended with '/'")
                sys.exit( 255) 

            hsh['channel'] = "%d" % int(nb_attrzerodctrl)
        #
        # attributes as oned
        #
        elif hsh[ 'module'] == 'tangoattributeonedctrl':
            global nb_attronedctrl
            nb_attronedctrl = nb_attronedctrl + 1
            hsh['controller'] = hsh['module']
            try: 
                if ( (hsh['device'].find(':') > 0 and len(hsh['device'].split('/')) == 5) or
                     (hsh['device'].find(':') < 0 and len(hsh['device'].split('/')) == 4) ):
                    hsh['rootdevicename'] = hsh['device']
                else:   
                    hsh['rootdevicename'] = hsh['device'] +  "/" +  hsh['name'].split('_')[1]
            except Exception as e: 
                print( "SardanaConvert: error, wrong tangoattributeonedctrl syntax for %s" % hsh[ 'name'])
                print( "  %s" % repr( hsh))
                print( "  check /online_dir/online.xml")
                print( "  the attribute has to appear as a postfix in 'name', appended with '_'")
                print( "  or in 'device', appended with '/'")
                sys.exit( 255) 

            hsh['channel'] = "%d" % int(nb_attronedctrl)
        #
        # vcexecutor
        # 
        elif hsh[ 'device'].find( 'vcexecutor') >= 0:
            hsh['controller'] = 'vc_' + hsh['name']
            hsh['channel'] = '1'
            hsh['rootdevicename'] = hsh['device']
        #
        # vmexecutor
        # 
        elif hsh[ 'device'].find( 'vmexecutor') >= 0:
            hsh['controller'] = 'vm_' + hsh['name']
            hsh['channel'] = '1'
            hsh['rootdevicename'] = hsh['device']
        #
        # attributes as io registers
        #
        elif hsh[ 'module'] == 'tangoattributeiorctrl':
            global nb_attriorctrl
            nb_attriorctrl = nb_attriorctrl + 1
            hsh['controller'] = hsh['module']
            try: 
                if ( (hsh['device'].find(':') > 0 and len(hsh['device'].split('/')) == 5) or
                     (hsh['device'].find(':') < 0 and len(hsh['device'].split('/')) == 4) ):
                    hsh['rootdevicename'] = hsh['device']
                else:   
                    hsh['rootdevicename'] = hsh['device'] +  "/" +  hsh['name'].split('_')[1]
            except Exception as e: 
                print( "SardanaConvert: error, wrong tangoattributeioctrl syntax for %s" % hsh[ 'name'])
                print( "  %s" % repr( hsh))
                print( "  check /online_dir/online.xml")
                print( "  the attribute has to appear as a postfix in 'name', appended with '_'")
                print( "  or in 'device', appended with '/'")
                sys.exit( 255) 

            hsh['channel'] = "%d" % int(nb_attriorctrl)
        #
        # dcm_energy
        #
        elif ( (hsh[ 'device'].find( 'dcmener') >= 0 or 
        hsh[ 'device'].find( 'fmbenergy') >= 0 or
        hsh[ 'device'].find( 'enerygfmb') >= 0 ) and
        hsh[ 'module'] != 'tangoattributectctrl' and
        hsh[ 'module'] != 'tangoattributeiorctrl'): # to avoid problems if changes in order
            hsh['controller'] = 'dcm_energy'
            hsh['channel'] = '1'
            hsh['rootdevicename'] = hsh['device']
        #
        # multiplemotors
        #
        elif hsh[ 'device'].find( 'multiplemotors') >= 0:
            hsh['controller'] = 'mult_' + hsh['name']
            hsh['channel'] = '1'
            hsh['rootdevicename'] = hsh['device']
        #
        # pseudomotors
        #
        elif hsh[ 'type'] == 'pseudomotor':
            hsh['controller'] = 'pm_' + hsh['name']
            hsh['channel'] = '1'
            hsh['rootdevicename'] = hsh['device']
        #
        # diffractometer
        #
        elif hsh['type'] == 'diffractometercontroller':            
            if hsh['device'].find('p08') >= 0:
                controller = 'kohzu_diff'
            else:
                predefined = 0
                for ( rootdevicename, predef_controller) in predefined_oms58:
                    if hsh[ 'device'].find( rootdevicename) >= 0:
                        controller = predef_controller
                        predefined = 1
                if not predefined:
                    device_split = hsh['device'].rsplit('.',1)[0]
                    device_split = device_split.split('/')                
                    if hsh['device'].find(':') == -1:
                        index = 1
                        pref = ''
                    else:
                        index = 2
                        pref = device_split[0].split(':')[0] + "_"
                        hsh['device'] = hsh['device'].split('/',1)[1]
                    controller = 'omsvme58_' + pref + device_split[index].replace('omsvme58','') + '_' + device_split[index+1].replace('.','')
                    controller.replace("__", "_")
            hsh['controller'] = controller
            hsh['channel'] = '1'
            hsh['rootdevicename'] = hsh['device'].split('.')[0]
        #
        # measurement group
        #
        elif hsh['type'] == 'measurement_group':
            hsh['controller'] = "None"
            hsh['channel'] = "None"
            hsh['rootdevicename'] = "None"
        #
        # tangomotor
        #
        elif hsh[ 'device'].find( 'tangomotor') >= 0:
            rootdevicename = hsh[ 'device'].split( '.')[0]
            controller = 'tm_' + rootdevicename.split('/')[2]
            hsh['controller'] = controller
            channel = find_channel_number( hsh['hostname'], rootdevicename, hsh['device'])
            hsh['channel'] = "%d" % int( channel)
            hsh['rootdevicename'] = rootdevicename
        #
        # piezopi & mico axis
        #
        elif hsh[ 'device'].find( 'piezopi') >= 0 or hsh[ 'device'].find( 'axis/mi') >=0:
            rootdevicename = hsh[ 'device'].rsplit( '.',1)[0]
            controller = 'tm_' + rootdevicename.split('/')[1] + '_' + rootdevicename.split('/')[2]
            hsh['controller'] = controller
            channel = find_channel_number( hsh['hostname'], rootdevicename, hsh['device'])
            hsh['channel'] = "%d" % int( channel)
            hsh['rootdevicename'] = rootdevicename
        #
        # petra3undulator
        #
        elif (hsh[ 'module'] == 'motor_tango' and hsh[ 'device'].find( 'petra3undulator') >= 0):
            hsh['controller'] = 'tm_undulator'
            hsh['channel'] = '1'
            hsh['rootdevicename'] = hsh['device']
        #
        # oxfordcryostrem700
        # 
        elif hsh[ 'module'] == 'oxfcryo700':
            hsh['controller'] = 'oxfcryo700ctrl_' + hsh['name']
            hsh['channel'] = '1'
            hsh['rootdevicename'] = hsh['device']
        #
        # pilctriggergenerator as timer
        #
        elif hsh[ 'module'] == 'pilctimer':
            rootdevicename = hsh['device']
            device_split = hsh['device'].split('/')
            if hsh['device'].find(':') == -1:
                index = 1
                pref = ''
            else:
                index = 2
                pref = device_split[0].split(':')[0] + "_"
                hsh['device'] = hsh['device'].split('/',1)[1]
            controller = 'pilctimer_' + pref + device_split[index].replace('pilctriggergenerator','') + '_' + device_split[index+1].replace('.','')
            controller = controller.replace("__", "_")
            hsh['controller'] = controller
            if rootdevicename.find(':') >=0:
                rootdevicename = rootdevicename.split('/',1)[1]
            hsh['rootdevicename'] = rootdevicename
            channel = 1
            hsh['channel'] = "%d" % int( channel)
        #
        # pilcgatetriggeredvfc as timer
        #
        elif hsh[ 'module'] == 'pilcgtvfctimer':
            rootdevicename = hsh['device']
            device_split = hsh['device'].split('/')
            if hsh['device'].find(':') == -1:
                index = 1
                pref = ''
            else:
                index = 2
                pref = device_split[0].split(':')[0] + "_"
                hsh['device'] = hsh['device'].split('/',1)[1]
            controller = 'pilcgtvfctimer_' + pref + device_split[index].replace('pilctriggergenerator','') + '_' + device_split[index+1].replace('.','')
            controller = controller.replace("__", "_")
            hsh['controller'] = controller
            if rootdevicename.find(':') >=0:
                rootdevicename = rootdevicename.split('/',1)[1]
            hsh['rootdevicename'] = rootdevicename
            channel = 1
            hsh['channel'] = "%d" % int( channel)
        #
        # dcm_motor have the strange numbering, chose one controller for each device
        #
        elif (hsh[ 'module'] == 'motor_tango' or 
              hsh[ 'module'] == 'absbox' or
              hsh[ 'module'] == 'kohzu' or
              hsh[ 'module'] == 'phymotion' or
              hsh[ 'module'] == 'smchydra' or
              hsh[ 'module'] == 'lom'):
            predefined = 0
            for ( rootdevicename, controller) in \
                    [ 
                     ( 'p01/dcmmotor/oh.01', 'dcm_motor_oh_01'), 
                     ( 'p01/dcmmotor/oh.03', 'dcm_motor_oh_03'), 
                     ( 'p01/dcmmotor/oh.04', 'dcm_motor_oh_04'),
                     ( 'p01/dcmener/oh.01', 'dcm_ener_oh'), 
                     ( 'p02/dcmmotor/oh.01', 'dcm_motor_oh_01'), 
                     ( 'p02/dcmmotor/oh.03', 'dcm_motor_oh_03'), 
                     ( 'p02/dcmmotor/oh.04', 'dcm_motor_oh_04'),
                     ( 'p03/lomenergy/exp.01', 'elom_exp'), 
                     ( 'p04/undulator/1', 'tm_undulator'), 
                     ( 'p04/undulatorp04/exp2.01', 'tm_undp04'), 
                     ( 'p04/monop04/exp2.01', 'tm_monop04'), 
                     ( 'p06/undulator/1', 'tm_undulator'), 
                     ( 'p06/dcmmotor/mono.01', 'dcm_motor_mono_01'), 
                     ( 'p07/aerotech/mapper_a', 'tm_aero_a'), 
                     ( 'p07/aerotech/mapper_y', 'tm_aero_y'), 
                     ( 'p07/aerotech/mapper_xs', 'tm_aero_xs'), 
                     ( 'p07/aerotech/mapper_ys', 'tm_aero_ys'), 
                     ( 'p07/aerotech/mapper_xxs', 'tm_aero_xxs'), 
                     ( 'p07/aerotech/mapper_yys', 'tm_aero_yys'), 
                     ( 'p07/beckhoffmotor/m2', 'tm_beckhoffm2'), 
                     ( 'p07/beckhoffmotor/eh4.01', 'tm_beckhoffeh4_01'), 
                     ( 'p07/beckhoffmotor/eh4.02', 'tm_beckhoffeh4_02'), 
                     ( 'p07/beckhoffmotor/eh4.03', 'tm_beckhoffeh4_03'), 
                     ( 'p07/beckhoffmotor/eh4.04', 'tm_beckhoffeh4_04'), 
                     ( 'p07/beckhoffmotor/eh4.05', 'tm_beckhoffeh4_05'), 
                     ( 'p07/beckhoffmotor/eh4.11', 'tm_beckhoffeh4_11'), 
                     ( 'p07/beckhoffmotor/eh4.12', 'tm_beckhoffeh4_12'), 
                     ( 'p07/beckhoffmotor/eh4.13', 'tm_beckhoffeh4_13'), 
                     ( 'p07/beckhoffmotor/eh4.14', 'tm_beckhoffeh4_14'), 
                     ( 'p07/beckhoffmotor/eh4.15', 'tm_beckhoffeh4_15'), 
                     ( 'p07/beckhoffmotor/eh4.16', 'tm_beckhoffeh4_16'), 
                     ( 'p07/beckhoffmotor/eh4.17', 'tm_beckhoffeh4_17'), 
                     ( 'p07/beckhoffmotor/eh4.18', 'tm_beckhoffeh4_18'), 
                     ( 'p07/beckhoffmotor/eh4.19', 'tm_beckhoffeh4_19'), 
                     ( 'p07/beckhoffmotor/eh4.20', 'tm_beckhoffeh4_20'), 
                     ( 'p07/beckhoffmotor/eh4.21', 'tm_beckhoffeh4_21'), 
                     ( 'p07/beckhoffmotor/eh4.22', 'tm_beckhoffeh4_22'), 
                     ( 'p07/beckhoffmotor/eh4.23', 'tm_beckhoffeh4_23'), 
                     ( 'p07/beckhoffmotor/eh4.24', 'tm_beckhoffeh4_24'), 
                     ( 'p07/beckhoffmotor/eh4.25', 'tm_beckhoffeh4_25'), 
                     ( 'p07/beckhoffmotor/eh4.26', 'tm_beckhoffeh4_26'), 
                     ( 'p07/beckhoffmotor/eh4.27', 'tm_beckhoffeh4_27'), 
                     ( 'p07/beckhoffmotor/eh4.28', 'tm_beckhoffeh4_28'), 
                     ( 'p07/beckhoffmotor/eh4.29', 'tm_beckhoffeh4_29'), 
                     ( 'p07/beckhoffmotor/eh4.30', 'tm_beckhoffeh4_30'), 
                     ( 'p07/beckhoffmotor/eh4.31', 'tm_beckhoffeh4_31'), 
                     ( 'p07/beckhoffmotor/eh4.32', 'tm_beckhoffeh4_32'), 
                     ( 'p07/beckhoffmotor/eh4.33', 'tm_beckhoffeh4_33'), 
                     ( 'p07/beckhoffmotor/eh4.34', 'tm_beckhoffeh4_34'), 
                     ( 'p07/beckhoffmotor/eh4.35', 'tm_beckhoffeh4_35'), 
                     ( 'p07/beckhoffmotor/eh4.36', 'tm_beckhoffeh4_36'), 
                     ( 'p07/beckhoffmotor/eh4.37', 'tm_beckhoffeh4_37'), 
                     ( 'p07/beckhoffmotor/eh4.38', 'tm_beckhoffeh4_38'), 
                     ( 'p07/beckhoffmotor/eh4.39', 'tm_beckhoffeh4_39'), 
                     ( 'p07/beckhoffmotor/eh4.40', 'tm_beckhoffeh4_40'), 
                     ( 'p07/beckhoffmotor/eh4.41', 'tm_beckhoffeh4_41'), 
                     ( 'p07/hexapodbig/x', 'tm_hexabigx'), 
                     ( 'p07/hexapodbig/y', 'tm_hexabigy'), 
                     ( 'p07/hexapodbig/z', 'tm_hexabigy'), 
                     ( 'p07/hexapodbig/u', 'tm_hexabigu'), 
                     ( 'p07/hexapodbig/v', 'tm_hexabigv'), 
                     ( 'p07/hexapodbig/w', 'tm_hexabigw'),  
                     ( 'p07/hexapodsmall/x', 'tm_hexasmallx'), 
                     ( 'p07/hexapodsmall/y', 'tm_hexasmally'), 
                     ( 'p07/hexapodsmall/z', 'tm_hexasmallz'), 
                     ( 'p07/hexapodsmall/u', 'tm_hexasmallu'), 
                     ( 'p07/hexapodsmall/v', 'tm_hexasmallv'), 
                     ( 'p07/hexapodsmall/w', 'tm_hexasmallw'),  
                     ( 'p07/motor/hex_omega_big', 'tm_hexabigom'), 
                     ( 'p07/portal1_motor/x', 'tm_portallx'), 
                     ( 'p07/portal1_motor/y', 'tm_portally'), 
                     ( 'p07/portal1_motor/z', 'tm_portallz'), 
                     ( 'p07/portal1_motor/g', 'tm_portallg'), 
                     ( 'p07/portal1_motor/w', 'tm_portallw'), 
                     ( 'p07/dcmmotor/14', 'dcm_motor_14'), 
                     ( 'p07/dcmmotor/15', 'dcm_motor_15'), 
                     ( 'p07/dcmmotor/16', 'dcm_motor_16'), 
                     ( 'p07/dcmmotor/17', 'dcm_motor_17'), 
                     ( 'p07/dcmmotor/21', 'dcm_motor_21'), 
                     ( 'p07/dcmmotor/22', 'dcm_motor_22'), 
                     ( 'p07/dcmmotor/23', 'dcm_motor_23'), 
                     ( 'p07/dcmmotor/24', 'dcm_motor_24'), 
                     ( 'p07/dcmmotor/25', 'dcm_motor_25'), 
                     ( 'p07/dcmmotor/26', 'dcm_motor_26'), 
                     ( 'p07/dcmmotor/27', 'dcm_motor_27'), 
                     ( 'p07/dcmmotor/28', 'dcm_motor_28'), 
                     ( 'p07/sbmmotor/01', 'tm_sbm01'), 
                     ( 'p07/sbmmotor/02', 'tm_sbm02'), 
                     ( 'p07/sbmmotor/03', 'tm_sbm03'), 
                     ( 'p07/sbmmotor/04', 'tm_sbm04'), 
                     ( 'p07/sbmenergy/01', 'tm_sbmener01'), 
                     ( 'p07/undulator/01', 'tm_undulator'), 
                     ( 'p08/absorber/01', 'tm_absbox_01'),  
                     ( 'p08/lensctrl/eh.01', 'tm_absbox_eh01'),  
                     ( 'p08/lensctrl/oh.01', 'tm_absbox_oh01'), 
                     ( 'p08/blenergy/mono.01', 'tm_blenergy'), 
                     ( 'p08/lomenergy/exp.01', 'elom_exp'), 
                     ( 'p08/dcmmotor/mono.01', 'dcm_motor_mono_01'), 
                     ( 'p08/dcmmotor/mono.03', 'dcm_motor_mono_03'), 
                     ( 'p08/dcmmotor/mono.04', 'dcm_motor_mono_04'),
                     ( 'p08/piezonv40axis/exp.01', 'piezonv40_01'),
                     ( 'p08/piezonv40axis/exp.02', 'piezonv40_02'),
                     ( 'p08/piezonv40axis/exp.03', 'piezonv40_03'),
                     ( 'p09/absorber/01', 'tm_absbox'), 
                     ( 'p09/absorbercontroller/mag.01', 'tm_absbox_mag'), 
                     ( 'p09/analyzer/eh1.01', 'analyzer_eh1'),
                     ( 'p09/dcmmotor/mono.01', 'dcm_motor_mono_01'),
                     ( 'p09/undulator/1', 'tm_undulator'), 
                     ( 'p10/undulator/1', 'tm_undulator'), 
                     ( 'p10/dcmmotor/opt.01', 'dcm_motor_opt_01'), 
                     ( 'p10/dcmmotor/opt.03', 'dcm_motor_opt_03'), 
                     ( 'p10/dcmmotor/opt.04', 'dcm_motor_opt_04'),
                     ( 'p10/lensesbox/e1.01', 'tm_lenses'),
                     ( 'delay/hexasmarlimotor/exp.01', 'hexa_1'),   
                     ( 'delay/hexasmarlimotor/exp.02', 'hexa_2'),   
                     ( 'delay/hexasmarlimotor/exp.03', 'hexa_3'),   
                     ( 'delay/hexasmarlimotor/exp.04', 'hexa_4'),   
                     ( 'delay/hexasmarlimotor/exp.05', 'hexa_5'),   
                     ( 'delay/hexasmarlimotor/exp.06', 'hexa_6'),   
                     ( 'delay/hexasmarlimotor/exp.07', 'hexa_7'),   
                     ( 'delay/hexasmarlimotor/exp.08', 'hexa_8'),   
                     ( 'delay/hexasmarlimotor/exp.09', 'hexa_9'),   
                     ( 'p02/newfocuspicoaxis/eh2.01', 'nfpaxiseh2_01'),   
                     ( 'p02/newfocuspicoaxis/eh2.02', 'nfpaxiseh2_02'),    
                     ( 'p02/newfocuspicoaxis/eh2.03', 'nfpaxiseh2_03'),    
                     ( 'p02/newfocuspicoaxis/eh2.04', 'nfpaxiseh2_04'),    
                     ( 'p02/newfocuspicoaxis/eh2.05', 'nfpaxiseh2_05'),   
                     ( 'p02/newfocuspicoaxis/eh2.06', 'nfpaxiseh2_06'),
                     ( 'p09/newfocuspico8742/eh.01', 'pico8742_01'),
                     ( 'p09/newfocuspico8742/eh.02', 'pico8742_02'),
                     ( 'p09/newfocuspico8742/eh.03', 'pico8742_03'),
                     ( 'p09/newfocuspico8742/eh.04', 'pico8742_04'),
                     ( 'p64/newfocuspico8742/exp.01', 'pico8742_01'),
                     ( 'p64/newfocuspico8742/exp.02', 'pico8742_02'),
                     ( 'p64/newfocuspico8742/exp.03', 'pico8742_03'),
                     ( 'p64/newfocuspico8742/exp.04', 'pico8742_04'),
                     ( 'p64/dcmtsai/axis1', 'tm_tsai_01'),
                     ( 'p06/hexasmarmotor1/px', 'tm_hexasmarmotor1_px'),
                     ( 'p06/hexasmarmotor1/py', 'tm_hexasmarmotor1_py'),
                     ( 'p06/hexasmarmotor1/pz', 'tm_hexasmarmotor1_pz'),
                     ( 'p06/hexasmarmotor1/rx', 'tm_hexasmarmotor1_rx'),
                     ( 'p06/hexasmarmotor1/ry', 'tm_hexasmarmotor1_ry'),
                     ( 'p06/hexasmarmotor1/rz', 'tm_hexasmarmotor1_rz'),
                     ( 'p06/hexasmarmotor1/x', 'tm_hexasmarmotor1_x'),
                     ( 'p06/hexasmarmotor1/y', 'tm_hexasmarmotor1_y'),
                     ( 'p06/hexasmarmotor1/z', 'tm_hexasmarmotor1_z'),
                     ( 'p06/hexasmarmotor2/px', 'tm_hexasmarmotor2_px'),
                     ( 'p06/hexasmarmotor2/py', 'tm_hexasmarmotor2_py'),
                     ( 'p06/hexasmarmotor2/pz', 'tm_hexasmarmotor2_pz'),
                     ( 'p06/hexasmarmotor2/rx', 'tm_hexasmarmotor2_rx'),
                     ( 'p06/hexasmarmotor2/ry', 'tm_hexasmarmotor2_ry'),
                     ( 'p06/hexasmarmotor2/rz', 'tm_hexasmarmotor2_rz'),
                     ( 'p06/hexasmarmotor2/x', 'tm_hexasmarmotor2_x'),
                     ( 'p06/hexasmarmotor2/y', 'tm_hexasmarmotor2_y'),
                     ( 'p06/hexasmarmotor2/z', 'tm_hexasmarmotor2_z'),
                        
                     ]:
                if hsh[ 'device'] == rootdevicename:
                    hsh['controller'] = controller
                    hsh['rootdevicename'] = rootdevicename
                    channel = 1
                    hsh['channel'] = "%d" % int( channel)
                    predefined = 1
                    break
            for ( rootdevicename, controller) in \
                    [ ( 'p01/analyzerep01/eh2', 'analyzerep01_eh2'), 
                     ( 'p01/bscryotempcontrolp01/eh3', 'bscryotempcontrolp01_eh3'), 
                     ( 'p01/tcpipmotorp10/exp', 'tcpipmotorp10_exp'),
                     ( 'p03/hexapodmotor/hexa3', 'hexa_3'),
                     ( 'p03/hexapodmotor/hexa4', 'hexa_4'),
                     ( 'p03/hexapodmotor/hexa5', 'hexa_5'),
                     ( 'p03/hexapodmotor/hexa2', 'hexa_2'),
                     ( 'p03/hexapodmotor/hexa4', 'hexa_4'),
                     ( 'p03/hexapodmotor/cube2', 'cube_4'),
                     ( 'p03nano/galildmcslit/slit', 'galil_dmc_slit'), 
                     ( 'p03/galildmcslit/slit3', 'galil_dmc_slit3'), 
                     ( 'p03/galildmcslit/slit4', 'galil_dmc_slit4'), 
                     ( 'p03/galildmcslit/slit5', 'galil_dmc_slit5'), 
                     ( 'p03/smarpodmotor/p03nano', 'smarpod_p03nano'),
                     ( 'p03/lom/exp', 'lom_exp'),
                     ( 'p06/galildmcslit/slit', 'galil_dmc_slit'), 
                     ( 'p06/hydramotor/exp', 'smchydra'), 
                     ( 'p07/galildmcslit/slit', 'galil_dmc_slit'), 
                     ( 'p07/twothetap07/eh2a.01', 'tth_eh2a'), 
                     ( 'p08/motor/diff', 'kohzu_diff'),
                     ( 'p08/phymotion/dev', 'phymotion_dev'),
                     ( 'p08/lom/exp', 'lom_exp'),
                     ( 'tdot/robotxmotor/exp', 'tm_robotx'),        # fischertechnik
                     ( 'p09/phaseretarder/exp', 'phaseretarder_exp'),
                     ( 'p09/hexapodmotor/mag', 'hexa_mag'),
                     ( 'p09/attocubeanc300motor/exp', 'atto300_exp'), 
                     ( 'p09/galildmcslit/exp', 'galil_dmc_slit'),
                     ( 'p09/diffracmu/mag', 'diffracmu_mag'),
                     ( 'p10/galildmcslit/e1', 'galil_dmc_e1'), 
                     ( 'p10/galildmcslit/e2', 'galil_dmc_e2'),
                     ( 'p10lab/attocubemotor/exp', 'atto300_exp'), 
                     ( 'p10/hexapodmotor/hexa1', 'hexa_1'),
                     ( 'p10/eh2tth/e2', 'tm_eh2tth'),
                     ( 'p10/smaractmcsmotor/exp', 'smaractmcs_exp'),
                     ( 'p06/smaractmotor/exp', 'smaract_exp'),  
                     ( 'p11/piezomotor/eh.4', 'galil_dmc_eh4'),  
                     ( 'metro/aerotechmotor/lab', 'tm_aerotechmotor_metro'),  
                     ( 'p06/aerotechmotor/lab', 'tm_aerotechmotor_p06'),
                     ( 'p06/pegasusmotor/nc1', 'tm_pegasusmotor_nc1'),
                     ( 'p06/newportaxis/exp', 'tm_newportaxis_exp'),
                     ]:
                if hsh[ 'device'].find( rootdevicename) >= 0:
                    hsh['controller'] = controller
                    channel = find_channel_number( hsh['hostname'], rootdevicename, hsh['device'])
                    hsh['channel'] = "%d" % int( channel)
                    hsh['rootdevicename'] = rootdevicename
                    predefined = 1
                    break
            if not predefined:
                device_split = hsh['device'].rsplit('.',1)[0]
                rootdevicename = device_split
                device_split = device_split.split('/')                
                if hsh['device'].find(':') == -1:
                    index = 1
                    pref = ''
                else:
                    index = 2
                    pref = device_split[0].split(':')[0] + "_"
                    hsh['device'] = hsh['device'].split('/',1)[1]
                controller = 'tm_' + pref + device_split[index] + '_' + device_split[index+1].replace('.','')
                hsh['controller'] = controller
                if rootdevicename.find(':') >=0:
                    rootdevicename = rootdevicename.split('/',1)[1]
                hsh['rootdevicename'] = rootdevicename
                channel = find_channel_number( hsh['hostname'], rootdevicename, hsh['device'])
                hsh['channel'] = "%d" % int( channel)
        #
        # dgg2,
        # every device needs a controller, MntGrp issue
        #
        elif hsh[ 'module'] == 'dgg2':
            predefined = 0
            for ( rootdevicename, controller) in \
                    [ ('fmc/timer/mob.01', 'dgg2_mob_01'),
                      ('fmc/timer/mob.02', 'dgg2_mob_02'),
                      ('p01/timer/eh1.01', 'dgg2_eh1_01'),
                      ('p01/timer/eh1.02', 'dgg2_eh1_02'),
                      ('p01/timer/eh2.01', 'dgg2_eh2_01'),
                      ('p01/timer/eh2.02', 'dgg2_eh2_02'),
                      ('p01/timer/eh3.01', 'dgg2_eh3_01'),
                      ('p01/timer/eh3.02', 'dgg2_eh3_02'),
                      ('p01/timer/eh3.01', 'dgg2_eh3_01'),
                      ('p01/timer/eh3.02', 'dgg2_eh3_02'),
                      ('p02/timer/oh1.01', 'dgg2_oh1_01'),
                      ('p02/timer/oh1.02', 'dgg2_oh1_02'),
                      ('p02/timer/eh1a.01', 'dgg2_eh1a_01'),
                      ('p02/timer/eh1a.02', 'dgg2_eh1a_02'),
                      ('p02/timer/eh2a.01', 'dgg2_eh2a_01'),
                      ('p02/timer/eh2a.02', 'dgg2_eh2a_02'),
                      ('p02/timer/eh1b.01', 'dgg2_eh1b_01'),
                      ('p02/timer/eh1b.02', 'dgg2_eh1b_02'),
                      ('p02/timer/eh2b.01', 'dgg2_eh2b_01'),
                      ('p02/timer/eh2b.02', 'dgg2_eh2b_02'),
                      ('p03/timer/exp.01', 'dgg2_exp_01'),
                      ('p03/timer/exp.02', 'dgg2_exp_02'),
                      ('p03p03nano/timer/p03nano.01', 'dgg2_p03nano_01'),
                      ('p03nano/timer/p03nano.02', 'dgg2_p03nano_02'),
                      ('p04/timer/exp1.01', 'dgg2_exp1_01'),
                      ('p04/timer/exp1.02', 'dgg2_exp1_02'),
                      ('p04/timer/exp2.01', 'dgg2_exp2_01'),
                      ('p04/timer/exp2.02', 'dgg2_exp2_02'),
                      ('p06/timer/exp.01', 'dgg2_exp_01'),
                      ('p06/timer/exp.02', 'dgg2_exp_02'),
                      ('p06/timer/mono.01', 'dgg2_mono_01'),
                      ('p06/timer/mono.02', 'dgg2_mono_02'),
                      ('p07/timer/eh1.01', 'dgg2_eh1_01'),
                      ('p07/timer/eh1.02', 'dgg2_eh1_02'),
                      ('p07/timer/eh2.01', 'dgg2_eh2_01'),
                      ('p07/timer/eh2.02', 'dgg2_eh2_02'),
                      ('p07/timer/eh3.01', 'dgg2_eh3_01'),
                      ('p07/timer/eh3.02', 'dgg2_eh3_02'),
                      ('p07/timer/exp.01', 'dgg2_exp_01'),
                      ('p07/timer/exp.02', 'dgg2_exp_02'),
                      ('p08/timer/exp.01', 'dgg2_exp_01'),
                      ('p08/timer/exp.02', 'dgg2_exp_02'),
                      ('p09/dgg2/exp.01', 'dgg2_exp_01'),
                      ('p09/dgg2/exp.02', 'dgg2_exp_02'),
                      ('p09/dgg2/d1.01', 'dgg2_d1_01'),
                      ('p09/dgg2/d1.02', 'dgg2_d1_02'),
                      ('p09/dgg2/eh.01', 'dgg2_eh_01'),
                      ('p09/dgg2/eh.02', 'dgg2_eh_02'),
                      ('p09/mdgg8/d1.01', 'dgg2_d1_03'),
                      ('p09/mdgg8/d1.02', 'dgg2_d1_04'),
                      ('p09/mdgg8/eh.01', 'dgg2_eh_03'),
                      ('p09/mdgg8/eh.02', 'dgg2_eh_04'),
                      ('p09/timer/exp.01', 'dgg2_exp_01'),
                      ('p09/timer/exp.02', 'dgg2_exp_02'),
                      ('p09/timer/mono.01', 'dgg2_mono_01'),
                      ('p09/timer/mono.02', 'dgg2_mono_02'),
                      ('p09/timer/mag.01', 'dgg2_mag_01'),
                      ('p09/timer/mag.02', 'dgg2_mag_02'),
                      ('p09/timer/haxps.01', 'dgg2_haxps_01'),
                      ('p09/timer/haxps.02', 'dgg2_haxps_02'),
                      ('p10/timer/e1.01', 'dgg2_e1_01'),
                      ('p10/timer/e1.02', 'dgg2_e1_02'),
                      ('p10/timer/e2.01', 'dgg2_e2_01'),
                      ('p10/timer/e2.02', 'dgg2_e2_02'),
                      ('p10/timer/lab.01', 'dgg2_lab_01'),
                      ('p10/timer/lab.02', 'dgg2_lab_02'),
                      ('p11/dgg2/ehb.01', 'dgg2_ehb_01'),
                      ('p11/dgg2/ehb.02', 'dgg2_ehb_02'),
                      ('p11/dgg2/ehc.01', 'dgg2_ehc_01'),
                      ('p11/dgg2/ehc.02', 'dgg2_ehc_02'),
                      ('p11/dgg2/pp.01', 'dgg2_pp_01'),
                      ('p11/dgg2/pp.02', 'dgg2_pp_02'),
                      ('p11/timer/eh.1.01', 'dgg2_eh1_01'),
                      ('p11/timer/eh.1.02', 'dgg2_eh1_02'),
                      ('p11/timer/ehc.01', 'dgg2_timerehc_01'),
                      ('p11/timer/ehc.02', 'dgg2_timerehc_02'),
                      ('p24/timer/exp.01', 'dgg2_exp_01'),
                      ('p24/timer/exp.02', 'dgg2_exp_02'),
                      ('p64/timer/exp.01', 'dgg2_exp_01'),
                      ('p64/timer/exp.02', 'dgg2_exp_02'),
                      ('p65/timer/a2.01', 'dgg2_a2_01'),
                      ('p65/timer/a2.02', 'dgg2_a2_02'),
                      ('p66/timer/exp.01', 'dgg2_exp_01'),
                      ('p66/timer/exp.02', 'dgg2_exp_02'),
                      ('delay/timer/exp.01', 'dgg2_exp_01'),
                      ('delay/timer/exp.02', 'dgg2_exp_02'),
                      ('delay/timer/exp.03', 'dgg2_exp_03'),
                      ('delay/timer/exp.04', 'dgg2_exp_04'),
                      ]:
                if hsh[ 'device'].find( rootdevicename) >= 0:
                    hsh['controller'] = controller
                    hsh['rootdevicename'] = rootdevicename
                    channel = 1
                    hsh['channel'] = "%d" % int( channel)
                    predefined = 1
                    break
            if not predefined:
                rootdevicename = hsh['device']
                device_split = hsh['device'].split('/')
                if hsh['device'].find(':') == -1:
                    index = 1
                    pref = ''
                else:
                    index = 2
                    pref = device_split[0].split(':')[0] + "_"
                    hsh['device'] = hsh['device'].split('/',1)[1]
                controller = 'dgg2_' + pref + device_split[index].replace('dgg2','') + '_' + device_split[index+1].replace('.','')
                controller.replace("__", "_")
                hsh['controller'] = controller
                if rootdevicename.find(':') >=0:
                    rootdevicename = rootdevicename.split('/',1)[1]
                hsh['rootdevicename'] = rootdevicename
                channel = 1
                hsh['channel'] = "%d" % int( channel)
                
        #
        # mythenroi, mca8715, sis3302 
        #
        elif (hsh[ 'module'] == 'mythenroi' or 
              hsh[ 'module'] == 'mca8715roi' or 
              hsh[ 'module'] == 'sis3302roi' or 
              hsh[ 'module'] == 'kromoroi'):
            if len(hsh['device'].split("/")) < 4:
                print( "Device for mythenroi and mca8715 must contain an attribute name, sis3302 must contain an roi index. Not converted")
            else:
                splitnames = hsh['device'].rsplit("/",1)
                splitdev = splitnames[0].rsplit("/",1)
                splitdev2 = splitdev[0].rsplit("/",1)
                device = splitnames[0]
                if device not in channel_mythenmcasisroi:
                    channel_mythenmcasisroi[device] = 0
                hsh['rootdevicename'] = splitnames[0]
                hsh['controller'] = hsh[ 'module'] + str(splitdev2[1]) + str(splitdev[1]) + 'ctrl'
                hsh['controller'] = hsh['controller'].replace("kromoroikromo", "kromoroi")
                hsh['channel'] = "%d" % (channel_mythenmcasisroi[device] + 1)
                channel_mythenmcasisroi[device] = channel_mythenmcasisroi[device] + 1 
        #
        # amptekroi
        #
        elif (hsh[ 'module'] == 'amptekroi'):
            channel = int(hsh['device'].rsplit("/",1)[1])
            hsh['device'] = hsh['device'].rsplit("/",1)[0]
            hsh['rootdevicename'] = hsh['device']
            alphabetic_device_name = ''.join(c for c in hsh['device'] if c.isalnum())
            hsh['controller'] = 'amptekroi' + alphabetic_device_name + 'ctrl'
            hsh['channel'] = "%d" % (channel)
        #
        # sis3302 (spectrum and rois)
        #
        elif (hsh[ 'module'] == 'sis3302'):
            splitnames = hsh['device'].replace(".","").split("/")
            if len(splitnames) == 4:
                channel =  int(hsh['device'].rsplit("/",1)[1]) + 1
                hsh['rootdevicename'] = hsh['device'].rsplit("/",1)[0]
            else:
                channel = 1
                hsh['rootdevicename'] = hsh['device']
            hsh['controller'] = 'sis3302roi1d' + splitnames[2] + 'ctrl'
            hsh['channel'] = "%d" % (channel)
        #
        # sis3302 in multiscans mode (spectrum and rois)
        #
        elif (hsh[ 'module'] == 'sis3302multiscan'):
            splitnames = hsh['device'].replace(".","").split("/")
            if len(splitnames) == 4:
                channel =  int(hsh['device'].rsplit("/",1)[1]) + 1
                hsh['rootdevicename'] = hsh['device'].rsplit("/",1)[0]
            else:
                channel = 1
                hsh['rootdevicename'] = hsh['device']
            hsh['controller'] = 'sis3302ms1d' + splitnames[2] + 'ctrl'
            hsh['channel'] = "%d" % (channel)          
        #
        # limaroicounter
        #
        elif (hsh[ 'module'] == 'limaroicounter'):
            splitnames = hsh['device'].replace(".","").split("/")
            device = hsh['device']
            if device not in channel_limaroicounter:
                channel_limaroicounter[device] = 0
            hsh['rootdevicename'] = device
            hsh['controller'] = 'lima' + str(splitnames[1]) + str(splitnames[2]) + 'ctrl'
            hsh['channel'] = "%d" % (channel_limaroicounter[device] + 1)
            channel_limaroicounter[device] = channel_limaroicounter[device] + 1              
        #
        # onedroi
        #
        elif (hsh[ 'module'] == 'onedroi'):
            splitnames = hsh['device'].replace(".","").split("/")
            device = hsh['device']
            if device not in channel_onedroi:
                channel_onedroi[device] = 0
            hsh['rootdevicename'] = device
            hsh['controller'] = 'onedroi' + str(splitnames[1]) + str(splitnames[2]) + 'ctrl'
            hsh['channel'] = "%d" % (channel_onedroi[device] + 1)
            channel_onedroi[device] = channel_onedroi[device] + 1
        #
        # pscameravhrroi
        #
        elif (hsh[ 'module'] == 'pscameravhrroi'):
            hsh['rootdevicename'] = hsh['device']
            hsh['controller'] = 'pscameravhrroi' + hsh['name'] + 'ctrl'
            hsh['channel'] = '1' 
        #
        # xspress3roi
        #
        elif (hsh[ 'module'] == 'xspress3roi'):
            splitnames = hsh['device'].replace(".","").split("/")
            device = hsh['device']
            if device not in channel_xspress3roi:
                channel_xspress3roi[device] = 0
            hsh['rootdevicename'] = hsh['device']
            hsh['controller'] = 'xspress3roi' + str(splitnames[1]) + str(splitnames[2]) + 'ctrl'
            hsh['channel'] = "%d" % (channel_xspress3roi[device] + 1)
            channel_xspress3roi[device] = channel_xspress3roi[device] + 1
        #
        # mhzdaqp01
        #
        elif (hsh[ 'module'] == 'mhzdaqp01'):
            splitnames = hsh['device'].rsplit("/",1)
            splitdev = splitnames[0].rsplit("/",1)
            device = splitnames[0]
            hsh['rootdevicename'] = splitnames[0]
            hsh['controller'] = 'mhzdaqp01' + str(splitdev[1].replace(".", "")) + 'ctrl'
            if splitnames[1].lower().find("mean") >=0:
                hsh['channel'] = "1" # Channel indicate different attribute from same device
            else:
                hsh['channel'] = "2"
        #
        # xmcd
        #
        elif (hsh[ 'module'] == 'xmcd'):
            splitnames = hsh['device'].rsplit("/",1)
            splitdev = splitnames[0].rsplit("/",1)
            device = splitnames[0]
            if device not in channel_xmcd:
                channel_xmcd[device] = 0
            hsh['rootdevicename'] = splitnames[0]
            hsh['controller'] = 'xmcd' + str(splitdev[1]) + 'ctrl'
            hsh['channel'] = "%d" % (channel_xmcd[device] + 1)
            channel_xmcd[device] = channel_xmcd[device] + 1        
        #
        # kromo detector
        #
        elif (hsh[ 'module'] == 'kromo'):
            splitnames = hsh['device'].replace(".","").split("/")
            device = hsh['device']
            hsh['rootdevicename'] = device
            hsh['controller'] = 'kromo_' + str(splitnames[1]) + str(splitnames[2]) + 'ctrl'
            hsh['controller'] = hsh['controller'].replace("kromo_kromo", "kromo_")
            hsh['channel'] = str(1)       
        #
        # avantes spectrometer
        #
        elif (hsh[ 'module'] == 'avantes'):
            splitnames = hsh['device'].replace(".","").split("/")
            device = hsh['device']
            hsh['rootdevicename'] = device
            hsh['controller'] = 'avantes_' + str(splitnames[1]) + str(splitnames[2]) + 'ctrl'
            hsh['controller'] = hsh['controller'].replace("avantes_avantes", "avantes_")
            hsh['channel'] = str(1)            
        #
        # cobold spectrometer
        #
        elif (hsh[ 'module'] == 'cobold'):
            splitnames = hsh['device'].replace(".","").split("/")
            device = hsh['device']
            hsh['rootdevicename'] = device
            hsh['controller'] = 'cobold_' + str(splitnames[1]) + str(splitnames[2]) + 'ctrl'
            hsh['controller'] = hsh['controller'].replace("cobold_cobold", "cobold_")
            hsh['channel'] = str(1)      
        #
        # spadqdigitizer
        #
        elif (hsh[ 'module'] == 'spadq'):
            splitnames = hsh['device'].rsplit("/",1)
            splitdev = splitnames[0].rsplit("/",1)
            splitdev2 = splitdev[0].rsplit("/",1)
            device = splitnames[0]
            hsh['rootdevicename'] = device
            hsh['controller'] = 'spadq_' + str(splitdev[1].replace('.','')) + str(splitnames[1].replace("DataStreamCh", "").replace("datastreamch", "")) + 'ctrl'
            hsh['controller'] = hsh['controller'].replace("spadq_spadq", "spadq_")
            hsh['channel'] = str(1)
                
        #
        # mca8701, XIA
        #
        elif (hsh[ 'module'] == 'mca_8701' \
              or hsh[ 'module'] == 'mca_xia' \
              or hsh[ 'module'] == 'hydraharp400' \
              or hsh[ 'module'] == 'mca_8715'):
            predefined = 0
            for ( rootdevicename, controller) in \
                    [ ( 'delay/mca/exp', 'mca8701_exp'),
                      ( 'p01/mca/eh1', 'mca8701_eh1'),
                      ( 'p01/mca/eh2', 'mca8701_eh2'),
                      ( 'p01/mca/eh3', 'mca8701_eh3'),
                      ( 'p02/mca/eh2a', 'mca8701_eh2a'),
                      ( 'p02/mca/exp', 'mca8701_exp'),
                      ( 'p03/mca/exp', 'mca8701_exp'), 
                      ( 'p03nano/mca/p03nano', 'mca8701_p03nano'), 
                      ( 'p06/xia/p06', 'xia_p06'), 
                      ( 'p06/xia/exp', 'xia_exp'), 
                      ( 'p06/mca/exp', 'mca8701_exp'), 
                      ( 'p06/hydraharp400/exp', 'hydraharp400_exp'),
                      ( 'p07/mca/eh2a', 'mca8701_eh2a'), 
                      ( 'p07/vonedexecutor/eh', 'mca8701_eh'), 
                      ( 'p09/mca/exp', 'mca8701_exp'), 
                      ( 'p09/mca/d1', 'mca8701_d1'),  # haso113k, Luna 
                      ( 'p09/mca/eh', 'mca8701_eh'),  # haso113k, Luna 
                      ( 'p09/mca/eh', 'mca8701_eh'), 
                      ( 'p99/mca/eh', 'mca8701_eh'), 
                      ( 'p09/vonedexecutor/eh', 'vonedexecutor_eh'), 
                      ( 'p10/mca/e1', 'mca8701_e1'), 
                      ( 'p11/xia/oh', 'mca8701_oh'),
                      ( 'p64/mca/exp', 'mca8715_exp'),
                      ( 'p65/mca/exp', 'mca8701_exp'), 
                      ( 'p24/mca/exp', 'mca8701_exp'), 
                      ( 'slm/hydraharp400/lab', 'hydraharp400_lab'),
                      ( 'slm/mca/eh', 'mca8701_eh'),
                      ]:
                if hsh[ 'device'].find( rootdevicename) >= 0:
                    hsh['controller'] = controller
                    channel = find_channel_number( hsh['hostname'], rootdevicename, hsh['device'])
                    hsh['channel'] = "%d" % int( channel)
                    hsh['rootdevicename'] = rootdevicename
                    predefined = 1
                    break
            if not predefined:
                device_split = hsh['device'].rsplit('.',1)[0]
                rootdevicename = device_split
                device_split = device_split.split('/')                
                if hsh['device'].find(':') == -1:
                    index = 1
                    pref = ''
                else:
                    index = 2
                    pref = device_split[0].split(':')[0] + "_"
                    hsh['device'] = hsh['device'].split('/',1)[1]
                controller = 'xia_' + pref + device_split[index].replace('xia','') + '_' + device_split[index+1].replace('.','')
                controller.replace("__", "_")
                hsh['controller'] = controller
                if rootdevicename.find(':') >=0:
                    rootdevicename = rootdevicename.split('/',1)[1]
                hsh['rootdevicename'] = rootdevicename
                channel = find_channel_number( hsh['hostname'], rootdevicename, hsh['device'])
                hsh['channel'] = "%d" % int( channel) 
            
        #
        # pilatus
        #
        elif (hsh[ 'module'].lower() == 'pilatus100k' or 
              hsh[ 'module'].lower() == 'pilatus300k' or 
              hsh[ 'module'].lower() == 'pilatus1m' or 
              hsh[ 'module'].lower() == 'pilatus2m' or 
              hsh[ 'module'].lower() == 'pilatus6m'):
            hsh['controller'] = hsh['module'].lower() + hsh['name'].lower() + "ctrl"
            channel = 1
            hsh['channel'] = "%d" % int( channel)
            hsh['rootdevicename'] = hsh['device']
        #
        # pco, marccd, perkinelmer, lima, lcxcamera, lambda, amptek, pscameravhr, tangovimba, varex2315, minipix
        #
        elif (hsh[ 'module'].lower().find('pco') >=0 or 
              hsh[ 'module'].lower().find('marccd') >=0 or
              hsh[ 'module'].lower().find('maranax') >=0 or
              hsh[ 'module'].lower().find('andorikon') >=0 or
              hsh[ 'module'].lower().find('perkinelmer') >=0 or
              hsh[ 'module'].lower().find('limaccd') >=0 or
              hsh[ 'module'].lower().find('lcxcamera') >=0 or
              hsh[ 'module'].lower().find('lambda') >=0 or
              hsh[ 'module'].lower().find('eigerdectris') >=0 or
              hsh[ 'module'].lower().find('eigerpsi') >=0 or
              hsh[ 'module'].lower() == 'amptekoned' or
              hsh[ 'module'].lower().find('pscameravhr') >=0 or
              hsh[ 'module'].lower().find('tangovimba') >=0 or
              hsh[ 'module'].lower().find('dalsa') >=0 or
              hsh[ 'module'].lower().find('greateyes') >=0 or
              hsh[ 'module'].lower().find('hzgdcam') >=0 or
              hsh[ 'module'].lower().find('varex2315') >=0 or
              hsh[ 'module'].lower().find('timepix') >=0 or
              hsh[ 'module'].lower().find('minipix') >=0):
            #
            # eiger_filewriter and eiger_monitor should be in online.xml, 
            # but not in onlineSardana.xml
            #
            if 'flag' in hsh and hsh[ 'flag'].lower() == 'nopool':
                continue
            hsh['controller'] = hsh['module'].lower() + hsh['name'].lower() + "ctrl"
            channel = 1
            hsh['channel'] = "%d" % int( channel)
            hsh['rootdevicename'] = hsh['device']
        #
        # oms
        #
        elif hsh[ 'module'] == 'oms58':
            predefined = 0
            for ( rootdevicename, controller) in predefined_oms58:
                if hsh[ 'device'].find( rootdevicename) >= 0:
                    hsh['controller'] = controller
                    channel = find_channel_number( hsh['hostname'], rootdevicename, hsh['device'])
                    hsh['channel'] = "%d" % int( channel)
                    hsh['rootdevicename'] = rootdevicename
                    predefined = 1
                    break
            if not predefined:
                device_split = hsh['device'].rsplit('.',1)[0]
                rootdevicename = device_split
                device_split = device_split.split('/')                
                if hsh['device'].find(':') == -1:
                    index = 1
                    pref = ''
                else:
                    index = 2
                    pref = device_split[0].split(':')[0] + "_"
                    hsh['device'] = hsh['device'].split('/',1)[1]
                controller = 'omsvme58_' + pref + device_split[index].replace('omsvme58','') + '_' + device_split[index+1].replace('.','')
                controller.replace("__", "_")
                hsh['controller'] = controller
                if rootdevicename.find(':') >=0:
                    rootdevicename = rootdevicename.split('/',1)[1]
                hsh['rootdevicename'] = rootdevicename
                channel = find_channel_number( hsh['hostname'], rootdevicename, hsh['device'])
                hsh['channel'] = "%d" % int( channel)            
        #
        # sis3302
        #
        elif hsh[ 'module'] == 'mca_sis3302':
            for ( rootdevicename, controller) in \
                    [( 'p02/sis3302client/exp', 'sis3302_exp'), 
                     ( 'p08/SIS3302Client/exp', 'sis3302_exp'), 
                     ( 'p09/sis3302client/exp', 'sis3302_exp'), 
                     ( 'p09/sis3302client/eh', 'sis3302_eh'), 
                     ]:
                if hsh[ 'device'].find( rootdevicename) >= 0:
                    hsh['controller'] = controller
                    channel = find_channel_number( hsh['hostname'], rootdevicename, hsh['device'])
                    hsh['channel'] = "%d" % (int( channel))
                    hsh['rootdevicename'] = rootdevicename
                    break
        #
        # sis3302new
        #
        elif hsh[ 'module'] == 'mca_sis3302new':
            if hsh['device'].find("sis3302") >=0:
                rootdevicename = hsh[ 'device'].rsplit('.',1)[0]
                last_name =  hsh[ 'device'].rsplit('/',1)[1]
                append = last_name.split('.',1)[0]
                channel = hsh[ 'device'].rsplit( '.',1)[1]
                hsh['controller'] = "sis3302_" + append
                channel = find_channel_number( hsh['hostname'], rootdevicename, hsh['device'])
                hsh['channel'] = "%d" % (int( channel))
                hsh['rootdevicename'] = rootdevicename
        #
        # sis3610 
        #
        elif hsh[ 'module'] == 'sis3610':
            predefined = 0
            for ( rootdevicename, controller) in \
                    [ 
                        ( 'flash/register/diag1.in', 'sis3610in_diag1'),
                        ( 'flash/register/diag1.out', 'sis3610out_diag1'),
                        ( 'flash/register/vls.in', 'sis3610in_vls'),
                        ( 'flash/register/vls.out', 'sis3610out_vls'),
                        ( 'fmc/register/mob.in', 'sis3610in_mob'),
                        ( 'fmc/register/mob.out', 'sis3610out_mob'),
                        ( 'p01/register/exp.in', 'sis3610in_exp'),
                        ( 'p01/register/exp.out', 'sis3610out_exp'),
                        ( 'p01/register/eh2.in', 'sis3610in_eh2'),
                        ( 'p01/register/eh2.out', 'sis3610out_eh2'),
                        ( 'p01/register/eh2.in', 'sis3610in_eh2'),
                        ( 'p01/register/eh2.out', 'sis3610out_eh2'),
                        ( 'p01/register/eh3.in', 'sis3610in_eh3'),
                        ( 'p01/register/eh3.out', 'sis3610out_eh3'),
                      ( 'p02/register/oh1.in', 'sis3610in_oh1'),
                      ( 'p02/register/oh1.out', 'sis3610out_oh1'),
                      ( 'p02/register/eh.in', 'sis3610in_eh'),
                      ( 'p02/register/eh.out', 'sis3610out_eh'),
                      ( 'p02/register/eh1a.in', 'sis3610in_eh1a'),
                      ( 'p02/register/eh1a.out', 'sis3610out_eh1a'),
                      ( 'p02/register/eh1b.in', 'sis3610in_eh1b'),
                      ( 'p02/register/eh1b.out', 'sis3610out_eh1b'),
                      ( 'p02/register/eh2a.in', 'sis3610in_eh2a'),
                      ( 'p02/register/eh2a.out', 'sis3610out_eh2a'),
                      ( 'p02/register/eh2b.in', 'sis3610in_eh2b'),
                      ( 'p02/register/eh2b.out', 'sis3610out_eh2b'),
                      ( 'p02/register/exp.in', 'sis3610in_exp'),
                      ( 'p02/register/exp.out', 'sis3610out_exp'),

                      ( 'p03/register/exp.in', 'sis3610in_exp'),
                      ( 'p03/register/exp.out', 'sis3610out_exp'),
                      ( 'p03nano/register/p03nano.in', 'sis3610in_p03nano'),
                      ( 'p03nano/register/p03nano.out', 'sis3610out_p03nano'),
                      ( 'p04/register/exp1.in', 'sis3610in_exp1'),
                      ( 'p04/register/exp1.out', 'sis3610out_exp1'),
                      ( 'p04/register/exp2.in', 'sis3610in_exp2'),
                      ( 'p04/register/exp2.out', 'sis3610out_exp2'),
                      ( 'p06/register/exp.in', 'sis3610in_exp'),
                      ( 'p06/register/exp.out', 'sis3610out_exp'),
                      ( 'p06/register/mono.in', 'sis3610in_mono'),
                      ( 'p06/register/mono.out', 'sis3610out_mono'),
                      ( 'p07/register/eh1.in', 'sis3610in_eh1'),
                      ( 'p07/register/eh1.out', 'sis3610out_eh1'),
                      ( 'p07/register/eh2.in', 'sis3610in_eh2'),
                      ( 'p07/register/eh2.out', 'sis3610out_eh2'),
                      ( 'p07/register/eh3.in', 'sis3610in_eh3'),
                      ( 'p07/register/eh3.out', 'sis3610out_exp'),
                      ( 'p07/register/exp.in', 'sis3610in_exp'),
                      ( 'p07/register/exp.out', 'sis3610out_eh3'),
                      ( 'p08/register/exp.in', 'sis3610in_exp'),
                      ( 'p08/register/exp.out', 'sis3610out_exp'),
                      ( 'p09/register/exp.in', 'sis3610in_exp'),
                      ( 'p09/register/d1.out', 'sis3610out_d1'),
                      ( 'p09/register/d1.in', 'sis3610in_d1'),
                      ( 'p09/register/eh.out', 'sis3610out_eh'),
                      ( 'p09/register/eh.in', 'sis3610in_eh'),
                      ( 'p09/register/exp.out', 'sis3610out_exp'),
                      ( 'p09/register/haxps.in', 'sis3610in_haxps'),
                      ( 'p09/register/haxps.out', 'sis3610out_haxps'),
                      ( 'p10/register/e1.in', 'sis3610in_e1'),
                      ( 'p10/register/e1.out', 'sis3610out_e1'),
                      ( 'p10/register/e2.in', 'sis3610in_e2'),
                      ( 'p10/register/e2.out', 'sis3610out_e2'),
                      ( 'p10/register/lab-in', 'sis3610in_lab'),
                      ( 'p10/register/lab-out', 'sis3610out_lab'),
                      ( 'p11/register/eh.in', 'sis3610in_eh'),
                      ( 'p11/register/eh.out', 'sis3610out_eh'),
                      ( 'p11/register/eh.i.1.', 'sis3610in_eh1'),
                      ( 'p11/register/eh.i.2.', 'sis3610in_eh2'),
                      ( 'p11/register/eh.i.3.', 'sis3610in_eh3'),
                      ( 'p11/register/eh.o.1.', 'sis3610out_eh1'),
                      ( 'p11/register/eh.o.2.', 'sis3610out_eh2'),
                      ( 'p11/register/eh.o.3.', 'sis3610out_eh3'),
                      ( 'p11/register/nano.in', 'sis3610in_nano'),
                      ( 'p11/register/nano.out', 'sis3610out_nano'),
                      ( 'p11/register/pp.in', 'sis3610in_pp'),
                      ( 'p11/register/pp.out', 'sis3610out_pp'),
                      ( 'p211/register/exp.in', 'sis3610in_exp'),
                      ( 'p211/register/exp.out', 'sis3610out_exp'),
                      ( 'p23/register/eh.in', 'sis3610in_eh2'),
                      ( 'p23/register/eh.out', 'sis3610out_eh2'),
                      ( 'p24/register/eh2.in', 'sis3610in_eh2'),
                      ( 'p24/register/eh2.out', 'sis3610out_eh2'),
                      ( 'p25/register/eh.in', 'sis3610in_eh'),
                      ( 'p25/register/eh.out', 'sis3610out_eh'),
                      ( 'p66/register/exp.in', 'sis3610in_exp'),
                      ( 'p66/register/exp.out', 'sis3610out_exp'),
                      ( 'p104/register/eh.in', 'sis3610in_eh'),
                      ( 'p104/register/eh.out', 'sis3610out_eh'),
                      ]:
                if hsh[ 'device'].find( rootdevicename) >= 0:
                    hsh['controller'] = controller
                    hsh['rootdevicename'] = rootdevicename
                    channel = find_channel_number( hsh['hostname'], rootdevicename, hsh['device'])
                    hsh['channel'] = "%d" % int( channel)
                    predefined = 1
                    break
            if not predefined:
                test_end = hsh['device'].rsplit('.',1)[1]
                tmp_end = ''
                try:
                    channel = int(test_end)
                except:
                    if test_end.find('in') != -1:
                        tmp_end = 'in'
                    elif test_end.find('out') != -1:
                        tmp_end = 'out'
                device_split = hsh['device'].rsplit('.'+tmp_end,1)[0]
                if tmp_end == '':
                    rootdevicename =  hsh['device'].rsplit('.',1)[0]
                else:
                    rootdevicename =  hsh['device'].rsplit(tmp_end,1)[0] + tmp_end
            
                device_split = device_split.split('/')
                if hsh['device'].find(':') == -1:
                    index = 1
                    pref = ''
                else:
                    index = 2
                    pref = device_split[0].split(':')[0] + "_"
                    hsh['device'] = hsh['device'].split('/',1)[1]
                controller = 'sis3610_' + pref + device_split[index+1].replace('.','') + tmp_end
            
                hsh['controller'] = controller
                if rootdevicename.find(':') >=0:
                    rootdevicename = rootdevicename.split('/',1)[1]
                hsh['rootdevicename'] = rootdevicename
                channel = find_channel_number( hsh['hostname'], rootdevicename, hsh['device'])
                hsh['channel'] = "%d" % int( channel)  
        #
        # sis3820
        #
        elif hsh[ 'module'] == 'sis3820':
            predefined = 0
            for ( rootdevicename, controller) in \
                    [ ( 'delay/counter/exp', 'sis3820_exp'),
                      ( 'fmc/counter/mob', 'sis3820_mob'),
                      ( 'p01/counter/exp', 'sis3820_exp'),
                      ( 'p01/counter/eh2', 'sis3820_eh2'),
                      ( 'p01/counter/eh3', 'sis3820_eh3'),
                      ( 'p02/counter/oh1', 'sis3820_oh1'),
                      ( 'p02/counter/eh1a', 'sis3820_eh1a'),
                      ( 'p02/counter/eh1b', 'sis3820_eh1b'),
                      ( 'p02/counter/eh2a', 'sis3820_eh2a'),
                      ( 'p03/counter/exp', 'sis3820_exp'),
                      ( 'p03nano/counter/p03nano', 'sis3820_p03nano'),
                      ( 'p06/counter/mono', 'sis3820_mono'),
                      ( 'p06/counter/exp', 'sis3820_exp'),
                      ( 'p07/counter/eh1', 'sis3820_eh1'),
                      ( 'p07/counter/eh2', 'sis3820_eh2'),
                      ( 'p07/counter/eh3', 'sis3820_eh3'),
                      ( 'p07/counter/eh4', 'sis3820_eh4'),
                      ( 'p07/counter/exp', 'sis3820_exp'),
                      ( 'p08/counter/exp', 'sis3820_exp'),
                      ( 'p09/counter/exp', 'sis3820_exp'),
                      ( 'p09/counter/oh1', 'sis3820_oh1'),   # tk tests
                      ( 'p09/counter/mono', 'sis3820_mono'),
                      ( 'p09/counter/eh', 'sis3820_eh'),
                      ( 'p09/counter/mag', 'sis3820_mag'),
                      ( 'p09/counter/haxps', 'sis3820_haxps'),
                      ( 'p10/counter/e1', 'sis3820_e1'),
                      ( 'p10/counter/e2', 'sis3820_e2'),
                      ( 'p10/counter/lab', 'sis3820_lab'),
                      ( 'p11/counter/ehc', 'sis3820_ehc'),
                      ( 'p11/counter/nano', 'sis3820_nano'),
                      ( 'p11/counter/pp', 'sis3820_pp'),
                      ( 'p23/counter/eh', 'sis3820_eh'),
                      ( 'p24/counter/exp', 'sis3820_exp'),
                      ( 'p65/counter/a2', 'sis3820_a2'),
                      ( 'p66/counter/exp', 'sis3820_exp'),
                      ]:
                if hsh[ 'device'].find( rootdevicename) >= 0:
                    hsh['controller'] = controller
                    hsh['rootdevicename'] = rootdevicename
                    channel = find_channel_number( hsh['hostname'], rootdevicename, hsh['device'])
                    hsh['channel'] = "%d" % int( channel)
                    predefined = 1
                    break
            if not predefined:
                device_split = hsh['device'].rsplit('.',1)[0]
                rootdevicename = device_split
                device_split = device_split.split('/')                
                if hsh['device'].find(':') == -1:
                    index = 1
                    pref = ''
                else:
                    index = 2
                    pref = device_split[0].split(':')[0] + "_"
                    hsh['device'] = hsh['device'].split('/',1)[1]
                controller = 'sis3820_' + pref + device_split[index+1].replace('.','')
                hsh['controller'] = controller
                if rootdevicename.find(':') >=0:
                    rootdevicename = rootdevicename.split('/',1)[1]
                hsh['rootdevicename'] = rootdevicename
                channel = find_channel_number( hsh['hostname'], rootdevicename, hsh['device'])
                hsh['channel'] = "%d" % int( channel)
        #
        # sis8800
        #
        elif hsh[ 'module'] == 'sis8800':
            predefined = 0
            for ( rootdevicename, controller) in \
                    [ ( 'p09/sis8800/eh', 'sis8800_eh'),
                      ]:
                if hsh[ 'device'].find( rootdevicename) >= 0:
                    hsh['controller'] = controller
                    hsh['rootdevicename'] = rootdevicename
                    channel = find_channel_number( hsh['hostname'], rootdevicename, hsh['device'])
                    hsh['channel'] = "%d" % int( channel)
                    predefined = 1
                    break
        #
        # v260
        #
        elif hsh[ 'module'] == 'v260':
            predefined = 0
            for ( rootdevicename, controller) in \
                    [ ( 'p24eh1/counter/exp', 'v260_exp'),
                      ]:
                if hsh[ 'device'].find( rootdevicename) >= 0:
                    hsh['controller'] = controller
                    hsh['rootdevicename'] = rootdevicename
                    channel = find_channel_number( hsh['hostname'], rootdevicename, hsh['device'])
                    hsh['channel'] = "%d" % int( channel)
                    predefined = 1
                    break
            if not predefined:
                device_split = hsh['device'].rsplit('.',1)[0]
                rootdevicename = device_split
                device_split = device_split.split('/')                
                if hsh['device'].find(':') == -1:
                    index = 1
                    pref = ''
                else:
                    index = 2
                    pref = device_split[0].split(':')[0] + "_"
                    hsh['device'] = hsh['device'].split('/',1)[1]
                controller = 'v260_' + pref + device_split[index+1].replace('.','')
                hsh['controller'] = controller
                if rootdevicename.find(':') >=0:
                    rootdevicename = rootdevicename.split('/',1)[1]
                hsh['rootdevicename'] = rootdevicename
                channel = find_channel_number( hsh['hostname'], rootdevicename, hsh['device'])
                hsh['channel'] = "%d" % int( channel)
        #
        # vdot32
        #
        elif hsh[ 'module'] == 'vdot32in':
            predefined = 0
            for ( rootdevicename, controller) in \
                    [ 
                        ( 'p24eh1/vdot32/ext', 'vdot32in_ext'),
                      ]:
                if hsh[ 'device'].find( rootdevicename) >= 0:
                    hsh['controller'] = controller
                    hsh['rootdevicename'] = rootdevicename
                    channel = find_channel_number( hsh['hostname'], rootdevicename, hsh['device'])
                    hsh['channel'] = "%d" % int( channel)
                    predefined = 1
                    break
            if not predefined:
                print( "*** SardanaConvert.main: trouble with %s" % hsh['device'])
        #
        # spk
        #
        elif hsh[ 'module'] == 'spk':
            predefined = 0
            for ( rootdevicename, controller) in \
                [ ( 'p01/slt/exp', 'slt_exp'),
                  ( 'p02/slt/exp', 'slt_exp'),
                  ( 'p04/slt/exp', 'slt_exp'),
                  ( 'p04/spk/exp', 'spk_exp'),
                  ( 'p06/slt/exp', 'slt_exp'),
                  ( 'p06/spk/exp', 'spk_exp'),
                  ( 'p07/slt/exp', 'slt_exp'),
                  ( 'p09/slt/exp', 'slt_exp'),  # also used by P08
                  ( 'p09/spk/exp', 'spk_exp'),  
                  ( 'p10/slt/exp', 'slt_exp'),  
                  ( 'p10/spk/exp', 'spk_exp'),  
                ]:
                if hsh[ 'device'].find( rootdevicename) >= 0:
                    hsh['controller'] = controller
                    hsh['rootdevicename'] = rootdevicename
                    channel = find_channel_number( hsh['hostname'], rootdevicename, hsh['device'])
                    hsh['channel'] = "%d" % int( channel)
                    predefined = 1
                    break
            #
            # one channel controller
            #
            for ( rootdevicename, controller) in \
                [ ( 'p03/slt/exp.03', 'slt_exp03'),
                  ( 'p03/slt/exp.04', 'slt_exp04'),
                  ( 'p03/slt/exp.05', 'slt_exp05'),
                  ( 'p03/slt/exp.06', 'slt_exp06'),
                  ( 'p03/spk/exp.07', 'spk_exp07'),
                  ( 'p03/spk/exp.08', 'spk_exp08'),
                  ( 'p03/spk/exp.09', 'spk_exp09'),
                  ( 'p03/spk/exp.10', 'spk_exp10'),
                  ( 'p03/spk/exp.11', 'spk_exp11'),
                  ( 'p03/spk/exp.12', 'spk_exp12'),
                  ( 'p08/slt/exp.03', 'slt_exp03'),
                  ( 'p08/slt/exp.04', 'slt_exp04'),
                  ( 'p08/slt/exp.05', 'slt_exp05'),
                  ( 'p08/slt/exp.06', 'slt_exp06'),
                ]:
                if hsh[ 'device'].find( rootdevicename) >= 0:
                    hsh['controller'] = controller
                    hsh['rootdevicename'] = rootdevicename
                    hsh['channel'] = "1"
                    predefined = 1
                    break
            if not predefined:
                device_split = hsh['device'].rsplit('.',1)[0]
                rootdevicename = device_split
                device_split = device_split.split('/')                
                if hsh['device'].find(':') == -1:
                    index = 1
                    pref = ''
                else:
                    index = 2
                    pref = device_split[0].split(':')[0] + "_"
                    hsh['device'] = hsh['device'].split('/',1)[1]
                controller = device_split[index] + '_' + pref + "_" + device_split[index+1].replace('.','')
                controller.replace("__", "_")
                hsh['controller'] = controller
                if rootdevicename.find(':') >=0:
                    rootdevicename = rootdevicename.split('/',1)[1]
                hsh['rootdevicename'] = rootdevicename
                channel = find_channel_number( hsh['hostname'], rootdevicename, hsh['device'])
                hsh['channel'] = "%d" % int( channel)   
                
        #
        # tip551
        #
        elif hsh[ 'module'] == 'tip551':
            predefined = 0
            for ( rootdevicename, controller) in \
                    [ ( 'delay/dac/exp', 'tip551_exp'),
                      ( 'p01/dac/exp', 'tip551_exp'),
                      ( 'p01/dac/oh1', 'tip551_oh1'),
                      ( 'p01/dac/eh3', 'tip551_eh3'),
                      ( 'P02/dac/oh1', 'tip551_oh1'),
                      ( 'P02/dac/eh1b', 'tip551_eh1b'),
                      ( 'p03/dac/exp', 'tip551_exp'),
                      ( 'p03nano/dac/p03nano', 'tip551_p03nano'),
                      ( 'p06/dac/exp', 'tip551_exp'),
                      ( 'p07/dac/eh2a', 'tip551_eh2a'),
                      ( 'p08/dac/exp', 'tip551_exp'),
                      ( 'p09/dac/exp', 'tip551_exp'),
                      ( 'p09/dac/haxps', 'tip551_haxps'),
                      ( 'p09/dac/eh', 'tip551_eh'),
                      ( 'p10/dac/e1', 'tip551_e1'),
                      ( 'p10/dac/e2', 'tip551_e2'),
                      ( 'P10/dac/opt', 'tip551_opt'),
                      ( 'p11/dac/ehc', 'tip551_ehc'),
                      ( 'p11/dac/eh', 'tip551_eh'),
                      ( 'p11/dac/pp', 'tip551_pp'),
                      ( 'p24/dac/exp', 'tip551_exp'),
                      ( 'p66/dac/exp', 'tip551_exp'),
                      ]:
                if hsh[ 'device'].find( rootdevicename) >= 0:
                    hsh['controller'] = controller
                    hsh['rootdevicename'] = rootdevicename
                    channel = find_channel_number( hsh['hostname'], rootdevicename, hsh['device'])
                    hsh['channel'] = "%d" % int( channel)
                    predefined = 1
                    break
            if not predefined:
                device_split = hsh['device'].rsplit('.',1)[0]
                rootdevicename = device_split
                device_split = device_split.split('/')                
                if hsh['device'].find(':') == -1:
                    index = 1
                    pref = ''
                else:
                    index = 2
                    pref = device_split[0].split(':')[0] + "_"
                    hsh['device'] = hsh['device'].split('/',1)[1]
                controller = 'tip551_' + pref + device_split[index+1].replace('.','')
                hsh['controller'] = controller
                if rootdevicename.find(':') >=0:
                    rootdevicename = rootdevicename.split('/',1)[1]
                hsh['rootdevicename'] = rootdevicename
                channel = find_channel_number( hsh['hostname'], rootdevicename, hsh['device'])
                hsh['channel'] = "%d" % int( channel)
        #
        # tip830
        #
        elif hsh[ 'module'] == 'tip830':
            predefined = 0
            for ( rootdevicename, controller) in \
                    [ ( 'delay/adc/exp', 'tip830_exp'),
                      ( 'p01/adc/exp', 'tip830_exp'),
                      ( 'p01/adc/oh1', 'tip830_oh1'),
                      ( 'p01/adc/eh3', 'tip830_eh3'),
                      ( 'P02/adc/oh1', 'tip830_oh1'),
                      ( 'p02/adc/oh1', 'tip830_oh1'),
                      ( 'p02/adc/eh1b', 'tip830_eh1b'),
                      ( 'p02/adc/eh2b', 'tip830_eh2b'),
                      ( 'p03/adc/exp', 'tip830_exp'),
                      ( 'p03nano/adc/p03nano', 'tip830_p03nano'),
                      ( 'p07/adc/eh2', 'tip830_eh2'),
                      ( 'p07/adc/eh2a', 'tip830_eh2a'),
                      ( 'p06/adc/exp', 'tip830_exp'),
                      ( 'p08/adc/exp', 'tip830_exp'),
                      ( 'p09/adc/exp', 'tip830_exp'),
                      ( 'p09/adc/haxps', 'tip830_hasps'),
                      ( 'p09/adc/d1', 'tip830_d1'),
                      ( 'p09/adc/eh', 'tip830_eh'),
                      ( 'p10/adc/e1', 'tip830_e1'),
                      ( 'p10/adc/e2', 'tip830_e2'),
                      ( 'P10/adc/opt', 'tip830_opt'),
                      ( 'p11/adc/ehc', 'tip830_ehc'),
                      ( 'p11/adc/eh', 'tip830_eh'),
                      ( 'p11/adc/if', 'tip830_if'),
                      ( 'p11/adc/pp', 'tip830_pp'),
                      ( 'p211/adc/exp', 'tip830_exp'),
                      ( 'p24/adc/exp', 'tip830_exp'),
                      ( 'p25/adc/eh', 'tip830_eh'),
                      ( 'p61/adc/eh', 'tip830_eh'),
                      ( 'p66/adc/exp', 'tip830_exp'),
                      ( 'metro/adc/eh', 'tip830_eh'),
                      ( 'slm/adc/lab', 'tip830_lab'),
                      ]:
                if hsh[ 'device'].find( rootdevicename) >= 0:
                    hsh['controller'] = controller
                    hsh['rootdevicename'] = rootdevicename
                    channel = find_channel_number( hsh['hostname'], rootdevicename, hsh['device'])
                    hsh['channel'] = "%d" % int( channel)
                    predefined = 1
                    break
            if not predefined:
                device_split = hsh['device'].rsplit('.',1)[0]
                rootdevicename = device_split
                device_split = device_split.split('/')                
                if hsh['device'].find(':') == -1:
                    index = 1
                    pref = ''
                else:
                    index = 2
                    pref = device_split[0].split(':')[0] + "_"
                    hsh['device'] = hsh['device'].split('/',1)[1]
                controller = 'tip830_' + pref + device_split[index+1].replace('.','')
                hsh['controller'] = controller
                if rootdevicename.find(':') >=0:
                    rootdevicename = rootdevicename.split('/',1)[1]
                hsh['rootdevicename'] = rootdevicename
                channel = find_channel_number( hsh['hostname'], rootdevicename, hsh['device'])
                hsh['channel'] = "%d" % int( channel)
        #
        # tip850adc
        #
        elif hsh[ 'module'] == 'tip850adc':
            predefined = 0
            for ( rootdevicename, controller) in \
                    [ ( 'flash/tip850adc/adcs', 'tip850adc_s'),
                      ( 'flash/tip850adc/adc', 'tip850adc_exp'),
                      ( 'p24eh1/tip850adc/exp', 'tip850adc_exp'),
                      ]:
                if hsh[ 'device'].find( rootdevicename) >= 0:
                    hsh['controller'] = controller
                    hsh['rootdevicename'] = rootdevicename
                    channel = find_channel_number( hsh['hostname'], rootdevicename, hsh['device'])
                    hsh['channel'] = "%d" % int( channel)
                    predefined = 1
                    break
            if not predefined:
                device_split = hsh['device'].rsplit('.',1)[0]
                rootdevicename = device_split
                device_split = device_split.split('/')                
                if hsh['device'].find(':') == -1:
                    index = 1
                    pref = ''
                else:
                    index = 2
                    pref = device_split[0].split(':')[0] + "_"
                    hsh['device'] = hsh['device'].split('/',1)[1]
                controller = 'tip850adc_' + pref + device_split[index+1].replace('.','')
                hsh['controller'] = controller
                if rootdevicename.find(':') >=0:
                    rootdevicename = rootdevicename.split('/',1)[1]
                hsh['rootdevicename'] = rootdevicename
                channel = find_channel_number( hsh['hostname'], rootdevicename, hsh['device'])
                hsh['channel'] = "%d" % int( channel)
            
        #
        # tip850dac
        #
        elif hsh[ 'module'] == 'tip850dac':
            predefined = 0
            for ( rootdevicename, controller) in \
                    [ ( 'flash/tip850adc/dac', 'tip850dac_exp'),
                      ( 'p24eh1/tip850adc/exp', 'tip850dac_exp'),
                      ]:
                if hsh[ 'device'].find( rootdevicename) >= 0:
                    hsh['controller'] = controller
                    hsh['rootdevicename'] = rootdevicename
                    channel = find_channel_number( hsh['hostname'], rootdevicename, hsh['device'])
                    hsh['channel'] = "%d" % int( channel)
                    predefined = 1
                    break
            if not predefined:
                device_split = hsh['device'].rsplit('.',1)[0]
                rootdevicename = device_split
                device_split = device_split.split('/')                
                if hsh['device'].find(':') == -1:
                    index = 1
                    pref = ''
                else:
                    index = 2
                    pref = device_split[0].split(':')[0] + "_"
                    hsh['device'] = hsh['device'].split('/',1)[1]
                controller = 'tip830_' + pref + device_split[index+1].replace('.','')
                hsh['controller'] = controller
                if rootdevicename.find(':') >=0:
                    rootdevicename = rootdevicename.split('/',1)[1]
                hsh['rootdevicename'] = rootdevicename
                channel = find_channel_number( hsh['hostname'], rootdevicename, hsh['device'])
                hsh['channel'] = "%d" % int( channel)
            
        #
        # vfcadc
        #
        elif hsh[ 'module'] == 'vfcadc':
            predefined = 0
            for ( rootdevicename, controller) in \
                    [ ( 'delay/vfc/exp', 'vfcadc_exp'),
                      ( 'fmc/vfc/mob', 'vfcadc_mob'),
                      ( 'p01/vfc/eh2', 'vfcadc_eh2'),
                      ( 'p01/vfc/eh3', 'vfcadc_eh3'),
                      ( 'P02/vfc/oh1', 'vfcadc_oh1'),
                      ( 'P02/vfc/eh1a', 'vfcadc_eh1a'),
                      ( 'p02/vfc/eh2a', 'vfcadc_eh2a'),
                      ( 'p02/vfc/eh1b', 'vfcadc_eh1b'),
                      ( 'p02/vfc/eh2b', 'vfcadc_eh2b'),
                      ( 'p03/vfc/exp', 'vfcadc_exp'),
                      ( 'p03nano/vfc/p03nano', 'vfcadc_p03nano'),
                      ( 'p04/vfc/exp1', 'vfcadc_exp1'),
                      ( 'p04/vfc/exp2', 'vfcadc_exp2'),
                      ( 'p06/vfc/exp', 'vfcadc_exp'),
                      ( 'P06/vfc/mono', 'vfcadc_mono'),
                      ( 'p07/vfc/eh1', 'vfcadc_eh1'),
                      ( 'p07/vfc/eh2', 'vfcadc_eh2'),
                      ( 'p07/vfc/eh3', 'vfcadc_eh3'),
                      ( 'p08/vfc/exp', 'vfcadc_exp'),
                      ( 'p09/vfc/exp', 'vfcadc_exp'),
                      ( 'p09/vfc/mono', 'vfcadc_mono'),
                      ( 'p09/vfc/mag', 'vfcadc_mag'),
                      ( 'p09/vfc/haxps', 'vfcadc_haxps'),
                      ( 'p09/vfc/eh', 'vfcadc_eh'),
                      ( 'p10/vfc/e1', 'vfcadc_e1'),
                      ( 'p10/vfc/e2', 'vfcadc_e2'),
                      ( 'p10/adc/lab-vfc', 'vfcadc_lab'),
                      ( 'p11/vfc/ehb', 'vfcadc_ehb'),
                      ( 'p11/vfc/ehc', 'vfcadc_ehc'),
                      ( 'p11/vfc/pp2', 'vfcadc_pp2'),
                      ( 'p11/vfc/eh.1', 'vfcadc_eh1'),
                      ( 'p11/vfc/pp', 'vfcadc_pp'),
                      ( 'p65/vfc/exp', 'vfcadc_exp'),
                      ]:
                if hsh[ 'device'].find( rootdevicename) >= 0:
                    hsh['controller'] = controller
                    hsh['rootdevicename'] = rootdevicename
                    channel = find_channel_number( hsh['hostname'], rootdevicename, hsh['device'])
                    hsh['channel'] = "%d" % int( channel)
                    predefined = 1
                    break
            if not predefined:
                device_split = hsh['device'].rsplit('.',1)[0]
                rootdevicename = device_split
                device_split = device_split.split('/')                
                if hsh['device'].find(':') == -1:
                    index = 1
                    pref = ''
                else:
                    index = 2
                    pref = device_split[0].split(':')[0] + "_"
                    hsh['device'] = hsh['device'].split('/',1)[1]
                controller = 'vfcadc_' + pref + device_split[index+1].replace('.','')
                hsh['controller'] = controller
                if rootdevicename.find(':') >=0:
                    rootdevicename = rootdevicename.split('/',1)[1]
                hsh['rootdevicename'] = rootdevicename
                channel = find_channel_number( hsh['hostname'], rootdevicename, hsh['device'])
                hsh['channel'] = "%d" % int( channel)
        else:
            pass

        #
        # channel == -1 probably because the device is not exported
        #
        if 'channel' in hsh and hsh['channel'] == '-1':
            print( "SardanaConvert: %s offline, ignore" % (hsh['name']))
        else:
            #print( "+++SardanaConvert: print %s %s" % (hsh['name'], repr( hsh)))
            if not printDevice( hsh):
                _print( "<!-- error printing %s --> " % hsh['name'])

    _print( "</hw>")
    return 1

    
    
#
#
#

usage = "\n %prog -f /online_dir/online.xml -o /online_dir/onlineSardana.xml \n" + \
        "   create /online_dir/onlineSardand.xml \n"
parser = OptionParser(usage=usage)
parser.add_option( "-f", action="store", type="string", 
                   dest="xmlFileIn", help="input xmlfile, e.g. online.xml" )
parser.add_option( "-o", action="store", type="string", 
                   dest="xmlFileOut", help="output xmlfile, e.g. onlineSardana.xml" )
parser.add_option( "-t", action="store", dest="tags", 
                   default = None, help="respect tags in online.xml")
#parser.add_option( "-d", action="store_true", 
#                   dest="displayStarterHosts", default = False, 
#                   help="display the devices and StarterHosts")

(options, args) = parser.parse_args()

if options.xmlFileIn is None or \
        options.xmlFileOut is None:
    parser.print_help()
    sys.exit(255)

outFile = open( options.xmlFileOut, "w")

#if options.displayStarterHosts: 
#    parser.print_help()
#    sys.exit(255)

try:
    db = PyTango.Database()
except:
    print( "Can't connect to tango database on %s" % os.getenv('TANGO_HOST'))
    sys.exit(255)

try:
    dbProxy = PyTango.DeviceProxy( "sys/database/2")
except:
    print( "Can't proxy-connect to tango database-2 on %s" % os.getenv('TANGO_HOST'))
    sys.exit(255)

print( "SardanaConvert.py")
if not main():
    outFile.close()
    sys.exit( 255)

print( "SardanaConvert.py created %s" % options.xmlFileOut)
outFile.close()
if not HasyUtils.checkOnlineSardanaXml( options.xmlFileOut):
    sys.exit( 255)
sys.exit(0)



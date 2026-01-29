#!/usr/bin/env python
#
# this script executes an installation verification procedure
#
import sys, os, time, atexit
import shutil
import HasyUtils
import PyTango

doorProxy = None
scanDirOld = None

def exitHandler():
    print( "SardanaIVP.exithandler")
    if not scanDirOld is None:
        HasyUtils.setEnv( 'ScanDir', scanDirOld)
    os.system( "kill_proc -f SardanaMotorMonitor.py")
    os.system( "kill_proc -f SardanaMonitor.py")
    os.system( "kill_proc -f pyspMonitor.py")
    os.system( "kill_proc -f SardanaInfoViewer.py")
    os.system( "echo \"IVP run: %s\" >> /online_dir/SardanaIVP.log" % HasyUtils.getDateTime())
    os.system( "dpkg -l python3-hasyutils >> /online_dir/SardanaIVP.log")
 
def checkComponents(): 
    '''
    make sure that pilatus is in the list of components,  
    it is used for the nexus test
    '''

    prc = os.popen( "nxsconfig list")
    nxsList = prc.read()
    prc.close()
    
    comps = [
        'beamtime_id', 
        'default', 
        'defaultinstrument', 
        'defaultsample', 
        'eh_c01', 
        'eh_c02', 
        'eh_mca01', 
        'eh_vfc01', 
        'eh_vfc02', 
        'eh_vfc03', 
        'eh_vfc04', 
        'eh_vfc05', 
        'eh_vfc06', 
        'eh_vfc07', 
        'eh_vfc08', 
        'pilatus', 
        'slit1', 
        'source'] 

    for elm in comps: 
        if elm not in nxsList: 
            print( "SardanaIVP.checkComponents: %s component is missing" % elm)
            sys.exit(255)

    return 
    
def checkHasyUtils():
    print( ">>> HasyUtils")
    #
    # look at sardana versions
    #
    #ver = HasyUtils.getVersionSardana()
    #if HasyUtils.getHostname() == 'haso107d1' and ver != '3.0.4.1-1+deb10u1~fsec':
    #    print( "SardanaIVP.checkHasyUtils: wrong Sardana version: %s" % ver)
    #    sys.exit()

    # 27.09.2018, replaced '2.4.1.4-1+deb9u4~fsec':
    # 19.10.2018, replaced '2.5.1.3-1+deb9u5~fsec
    # 14.05.2019, replaced '2.5.1.2-1+deb9u5~fsec'
    # 11.07.2019, replaced '2.5.1.5-3+deb9u5~fsec'
    # 11.07.2019, replaced '2.8.1.1-1+deb9u5~fsec' on 11.7.2019, tests failed
    # 24.07.2019, replaced '2.5.1.5-1+deb9u5~fsec' on 11.7.2019, tests failed
    # 19.08.2019, replaced '2.5.1.6-1+deb9u5~fsec' on 11.7.2019, tests failed
    # 21.08.2019, replaced '2.5.1.5-3+deb9u5~fsec' on 11.7.2019, tests failed
    #if HasyUtils.getHostname() == 'haso107tk' and ver != '2.5.1.6-1+deb9u9~fsec': 
    #    print( "SardanaIVP.checkHasyUtils: wrong Sardana version: %s" % ver)
    #    sys.exit()

    #if HasyUtils.getHostname() == 'haso107d1' and not HasyUtils.versionSardanaNewMg():
    #    print( "SardanaIVP.checkHasyUtils: wrong reply by veRsionSardanaNewMg")
    #    sys.exit()

    # storeEnv()
    #
    os.system( "/bin/rm /home/kracht/Misc/IVP/*.env")
    envFile = HasyUtils.storeEnv( "/home/kracht/Misc/IVP") 
    if envFile is None:
        print( "SardanaIVP.checkhasyUtils: storeEnv() returned None")
        sys.exit()
    if not os.path.exists( envFile):
        print( "SardanaIVP.checkhasyUtils: storeEnv, %s does not exist" % envFile)
        sys.exit()
    print( "SardanaIVP.checkHasyUtils: stored env %s" % envFile)
    #
    # check tags
    # 
    a = HasyUtils.getOnlineXML( xmlFile = "/home/kracht/Misc/IVP/onlineIVP.xml")
    if len(a) != 23:
        print( "SardanaIVP.checkhasyUtils: tags, len(), != 23, %d" % len( a))
        sys.exit()
    a = HasyUtils.getOnlineXML( xmlFile = "/home/kracht/Misc/IVP/onlineIVP.xml", cliTags = "standard")
    if len(a) != 20:
        print( "SardanaIVP.checkhasyUtils: tags, 'standard', len() != 20, %d" % len( a))
        sys.exit()
    a = HasyUtils.getOnlineXML( xmlFile = "/home/kracht/Misc/IVP/onlineIVP.xml", cliTags = "pilatus")
    if len(a) != 1:
        print( "SardanaIVP.checkhasyUtils: tags, 'pilatus', len() != 1 %d" % len(a))
        sys.exit()
    a = HasyUtils.getOnlineXML( xmlFile = "/home/kracht/Misc/IVP/onlineIVP.xml", cliTags = " expert, pilatus")
    if len(a) != 2:
        print( "SardanaIVP.checkhasyUtils: tags, 'expert, pilatus', len() != 1, %d" % len(a))
        sys.exit()
    print( "SardanaIVP.checkHasyUtils: tags, 4 tests OK")
        
    tmp = HasyUtils.getHostname()

    dev = HasyUtils.getDeviceNameByAlias( "eh_mot65")
    if dev != 'motor/omsvme58_eh/65':
        print( "SardanaIVP.checkHasyUtils: wrong device name for eh_mot65: %s Pool running?" % dev)
        sys.exit()
    al = HasyUtils.getAlias( dev)
    if al != "eh_mot65":
        print( "SardanaIVP.checkHasyUtils: wrong alias for %s : %s" % ( dev, al))
        sys.exit()
        
    tmp = HasyUtils.getHostnameLong()
        
    lst = HasyUtils.getDoorNames()
    if len(lst) != 3:
        print( "SardanaIVP.checkHasyUtils: no. of door names != 3")
        sys.exit()

    if HasyUtils.getHostname() == 'haso107d1' and lst[0] != 'p09/door/haso107d1.01':
        print( "SardanaIVP.checkHasyUtils: wrong first door name %s" % lst[0])
        sys.exit()

    if HasyUtils.getHostname() == 'haso107d10' and lst[0] != 'p09/door/haso107d10.01':
        print( "SardanaIVP.checkHasyUtils: wrong first door name %s" % lst[0])
        sys.exit()
    #
    # petra/globals/keyword
    #
    res = HasyUtils.petraBeamCurrent()
    if res is None:
        print( "HasyUtils.petraBeamCurrent() returnd None")
        sys.exit()
    print( "SardanaIVP.checkHasyUtils: petraBeamCurrent %g" % res)

    res = HasyUtils.petraMachineState()
    if res is None:
        print( "HasyUtils.petraMachinState() returnd None")
        sys.exit()
    print( "SardanaIVP.checkHasyUtils: petraMachineState %s" % res)

    res = HasyUtils.petraMachineStateText()
    if res is None:
        print( "HasyUtils.petraMachinStateText() returnd None")
        sys.exit()
    print( "SardanaIVP.checkHasyUtils: petraMachineStateText %s" % res)

    res = HasyUtils.petraMachineStateExt()
    if res is None:
        print( "HasyUtils.petraMachinStateExt() returnd None")
        sys.exit()
    print( "SardanaIVP.checkHasyUtils: petraMachineStateExt %s" % res)

    res = HasyUtils.petraMachineStateTextExt()
    if res is None:
        print( "HasyUtils.petraMachinStateTextExt() returnd None")
        sys.exit()
    print( "SardanaIVP.checkHasyUtils: petraMachineStateTextExt %s" % res)

    res = HasyUtils.checkHostExists( "haspp08")
    if not res:
        print( "HasyUtils.checkHostExists, haspp08, return False")
        sys.exit()
    print( "SardanaIVP.checkHasyUtils: haspp08 exists")

    res = HasyUtils.checkHostExists( "haspp08kkk")
    if res:
        print( "HasyUtils.checkHostExists, haspp08kkk, returned True")
        sys.exit()

    res = HasyUtils.checkHostOnline( "haspp08")
    if not res:
        print( "HasyUtils.checkHostExists, haspp08, is not online")
        sys.exit()
    print( "SardanaIVP.checkHasyUtils: haspp08 is online")

    res = HasyUtils.checkHostRootLogin( "haspp08")
    if not res:
        print( "HasyUtils.checkHostExists, haspp08, no root login")
        sys.exit()
    print( "SardanaIVP.checkHasyUtils: haspp08, root login OK")
        
    print( ">>> HasyUtils, OK")

def checkPoolMsDoorMg():
    """
    checks, if there is one pool, one macroserver, three doors
    creates mg_ivp
    """
    global doorProxy
 
    print( ">>> checkPoolMsDoor")

    pools = HasyUtils.getPoolNames()
    if len( pools) != 1:
        print( "no. of pools != 1 %s" % repr(pools))
        sys.exit()
    print( "Pool %s ok" % repr(pools))

    macroServers = HasyUtils.getMacroServerNames()
    if len( macroServers) != 1:
        print( "no. of macroServers != 1 %s " % repr( macroServers))
        sys.exit()
    print( "MacroServer %s" % repr( macroServers))

    doors = HasyUtils.getDoorNames()    
    if len( doors) != 3:
        print( "no. of doors != 3 %s" % repr(doors))
        sys.exit()
    print( "Doors: %s ok" % repr(doors))
    #
    # create mg_ivp
    #
    timers = HasyUtils.getTimerAliases()
    counters = HasyUtils.getCounterAliases()
    mgAliases = HasyUtils.getMgAliases()
    mcas = HasyUtils.getMcaAliases()
    if True or "mg_ivp" not in mgAliases: 
        if timers is None:
            print( "failed to create mg_ivp: no timers")
            sys.exit( 255)
        if counters is None:
            print( "failed to create mg_ivp: no counter")
            sys.exit( 255)
        if mcas is None:
            print( "failed to create mg_ivp: no mca")
            sys.exit( 255)
        counterStr = "%s" % counters[0]
        if HasyUtils.isDevice( "sig_gen"):
            counterStr = counterStr + ",sig_gen"
        if HasyUtils.isDevice( "exp_petra"):
            counterStr = counterStr + ",exp_petra"
        if HasyUtils.isDevice( "pilatus"):
            pilatusStr = "pilatus"

        pVersion = ''
        if sys.version_info.major  == 3: 
            pVersion = '3'
        cmd = "SardanaChMg%s.py -p %s -g mg_ivp -t %s -c %s -m %s -q %s" % ( pVersion, pools[0], timers[0], counterStr, mcas[0], pilatusStr)
        print( "cmd: %s" % cmd)
        os.system( cmd)

    elemList = HasyUtils.getMgElements( "mg_ivp")
    print( "mv_ivp contains %s " % str( elemList))
    if not timers[0] in elemList or \
            not counters[0] in elemList or \
            not mcas[0] in elemList:
        print( "mg_ivp %s,\n does not contain expected element" % str( elemList))
        sys.exit( 255)

    HasyUtils.setEnv( 'ActiveMntGrp', 'mg_ivp')
    doorProxy = PyTango.DeviceProxy( doors[0])
    #
    # HasyUtils.checkActiveMntGrpStatus()
    # HasyUtils.getActiveMntGrpStatus()
    #
    print( "SardanaIVP.checkActiveMntGrpStatus()")
    if not HasyUtils.checkActiveMntGrpStatus():
        print( "status of mg_ivp is not OK (1)")
        sys.exit( 255)
    print( "SardanaIVP.checkActiveMntGrpStatus() True, OK")
    '''
    5.9.2019: these tests have to be removed after the hack in the controller
    became necessary. 

    print( "stop SIS3820/EH")
    HasyUtils.stopServer( "SIS3820/EH", None)
    if HasyUtils.checkActiveMntGrpStatus():
        print( "status of mg_ivp should not be OK")
        sys.exit( 255)
    lst = HasyUtils.getActiveMntGrpStatus()
    if lst[0] != 'eh_c01 is in FAULT state':
        print( "eh_c01 should be in FAULT state")
        sys.exit( 255)
    print( "SardanaIVP.checkActiveMntGrpStatus() False, OK")
    print( "start SIS3820/EH")
    HasyUtils.startServer( "SIS3820/EH", None)
    if not HasyUtils.checkActiveMntGrpStatus():
        print( "status of mg_ivp is not OK (2)")
        sys.exit( 255)
    '''
    print( "mg_ivp ok")

def checkSardanaChMgDebian10():
    '''
    check SardanaChMg, in particular the different display/plot options
    '''
    mgName = "mg_chckMg"
    #
    # first test: -t, -c options only
    #
    # plot_type controls graphics display
    # output controls spock column selection
    #

    pVersion = ''
    if sys.version_info.major  == 3: 
        pVersion = '3'
 
    cmd = "SardanaChMg%s.py -g %s -t eh_t01 -c eh_c01,eh_c02,eh_c03" % ( pVersion, mgName)
        
    print( "cmd: %s" % cmd)
    os.system( cmd)

    hsh = HasyUtils.getMgConfiguration( mgName) 

    subHsh = hsh[ 'controllers']['tango://haso107d10:10000/controller/sis3820ctrl/sis3820_eh']['channels']

    if subHsh['tango://haso107d10:10000/expchan/sis3820_eh/1']['output'] is not True:
        print( "%s, eh_c01 output is not True" % mgName)
        sys.exit( 255)

    if subHsh['tango://haso107d10:10000/expchan/sis3820_eh/1']['plot_type'] != 1:
        print( "%s, eh_c01 plot_type != 1" % mgName)
        sys.exit( 255)

    if subHsh['tango://haso107d10:10000/expchan/sis3820_eh/2']['output'] is not True:
        print( "%s, eh_c02 output is not True" % mgName)
        sys.exit( 255)

    if subHsh['tango://haso107d10:10000/expchan/sis3820_eh/2']['plot_type'] != 1:
        print( "%s, eh_c02 plot_type != 1" % mgName)
        sys.exit( 255)

    if subHsh['tango://haso107d10:10000/expchan/sis3820_eh/3']['output'] is not True:
        print( "%s, eh_c03 output is not True" % mgName)
        sys.exit( 255)

    if subHsh['tango://haso107d10:10000/expchan/sis3820_eh/3']['plot_type'] != 1:
        print( "%s, eh_c03 plot_type != 1" % mgName)
        sys.exit( 255)
    #
    # second test: -t, -c, -n 
    #
    pVersion = ''
    if sys.version_info.major  == 3: 
        pVersion = '3'

    cmd = "SardanaChMg%s.py -g %s -t eh_t01 -c eh_c01 -n eh_c02,eh_c03" % ( pVersion, mgName)

    print( "cmd: %s" % cmd)
    os.system( cmd)

    hsh = HasyUtils.getMgConfiguration( mgName) 
    subHsh = hsh[ 'controllers']['tango://haso107d10:10000/controller/sis3820ctrl/sis3820_eh']['channels']

    if subHsh['tango://haso107d10:10000/expchan/sis3820_eh/1']['output'] is not True:
        print( "%s, eh_c01 output is not True" % mgName)
        sys.exit( 255)

    if subHsh['tango://haso107d10:10000/expchan/sis3820_eh/1']['plot_type'] != 1:
        print( "%s, eh_c01 plot_type != 1" % mgName)
        sys.exit( 255)

    if subHsh['tango://haso107d10:10000/expchan/sis3820_eh/2']['output'] is not True:
        print( "%s, eh_c02 output is not True" % mgName)
        sys.exit( 255)

    if subHsh['tango://haso107d10:10000/expchan/sis3820_eh/2']['plot_type'] != 0:
        print( "%s, eh_c02 plot_type != 0" % mgName)
        sys.exit( 255)

    if subHsh['tango://haso107d10:10000/expchan/sis3820_eh/3']['output'] is not True:
        print( "%s, eh_c03 output is not True" % mgName)
        sys.exit( 255)

    if subHsh['tango://haso107d10:10000/expchan/sis3820_eh/3']['plot_type'] != 0:
        print( "%s, eh_c03 plot_type != 0" % mgName)
        sys.exit( 255)
    
    #
    # second test -c, --no, --nd, --ndo
    #
    cmd = "SardanaChMg%s.py -g %s -t eh_t01 -c eh_c01 --no eh_c02 --nd eh_c03 --ndo eh_c04" % ( pVersion, mgName)

    print( "cmd: %s" % cmd)
    os.system( cmd)

    hsh = HasyUtils.getMgConfiguration( mgName) 

    subHsh = hsh[ 'controllers']['tango://haso107d10:10000/controller/sis3820ctrl/sis3820_eh']['channels']
    #
    # '-c': output: True, plot_type: 1
    #
    if subHsh['tango://haso107d10:10000/expchan/sis3820_eh/1']['output'] is not True:
        print( "%s, eh_c01 output is not True" % mgName)
        sys.exit( 255)

    if subHsh['tango://haso107d10:10000/expchan/sis3820_eh/1']['plot_type'] != 1:
        print( "%s, eh_c01 plot_type != 1" % mgName)
        sys.exit( 255)

    #
    # '--no': output: False, plot_type: 1
    #
    if subHsh['tango://haso107d10:10000/expchan/sis3820_eh/2']['output'] is not False:
        print( "%s, eh_c02 output is not False" % mgName)
        sys.exit( 255)

    if subHsh['tango://haso107d10:10000/expchan/sis3820_eh/2']['plot_type'] != 1:
        print( "%s, eh_c02 plot_type != 1" % mgName)
        sys.exit( 255)

    #
    # '--nd': output: True, plot_type: 0
    #
    if subHsh['tango://haso107d10:10000/expchan/sis3820_eh/3']['output'] is not True:
        print( "%s, eh_c03 output is not True" % mgName)
        sys.exit( 255)

    if subHsh['tango://haso107d10:10000/expchan/sis3820_eh/3']['plot_type'] != 0:
        print( "%s, eh_c03 plot_type != 0" % mgName)
        sys.exit( 255)

    #
    # '--ndo': output: False, plot_type: 0
    #
    if subHsh['tango://haso107d10:10000/expchan/sis3820_eh/4']['output'] is not False:
        print( "%s, eh_c04 output is not False" % mgName)
        sys.exit( 255)

    if subHsh['tango://haso107d10:10000/expchan/sis3820_eh/4']['plot_type'] != 0:
        print( "mgName, eh_c04 plot_type != 0")
        sys.exit( 255)

    pools = HasyUtils.getPoolNames()
    pool = PyTango.DeviceProxy( pools[0])
    pool.DeleteElement( mgName)

    print( "checkSardanaChMg, OK")

    return 

def checkSardanaChMgDebian11():
    '''
    check SardanaChMg, in particular the different display/plot options
    '''
    mgName = "mg_chckMg"
    #
    # first test: -t, -c options only
    #
    # plot_type controls graphics display
    # output controls spock column selection
    #

    pVersion = ''
    if sys.version_info.major  == 3: 
        pVersion = '3'
 
    cmd = "SardanaChMg%s.py -g %s -t eh_t01 -c eh_c01,eh_c02,eh_c03" % ( pVersion, mgName)
        
    print( "cmd: %s" % cmd)
    os.system( cmd)

    hsh = HasyUtils.getMgConfiguration( mgName) 

    subHsh = hsh[ 'controllers']['tango://haso107d1:10000/controller/sis3820ctrl/sis3820_eh']['channels']

    if subHsh['tango://haso107d1:10000/expchan/sis3820_eh/1']['output'] is not True:
        print( "%s, eh_c01 output is not True" % mgName)
        sys.exit( 255)

    if subHsh['tango://haso107d1:10000/expchan/sis3820_eh/1']['plot_type'] != 1:
        print( "%s, eh_c01 plot_type != 1" % mgName)
        sys.exit( 255)

    if subHsh['tango://haso107d1:10000/expchan/sis3820_eh/2']['output'] is not True:
        print( "%s, eh_c02 output is not True" % mgName)
        sys.exit( 255)

    if subHsh['tango://haso107d1:10000/expchan/sis3820_eh/2']['plot_type'] != 1:
        print( "%s, eh_c02 plot_type != 1" % mgName)
        sys.exit( 255)

    if subHsh['tango://haso107d1:10000/expchan/sis3820_eh/3']['output'] is not True:
        print( "%s, eh_c03 output is not True" % mgName)
        sys.exit( 255)

    if subHsh['tango://haso107d1:10000/expchan/sis3820_eh/3']['plot_type'] != 1:
        print( "%s, eh_c03 plot_type != 1" % mgName)
        sys.exit( 255)
    #
    # second test: -t, -c, -n 
    #
    pVersion = ''
    if sys.version_info.major  == 3: 
        pVersion = '3'

    cmd = "SardanaChMg%s.py -g %s -t eh_t01 -c eh_c01 -n eh_c02,eh_c03" % ( pVersion, mgName)

    print( "cmd: %s" % cmd)
    os.system( cmd)

    hsh = HasyUtils.getMgConfiguration( mgName) 
    subHsh = hsh[ 'controllers']['tango://haso107d1:10000/controller/sis3820ctrl/sis3820_eh']['channels']

    if subHsh['tango://haso107d1:10000/expchan/sis3820_eh/1']['output'] is not True:
        print( "%s, eh_c01 output is not True" % mgName)
        sys.exit( 255)

    if subHsh['tango://haso107d1:10000/expchan/sis3820_eh/1']['plot_type'] != 1:
        print( "%s, eh_c01 plot_type != 1" % mgName)
        sys.exit( 255)

    if subHsh['tango://haso107d1:10000/expchan/sis3820_eh/2']['output'] is not True:
        print( "%s, eh_c02 output is not True" % mgName)
        sys.exit( 255)

    if subHsh['tango://haso107d1:10000/expchan/sis3820_eh/2']['plot_type'] != 0:
        print( "%s, eh_c02 plot_type != 0" % mgName)
        sys.exit( 255)

    if subHsh['tango://haso107d1:10000/expchan/sis3820_eh/3']['output'] is not True:
        print( "%s, eh_c03 output is not True" % mgName)
        sys.exit( 255)

    if subHsh['tango://haso107d1:10000/expchan/sis3820_eh/3']['plot_type'] != 0:
        print( "%s, eh_c03 plot_type != 0" % mgName)
        sys.exit( 255)
    
    #
    # second test -c, --no, --nd, --ndo
    #
    cmd = "SardanaChMg%s.py -g %s -t eh_t01 -c eh_c01 --no eh_c02 --nd eh_c03 --ndo eh_c04" % ( pVersion, mgName)

    print( "cmd: %s" % cmd)
    os.system( cmd)

    hsh = HasyUtils.getMgConfiguration( mgName) 

    subHsh = hsh[ 'controllers']['tango://haso107d1:10000/controller/sis3820ctrl/sis3820_eh']['channels']
    #
    # '-c': output: True, plot_type: 1
    #
    if subHsh['tango://haso107d1:10000/expchan/sis3820_eh/1']['output'] is not True:
        print( "%s, eh_c01 output is not True" % mgName)
        sys.exit( 255)

    if subHsh['tango://haso107d1:10000/expchan/sis3820_eh/1']['plot_type'] != 1:
        print( "%s, eh_c01 plot_type != 1" % mgName)
        sys.exit( 255)

    #
    # '--no': output: False, plot_type: 1
    #
    if subHsh['tango://haso107d1:10000/expchan/sis3820_eh/2']['output'] is not False:
        print( "%s, eh_c02 output is not False" % mgName)
        sys.exit( 255)

    if subHsh['tango://haso107d1:10000/expchan/sis3820_eh/2']['plot_type'] != 1:
        print( "%s, eh_c02 plot_type != 1" % mgName)
        sys.exit( 255)

    #
    # '--nd': output: True, plot_type: 0
    #
    if subHsh['tango://haso107d1:10000/expchan/sis3820_eh/3']['output'] is not True:
        print( "%s, eh_c03 output is not True" % mgName)
        sys.exit( 255)

    if subHsh['tango://haso107d1:10000/expchan/sis3820_eh/3']['plot_type'] != 0:
        print( "%s, eh_c03 plot_type != 0" % mgName)
        sys.exit( 255)

    #
    # '--ndo': output: False, plot_type: 0
    #
    if subHsh['tango://haso107d1:10000/expchan/sis3820_eh/4']['output'] is not False:
        print( "%s, eh_c04 output is not False" % mgName)
        sys.exit( 255)

    if subHsh['tango://haso107d1:10000/expchan/sis3820_eh/4']['plot_type'] != 0:
        print( "mgName, eh_c04 plot_type != 0")
        sys.exit( 255)

    pools = HasyUtils.getPoolNames()
    pool = PyTango.DeviceProxy( pools[0])
    pool.DeleteElement( mgName)

    print( "checkSardanaChMg, OK")

    return 

def checkSardanaChMg():
    '''
    check SardanaChMg, in particular the different display/plot options
    '''
    #
    # there are many hasy107tk-specific things, e.g. controller names
    #
    if HasyUtils.getHostname() == 'haso107d10':
        return checkSardanaChMgDebian10()
    if HasyUtils.getHostname() == 'haso107d1':
        return checkSardanaChMgDebian11()

    print( "SardanaIVP.checkSardanaMg: wrong host name %s" % HasyUtils.getHostName())
    sys.exit( 255)
        
def checkCertainVariables(): 
    """
    checks certain variables, returns 0, if one of these is missing
    """
    print( ">>> Check certain variables")
    argout = True
    for var in ['ActiveMntGrp', 'ScanDir', 'ScanFile', 'SignalCounter']:
        value = HasyUtils.getEnv( var)
        if value is None:
            print( "*** variable '%s' is missing" % ( var))
            sys.exit( 255)
        else:
            print( "%s: %s" % ( var, value))
    return argout

def executeListOfMacros():

    listOfMacros = [
        ['relmac', 'IVPmacro'],
        ['senv', 'ScanFile', '["tst.fio"]'],
        ['IVPmacro', 'all'],
        ]

    print( "\n>>> executing a list of macros")

    for cmd in listOfMacros:
        print( "%s" % (str( cmd)))
        doorProxy.RunMacro( cmd)
        attrOutput = []
        attrInfo = []
        attrError = []
        time.sleep(0.05)
        while doorProxy.state() != PyTango.DevState.ON:
            time.sleep(0.05)
            lines = doorProxy.Info
            if not lines is None:
                if len( lines) > len( attrInfo):
                    for line in lines[len(attrInfo):]:
                        print( "%s" % line)
                    attrInfo = lines[:]
            lines = doorProxy.output
            if not lines is None:
                if len( lines) > len( attrOutput):
                    for line in lines[len(attrOutput):]:
                        print( "%s" % line)
                    attrOutput = lines[:]
            lines = doorProxy.Error
            if not lines is None:
                if len( lines) > len( attrError):
                    for line in lines[len(attrError):]:
                        print( "*** %s" % line)
                    attrError = lines[:]
            if doorProxy.state() == PyTango.DevState.ALARM:
                print( "*** Door in ALARM -> break")
                break
        time.sleep(1)

def main(): 

    from optparse import OptionParser

    if os.getenv( 'USER') != 'kracht': 
        print( "SardanaIVP: wrong user name")
        sys.exit( 255) 

    usage = "%prog -x \n" + \
        "  executes the Sardana IVP procedure"

    parser = OptionParser(usage=usage)
    parser.add_option( "-x", action="store_true", dest="execute", 
                       default = False, help="execute")
    parser.add_option( "-f", action="store_true", dest="fast", 
                       default = False, help="fast mode, no AIO")
    
    (options, args) = parser.parse_args()
    
    if not options.execute and not options.fast:
        parser.print_help()
        sys.exit(255)

    checkComponents()

    checkHasyUtils()

    pVersion = ''
    if sys.version_info.major  == 3: 
        pVersion = '3'
    
    if not options.fast: 
        if os.system( "SardanaAIO%s.py -x" % pVersion):
            print( "*** SardanaAIO.py failed")
            sys.exit(255)

        res = HasyUtils.getDeviceNameByAlias( "eh_neverstart")
        if res is not None: 
            print( "*** eh_neverstart exists")
            sys.exit(255)

    print( "launching SardanaMonitor") 
    if os.system( "SardanaMonitor%s.py &" % pVersion):
        print( "failed to launch the SardanaMonitor")
        sys.exit(255)  

    if not options.fast: 
        print( "launching SardanaMotorMonitor")
        if os.system( "SardanaMotorMonitor%s.py &" % pVersion):
            print( "failed to launch the SardanaMotorMonitor")
            sys.exit(255)
        time.sleep(3)

    print( "launching pyspMonitor")
    if os.system( "pyspMonitor%s.py &" % pVersion):
        print( "failed to launch the pyspMonitor")
        sys.exit(255)
    time.sleep(3)

    if not options.fast: 
        print( "launching SardanaInfoViewer")
        if os.system( "SardanaInfoViewer%s.py &" % pVersion):
            print( "failed to launch the SardanaInfoViewer")
            sys.exit(255)
        time.sleep(1)
    #
    # exit handler resets ScanDir and kills SardanaMonitor and MessageWindow
    #
    atexit.register( exitHandler)

    checkPoolMsDoorMg()
    #
    # check SardanaChMg
    #
    checkSardanaChMg()

    if not checkCertainVariables():
        print( "*** SardanaIVP terminates because certain env variables do not exit")
        sys.exit( 255)

    scanDirOld = HasyUtils.getEnv( 'ScanDir')
    HasyUtils.setEnv( 'ScanDir', '/home/kracht/Misc/IVP/temp')
    #
    # also executes IVPMacro
    #
    executeListOfMacros()

    print( "Launch TngGui.py ")
    sys.stdout.write( "prtc ")
    sys.stdout.flush()
    line = sys.stdin.readline()
    return 

if __name__ == "__main__":
    main()

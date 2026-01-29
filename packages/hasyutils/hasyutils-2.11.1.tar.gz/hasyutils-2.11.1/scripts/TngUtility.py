#!/usr/bin/env python
'''
TngUtility
    - operates servers: kill, start, restart 
    - displays server info, classes, devices, properties and attributes
    - handles SimulationMode, list, sim-on, sim-off
    - creates /online_dir/TangoDump.lis with all attributes and properties

  IVP:
    TngUtility.py --list 
    TngUtility.py --list dgg mca
    TngUtility.py --list dgg mca --prop 
    TngUtility.py --list dgg mca --prop base
    TngUtility.py --list dgg --attr
    TngUtility.py --list dgg --attr --dev 01
    TngUtility.py --list dgg --attr sampl --dev 01
    TngUtility.py --restart dgg mca
    TngUtility.py --restart dgg mca --force
    TngUtility.py --simlist dgg mca 
    TngUtility.py --simon dgg mca 

'''
import sys, time, os, signal, time, json
import argparse
import HasyUtils
import PyTango

args = None
fileDumpLis = "/online_dir/TangoDump.lis"
fileSrvDevPy = "/online_dir/TangoSrvDev.py"
fileDumpPy = "/online_dir/TangoDump.py"
DBHOSTS = '/afs/desy.de/group/hasylab/Tango/HostLists/dbHosts.lis'

EXPERT_USERS = [ 'mfleck', 'blume', 'tnunez', 
                 'medved', 'kracht', 'jkotan', 'pithanli']

def pairs( lst):
    a = iter(lst)
    return list( zip(a, a))

class dbTMO( Exception):
    '''
    this class is raised by the time-out handler
    '''
    def __init__( self, *argin):
        self.value = argin
    def __str__( self): 
        return repr( self.value)

def handlerALRM( signum, frame):
    print( "handlerALRM: called with %d" % signum)
    raise dbTMO( "db-connect time-out")

class TngUtility():
    '''
    Tasks:
      - list servers and their status, devices, attribute, properties
      - kill, start, restart a list of servers

    Servers are identified by a prefix, e.g. 'DGG' matches 'DGG2/PETRA-3'
    '''
    def __init__( self, dbHost):
        '''
        dbHost: TANGO_HOST to connect to
        '''
        self.fileOutLis = None
        self.fileOutPy = None
        self.dbHost = dbHost
        self.db = None
        self.flagIsATty = os.isatty( 1)
        signal.signal( signal.SIGALRM, handlerALRM)
        signal.alarm(2)
        try:
            sys.stdout.write( "--- Connecting to TangoDB on %s:10000" % dbHost)
            sys.stdout.flush()
            self.db = PyTango.Database( self.dbHost, 10000)
        except dbTMO as e:
            print( "\n*** Caught %s" % repr( e.value))
            return 
        except Exception as e: 
            sys.stderr.write( "\n Failed to connect to TangoDB on %s:10000\n" % self.dbHost)
            sys.stderr.write( "%s\n" % str( e))            
            signal.alarm(0)
            return 
        signal.alarm(0)
        sys.stdout.write( ", OK\n")
        sys.stdout.flush()

    def writeOutputLis( self, msg):
        '''
        write msg to TangoDump.lis and possibly to stdout
        '''
        if self.fileOutLis is None:
            print( "%s" % msg)
        else:
            if self.flagIsATty:
                print( "%s" % msg)
            self.fileOutLis.write( "%s\n" % msg)

    def writeOutputPy( self, msg):
        '''
        write msg to TangoDump.py and possibly to stdout
        '''
        if not self.fileOutPy is None:
            self.fileOutPy.write( "%s\n" % msg)

    def pairs( self, lst):
        a = iter(lst)
        return list( zip(a, a))

    def getStartStopTime( self, serverName):
        '''
        returns the start/stop time of a server
        '''
        lstDeviceClass = self.db.get_device_class_list( serverName).value_string
        dInfo  = self.db.get_device_info( lstDeviceClass[0])
        argout = "no time"
        if dInfo.exported == 1:
            argout = "since %s" % dInfo.started_date
        else:
            argout = "since %s" % dInfo.stopped_date
        return argout

    def serverControlledByStarter( self, serverName):
        '''
        return True, if the server is contolled by the Starter
        '''
        try:
            srvInfo = self.db.get_server_info( serverName)
        except:
            sys.stderr.write( "TngUtility.serverControlledByStarter: failed to get_server_info for %s\n" % serverName)
            sys.exit( 255)

        if len( srvInfo.host.strip()) == 0:
            return False

        return True

    def sendStartServers( self, serverNames):
        """
        tell the starter to start servers. The function does not wait for the servers to run
        """
        proxies = {}
        for serverName in serverNames:
            starterProxy = None
            if serverName not in proxies:
                starter = HasyUtils.getStarterDevice( serverName, "%s:10000" % (self.dbHost))
                if starter is None: 
                    print( "TngUtility: %s not controlled by starter" % serverName)
                    continue
                try:
                    starterProxy = PyTango.DeviceProxy( starter)
                except:
                    sys.stderr.write( "TngUtility.sendStartServer: failed to create proxy to starter\n", serverName, starter)
                    sys.exit( 255)
                proxies[ serverName] = starterProxy
            else:
                starterProxy = proxies[ serverName]

            lst = starterProxy.command_inout("DevGetRunningServers", True)
            print( "sendStartServers to %s on %s" % ( serverName, starterProxy.name()))
            if not serverName in lst: 
                starterProxy.DevStart( serverName)
        return True

    def sendStopServers( self, serverNames):
        """
        tell the starter to stop servers. The function does not wait for the servers to stop
        """
        proxies = {}
        for serverName in serverNames:
            starterProxy = None
            if serverName not in proxies:
                starter = HasyUtils.getStarterDevice( serverName, "%s:10000" % (self.dbHost))
                if starter is None: 
                    print( "TngUtility: %s not controlled by starter" % serverName)
                    continue
                try:
                    starterProxy = PyTango.DeviceProxy( starter)
                except:
                    sys.stderr.write( "TngUtility.sendStopServers: failed to create proxy to starter %s, %s %s on %s\n" % 
                                      (starter, serverName, starter, self.dbHost))
                    sys.exit( 255)
                proxies[ serverName] = starterProxy
            else:
                starterProxy = proxies[ serverName]

            lst = starterProxy.command_inout("DevGetStopServers", True)
            print( "sendStopServers to %s on %s" % ( serverName, starterProxy.name()))
            if not serverName in lst: 
                starterProxy.DevStop( serverName)
        return True

    def waitStopServers( self, serverNames):
        """
        wait for the servers to appear in the DevGetStopServers list after they received a stop command
        """
        proxies = {}
        for serverName in serverNames:
            starterProxy = None
            if serverName not in proxies:
                starter = HasyUtils.getStarterDevice( serverName, "%s:10000" % (self.dbHost))
                if starter is None: 
                    print( "TngUtility: %s not controlled by starter" % serverName)
                    continue
                try:
                    starterProxy = PyTango.DeviceProxy( starter)
                except:
                    sys.stderr.write( "TngUtility.waitStopServer: failed to create proxy to starter\n", serverName, starter)
                    sys.exit( 255)
                proxies[ serverName] = starterProxy
            else:
                starterProxy = proxies[ serverName]

            sys.stdout.write( "Stopping %s " % serverName)
            sys.stdout.flush()
            waitTime = 5
            while waitTime > 0:
                time.sleep(0.5)
                waitTime -= 0.5
                starterProxy.command_inout("UpdateServersInfo")
                lst = starterProxy.command_inout("DevGetStopServers", True)
                if serverName in lst:
                    print( " OK")
                    break
                sys.stdout.write( '.')
                sys.stdout.flush()
            else:
                print( "TngUtility.waitStopServer: %s did not stop" % serverName)
                return False

        time.sleep(2.)
        return True

    def waitStartServers( self, serverNames):
        """
        wait for the servers to appear in the DevGetRunningServers list after they received a start command
        """
        proxies = {}
        for serverName in serverNames:
            if serverName not in proxies:
                starter = HasyUtils.getStarterDevice( serverName, "%s:10000" % (self.dbHost))
                if starter is None: 
                    print( "TngUtility: %s not controlled by starter" % serverName)
                    continue
                try:
                    starterProxy = PyTango.DeviceProxy( starter)
                except:
                    sys.stderr.write( "TngUtility.waitStartServer: failed to create proxy to starter\n", serverName, starter)
                    sys.exit( 255)
                proxies[serverName] = starterProxy
            else:
                starterProxy = proxies[serverName]
    
            sys.stdout.write( "Starting %s " % serverName)
            sys.stdout.flush()
            waitTime = 10
            while waitTime > 0:
                time.sleep(0.5)
                waitTime -= 0.5
                starterProxy.command_inout("UpdateServersInfo")
                lst = starterProxy.command_inout("DevGetRunningServers", True)
                if serverName in lst:
                    print( " OK")
                    break
                sys.stdout.write( '.')
                sys.stdout.flush()
            else:
                print( "TngUtility.waitStartServer: %s did not start" % serverName)
                return False
    
        return True

    def argSupplied( self, arg):
        '''
        for optional arguments that may have a parameter. 
        return True, if the optional arguments was supplied, with or 
        without a parameter, e.g. '--dev' or '--dev exp.01' --> true
        '''

        if arg is None:
            return True
        elif arg.find( 'Missing') == 0:
            return False
        else:
            return True

            
    def getSelectedServers( self, names):
        '''
        returns a list of server that match names.
        Server has to be controlled by the starter.
        If names is empty, all servers are returned
        '''
        try:
            lstServer = self.db.get_server_list().value_string
        except: 
            print( "TngUtility.getSelectedServers: get_server_list() failed")
            return []
        selected = []
        for server in lstServer:
            #
            # some of the eigers are not controlled, still I want to see them
            #
            #if not self.serverControlledByStarter( server):
            #    continue
            if len( names) == 0:
                selected.append( server)
                continue
            for name in names:
                if HasyUtils.match( server, name):
                    #
                    # fix for the 'tu --list mdgg dgg' where 'dgg' machtes
                    # DGG2 and MDGG8 which is already in the list because
                    # it matches 'mdgg'
                    #
                    if not server in selected:
                        selected.append( server)
        return selected

    def green( self, msg):
        argout = ""
        if self.flagIsATty and self.fileOutLis is None:
            argout = "\033[32m%s\033[0m" % msg
        else:
            argout = msg
        return argout

    def red( self, msg):
        argout = ""
        if self.flagIsATty and self.fileOutLis is None:
            argout = "\033[31m%s\033[0m" % msg
        else:
            argout = msg
        return argout

    def blue( self, msg):
        argout = ""
        if self.flagIsATty and self.fileOutLis is None:
            argout = "\033[34m%s\033[0m" % msg
        else:
            argout = msg
        return argout

    def displayMG( self, dev, deviceBufferLocal):
        '''
        displays information of a MG
        '''
        alias = None
        try:
            alias = self.db.get_alias( dev)
        except:
            return
        if not alias is None:
            if not HasyUtils.match( alias, args.mgPattern):
                return
        deviceBufferLocal.append( "    %s (%s)" % (dev, alias))
        name = "//%s:10000/%s" % (self.dbHost, dev)
        try:
            p = PyTango.DeviceProxy( name)
        except: 
            deviceBufferLocal.append( "TngUtility.displayMG: cannot connect to %s" % name)
            return
        for attr in ['ElementList', 'IntegrationTime']:
            val = str(p.read_attribute( attr).value)
            if len( val) > 500: 
                l = len( val)
                val = "truncated, total length %d, %s ..." % (l, repr( val[:200]))
            deviceBufferLocal.append( "        %-15s: %s" % (attr, repr( val)))
# ---
#{
#  u'controllers': 
#    {
#      u'haso107d1:10000/controller/dgg2ctrl/dgg2_d1_01': 
#        {
#          u'units': 
#            {
#              u'0': 
#                {
#                  u'channels': 
#                    {
#                      u'haso107d1:10000/expchan/dgg2_d1_01/1': 
#                        {
#                           u'conditioning': u'',
#                           u'enabled': True,
#                           u'full_name': u'haso107d1:10000/expchan/dgg2_d1_01/1',
#                           u'index': 0,
#                           u'instrument': u'',
#                           u'label': u'd1_t01',
#                           u'name': u'd1_t01',
#                           u'ndim': 0,
#                           u'normalization': 0,
#                           u'output': True,
#                           u'plot_axes': [],
#                           u'plot_type': 0,
#                           u'source': u'haso107d1:10000/expchan/dgg2_d1_01/1/Value',
#                        },
#                    },
#                   u'id': 0,
#                   u'monitor': u'haso107d1:10000/expchan/dgg2_d1_01/1',
#                   u'timer': u'haso107d1:10000/expchan/dgg2_d1_01/1',
#                   u'trigger_type': 0,
#                },
#            },
#        },
#      u'haso107d1:10000/controller/sis3820ctrl/sis3820_d1': 
#        {
#          u'units': 
#            {
#              u'0': 
#                {
#                  u'channels': 
#                    {
#                      u'haso107d1:10000/expchan/sis3820_d1/1': 
#                        {
#                           u'conditioning': u'',
#                           u'enabled': True,
#                           u'full_name': u'haso107d1:10000/expchan/sis3820_d1/1',
#                           u'index': 1,
#                           u'instrument': u'',
#                           u'label': u'd1_c01',
#                           u'name': u'd1_c01',
#                           u'ndim': 0,
#                           u'normalization': 0,
#                           u'output': True,
#                           u'plot_axes': [u'<mov>'],
#                           u'plot_type': 1,
#                           u'source': u'haso107d1:10000/expchan/sis3820_d1/1/Value',
#                        },
#                    },
#                   u'id': 0,
#                   u'monitor': u'haso107d1:10000/expchan/sis3820_d1/1',
#                   u'timer': u'haso107d1:10000/expchan/sis3820_d1/1',
#                   u'trigger_type': 0,
#                },
#            },
#        },
#      u'haso107d1:10000/controller/sis3820ctrl/vc_rndm': 
#        {
#          u'units': 
#            {
#              u'0': 
#                {
#                  u'channels': 
#                    {
#                      u'haso107d1:10000/expchan/vc_rndm/1': 
#                        {
#                           u'conditioning': u'',
#                           u'enabled': True,
#                           u'full_name': u'haso107d1:10000/expchan/vc_rndm/1',
#                           u'index': 2,
#                           u'instrument': u'',
#                           u'label': u'rndm',
#                           u'name': u'rndm',
#                           u'ndim': 0,
#                           u'normalization': 0,
#                           u'output': True,
#                           u'plot_axes': [u'<mov>'],
#                           u'plot_type': 1,
#                           u'source': u'haso107d1:10000/expchan/vc_rndm/1/Value',
#                        },
#                    },
#                   u'id': 0,
#                   u'monitor': u'haso107d1:10000/expchan/vc_rndm/1',
#                   u'timer': u'haso107d1:10000/expchan/vc_rndm/1',
#                   u'trigger_type': 0,
#                },
#            },
#        },
#      u'haso107d1:10000/controller/sis3820ctrl/vc_sig_gen': 
#        {
#          u'units': 
#            {
#              u'0': 
#                {
#                  u'channels': 
#                    {
#                      u'haso107d1:10000/expchan/vc_sig_gen/1': 
#                        {
#                           u'conditioning': u'',
#                           u'enabled': True,
#                           u'full_name': u'haso107d1:10000/expchan/vc_sig_gen/1',
#                           u'index': 3,
#                           u'instrument': u'',
#                           u'label': u'sig_gen',
#                           u'name': u'sig_gen',
#                           u'ndim': 0,
#                           u'normalization': 0,
#                           u'output': True,
#                           u'plot_axes': [u'<mov>'],
#                           u'plot_type': 1,
#                           u'source': u'haso107d1:10000/expchan/vc_sig_gen/1/Value',
#                        },
#                    },
#                   u'id': 0,
#                   u'monitor': u'haso107d1:10000/expchan/vc_sig_gen/1',
#                   u'timer': u'haso107d1:10000/expchan/vc_sig_gen/1',
#                   u'trigger_type': 0,
#                },
#            },
#        },
#      u'haso107d1:10000/controller/vfcadcctrl/vfcadc_d1': 
#        {
#          u'units': 
#            {
#              u'0': 
#                {
#                  u'channels': 
#                    {
#                      u'haso107d1:10000/expchan/vfcadc_d1/1': 
#                        {
#                           u'conditioning': u'',
#                           u'enabled': True,
#                           u'full_name': u'haso107d1:10000/expchan/vfcadc_d1/1',
#                           u'index': 4,
#                           u'instrument': u'',
#                           u'label': u'd1_vfc01',
#                           u'name': u'd1_vfc01',
#                           u'ndim': 0,
#                           u'normalization': 0,
#                           u'output': True,
#                           u'plot_axes': [u'<mov>'],
#                           u'plot_type': 1,
#                           u'source': u'haso107d1:10000/expchan/vfcadc_d1/1/Value',
#                        },
#                    },
#                   u'id': 0,
#                   u'monitor': u'haso107d1:10000/expchan/vfcadc_d1/1',
#                   u'timer': u'haso107d1:10000/expchan/vfcadc_d1/1',
#                   u'trigger_type': 0,
#                },
#            },
#        },
#    },
#   u'description': u'General purpose measurement group',
#   u'label': u'mg_tk',
#   u'monitor': u'haso107d1:10000/expchan/dgg2_d1_01/1',
#   u'timer': u'haso107d1:10000/expchan/dgg2_d1_01/1',
#}

# ---

        hsh = json.loads( p.Configuration) 
        # +++
        # HasyUtils.dct_print( hsh)
        deviceBufferLocal.append( "        Configuration")
        for k,v in list(hsh.items()):
            if k == 'controllers':
                deviceBufferLocal.append( "            controllers")
                for ctrlName, ctrlValue in list(hsh['controllers'].items()):
                    deviceBufferLocal.append( "                %s" % (ctrlName))
                    if 'units' in ctrlValue:
                        for k0, val0 in list(ctrlValue['units']['0'].items()):
                            if k0 == 'channels':
                                for chan, chanVal in val0.items():
                                    deviceBufferLocal.append( "                    channel: %s" % (chan))
                                    if not args.full:
                                        continue
                                    for k1, val1 in list(chanVal.items()):
                                        deviceBufferLocal.append( "                        %s: %s" % (k1, val1))
                                 
                            else:
                                deviceBufferLocal.append( "                    %s: %s" % (k0, val0))
                    else:  # new sardana 
                        for k0, val0 in list(ctrlValue.items()):
                            if k0 == 'channels':
                                for chan, chanVal in list(val0.items()):
                                    deviceBufferLocal.append( "                    channel: %s" % (chan))
                                    if not args.full:
                                        continue
                                    for k1, val1 in list( chanVal.items()):
                                        deviceBufferLocal.append( "                        %s: %s" % (k1, val1))
                                 
                            else:
                                deviceBufferLocal.append( "                    %s: %s" % (k0, val0))
            else:
                deviceBufferLocal.append( "            %s: %s" % (k, v))
        
    def listServer( self, names):
        '''
        list servers, optionally including class, devices, properties and attributes
        '''
        simulated = []
        simulatedPartly = []
        #                    
        #  loop over the servers
        #                    
        for serverName in self.getSelectedServers( names): 
            # 25.7.2023: find out how many MacroServer are running
            #if serverName.find( 'TangoTest') == 0 or \
            #   #serverName[0:4] == 'Pool' or \
            #   #serverName[0:11] == 'MacroServer': 
            #   serverName[0:10] == 'DataBaseds':
            #    continue
            #print( "+++TngUtility: server %s " % serverName)
            #
            # display the server name, state, starter host and start/stop time
            #
            serverBuffer = []
            flagRunning = False
            starter = HasyUtils.getStarterDevice( serverName, "%s:10000" % (self.dbHost))
            if starter is None: 
                serverBuffer.append( "%-30s %s" % (serverName, self.blue( 'not controlled')))
            else: 
                lst = starter.split( '/')
                if HasyUtils.serverIsRunning( serverName, "%s:10000" % (self.dbHost)):
                    serverBuffer.append( "%-30s %s on %s %s" % (serverName, self.green( 'running'), 
                                                                lst[-1], self.getStartStopTime( serverName)))
                    flagRunning = True
                elif HasyUtils.serverIsStopped( serverName, "%s:10000" % (self.dbHost)):
                    serverBuffer.append( "%-30s %s on %s %s" % (serverName, self.red( 'stopped'), 
                                                                lst[-1], self.getStartStopTime( serverName)) )
                else:
                    serverBuffer.append( "%-30s %s" % (serverName, self.blue( 'unknown'))  )
            lstDeviceClass = self.db.get_device_class_list( serverName).value_string
            clsOld = "None"
            simuOn = 0
            simuOff = 0
            #
            # loop over the devices
            #
            deviceBufferLis = []
            deviceBufferPy = []
            for dev,cls in self.pairs( lstDeviceClass):
                if cls == 'DServer': 
                    continue
                #print( "+++TngUtility: device %s " % dev)
                #
                # if --stateFAULT is supplied
                #
                if flagRunning and args.stateFAULT:
                    name = "//%s:10000/%s" % (self.dbHost, dev)
                    try:
                        p = PyTango.DeviceProxy( name)
                    except: 
                        deviceBufferLis.append( "TngUtility.listServer: cannot connect to %s" % name)
                        continue
                    try:
                        if p.read_attribute( 'State').value == PyTango.DevState.FAULT:
                            deviceBufferLis.append( "  Class: %s" % cls)
                            deviceBufferLis.append( "    %s" %dev)
                            deviceBufferLis.append( "      State: FAULT")
                            deviceBufferLis.append( "      Status: %s" % p.read_attribute( 'Status').value)
                            continue
                    except:
                        deviceBufferLis.append( "      Failed to get proxy.state() for %s" % name)
                        continue
                    continue
                #
                # if --stateALARM is supplied
                #
                if flagRunning and args.stateALARM:
                    name = "//%s:10000/%s" % (self.dbHost, dev)
                    try:
                        p = PyTango.DeviceProxy( name)
                    except: 
                        deviceBufferLis.append( "TngUtility.listServer: cannot connect to %s" % name)
                        continue
                    try:
                        if p.read_attribute( 'State').value == PyTango.DevState.ALARM:
                            deviceBufferLis.append( "  Class: %s" % cls)
                            deviceBufferLis.append( "    %s" %dev)
                            deviceBufferLis.append( "      State: ALARM")
                            deviceBufferLis.append( "      Status: %s" % p.read_attribute( 'Status').value)
                            continue
                    except:
                        deviceBufferLis.append( "      Failed to get proxy.state() for %s" % name)
                        continue
                    continue
                #
                # if --dev is supplied, make the match
                #
                if self.argSupplied( args.devPattern) and not HasyUtils.match( dev, args.devPattern):
                    continue
                #
                # if --alias is supplied, make the match
                #
                if self.argSupplied( args.aliasPattern):
                    alias = None
                    try:
                        alias = self.db.get_alias( dev)
                    except:
                        continue
                    if not alias is None:
                         if not HasyUtils.match( alias, args.aliasPattern):
                             continue
                #
                # if --class is supplied, make the match
                #
                if self.argSupplied( args.classPattern) and not HasyUtils.match( cls, args.classPattern):
                    continue
                #
                # don't show the class for every device, display 
                # only, if the class name changes
                #
                if cls != clsOld:
                    if self.argSupplied( args.classPattern) or \
                       self.argSupplied( args.devPattern) or \
                       self.argSupplied( args.aliasPattern) or \
                       self.argSupplied( args.attrPattern) or \
                       self.argSupplied( args.propPattern):
                        deviceBufferLis.append( "  Class: %s" % cls)
                        deviceBufferPy.append( "#\n#  Class: %s" % cls)
                    clsOld = cls
                #
                # if --mg is supplied, no attrs or props will be displayed
                #
                if self.argSupplied( args.mgPattern):
                    if cls != 'MeasurementGroup':
                        continue                 
                    self.displayMG( dev, deviceBufferLis)
                    continue
                #
                # if --prop or --attr is supplied the device is displayed
                #
                if self.argSupplied( args.devPattern) or \
                   self.argSupplied( args.aliasPattern) or \
                   self.argSupplied( args.attrPattern) or \
                   self.argSupplied( args.mgPattern) or \
                   self.argSupplied( args.propPattern):
                    alias = None
                    try:
                        alias = self.db.get_alias( dev)
                    except: 
                        pass
                    if alias:
                        deviceBufferLis.append( "    %s (%s)" % (dev, alias))
                        deviceBufferPy.append( "#    %s (%s)" % (dev, alias))
                    else:
                        deviceBufferLis.append( "    %s" % (dev))
                        deviceBufferPy.append( "#    %s" % (dev))

                        
                devPropertyList = self.db.get_device_property_list( dev, "*")
                if 'SimulationMode' in devPropertyList.value_string:
                    devProperty = self.db.get_device_property( dev, 'SimulationMode')
                    if devProperty[ 'SimulationMode'][0] == '1':
                        simuOn += 1
                    else:
                        simuOff += 1
                #        
                # display the properties
                #        
                if self.argSupplied( args.propPattern):
                    #print( "+++TngUtility: properties of %s " % dev)
                    deviceBufferLis.append( "      Properties")
                    deviceBufferPy.append( "#      Properties")
                    for prp in devPropertyList.value_string:
                        devProperty = self.db.get_device_property( dev, prp)
                        if not HasyUtils.match( prp, args.propPattern):
                            continue
                        if not hasattr( devProperty[prp], '__iter__'): # kommt nicht vor
                            deviceBufferLis.append( "        %-15s: %s" % (prp, devProperty[prp]))
                            deviceBufferPy.append( "db.put_device_property( '%s', {'%s': '%s'})" % (dev, prp, str(devProperty[prp]))) 
                        elif len( devProperty[prp]) == 1:
                            deviceBufferLis.append( "        %-15s: %s" % (prp, devProperty[prp][0]))
                            deviceBufferPy.append( "db.put_device_property( '%s', {'%s': '%s'})" % (dev, prp, str(devProperty[prp][0]))) 
                        else:
                            deviceBufferLis.append( "        %-15s: ['%s'," % (prp, devProperty[prp][0]))
                            for i in range( 1, len(devProperty[prp]) - 1):
                                deviceBufferLis.append( "                          '%s'," % (devProperty[prp][i]))
                            deviceBufferLis.append( "                          '%s']" % (devProperty[prp][len(devProperty[prp]) - 1]))

                            deviceBufferPy.append( "db.put_device_property( '%s', {'%s': %s})" % (dev, prp, str(devProperty[prp]))) 
                                
                #        
                # display the attributes
                #        
                if self.argSupplied( args.attrPattern):
                    if not flagRunning:
                        deviceBufferLis.append( "      Server not running")
                        continue
                    #print( "+++TngUtility: attributes of %s " % dev)
                        
                    name = "//%s:10000/%s" % (self.dbHost, dev)
                    try:
                        p = PyTango.DeviceProxy( name)
                    except: 
                        deviceBufferLis.append( "TngUtility.listServer: cannot connect to %s" % name)
                        continue
                    try:
                        if p.read_attribute( 'State').value == PyTango.DevState.ALARM:
                            deviceBufferLis.append( "      State: ALARM")
                            deviceBufferLis.append( "      Status: %s" % repr( p.read_attribute( 'Status').value))
                            continue
                    except:
                        deviceBufferLis.append( "      Failed to get proxy.state() for %s" % name)
                        continue
                    try:
                        if p.read_attribute( 'State').value == PyTango.DevState.FAULT:
                            deviceBufferLis.append( "      State: FAULT")
                            deviceBufferLis.append( "      Status: %s" % repr( p.read_attribute( 'Status').value))
                            continue
                    except:
                        deviceBufferLis.append( "      Failed to get proxy.state() for %s" % name)
                        continue
                    
                    #
                    # if '--attr black_box' is supplied no other attributes are looked at
                    #
                    if args.attrPattern is not None and HasyUtils.match( 'black_box', args.attrPattern):
                        lst = p.black_box( 40)
                        deviceBufferLis.append( "      Black_box")
                        for line in lst: 
                            deviceBufferLis.append( "        %s" % line)
                        continue

                    lst = p.get_attribute_list()
                    deviceBufferLis.append( "      Attributes")
                    deviceBufferPy.append( "#")
                    deviceBufferPy.append( "#      Attributes")
                    deviceBufferPy.append( "proxy = PyTango.DeviceProxy( '%s')"  % (dev))
                    for attr in lst:
                        if not HasyUtils.match( attr, args.attrPattern):
                            continue
                        #print( "+++TngUtility: attribute %s " % attr)
                        #
                        # 'RecentWrites' is the Oms debugging feature
                        #
                        if attr.find( 'RecentWrites') == 0:
                            deviceBufferLis.append( "        %-15s: ignored" % (attr))
                            deviceBufferPy.append( "# ignored %s"  % (attr))
                            continue
                        try:
                            attrInfo = p.get_attribute_config( attr)
                            val = p.read_attribute( attr).value
                            valStr = str(val)
                            if len( valStr) > 80: 
                                l = len( valStr)
                                valStr = "truncated, total length %d, %s ..." % (l, repr( valStr[:800]))
                            deviceBufferLis.append( "        %-15s: %s" % (attr, repr( valStr)))
                            if attrInfo.writable == PyTango._PyTango.AttrWriteType.READ_WRITE:
                                if attrInfo.data_format == PyTango._tango.AttrDataFormat.SCALAR: 
                                    if( attr.lower() == 'position'):
                                        deviceBufferPy.append( "# position attribute: %s: %s"  % (attr, repr(val)))
                                    elif( attr.lower() in ['environment', 'configuration', 'selection',
                                                           'profileconfiguration', 'xmlstring', 'image', 'flaguseencoderposition', 
                                                           'flagclosedloop', 'flagencoderhomed']):
                                        deviceBufferPy.append( "# %s: ignored" % attr)
                                    else:
                                        if (attrInfo.data_type == PyTango._PyTango.CmdArgType.DevDouble) or \
                                           (attrInfo.data_type == PyTango._PyTango.CmdArgType.DevFloat):
                                            deviceBufferPy.append( "proxy.write_attribute( '%s', %g) "  % (attr, val))
                                        elif (attrInfo.data_type == PyTango._PyTango.CmdArgType.DevLong) or \
                                             (attrInfo.data_type == PyTango._PyTango.CmdArgType.DevShort) or \
                                             (attrInfo.data_type == PyTango._PyTango.CmdArgType.DevBoolean):
                                            deviceBufferPy.append( "proxy.write_attribute( '%s', %s) "  % (attr, repr(val)))
                                        elif type( val) is dict:
                                            deviceBufferPy.append( "proxy.write_attribute( '%s', %s) "  % (attr, str(val)))
                                        elif type( val) is list:
                                            deviceBufferPy.append( "proxy.write_attribute( '%s', %s) "  % (attr, str(val)))
                                        else:
                                            deviceBufferPy.append( "proxy.write_attribute( '%s', '%s') "  % (attr, str(val)))
                                else:
                                    deviceBufferPy.append( "# %s format %s: %s"  % (attr, repr( attrInfo.data_format), valStr))
                            else:
                                deviceBufferPy.append( "# read-only attribute: %s: %s"  % (attr, valStr))
                        except PyTango.DevFailed as e:
                            deviceBufferLis.append( "        %-15s: DevFailed" % (attr))
                            for arg in e.args: 
                                deviceBufferLis.append( "          Desc: %s" % (str( arg.desc.strip())))
                                #deviceBufferLis.append( "origin: %s" % (arg.origin))
                                #deviceBufferLis.append( "reason: %s" % (arg.reason))
                                #deviceBufferLis.append( "severity: %s" % (arg.severity))
                            #PyTango.Except.print_exception( e)          
                            #+++deviceBufferLis.append( "        %-15s: error, terminated reading this device" % (attr))
                            deviceBufferLis.append( "        %-15s: error" % (attr))
                            #  break
                        except Exception as e: 
                            deviceBufferLis.append( sys.exc_info()[0])
                            deviceBufferLis.append( e)
                            #+++deviceBufferLis.append( "        %-15s: error, terminated reading this device" % (attr))
                            deviceBufferLis.append( "        %-15s: error" % (attr))
                            break

            if simuOn != 0 and simuOff == 0:
                simulated.append( serverName)
            elif simuOn != 0 and simuOff != 0:
                simulatedPartly.append( serverName)


            #
            # print server details only, if --dev produced some output
            #
            if len( deviceBufferLis) > 0:
                [ self.writeOutputLis( msg) for msg in serverBuffer]
                [ self.writeOutputLis( msg) for msg in deviceBufferLis]
                [ self.writeOutputPy( msg) for msg in deviceBufferPy]
            #
            # or if --dev, --class, --alias, --attr or --prop have not been supplied
            #
            elif( not self.argSupplied( args.devPattern) and 
                  not self.argSupplied( args.classPattern) and 
                  not self.argSupplied( args.aliasPattern) and 
                  not self.argSupplied( args.attrPattern) and 
                  not self.argSupplied( args.propPattern)):
                [ self.writeOutputLis( msg) for msg in serverBuffer]
                
        if len( simulated) > 0: 
            self.writeOutputLis( "%s" % self.red( "Simulated: %s" % str(simulated)))
        if len( simulatedPartly) > 0: 
            self.writeOutputLis( "%s" % self.red( "Partly simulated: %s" % str(simulatedPartly)))


    def simServer( self, names, flag):
        '''
        enable/disable the SimulationMode: flag: 1: on, 0: off, 2: list
        '''
        #                    
        #  loop over the servers
        #                    
        for serverName in self.getSelectedServers( names): 
            if serverName.find( 'TangoTest') == 0 or \
               serverName.find( 'DataBaseds') == 0 or \
               serverName.find( 'Starter') == 0 or \
               serverName.find( 'TangoAccess') == 0:
                continue
            starter = HasyUtils.getStarterDevice( serverName, "%s:10000" % (self.dbHost))
            #
            # e.g.: VmExecutor/NeverStar
            #
            if starter is None: 
                print( "TngUtility: failed to getStarterDevice for %s" % serverName)
                continue
            lst = starter.split( '/')
            if HasyUtils.serverIsRunning( serverName, "%s:10000" % (self.dbHost)):
                print( "%-30s %s on %s" % (serverName, self.green( 'running'), lst[-1]) )
            elif HasyUtils.serverIsStopped( serverName, "%s:10000" % (self.dbHost)):
                print( "%-30s %s on %s" % (serverName, self.red( 'stopped'), lst[-1]))
            else:
                print( "%-30s %s" % (serverName, self.blue( 'unknown')))
            #
            # loop over the devices
            #
            # In [3]: db.get_device_class_list( 'DGG2/PETRA-3')
            # Out[3]: DbDatum(name = 'server', value_string = 
            #          ['dserver/DGG2/PETRA-3', 'DServer', 'p09/dgg2/d1.01', 'DGG2', 'p09/dgg2/d1.02', 'DGG2'])
            #
            lstDeviceClass = self.db.get_device_class_list( serverName).value_string
            for dev,cls in self.pairs( lstDeviceClass):
                if cls == 'DServer': 
                    continue
                devPropertyList = self.db.get_device_property_list( dev, "*")
                if 'SimulationMode' in devPropertyList.value_string:
                    devProperty = self.db.get_device_property( dev, 'SimulationMode')
                    if flag == 1:
                        self.db.put_device_property( dev, {'SimulationMode': ['1']})
                        print( "  %s SimuationMode: -> 1" % (dev))
                    elif flag == 0:
                        self.db.put_device_property( dev, {'SimulationMode': ['0']})
                        print( "  %s SimuationMode: -> 0" % (dev))
                    else:
                        print( "  %s SimuationMode: %s" % (dev, devProperty[ 'SimulationMode'][0]))

    def checkTangoHost( self):
        """
        make sure that hostname and TANGO_HOST are compliant:
           - return True, if dbHost does not begin with 'haspp'
           - haspp08 and haspp08mono return True
           - haspp08 and haspp09     return False
        """
        hostname = HasyUtils.getHostname()
        dbHost = self.dbHost

        if dbHost.find( 'haspp') == 0:
            if dbHost[:7] == hostname[:7]:
                return True
            else:
                return False
        return True

    def killServer( self, namePatterns):
        '''
        kill a list of servers
        '''
        if namePatterns == []:
            print( "killServer: selection patters is empty")
            return 

        if self.checkTangoHost() is False:
            print( "killServer: hostname (%s) inconsistent with dbHost (%s)" % \
                (HasyUtils.getHostname(), self.dbHost))
            return False

        selected = self.getSelectedServers( namePatterns)

        if len( selected) == 0:
            print( "Nothing selected, aborting")
            return

        print( "")
        for serverName in selected: print( "  %s" % serverName )

        if not args.force and not HasyUtils.yesno( "\nKill these servers [n] "):
            print( "Aborted")
            return

        if not self.sendStopServers( selected):
            return False

        if not self.waitStopServers( selected):
            return False

        return True

    def restartServer( self, namePatterns):
        '''
        restart servers, start is executed in reverted order
        '''
        if namePatterns == []:
            print( "restartServer: selection patters is empty")
            return 


        if self.checkTangoHost() is False:
            print( "restartServer: hostname (%s) inconsistent with dbHost (%s)" % \
                (HasyUtils.getHostname(), self.dbHost))
            return False

        selected = self.getSelectedServers( namePatterns)

        if len( selected) == 0:
            print( "Nothing selected, aborting")
            return

        print( "")
        for serverName in selected: print( "  %s" % serverName )

        if not args.force and not HasyUtils.yesno( "\nRestart these servers [n] "):
            print( "Aborted")
            return

        if not self.sendStopServers( selected):
            return False

        if not self.waitStopServers( selected):
            return False
        #
        # reverting the order, think of Pool and MacroServer
        #
        selected.reverse()

        if not self.sendStartServers( selected):
            return False

        if not self.waitStartServers( selected):
            return False

    def startServer( self, namePatterns):
        '''
        start a list of servers
        '''
        if namePatterns == []:
            print( "startServer: selection patters is empty")
            return 


        if self.checkTangoHost() is False:
            print( "startServer: hostname (%s) inconsistent with dbHost (%s)" % \
                (HasyUtils.getHostname(), self.dbHost))
            return False

        selected = self.getSelectedServers( namePatterns)

        if len( selected) == 0:
            print( "Nothing selected, aborting")
            return

        print( "")
        for serverName in selected: print( "  %s" % serverName )

        if not args.force and not HasyUtils.yesno( "\nStart these servers [n] "):
            print( "Aborted")
            return

        if not self.sendStartServers( selected):
            return False

        if not self.waitStartServers( selected):
            return False

        return True

    def dump( self):
        '''
        create a new version on /online_dir/TangoDump.lis and ~.py
        including all attributes and properties of all devices
        '''
        global args

        if not os.path.isdir( '/online_dir'):
            print( "TngUtility.dump: /online_dir does not exist, aborting")
            sys.exit( 255)

        #
        # versioning of TangoDump.lis and TangoDump.py
        #
        for fname in [fileDumpLis, fileSrvDevPy, fileDumpPy]:
            if os.path.exists( fname):
                if not os.path.exists( '/usr/local/bin/vrsn'):
                    sys.stderr.write( "TngUtility.dump: /usr/local/bin/vrsn does not exist\n")
                    sys.exit( 255)
                print( "/usr/local/bin/vrsn -s -nolog %s" % fname)
                os.system( "/usr/local/bin/vrsn -s -nolog %s" % fname)

        #
        # prepare /online_dir/TangoDump.lis
        #
        try:
            self.fileOutLis = open( "%s" % fileDumpLis, "w")
        except Exception as e:
            print( "dump: failed to open %s" % fileDumpLis)
            sys.stderr.write( "%s\n" % str( e))            
            return 
        self.writeOutputLis( "Created: %s by TngUtility.py \n" % HasyUtils.getDateTime())
        #
        # prepare /online_dir/TangoDump.py
        #
        try:
            self.fileOutPy = open( "%s" % fileDumpPy, "w")
        except Exception as e:
            print( "dump: failed to open %s" % fileDumpPy)
            sys.stderr.write( "%s\n" % str( e))            
            return 
        #
        # prepare /online_dir/TangoSrvDev.py
        #
        try:
            self.fileOutSrvDevPy = open( "%s" % fileSrvDevPy, "w")
        except Exception as e:
            print( "dump: failed to open %s" % fileSrvDevPy)
            sys.stderr.write( "%s\n" % str( e))            
            return 
        self.fileOutSrvDevPy.write( "#!/usr/bin/env python3\n")
        self.fileOutSrvDevPy.write( "#\n")
        self.fileOutSrvDevPy.write( "# Created: %s by TngUtility.py \n" % HasyUtils.getDateTime())
        self.fileOutSrvDevPy.write( "#\n")
        self.fileOutSrvDevPy.write( "import PyTango\n")
        self.fileOutSrvDevPy.write( "dp = PyTango.Database()\n")
        #
        # servers and devices
        #
        for srv in self.db.get_server_list():
            #if srv[0:10] == 'DataBaseds':
            #    #srv[0:4] == 'Pool' or \
            #    #srv[0:11] == 'MacroServer': 
            #   
            #    continue
            self.fileOutSrvDevPy.write( "#\n# %s\n#\n" % srv)
            self.fileOutSrvDevPy.write( "devInfoList = []\n")
            srvInfo = self.db.get_server_info( srv)
        
            lstDeviceClass = self.db.get_device_class_list( srv).value_string

            for dev,cls in pairs( lstDeviceClass):
                self.fileOutSrvDevPy.write( "device_info = PyTango.DbDevInfo()\n") 
                self.fileOutSrvDevPy.write( "device_info.name = \"%s\"\n" % dev)
                self.fileOutSrvDevPy.write( "device_info.klass = \"%s\"\n" % cls)
                self.fileOutSrvDevPy.write( "device_info.server = \"%s\"\n" % srv)
                self.fileOutSrvDevPy.write( "device_info.server_id = 0\n")
                self.fileOutSrvDevPy.write( "devInfoList.append( device_info)\n")

            self.fileOutSrvDevPy.write( "db.add_server( \"%s\", devInfoList, with_dserver=True)\n" % srv)

            self.fileOutSrvDevPy.write( "serverInfo = PyTango.DbServerInfo()\n") 
            self.fileOutSrvDevPy.write( "serverInfo.name = \"%s\"\n" % srv)
            self.fileOutSrvDevPy.write( "serverInfo.host = \"%s\"\n" % srvInfo.host)
            self.fileOutSrvDevPy.write( "serverInfo.level = %d\n" % srvInfo.level)
            self.fileOutSrvDevPy.write( "serverInfo.mode = %d\n" % srvInfo.mode)
            self.fileOutSrvDevPy.write( "db.put_server_info( serverInfo)\n")
            #
            # the servers have to run to deal with the attributes
            #
            self.fileOutSrvDevPy.write( "HasyUtils.startServer( \"%s\")\n" % srv)
        self.fileOutSrvDevPy.close()

        self.writeOutputPy( "#!/usr/bin/env python")
        self.writeOutputPy( "#")
        self.writeOutputPy( "# Created: %s" % HasyUtils.getDateTime())
        self.writeOutputPy( "#")
        self.writeOutputPy( "# The 'import PyTango' statement has intentionally been commented out to")
        self.writeOutputPy( "# make this file not-executable. Before you execute this file or parts of it,")
        self.writeOutputPy( "# be sure that you know what you are doing. ")
        self.writeOutputPy( "#")
        self.writeOutputPy( "# import PyTango")
        self.writeOutputPy( "import HasyUtils")
        self.writeOutputPy( "db = PyTango.Database()")

        args.list = True
        args.attrPattern = None
        args.propPattern = None

        self.listServer( [])

        self.fileOutLis.close()
        self.fileOutLis = None
        self.fileOutPy.close()
        self.fileOutPy = None

        return
#
#
#
def print_examples():
    print( '''
Examples:
  TngUtility.py --start dgg sis tip
    start servers containing 'dgg', 'sis', or 'tip'
    Btw.: "tus" expands to "dgg2 mca omsvme58 sis tip vfc"

  TngUtility.py --list ^dgg --dev
    list the devices exported by servers beginning with 'dgg'

  TngUtility.py --list 
    list all servers including state and starter host, 
    simulated devices are reported.

  TngUtility.py --list omsv --prop base 
    list the base properties of the Oms devices

  TngUtility.py --simOn dgg sis tip omsv
    set the SimulationMode property of the selected servers to 1

  TngUtility.py --list ^omsvme58$ --prop --dev 71
    list the properties of the OmsVme58 server for those devices 
    including 71 in the device names.

  TngUtility --list  --dev --alias exp_mot01
    display only the device which has the alias exp_mot01

  TngUtility --list  --dev petra/globals/keyword --attr black_box
    display the black_box of petra/globals/keyword, 40 lines

  TngUtility.py --dump
    create a new version of /online_dir/TangoDump.lis

  TngUtility.py --dbhost haspp17 --list
    list the servers of hosts beginning with haspp17

  TngUtility.py --dbhost --list dgg2
    list the servers matching dgg2 from all DB-hosts

  TngUtility.py --list Pool --mg mg_name --full
    print information about a MeasurementGroup.

  TngUtility.py --list zmx --dbhost haspp10 --class ZMX --stateFAULT
    print the ZMX, class ZMX, devices that are in the FAULT state 
    ''')
#
#
#
def print_matching():
    print( '''
  TngUtility.py --list
    no pattern supplied, all server names match

  If a pattern is supplied, it is matched against names by re.search.
  A name represents a server, a class, a device, a property or an attribute.
  
  Examples: 
    TngUtility.py --list dgg
      matches DGG2, MDGG8

    TngUtility.py --list ^dgg
      matches DGG2

    TngUtility --list omsv --dev 01 --attr position
      matches StepPositionInternal, StepPositionController and many more
      (of Oms devices containing '01')

    TngUtility --list omsv --dev 01 --attr position$
      matches Position, HomePosition, FlagEncoderPosition

    TngUtility --list omsv --dev 01 --attr ^position$
      matches Position

    TngUtility --dbhost ^haspp09mono$ --list omsv --dev exp.01
      exact dbhost match
    ''')
#
#
#
def execIVP():
    comList = [
        'TngUtility.py --list',
        'TngUtility.py --list dgg',
        'TngUtility.py --list dgg --dev',
        'TngUtility.py --list dgg --prop',
        'TngUtility.py --list dgg --dev 01 --prop base',
        'TngUtility.py --list dgg --dbhost haspp08mono --attr sample',
        ]
    for com in comList:
        print( ">>> executing '%s'" % com)
        prc = os.popen( "%s 2>&1" % com)
        ret = prc.read()
        prc.close()
        if str( ret).lower().find( 'error') != -1 or str( ret).lower().find( 'usage') != -1:
            print( "'%s' produces an error" % com)
        print( ret)
#
# main
#
def main():
    parser = argparse.ArgumentParser( 
        formatter_class = argparse.RawDescriptionHelpFormatter,
        description="Tango Server Utility", 
        epilog='''\
Examples see:       TngUtility.py --examples
Matching rules see: TngUtility.py --matching

Example:
  TngUtility.py --list pilatus --dbhost haspp99 --prop
    Lists all properties of all servers containing pilatus on all hosts containing haspp99

    ''')
    parser.add_argument( 'pattern', nargs='*', help='server name pattern, case in-sensitive, can be "tus"')
    parser.add_argument( '--alias', dest="aliasPattern", nargs='?', default='Missing', help='restrict search with alias (with --list)')
    parser.add_argument( '--class', dest="classPattern", nargs='?', default='Missing', help='show classes (with --list)')
    parser.add_argument( '--attr', dest="attrPattern", nargs='?', default='Missing', help='show attributes (with --list), including black_box')
    parser.add_argument( '--dbhost', dest="dbHostPattern", nargs='?', default='Missing', help="the dbHost, default: local host")
    parser.add_argument( '--dev', dest="devPattern", nargs='?', default='Missing', help='show devices (with --list)')
    parser.add_argument( '--dump', dest="dump", action="store_true", help="create a new version of %s" % fileDumpLis)
    parser.add_argument( '--examples', dest="examples", action="store_true", help="list examples")
    parser.add_argument( '--force', dest="force", action="store_true", help='execute without confirmation (kill, (re)start)')
    parser.add_argument( '--full', dest="full", action="store_true", help="full MG listing")
    parser.add_argument( '--ivp', dest="ivp", action="store_true", help="installation verification procedure")
    parser.add_argument( '--list', dest="list", action="store_true", help='list servers and devices')
    parser.add_argument( '--mg', dest="mgPattern", nargs='?', default='Missing', help='restrict search with mg (with --list), consider --full')
    parser.add_argument( '--kill', dest="kill", action="store_true", help="kill servers")
    parser.add_argument( '--stop', dest="kill", action="store_true", help="stop servers")
    parser.add_argument( '--matching', dest="matching", action="store_true", help="list matching rules")
    parser.add_argument( '--prop', dest="propPattern", nargs='?', default='Missing', help='show (selected) properties (with --list)')
    parser.add_argument( '--restart', dest="restart", action="store_true", help='restart servers, start in reverted order')
    parser.add_argument( '--simon', dest="simOn", action="store_true", help='SimulationMode: 1')
    parser.add_argument( '--simoff', dest="simOff", action="store_true", help='SimulationMode: 0')
    parser.add_argument( '--simlist', dest="simList", action="store_true", help='List SimulationMode')
    parser.add_argument( '--stateFAULT', dest="stateFAULT", action="store_true", help='search for state == FAULT')
    parser.add_argument( '--stateALARM', dest="stateALARM", action="store_true", help='search for state == ALARM')
    parser.add_argument( '--start', dest="start", action="store_true", help='start servers')

    global args
    args = parser.parse_args()

    if args.examples:
        print_examples()
        return
 
    if args.matching:
        print_matching()
        return
    
    if args.ivp:
        execIVP()
        return

    if( args.list is False and 
        args.kill is False and
        args.restart is False and
        args.start is False and
        args.simOn is False and
        args.simOff is False and
        args.simList is False and
        args.dump is False):
        parser.print_help()
        return 

    selected = []
    if args.dbHostPattern == "Missing":
        tangoHost = os.getenv( 'TANGO_HOST')
        if tangoHost is None:
            print( "TANGO_HOST is not defined")
            return
        selected.append( tangoHost.split(':')[0])
    else:
        if os.getlogin() not in EXPERT_USERS: 
            print( "Please do not use TngUtility across hosts")
            return 

        lst = HasyUtils.getListFromFile( DBHOSTS)
        for host in lst: 
            if HasyUtils.match( host, args.dbHostPattern):
                if not HasyUtils.checkHostOnline( host): 
                    print( "host %s is offline" % host)
                    continue
                selected.append( host)

    if selected == []:
        print( "No matching dbHost found")
        return
 
    if len( args.pattern) == 1 and args.pattern[0] == 'tus':
        args.pattern = []
        args.pattern.append( "dgg2")
        args.pattern.append( "mdgg8")
        args.pattern.append( "mca")
        args.pattern.append( "omsvme58")
        # sis3302 module in my crate
        #args.pattern.append( "sis33")
        args.pattern.append( "sis36")
        args.pattern.append( "sis38")
        args.pattern.append( "tip")
        args.pattern.append( "vfc")
        args.pattern.append( "zmx")
    #
    # of more than one host is selected, only --list is allowed
    #
    if len( selected) > 1:
        if args.list is False:
            print( "TngUtility: selected dbHosts %s" % str( selected))
            print( "TngUtility: multiple-host actions only for --list")
            sys.exit( 255)
        for host in selected:
            if os.system( "ping -c 1 -w 1 -q %s > /dev/null 2>&1" % host):
                print( "%s is offline" % host)
                continue
            tg = TngUtility( host)
            if tg.db is None:
                print( "exception for %s" % host)
                continue
            tg.listServer( args.pattern)
        return

    tg = TngUtility( selected[0])

    if args.list is True:
        tg.listServer( args.pattern)
    elif args.restart is True:
        tg.restartServer( args.pattern)
    elif args.start is True:
        tg.startServer( args.pattern)
    elif args.kill is True:
        tg.killServer( args.pattern)
    elif args.simOn is True:
        tg.simServer( args.pattern, 1)
    elif args.simOff is True:
        tg.simServer( args.pattern, 0)
    elif args.simList is True:
        tg.simServer( args.pattern, 2)
    elif args.dump is True:
        tg.dump()
    else:
        print( "wrong input")

if __name__ == '__main__':
    main()

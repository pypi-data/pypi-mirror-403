#!/usr/bin/env python
#
import string
import sys, os
try: 
    from PyTango import *
except:
    pass
import json
import pprint
from . import TgUtils
import platform

pp = pprint.PrettyPrinter()

#
#
#
class MgConf:
    '''
    poolName:   if None, the first pool is taken
    mntgrpName: the group name
    flagClear:  if True, the MG is cleared

    Example: 

      mg = HasyUtils.MgUtils.MgConf( None, "mg1", True)
        create mg1, in the default pool and clear it 
      mg.addTimer( "eh_t01")
      mg.addCounter( "eh_c01", True)
        flagDisplay == True
      mg.addMCA( "eh_mca01")

      mg.updateConfiguration()

    '''
    def __init__(self, poolName, mntgrpName, flagClear = False):
        self.db = Database()

        poolNames = TgUtils.getLocalPoolNames()
        if poolName is None: 
            if len( poolNames) > 0: 
                poolName = poolNames[0]
            else: 
                raise ValueError( "MgConf.__init__(): no pool")
        #
        # the pool for the Mg
        #
        try: 
            self.poolMg = DeviceProxy( poolName) 
        except DevFailed as e:
            Except.print_exception( e)
            print( "failed to get proxy to %s " % poolName)
            sys.exit(255)
        if not TgUtils.proxyHasAttribute( self.poolMg, 'ControllerList'):
            print( "MgUtils.MgConf.__init__: %s is not a pool" % poolName)
            sys.exit(255)
            
        #
        # note: getLocalPoolNames() returns only the local pools
        # that have been exported at least once. 
        #
        poolNames = TgUtils.getLocalPoolNames()
        self.pools = []
        for pool in poolNames:
            if not checkPoolNameValid( pool): 
                print( "*** MgUtils.MgConf: ignoring pool %s" % pool)
                continue
            try:
                self.pools.append( DeviceProxy( pool))
            except: 
                Except.print_exception( e)
                print( "failed to get proxy to %s" % pool)
                sys.exit(255)
        # 
        # find the MG
        #
        self.mntgrpName = mntgrpName
        try: 
            self.mg = DeviceProxy( mntgrpName)
        except:
            timers = TgUtils.getTimerAliases()
            if timers is None: 
                print( "MgConf: %s does not exist and cannot be created " % mntgrpName)
            lst = [ mntgrpName, timers[0]]
            try:
                self.poolMg.command_inout( 'CreateMeasurementGroup', lst)
            except Exception as e:
                print( "MgUtils.MgConf.__init__(): CreateMeasurementGroup failed on %s" % self.poolMg.name())
                print( "MgUtils.MgConf.__init__(): %s" % repr( lst))
            self.mg = DeviceProxy( mntgrpName)
            
        if not flagClear:
            self.hsh = json.loads( self.mg.Configuration) 
            self.masterTimer = self.findMasterTimer()
            self.index = len(self.mg.ElementList)
            #TgUtils.dct_print( self.hsh)
        else:
            self.hsh = {}
            self.hsh[ 'controllers'] = {}
            self.hsh[ 'description'] = "Measurement Group"
            self.hsh[ 'label'] = mntgrpName
            self.index = 0
        #print( "+++MgUtils.__init()__\n%s" % TgUtils.dct_print2str( self.hsh))

    def updateConfiguration( self):
        """
        json-dump the dictionary self.hsh to the Mg configuration
        """
        #print( "+++MgUtils.updateConfiguration:\n%s" % TgUtils.dct_print2str( self.hsh))
        self.mg.Configuration = json.dumps( self.hsh)
            
    def findMasterTimer( self):
        
        for ctrl in self.hsh[ 'controllers']:
            if 'units' in self.hsh['controllers'][ctrl]:
                Channels = self.hsh[ 'controllers'][ctrl][ 'units'][ '0'][ 'channels']
            else:
                Channels = self.hsh[ 'controllers'][ctrl][ 'channels']
            for chan in Channels:
                # dgg8 is also a dgg2 (interface-wise)
                if chan.find( 'dgg2') > 0: 
                    temp = chan
                    #
                    # Debian-8: haso107d1:10000/expchan/dgg2_d1_01/1 -> expchan/dgg2_d1_01/1
                    # Debian-9: tango://hasep212lab.desy.de:10000/expchan/dgg2__lab01/1
                    #
                    pos = temp.find( '0000')
                    if pos > 0:
                        temp = temp[pos+5:]
                    masterTimer = self.db.get_alias( str(temp))
                    return masterTimer
        raise Exception( 'MgUtils.findMasterTimer', "No timer found")


    def findDeviceController( self, device):
        """
        returns the controller that belongs to a device
        """
        lst = []
        for pool in self.pools:
            try: 
                if not pool.ExpChannelList is None:
                    lst += pool.ExpChannelList
            except Exception as e:
                print("MgUtils.findDeviceController: something is wrong with %s" % pool.dev_name())
                print( "%s" % repr( e))
                sys.exit(255)
                
        ctrl = None
        for elm in lst:
            chan = json.loads( elm)
            # chan: 
            #{
            # 'axis': 17,
            # 'controller': 'haso107klx:10000/controller/sis3820ctrl/sis3820_exp',
            # 'full_name': 'haso107klx:10000/expchan/sis3820_exp/17',
            # 'id': 146,
            # 'instrument': '',
            # 'interfaces': ['Object', 'PoolObject', 'Element', 'ExpChannel', 'PoolElement', 'CTExpChannel', 'Acquirable'],
            # 'manager': 'exp_pool01',
            # 'name': 'exp_c17',
            # 'parent': 'sis3820_exp',
            # 'pool': 'exp_pool01',
            # 'source': 'haso107klx:10000/expchan/sis3820_exp/17/value',
            # 'type': 'CTExpChannel',
            # 'unit': '0',
            #}
            if device == chan['name']:
                ctrl = chan['controller']
                break
        if ctrl is None and device.find("adc") >= 0:
            ctrl = os.getenv("TANGO_HOST") + "/" + "controller/hasylabadcctrl/hasyadcctrl"
        elif ctrl is None and device.find("vfc") >= 0:
            ctrl = os.getenv("TANGO_HOST") + "/" + "controller/vfcadccontroller/hasyvfcadcctrl"
        return ctrl


    def findFullDeviceName( self, device):
        """
          input: exp_c01
          returns: expchan/hasylabvirtualcounterctrl/1
        """
        lst = []
        for pool in self.pools:
            lst += pool.AcqChannelList
        argout = None
        for elm in lst:
            chan = json.loads( elm)
            if device == chan['name']:
                #
                # from: expchan/hasysis3820ctrl/1/value
                # to:   expchan/hasysis3820ctrl/1
                #
                arr = chan['full_name'].split("/")
                argout = "/".join(arr[0:-1])
        if argout is None:
            raise Exception( 'MgUUtils.findFullDeviceName, %s' % device, "failed to find  %s" % device)
        return argout


    def addTimer( self, device):
        """ 
        add a timer to the Mg
        device: exp_t01
        """
        ctrl = self.findDeviceController( device)
        
        if ctrl not in self.hsh[ 'controllers']:
            self.masterTimer = device
            self.hsh[ 'monitor'] = self.findFullDeviceName( device)
            self.hsh[ 'timer'] = self.findFullDeviceName( device)
            self.hsh[ 'controllers'][ ctrl] = {}
            self.hsh[ 'controllers'][ ctrl][ 'synchronizer'] = "software"
            self.hsh[ 'controllers'][ ctrl][ 'channels'] = {}
            self.hsh[ 'controllers'][ ctrl][ 'monitor'] = self.findFullDeviceName(device)
            self.hsh[ 'controllers'][ ctrl][ 'timer'] = self.findFullDeviceName(device)
            self.hsh[ 'controllers'][ ctrl][ 'trigger_type'] = 0

        ctrlChannels = self.hsh[ 'controllers'][ctrl][ 'channels']

        fullDeviceName = self.findFullDeviceName( device)
        if not fullDeviceName in list( ctrlChannels.keys()):
            dct = {}
            dct['conditioning'] = ''
            dct['enabled'] = True
            dct['full_name'] = fullDeviceName
            dct['index'] = self.index
            self.index += 1
            dct['label'] = str( device)
            dct['name'] = str( device)
            dct['ndim'] = 0
            dct['normalization'] = 0
            dct['output'] = True
            dct['plot_axes'] = ['<mov>']
            dct['plot_type'] = 0
            dct['source'] = dct['full_name'] + "/Value"
            ctrlChannels[fullDeviceName] = dct

    #
    # add an extra timer to the measurement group
    #
    def addExtraTimer( self, device):
        """ device: exp_t01"""
        ctrl = self.findDeviceController( device)

        if ctrl not in self.hsh[ 'controllers']:
            self.hsh[ 'controllers'][ ctrl] = {}
            self.hsh[ 'controllers'][ ctrl][ 'synchronizer'] = "software"
            self.hsh[ 'controllers'][ ctrl][ 'channels'] = {}
            self.hsh[ 'controllers'][ ctrl][ 'monitor'] = self.findFullDeviceName(device)
            self.hsh[ 'controllers'][ ctrl][ 'timer'] = self.findFullDeviceName(device)
            self.hsh[ 'controllers'][ ctrl][ 'trigger_type'] = 0

        ctrlChannels = self.hsh[ 'controllers'][ctrl][ 'channels']

        fullDeviceName = self.findFullDeviceName( device)
        if not fullDeviceName in list( ctrlChannels.keys()):
            dct = {}
            dct['conditioning'] = ''
            dct['enabled'] = True
            dct['full_name'] = fullDeviceName
            dct['index'] = self.index
            self.index += 1
            dct['label'] = str( device)
            dct['name'] = str( device)
            dct['ndim'] = 0
            dct['normalization'] = 0
            dct['output'] = True
            dct['plot_axes'] = ['<mov>']
            dct['plot_type'] = 0
            dct['source'] = dct['full_name'] + "/Value"
            ctrlChannels[fullDeviceName] = dct
    #
    # add a counter to the measurement group
    #
    def addCounter( self, device, flagDisplay, flagOutput = 1):

        if device.find( 'sca_') == 0:
            return self.addSCA( device, flagDisplay, flagOutput)

        ctrl = self.findDeviceController( device)
        fullDeviceName = self.findFullDeviceName( device)

        if ctrl not in self.hsh[ 'controllers']:
            self.hsh[ 'controllers'][ ctrl] = {}
            self.hsh[ 'controllers'][ ctrl][ 'synchronization'] = 0
            self.hsh[ 'controllers'][ ctrl][ 'synchronizer'] = "software"
            self.hsh[ 'controllers'][ ctrl][ 'channels'] = {}
            self.hsh[ 'controllers'][ ctrl][ 'monitor'] = fullDeviceName
            self.hsh[ 'controllers'][ ctrl][ 'timer'] = fullDeviceName
            self.hsh[ 'controllers'][ ctrl][ 'trigger_type'] = 0

        ctrlChannels = self.hsh['controllers'][ctrl]['channels']

        if not fullDeviceName in list( ctrlChannels.keys()):
            dct = {}
            dct['conditioning'] = ''
            dct['enabled'] = True
            dct['full_name'] = fullDeviceName
            dct['index'] = self.index
            self.index += 1
            dct['label'] = str( device)
            dct['name'] = str( device)
            dct['ndim'] = 0
            dct['normalization'] = 0
            if flagOutput:
                dct['output'] = True
            else:
                dct['output'] = False
            dct['plot_axes'] = ['<mov>']
            if flagDisplay:
                dct['plot_type'] = 1
            else:
                dct['plot_type'] = 0
            dct['source'] = dct['full_name'] + "/Value"
            ctrlChannels[fullDeviceName] = dct
    #
    # add a MCA to the measurement group
    #
    def addMCA( self, device):
        ctrl = self.findDeviceController( device)
        fullDeviceName = self.findFullDeviceName( device)

        #
        # tango://haso107tk.desy.de:10000/controller/hasyonedctrl/mca8701_eh
        #
        if ctrl not in self.hsh[ 'controllers']:
            # print( "MgUtils.addMCA adding controller %s" % ctrl)
            self.hsh[ 'controllers'][ ctrl] = {}
            self.hsh[ 'controllers'][ ctrl][ 'synchronizer'] = "software"
            self.hsh[ 'controllers'][ ctrl][ 'channels'] = {}
            self.hsh[ 'controllers'][ ctrl][ 'monitor'] = fullDeviceName
            self.hsh[ 'controllers'][ ctrl][ 'timer'] = fullDeviceName
            #self.hsh[ 'controllers'][ ctrl][ 'monitor'] = self.findFullDeviceName(self.masterTimer)
            #self.hsh[ 'controllers'][ ctrl][ 'timer'] = self.findFullDeviceName(self.masterTimer)
            self.hsh[ 'controllers'][ ctrl][ 'trigger_type'] = 0

        ctrlChannels = self.hsh['controllers'][ctrl]['channels']

        if not fullDeviceName in list( ctrlChannels.keys()):
            dct = {}
            dct['conditioning'] = ''
            dct['enabled'] = True
            dct['full_name'] = fullDeviceName
            dct['index'] = self.index
            self.index += 1
            dct['label'] = str( device)
            dct['name'] = str( device)
            dct['ndim'] = 0
            dct['normalization'] = 0
            dct['output'] = True
            dct['plot_axes'] = ['<mov>']
            dct['plot_type'] = 0
            dct['source'] = dct['full_name'] + "/Value"
            ctrlChannels[fullDeviceName] = dct
    #
    # add a MCA to the measurement group
    #
    def addPilatus( self, device):
        ctrl = self.findDeviceController( device)
        fullDeviceName = self.findFullDeviceName( device)

        if ctrl not in self.hsh[ 'controllers']:
            #print( "MgUtils.addPilatus adding controller %s" % ctrl)
            self.hsh[ 'controllers'][ ctrl] = {}
            self.hsh[ 'controllers'][ ctrl][ 'synchronization'] = 0
            self.hsh[ 'controllers'][ ctrl][ 'synchronizer'] = "software"
            self.hsh[ 'controllers'][ ctrl][ 'channels'] = {}
            self.hsh[ 'controllers'][ ctrl][ 'monitor'] = fullDeviceName
            self.hsh[ 'controllers'][ ctrl][ 'timer'] = fullDeviceName
            #self.hsh[ 'controllers'][ ctrl][ 'monitor'] = self.findFullDeviceName(self.masterTimer)
            #self.hsh[ 'controllers'][ ctrl][ 'timer'] = self.findFullDeviceName(self.masterTimer)
            self.hsh[ 'controllers'][ ctrl][ 'trigger_type'] = 0

        ctrlChannels = self.hsh['controllers'][ctrl]['channels']
            
        if not fullDeviceName in list( ctrlChannels.keys()):
            dct = {}
            dct['conditioning'] = ''
            dct['enabled'] = True
            dct['full_name'] = fullDeviceName
            dct['index'] = self.index
            self.index += 1
            dct['label'] = str( device)
            dct['name'] = str( device)
            dct['ndim'] = 2
            dct['normalization'] = 0
            dct['output'] = True
            dct['plot_axes'] = ['<mov>']
            dct['plot_type'] = 0
            dct['source'] = dct['full_name'] + "/Value"
            ctrlChannels[fullDeviceName] = dct
    #
    # other: pilatus, lambda, 
    #
    def addOther( self, device):
        ctrl = self.findDeviceController( device)
        fullDeviceName = self.findFullDeviceName( device)

        if ctrl not in self.hsh[ 'controllers']:
            self.hsh[ 'controllers'][ ctrl] = {}
            self.hsh[ 'controllers'][ ctrl][ 'synchronizer'] = "software"
            self.hsh[ 'controllers'][ ctrl][ 'channels'] = {}
            self.hsh[ 'controllers'][ ctrl][ 'monitor'] = fullDeviceName
            self.hsh[ 'controllers'][ ctrl][ 'timer'] = fullDeviceName
            #self.hsh[ 'controllers'][ ctrl][ 'monitor'] = self.findFullDeviceName(self.masterTimer)
            #self.hsh[ 'controllers'][ ctrl][ 'timer'] = self.findFullDeviceName(self.masterTimer)
            self.hsh[ 'controllers'][ ctrl][ 'trigger_type'] = 0

        ctrlChannels = self.hsh['controllers'][ctrl]['channels']
            
        if not fullDeviceName in list( ctrlChannels.keys()):
            dct = {}
            dct['conditioning'] = ''
            dct['enabled'] = True
            dct['full_name'] = fullDeviceName
            dct['index'] = self.index
            self.index += 1
            dct['label'] = str( device)
            dct['name'] = str( device)
            dct['ndim'] = 2
            dct['normalization'] = 0
            dct['output'] = True
            dct['plot_axes'] = []
            dct['plot_type'] = 0
            dct['source'] = dct['full_name'] + "/Value"
            ctrlChannels[fullDeviceName] = dct


    def parseSCA( self, name):
        """
        name: sca_exp_mca01_100_200, returns [ 'exp_mca01', '100', '200']
        """
        lst = name.split('_')
        return [ lst[1] + '_' + lst[2], lst[3], lst[4]]


    def _getMcaName( self, mcaSardanaDeviceAlias):
        """
        input: sardana device name alias
        output: the MCA Tango server name which is used by the Sardana device
        """
        try: 
            proxy = DeviceProxy( mcaSardanaDeviceAlias)
        except DevFailed as e:
            Except.re_throw_exception( e, 
                                       "MgUtils",
                                       "failed to create proxy to %s " % mcaSardanaDeviceAlias,
                                       "MgUtils._gHeMcaName")
        return proxy.TangoDevice

    def _addSca( self, device):
        """
        Input: device: sca_exp_mca01_100_200
        Returns full controller name as e.g.: haso107klx:10000/controller/hasscactrl/sca_exp_mca01_100_200
        Creates a HasySca controller and creates a device for this controller, There
        is only one device per controller
        """
        mca, roiMin, roiMax = self.parseSCA( device)
        #
        # find the tango device name which is used my the sardana device
        #
        tgMca = self._getMcaName( mca)
        #
        # sca_exp_mca01_100_200_ctrl
        #
        ctrlAlias = device + "_ctrl"
        #
        # see whether the controller exists already
        #
        lst = []
        for pool in self.pools:
            lst += pool.ControllerList
        ctrlFullName = None
        for elm in lst:
            chan = json.loads( elm)
            if ctrlAlias == chan['name']:
                ctrlFullName = chan['full_name']
                break
        #
        # if the controller does not exist, create it
        #
        proxy = DeviceProxy( tgMca)
        dataLength = proxy.DataLength
        if int(roiMax) >= dataLength:
            raise Exception( "MgUtils._addSca %s " % device,
                             "roiMax %d  >= datalength %d " % (int(roiMax), int(dataLength)))
        if int(roiMin) >= dataLength:
            raise Exception( "MgUtils._addSca %s " % device,
                             "roiMin %d  >= datalength %d " % (int(roiMin), dataLength))

        
        if ctrlFullName is None:
            lst = [ 'CTExpChannel', 'HasyScaCtrl.py', 'HasyScaCtrl', ctrlAlias, "mca", tgMca, "roi1", roiMin, "roi2", roiMax] 
            try:
                self.poolMg.CreateController( lst)
            except DevFailed as e:
                Except.print_exception( e)
                print( "poolMg.CreateController failed for %s" % str(lst))
                sys.exit(255)

            lst = self.poolMg.ControllerList
            for elm in lst:
                chan = json.loads( elm)
                if ctrlAlias == chan['name']:
                    ctrlFullName = chan['full_name']
                    break
        if ctrlFullName is None:
            raise Exception( 'MgUtils._addSca', "failed to make controller for %s" % device)
                
        #
        # see whether the SCA device exists
        #
        lst = []
        for pool in self.pools:
            lst += pool.ExpChannelList
        flag = False
        for elm in lst:
            chan = json.loads( elm)
            if device == chan['name']:
                flag = True
                break

        if not flag:
            #
            # "CTExpChannel","HasyScaCtrl","1","sca_exp_mca01_100_200"
            #
            lst = [ "CTExpChannel", ctrlAlias, "1", device]
            self.poolMg.CreateElement( lst)

        return ctrlFullName

    def makeScaControllerForPseudoCounter( self, device):
        """
        Input: device: sca_exp_mca01_100_200
        Returns full controller name, e.g.: haso107klx:10000/controller/mca2scactrl/sca_exp_mca01_100_200_ctrl
        """
        mca, roiMin, roiMax = self.parseSCA( device)
        
        ctrlAlias = device + "_ctrl"
        #
        # see whether the controller exists already
        #
        lst = []
        for pool in self.pools:
            lst += pool.ControllerList
        for elm in lst:
            chan = json.loads( elm)
            if ctrlAlias == chan['name']:
                return chan['full_name']
        lst = [ 'PseudoCounter', 'MCA2SCACtrl.py', 'MCA2SCACtrl', device + "_ctrl", 
                'mca=' + self.findFullDeviceName( mca), 'sca=' + device]

        self.poolMg.CreateController( lst)
        #
        # now it has been created. go through the list again an return the full controller name
        #
        lst = self.poolMg.ControllerList
        for elm in lst:
            chan = json.loads( elm)
            if ctrlAlias == chan['name']:
                # TgUtils.dct_print( chan)
                #
                # set the ROIs
                #
                proxy = DeviceProxy( device)
                proxy.Roi1 = int(roiMin)
                proxy.Roi2 = int(roiMax)
                return chan['full_name']
        raise Exception( 'MgUtils.makeController', "failed to make controller for %s" % device)


    def addSCA( self, device, flagDisplay, flagOutput):
        """
        add a SCA to the measurement group
          input: device, e.g. sca_exp_mca01_100_200

        SardanaChMg.py -g tktest -t eh_t01 -c eh_c01,sca_eh_mca01_100_200 -m eh_mca01

        """
        if device.find('sca_') != 0:
            print( "MgUtils.addSCA: '%s' does not begin with 'sca_'," % device)
            return False

        #
        # there is one element per controller
        #
        ctrl = self._addSca( device)
        fullDeviceName = self.findFullDeviceName( device)
        
        if ctrl not in self.hsh[ 'controllers']:
            #print( "MgUtils.addSca adding controller %s " % fullCtrlName)
            self.hsh[ 'controllers'][ ctrl] = {}
            self.hsh[ 'controllers'][ ctrl][ 'synchronizer'] = "software"
            self.hsh[ 'controllers'][ ctrl][ 'channels'] = {}
            self.hsh[ 'controllers'][ ctrl][ 'monitor'] = fullDeviceName
            self.hsh[ 'controllers'][ ctrl][ 'timer'] = fullDeviceName
            self.hsh[ 'controllers'][ ctrl][ 'trigger_type'] = 0

        ctrlChannels = self.hsh['controllers'][ctrl]['channels']
        
        if not fullDeviceName in list( ctrlChannels.keys()):
            dct = {}
            dct['conditioning'] = ''
            dct['enabled'] = True
            dct['full_name'] = fullDeviceName
            dct['index'] = self.index
            self.index += 1
            dct['label'] = str( device)
            dct['name'] = str( device)
            dct['ndim'] = 0
            dct['normalization'] = 0
            if flagOutput:
                dct['output'] = True
            else:
                dct['output'] = False
            dct['plot_axes'] = ['<mov>']
            if flagDisplay:
                dct['plot_type'] = 1
            else:
                dct['plot_type'] = 0
            dct['source'] = dct['full_name'] + "/Value"
            ctrlChannels[fullDeviceName] = dct

        return True
    

def setMg( poolName = None, mgName = None, 
           timer = None, extraTimers = None, 
           counters = None, countersNodisplay = None, 
           mcas = None, others = None):
    """
    fill timer, extraTimers, counters, mcas, pilatus, lambda, into a MG

    Example: 
       HasyUtils.MgUtils.setMg( mgName= "mg_tnggui", timer = "eh_t01", mcas = "eh_mca01,eh_mca02")
    """

    if mgName is None: 
        raise ValueError( "MgUtils.setMg: MG name is missing")

    if timer is None: 
        raise ValueError( "MgUtils.setMg: master timer is missing")

    # if poolName is not supplied and only one pool exists, take this one
    #
    if poolName is None:
        lst = TgUtils.getPoolNames()
        if len( lst) == 0:
            raise ValueError( "MgUtils.setMg: no pool")
        poolName = lst[0]

    flagClear = True
    mgConf = MgConf( poolName, mgName, flagClear)

    mgConf.addTimer( timer)

    if extraTimers is not None and len( extraTimers) > 0: 
        for timer in extraTimers.split(','):
            mgConf.addExtraTimer( timer)

    if mcas is not None and len( mcas) > 0: 
        for mca in mcas.split(','):
            if mca:
                mgConf.addMCA( mca)

    if counters is not None and len( counters) > 0: 
        for counter in counters.split(','):
            if counter:
                mgConf.addCounter( counter, 1, 1)

    if countersNodisplay is not None and len( countersNodisplay) > 0:
        for counter in countersNodisplay.split(','):
            if counter:
                mgConf.addCounter( counter, 0, 1)
                    
    if others is not None and len( others) > 0:
        for other in others.split(','):
            if other:
                mgConf.addOther( other)

    mgConf.updateConfiguration()
    return 
    
    
def checkPoolNameValid( deviceName): 
    """
    check whether a MacroServer is using this pool

    deviceName: 'p09/pool/haso107tk'

    return False
      if the alias of the device name is 'NoAlias'
      if no MacroServer is pointing to this Pool, property PoolNames

    """
    alias = TgUtils.getAlias( deviceName)
    if alias.lower() == 'noalias': 
        #print( "MgUtils.checkPoolNameValid: NoAlias for %s, return False" % str( deviceName))
        return False

    msNames = TgUtils.getMacroServerNames()

    if len( msNames) == 0: 
        print( "MgUtils.checkPoolNameValid: len( msNames) == 0")
        sys.exit( 255)
    elif len( msNames) > 1: 
        print( "MgUtils.checkPoolNameValid: len( msNames) > 1: %s" % str( msNames))
        sys.exit( 255)

    lst = TgUtils.getDeviceProperty( msNames[0], 'PoolNames')

    for elm in lst: 
        if elm == alias: 
            #print( "MgUtils.checkPoolNameValid: Macroserver %s is using %s, OK" % (msNames[0], alias))
            return True

    print( "MgUtils.checkPoolNameValid: Macroserver %s is NOT using %s, BAD" % (msNames[0], alias))
    return False
            
    

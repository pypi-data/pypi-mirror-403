#!/bin/env python3
'''
$ python3 -m unittest discover -v

python3 /home/kracht/Misc/hasyutils/test/testTgUtils.py

python3 ./test/testTgUtils.py testTgUtils.test_versionSardanaNewMg
python3 ./test/testTgUtils.py testTgUtils.test_versionPySpectra
python3 ./test/testTgUtils.py testTgUtils.test_getMisc
python3 ./test/testTgUtils.py testTgUtils.test_DMSP
python3 ./test/testTgUtils.py testTgUtils.test_ENV
python3 ./test/testTgUtils.py testTgUtils.test_lsMacroServerEnvironment
python3 ./test/testTgUtils.py testTgUtils.test_getMacroInfo
python3 ./test/testTgUtils.py testTgUtils.test_runMacro
python3 ./test/testTgUtils.py testTgUtils.test_checkMacroServerPool
python3 ./test/testTgUtils.py testTgUtils.test_ECMonitor
python3 ./test/testTgUtils.py testTgUtils.test_getHostList
python3 ./test/testTgUtils.py testTgUtils.test_getHostListFromFile
'''
import unittest, sys, os, time
import HasyUtils
import PyTango

class testTgUtils( unittest.TestCase):

    @classmethod
    def setUpClass( clss):
    
        if not HasyUtils.unitTestChecks( "%s.setupClass" % clss):
            sys.exit( 255) 

    @classmethod
    def tearDownClass( clss): 

        if not HasyUtils.unitTestChecks( "%s.tearDownClass" % clss):
            sys.exit( 255) 

    def test_versionPySpectra( self):

        print( "\n>>> testTgUtils.test_versionPySpectra, BEGIN")
        ret = HasyUtils.getPackageVersion( 'bongo')
        self.assertTrue( ret is None)
        hostname = HasyUtils.getHostname()
        ret = HasyUtils.getPackageVersion( 'python3-pyspectra')
        self.assertTrue( ret is not None)
        ret = HasyUtils.getPackageVersion( 'python-pyspectra')
        self.assertTrue( ret is None)
        ret = HasyUtils.getVersionSardana()
        self.assertTrue( ret.find( 'fsec') > 0)

        print( ">>> testTgUtils.test_versionPySpectra, DONE")
        return

    def test_versionSardanaNewMg( self):
        ret = HasyUtils.versionSardanaNewMg()
        self.assertTrue( ret)
        return

    def test_waitForServer( self):
        print( "\n>>> testTgUtils.test_waitForServer BEGIN")
        ret = HasyUtils.waitForServer( "OmsVme58/EH", 1)
        self.assertTrue( ret)
        print( ">>> testTgUtils.test_waitForServer DONE")
        return

    def test_serverIsRunningStopped( self):
        print( "\n>>> testTgUtils.test_serverIsRunningStopped BEGIN")
        ret = HasyUtils.serverIsRunning( "OmsVme58/EH")
        self.assertTrue( ret)
        ret = HasyUtils.serverIsStopped( "OmsVme58/EH")
        self.assertFalse( ret)
        print( ">>> testTgUtils.test_serverIsRunningStopped DONE")
        return

    def test_checkMacroServerPool( self):
        print( "\n>>> testTgUtils.test_checkMacroServerPool BEGIN")
        lst = []
        ret = HasyUtils.checkMacroServer( lst, False)
        self.assertEqual( ret, True)
        self.assertEqual( len( lst), 0)
        lst = []
        ret = HasyUtils.checkPool( lst, False)
        self.assertEqual( ret, True)
        #+++self.assertEqual( len( lst), 0)
        lst = []
        ret = HasyUtils.checkDoor( lst, False)
        self.assertEqual( ret, True)
        self.assertEqual( len( lst), 0)
        lst = []
        ret = HasyUtils.checkActiveMeasurementGroup( lst, False)
        self.assertEqual( ret, True)
        self.assertEqual( len( lst), 0)
        print( ">>> testTgUtils.test_checkMacroServerPool DONE")
        return

    def test_getClassList( self):
        print( "\n>>> testTgUtils.test_getClassList BEGIN")
        ret = HasyUtils.getClassList()
        self.assertGreater( len( ret), 30) # 24.1.2020: 38
        ret = HasyUtils.getClassList( "haspp08mono")
        self.assertGreater( len( ret), 100) # 24.1.2020: 107
        print( ">>> testTgUtils.test_getClassList DONE")
        return

    def test_getHostList( self):
        print( "\n>>> testTgUtils.test_getHostList BEGIN")
        lst = HasyUtils.getHostList()
        lst1 = []
        for elm in lst:
            if elm == 'null': 
                continue
            lst1.append( elm)
        hostname = HasyUtils.getHostname()
        if hostname == "haso107d10": 
            self.assertEqual( len( lst1), 1) 
        elif hostname == "haso107d1": 
            self.assertEqual( len( lst1), 2) 
        print( ">>> testTgUtils.test_getHostList DONE")
            
        return

    def test_getHostListFromFile( self):
        print( "\n>>> testTgUtils.test_getHostListListFromFile BEGIN")
        lst = HasyUtils.getHostListFromFile( "./test/unitTestHosts.lis")
        self.assertEqual( len(lst), 18) 
        print( ">>> testTgUtils.test_getHostListFromFile DONE")
            
        return

    def test_getAlias( self):
        print( "\n>>> testTgUtils.test_getAlias BEGIN")
        ret = HasyUtils.getAlias( 'motor/omsvme58_eh/12')
        self.assertEqual( ret, 'chi')
        ret = HasyUtils.getDeviceNameByAlias( 'chi')
        self.assertEqual( ret, 'motor/omsvme58_eh/12')
        print( ">>> testTgUtils.test_getAlias DONE")

    def test_getMisc( self):
        print( "\n>>> testTgUtils.test_getMisc BEGIN")
        hostname = HasyUtils.getHostname()
        ret = HasyUtils.getDeviceNamesByServer( "DGG2/EH")
        self.assertEqual( len( ret), 2)
        self.assertEqual( ret[0], 'p09/dgg2/eh.01')
        self.assertEqual( ret[1], 'p09/dgg2/eh.02')
        ret = HasyUtils.getDeviceNamesByClass( "DGG2")
        self.assertEqual( len( ret), 2)
        self.assertEqual( ret[0], 'p09/dgg2/eh.01')
        self.assertEqual( ret[1], 'p09/dgg2/eh.02')
        ret = HasyUtils.getMotorNames()
        self.assertGreater( len( ret), 90) # 24.1.2020: 92
        ret = HasyUtils.getServerInstance( "OmsVme58")
        if hostname == 'haso107d1': 
            self.assertEqual( len( ret), 2)
            self.assertEqual( ret[0], "D1")
            self.assertEqual( ret[1], "EH")
        else: 
            self.assertEqual( len( ret), 1)
            self.assertEqual( ret[0], "EH")
        ret = HasyUtils.getServerNameByClass( "DGG2")
        self.assertEqual( len( ret), 1)
        self.assertEqual( ret[0], "DGG2/EH")
        ret = HasyUtils.getDoorNames()
        self.assertEqual( len( ret), 3)
        BL = 'p09'
        if hostname == 'haszvmtangout': 
            BL = 'p09'
        self.assertEqual( ret[0], "%s/door/%s.01" % (BL, hostname))
        self.assertEqual( ret[1], "%s/door/%s.02" % (BL, hostname))
        self.assertEqual( ret[2], "%s/door/%s.03" % (BL, hostname))

        ret = HasyUtils.getLocalDoorNames()
        self.assertEqual( len( ret), 3)

        self.assertEqual( ret[0], "%s/door/%s.01" % (BL, hostname))
        self.assertEqual( ret[1], "%s/door/%s.02" % (BL, hostname))
        self.assertEqual( ret[2], "%s/door/%s.03" % (BL, hostname))

        ret = HasyUtils.getMacroServerNames()
        self.assertEqual( len( ret), 1)
        self.assertEqual( ret[0], "%s/macroserver/%s.01" % (BL, hostname))
        ret = HasyUtils.getLocalMacroServerNames()
        self.assertEqual( len( ret), 1)
        self.assertEqual( ret[0], "%s/macroserver/%s.01" % (BL, hostname))
        ret = HasyUtils.getMacroServerServers()
        self.assertEqual( len( ret.value_string), 1)
        self.assertEqual( ret.value_string[0], "MacroServer/%s" % hostname)

        ret = HasyUtils.getMacroServerStatusInfo()
        if ret != "Idle": 
            print( "testTgUtils._getMisc: MS status %s" % ret)
        self.assertEqual( ret, "Idle")

        ret = HasyUtils.getPoolNames()
        self.assertEqual( len( ret), 1)
        self.assertEqual( ret[0], "%s/pool/%s" % (BL, hostname))

        ret = HasyUtils.getLocalPoolNames()
        self.assertEqual( len( ret), 1)
        self.assertEqual( ret[0], "%s/pool/%s" % (BL, hostname))

        ret = HasyUtils.getLocalPoolServers()
        self.assertEqual( len( ret), 1)
        self.assertEqual( ret[0], "Pool/%s" % hostname)

        ret = HasyUtils.getStarterHostByDevice( '%s/motor/eh.01' % (BL))
        self.assertEqual( ret, '%s.desy.de' % hostname)

        ret = HasyUtils.getStarterHostByDevice( '%s:10000/%s/motor/eh.01' % (hostname, BL))
        self.assertEqual( ret, '%s.desy.de' % hostname)

        ret = HasyUtils.getMgAliases()
        self.assertGreater( len( ret), 3)

        self.assertEqual( HasyUtils.checkMacroServerEnvironment(), True)
        self.assertEqual( HasyUtils.checkECStatus(), True)

        print( ">>> testTgUtils.test_getMisc DONE")

        return

    def test_DMSP( self):
        print( "\n>>> testTgUtils.test_DMSP BEGIN")
        dmsp = HasyUtils.DMSP( HasyUtils.getDoorNames()[0])

        dmsp.setEnv( "testKey1", "testVar1")
        self.assertEqual( dmsp.getEnv( 'testKey1'), 'testVar1')
        dmsp.unsetEnv( "testKey1")
        self.assertEqual( dmsp.getEnv( 'testKey1'), None)
#
# d10 has a different debian version
#        dmsp = HasyUtils.DMSP( 'haso107d10:10000/p09/door/haso107d10.01')
#        dmsp.setEnv( "testKey2", "testVar2")
#        self.assertEqual( dmsp.getEnv( 'testKey2'), 'testVar2')
#        dmsp.unsetEnv( "testKey2")
#        self.assertEqual( dmsp.getEnv( 'testKey2'), None)

        dmsp = HasyUtils.DMSP( 'haso107d10:10000/p09/door/haso107d10.01')
        dmsp.setEnv( "testKey2", "testVar2")
        self.assertEqual( dmsp.getEnv( 'testKey2'), 'testVar2')
        dmsp.unsetEnv( "testKey2")
        self.assertEqual( dmsp.getEnv( 'testKey2'), None)
        
        print( ">>> test_DMSP OK")
        return 

    def test_ENV( self):
        print( "\n>>> test.TgUtils.test_ENV BEGIN")

        self.assertEqual( HasyUtils.setEnv( "testKey2", "testVar2"), True)
        self.assertEqual( HasyUtils.getEnv( 'testKey2'), 'testVar2')
        self.assertEqual( HasyUtils.unsetEnv( "testKey2"), True) 
        self.assertEqual( HasyUtils.getEnv( 'testKey2'), None)

        self.assertEqual( HasyUtils.setEnvCautious( { "cautiousKey1": "cautiousValue1", 
                                                      "cautiousKey2": "cautiousValue2"}), True)

        self.assertEqual( HasyUtils.getEnv( 'cautiousKey1'), 'cautiousValue1')

        self.assertEqual( HasyUtils.setEnvCautious( { "cautiousKey1": "cautiousValue11", 
                                                      "cautiousKey2": "cautiousValue22",
                                                      "cautiousKey3": "cautiousValue33"}), True)

        self.assertEqual( HasyUtils.getEnv( 'cautiousKey1'), 'cautiousValue1')
        self.assertEqual( HasyUtils.getEnv( 'cautiousKey2'), 'cautiousValue2')
        self.assertEqual( HasyUtils.getEnv( 'cautiousKey3'), 'cautiousValue33')

        self.assertEqual( HasyUtils.unsetEnv( "cautiousKey1"), True) 
        self.assertEqual( HasyUtils.unsetEnv( "cautiousKey2"), True) 
        self.assertEqual( HasyUtils.unsetEnv( "cautiousKey3"), True) 

        self.assertEqual( HasyUtils.setEnv( "testKey3", "testVar3"), True)
        hsh = HasyUtils.getEnvDct()

        self.assertEqual( 'testKey3' in hsh, True) 
        self.assertEqual( HasyUtils.unsetEnv( "testKey3"), True) 
        self.assertEqual( HasyUtils.getEnv( 'testKey3'), None)

        hsh = HasyUtils.getEnvDct()
        
        self.assertEqual( 'ScanFile' in hsh, True) 
        self.assertEqual( 'ScanDir' in hsh, True) 
        self.assertEqual( 'ScanID' in hsh, True) 

        hsh = HasyUtils.getEnvVarAsDct( '_GeneralHooks')
        print( "%s" % repr( hsh))

        print( ">>> test_ENV OK")
        return 

    def test_lsMacroServerEnvironment( self):
        print( "\n>>> testTgUtils.test_lsMSENV BEGIN")

        self.assertEqual( HasyUtils.lsMacroServerEnvironment(), True)

        print( ">>> test_lsMSEN OK")
        return 

    def test_getMacroInfo( self):
        print( "\n>>> testTgUtils.test_getMacroInfo BEGIN")

        macroInfo = HasyUtils.getMacroInfo( 'wa')
        self.assertEqual( macroInfo[ 'description'], 'Show all motor positions')

        print( ">>> test_getMacroInfo OK")
        return 

    def test_runMacro( self):
        print( "\n>>> testTgUtils.test_runMacro BEGIN")

        mgOld = HasyUtils.getEnv( "ActiveMntGrp") 

        HasyUtils.runMacro( "change_mg -g mg_ivp -t eh_t01 -c eh_c01,sig_gen,eh_c02")

        mg = HasyUtils.getEnv( "ActiveMntGrp") 
        self.assertEqual( mg, 'mg_ivp')

        startTime = time.time()
        ret = HasyUtils.runMacro( "lsmac wm")
        diffTime = time.time() - startTime
        # 0.14
        self.assertEqual( len( ret), 3)
        self.assertEqual( (diffTime < 0.5), True)

        startTime = time.time()
        ret = HasyUtils.runMacro( "lsenv")
        diffTime = time.time() - startTime
        # 0.16
        self.assertEqual( (diffTime < 0.5), True)

        startTime = time.time()
        # takes about 3.9s, d1 6s
        ret = HasyUtils.runMacro( "ascan exp_dmy01 0 1 10 0.1")
        diffTime = time.time() - startTime
        self.assertEqual( (diffTime < 7), True)

        HasyUtils.setEnv( "ActiveMntGrp", mgOld) 

        print( ">>> test_runMacro OK")
        return 

    def test_ECMonitor( self): 

        print( "\n>>> testTgUtils.test_ECMonitor BEGIN")
        mgOld = HasyUtils.getEnv( "ActiveMntGrp") 

        doorProxy = HasyUtils.getDoorProxies()[0]

        if doorProxy.state() != PyTango.DevState.ON:
            print( "***testTgUtils.test_ECMonitor: door is not ON, %s" % repr( doorProxy.state()))
            sys.exit( 255)

        HasyUtils.runMacro( "change_mg -g mg_ivp -t eh_t01 -c eh_c01,sig_gen,eh_c02")

        mg = HasyUtils.getEnv( "ActiveMntGrp") 
        self.assertEqual( mg, 'mg_ivp')

        msgs = []
        self.assertEqual( HasyUtils.checkActiveMeasurementGroup( errorMsgs = msgs, verbose = True), True)

        print( "testTgUtils: msgs %s " % repr( msgs))
        HasyUtils.stopServer( "DGG2/EH")

        self.assertEqual( HasyUtils.checkActiveMeasurementGroup(), False)
        
        HasyUtils.startServer( "DGG2/EH")

        self.assertEqual( HasyUtils.checkActiveMeasurementGroup(), True)

        HasyUtils.stopServer( "SIS3820/EH")

        self.assertEqual( HasyUtils.checkActiveMeasurementGroup(), False)

        HasyUtils.startServer( "SIS3820/EH")

        self.assertEqual( HasyUtils.checkActiveMeasurementGroup(), True)

        self.assertEqual( HasyUtils.checkMacroServer(), True)

        hostname = HasyUtils.getHostname()

        HasyUtils.stopServer( "MacroServer/%s" % hostname)

        self.assertEqual( HasyUtils.checkMacroServer(), False)

        HasyUtils.startServer( "MacroServer/%s" % hostname)

        self.assertEqual( HasyUtils.checkMacroServer(), True)

        self.assertEqual( HasyUtils.checkPool(), True)

        HasyUtils.stopServer( "Pool/%s" % hostname)

        self.assertEqual( HasyUtils.checkPool(), False)

        HasyUtils.startServer( "Pool/%s" % hostname)

        HasyUtils.restartServer( "MacroServer/%s" % hostname)

        self.assertEqual( HasyUtils.checkPool(), True)

        #
        # try to move a motor outside limits, generate a door ALARM state
        # 28.11.2023: ALARM is not so good. state() has to be ON at the
        # end of HasyUtils.runMacro()
        #
        #p = PyTango.DeviceProxy( "eh_mot01")
        #p = PyTango.DeviceProxy( p.tangodevice)
        #pOld = p.position
        #HasyUtils.runMacro( "mv eh_mot01 %g" % (p.unitLimitMax + 1))
        #self.assertEqual( HasyUtils.checkDoor(), False)
        #time.sleep(1)
        #HasyUtils.runMacro( "mv eh_mot01 %g" % pOld)
        #self.assertEqual( HasyUtils.checkDoor(), True)

        HasyUtils.setEnv( "ActiveMntGrp", mgOld) 

if __name__ == "__main__":
    unittest.main()

#!/bin/env python
'''
$ python -m unittest discover -v
python ./test/testVirtuals.py testVirtuals.test_restartVc
python ./test/testVirtuals.py testVirtuals.test_restartVm
'''
import unittest, sys, os, time
import HasyUtils
import PyTango

class testVirtuals( unittest.TestCase):

    @classmethod
    def setUpClass( clss):
    
        if not HasyUtils.unitTestChecks( "%s.setupClass" % clss):
            sys.exit( 255) 

    @classmethod
    def tearDownClass( clss): 

        if not HasyUtils.unitTestChecks( "%s.tearDownClass" % clss):
            sys.exit( 255) 

    def test_restartVc( self):
        '''
        stop/start VcExecutor
        '''
        print( "\ntestVirtuals.test_restartVc, BEGIN")
        
        serverName = "VcExecutor/EH"
        deviceName = "p09/vcexecutor/eh.01"

        try: 
            ret = HasyUtils.startServer( serverName)
        except:
            ret = True
        self.assertTrue( ret)
        p = PyTango.DeviceProxy( deviceName)
        ret = HasyUtils.stopServer( serverName)
        self.assertTrue( ret)

        flag = False
        try:
            ret = p.state()
        except Exception as e:
            self.assertEqual( e.args[0].desc.find( "Device %s is not exported" % deviceName), 0)
            print( "testVirtuals.test_restartVc: %s is not exported, OK" % p.dev_name())
            flag = True

        self.assertTrue( flag)
         
        ret = HasyUtils.startServer( serverName)
        self.assertTrue( ret)
            
        self.assertEqual( p.state(), PyTango.DevState.ON)
        print( "testVirtuals.test_restartVc: %s is ON, OK" % p.name())

        print( "testVirtuals.test_restartVc, DONE")
        
        return

    def test_restartVm( self):
        '''
        stop/start VmExecutor
        '''
        print( "\ntestVirtuals.test_restartVm, BEGIN")
        
        serverName = "VmExecutor/EH"
        deviceName = "p09/vmexecutor/eh.01"

        try: 
            ret = HasyUtils.startServer( serverName)
        except:
            ret = True
        self.assertTrue( ret)
        p = PyTango.DeviceProxy( deviceName)
        ret = HasyUtils.stopServer( serverName)
        self.assertTrue( ret)

        flag = False
        try:
            ret = p.state()
        except Exception as e:
            self.assertEqual( e.args[0].desc.find( "Device %s is not exported" % deviceName), 0)
            print( "testVirtuals.test_restartVm: %s is not exported, OK" % p.dev_name())
            flag = True
        
        ret = HasyUtils.startServer( serverName)
        self.assertTrue( ret)

        self.assertEqual( p.state(), PyTango.DevState.ON)
        print( "testVirtuals.test_restartVm: %s is ON, OK" % p.name())
        
        print( "testVirtuals.test_restartVm, DONE")
        return

if __name__ == "__main__":
    unittest.main()

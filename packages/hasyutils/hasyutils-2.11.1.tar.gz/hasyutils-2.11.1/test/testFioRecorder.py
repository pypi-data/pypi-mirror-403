
#!/bin/env python
'''
python3 ./test/testFioRecorder.py testFioRecorder.test_createFio
'''
import unittest, sys, os, time
import HasyUtils
import HasyUtils.MgUtils
import PyTango
import numpy as np

class testFioRecorder( unittest.TestCase):

    @classmethod
    def setUpClass( clss):
    
        print( "testFioRecorder.setUpClass") 
        if not HasyUtils.unitTestChecks( "%s.setupClass" % clss):
            sys.exit( 255) 

    @classmethod
    def tearDownClass( clss): 

        if not HasyUtils.unitTestChecks( "%s.tearDownClass" % clss):
            sys.exit( 255) 

    def test_createFio(  self):

        print( "\n>>> testFioRecorder.test_createFio BEGIN")

        HasyUtils.setEnv( "ActiveMntGrp", "mg_pysp")
        HasyUtils.setEnv( "FlagFioWriteMotorPositions", True)
        HasyUtils.setEnv( "FioAdditions", "/online_dir/fioAdds.py")

        door = PyTango.DeviceProxy( HasyUtils.getDoorNames()[0])
        if door.state() != PyTango.DevState.ON: 
            print( "testFioRecorder.testCreateFio: door is not ON %s" % repr( door.state()))
            return 

        exp_dmy01 = PyTango.DeviceProxy( "exp_dmy01")
        
        #  ascan exp_dmy01 0 1 49 0.1
        door.runmacro( [ "ascan", "exp_dmy01", "0", "1", "5", "0.1"])

        startTime = time.time()
        while door.state() == PyTango.DevState.RUNNING: 
            print( "testFioRecorder.testCreateFio: ascan is RUNNING, exp_dmy01.position %g [0, 1]" % 
                   exp_dmy01.position)
            time.sleep(2)
            # 25.4.2023: 45 -> 80
            if (time.time() - startTime) > 80: 
                print( "testFioRecorder.testcreateFio: ascan takes too much time %g ( > 80s )" % 
                       (time.time() - startTime))
                HasyUtils.checkECStatus( verbose = True)
                sys.exit( 255) 
        print( "testFioRecorder.testCreateFio: after ascan, door state %s, exp_dmy01.position %g [0, 1]" % 
               ( repr( door.state()), exp_dmy01.position))

        fioObj = HasyUtils.fioReader( HasyUtils.getScanFileName())

        for elm in [ 'eh_mot01', 'eh_mot02', 'exp_dmy01', 'fioAdd_par1', 'fioAdd_par2']:
            ret = elm in fioObj.parameters
            self.assertEqual( ret, True)

        self.assertEqual( fioObj.parameters[ 'fioAdd_par1'], 'value1')
        self.assertEqual( fioObj.parameters[ 'fioAdd_par2'], 'value2')
        self.assertEqual( fioObj.parameters[ 'fioAdd_par3'], 'value3')
            
        HasyUtils.setEnv( "FlagFioWriteMotorPositions", False)
        HasyUtils.unsetEnv( "FioAdditions")
        
        #  ascan exp_dmy01 0 1 49 0.1
        door.runmacro( [ "ascan", "exp_dmy01", "0", "1", "5", "0.1"])

        startTime = time.time()
        while door.state() == PyTango.DevState.RUNNING: 
            print( "testCreateFio: ascan is RUNNING, pos %g " % exp_dmy01.position)
            time.sleep(3)
            # 25.4.2023: 45 -> 80
            if (time.time() - startTime) > 80: 
                print( "testFioRecorder.testcreateFio: ascan takes too much time %g ( > 8s )" % (time.time() - startTime))
                HasyUtils.checkECStatus( verbose = True)
                sys.exit( 255) 
        print( "testCreateFio: door state %s, exp_dmy01.position %g [0, 1]" % ( repr( door.state()), exp_dmy01.position))

        fioObj = HasyUtils.fioReader( HasyUtils.getScanFileName())

        for elm in [ 'eh_mot01', 'eh_mot02', 'exp_dmy01', 'fioAdd_par1', 'fioAdd_par2']:
            ret = elm in fioObj.parameters
            self.assertEqual( ret, False)

        HasyUtils.setEnv( "FioAdditions", "/online_dir/fioAdds.py")
                          
        print( ">>> testFioRecorder.test_createFio, DONE")
        return 


if __name__ == "__main__":
    unittest.main()

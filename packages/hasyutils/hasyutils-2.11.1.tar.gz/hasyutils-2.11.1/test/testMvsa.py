#!/usr/bin/env python
'''
$ python3 -m unittest discover -v
python3 ./test/testMvsa.py testMvsa.testMvsa
'''
import unittest, sys, os, time
import HasyUtils
import PyTango

class testMvsa( unittest.TestCase):

    @classmethod
    def setUpClass( clss):
    
        if not HasyUtils.unitTestChecks( "%s.setupClass" % clss):
            sys.exit( 255) 

    @classmethod
    def tearDownClass( clss): 

        if not HasyUtils.unitTestChecks( "%s.tearDownClass" % clss):
            sys.exit( 255) 

        return 

    def testMvsa( self):
        '''
        the gitlab-runner has no DISPLAY set, normally but it can be done
        '''
        if os.getenv( "DISPLAY") is None: 
            print( "\n***\n*** testMvsa: no DISPLAY, return\n***")
            return 1

        print( "\n>>>testMvsa.testMvsa, BEGIN")

        door = PyTango.DeviceProxy( HasyUtils.getDoorNames()[0])
        if door.state() != PyTango.DevState.ON: 
            print( "testMvsa.testMvsa: door is not ON %s" % repr( door.state()))
            sys.exit( 255) 

        HasyUtils.stopPyspMonitors()
        
        HasyUtils.setEnv( "ActiveMntGrp", "mg_pysp")
        (status, wasLaunched) = HasyUtils.assertProcessRunning( '/usr/bin/pyspMonitor.py')
        if not status: 
            print( "testMvsa.testMvsa: trouble launching pyspMonitor.py")
            return

        exp_dmy01 = PyTango.DeviceProxy( "exp_dmy01")

        #  ascan exp_dmy01 0 1 49 0.1
        door.runmacro( [ "ascan", "exp_dmy01", "0", "1", "49", "0.1"])

        startTime = time.time()
        while door.state() == PyTango.DevState.RUNNING: 
            print( "testMvsa: ascan is RUNNING")
            time.sleep(3)
            # 25.4.2023: 45 -> 80
            if (time.time() - startTime) > 80: 
                print( "testMvsa.testMvsa: ascan takes too much time %g ( > 8s )" % (time.time() - startTime))
                return 
                
        temp = HasyUtils.createScanInfo()
        self.assertEqual( temp[ 'motors'][0]['name'], 'exp_dmy01')
        self.assertEqual( temp[ 'motors'][0]['start'], 0.)
        self.assertEqual( temp[ 'motors'][0]['stop'], 1.0)
        self.assertEqual( temp[ 'title'], 'ascan exp_dmy01 0.0 1.0 49 0.1' )
        self.assertEqual( temp[ 'intervals'], 49)
        self.assertEqual( temp[ 'nPts'], 50)
        self.assertEqual( temp[ 'sampleTime'], 0.1)

        print( "door %s" % door.state())

        HasyUtils.toPyspMonitor( {'command': ['cls', 'display sig_gen']})
        HasyUtils.setEnv( "SignalCounter", "sig_gen")

        dct = { 'peak': 0.48979591, 
                'cms': 0.5068027, 
                'cen': 0.506803, 
                'peakssa': 0.5102040, 
                'cmsssa': 0.506803, 
                'censsa': 0.506731}

        for mode in [ 'peak', 'cms', 'cen', 
                      'peakssa', 'cmsssa', 'censsa']: 

            print( "mode %s" % mode)
            door.runmacro( [ "mv", "exp_dmy01", "1"])
            time.sleep( 0.5) 
            startTime = time.time()
            while door.state() == PyTango.DevState.RUNNING: 
                print( "mvsa ist running")
                time.sleep(1)
                if (time.time() - startTime) > 3: 
                    print( "testMvsa.testMvsa: mv takes too much time %g ( > 3s)" % (time.time() - startTime))
                    return 

            door.runmacro( [ "mvsa", mode, "0"])
            time.sleep( 0.5) 
            startTime = time.time()
            while door.state() == PyTango.DevState.RUNNING: 
                print( "mvsa ist running, %s" % repr( mode))
                time.sleep(1)
                if (time.time() - startTime) > 3: 
                    print( "testMvsa.testMvsa: mvsa takes too much time %g ( > 3s)" % (time.time() - startTime))
                    return 

            #self.assertAlmostEqual( dct[ mode], exp_dmy01.position, 4)

        HasyUtils.toPyspMonitor( {'command': ['cls', 'display step_gen']})
        HasyUtils.setEnv( "SignalCounter", "step_gen")
        dct = { 'step': 0.510204, 
                'stepc': 0.511278, 
                'stepm': 0.513033, 
                'stepssa': 0.5102040, 
                'stepcssa': 0.511924, 
                'stepmssa': 0.470115}
        for mode in [ 'step', 'stepc', 'stepm', 
                      'stepssa', 'stepcssa', 'stepmssa']: 

            print( "mode %s" % mode)
            door.runmacro( [ "mv", "exp_dmy01", "1"])
            time.sleep( 0.5)
            startTime = time.time()
            while door.state() == PyTango.DevState.RUNNING: 
                print( "mvsa ist running")
                time.sleep(1)
                if (time.time() - startTime) > 3: 
                    print( "testMvsa.testMvsa: mvsa-2 takes too much time %g ( > 3s)" % (time.time() - startTime))
                    return 

            door.runmacro( [ "mvsa", mode, "0"])
            time.sleep( 0.5)
            startTime = time.time()
            while door.state() == PyTango.DevState.RUNNING: 
                print( "mvsa ist running, %s" % repr( mode))
                time.sleep(1)
                if (time.time() - startTime) > 3: 
                    print( "testMvsa.testMvsa: mvsa-3 takes too much time %g ( > 3s)" % (time.time() - startTime))
                    return 

            #self.assertAlmostEqual( dct[ mode], exp_dmy01.position, 4)

        HasyUtils.toPyspMonitor( {'command': ['cls', 'display dip_gen']})
        HasyUtils.setEnv( "SignalCounter", "dip_gen")
        dct = { 'dip': 0.510204, 
                'dipc': 0.511278, 
                'dipm': 0.513033, 
                'dipssa': 0.5102040, 
                'dipcssa': 0.511924, 
                'dipmssa': 0.470115}
        for mode in [ 'dip', 'dipc', 'dipm', 
                      'dipssa', 'dipcssa', 'dipmssa']: 

            print( "mode %s" % mode)
            door.runmacro( [ "mv", "exp_dmy01", "1"])
            time.sleep( 0.5)
            startTime = time.time()
            while door.state() == PyTango.DevState.RUNNING: 
                print( "mvsa ist running")
                time.sleep(1)
                if (time.time() - startTime) > 3: 
                    print( "testMvsa.testMvsa: mv-2 takes too much time %g ( > 3s)" % (time.time() - startTime))
                    return 

            door.runmacro( [ "mvsa", mode, "0"])
            time.sleep( 0.5)
            startTime = time.time()
            while door.state() == PyTango.DevState.RUNNING: 
                print( "mvsa ist running, %s" % repr( mode))
                time.sleep(1)
                if (time.time() - startTime) > 3: 
                    print( "testMvsa.testMvsa: mvsa-3 takes too much time %g ( > 3s)" % (time.time() - startTime))
                    return 

            #self.assertAlmostEqual( dct[ mode], exp_dmy01.position, 4)

        #self.assertTrue( ret)
        #self.assertEqual( p.state(), PyTango.DevState.ON)

        HasyUtils.setEnv( "SignalCounter", "sig_gen")
        HasyUtils.setEnv( "ActiveMntGrp", "mg_ivp")

        HasyUtils.stopPyspMonitors()

        print( ">>>testMvsa.testMvsa, DONE")
        
        return


if __name__ == "__main__":
    unittest.main()

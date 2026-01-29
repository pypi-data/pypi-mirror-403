#!/usr/bin/env python
'''
$ python -m unittest discover -v
python ./test/testDiffractometer.py testDiffractometer.testDiffractometer
python3 ./test/testDiffractometer.py testDiffractometer.testDiffractometer
'''
import unittest, sys, os, time
import HasyUtils
import PyTango

class testDiffractometer( unittest.TestCase):

    @classmethod
    def setUpClass( clss):

        if not HasyUtils.unitTestChecks( "%s.setupClass" % clss):
            sys.exit( 255) 

    @classmethod
    def tearDownClass( clss): 
        if not HasyUtils.unitTestChecks( "%s.tearDownClass" % clss):
            sys.exit( 255) 

    def testDiffractometer( self):
        '''
        '''
        print( "\ntestDiffractometer.testDiffractometer, BEGIN")

        door = PyTango.DeviceProxy( HasyUtils.getDoorNames()[0])

        if door.state() != PyTango.DevState.ON: 
            print( "testDiffractometer.testDiffractometer: door is not ON %s" % repr( door.state()))
            return 
        diffOld = HasyUtils.getEnv( "DiffracDevice")
        print( "testDiffractometer: storing %s" % diffOld)
        #
        # let's see whether all diffractometers are alive
        #
        diffList = [ 
            #{ 'diff': "controller/diffrac6cp23/e6c", 'Psi':  'pm/e6c/4'}, 
            { 'diff': "controller/diffrace6c/e6cctrleh1", 'Psi':  'pm/e6cctrleh1/4'}, 
            #{ 'diff': "controller/diffrac6c/e6cctrleh2", 'Psi':  None},
            #{ 'diff': "controller/diffrace6c/e6cctrltk", 'Psi':  'pm/e6cctrltk/4'}, 
            #{ 'diff': "controller/diffrace6c/kozhue6cctrl", 'Psi': None},  
       #     { 'diff': "controller/diffrace4c/e4chctrl", 'Psi': 'pm/e4chctrl/4'}, 
            #{ 'diff': "controller/diffrac4cp23/h4c", 'Psi':  'pm/h4c/1'},  # failes under debian-10
        ]
        for hsh in diffList:

            print( "testDiffractometer.testDiffractometer, checking %s" % hsh[ 'diff'])
            #
            #
            #
            if hsh[ 'diff'].find( "4cp23") > 0 and \
               HasyUtils.getHostname() == 'haso107d1': 
                print( "testDiffractometer.testDiffractometer, %s failes under Debian-10" % hsh[ 'diff'])
                continue

            HasyUtils.setEnv( "DiffracDevice", hsh[ 'diff']) 
            ctrl = PyTango.DeviceProxy( hsh[ 'diff'])
            self.assertEqual( ctrl.state(), PyTango.DevState.ON)
            
            if hsh[ 'Psi'] is not None: 
                HasyUtils.setEnv( "Psi", hsh[ 'Psi']) 
                psi = PyTango.DeviceProxy( hsh[ 'Psi'])
                self.assertEqual( psi.state(), PyTango.DevState.ON)
            else: 
                HasyUtils.unsetEnv( "Psi")

            door.runmacro( [ "wh"])
            #
            # need some time to enter RUNNING state
            #
            time.sleep(0.1)
            while door.state() == PyTango.DevState.RUNNING: 
                time.sleep(0.5)

            self.assertEqual( door.state(), PyTango.DevState.ON)


        print( "testDiffractometer: re-storing %s" % diffOld)
            
        HasyUtils.setEnv( "DiffracDevice", diffOld) 
            
        print( "testDiffractometer.testDiffractometer, DONE")
        
        return


if __name__ == "__main__":
    unittest.main()

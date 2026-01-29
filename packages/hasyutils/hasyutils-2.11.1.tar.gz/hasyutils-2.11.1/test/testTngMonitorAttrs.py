#!/bin/env python
'''
$ python -m unittest discover -v
python3 ./test/testTngMonitorAttrs.py testTngMonitorAttrs.test_tngMonitorAttrs
'''
import unittest, sys, os, time
import HasyUtils
import PyTango
from HasyUtils.pyqtSelector import *

class testTngMonitorAttrs( unittest.TestCase):

    @classmethod
    def setUpClass( clss):
    
        if not HasyUtils.unitTestChecks( "%s.setupClass" % clss):
            sys.exit( 255) 

    @classmethod
    def tearDownClass( clss): 

        if not HasyUtils.unitTestChecks( "%s.tearDownClass" % clss):
            sys.exit( 255) 

    def test_tngMonitorAttrs( self):
        '''
        '''
        print( "\ntestTngMonitorAttrs, BEGIN")

        app = QApplication.instance()
        if app is None: 
            app = QApplication(sys.argv)

        #w = HasyUtils.tngMonitorAttrs( attrs = ['haso107d10:10000/petra/globals/keyword/BeamCurrent PetraCurrent'])
        w = HasyUtils.tngMonitorAttrs.monitorMenu( app = app, attrs = 
                                                   ['haso107d10:10000/petra/globals/keyword/BeamCurrent PetraCurrent',
                                                    'haso107d10:10000/petra/globals/keyword/BeamLifetime BeamLifetime'])
        w.show()

        w.logWidget.append( "Read some data, 3s") 

        for i in range( 30): 
            app.processEvents()
            time.sleep( 0.1)

        w.logWidget.append( "Change ScanDir") 
        o = w.cb_scanDir()
        for i in range( 20): 
            app.processEvents()
            time.sleep( 0.1)
        w.logWidget.append( "Scandir to /tmp") 
        o.scanDirLine.setText( "/tmp")
        for i in range( 20): 
            app.processEvents()
            time.sleep( 0.1)
        o.cb_applyScanDir()

        for i in range( 20): 
            app.processEvents()
            time.sleep( 0.1)
        w.logWidget.append( "Scandir to /home/kracht/temp") 
        o.scanDirLine.setText( "/home/kracht/temp")
        for i in range( 20): 
            app.processEvents()
            time.sleep( 0.1)
        o.cb_applyScanDir()
        for i in range( 50): 
            app.processEvents()
            time.sleep( 0.1)
        w.logWidget.append( "Closing ScanDir widget") 
        o.close()
        
        app.exit()
        print( "\ntestTngMonitorAttrs, END")
        
        return

if __name__ == "__main__":
    unittest.main()


#!/bin/env python
'''
$ python3 -m unittest discover -v
python3 ./test/testMsUtils.py testMsUtils.test_dataRecordToScanInfo
python3 ./test/testMsUtils.py testMsUtils.test_dataRecordToScanInfo2
python3 ./test/testMsUtils.py testMsUtils.test_scanTitleToScanInfo
python3 ./test/testMsUtils.py testMsUtils.test_import
python3 ./test/testMsUtils.py testMsUtils.test_mg1
'''
import unittest, sys, os, time
import HasyUtils
import HasyUtils.MgUtils
import PyTango

class testMsUtils( unittest.TestCase):

    @classmethod
    def setUpClass( clss):
    
        if not HasyUtils.unitTestChecks( "%s.setupClass" % clss):
            sys.exit( 255) 

    @classmethod
    def tearDownClass( clss): 

        if not HasyUtils.unitTestChecks( "%s.tearDownClass" % clss):
            sys.exit( 255) 

    def test_scanTitleToScanInfo(  self):
        """
        """
        print( "\n>>> test_scanTitleToScanInfo BEGIN")
        
        #
        # for dscan
        #
        HasyUtils.runMacro( "mv exp_dmy01 1") 
        HasyUtils.runMacro( "mv exp_dmy02 2") 
        HasyUtils.runMacro( "mv exp_dmy03 3") 

        scanInfo = {}
        scanInfo[ 'motors'] = []
        scanInfo[ 'title'] = "ascan exp_dmy01 0 1 10 0.1"
        HasyUtils.scanTitleToScanInfo( scanInfo[ 'title'], scanInfo)
        self.assertEqual( scanInfo[ 'sampleTime'], 0.1)
        self.assertEqual( scanInfo[ 'intervals'], 10)
        self.assertEqual( scanInfo[ 'nPts'], 11)
        self.assertEqual( scanInfo[ 'motors'][0][ 'name'], 'exp_dmy01')
        self.assertEqual( scanInfo[ 'motors'][0][ 'start'], 0.0)
        self.assertEqual( scanInfo[ 'motors'][0][ 'stop'], 1.0)

        scanInfo = {}
        scanInfo[ 'motors'] = []
        scanInfo[ 'title'] = "a2scan exp_dmy01 0 1 exp_dmy02 2 4 10 0.1"
        HasyUtils.scanTitleToScanInfo( scanInfo[ 'title'], scanInfo)
        self.assertEqual( scanInfo[ 'sampleTime'], 0.1)
        self.assertEqual( scanInfo[ 'intervals'], 10)
        self.assertEqual( scanInfo[ 'nPts'], 11)
        self.assertEqual( scanInfo[ 'motors'][0][ 'name'], 'exp_dmy01')
        self.assertEqual( scanInfo[ 'motors'][0][ 'start'], 0.0)
        self.assertEqual( scanInfo[ 'motors'][0][ 'stop'], 1.0)
        self.assertEqual( scanInfo[ 'motors'][1][ 'name'], 'exp_dmy02')
        self.assertEqual( scanInfo[ 'motors'][1][ 'start'], 2.0)
        self.assertEqual( scanInfo[ 'motors'][1][ 'stop'], 4.0)

        scanInfo = {}
        scanInfo[ 'motors'] = []
        scanInfo[ 'title'] = "a3scan exp_dmy01 0 1 exp_dmy02 2 4 exp_dmy03 10 11 10 0.1"
        HasyUtils.scanTitleToScanInfo( scanInfo[ 'title'], scanInfo)
        self.assertEqual( scanInfo[ 'sampleTime'], 0.1)
        self.assertEqual( scanInfo[ 'intervals'], 10)
        self.assertEqual( scanInfo[ 'nPts'], 11)
        self.assertEqual( scanInfo[ 'motors'][0][ 'name'], 'exp_dmy01')
        self.assertEqual( scanInfo[ 'motors'][0][ 'start'], 0.0)
        self.assertEqual( scanInfo[ 'motors'][0][ 'stop'], 1.0)
        self.assertEqual( scanInfo[ 'motors'][1][ 'name'], 'exp_dmy02')
        self.assertEqual( scanInfo[ 'motors'][1][ 'start'], 2.0)
        self.assertEqual( scanInfo[ 'motors'][1][ 'stop'], 4.0)
        self.assertEqual( scanInfo[ 'motors'][2][ 'name'], 'exp_dmy03')
        self.assertEqual( scanInfo[ 'motors'][2][ 'start'], 10.0)
        self.assertEqual( scanInfo[ 'motors'][2][ 'stop'], 11.0)

        scanInfo = {}
        scanInfo[ 'motors'] = []
        scanInfo[ 'title'] = "ascan_repeat exp_dmy01 0 1 10 0.1 15"
        HasyUtils.scanTitleToScanInfo( scanInfo[ 'title'], scanInfo)
        self.assertEqual( scanInfo[ 'sampleTime'], 0.1)
        self.assertEqual( scanInfo[ 'intervals'], 10)
        self.assertEqual( scanInfo[ 'nPts'], 11)
        self.assertEqual( scanInfo[ 'repeats'], 15)
        self.assertEqual( scanInfo[ 'motors'][0][ 'name'], 'exp_dmy01')
        self.assertEqual( scanInfo[ 'motors'][0][ 'start'], 0.0)
        self.assertEqual( scanInfo[ 'motors'][0][ 'stop'], 1.0)

        scanInfo = {}
        scanInfo[ 'motors'] = []
        scanInfo[ 'title'] = "hscan 1.0 1.1 20 0.1"
        HasyUtils.scanTitleToScanInfo( scanInfo[ 'title'], scanInfo)
        self.assertEqual( scanInfo[ 'sampleTime'], 0.1)
        self.assertEqual( scanInfo[ 'intervals'], 20)
        self.assertEqual( scanInfo[ 'nPts'], 21)
        hostname = HasyUtils.getHostname()
        self.assertEqual( scanInfo[ 'motors'][0][ 'name'], 'e6cctrl_h')

        self.assertEqual( scanInfo[ 'motors'][0][ 'start'], 1.0)
        self.assertEqual( scanInfo[ 'motors'][0][ 'stop'], 1.1)

        scanInfo = {}
        scanInfo[ 'motors'] = []
        scanInfo[ 'title'] = "kscan 1.0 1.1 20 0.1"
        HasyUtils.scanTitleToScanInfo( scanInfo[ 'title'], scanInfo)
        self.assertEqual( scanInfo[ 'sampleTime'], 0.1)
        self.assertEqual( scanInfo[ 'intervals'], 20)
        self.assertEqual( scanInfo[ 'nPts'], 21)
        self.assertEqual( scanInfo[ 'motors'][0][ 'name'], 'e6cctrl_k')
        self.assertEqual( scanInfo[ 'motors'][0][ 'start'], 1.0)
        self.assertEqual( scanInfo[ 'motors'][0][ 'stop'], 1.1)

        scanInfo = {}
        scanInfo[ 'motors'] = []
        scanInfo[ 'title'] = "lscan 1.0 1.1 20 0.1"
        HasyUtils.scanTitleToScanInfo( scanInfo[ 'title'], scanInfo)
        self.assertEqual( scanInfo[ 'sampleTime'], 0.1)
        self.assertEqual( scanInfo[ 'intervals'], 20)
        self.assertEqual( scanInfo[ 'nPts'], 21)
        self.assertEqual( scanInfo[ 'motors'][0][ 'name'], 'e6cctrl_l')
        self.assertEqual( scanInfo[ 'motors'][0][ 'start'], 1.0)
        self.assertEqual( scanInfo[ 'motors'][0][ 'stop'], 1.1)

        scanInfo = {}
        scanInfo[ 'motors'] = []
        scanInfo[ 'title'] = "hklscan 1.0 1.1 2.0 2.2 3.0 3.3 20 0.1"
        HasyUtils.scanTitleToScanInfo( scanInfo[ 'title'], scanInfo)
        self.assertEqual( scanInfo[ 'sampleTime'], 0.1)
        self.assertEqual( scanInfo[ 'intervals'], 20)
        self.assertEqual( scanInfo[ 'nPts'], 21)
        self.assertEqual( scanInfo[ 'motors'][0][ 'name'], 'e6cctrl_l')
        self.assertEqual( scanInfo[ 'motors'][0][ 'start'], 3.0)
        self.assertEqual( scanInfo[ 'motors'][0][ 'stop'], 3.3)
        self.assertEqual( scanInfo[ 'motors'][1][ 'name'], 'e6cctrl_h')
        self.assertEqual( scanInfo[ 'motors'][1][ 'start'], 1.0)
        self.assertEqual( scanInfo[ 'motors'][1][ 'stop'], 1.1)
        self.assertEqual( scanInfo[ 'motors'][2][ 'name'], 'e6cctrl_k')
        self.assertEqual( scanInfo[ 'motors'][2][ 'start'], 2.0)
        self.assertEqual( scanInfo[ 'motors'][2][ 'stop'], 2.2) 

        scanInfo = {}
        scanInfo[ 'motors'] = []
        scanInfo[ 'title'] = "dscan exp_dmy01 -1 1 20 0.1"
        HasyUtils.scanTitleToScanInfo( scanInfo[ 'title'], scanInfo)
        self.assertEqual( scanInfo[ 'sampleTime'], 0.1)
        self.assertEqual( scanInfo[ 'intervals'], 20)
        self.assertEqual( scanInfo[ 'nPts'], 21)
        self.assertEqual( scanInfo[ 'motors'][0][ 'name'], 'exp_dmy01')
        self.assertEqual( scanInfo[ 'motors'][0][ 'start'], 0.0)
        self.assertEqual( scanInfo[ 'motors'][0][ 'stop'], 2.0)

        scanInfo = {}
        scanInfo[ 'motors'] = []
        scanInfo[ 'title'] = "d2scan exp_dmy01 -1 1 exp_dmy02 -0.5 0.5 20 0.1"
        HasyUtils.scanTitleToScanInfo( scanInfo[ 'title'], scanInfo)
        self.assertEqual( scanInfo[ 'sampleTime'], 0.1)
        self.assertEqual( scanInfo[ 'intervals'], 20)
        self.assertEqual( scanInfo[ 'nPts'], 21)
        self.assertEqual( scanInfo[ 'motors'][0][ 'name'], 'exp_dmy01')
        self.assertEqual( scanInfo[ 'motors'][0][ 'start'], 0.0)
        self.assertEqual( scanInfo[ 'motors'][0][ 'stop'], 2.0)
        self.assertEqual( scanInfo[ 'motors'][1][ 'name'], 'exp_dmy02')
        self.assertEqual( scanInfo[ 'motors'][1][ 'start'], 1.5)
        self.assertEqual( scanInfo[ 'motors'][1][ 'stop'], 2.5)

        scanInfo = {}
        scanInfo[ 'motors'] = []
        scanInfo[ 'title'] = "d3scan exp_dmy01 -1 1 exp_dmy02 -0.5 0.5 exp_dmy03 -0.1 0.1 20 0.1"
        HasyUtils.scanTitleToScanInfo( scanInfo[ 'title'], scanInfo)
        self.assertEqual( scanInfo[ 'sampleTime'], 0.1)
        self.assertEqual( scanInfo[ 'intervals'], 20)
        self.assertEqual( scanInfo[ 'nPts'], 21)
        self.assertEqual( scanInfo[ 'motors'][0][ 'name'], 'exp_dmy01')
        self.assertEqual( scanInfo[ 'motors'][0][ 'start'], 0.0)
        self.assertEqual( scanInfo[ 'motors'][0][ 'stop'], 2.0)
        self.assertEqual( scanInfo[ 'motors'][1][ 'name'], 'exp_dmy02')
        self.assertEqual( scanInfo[ 'motors'][1][ 'start'], 1.5)
        self.assertEqual( scanInfo[ 'motors'][1][ 'stop'], 2.5)
        self.assertEqual( scanInfo[ 'motors'][2][ 'name'], 'exp_dmy03')
        self.assertEqual( scanInfo[ 'motors'][2][ 'start'], 2.9)
        self.assertEqual( scanInfo[ 'motors'][2][ 'stop'], 3.1)


        scanInfo = {}
        scanInfo[ 'motors'] = []
        scanInfo[ 'title'] = "dscan_repeat exp_dmy01 -1 1 10 0.1 15"
        HasyUtils.scanTitleToScanInfo( scanInfo[ 'title'], scanInfo)
        self.assertEqual( scanInfo[ 'sampleTime'], 0.1)
        self.assertEqual( scanInfo[ 'intervals'], 10)
        self.assertEqual( scanInfo[ 'nPts'], 11)
        self.assertEqual( scanInfo[ 'repeats'], 15)
        self.assertEqual( scanInfo[ 'motors'][0][ 'name'], 'exp_dmy01')
        self.assertEqual( scanInfo[ 'motors'][0][ 'start'], 0.0)
        self.assertEqual( scanInfo[ 'motors'][0][ 'stop'], 2.0)

        scanInfo = {}
        scanInfo[ 'motors'] = []
        scanInfo[ 'title'] = "mesh exp_dmy01 0 1 10 exp_dmy02 1 2 20 0.1"
        HasyUtils.scanTitleToScanInfo( scanInfo[ 'title'], scanInfo)
        self.assertEqual( scanInfo[ 'sampleTime'], 0.1)
        self.assertEqual( scanInfo[ 'nPts'], 231)
        self.assertEqual( scanInfo[ 'motors'][0][ 'name'], 'exp_dmy01')
        self.assertEqual( scanInfo[ 'motors'][0][ 'start'], 0.0)
        self.assertEqual( scanInfo[ 'motors'][0][ 'stop'], 1.0)
        self.assertEqual( scanInfo[ 'motors'][0][ 'intervals'], 10)
        self.assertEqual( scanInfo[ 'motors'][1][ 'name'], 'exp_dmy02')
        self.assertEqual( scanInfo[ 'motors'][1][ 'start'], 1.0)
        self.assertEqual( scanInfo[ 'motors'][1][ 'stop'], 2.0)
        self.assertEqual( scanInfo[ 'motors'][1][ 'intervals'], 20)

        scanInfo = {}
        scanInfo[ 'motors'] = []
        scanInfo[ 'title'] = "dmesh exp_dmy01 -1 1 10 exp_dmy02 -1 2 20 0.1"
        HasyUtils.scanTitleToScanInfo( scanInfo[ 'title'], scanInfo)
        self.assertEqual( scanInfo[ 'sampleTime'], 0.1)
        self.assertEqual( scanInfo[ 'nPts'], 231)
        self.assertEqual( scanInfo[ 'motors'][0][ 'name'], 'exp_dmy01')
        self.assertEqual( scanInfo[ 'motors'][0][ 'start'], 0.0)
        self.assertEqual( scanInfo[ 'motors'][0][ 'stop'], 2.0)
        self.assertEqual( scanInfo[ 'motors'][0][ 'intervals'], 10)
        self.assertEqual( scanInfo[ 'motors'][1][ 'name'], 'exp_dmy02')
        self.assertEqual( scanInfo[ 'motors'][1][ 'start'], 1.0)
        self.assertEqual( scanInfo[ 'motors'][1][ 'stop'], 4.0)
        self.assertEqual( scanInfo[ 'motors'][1][ 'intervals'], 20)

        scanInfo = {}
        scanInfo[ 'motors'] = []
        scanInfo[ 'title'] = "fscan np=1500 0.1 exp_dmy01 exp_dmy02"
        HasyUtils.scanTitleToScanInfo( scanInfo[ 'title'], scanInfo)
        self.assertEqual( scanInfo[ 'sampleTime'], 0.1)
        self.assertEqual( scanInfo[ 'nPts'], 2253001)
        self.assertEqual( scanInfo[ 'motors'][0][ 'name'], 'exp_dmy01')
        self.assertEqual( scanInfo[ 'motors'][0][ 'start'], 0.0)
        self.assertEqual( scanInfo[ 'motors'][0][ 'stop'], 100.0)
        self.assertEqual( scanInfo[ 'motors'][0][ 'intervals'], 1500)
        self.assertEqual( scanInfo[ 'motors'][1][ 'name'], 'exp_dmy02')
        self.assertEqual( scanInfo[ 'motors'][1][ 'start'], 0.0)
        self.assertEqual( scanInfo[ 'motors'][1][ 'stop'], 100.0)
        self.assertEqual( scanInfo[ 'motors'][1][ 'intervals'], 1500)

        print( ">>> test_scanTitleToScanInfo, DONE")
        return 

    def test_import(  self):
        """
        """
        hostname = HasyUtils.getHostname()

        print( "\n>>> test_import BEGIN")
        
        ret = HasyUtils.testImport( "./test/tstImportOK")
        self.assertEqual( ret[0], True)
        ret = HasyUtils.testImport( "./test/tstImportFail")
        self.assertEqual( ret[0], False)

        print( ">>> test_import, DONE")
        return 

    def test_mg1(  self):
        """
        """
        print( "\n>>> test_mg1, BEGIN")
        hostname = HasyUtils.getHostname()

        HasyUtils.runMacro( "change_mg -g mg_unittest -t eh_t01 -c eh_c01,sig_gen,eh_c02")
        print( ">>> test_mg1, (1)")

        ret = HasyUtils.testImport( "./test/tstImportOK")
        self.assertEqual( ret[0], True)
        print( ">>> test_mg1, (2)")
        ret = HasyUtils.testImport( "./test/tstImportFail")
        self.assertEqual( ret[0], False)

        print( ">>> test_mg1, DONE")
        return 

if __name__ == "__main__":
    unittest.main()

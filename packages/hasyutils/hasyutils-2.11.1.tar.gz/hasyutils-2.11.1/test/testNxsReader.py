#!/bin/env python3
'''
$ python3 -m unittest discover -v

cd test
$ python3 -m unittest testNxsReader

python3 ./test/testNxsReader.py testNxsReader.test_nxspni
python3 ./test/testNxsReader.py testNxsReader.test_nxsTDCpni
python3 ./test/testNxsReader.py testNxsReader.test_nxsh5py
python3 ./test/testNxsReader.py testNxsReader.test_nxsTDCh5py
'''
import unittest, sys, os, time
import HasyUtils
import PyTango
import numpy

class testNxsReader( unittest.TestCase):

    @classmethod
    def setUpClass( clss):
    
        if not HasyUtils.unitTestChecks( "%s.setupClass" % clss):
            sys.exit( 255) 

    @classmethod
    def tearDownClass( clss): 

        if not HasyUtils.unitTestChecks( "%s.tearDownClass" % clss):
            sys.exit( 255) 

    def test_nxspni( self):

        print( "\n>>> testNxsReader.test_nxspni, BEGIN")

        with self.assertRaises( Exception) as context:
            o = HasyUtils.pniReader( "unitTestttt.nxs")
        #print("test_fileh5: %s" %  str(context.exception))
        self.assertEqual( str(context.exception) == 'pniReader.__init__: unitTestttt.nxs does not exist', True) 

        o = HasyUtils.pniReader( "./test/unitTestNeXus.nxs")

        self._testNxsObj( o)
        
        print( ">>> testNxsReader.test_nxspni, DONE")

        return

    def test_nxsTDCpni( self):

        print( "\n>>> testNxsReader.test_nxsTDCpni, BEGIN")

        o = HasyUtils.pniReader( "./test/unitTestTDCNeXus.nxs")

        self._testNxsTDCObj( o)
        
        print( ">>> testNxsReader.test_nxsTDCpni, DONE")

        return
    
    def test_nxsh5py( self):

        print( "\n>>> testNxsReader.test_nxsh5py, BEGIN")

        with self.assertRaises( Exception) as context:
            o = HasyUtils.h5pyReader( "unitTestt.nxs")
        #print("test_fileh5: %s" %  str(context.exception))
        self.assertEqual( str(context.exception) == 'h5pyReader.__init__: unitTestt.nxs does not exist', True) 

        o = HasyUtils.h5pyReader( "./test/unitTestNeXus.nxs")

        self._testNxsObj( o)

        print( ">>> testNxsReader.test_nxsh5py, DONE")

        return
    
    def test_nxsTDCh5py( self):

        print( "\n>>> testNxsReader.test_nxsTDCh5py, BEGIN")

        o = HasyUtils.h5pyReader( "./test/unitTestTDCNeXus.nxs")

        self._testNxsTDCObj( o)

        print( ">>> testNxsReader.test_nxshTDC5py, DONE")

        return

    def _testNxsObj( self, o): 

        #[ print( line) for line in o.display()]

        lst = o.getDatasetNames()
        self.assertEqual( len( lst), 149)

        lst = o.getDatasetNames1D()

        self.assertEqual( len( lst), 7)
        #
        # the order of the datasets is different for nxspni and hypy.
        #
        for node in ['/scan/instrument/collection/point_nb', 
                     '/scan/instrument/collection/exp_dmy01', 
                     '/scan/instrument/collection/sig_gen', 
                     '/scan/instrument/collection/timestamp', 
                     '/scan/instrument/collection/eh_t01', 
                     '/scan/instrument/detector/collection/eh_c02', 
                     '/scan/instrument/detector/collection/eh_c01']: 
            ret = node in lst
            self.assertEqual( ret, True)
            

        lst = o.getDatasetObjs()
        self.assertEqual( len( lst), 149)

        lst = o.getDatasetNamesInfo()
        self.assertEqual( len( lst), 149)
        
        ds = o.getDataset( '/scan/instrument/detector/collection/eh_c01')
        self.assertEqual( type( ds), numpy.ndarray)
        self.assertEqual( len( ds), 51)
        self.assertEqual( ds.shape[0], 51)
        
        ds = o.getDataset( '/scan/instrument/source/name')

        if type( ds) == bytes:
            self.assertEqual( type( ds), bytes)
            self.assertEqual( len( ds), 9)
            self.assertEqual( ds, b'PETRA III')
        else: 
            self.assertEqual( type( ds), numpy.ndarray)
            self.assertEqual( len( ds[0]), 9)
            self.assertEqual( ds[0], 'PETRA III')
        
        ds = o.getDataset( '/scan/experiment_identifier')
        if type( ds) == bytes:
            self.assertEqual( type( ds), bytes)
            self.assertEqual( ds, b'P09_2022-10-18T13:24:02.430609+0200@haso107d10')
        else: 
            self.assertEqual( type( ds), numpy.ndarray)
            self.assertEqual( ds[0], 'P09_2022-10-18T13:24:02.430609+0200@haso107d10')

        lst = o.getAttributeNames()
        self.assertEqual( len( lst), 738)

        ret = o.getAttributeValue( '/scan/title', 'type')
        self.assertEqual( ret, 'NX_CHAR')

        ret = o.getAttributeValue( "/scan/program_name", "scan_command")
        self.assertEqual( ret, 'ascan exp_dmy01 0.0 10.0 50 0.1')

        obj = o.getDatasetObj( '/scan/data/eh_c01')
        self.assertEqual( obj.linkType, "SOFT")
        self.assertEqual( obj.linkTarget, "/scan/instrument/detector/collection/eh_c01")
        self.assertEqual( type( obj.data), numpy.ndarray)
        self.assertAlmostEqual( obj.data[1], 0.1899712180, 5)

        obj = o.getDatasetObj( "/scan/instrument/detector/collection/eh_c01")
        self.assertEqual( obj.linkType, "HARD")
        self.assertEqual( obj.linkTarget, None) 
        self.assertEqual( type( obj.data), numpy.ndarray)
        self.assertAlmostEqual( obj.data[1], 0.1899712180, 5)

        ds = o.getDataset( '/scan/data/eh_c01')
        self.assertEqual( type( ds), numpy.ndarray)
        self.assertAlmostEqual( ds[1], 0.1899712180, 5)

        return 

    def _testNxsTDCObj( self, o): 

        #[ print( line) for line in o.display()]

        lst = o.getDatasetNames()
        self.assertEqual( len( lst), 61)

        lst = o.getDatasetNames1D()
        self.assertEqual( len( lst), 9)
        #
        # the order of the datasets is different for nxspni and hypy.
        #
        for node in ['/scan/instrument/collection/coboldctrl',
                     '/scan/instrument/collection/countscoboldch01',
                     '/scan/instrument/collection/countscoboldch11',
                     '/scan/instrument/collection/countscoboldch12',
                     '/scan/instrument/collection/countscoboldch13',
                     '/scan/instrument/collection/dgg1',
                     '/scan/instrument/collection/mono1',
                     '/scan/instrument/collection/point_nb',
                     '/scan/instrument/collection/timestamp']: 
            ret = node in lst
            self.assertEqual( ret, True)
            

        lst = o.getDatasetObjs()
        self.assertEqual( len( lst), 61)

        lst = o.getDatasetNamesInfo()
        self.assertEqual( len( lst), 61)
        
        ds = o.getDataset( '/scan/instrument/collection/coboldctrl')
        self.assertEqual( type( ds), numpy.ndarray)
        self.assertEqual( len( ds), 34)
        self.assertEqual( ds.shape[0], 34)
        
        ds = o.getDataset( "/scan/title")

        if type( ds) == bytes:
            self.assertEqual( type( ds), bytes)
            self.assertEqual( len( ds), 3)
            self.assertEqual( ds, b'tst')
        else: 
            self.assertEqual( type( ds), numpy.ndarray)
            self.assertEqual( len( ds[0]), 3)
            self.assertEqual( ds[0], 'tst')
        
        lst = o.getAttributeNames()
        self.assertEqual( len( lst), 245)

        ret = o.getAttributeValue( '/scan/title', 'type')
        self.assertEqual( ret, 'NX_CHAR')

        ret = o.getAttributeValue( "/scan/program_name", "scan_command")
        self.assertEqual( ret, 'ascan mono1 400.0 499.0 33 60.0')

        lst = o.getDatasetNames2D()
        self.assertEqual( len( lst), 4)
        
        #
        # the order of the datasets is different for nxspni and hypy.
        #
        for node in ['/scan/instrument/histogram_ch01/data',
                     '/scan/instrument/histogram_ch11/data',
                     '/scan/instrument/histogram_ch12/data',
                     '/scan/instrument/histogram_ch13/data']:
            ret = node in lst
            self.assertEqual( ret, True)

        ds = o.getDataset( '/scan/instrument/histogram_ch01/data')
        self.assertEqual( type( ds), numpy.ndarray)
        self.assertEqual( len( ds), 34)
        self.assertEqual( ds.shape[0], 34)
        self.assertEqual( ds.shape[1], 1920)

        obj = o.getDatasetObj( '/scan/instrument/histogram_ch01/data')
        # 
        # obj.name
        #   - h5py: <class str>
        #   - pni:  <class 'pninexus.h5cpp._h5cpp.Path'>
        # 
        self.assertEqual( str( obj.name), '/scan/instrument/histogram_ch01/data')
        self.assertEqual( obj.linkType, 'HARD')
        self.assertEqual( obj.data[0][0], 1658.0)
        self.assertEqual( obj.data[1][2], 3162.0)

        return 

if __name__ == "__main__":
    unittest.main()

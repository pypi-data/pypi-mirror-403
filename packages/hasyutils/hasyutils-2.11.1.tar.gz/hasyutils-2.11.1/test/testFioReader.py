
#!/bin/env python
'''
$ python3 -m unittest discover -v
python3 ./test/testFioReader.py testFioReader.test_fileFio
python3 ./test/testFioReader.py testFioReader.test_fileDat
python3 ./test/testFioReader.py testFioReader.test_fileNxs
python3 ./test/testFioReader.py testFioReader.test_fioObj
#python3 ./test/testFioReader.py testFioReader.test_fioPlotter
'''
import unittest, sys, os, time
import HasyUtils
import HasyUtils.MgUtils
import PyTango
import numpy as np

class testFioReader( unittest.TestCase):

    @classmethod
    def setUpClass( clss):
    
        if not HasyUtils.unitTestChecks( "%s.setupClass" % clss):
            sys.exit( 255) 

    @classmethod
    def tearDownClass( clss): 

        if not HasyUtils.unitTestChecks( "%s.tearDownClass" % clss):
            sys.exit( 255) 

    def test_fileFio(  self):

        print( "\n>>> testFioReader.test_fileFio BEGIN")

        print( "getcwd %s" % os.getcwd())

        o = HasyUtils.fioReader( "./test/unitTestFIO.fio")

        self.assertEqual( o.columns[0].name, "eh_c01")
        self.assertEqual( o.columns[1].name, "eh_c02")
        self.assertEqual( o.columns[2].name, "eh_t01")
        self.assertEqual( o.columns[3].name, "sig_gen")
        self.assertEqual( len( o.columns[0].x), 51)
        self.assertEqual( len( o.columns[0].y), 51)
        self.assertEqual( len( o.columns[1].x), 51)
        self.assertEqual( len( o.columns[1].y), 51)
        
        print( ">>> testFioReader.test_fileFio, DONE")
        return 

    def test_fileDat(  self):

        print( "\n>>> testFioReader.test_fileDat BEGIN")

        print( "getcwd %s" % os.getcwd())

        o = HasyUtils.fioReader( "./test/unitTestDAT.dat")

        self.assertEqual( o.columns[0].name, "scan1")
        self.assertEqual( o.columns[1].name, "scan2")
        self.assertEqual( o.columns[2].name, "scan3")
        self.assertEqual( o.columns[3].name, "scan4")
        self.assertEqual( len( o.columns[0].x), 51)
        self.assertEqual( len( o.columns[0].y), 51)
        self.assertEqual( len( o.columns[1].x), 51)
        self.assertEqual( len( o.columns[1].y), 51)
        self.assertEqual( len( o.columns[2].x), 51)
        self.assertEqual( len( o.columns[2].y), 51)
        self.assertEqual( len( o.columns[3].x), 51)
        self.assertEqual( len( o.columns[3].y), 51)
        
        print( ">>> testFioReader.test_fileDat, DONE")
        return 

    def test_fileNxs(  self):

        hostname = HasyUtils.getHostname()
        #if hostname != 'haso107d10':
        #    return 

        print( "\n>>> testFioReader.test_fileNxs BEGIN")

        print( "getcwd %s" % os.getcwd())

        o = HasyUtils.fioReader( "./test/unitTestNeXus.nxs")

        self.assertEqual( len( o.columns), 6 )
        self.assertEqual( o.columns[0].name, "/scan/instrument/collection/eh_t01")
        self.assertEqual( o.columns[1].name, "/scan/instrument/collection/point_nb")
        self.assertEqual( o.columns[2].name, "/scan/instrument/collection/sig_gen")
        self.assertEqual( o.columns[3].name, "/scan/instrument/collection/timestamp")
        self.assertEqual( o.columns[4].name, "/scan/instrument/detector/collection/eh_c01")
        self.assertEqual( o.columns[5].name, "/scan/instrument/detector/collection/eh_c02")
        self.assertEqual( len( o.columns[0].x), 51)
        self.assertEqual( len( o.columns[0].y), 51)
        self.assertEqual( len( o.columns[1].x), 51)
        self.assertEqual( len( o.columns[1].y), 51)
        self.assertEqual( len( o.columns[2].x), 51)
        self.assertEqual( len( o.columns[2].y), 51)
        self.assertEqual( len( o.columns[3].x), 51)
        self.assertEqual( len( o.columns[3].y), 51)
        self.assertEqual( len( o.columns[4].x), 51)
        self.assertEqual( len( o.columns[4].y), 51)
        self.assertEqual( len( o.columns[5].x), 51)
        self.assertEqual( len( o.columns[5].y), 51)
        
        print( ">>> testFioReader.test_fileNxs, DONE")
        return 

    def test_fioObj(  self):

        print( "\n>>> testFioReader.test_fioObjt BEGIN")

        fileName = "./test/unitTestFioObj.fio"
        if os.path.exists( fileName): 
            os.remove( fileName)

        o = HasyUtils.fioObj( fileName = fileName, 
                              scanName = "cu", 
                              motorName = "exp_dmy01")

        o.parameters[ 'energy'] = 8980 
        o.comments.append( "Copper")
        o.user_comments.append( "Some user comment")
        col = HasyUtils.fioColumn( 'random')
        col.x = np.linspace( 0, 1, 6)
        col.y = np.random.random_sample( 6)
        o.columns.append( col)
        col = HasyUtils.fioColumn( 'linear')
        col.x = np.linspace( 0, 1, 6)
        col.y = np.linspace( 10, 20, 6)
        o.columns.append( col)

        fileName = o.write()

        o = HasyUtils.fioReader( fileName)
        self.assertEqual( len( o.columns), 2)
        self.assertEqual( len( o.columns[0].x), 6)
        self.assertEqual( len( o.columns[0].y), 6)
        self.assertEqual( len( o.columns[1].x), 6)
        self.assertEqual( len( o.columns[1].y), 6)
        self.assertEqual( o.columns[0].name, 'random')
        self.assertEqual( o.columns[1].name, 'linear')

        self.assertEqual( o.parameters[ 'ScanName'], 'cu')
        self.assertEqual( o.parameters[ 'energy'], '8980')

        self.assertEqual( o.motorName, 'exp_dmy01')
        self.assertEqual( o.fileName, './test/unitTestFioObj.fio')

        self.assertEqual( o.user_comments[0], '! Some user comment')
        self.assertEqual( o.user_comments[1], '!')
        self.assertEqual( o.user_comments[2], '! Comments')
        self.assertEqual( o.user_comments[3], '!')
        self.assertEqual( o.user_comments[4], '!')
        self.assertEqual( o.user_comments[5], '! Parameter')
        self.assertEqual( o.user_comments[6], '!')
        self.assertEqual( o.user_comments[7], '!')
        self.assertEqual( o.user_comments[8], '! Data')
        self.assertEqual( o.user_comments[9], '!')


        print( ">>> testFioReader.test_fioObj, DONE")
        return 

#    def test_fioPlotter( self):
#
#        print( ">>> testFioReader.test_fioPloter BEGIN")
#        ret = HasyUtils.fioPlotter( "./test/unitTestFIO.fio")
#        time.sleep(1)
#        print( ">>> testFioReader.test_fioPlotter, DONE")
#        return 

if __name__ == "__main__":
    unittest.main()

#!/bin/env python3
'''
$ python3 -m unittest discover -v

cd test
$ python3 -m unittest testOtherUtils

python3 ./test/testOtherUtils.py testOtherUtils.test_versions
python3 ./test/testOtherUtils.py testOtherUtils.test_checks
python3 ./test/testOtherUtils.py testOtherUtils.test_misc
python3 ./test/testOtherUtils.py testOtherUtils.test_analyseLogFiles
'''
import unittest, sys, os, time
import HasyUtils
import PyTango

class testOtherUtils( unittest.TestCase):

    @classmethod
    def setUpClass( clss):
    
        if not HasyUtils.unitTestChecks( "%s.setupClass" % clss):
            sys.exit( 255) 

    @classmethod
    def tearDownClass( clss): 

        if not HasyUtils.unitTestChecks( "%s.tearDownClass" % clss):
            sys.exit( 255) 

    def test_versions( self):

        print( "\n>>> testOtherUtils.test_versions, BEGIN")

        #
        # versions are tested through the root account, don't do it from CI
        #
        if os.getenv( "CiRunning") == "True":
            print( ">>> testOtherUtils.test_versions, CiRunning, return ")
            return 
        
        hostname = HasyUtils.getHostname()

        ret = HasyUtils.getHostVersionSardana( host = 'haszvmtangout.desy.de')
        self.assertEqual( ret, 3)
        ret = HasyUtils.checkHostDebian9( host = 'haszvmtangout.desy.de')
        self.assertEqual( ret, False)
        ret = HasyUtils.checkHostDebian10( host = 'haszvmtangout.desy.de')
        self.assertEqual( ret, False)
        ret = HasyUtils.checkHostDebian11( host = 'haszvmtangout.desy.de')
        self.assertEqual( ret, True)
        ret = HasyUtils.checkHostDebian12( host = 'haso107d10.desy.de')
        self.assertEqual( ret, True)
        
        print( ">>> testOtherUtils.test_versions, DONE")

        return

    def test_checks( self):
        #
        # check that require root-login cannot be made. gitlab-runner
        # is not a safe user
        #
        print( "\n>>> testOtherUtils.test_checks, BEGIN")

        ret = HasyUtils.checkHostOnline( 'haszvmtangout.desy.de')
        self.assertEqual( ret, True)
        ret = HasyUtils.checkHostOnline( 'haszvmtangout0.desy.de')
        self.assertEqual( ret, False)
        ret = HasyUtils.checkHostExists( 'haszvmtangout.desy.de')
        self.assertEqual( ret, True)
        ret = HasyUtils.checkHostExists( 'haszvmtangout0.desy.de')
        self.assertEqual( ret, False)

        return

    def test_misc( self):

        print( "\n>>> testOtherUtils.test_misc, BEGIN")
        ret = HasyUtils.doty2datetime( 100.1, 2022)
        self.assertEqual( ret.year, 2022)
        self.assertEqual( ret.month, 4)
        self.assertEqual( ret.day, 11)
        self.assertEqual( ret.hour, 2)
        self.assertEqual( ret.minute, 24)

        hostList = HasyUtils.readHostList( "/home/kracht/Monitors/ExpNodes.lis")         
        self.assertEqual( 'haspp08' in hostList, True)
        self.assertEqual( 'haspp10e1' in hostList, True)

        if os.path.exists( "temp.fio"):
            os.remove( "temp.fio")

        temp1 = HasyUtils.getEnv( "FioAdditions")
        HasyUtils.setEnv( "FioAdditions", "/online_dir/fioAddsUnitTest.py")
        """
        !
        ! Comments
        !
        %c
        fioAdd_line1
        fioAdd_line2
        fioAdd_line3
        !
        ! Parameter
        !
        %p
        
        fioAdd_par1 = value1
        fioAdd_par2 = value2
        fioAdd_par3 = value3
        """            
        ret = HasyUtils.fioAddsToFile( "temp.fio")
        with open( "temp.fio") as f: 
            lines = f.read().splitlines()

        self.assertEqual( '! Comments' in lines, True)
        self.assertEqual( 'fioAdd_line1' in lines, True)
        self.assertEqual( '! Parameter' in lines, True)
        self.assertEqual( 'fioAdd_par1 = value1' in lines, True)
        self.assertEqual( 'ubmatrix = [[1, 2, 3], [4, 5, 6], [7, 8, 9]]' in lines, True)

        ret = str( HasyUtils.getFioAdds())
        self.assertEqual( ret.find( 'fioAdd_line1') > -1, True)
        self.assertEqual( ret.find( 'fioAdd_par1') > -1, True)

        os.remove( "temp.fio")

        HasyUtils.setEnv( "FioAdditions", temp1)

        self.assertEqual( HasyUtils.findEditor() == 'emacs', True)

        hostname = HasyUtils.getHostname()
        ret = HasyUtils.runSubprocess( "hostname")
        self.assertEqual( ret[0] == "%s\n" % hostname, True)

        if os.path.exists( "temp.pkl"):
            os.remove( "temp.pkl")

        HasyUtils.pickleWriteDct( 'temp.pkl' , { 'a': "1 2 3"})
        ret = HasyUtils.pickleReadDct( 'temp.pkl')
        self.assertEqual( str( ret) == "{'a': '1 2 3'}", True)

        os.remove( "temp.pkl")

        temp1 = HasyUtils.getEnv( "MetadataScript")
        HasyUtils.setEnv( "MetadataScript", "/online_dir/metadataScriptUnitTest.py")

        dct = HasyUtils.getMetadata()
        self.assertEqual( dct[ 'temperature'], -271)
        self.assertEqual( dct[ 'temperature@unit'], 'Kelvin')

        
        HasyUtils.setEnv( "MetadataScript", temp1)
     
        print( ">>> testOtherUtils.test_misc, DONE")
        
        return

    def test_analyseLogFiles( self):

        print( "\n>>> testOtherUtils.test_analyseLogFiles, BEGIN")

        if os.getcwd().split( '/')[-1] == 'test': 
            lst = HasyUtils.analyseLogFile( "unitTestLog.txt")
        else: 
            lst = HasyUtils.analyseLogFile( "./test/unitTestLog.txt")
        self.assertEqual( len( lst), 28)
        print( ">>> testOtherUtils.test_analyseLogFiles, DONE")
        return 

if __name__ == "__main__":
    unittest.main()

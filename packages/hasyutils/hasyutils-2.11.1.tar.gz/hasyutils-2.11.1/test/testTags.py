#!/usr/bin/env python
'''
$ python -m unittest discover -v
python3 ./test/testTags.py testTags.testTags
'''
import unittest, sys, os, time
import HasyUtils
import PyTango

class testTags( unittest.TestCase):

    @classmethod
    def setUpClass( clss):
    
        if not HasyUtils.unitTestChecks( "%s.setupClass" % clss):
            sys.exit( 255) 

    @classmethod
    def tearDownClass( clss): 

        if not HasyUtils.unitTestChecks( "%s.tearDownClass" % clss):
            sys.exit( 255) 

    def testTags( self):
        '''
        '''
        print( "\n>>> testTags.testTags, BEGIN")

        hostname = HasyUtils.getHostname()

        if hostname == 'haszvmtangout': 
            devList = HasyUtils.getOnlineXML( xmlFile = None, cliTags = [ 'user'])
            self.assertEqual( len( devList), 25)

            devList = HasyUtils.getOnlineXML( xmlFile = None, cliTags = 'user')
            self.assertEqual( len( devList), 25)
            
            devList = HasyUtils.getOnlineXML( xmlFile = None, cliTags = [ 'expert'])
            self.assertEqual( len( devList), 17)
            
            devList = HasyUtils.getOnlineXML( xmlFile = None, cliTags = [ 'user,expert'])
            self.assertEqual( len( devList), 27)
            
            devList = HasyUtils.getOnlineXML( xmlFile = None, cliTags = [ 'user' , 'expert'])
            self.assertEqual( len( devList), 27)
            
            devList = HasyUtils.getOnlineXML( xmlFile = None, cliTags = 'user,expert')
            self.assertEqual( len( devList), 27)
            
        print( ">>> testTags.testTags, DONE")
        
        return


if __name__ == "__main__":
    unittest.main()

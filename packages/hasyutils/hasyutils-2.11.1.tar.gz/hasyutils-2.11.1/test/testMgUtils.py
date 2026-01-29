
#!/bin/env python
'''
$ python3 -m unittest discover -v
python3 ./test/testMgUtils.py testMgUtils.test_checkPoolNameValid
python3 ./test/testMgUtils.py testMgUtils.test_createMg
python3 ./test/testMgUtils.py testMgUtils.test_createMg2
python3 ./test/testMgUtils.py testMgUtils.test_createMg3
'''
import unittest, sys, os, time
import HasyUtils
import HasyUtils.MgUtils
import PyTango

class testMgUtils( unittest.TestCase):

    @classmethod
    def setUpClass( clss):
    
        if not HasyUtils.unitTestChecks( "%s.setupClass" % clss):
            sys.exit( 255) 

    @classmethod
    def tearDownClass( clss): 

        if not HasyUtils.unitTestChecks( "%s.tearDownClass" % clss):
            sys.exit( 255) 

    def test_checkPoolNameValid( self):
        print( "\n>>> test_checkPoolNameValid BEGIN")

        hostname = HasyUtils.getHostname()
        BL = 'p09'
        if hostname == 'haszmvtangout':
            BL = p99
            
        self.assertEqual( HasyUtils.MgUtils.checkPoolNameValid( '%s/pool/%s' % ( BL, hostname)), True)

        print( ">>> test_checkPoolNameValid OK")
        return 

    def test_createMg(  self):

        hostname = HasyUtils.getHostname()

        # +++
        #if hostname == "haszvmtangout": 
        #    return

        print( "\n>>> test_createMg BEGIN")

        mg = HasyUtils.MgUtils.MgConf( None, "mgunittest", True)
        self.assertEqual( mg is not None, True)

        mg.addCounter( "eh_c01", True)
        mg.addCounter( "eh_c02", True)
        mg.addOther( "eh_c03")
        mg.addMCA( "eh_mca01")
        mg.addPilatus( "pilatus")
        mg.addTimer( "eh_t01")
        mg.addExtraTimer( "eh_t02")
        mg.addSCA( "sca_eh_mca01_100_200", True, True)

        self.assertEqual( mg.hsh[ 'timer'], 'tango://%s:10000/expchan/dgg2_eh_01/1' % hostname)
        self.assertEqual( mg.hsh[ 'monitor'], 'tango://%s:10000/expchan/dgg2_eh_01/1' % hostname)

        self.assertEqual( mg.hsh[ 'controllers']['tango://%s:10000/controller/sis3820ctrl/sis3820_eh' % hostname]['channels']['tango://%s:10000/expchan/sis3820_eh/1' % hostname]['enabled'], True)
        self.assertEqual( mg.hsh[ 'controllers']['tango://%s:10000/controller/sis3820ctrl/sis3820_eh' % hostname]['channels']['tango://%s:10000/expchan/sis3820_eh/1' % hostname]['full_name'], 'tango://%s:10000/expchan/sis3820_eh/1' % hostname)
        self.assertEqual( mg.hsh[ 'controllers']['tango://%s:10000/controller/sis3820ctrl/sis3820_eh' % hostname]['channels']['tango://%s:10000/expchan/sis3820_eh/1' % hostname]['index'], 0)
        self.assertEqual( mg.hsh[ 'controllers']['tango://%s:10000/controller/sis3820ctrl/sis3820_eh' % hostname]['channels']['tango://%s:10000/expchan/sis3820_eh/1' % hostname]['label'], 'eh_c01')
        self.assertEqual( mg.hsh[ 'controllers']['tango://%s:10000/controller/sis3820ctrl/sis3820_eh' % hostname]['channels']['tango://%s:10000/expchan/sis3820_eh/1' % hostname]['name'], 'eh_c01')
        self.assertEqual( mg.hsh[ 'controllers']['tango://%s:10000/controller/sis3820ctrl/sis3820_eh' % hostname]['channels']['tango://%s:10000/expchan/sis3820_eh/1' % hostname]['ndim'], 0)
        self.assertEqual( mg.hsh[ 'controllers']['tango://%s:10000/controller/sis3820ctrl/sis3820_eh' % hostname]['channels']['tango://%s:10000/expchan/sis3820_eh/1' % hostname]['normalization'], 0)
        self.assertEqual( mg.hsh[ 'controllers']['tango://%s:10000/controller/sis3820ctrl/sis3820_eh' % hostname]['channels']['tango://%s:10000/expchan/sis3820_eh/1' % hostname]['plot_type'], 1)
        self.assertEqual( mg.hsh[ 'controllers']['tango://%s:10000/controller/sis3820ctrl/sis3820_eh' % hostname]['channels']['tango://%s:10000/expchan/sis3820_eh/1' % hostname]['source'], 'tango://%s:10000/expchan/sis3820_eh/1/Value' % hostname)

        self.assertEqual( mg.hsh[ 'controllers']['tango://%s:10000/controller/sis3820ctrl/sis3820_eh' % hostname]['channels']['tango://%s:10000/expchan/sis3820_eh/2' % hostname]['enabled'], True)
        self.assertEqual( mg.hsh[ 'controllers']['tango://%s:10000/controller/sis3820ctrl/sis3820_eh' % hostname]['channels']['tango://%s:10000/expchan/sis3820_eh/2' % hostname]['full_name'], 'tango://%s:10000/expchan/sis3820_eh/2' % hostname)
        self.assertEqual( mg.hsh[ 'controllers']['tango://%s:10000/controller/sis3820ctrl/sis3820_eh' % hostname]['channels']['tango://%s:10000/expchan/sis3820_eh/2' % hostname]['index'], 1)
        self.assertEqual( mg.hsh[ 'controllers']['tango://%s:10000/controller/sis3820ctrl/sis3820_eh' % hostname]['channels']['tango://%s:10000/expchan/sis3820_eh/2' % hostname]['label'], 'eh_c02')
        self.assertEqual( mg.hsh[ 'controllers']['tango://%s:10000/controller/sis3820ctrl/sis3820_eh' % hostname]['channels']['tango://%s:10000/expchan/sis3820_eh/2' % hostname]['name'], 'eh_c02')
        self.assertEqual( mg.hsh[ 'controllers']['tango://%s:10000/controller/sis3820ctrl/sis3820_eh' % hostname]['channels']['tango://%s:10000/expchan/sis3820_eh/2' % hostname]['ndim'], 0)
        self.assertEqual( mg.hsh[ 'controllers']['tango://%s:10000/controller/sis3820ctrl/sis3820_eh' % hostname]['channels']['tango://%s:10000/expchan/sis3820_eh/2' % hostname]['normalization'], 0)
        self.assertEqual( mg.hsh[ 'controllers']['tango://%s:10000/controller/sis3820ctrl/sis3820_eh' % hostname]['channels']['tango://%s:10000/expchan/sis3820_eh/2' % hostname]['plot_type'], 1)
        self.assertEqual( mg.hsh[ 'controllers']['tango://%s:10000/controller/sis3820ctrl/sis3820_eh' % hostname]['channels']['tango://%s:10000/expchan/sis3820_eh/2' % hostname]['source'], 'tango://%s:10000/expchan/sis3820_eh/2/Value' % hostname)


        self.assertEqual( mg.hsh['controllers']['tango://%s:10000/controller/pilatusctrl/pilatus300kpilatusctrl' % hostname]['trigger_type'], 0)
        self.assertEqual( mg.hsh[ 'controllers']['tango://%s:10000/controller/pilatusctrl/pilatus300kpilatusctrl' % hostname]['channels']['tango://%s:10000/expchan/pilatus300kpilatusctrl/1' % hostname]['full_name'], 'tango://%s:10000/expchan/pilatus300kpilatusctrl/1' % hostname)
        self.assertEqual( mg.hsh[ 'controllers']['tango://%s:10000/controller/pilatusctrl/pilatus300kpilatusctrl' % hostname]['channels']['tango://%s:10000/expchan/pilatus300kpilatusctrl/1' % hostname]['label'], 'pilatus')
        self.assertEqual( mg.hsh[ 'controllers']['tango://%s:10000/controller/pilatusctrl/pilatus300kpilatusctrl' % hostname]['channels']['tango://%s:10000/expchan/pilatus300kpilatusctrl/1' % hostname]['name'], 'pilatus')
        self.assertEqual( mg.hsh[ 'controllers']['tango://%s:10000/controller/pilatusctrl/pilatus300kpilatusctrl' % hostname]['channels']['tango://%s:10000/expchan/pilatus300kpilatusctrl/1' % hostname]['index'], 4)
        self.assertEqual( mg.hsh[ 'controllers']['tango://%s:10000/controller/pilatusctrl/pilatus300kpilatusctrl' % hostname]['channels']['tango://%s:10000/expchan/pilatus300kpilatusctrl/1' % hostname]['plot_type'], 0)

        self.assertEqual( mg.findMasterTimer(), 'eh_t01')
        self.assertEqual( mg.findDeviceController( "eh_c01"), 'tango://%s:10000/controller/sis3820ctrl/sis3820_eh' % hostname)
        self.assertEqual( mg.findFullDeviceName( "eh_c01"), 'tango://%s:10000/expchan/sis3820_eh/1' % hostname)

        mg.updateConfiguration()
        p = PyTango.DeviceProxy( "mgunittest") 

        lst = p.elementlist
        self.assertEqual( 'eh_t01' in lst, True)
        self.assertEqual( 'eh_t02' in lst, True)
        self.assertEqual( 'eh_c01' in lst, True)
        self.assertEqual( 'eh_c02' in lst, True)
        self.assertEqual( 'eh_c03' in lst, True)
        self.assertEqual( 'eh_mca01' in lst, True)
        self.assertEqual( 'sca_eh_mca01_100_200' in lst, True)

        self.assertEqual( 'pilatus' in lst, True)

        pool = PyTango.DeviceProxy( "p09/pool/%s" % hostname) 
        pool.command_inout( "DeleteElement", "mgunittest")  

        self.assertEqual( HasyUtils.MgUtils.checkPoolNameValid( "p09/pool/%s" % hostname), True)

        print( ">>> test_createMg, DONE")
        return 

    def test_createMg2(  self):

        hostname = HasyUtils.getHostname()
        # +++
        #if hostname == "haszvmtangout": 
        #    return

        print( "\n>>> test_createMg2 BEGIN")

        HasyUtils.MgUtils.setMg( None, mgName = 'mgunittest', 
                                timer = "eh_t02", 
                                extraTimers = None, 
                                counters = "eh_c03,eh_c04", 
                                mcas = "eh_mca02", others = None)
        p = PyTango.DeviceProxy( "mgunittest") 
        lst = p.elementlist
        print( "elementlist %s" % str( lst))
        self.assertEqual( 'eh_t02' in lst, True)
        self.assertEqual( 'eh_c03' in lst, True)
        self.assertEqual( 'eh_c04' in lst, True)
        self.assertEqual( 'eh_mca02' in lst, True)

        pool = PyTango.DeviceProxy( "p09/pool/%s" % hostname) 
        pool.command_inout( "DeleteElement", "mgunittest")  
        
        print( ">>> test_createMg2, DONE")
        return 


    def test_createMg3(  self):

        hostname = HasyUtils.getHostname()

        # +++
        #if hostname == "haszvmtangout": 
        #    return

        print( "\n>>> test_createMg3 BEGIN")

        mg = HasyUtils.MgUtils.MgConf( None, "mgunittest", True)
        self.assertEqual( mg is not None, True)

        mg.addCounter( "eh_c01", True)
        mg.addCounter( "eh_c02", True)
        mg.addOther( "eh_c03")
        mg.addMCA( "eh_mca01")
        mg.addPilatus( "pilatus")
        mg.addTimer( "eh_t01")
        mg.addExtraTimer( "eh_t02")
        mg.addSCA( "sca_eh_mca01_100_200", True, True)

        mg.updateConfiguration()

        p = PyTango.DeviceProxy( "mgunittest") 

        lst = p.elementlist
        self.assertEqual( 'eh_t01' in lst, True)
        self.assertEqual( 'eh_t02' in lst, True)
        self.assertEqual( 'eh_c01' in lst, True)
        self.assertEqual( 'eh_c02' in lst, True)
        self.assertEqual( 'eh_c03' in lst, True)
        self.assertEqual( 'eh_mca01' in lst, True)
        self.assertEqual( 'sca_eh_mca01_100_200' in lst, True)

        self.assertEqual( 'pilatus' in lst, True)

        pool = PyTango.DeviceProxy( "p09/pool/%s" % hostname) 
        pool.command_inout( "DeleteElement", "mgunittest")  

        print( ">>> test_createMg, DONE")
        return 
    
if __name__ == "__main__":
    unittest.main()

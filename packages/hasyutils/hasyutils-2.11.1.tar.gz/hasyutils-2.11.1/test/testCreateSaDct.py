#!/usr/bin/env python
'''
$ python -m unittest discover -v
cd test
python3 ./test/testCreateSaDct.py testCreateSaDct.testCreateSaDct
'''

import unittest, sys, os, time
import HasyUtils
import PyTango
'''
 Col 1 position DOUBLE
 Col 2 sig_gen DOUBLE
 Col 3 step_gen DOUBLE 
 Col 4 dip_gen DOUBLE
 Col 5 slit_gen DOUBLE
'''
#
# use always the same data. The VcExecutors do not reliably 
# generate the same sequence. Don't know why.
#
DATA = [
    "0.0 4.03656696307e-08 17.0563443809 999.99999996 1.85457085253",
    "0.02 2.62186187208e-07 18.0412146835 999.999999738 2.86034893118",
    "0.04 1.57693223396e-06 15.1728543689 999.999998423 0.0146961486531",
    "0.06 8.78257423783e-06 18.063577085 999.999991217 2.93016872353",
    "0.08 4.52935336845e-05 15.7526020038 999.999954706 0.646273985085",
    "0.1 0.00021629981886 16.4356538953 999.9997837 1.35908166896",
    "0.12 0.000956492751297 15.9884277999 999.999043507 0.944703293189",
    "0.14 0.00391663216909 16.2732798838 999.996083368 1.26600252421",
    "0.16 0.0148507869034 17.5093860602 999.985149213 2.54278005364",
    "0.18 0.0521424846842 16.6805531385 999.947857515 1.75962062623",
    "0.2 0.169527264509 17.0177703784 999.830472735 2.14849447009",
    "0.22 0.510379194937 15.3345564764 999.489620805 0.524174950363",
    "0.24 1.42282650536 16.558059641 998.577173495 1.81544093329",
    "0.26 3.6729626112 16.3822380061 996.327037389 1.71840888366",
    "0.28 8.77984086188 15.9695647051 991.220159138 1.39846914291",
    "0.3 19.4340071028 15.1986346679 980.565992897 0.738256450609",
    "0.32 39.8330577748 15.8720402097 960.166942225 1.54611909337",
    "0.34 75.6015172467 16.7496794013 924.398482753 2.59043841637",
    "0.36 132.868781691 15.7449365775 867.131218309 1.7976219436",
    "0.38 216.232500474 15.7228587702 783.767499526 2.05373469581",
    "0.4 325.855131229 14.454865343 674.144868771 1.16630520693",
    "0.42 454.70919255 15.3698596301 545.29080745 2.63141887373",
    "0.44 587.554937544 14.2650058382 412.445062456 2.38477176043",
    "0.46 703.02181657 12.0643361777 296.97818343 1.67529425462",
    "0.48 778.923310434 7.80768873112 221.076689566 0.397102304651",
    "0.5 799.146083808 3.943075691 200.853916192 3.95044578544",
    "0.52 759.212284001 -5.75807964446 240.787715999 9.18122866311",
    "0.54 667.891402931 -9.04322196742 332.108597069 17.5815173043",
    "0.56 544.069094022 -10.7344793973 455.930905978 25.5815459165",
    "0.58 410.400456984 -11.0030976761 589.599543016 34.1736217662",
    "0.6 286.660062456 -10.339313054 713.339937544 43.312349128",
    "0.62 185.409559793 -12.4121917933 814.590440207 49.5099117803",
    "0.64 111.045926154 -12.8148019583 888.954073846 57.2576693092",
    "0.66 61.5855344366 -13.4062610889 938.414465563 64.7404796727",
    "0.68 31.6271730394 -12.063415704 968.372826961 74.1064765775",
    "0.7 15.0399922 -12.422637515 984.9600078 81.7344714427",
    "0.72 6.62278144734 -11.9570526177 993.377218553 90.1610762419",
    "0.74 2.70046661224 -13.5060191722 997.299533388 96.5534566424",
    "0.76 1.01963040382 -12.8402680986 998.980369596 105.145412127",
    "0.78 0.356494076474 -12.3871334766 999.643505924 113.512850862",
    "0.8 0.115416376407 -12.643180866 999.884583624 121.161587736",
    "0.82 0.0346009584125 -14.8127672953 999.965399042 126.889052268",
    "0.84 0.00960537662192 -12.1985890839 999.990394623 137.393914787",
    "0.86 0.00246914300525 -14.7865134935 999.997530857 142.691371092",
    "0.88 0.000587737857549 -12.3944191603 999.999412262 152.964381763",
    "0.9 0.000129546792188 -13.386366666 999.999870453 159.849557479",
    "0.92 2.64408393657e-05 -12.8053599025 999.999973559 168.304437618",
    "0.94 4.99723057037e-06 -14.6774496397 999.999995003 174.303415776",
    "0.96 8.74559002408e-07 -14.6945894493 999.999999125 182.154905345",
    "0.98 1.4172759492e-07 -13.5646464555 999.999999858 191.151344898",
    "1.0 2.12679336219e-08 -14.6840076908 999.999999979 197.896604094",
]
class testCreateSaDct( unittest.TestCase):

    @classmethod
    def setUpClass( clss):
    
        if not HasyUtils.unitTestChecks( "%s.setupClass" % clss):
            sys.exit( 255) 

    @classmethod
    def tearDownClass( clss): 

        if not HasyUtils.unitTestChecks( "%s.tearDownClass" % clss):
            sys.exit( 255) 

    def testCreateSaDct( self):
        '''
        '''
        # the gitlab-runner has no DISPLAY set, normally
        if os.getenv( "DISPLAY") is None:
            print( "\n***\n*** testCreateSaDct: no DISPLAY, return\n***")
            return 1

        print( "\n>>> testCreateSaDct.testCreateSaDct, BEGIN")
        #
        # start with fresh data, but we cannot kill
        # a process that belongs to somebody else
        #
        try: 
            HasyUtils.killProcessName( "pyspMonitor") 
        except: 
            pass

        (status, wasLaunched) = HasyUtils.assertProcessRunning( '/usr/bin/pyspMonitor.py')

        if not status: 
            print( "testCreateSaDct.testCreateSaDct: trouble launching pyspMonitor.py")
            return

        door = PyTango.DeviceProxy( HasyUtils.getDoorNames()[0])

        if door.state() != PyTango.DevState.ON: 
            print( "testCreateSaDct.testCreateSaDct: door is not ON %s" % repr( door.state()))
            return 

        #
        # just to put 'ascan' into the history, needed by mvsa.py
        #
        HasyUtils.runMacro( "change_mg -g mg_unittest -t eh_t01 -c eh_c01,sig_gen,eh_c02")
        HasyUtils.runMacro( "ascan exp_dmy01 0 1 10 0.1")
        #
        # Col 1 position DOUBLE
        # Col 2 sig_gen DOUBLE
        # Col 3 step_gen DOUBLE
        # Col 4 dip_gen DOUBLE
        # Col 5 slit_gen DOUBLE
        #
        
        posArr = []
        sigArr = []
        stepArr = []
        dipArr = []
        slitArr = []
        
        for line in DATA:
            (pos, sig, step, dip, slit) = line.split()
            posArr.append( pos)
            sigArr.append( sig)
            stepArr.append( step)
            dipArr.append( dip)
            slitArr.append( slit)
        hsh = { 'putData':
                {'title': "some data", 
                 'columns': 
                 [ { 'name': "eh_mot01", 'data' : posArr},
                   { 'name': "sig_gen", 'data' : sigArr},
                   { 'name': "step_gen", 'data' : stepArr},
                   { 'name': "dip_gen", 'data' : dipArr},
                   { 'name': "slit_gen", 'data' : slitArr},]}}
        hsh = HasyUtils.toPyspMonitor( hsh)

        #
        # peak
        #
        HasyUtils.toPyspMonitor( {'command': ['cls', 'display']})

        cmpDct = { 
        'peak': 
            {
                'flagDataFromMonitor':True,
                'message':'success',
                'mode':'peak',
                'npSig':10,
                'npTotal':51,
                'signalCounter':'sig_gen',
                'xpos':0.5,
                'xcen':0.49666666666664677,
                'xcms':0.4966666666663814,
                'yMax':799.146083808,
                'yMin':1.12679336219e-08,
            },
        'stepssa': 
            {
                'flagDataFromMonitor':True,
                'message':'success',
                'mode':'stepssa',
                'npSig':5,
                'npTotal':51,
                'signalCounter':'step_gen',
                'xpos':0.5,
                'xstepcssa':0.50063919542,
                'xstepmssa':0.431700841401,
                'xstepssa':0.5,
                'yMax':18.063577085,
                'yMin':-14.8127672953,
            },
        'dip': 
            {
                'flagDataFromMonitor':True,
                'message':'success',
                'mode':'dip',
                'npSig':10,
                'npTotal':51,
                'signalCounter':'dip_gen',
                'xdip':0.5,
                'xdipc':0.4966666666666522,
                'xdipm':0.4966666666663044,
                'xpos':0.5,
                'yMax':999.999999979,
                'yMin':200.853916192,
            },
        'slit': 
            {
                'flagDataFromMonitor':True,
                'message':'success',
                'mode':'slit',
                'npSig':8,
                'npTotal':51,
                'signalCounter':'slit_gen',
                'xpos':0.5,
                'xslit':0.5,
                'xslitc':0.499717970749072,
                'xslitm':0.4737263184515599,
                'yMax':197.896604094,
                'yMin':0.0146961486531,
            },
        }

        for mode in list(cmpDct.keys()): 

            if mode in [ 'peak', 'cms', 'cen', 'peakssa', 'cmsssa', 'censsa']: 
                HasyUtils.setEnv( "SignalCounter", "sig_gen")
            elif mode in [ 'step', 'stepm', 'stepc', 'stepssa', 'stepmssa', 'stepcssa']: 
                HasyUtils.setEnv( "SignalCounter", "step_gen")
            elif mode in [ 'dip', 'dipm', 'dipc', 'dipssa', 'dipmssa', 'dipcssa']: 
                HasyUtils.setEnv( "SignalCounter", "dip_gen")
            elif mode in [ 'slit', 'slitm', 'slitc', 'slitssa', 'slitmssa', 'slitcssa']: 
                HasyUtils.setEnv( "SignalCounter", "slit_gen")
            else: 
                print( "testCreateSaDct: wrong mode")
                return 

            print("testCreateSaDct: createSaDct %s" % mode)
            door.runmacro( [ "createSaDct", mode])
            while door.state() == PyTango.DevState.RUNNING: 
                #print( "testCreateSaDct: createSaDct is active")
                time.sleep(0.5)

            saDct = HasyUtils.getEnv( "saDct")
            if saDct[ 'message'] != 'success':
                print( "testCreateSaDct: error, %s" % HasyUtils.dct_print2str( saDct))
                return 

            del saDct[ 'xData']
            del saDct[ 'yData']
            del saDct[ 'motorArr']
            del saDct[ 'scanInfo']
            del saDct[ 'fileName']

            print( "saDct  %s" % HasyUtils.dct_print2str( saDct))
            print( "cmpDct %s" % HasyUtils.dct_print2str( cmpDct[ mode]))

            for k in list( cmpDct[ mode].keys()): 
                print( "testCreateSaDct: comparing (%s) %s %s (cmpDct) and %s (saDct)" % 
                       (mode, k, repr( cmpDct[ mode][ k]), repr( saDct[ k])))
                if type( saDct[ k]) is float: 
                    self.assertAlmostEqual( cmpDct[ mode][ k], saDct[ k], 7)
                else:
                    self.assertEqual( cmpDct[ mode][ k], saDct[ k])
            
        HasyUtils.setEnv( "SignalCounter", "sig_gen")
        HasyUtils.setEnv( "ActiveMntGrp", "mg_ivp")
        HasyUtils.stopPyspMonitors()

        print( ">>> testCreateSaDct.testCreateSaDct, DONE")
        
        return



if __name__ == "__main__":
    unittest.main()

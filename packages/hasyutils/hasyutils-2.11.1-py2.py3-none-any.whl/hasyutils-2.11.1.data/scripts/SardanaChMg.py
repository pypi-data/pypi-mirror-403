#!python
#

import string
import sys, os
from PyTango import *
from optparse import OptionParser
import json
import pprint
import HasyUtils
import HasyUtils.pooltools
import HasyUtils.MgUtils
import socket
import traceback

pp = pprint.PrettyPrinter(indent=2)
db = Database()

def testRunningDoors():
    """ return True, if there is at least one running door """

    lst = HasyUtils.getDoorNames()
    for door in lst:
        proxy = DeviceProxy( door)
        if proxy.state() == DevState.RUNNING and not options.listFlag:
            return True
    return False

def main():
    global options

    hostname = socket.gethostname()

    if hostname.find( 'haspp01eh') >= 0: 
        usage = "%prog -p <pool> -g <mgName> -t <timer> -e <extraTimer> -c <counter> -m <mca>\n" +\
                " Change the contents of the measurement group, e.g.: \n" +\
                "  %prog -t eh2_t01 -c eh2_c01 -m sis3302_01\n"\
                "   this clears the group, if it exists, and fills it with the specified devices \n\n"\
                "  %prog -p p01/pool/haspp01eh1 -g mg_haspp01eh1 -a -c eh2_c02 -m eh2_mca02 \n"\
                "   adds some device to the existing group "
    elif hostname.find( 'haspp02ch1a') >= 0: 
        usage = "%prog -p <pool> -g <mgName> -t <timer> -e <extraTimer> -c <counter> -m <mca>\n" +\
                " Change the contents of the measurement group, e.g.: \n" +\
                "  %prog -t eh1a_t01 -c eh1a_c01 -m sis3302_01\n"\
                "   this clears the group, if it exists, and fills it with the specified devices \n\n"\
                "  %prog -p p02/pool/haspp02ch1a -g mg_haspp02ch1a -a -c eh1a_c02 -m eh1a_mca02 \n"\
                "   adds some device to the existing group "
    elif hostname.find( 'haspp02cha') >= 0: 
        usage = "%prog -p <pool> -g <mgName> -t <timer> -e <extraTimer> -c <counter> -m <mca>\n" +\
                " Change the contents of the measurement group, e.g.: \n" +\
                "  %prog -t eh2a_t01 -c eh2a_c01 -m sis3302_01\n"\
                "   this clears the group, if it exists, and fills it with the specified devices \n\n"\
                "  %prog -p p02/pool/haspp02ch2 -g mg_haspp02ch2 -a -c eh2a_c02 -m eh2a_mca02 \n"\
                "   adds some device to the existing group "
    else:
        usage = "%prog -p <pool> -g <mgName> -t <timer> -e <extraTimer> -c <counter> -m <mca>\n" +\
                " Change the contents of the measurement group, e.g.: \n" +\
                "  %prog -p pXX/pool/XXX -g mg1 -t exp_t01 -c exp_c01,exp_adc01,exp_vfc01 -m exp_mca01\n"\
                "  %prog -t exp_t01 -c exp_c01,exp_adc01,exp_vfc01 -m exp_mca01\n"\
                "   this clears the group, if it exists, and fills it with the specified devices \n\n"\
                "  %prog -p p09/pool/exp.01 -g mg1 -a -c exp_c04 -m exp_mca01 \n"\
                "   adds some device to the existing group "

    parser = OptionParser(usage=usage)
    parser.add_option("-a", action="store_true", dest="addFlag", help="adds devices to the mg")
    parser.add_option("-b", action="store_true", dest="testFlag", help="make test, with -a")
    parser.add_option("-c", action="store", type="string", dest="counterNames", help="e.g.: -c exp_c01,exp_c02")
    parser.add_option("-e", action="store", type="string", dest="extraTimerNames", help="extra timers, e.g. -e exp_t02")
    parser.add_option("-f", action="store_true", dest="listFullFlag", help="full mg listing, debugging tool")
    parser.add_option("-g", action="store", type="string", dest="mgName", help="e.g.: -g mg_xxx")
    parser.add_option("-l", action="store_true", dest="listFlag", help="lists the mg")
    parser.add_option("-m", action="store", type="string", dest="mcaNames", help="e.g.: -m exp_mca01")
    parser.add_option("-n", action="store", type="string", dest="countersNoDisplay", help="e.g.: -n exp_c03,exp_c04")
    parser.add_option("--nd", action="store", type="string", dest="countersNoDisplay2nd", help="e.g.: -nd exp_c03,exp_c04")
    parser.add_option("--no", action="store", type="string", dest="countersNoSpockColumn", help="e.g.: -no exp_c03,exp_c04")
    parser.add_option("--ndo", action="store", type="string", dest="countersNoDisplayNoSpockColumn", help="e.g.: -ndo exp_c03,exp_c04")
    parser.add_option("-p", action="store", type="string", dest="poolName", help="e.g.: -p p09/pool/exp.01, optional")
    parser.add_option("-q", action="store", type="string", dest="pilatusNames", help="e.g.: -q pilatus300k, optional")
    parser.add_option("-t", action="store", type="string", dest="timerNames", help="master timer, e.g. -t exp_t01, mandatory")
    #parser.add_option("-w", action="store", type="string", dest="writeFile", help="update MG configuration from file")
    (options, args) = parser.parse_args()

    if len( sys.argv) == 1:
        parser.print_help()
        sys.exit(255)

    #
    # make sure that there are no running doors
    #
    if testRunningDoors() and not options.listFlag:
        print( "chMg: door is in RUNNING state, exiting")
        sys.exit(255)

    #
    # if no MG and no Pool is supplied and if there 
    # is only one MG, use this group and the related pool
    #
    if options.mgName is None and options.poolName is None:
        lst = HasyUtils.getLocalMgAliases()
        if not lst:
            print( "\nThere is no MeasurementGroup")
            sys.exit(255)
        elif len(lst) == 1:
            options.mgName = lst[0]
            print( "SardanaChMg.py, changing %s" % options.mgName)
        else:
            parser.print_help()
            print( "\nUse -g to choose a MeasurementGroup")
            for mg in HasyUtils.getMgAliases(): 
                print( " %s" % mg)
            sys.exit(255)
        options.poolName = HasyUtils.findPoolForMg( options.mgName)

    #
    # if we don't have a MG here quit
    #
    if options.mgName is None:
        parser.print_help()
        lst = HasyUtils.getMgAliases()
        if lst:
            print( "Chose one of %s" % repr( lst))
        else:
            print( "\nNo MeasurementGroup available\n ")
        sys.exit(255)

    #
    # if poolName is not supplied and only one pool exists, take this one
    #
    if options.poolName is None:
        lst = HasyUtils.getPoolNames()
        if lst is None:
            parser.print_help()
            print( "***")
            print( "*** SardanaChMg.py: no Pool")
            print( "***")
            sys.exit(255)
        options.poolName = lst[0]

    flagClear = True
    if options.addFlag:
        flagClear = False

    mgConf = HasyUtils.MgUtils.MgConf( options.poolName, options.mgName, flagClear)

    #
    # list the elements of the Mg
    #
    if options.listFlag:
        hsh = json.loads( mgConf.mg.Configuration) 
        print( "%s contains %s" % ( db.get_alias( mgConf.mg.name()), mgConf.mg.ElementList))
        #
        # exit because without the -a flag the  configuration mgConf.mg.hsh is cleared
        #
        sys.exit(255)
    #
    # display a full listing of the Mg
    #
    if options.listFullFlag:
        hsh = json.loads( mgConf.mg.Configuration) 
        ret = HasyUtils.dct_print2str( hsh)
        #HasyUtils.dct_print( hsh)
        print( "%s" % ret)
        print( "# ElementList: %s" % repr( mgConf.mg.ElementList))
        #
        # exit because without the -a flag the  configuration mgConf.mg.hsh is cleared
        #
        sys.exit(255)
    #
    # SardanaChMg.py -g mg_tk -a -b
    # use this command to do some manipulation of the MG
    #
    if options.testFlag:
        for ctrl in list( mgConf.hsh[ 'controllers']):
            for chan in list( mgConf.hsh[ 'controllers'][ ctrl][ 'channels']):
                print( "ctrl %s channel %s index %d " % 
                       (repr( ctrl), repr( chan), 
                        mgConf.hsh[ 'controllers'][ ctrl]['channels'][chan]['index']))
        if not options.addFlag:
            #
            # exit because without the -a flag the  configuration mgConf.mg.hsh is cleared
            #
            print( "SardanaChMg, no '-a', exit")
            sys.exit(255)
            


    # 
    # an important debugging feature
    # 
    #if options.writeFile:
    #    a = ""
    #    f = open( options.writeFile, 'r')
    #    for line in f.readlines():
    #        a = a + line.strip() + "\\\n"
    #    f.close()
    #    exec "dct = %s" % a
    #    mgConf.mg.Configuration = json.dumps( dct)
    #    sys.exit(255)

    print( "SardanaChMg.py: %s" % options.mgName)
    try:
        if not options.addFlag and not options.timerNames:
            lst = HasyUtils.getTimerAliases()
            if lst is not None and len( lst) > 0: 
                mgConf.addTimer( lst[0])
            else:
                parser.print_help()
                sys.exit(255)

        if options.timerNames: 
            print( "SardanaChMg.py: %s" % options.timerNames)
            for timer in options.timerNames.split(','):
                mgConf.addTimer( timer)

        if options.extraTimerNames:
            print( "SardanaChMg.py: %s" % options.extraTimerNames)
            for timer in options.extraTimerNames.split(','):
                mgConf.addExtraTimer( timer)

        if options.mcaNames:
            print( "SardanaChMg.py: %s" % options.mcaNames)
            for mca in options.mcaNames.split(','):
                if mca:
                    mgConf.addMCA( mca)

        if options.counterNames:
            print( "SardanaChMg.py: %s" % options.counterNames)
            for counter in options.counterNames.split(','):
                if counter:
                    mgConf.addCounter( counter, 1, 1)

        #
        # '-n'
        #
        if options.countersNoDisplay:
            print( "SardanaChMg.py: %s" % options.countersNoDisplay)
            for counter in options.countersNoDisplay.split(','):
                if counter:
                    mgConf.addCounter( counter, 0, 1)
        #
        # '--nd' no display
        #
        if options.countersNoDisplay2nd:
            print( "SardanaChMg.py: %s" % options.countersNoDisplay2nd)
            for counter in options.countersNoDisplay2nd.split(','):
                if counter:
                    mgConf.addCounter( counter, 0, 1)
        #
        # '--no' no spock column
        #
        if options.countersNoSpockColumn:
            print( "SardanaChMg.py: %s " % options.countersNoSpockColumn)
            for counter in options.countersNoSpockColumn.split(','):
                if counter:
                    mgConf.addCounter( counter, 1, 0)
        #
        # '--ndo' no display, no spock column
        #
        if options.countersNoDisplayNoSpockColumn:
            print( "SardanaChMg.py: %s" % options.countersNoDisplayNoSpockColumn)
            for counter in options.countersNoDisplayNoSpockColumn.split(','):
                if counter:
                    mgConf.addCounter( counter, 0, 0)
                    
        if options.pilatusNames:
            print( "SardanaChMg.py: %s" % options.pilatusNames)
            for pilatus in options.pilatusNames.split(','):
                if counter:
                    mgConf.addPilatus( pilatus)


    except Exception as e:
        print( "SardanaChMg.py %s" % repr(e))
        _, _, tb = sys.exc_info()
        traceback.print_tb(tb) 
        #tb_info = traceback.extract_tb(tb)
        #filename, line, func, text = tb_info[-1]
        #print( ">>> File %s, line %s, in %s \n    %s" % (filename, line, func, text))
    #print( "chMg")
    #HasyUtils.dct_print( mgConf.hsh)

    mgConf.updateConfiguration()

    HasyUtils.pooltools.clearSCAs()
        
    # print( "# %s" % mgConf.mg.ElementList )

if __name__ == "__main__":
    main()

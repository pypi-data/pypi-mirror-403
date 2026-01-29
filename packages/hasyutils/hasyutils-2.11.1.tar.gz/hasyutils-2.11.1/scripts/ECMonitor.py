#!/usr/bin/env python
#
import PyTango
import HasyUtils
import sys, time, os
from optparse import OptionParser
flagTTY = False
#
# sms/00491711992437@sms.desy.de,thorsten.kracht@desy.de
#

def main( flagLoop, timeSleep, notify, verbose):
    """
    check the MacroServer, Pool and MGs
    if flagLoop: notify people, if the status changes to 'error'
    """
    flagMsgSent = False
    doOnce = False
    while( flagLoop or not doOnce):
        doOnce = True
        errorMsgs = []
        HasyUtils.checkECStatus( errorMsgs, verbose)
        if len( errorMsgs):
            errorMsgs.insert( 0, time.strftime("%d %b %Y %H:%M:%S", time.localtime()))
            if flagTTY:
                print( "\n".join( errorMsgs))
            if not flagMsgSent:
                flagMsgSent = True
                if flagLoop and notify:
                    HasyUtils.tellBLStaff( errorMsgs, notify.split(','))
                    print( "notifying %s" % repr( notify.split(',')))
        else:
            if flagTTY:
                print( "%s" % (time.strftime("%d %b %Y %H:%M:%S", time.localtime())))
                print( "MacroServers, Pool, Doors, ActiveMntGrp are ok")
            flagMsgSent = False

        if flagLoop: time.sleep(timeSleep)

    return

if __name__ == "__main__":
    usage = "%prog -x [-l [-t <timeSleep> ]] \n" + \
        "  Checks the status of the MacroServers, the Pool, the Doors, the ActiveMntGrp\n" + \
        "  and the elements of the ActiveMntGrp. The user is notified, if a device is\n" + \
        "  not exported or in ALARM or FAULT state.\n" + \
        "  A message is sent for each transition from OK to NOT OK.\n" + \
        "  -x    the check is executed once, the errors are displayed, no notifications\n" \
        "  -x -v  the check is executed once, verbose mode\n" \
        "  -x -l the check is repeatedly executed \n" \
        "  -x -l -n firstname.name@desy.de\n" \
        "  -x -l -n firstname.name@desy.de,sms/0049123123123@sms.desy.de" \
    
    parser = OptionParser(usage=usage)
    parser.add_option( "-x", action="store_true", dest="execute", 
                       default = False, help="execute")
    parser.add_option( "-l", action="store_true", dest="loop", 
                       default = False, help="execute repeatedly")
    parser.add_option( "-n", type="string", dest="notify", 
                       default = None, help="comma separated notify list, no blanks")
    parser.add_option( "-t", dest="timesleep", type="int", 
                       default = 60, help="sleep time when looping, def. 60s")
    parser.add_option( "-v", action="store_true", dest="verbose", 
                       default = False, help="verbose mode")
    
    (options, args) = parser.parse_args()
    if options.execute is False:
        parser.print_help()
        sys.exit(255)

    #flagTTY = False
    #if os.isatty(1):
    #    flagTTY = True
    #
    # to call this from bl_status.py (web) we always have to create output
    #
    flagTTY = True

    if not options.loop and options.notify:
        parser.print_help()
        print( "-n requires -l ")
        sys.exit(255)

    main( options.loop, options.timesleep, options.notify, options.verbose)


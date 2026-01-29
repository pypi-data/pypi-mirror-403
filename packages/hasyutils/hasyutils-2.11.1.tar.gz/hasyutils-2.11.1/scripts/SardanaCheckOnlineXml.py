#!/usr/bin/env python
#
import PyTango
import HasyUtils
import argparse

ONLINEXML = "/online_dir/online.xml"

class CheckOnlineXml:
    """
    contains the loaded macros: pathName, macro_lib and classes
    """
    def __init__( self, tags):

        self.tags = tags
        self.hshList = HasyUtils.getOnlineXML( xmlFile = ONLINEXML, cliTags = tags)

        if self.hshList is None:
            raise ValueError( "SardanaCheckOnlineXml.py: online.xml empty or not existing" )
        
    def run( self):

        count = 0
        countBad = 0
        countOffline = 0
        tagDct = {}
        for hsh in self.hshList: 
            #
            # MGs have device: 'none'
            #
            if hsh[ 'device'].upper() == 'NONE':
                continue
            #
            # if no tags were specified on the command line, 
            # produce a tag statistic
            #
            if self.tags is None and 'tags' in hsh: 
                tagList = hsh[ 'tags'].split( ',')
                for t in tagList: 
                    if t not in tagDct: 
                        tagDct[ t] = 1
                    else: 
                        tagDct[ t] += 1
            count += 1
            #
            # take care of tangoattributectctrl: 'p09/vmexecutor/eh.02/position'
            #
            lst = hsh[ 'device'].split( '/')
            if len( lst) == 3: 
                dev = hsh[ 'device']
            elif len( lst) == 4: 
                dev = '/'.join( lst[0:3])

            try: 
                p = PyTango.DeviceProxy( "%s/%s" % ( hsh[ 'hostname'], dev))
            except Exception as e: 
                print(" Failed to create proxy to %s/%s " % ( hsh[ 'hostname'], dev))
                countOffline += 1
                continue
            try: 
                sts = p.state()
            except Exception as e: 
                print(" %s/%s is offline" % ( hsh[ 'hostname'], dev))
                countOffline += 1
                continue
            if sts == PyTango.DevState.ALARM or \
               sts == PyTango.DevState.FAULT:
                print( " %s/%s in %s" % ( hsh[ 'hostname'], dev, str( sts)))
                countBad += 1

        if countBad == 0 and countOffline == 0: 
            print( "SardanaCheckOnlineXml: all %d devices OK" % count)
        else: 
            print( "SardanaCheckOnlineXml: devices in ALARM or FAULT: %d, offline %d, total %d" % 
                   (countBad, countOffline, count))
               
        if self.tags is None: 
            print( "Tags: %s" % repr( tagDct))

        print( "SardanaCheckOnlineXml: searching for conflicts,\n  identical controller names on different hosts") 
        HasyUtils.checkOnlineSardanaXml( "/online_dir/onlineSardana.xml")
        
        return 

if __name__ == '__main__':
    parser = argparse.ArgumentParser( 
        formatter_class = argparse.RawDescriptionHelpFormatter,
        description=
"Create proxies to all devices in /online_dir/online.xml\n\
and evaluate their state()\n\
Calls HasyUtils.checkOnlineSardanaXml to detect conflicts, \n\
i. e. identical controller names on different hosts (P10-reported bug)",
        epilog='''\
Examples:
  SardanaCheckOnlineXml.py
    check all devices in /online_dir/online.xml and
    display a statistic of the tags.
  SardanaCheckOnlineXml.py -t expert
    check all devices in /online_dir/online.xml having the expert tag
  SardanaCheckOnlineXml.py -t expert,user
    ... having the expert and the user tag
    ''')
    parser.add_argument( '-t', dest='tags', help='tags matching online.xml tags')
    args = parser.parse_args()

    o = CheckOnlineXml( args.tags)
    o.run()


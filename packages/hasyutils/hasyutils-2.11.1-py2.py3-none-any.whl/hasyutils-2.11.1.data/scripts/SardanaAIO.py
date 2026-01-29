#!python
#
# this script execute all scripts necessary to shutdown and
# and restart the Sardana configuration
#
import sys, os
from optparse import OptionParser
import HasyUtils
import platform
import tango
import datetime

def main():
    usage = "%prog -x \n" + \
            "  all-in-one: executes a shutdown-convert-startup sequence \n" + \
            "  \n" + \
            "  About using tags: \n" + \
            "    + Devices and MGs are selected if \n" + \
            "      - there is no -t option on the command line \n" + \
            "      - at least one element of the <tags> field matches \n" + \
            "        a tag specified on the command line\n" + \
            "    + note that there is no blank space between 'hp'\n" +\
            "      and 'core' in '-t hp,core'\n" + \
            "    + note also that the tags are stored in AIO_INFO\n" +\
            "  Examples:\n" + \
            "    SardanaAIO.py -x\n" + \
            "      execute ignoring tags\n" + \
            "    SardanaAIO.py -x -t hp,rexs,core\n" + \
            "      select only devices and MGs which are tagged 'hp', 'rexs' or 'core'\n" \
            "      the tags are stored in AIO_INFO\n" \
            "    SardanaAIO.py -x -t default\n" + \
            "      use the tags as stored in AIO_INFO\n" \
            "    SardanaAIO.py -t display\n" + \
            "      display the default tags which are stored in AIO_INFO\n" \
            "    SardanaAIO.py -x -f /online_dir/onlineKiel.xml\n" + \
            "      specify a different online.xml file"


    parser = OptionParser(usage=usage)
    parser.add_option( "-x", action="store_true", dest="execute",
                       default = False, help="execute (safety measure)")
    parser.add_option( "-f", action="store", type="string", default="/online_dir/online.xml",
                       dest="xmlFileIn", help="input xmlfile, e.g. /online_dir/onlineKiel.xml" )
    #parser.add_option( "-c", action="store_true", dest="nocoredump",
    #                   default = False, help="produce no core dumps")
    parser.add_option( "-t", action="store", dest="tags",
                       default = None, help="select devices and MGs from online.xml using tags, tags stored in AIO_INFO")
    parser.add_option( "-d", "--debug", action="store_true", dest="debug",
                       default=False, help="add debug printouts")

    (options, args) = parser.parse_args()
    #
    # read aioInfo while the Macroserver is still running
    #
    aioInfo = HasyUtils.getEnv( 'AIO_INFO')
    #
    # -t display, display the default tags
    #
    if options.tags is not None and options.tags.lower() == 'display':
        if aioInfo is None or aioInfo[ 'TAGS'] is None:
            print( "SardanaAIO.py: error '-t display' and AIO_INFO == None")
            print( "SardanaAIO.py: verify MacroServer is running")
            sys.exit( 255)
        print( "SardanaAOI3: default tags: %s" % str( aioInfo[ 'TAGS']))
        sys.exit( 255)

    if options.execute is False:
        parser.print_help()
        sys.exit(255)
    #
    # -t default
    #
    if options.tags is not None and options.tags.lower() == 'default':
        if aioInfo is None or aioInfo[ 'TAGS'] is None:
            print( "SardanaAIO.py: error '-t default' and AIO_INFO == None")
            print( "SardanaAIO.py: verify MacroServer is running")
            sys.exit( 255)
        print( "SardanaAIO.py, using default tags: %s" % aioInfo[ 'TAGS'])
    #
    #    if not options.nocoredump:
    #        if os.system( "/usr/bin/SardanaDiag.py"):
    #            sys.exit( 255)
    #
    lst = options.xmlFileIn.split( '/')
    #
    #['', 'online_dir', 'online.xml']
    #
    if lst[1] != "online_dir":
        print( "SardanaAIO: the online.xml file should be in /online_dir")
        sys.exit( 255)
    lst1 = lst[2].split( '.')
    #
    if lst1[1] != 'xml':
        print( "SardanaAIO: wrong online.xml file name syntax")
        sys.exit( 255)
    prefix = lst1[0]

    HasyUtils.toAIOLog( "SardanaAIO")

    if os.system( "/usr/bin/SardanaShutdown.py -x"):
        sys.exit( 255)

    hsh = {}
    if options.tags is None:
        hsh[ 'TAGS'] = "NoTags"
        if os.system( "/usr/bin/SardanaConvert.py -f /online_dir/%s.xml -o /online_dir/%sSardana.xml" %
                      (prefix, prefix)):
            sys.exit( 255)
    else:
        if options.tags.lower() == 'default':
            options.tags = aioInfo[ 'TAGS']

        hsh[ 'TAGS'] = "%s" % options.tags
        print( "SardanaAIO: using tags %s" % hsh[ 'TAGS'])
        if options.tags.lower().find( 'notags') != -1:
            if os.system( "/usr/bin/SardanaConvert.py -f /online_dir/%s.xml -o /online_dir/%sSardana.xml" %
                          ( prefix, prefix)):
                sys.exit( 255)
        else:
            if os.system( "/usr/bin/SardanaConvert.py -t %s -f /online_dir/%s.xml -o /online_dir/%sSardana.xml" %
                          (options.tags, prefix, prefix)):
                sys.exit( 255)

    debugtags = "-d " if options.debug else ""
    if os.system( "/usr/bin/SardanaStartup.py -f /online_dir/%sSardana.xml %s" % (prefix, debugtags)):
        sys.exit( 255)

    try:
        db = tango.Database()
        pools = db.get_server_list("Pool/*").value_string
        for pool in pools:
            print("\nSardanaAIO: check_pool_device_attributes %s" % pool)
            tmpfile = "/tmp/check_pool_device_attributes_%s.log" \
                % pool.replace("/", "_")
            logfile = "/var/tmp/ds.log/check_pool_device_attributes_%s.log" \
                % pool.replace("/", "_")
            if os.system("/usr/bin/check_pool_device_attributes %s > %s 2>&1" \
                         % (pool, tmpfile)):
                isotime = datetime.datetime.now().isoformat()
                with open('%s' % tmpfile, 'r') as f:
                    tlog = f.read()
                print("\n%s" % tlog)
                print("Hint: "
                      "comment-out one of the above devices from online.xml\n")
                with open(logfile, "a") as flog:
                    flog.write("\n%s\n\n" % isotime)
                    flog.write(tlog)
    except Exception as e:
        print("WARNING: %s" % str(e))

    print( "SardanaAIO: nxscreate onlineds -b")
    if os.system( "nxscreate onlineds -b > /dev/null"):
        sys.exit( 255)
    #
    # set AIO_INFO at the end (esp. after the macroserver has been created)
    #
    print( "SardanaAIO: AIO_INFO to %s" % repr( hsh))
    HasyUtils.setEnv( "AIO_INFO", hsh)

    print( "SardanaAIO.py terminated successfully")
    HasyUtils.toAIOLog( "SardanaAIO DONE\n---")
    sys.exit(0)

if __name__ == "__main__":
    main()

#!python
import os
import sys
import socket
import HasyUtils
import HasyUtils.pooltools
from optparse import OptionParser

hostname = socket.gethostname()

# if os.getenv( "TANGO_HOST") != hostname + ":10000" and \
#     os.getenv( "TANGO_HOST") != "localhost:10000":
#     print( "SardanaStartup.py: " + hostname + " has no Tango DB ")
#     sys.exit(255)

#
# the plan is that eventually all SardanaHosts should be known
#
# the masterHost is the host where the MacroServer is  running
#
knownHosts = {
    'hasdelay' : { 'beamline': 'delay'},
    'hasdelay2' : { 'beamline': 'delsauto'},
    'hasfdiag1' : { 'beamline': 'flash'},
    'hasfpgm1' : { 'beamline': 'flash'},
    'hasfdp' : { 'beamline': 'flash'},
    'hasfvls' : { 'beamline': 'flash'},
    'hasfmirr' : { 'beamline': 'flash'},
    'hasfwfs02': {'beamline': 'flash'},
    'haskmusixtng' : { 'beamline': 'flash'},
    'hasmfmc' : { 'beamline': 'fmc'},
    'hasmcmwsctrl01' : { 'beamline': 'lqj'},
    'hasmlqj' : { 'beamline': 'lqj'},
    'hasx0016xlab' : { 'beamline': 'metro'},
    'haso052cpu' : { 'beamline': 'metro'},
    'hasodlsauto' : { 'beamline': 'dlsauto'},
    'hasvmtn' : { 'beamline': 'p09'},
    'hasvmscdd01' : { 'beamline': 'scdd'},    # Vijay
    'hasvmscdd02' : { 'beamline': 'scdd02'},  # Tim
    'haso111tn' : { 'beamline': 'p09'},
    'haso111p' : { 'beamline': 'p09'},
    'haso112ss' : { 'beamline': 'p112'},
    'haso113deb12test' : { 'beamline': 'p99'},
    'haso113b' : { 'beamline': 'p09'},
    'haso113u' : { 'beamline': 'p09'},
    'haso107tk' : { 'beamline': 'p09'},
    'haso102m' : { 'beamline': 'p09'},
    'localhost' : { 'beamline': 'p09'},   # docker
    'hasoe026n' : { 'beamline': 'p23'},
    'haso228k' : { 'beamline': 'p09'},
    'haso232s-vm' : { 'beamline': 'p02'},
    'haso228jk' : { 'beamline': 'p09'},
    'haso228yy' : { 'beamline': 'p09'},
    'haso306aadeb12' : { 'beamline': 'p99'},
    'haso306an' : { 'beamline': 'p99'},
    'haso306b' : { 'beamline': 'p09'},
    'haso306g' : { 'beamline': 'p09'},
    'haso306s' : { 'beamline': 'p09'},
    'haso306xl' : { 'beamline': 'p99'},
    'has6117b' : { 'beamline': 'p02'},
    'haspecsicl4' : { 'beamline': 'p02'},
    'haspilcstat' : { 'beamline': 'p17'},
    'haspllabcl1' : { 'beamline': 'llab'},
    'hasp144p' : { 'beamline': 'p11'},
    'hasp136g' : { 'beamline': 'p11'},
    'haspp01eh1' : { 'beamline': 'p01'},
    'haspp01eh2' : { 'beamline': 'p01'},
    'haspp01eh3' : { 'beamline': 'p01'},
    'haspp02ch1a' : { 'beamline': 'p02'},
    'haspp021ch1' : { 'beamline': 'p02'},
    'haspp02ch2' :  { 'beamline': 'p02'},
    'haspp02oh1' :  { 'beamline': 'p02'},
    'haspp02lakl' :  { 'beamline': 'p02'},
    'haspp021ch1a' :  { 'beamline': 'p021'},
    'haspp022ch' :  { 'beamline': 'p02'},
    'haspp022chms' :  { 'beamline': 'p022test'},
    'haspp022p03oh' :  { 'beamline': 'p02'},
    'haso224w' :  { 'beamline': 'p02'},
    'has4212s' :  { 'beamline': 'p02'},  # tim schoof
    'haspp021jenkins' :  { 'beamline': 'p021'},
    'haspp03' :  { 'beamline': 'p03'},
    'haspp03nano' :  { 'beamline': 'p03nano'},
    'haspp04exp1' :  { 'beamline': 'p04'},
    'haspp04exp2' :  { 'beamline': 'p04'},
    'haspp04ff' :  { 'beamline': 'p04'},
    'haspp04max' :  { 'beamline': 'p04'},
    'haspp04ps' :  { 'beamline': 'p04'},
    'haspp04user2' :  { 'beamline': 'p04'},
    'haspp04kmic' :  { 'beamline': 'p04'},
    'haspp06ctrl' :  { 'beamline': 'p06'},
    'haspp06mc01' :  { 'beamline': 'p06'},
    'haspp06nc1' :  { 'beamline': 'p06'},
    'haspp06deb12' :  { 'beamline': 'p06'},
    'hasp029rack' :  { 'beamline': 'p06'},
    'hasp058xlab' :  { 'beamline': 'xlab'},
    'hasx0016dem' :  { 'beamline': 'xlab'},
    'hasx0016spider' : { 'beamline': 'xlab'},
    'haspp07eh2' :  { 'beamline': 'p07'},
    'haspp08' :  { 'beamline': 'p08'},
    'haspp08lisa2' :  { 'beamline': 'p08'},
    'haspp08lisasam' :  { 'beamline': 'p08'},
    'haspp08dev' :  { 'beamline': 'p08'},
    'haspp08lmuirlin' :  { 'beamline': 'p08'},
    'haspp08bliss' :  { 'beamline': 'p08'},
    'haspp09' :  { 'beamline': 'p09'},
    'haspp09dif' :  { 'beamline': 'p09'},
    'haspp09camview' :  { 'beamline': 'p09'},
    'haspp09mag' :  { 'beamline': 'p09'},
    'haspp09eh3' :  { 'beamline': 'p09'},
    'hasp044mp' :  { 'beamline': 'p09'},
    'haspp10e1' :  { 'beamline': 'p10'},
    'haspp10e2' :  { 'beamline': 'p10'},
    'haspp10lcx' :  { 'beamline': 'p10'},
    'haspp10lab' :  { 'beamline': 'p10'},
    'haszmxtest' :  { 'beamline': 'p01'},
    'haszp10remote' :  { 'beamline': 'p10'},
    'haso102ym' :  { 'beamline': 'p09'},
    'haspp11oh' :  { 'beamline': 'p11'},
    'haspp11sardana' :  { 'beamline': 'p11'},
    'haspp11exp03' :  { 'beamline': 'p11'},
    'haspp11user02' :  { 'beamline': 'p11'},
    'hasep212lab01' :  { 'beamline': 'p21'},
    'hasep212lab02' :  { 'beamline': 'p21'},
    'hasep21eh2' : { 'beamline': 'p21'},
    'hasep21eh3' : { 'beamline': 'p21'},
    'hasep211eh' : { 'beamline': 'p21'},
    'hasep212oh' : { 'beamline': 'p21'},
    'hasep22oh' :  { 'beamline': 'p22'},
    'hasep22ch1' :  { 'beamline': 'p22'},
    'hasep22ch2' :  { 'beamline': 'p22'},
    'hasep23dev' :  { 'beamline': 'p23'},
    'hasep23eh' :  { 'beamline': 'p23'},
    'hasep23hika02' :  { 'beamline': 'p23'},
    'hasep23oh' :  { 'beamline': 'p23'},
    'hasep23ch' :  { 'beamline': 'p23'},
    'hasep23swt01' :  { 'beamline': 'p23'},
    'hase027f' :  { 'beamline': 'p24'},
    'hasep24' :  { 'beamline': 'p24'},
    'hasep24eh1' :  { 'beamline': 'p24eh1'},
    'hase027tngtest' :  { 'beamline': 'p25'},
    'hasep25lab01' : {'beamline': 'p25'},
    'hasep25oh1' : {'beamline': 'p25'},
    'hasep25sxfmch1' : {'beamline': 'p25'},
    'haso107klx' :  { 'beamline': 'p09'},
    'haso107d1' :  { 'beamline': 'p09'},
    'haso107d10' :  { 'beamline': 'p09'},
    'haso107vbullseye' :  { 'beamline': 'p09'},
    'haso107lp' :  { 'beamline': 'p09'},
    'vbtkdesy' :  { 'beamline': 'p09'},
    'vbtkhome' :  { 'beamline': 'p09'},
    'hascmexp' :  { 'beamline': 'cmexp'},
    'hasnp61ch1' : { 'beamline': 'p61'},
    'hasnp62eh' : { 'beamline': 'p62'},
    'hasnp62lab' : { 'beamline': 'p62'},
    'hasnp62oh' : { 'beamline': 'p62'},
    'hasnp64' : { 'beamline': 'p64'},
    # 'hasnp64oh' :  { 'beamline': 'p64'},  must not run a Pool
    'hasnp65' :  { 'beamline': 'p65'},
    'hasnp66' :  { 'beamline': 'p66'},
    'hasx013slmlxctrl' :  { 'beamline': 'slm'},
    'hasx013slmlxctrl02' : { 'beamline': 'slm'},
    'hasm7440slmctrl' : { 'beamline': 'slm'},
    'haszvmar' :  { 'beamline': 'p104'},
    'haszvmtangout' :  { 'beamline': 'p09'},
    'hzgpp07eh1' :  { 'beamline': 'p07'},
    'hzgpp07eh3' :  { 'beamline': 'p07'},
    'hzgpp07eh4' :  { 'beamline': 'p07'},
    'hzgpp07test' :  { 'beamline': 'p07'},
    'hzgpp07test2' :  { 'beamline': 'p99'},
    'cfeld-pcx27083' : { 'beamline': 'cfeld'},
    'cfeld-pcx39081' : { 'beamline': 'khz1'},
    'cfeld-pcx29119' : { 'beamline': 'atto1'},
    'cfeld-pcx32393' : { 'beamline': 'ecomo'},
    'cfeld-pcx40672' : { 'beamline': 'atto'},
    'hasmrixs' : { 'beamline': 'rix'},
    'hzgnp61eh1' : { 'beamline': 'p61'},
    'hasx0018ctrl' : { 'beamline': 'cxns_mech'},
    'haso010lab' : { 'beamline': 'fsbt'},
    'haszvmbookworm' : { 'beamline': 'p09'},
    'haszvmp' : { 'beamline': 'p99'},
    'hasofsecmotionlab' : { 'beamline': 'p99'},
    }


def main():
    if hostname in knownHosts:
        usage = "\n\n %prog -f /online_dir/onlineSardana.xml" + \
                ("\n\n  (%s is known, -b: %s) \n" % (
                    hostname,
                    knownHosts[hostname]['beamline'],
                ))
    else:
        usage = "\n\n %prog -b p17 -f /online_dir/onlineSardana.xml \n"
    parser = OptionParser(usage=usage)
    parser.add_option( "-b", action="store", type="string", dest="beamline", help="name of the beamline")
    parser.add_option( "-f", action="store", type="string", dest="xmlfile", help="xmlfile, e.g. online.xml")
    parser.add_option("-d", "--debug", action="store_true", dest="debug",
                      default=False, help="add debug printouts")

    (options, args) = parser.parse_args()

    if options.xmlfile is None:
        parser.print_help()
        sys.exit(255)

    if options.debug:
        HasyUtils.pooltools.debug = True

    if not os.path.exists( options.xmlfile):
        print( "\nerror: %s does not exist\n" % options.xmlfile)
        sys.exit(255)

    if options.beamline is None:
        if hostname in knownHosts:
            options.beamline = knownHosts[hostname]['beamline']
        else:
            parser.print_help()
            print( "\n")
            sys.exit(255)

    if not HasyUtils.pooltools.createPools( xmlFile = options.xmlfile,
                                            beamline = options.beamline):
        print( "startup failed to create the pools")
        sys.exit(255)

    if not HasyUtils.pooltools.createMacroServer( beamline = options.beamline):
        print( "startup failed to create the MacroServer")
        sys.exit(255)

    #
    # clean the local pool
    #
    if not HasyUtils.pooltools.deleteLocalPoolDevices():
        print( "shutdown: Failed to delete the Pool devices")

    if not HasyUtils.pooltools.createPoolDevices( xmlfile = options.xmlfile, beamline = options.beamline):
        print( "startup failed to create the pool devices")
        sys.exit(255)

    if not HasyUtils.pooltools.createMeasurementGroups( xmlfile = options.xmlfile):
        print( "startup failed to create measurement groups")
        sys.exit(255)

    if not HasyUtils.pooltools.createDefaultMeasurementGroup():
        print( "startup failed to create the default measurement group")
        sys.exit(255)

    if not HasyUtils.pooltools.fixActiveMntGrp():
        print( "startup failed to fix the ActiveMntGrp")
        sys.exit(255)
    #
    # do some Sardana configuration, if necessary
    #
    if os.path.isfile( "/online_dir/SardanaConfig.py"):
        if os.system( "%s /online_dir/SardanaConfig.py" % HasyUtils.getPythonVersionSardana()) != 0:
            print( "startup failed to execute /online_dir/SardanaConfig.py")
            sys.exit(255)
        #
        # restart the MacroServer because SardanaConfig might
        # has changed the MacroPath
        #
        print( "SardanaStartup: /online_dir/SardanaConfig.py has been executed, so restart the MacroServer")
        serverName = 'MacroServer/' + HasyUtils.getHostname()
        HasyUtils.restartServer( serverName)

    print( "SardanaStartup finished successfully")
    sys.exit(0)


if __name__ == "__main__":
    main()

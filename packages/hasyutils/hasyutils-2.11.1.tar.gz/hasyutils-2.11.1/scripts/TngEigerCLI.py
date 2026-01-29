#!/usr/bin/env python
'''

'''

import argparse, re
import requests
import sys, os, time
import PyTango
import HasyUtils

import urllib

try:
    # For Python 3.0 and later
    from urllib.request import urlopen
except ImportError:
    # Fall back to Python 2's urllib2
    from urllib2 import urlopen

EIGER2_NAME = "p99/eiger/eh.01"
EIGER2_FILEWRITER = "p99/eiger_filewriter/eh.01"
EPILOG = '''\

  TngEigerCLI.py p62e2x4m 
        list selected attributes from EigerPars_<name> 
  TngEigerCLI.py p62e2x4m --ct 1.5
        set the count time to 1.5 s in EigerPars_<name> and in the device

  TngEigerCLI.py p62e2x4m --list       list the DCU files
  TngEigerCLI.py p62e2x4m --download   download the DCU files to ScanDir
  TngEigerCLI.py p62e2x4m --download_scandir   download the DCU files to ScanDir
  TngEigerCLI.py p62e2x4m --download_dldir  download the DCU files to DownloadDirectory (Tango server attr.)
  TngEigerCLI.py p62e2x4m --delete     delete the DCU files and directories

  TngEigerCLI.py p62e2x4m --nbt 10 --ct 0.01 --ipf 10 --nbi 10
    10 software trigger, countTime 0.01, frameTime = ct + frameTimeMin
    images per file 10, number of images 10
    Update EigerPars_<name> and the device

  TngEigerCLI.py p62e2x4m --ints     write EigerPars_<name> then execute internal trigger run 
  TngEigerCLI.py p62e2x4m --exts     write EigerPars_<name> then execute external trigger run 
  TngEigerCLI.py p62e2x4m --extssim  write EigerPars_<name> then execute a sim. external trigger run 

    '''


def displayFurtherHelp(): 

    print( "\n\
\n\
The detector configuration parameter photon_energy has to be set to the X-ray energy \n\
used for the experiment. \n\
CountTime refers to the actual time the detector counts photons and frame_time is the \n\
interval between acquisitions of subsequent frames (i.e. period). IT is set automatically. \n\
The number of images in a series of images, after a trigger, is configured with the parameter NbImages.\n\
The detector always considers a trigger as the start of a series of n images. For example \n\
a single image is considered as a series of images containing 1 image. \n\
Once the detector has been armed a series can be started by issuing a trigger command or \n\
triggering the detector using an electronic pulse on the external trigger input (ExtIn). \n\
\n\
Setting values greater than 1 for NbTrigger allows several trigger commands or external trigger \n\
pulses per arm/disarm sequence. This mode allows recording several series of NbImages with the \n\
same parameters. The resulting number of frames is product of ntrigger and nimages. In external \n\
enable modes the parameter nimages is ignored (i.e. always 1) and the number of frames therefore \n\
has to be configured using the detector configuration parameter NbTrigger.\n\
\n\
The filewriter parameter FilenamePattern sets the name template/pattern for the HDF5 files. \n\
The pattern $id is replaced with a sequence identification number and therefore can be used \n\
to discriminate between subsequent series. The sequence identification number is reset after \n\
initializing the detector. The parameter ImagesPerFile sets the number of images stored \n\
per data file. A value of 1000 (default) means that for every 1000th image, a data file is \n\
created. If for example, 1800 images are expected to be recorded, the arm, trigger, disarm \n\
sequence means that a master file is created in the data directory after arming the detector. \n\
The trigger starts the image series and after 1000 recorded images one data container is made\n\
available on the buffer of the detector control unit. No further files will made available until \n\
the series is finished either by completing the nth image (nimages) of the nth trigger (ntrigger)\n\
or by ending the series using the detector command disarm. As soon as either criteria is met the \n\
second data container is closed and made available for fetching.\n\
")


def parseCLI():
    parser = argparse.ArgumentParser( 
        formatter_class = argparse.RawDescriptionHelpFormatter,
        description='''\

Command line interface to the Eiger detectors 

''', 
        epilog=EPILOG + str( HasyUtils.TgUtils.EIGER_DETECTORS.keys() ))
    #
    # notice that 'pattern' is a positional argument
    #
    parser.add_argument( 'namePattern', nargs='*', default = None,  
                         help=repr( sorted( HasyUtils.TgUtils.EIGER_DETECTORS.keys())))

    parser.add_argument( "--pe", 
                         dest='PhotonEnergy', default = None, 
                         help='the x-ray energy of the experiment [eV], e.g.: 8980 eV')
    parser.add_argument( "--et", 
                         dest='EnergyThreshold', default = None, 
                         help='energy threshold [eV], e.g.: 4020 eV')

    parser.add_argument( "--ct",  
                         dest='CountTime', default = None, 
                         help='the time the detector counts photons')

    parser.add_argument( '--pf',  
                         dest='Prefix', default = None, 
                         help='prefix used in current/raw/SingleShots/<devName>/<prefix>_$id')

    parser.add_argument( "--nbt", 
                         dest='NbTriggers', default = None, 
                         help='set NbTriggers attribute, e.g.: 1')

    parser.add_argument( "--nbi", 
                         dest='NbImages', default = None,
                         help='the number of images in a series of images after a trigger')

    parser.add_argument( "--ipf", 
                         dest='ImagesPerFile', default = None, 
                         help='images per file')

    parser.add_argument( '--ints',
                         dest='runInts', default = None, action="store_true", 
                         help='execute a run with using internal triggers ')

    parser.add_argument( '--tm', 
                         dest='TriggerMode', default = None, action="store_true", 
                         help='"ints" or "exts"')

    parser.add_argument( '--exts',
                         dest='runExts', default = None, action="store_true", 
                         help='execute a run with using external triggers')

    parser.add_argument( '--extssim',
                         dest='runExtsSim', default = None, action="store_true", 
                         help='execute a run with using external triggers, simulate with oreg ')

    parser.add_argument( '--fh',
                         dest='furtherHelp', default = None, action="store_true", 
                         help='Displays some lines from the Dectris docu')

    parser.add_argument( '--default',
                         dest='default', default = None, action="store_true", 
                         help='set EigerPars with default attributes, no I/O')

    parser.add_argument( '--list',
                         dest='list', default = None, action="store_true", 
                         help='list the files on the DCU')

    parser.add_argument( '--init',
                         dest='init', default = None, action="store_true", 
                         help='sets the Eiger attributes to some defaults')

    parser.add_argument( '--delete',
                         dest='delete', default = None, action="store_true", 
                         help='delete the files on the DCU')

    parser.add_argument( '--download',
                         dest='download', default = None, action="store_true", 
                         help='download files to ScanDir')

    parser.add_argument( '--download_scandir',
                         dest='download_scandir', default = None, action="store_true", 
                         help='download files to ScanDir')

    parser.add_argument( '--download_dldir',
                         dest='download_dldir', default = None, action="store_true", 
                         help='download files to DownloadDirectory (Tango server attribute)')

    parser.add_argument( '--write',
                         dest='write', default = None, action="store_true", 
                         help='write EigerPars_<name> dict to servers')

    parser.add_argument( '--read',
                         dest='read', default = None, action="store_true", 
                         help='read selected attributes from servers')

    parser.add_argument( '--display',
                         dest='display', default = None, action="store_true", 
                         help='display the MS env. dictionary EigerPars_<name>')

    args = parser.parse_args()

    return args, parser


def main():

    args, parser = parseCLI()

    if len( args.namePattern) == 0: 
        parser.print_help()
        return 

    name = args.namePattern[0]

    if name not in HasyUtils.TgUtils.EIGER_DETECTORS:
        print( "%s not in %s" % ( name, repr( sorted( HasyUtils.TgUtils.EIGER_DETECTORS.keys()))))
        return 

    if args.furtherHelp: 
        displayFurtherHelp()
        return 

    try: 
        eiger = HasyUtils.TgUtils.Eiger( name)
    except Exception as e: 
        print( "TngEigerCLI: %s" % repr( e))
        return 

    if args.default: 
        eiger.setDefaults( name)
        return 

    if args.read: 
        eiger.readDetector()
        return 

    if args.display: 
        eiger.displayEigerPars()
        return 

    parChanged = eiger.saveCLIArgs( args) 

    if args.init: 
        eiger.initDetector()
        return 

    #
    # if an attribute changed on the command line, 
    # update the device (not only update the MS variable
    #
    if args.write or parChanged:
        eiger.writeAttrs()
        eiger.readDetector()
        return 

    if args.list: 
        eiger.crawler( eiger.dataURL, eiger.listFunc)
        return 

    if args.delete: 
        eiger.crawler( eiger.dataURL, eiger.deleteFunc)
        eiger.crawler( eiger.dataURL, eiger.deleteDirFunc)
        return 

    if args.download or args.download_scandir: 
        eiger.crawler( eiger.dataURL, eiger.downloadFunc_scandir)
        return 

    if args.download_dldir: 
        eiger.crawler( eiger.dataURL, eiger.downloadFunc_dldir)
        return 

    if args.runInts is True:
        eiger.runInts()
        return 

    if args.runExts is True:
        eiger.runExts( True)
        return 

    if args.runExtsSim is True:
        eiger.runExts( False)
        return 

    eiger.displayEigerPars()

    return 
 
if __name__ =="__main__":
   main()

        

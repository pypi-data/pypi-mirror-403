#!/usr/bin/env python3
'''
nxsreader, the interface to the nxsReader class 
  $HOME/gitlabDESY/Sardana/hasyutils/HasyUtils/nxsReader.py
'''

__all__ = ['nxsreader']

import HasyUtils
import argparse as _argparse
import os as _os


def _main():

    parser = _argparse.ArgumentParser( 
        formatter_class = _argparse.RawDescriptionHelpFormatter,
        description="nxsreader, the CLI to the nxsReader class", 
        epilog='''\
Examples:
  nxsreader.py tst_00204.nxs
    displays groups, datasets, links and attributes, using h5cpp

  nxsreader.py --h5py tst_00204.nxs 
    displays groups, datasets, links and attributes, using h5py

  nxsreader nxsTest_00004.nxs --dataset
    display datasets

    ''')
    parser.add_argument( 'fileName', help='the name of the file to be processed')
    parser.add_argument( '--dataset', dest="datasetFlag", action="store_true",help='display datasets')
    parser.add_argument( '--h5py', dest="h5pyFlag", action="store_true",help='use h5pyReader, otherwise pniReader')
    args = parser.parse_args()


    if not _os.path.exists( args.fileName):
        raise Exception( "nxsreader: %s does not exist" % args.fileName)

    if args.h5pyFlag: 
        nxsObj = HasyUtils.h5pyReader( args.fileName)
    else:
        nxsObj = HasyUtils.pniReader( args.fileName)

    if HasyUtils.argSupplied( args.datasetFlag) and args.datasetFlag:
        lines = nxsObj.getDatasetNamesInfo()
        for line in lines: 
            print( line)
        return

    else: 
        lines = nxsObj.display()    
        for line in lines: 
            print( line)
 
    return 
#
# end of main()
#

if __name__ == '__main__':
    _main()

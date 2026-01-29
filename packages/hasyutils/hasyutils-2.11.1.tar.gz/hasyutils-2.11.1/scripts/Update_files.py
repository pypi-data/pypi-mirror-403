#!/usr/bin/env python3
#
import sys, os, argparse
import HasyUtils

DIR_TARGET9 = "/usr/bin"
DIR_TARGET10 = "/usr/bin"

def main(): 
    parser = argparse.ArgumentParser( 
        formatter_class = argparse.RawDescriptionHelpFormatter,
        usage='%(prog)s [options]', 
        description= "Update local files on some host\n \
  Examples: \n\
    ./Update_files.py haspp99 \n\
       update files that have changed \n\
        \n\
    ./Update_files.py haspp99 new\n\
      copy all files\n\
")
    
    parser.add_argument( 'argsCli', nargs='*', default='None', help='host [new]')
    args = parser.parse_args()

    if len( args.argsCli) != 1 and len( args.argsCli) != 2: 
        print( "OtherUtils.updateFiles expecting 'host [new]'")
        sys.exit( 255)

    host = args.argsCli[0]
    flagNew = 'NotNew'
    if len( args.argsCli) == 2:
        flagNew = args.argsCli[1]
        if flagNew.lower() != 'new': 
            print( "Update_files expecting 'host [new]'")
            sys.exit( 255)

    HasyUtils.updateFiles( target9 = DIR_TARGET9, 
                           target10 = DIR_TARGET10, 
                           host = host, 
                           fileName = "Files.lis", 
                           flagNew = flagNew)

    return 

if __name__ == "__main__": 
    main()





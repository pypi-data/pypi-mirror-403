#!/usr/bin/env python
""" 
  deletes motor groups from the pool
  this is a fix for a bug reported by P23, see notes, 22.10.2020
  [rt #1002115]
"""

import sys
import HasyUtils.pooltools
from optparse import OptionParser

def main():

    usage = "usage: %prog -x "
    parser = OptionParser(usage=usage)
    parser.add_option( "-x", action="store_true", dest="execute", default = False, 
                       help="deletes all MotorGroups from the Pool")
    
    (options, args) = parser.parse_args()
    
    if options.execute is False:
        parser.print_help()
        sys.exit(255)

    HasyUtils.pooltools.deleteMotorGroups()
            
    return

if __name__ == "__main__":
    main()



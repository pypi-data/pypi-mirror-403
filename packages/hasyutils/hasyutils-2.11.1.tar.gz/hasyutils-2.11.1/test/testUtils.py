#!/bin/env python
'''
'''
import HasyUtils

def execCheckstttt( msg):
    argout = True

    if not HasyUtils.checkECStatus():
        print( "*** %s, checkECStatus returned False" % msg)
        argout = False
        
    return argout


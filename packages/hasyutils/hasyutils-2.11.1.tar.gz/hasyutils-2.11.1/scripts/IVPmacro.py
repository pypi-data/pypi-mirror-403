#!/usr/bin/env python

"""
the installation verification procedure macro

this file has to be copied to ~/sardanaMacros
"""

__all__ = ["IVPmacro"]

import PyTango
from sardana.macroserver.macro import *
from sardana.macroserver.macro import macro
import PyTango

class IVPgeneralFeatures(Macro):
    """general features IVP"""
    
    param_def = []
    result_def = [[ "result", Type.Boolean, None, "completion status" ]]

    def run(self):

        self.writer = self.output
        if self.mwTest().getResult(): 
            self.writer = self.mwOutput

        ghSelectorOld = self.gh_getSelector().getResult()
        gcSelectorOld = self.gc_getSelector().getResult()
        gsSelectorOld = self.gs_getSelector().getResult()

        self.writer( "IVPgenFeat: ghSelector to ghSel")
        if not self.gh_setSelector( "ghSel"):
            self.writer( "IVPgenFeat: failed to gh_selector()")
            return False
        if self.gh_getSelector().getResult() == "ghSel":
            self.writer( "confirmed")
        else:
            self.writer( "failed")
            return False            

        self.writer( "IVPgenFeat: gcSelector to gcSel")
        if not self.gc_setSelector( "gcSel"):
            self.writer( "IVPgenFeat: failed to gc_selector()")
            return False
        if self.gc_getSelector().getResult() == "gcSel":
            self.writer( "confirmed")
        else:
            self.writer( "failed")
            return False            

        self.writer( "IVPgenFeat: gsSelector to gsSel")
        if not self.gs_setSelector( "gsSel"):
            self.writer( "IVPgenFeat: failed to gs_selector()")
            return False
        if self.gs_getSelector().getResult() == "gsSel":
            self.writer( "confirmed")
        else:
            self.writer( "failed")
            return False            

        self.gh_setSelector( ghSelectorOld)
        self.gc_setSelector( gcSelectorOld)
        self.gs_setSelector( gsSelectorOld)


listOfMacros = [
    ["lsenv"],
    ["lsmeas"],
    ["wm", "exp_dmy01"],
    ["mv", "exp_dmy01", "0"],
    ["mv", "exp_dmy01", "1"],
    ["mv", "exp_dmy01", "0"],
    ["ascan", "exp_dmy01", "0", "1", "50", "0.1"],
    ["mvsa", "peak", "0"],
    ["a2scan", "exp_dmy01", "0", "1", "exp_dmy02", "3", "7", "50", "0.1"],
    ["mvsa", "peak", "0"],
    ["dscan", "exp_dmy01", "-1", "1", "50", "0.1"],
    ["mvsa", "peak", "0"],
    ["d2scan", "exp_dmy01", "-1", "1", "exp_dmy02", "-0.1", "0.1", "50", "0.1"],
    ["mvsa", "peak", "0"],
    ]

class IVPListOfMacros(Macro):
    """IVP for a list of macros."""
    
    param_def = []
    result_def = [[ "result", Type.Boolean, None, "completion status" ]]

    def run(self):

        self.writer = self.output
        if self.mwTest().getResult(): 
            self.writer = self.mwOutput

        exp_dmy01 = PyTango.DeviceProxy( "exp_dmy01")
        for elm in listOfMacros:
            self.writer( "IVPListOfMacros %s" % str( elm))
            mcr, pars = self.createMacro( elm)
            res = self.runMacro(mcr)
            if not res is None:
                self.writer( "IVPListOfMacros: result %s" % repr( res))
            if elm[0] == "mv":
                self.writer( "IVPListOfMacros %s is at %g" % (exp_dmy01.alias(), exp_dmy01.position))
        return True

class IVPmacro(Macro):
    """the main IVP macro """

    param_def = []
    result_def = [[ "result", Type.Boolean, None, "completion status" ]]

    def run(self):
        self.writer = self.output
        a = self.mwTest()
        if a.getResult(): 
            self.writer = self.mwOutput

        result = False

        if not self.IVPListOfMacros().getResult(): 
            self.writer( "IVPListOfMacros failed")
            return result

        if not self.IVPgeneralFeatures().getResult(): 
            self.writer( "IVPgeneralFeatures failed")
            return result

                

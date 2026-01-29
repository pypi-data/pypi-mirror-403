#!/usr/bin/env python
""" this module contains functions that manage the Pool and MacroServer """
import PyTango
import json
import HasyUtils
import os
import sys

import HasyUtils.MgUtils

db = None


def _getServerProxies(servername):
    """Return the pool proxies."""
    argout = []
    for srv in HasyUtils.getServerNameByClass(servername):
        argout.append(PyTango.DeviceProxy(
            db.get_device_name(srv, servername).value_string[0]))
    return argout


def _findConfigServer():
    recProxies = _getServerProxies("NXSRecSelector")
    recproxy = None
    conf = None
    localhost = HasyUtils.getHostname()
    if recProxies and len(recProxies) == 1:
        recproxy = recProxies[0]
        conf = recproxy.configDevice
    else:
        for recp in recProxies:
            if recp.name().split("/")[-1] == localhost:
                recproxy = recp
                conf = recproxy.configDevice
                break
    if not conf:
        confProxies = _getServerProxies("NXSConfigServer")
        if confProxies and len(confProxies) == 1:
            conf = confProxies[0]
        else:
            for recp in confProxies:
                if recp.name().split("/")[-1] == localhost:
                    conf = recp
                    break
    if conf:
        return conf


def _getComponentDataSources(hshList):
    compdsources = {}

    for hsh in hshList:
        if 'sardananame' in list( hsh.keys()):
            name = hsh["sardananame"]
        elif 'name' in list( hsh.keys()):
            name = hsh["name"]
        if name:
            if 'nxsdatasource' in list( hsh.keys()):
                module = hsh["module"].strip().lower()
                if module not in list( moduleAttributes.keys()):
                    print( "nxsconftools.setComponentDataSources " \
                        + "%s module of %s not supported" % (module, name))
                    sys.exit(255)
                fcmp = hsh["nxsdatasource"].strip()
                if len(fcmp) > 4 and fcmp[0] == '[' and fcmp[-1] == ']':
                    fcmp = fcmp[1:-1]
                    active = False
                else:
                    active = True
                ellist = fcmp.strip().split(".")
                comp = None
                tempds = None
                if ellist:
                    comp = ellist[0]
                    if len(ellist) == 2:
                        tempds = ellist[1]
                if comp and comp not in compdsources:
                    compdsources[comp] = {}
                if tempds:
                    if active:
                        compdsources[comp][tempds] = name
                    else:
                        compdsources[comp][tempds] = ""
    return compdsources


def setComponentDataSources(**a):
    """Set componente datasources."""
    print( "setComponentDataSources: %s" % a)
    if not MOD_ATTRS:
        print( "nxsconftools.setComponentDataSources: " \
            + "Can't find moduleAttribute in nxstools.nxsdevicetools on", \
            os.getenv('TANGO_HOST'))
        return 0

    if 'xmlfile' not in list( a.keys()):
        print( "nxsconftools.setComponentDataSources: no xmlfile supplied")
        return 0

    hshList = HasyUtils.getOnlineXML( xmlFile = a['xmlfile'])

    if 'configdevice' not in list( a.keys()):
        configserver = _findConfigServer()
    else:
        configserver = a['configdevice']

    if not configserver:
        print( "nxsconftools.setComponentDataSources failed to find NXSConfigServer")
        sys.exit(255)
    print( "setComponentDataSources: ConfigServer %s has been found" % configserver)

    if os.system("nxscreate onlineds  %s -b -r %s" % (
            a['xmlfile'], configserver)):
        sys.exit(255)

    cnfproxy = PyTango.DeviceProxy(configserver)

    compdsources = _getComponentDataSources(hshList)

    if compdsources:
        print( "setComponentDataSources: call setComponentDataSources " \
            "on ConfigServer %s with:\n%s" % (configserver, compdsources))
        cnfproxy.setComponentDataSources(str(json.dumps(compdsources)))
    return 1

#
#
#
try:
    db = PyTango.Database()
except:
    print( "Can't connect to tango database on %s" % os.getenv('TANGO_HOST'))
    sys.exit(255)

try:
    from nxstools.nxsdevicetools import moduleAttributes
    MOD_ATTRS = True
except ImportError:
    MOD_ATTRS = False


if __name__ == "__main__":
    pass

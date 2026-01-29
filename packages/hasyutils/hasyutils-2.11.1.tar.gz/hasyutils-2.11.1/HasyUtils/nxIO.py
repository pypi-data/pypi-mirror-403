#!/usr/bin/env python

""" Client for the NeXus Selection Server """

import PyTango
import json
from datetime import datetime
from pytz import timezone
import pprint
import os, sys
import numpy
#import HasyUtils

class nxIO(object):

    ## constructor
    def __init__(self, selector):

        # Selector Server
        self.selector = PyTango.DeviceProxy(selector)
        # NeXus Writer
        self.writer = PyTango.DeviceProxy(self.selector.WriterDevice)
        self.writer.set_timeout_millis(30000)

        # Selected Channels
        # datasources = self.selector.DataSources
        self.appendEntry = self.selector.AppendEntry

        # user data
        self.datarecord = self.selector.UserData
        self.berlin = timezone('Europe/Berlin')
        self.fmt = '%Y-%m-%dT%H:%M:%S.%f%z'

        # name of a dynamic component
        self.dynamicCP = "__dynamic_component__"

        self.mcl = {"INIT": {}, "STEP": {}, "FINAL": {}}

        self.globalDct = {}
        self.components = []
        self.proxies = {}
        self.clientSources = []
        self.attributeNames = {}
        self.configurationXML = ""

        self.attrsToCheck = ["Value", "Position", "Counts", "Data",
                             "Voltage", "Energy", "SampleTime"]
        self.db = PyTango.Database()

        #
        # { "exp_c01" : "expchan/sis3820_exp/1", ...}  
        #
        self.dataSources = {}
        self.fillDataSources()

        self.tTn = {PyTango.DevLong64: "NX_INT64",
                    PyTango.DevLong: "NX_INT32",
                    PyTango.DevShort: "NX_INT16",
                    PyTango.DevUChar: "NX_UINT8",
                    PyTango.DevULong64: "NX_UINT64",
                    PyTango.DevULong: "NX_UINT32",
                    PyTango.DevUShort: "NX_UINT16",
                    PyTango.DevDouble: "NX_FLOAT64",
                    PyTango.DevFloat: "NX_FLOAT32",
                    PyTango.DevString: "NX_CHAR",
                    PyTango.DevBoolean: "NX_BOOLEAN"}

    def fillDataSources( self):
        lst = []
        if self.selector.DataSources:
            lst += self.selector.DataSources

        for elm in lst:
            try:
                self.dataSources[elm] = self.db.get_device_alias( elm)
            except:
                continue
        #+++print( pprint.pformat(self.dataSources))
    def openFile(self, nxsfile):
        # open the file
        print( "openFile %s" % nxsfile)
        self.writer.Init()
        self.writer.FileName = nxsfile
        self.writer.OpenFile()

    def getClientSources(self):
        return self.clientSources

    #
    # mostly "Value", but ...
    #
    def findAttributeName(self, proxy):
        result = None
        for at in self.attrsToCheck:
            if hasattr(proxy, at):
                result = at
                break
        return result

    @classmethod
    def isTangoDevice(cls, devName):
        try:
            dp = PyTango.DeviceProxy(str(devName))
            dp.ping()
            return dp
        except:
            # print( devName, " is not Tango device")
            return None

    def getShapeType(self, source):
        vl = None
        shp = []
        dt = None
        ap = PyTango.AttributeProxy(source)
        da = None
        ac = None

        try:
            ac = ap.get_config()
            if ac.data_format != PyTango.AttrDataFormat.SCALAR:
                da = ap.read()
                vl = da.value
        except Exception:
            if ac and ac.data_format != PyTango.AttrDataFormat.SCALAR \
                    and da is None:
                raise

        if vl is not None:
            shp = list(numpy.shape(vl))
        elif ac is not None:
            if ac.data_format != PyTango.AttrDataFormat.SCALAR:
                if da.dim_x and da.dim_x > 1:
                    shp = [da.dim_y, da.dim_x] \
                        if da.dim_y \
                        else [da.dim_x]
        if ac is not None:
            dt = self.tTn[ac.data_type]
        return (shp, dt)

    def fetchClientSources(self):
        self.clientSources = json.loads(self.selector.componentClientSources([]))
        dynClientSources = json.loads(
            self.selector.componentClientSources([self.dynamicCP])) \
            if self.dynamicCP else []
        self.clientSources.extend(dynClientSources)
        for elm in self.clientSources:
            sys.stdout.write( "comp and dynComp")
            sys.stdout.flush()
            print( pprint.pformat(elm, indent=1))
        self.mcl = {"INIT": {}, "STEP": {}, "FINAL": {}}
        shapes = json.loads(self.selector.channelProperties("shape"))
        types = json.loads(self.selector.channelProperties("data_type"))
        for cs in self.clientSources:
            self.mcl[cs["strategy"]][cs["record"]] = cs["dsname"]

            dp = self.isTangoDevice(cs["record"])
            self.proxies[cs["record"]] = dp
            if dp:
                self.attributeNames[cs["record"]] = self.findAttributeName(dp)
                if self.attributeNames[cs["record"]]:
                    source = "%s:%s/%s/%s" % (
                        dp.get_db_host(), dp.get_db_port(),
                        dp.name(), self.attributeNames[cs["record"]])
                    shape, nxstype = self.getShapeType(source)
                    print( "Source: %s %s %s" % ( source, shape, nxstype))
                    if shape is not None:
                        shapes[cs["dsname"]] = shape
                    if nxstype is not None:
                        types[cs["dsname"]] = nxstype
        self.selector.setChannelProperties(["shape", json.dumps(shapes)])
        self.selector.setChannelProperties(["data_type", json.dumps(types)])

    def createConfiguration(self):
        # components
        components = self.selector.Components
        if components:
            self.components = list(components)
        #
        # dynamicCP contains all dynamic data sources
        #
        self.dynamicCP = str(self.selector.createDynamicComponent([]))
        self.fetchClientSources()
        self.selector.RemoveDynamicComponent(self.dynamicCP)

        self.dynamicCP = str(self.selector.createDynamicComponent([]))
        self.selector.updateConfigVariables()

        if self.dynamicCP:
            self.components.append(self.dynamicCP)
        self.configurationXML = str(
            self.selector.CreateWriterConfiguration(self.components))
        self.selector.RemoveDynamicComponent(self.dynamicCP)

        return

    def openEntry(self, data=None):

        self.createConfiguration()

        self.writer.XMLSettings = self.configurationXML

        self.globalDct = json.loads(self.datarecord)
        # get start_time
        starttime = self.berlin.localize(datetime.now())
        self.globalDct["start_time"] = str(
            starttime.strftime(self.fmt))

        if isinstance(data, dict):
            self.globalDct.update(data)

        missing = list(
            set(self.mcl['INIT'].keys()) - set(self.globalDct.keys()))
        if missing:
            raise Exception("Missing INIT CLIENT data: %s" % missing)
        self.writer.JSONRecord = json.dumps({"data": self.globalDct})
        self.writer.OpenEntry()

    def execStep(self, data=None):
        localDct = {}
        if isinstance(data, dict):
            localDct = data 
        missing = list(
            (set(self.mcl['STEP'].keys()) - set(self.globalDct.keys())
             - set(localDct.keys())))

        # if the record name is Tango device we can try to read its Value
        for dv in missing:
            if self.proxies[str(dv)]:
                value = self.proxies[str(dv)].read_attribute(
                    self.attributeNames[str(dv)]).value
                if hasattr(value, "tolist"):
                    value = value.tolist()
                localDct[dv] = value
            else:
                localDct[dv] = "SomeValue"
        missing = list(
                (set(self.mcl['STEP'].keys())) - set(localDct.keys())
                - set(self.globalDct.keys()))
        if missing:
            raise Exception("Missing STEP CLIENT data: %s" % missing)
        print( "RECORD: %s" % localDct)
        #print( pprint.pformat(localDct, indent=1, depth=1))
        self.writer.Record(json.dumps({"data": localDct}))

    def closeEntry(self, data=None):
        endtime = self.berlin.localize(datetime.now())
        self.globalDct["end_time"] = str(endtime.strftime(self.fmt))

        if isinstance(data, dict):
            self.globalDct.update(data)

        missing = list(
            set(self.mcl['FINAL'].keys()) - set(self.globalDct.keys()))
        if missing:
            raise Exception("Missing FINAL CLIENT data: %s" % missing)

        self.writer.JSONRecord = json.dumps({"data": self.globalDct})
        self.writer.CloseEntry()

    def closeFile(self):
        self.writer.CloseFile()

    def getDeviceNameByAlias( self, alias):
        """Return the tango device which is referred to by an alias """
        return self.dbproxy.get_device_alias( alias)

    def getCounters( self):
        #
        # return the selected counters, e.g. ["exp_c01", "exp_c02"]
        #
        devices = []
        for elm in list( self.dataSources.keys()):
            if self.dataSources[elm].find( "sis3820") > 0:
                devices.append( elm)
        devices.sort()
        return devices

    def getMCAs( self):
        #
        # return the selected MCAs, e.g. [{exp_mca01 => 2048}, ...]
        #
        mcas = []
        for elm in list( self.dataSources.keys()):
            if self.dataSources[elm].find( "mca") < 0:
                continue
            hsh = {}
            try:
                proxy = PyTango.DeviceProxy(elm)
                hsh[elm] = proxy.DataLength
            except:
                continue
            mcas.append(hsh)
        return mcas

    def getTimers( self):
        #
        # return the selected timers, e.g. ["exp_t01", "exp_t02"]
        #
        devices = []
        for elm in list( self.dataSources.keys()):
            if self.dataSources[elm].find( "dgg2") > 0:
                devices.append( elm)
        devices.sort()
        return devices

if __name__ == '__main__':
    print( "this is nxIO.py")



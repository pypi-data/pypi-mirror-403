#!/usr/bin/env python 
'''
pniReader( fileName) gives access to a nexus/hdf5 file

o = HasyUtils.pniReader()
o = HasyUtils.h5pyReader()


  o.display()
  o.getAttributeNames()
  o.getAttributeObjs()
  o.getAttributeValue()
  o.getDataset()
  o.getDatasetNames()
  o.getDatasetNames1D()
  o.getDatasetNames2D()
  o.getDatasetNamesInfo()
  o.getDatasetObjs()
  o.getDatasetObj()
  o.getData1D()
  o.getData2D()
'''

__all__ = ['pniReader', 'h5pyReader', 'argSupplied']

import os as _os
import sys as _sys
try: 
    from pninexus import h5cpp
except: 
    pass
try: 
    import h5py
except: 
    pass
import numpy

def argSupplied( arg):
    '''
    for optional arguments that may have a parameter. 
    return True, if the optional arguments was supplied, with or 
    without a parameter, e.g. '--dev' or '--dev exp.01' --> true
    '''
    if arg is None:
        return True
    #
    # ndim = 2
    #
    elif not type( arg) is str:
        return True
    elif arg.find( 'Missing') == 0:
        return False
    else:
        return True

class nxsDataset(): 
    '''
    obj.name
      /scan/data/eh_c01
      numpy.ndarray, array([202.15531666, 196.62079061...])
    obj.data
      to avoid multiple reads
    obj.linkType HARD/SOFT
      SOFT
    obj.targetType None/<path> 
      /scan/instrument/detector/collection/eh_c01
    '''
    def __init__( self, name): 
        self.name = name
        return 

class nxsAttribute(): 
    def __init__( self, parent, name): 
        self.parent = parent 
        self.name = name 
        return 

class genericNxsReader( object): 
    def __init__( self):
        self._datasetNames = []
        self._datasetNames1D = []
        self._datasetNames2D = []
        self._datasetInfos = []
        self._displayLines = []
        self._datasetObjs = []
        self._attributeObjs = []
        self._attributeNames = []
        return 

    #
    # generic
    #
    def getDatasetObjs( self): 
        """
        return a list of Dataset() objects
        """
        if len( self._datasetObjs) == 0:
            self._getDatasetObjs( self._root)
        return self._datasetObjs

    #
    # generic
    #
    def getDatasetObj( self, name): 
        """
        return a Dataset() object
        """
        if len( self._datasetObjs) == 0:
            self._getDatasetObjs( self._root)
        for o in self._datasetObjs: 
            if str( o.name) == name:
                return o
        return None

    #
    # generic
    #
    def getAttributeObjs( self): 
        """
        return a list of nxsAttribute() objects
        """
        if len( self._datasetObjs) == 0:
            self._getDatasetObjs( self._root)
        return self._attributeObjs

    #
    # generic
    #
    def getAttributeValue( self, parent, name):
        """
        returns a value of an attribute, e.g.: 
            self.getAttributeValue( 'scan/program_name', 'scan_command')
        """
        if len( self._datasetObjs) == 0:
            self.getDatasetObjs()
        for o in self._attributeObjs: 
            if str( o.parent) == parent and o.name == name: 
                return str( o.value) 
        return None

    #
    # generic
    #
    def getAttributeNames( self):
        """
        returns alist of attribute names, parent and name
        """
        if len( self._datasetObjs) == 0:
            self.getDatasetObjs()
        self._attributeNames = []
        for o in self._attributeObjs: 
            self._attributeNames.append( str( o.parent) + " " + o.name)
        return self._attributeNames

    #
    # generic
    #
    def getScanCommand( self): 

        return self.getAttributeValue( '/scan/program_name', 'scan_command')

    #
    # generic
    #
    def getDatasetNames( self):
        """
        returns list containing all dataset names, the strings
        contain HARD or SOFT
        """
        if len( self._datasetObjs) == 0:
            self.getDatasetObjs()
        self._datasetNames = []
        for o in self._datasetObjs: 
            self._datasetNames.append( o.name)
        return self._datasetNames

    #
    # generic
    #
    def getDatasetNamesInfo( self):
        """
        returns list containing all dataset names, including some info
        """
        if len( self._datasetObjs) == 0:
            self.getDatasetObjs()
        self._datasetInfos = []
        for o in self._datasetObjs: 
            if type( o.data) is bytes: # bytes have no shape and dtype
                self._datasetInfos.append( "%s %s (1,)" % 
                                           (o.name, type( o.data)))
            else: 
                self._datasetInfos.append( "%s %s %s %s " % 
                                           (o.name, type( o.data), o.data.shape, o.data.dtype.name))
        return self._datasetInfos

    #
    # generic
    #
    def getDataset( self, name): 
        """
        return the data belonging to a dataset
        name: /scan/data/eh_c0
        """
        if len( self._datasetObjs) == 0:
            self.getDatasetObjs()
        for o in self._datasetObjs: 
            if str( o.name) == name:
                return o.data
        return None

    #
    # generic
    #
    def getDatasetNames1D( self):
        """
        returns list containing all 1D dataset names
        """
        if len( self._datasetObjs) == 0:
            self.getDatasetObjs()
        self._datasetNames1D = []
        for o in self._datasetObjs: 
            if o.linkType == 'HARD' and \
               type( o.data) == numpy.ndarray and \
               o.data.ndim == 1 and \
               len( o.data) > 1: 
                self._datasetNames1D.append( str( o.name))
        return self._datasetNames1D

    #
    # generic
    #
    def getDatasetNames2D( self):
        """
        returns list containing all 2D dataset names
        """
        if len( self._datasetObjs) == 0:
            self.getDatasetObjs()
        self._datasetNames2D = []
        for o in self._datasetObjs: 
            if o.linkType == 'HARD' and \
               type( o.data) == numpy.ndarray and \
               o.data.ndim == 2:
                self._datasetNames2D.append( str( o.name))
        return self._datasetNames2D

    #
    # generic
    #
    def getMotorNames( self): 
        motorNames = []
        if len( self._datasetObjs) == 0:
            self.getDatasetObjs()
        lst = self.getScanCommand().split()
        #
        # ascan exp_dmy01 0 10 100 0.1
        #
        if lst[0] == 'ascan' or \
           lst[0] == 'ascanc' or \
           lst[0] == 'ascan_checkabs' or \
           lst[0] == 'ascan_repeat' or \
           lst[0] == 'dscan' or \
           lst[0] == 'dscan_repeat' or \
           lst[0] == 'dscanc':
            motorNames.append( lst[1])
        #
        # a2scan exp_dmy01 0 10 exp_dmy02 10 20 100 0.1
        #
        elif lst[0] == 'a2scan' or \
             lst[0] == 'a2scanc' or \
             lst[0] == 'd2scan' or \
             lst[0] == 'd2scanc':
            motorNames.append( lst[1])
            motorNames.append( lst[4])
        #
        # a3scan exp_dmy01 0 10 exp_dmy02 10 20 exp_dmy03 20 30 100 0.1
        #
        elif lst[0] == 'a3scan' or \
             lst[0] == 'a3scanc' or \
             lst[0] == 'd3scan' or \
             lst[0] == 'd3scanc':
            motorNames.append( lst[1])
            motorNames.append( lst[4])
            motorNames.append( lst[7])
        #
        # a4scan ...
        #
        elif lst[0] == 'a4scan' or \
             lst[0] == 'a4scanc' or \
             lst[0] == 'd4scan':
            motorNames.append( lst[1])
            motorNames.append( lst[4])
            motorNames.append( lst[7])
            motorNames.append( lst[10])
        #
        # hscan 0.0 1.0 5 0.1
        #
        elif lst[0] == 'hscan':
            if HasyUtils.isDevice( 'e6cctrl_h'):
                motorNames.append( 'e6cctrl_h')
            elif HasyUtils.isDevice( 'kozhue6cctrl_h'):
                motorNames.append( 'kozhue6cctrl_h')
            else:
                motorNames.append( 'notknown1')
        #
        # kscan 0.0 1.0 5 0.1
        #
        elif lst[0] == 'kscan':
            if HasyUtils.isDevice( 'e6cctrl_k'):
                motorNames.append( 'e6cctrl_k')
            elif HasyUtils.isDevice( 'kozhue6cctrl_k'):
                motorNames.append( 'kozhue6cctrl_k')
            else:
                motorNames.append( 'notknown2')
        #
        # lscan 0.0 1.0 5 0.1
        #
        elif lst[0] == 'lscan':
            if HasyUtils.isDevice( 'e6cctrl_l'):
                motorNames.append( 'e6cctrl_l')
            elif HasyUtils.isDevice( 'kozhue6cctrl_l'):
                motorNames.append( 'kozhue6cctrl_l')
            else:
                motorNames.append( 'notknown3')
        #
        # hklscan 1.0 1.0 0.0 1.0 0.0 0.0 5 0.1
        #
        elif lst[0] == 'hklscan':
            diffH = math.fabs(float( lst[2]) - float( lst[1]))
            diffK = math.fabs(float( lst[4]) - float( lst[3]))
            diffL = math.fabs(float( lst[6]) - float( lst[5]))
            if diffH == 0. and diffK == 0. and diffL == 0.:
                raise Exception( "pniReader.getMotorNames",
                                 "diffH == diffK == diffL == 0.")
            motorNames.append( "diff_h")
            motorNames.append( "diff_k")
            motorNames.append( "diff_k")
        #
        # mesh exp_dmy01 0 1 10 exp_dmy02 2 3 10 0.2 flagSShape
        # 
        elif lst[0] == 'mesh' or lst[0] == 'dmesh': 
            motorNames.append( lst[1])

        #
        # a real fscan command line: 
        #   fscan 'x=[0,1,2,3,4],y=[10,11,12,13,14]' 0.1 "exp_dmy01" 'x' "exp_dmy02" 'y'
        # is reduced to 
        #   fscan np=5 0.1 exp_dmy01 exp_dmy02 
        # to save space
        #
        elif lst[0] == 'fscan':
            motorNames.append( lst[3:])
        elif lst[0] == 'timescan':
            motorNames.append( lst[0])
        else:
            pass

        return motorNames
        
    #
    # generic
    #
    def getData1D( self): 
        """
        returns a dictionary: 
            hsh[ 'motorList'] the list of motors involved
            hsh[ 'exp_dmy01'] the list of motor positions
            hsh[ 'eh_c01']    the eh_c01 array

        uses getDatasetNames1D()
        """
        hsh = {}
        
        for ds in self.getDatasetNames1D(): 
            #
            # ds: "/scan/data/eh_c01
            #   have to use the entire path because 2D data
            #   ends with 'data'
            #
            hsh[ ds] = self.getDataset( ds)

        return hsh

    #
    # generic
    #
    def getData2D( self): 
        """
        returns a dictionary: 
            hsh[ '/scan/instrument/histogram_ch01/data']  
        uses getDatasetNames2D()
        """
        hsh = {}
        
        for ds in self.getDatasetNames2D(): 
            #
            # ds: '/scan/instrument/histogram_ch01/data'
            #   have to use the entire path because 2D data
            #   ends with 'data'
            #
            hsh[ ds] = self.getDataset( ds)

        return hsh

    #
    # generic
    #
    def display( self): 
        """
        displays all groups, datasets and attributes of a file
        """
        self._displayLines = []
        self._displayGroup( self._root)
        return self._displayLines

class pniReader( genericNxsReader ):
    """
    class to read NeXus/HDF5 files using h5cpp

    o = pniReader( "tst_05671.nxs")

    o.display()
    o.getAttributeNames()
    o.getAttributeObjs()
    o.getAttributeValue()
    o.getDataset()
    o.getDatasetNames()
    o.getDatasetNames1D()
    o.getDatasetNamesInfo()
    o.getDatasetObjs()

    """
    _depth = 0 # used for display

    def __init__( self, fileName): 

        if not _os.path.exists( fileName): 
            raise Exception( "pniReader.__init__: %s does not exist" % fileName)
        
        if _sys.version_info.major > 2:
            super().__init__()
        else: 
            super( pniReader, self).__init__()
        
        self._handle = h5cpp.file.open( fileName)
        self._root = self._handle.root()

        return
#    
# --- public methods    
#    
# create a list of objects being the basis for further actions
#

    #
    # pni
    #
    def _getDatasetObjs( self, group):
        """
        returns a list of dataset objects
        """
        for a in group.attributes:
            temp = a.read()
            attr = nxsAttribute( group.link.path, a.name)
            #
            # array(['ascan exp_dmy01 0.0 1.0 10 0.2'], dtype=object) -> 
            #        'ascan exp_dmy01 0.0 1.0 10 0.
            #
            if type( temp) == numpy.ndarray and len( temp) == 1:
                attr.value = temp[0]
            else: 
                attr.value = temp
            self._attributeObjs.append( attr)

        for ni in range(group.nodes.size):
            try:
                n = group.nodes[ni]
            except Exception:
                self._displayLines.append(
                    "node for %s does not exist" % group.links[ni].path)
                continue
            if n.type == h5cpp._node.Type.GROUP:
                self._getDatasetObjs( n)
            else:
                for a in n.attributes:
                    temp = a.read()
                    attr = nxsAttribute( n.link.path, a.name)
                    #
                    # array(['ascan exp_dmy01 0.0 1.0 10 0.2'], dtype=object) -> 
                    #        'ascan exp_dmy01 0.0 1.0 10 0.
                    #
                    if type( temp) == numpy.ndarray and len( temp) == 1:
                        attr.value = temp[0]
                    else: 
                        attr.value = temp
                    self._attributeObjs.append( attr)
                o = nxsDataset( n.link.path)
                o.data = n.read()
                o.obj = n
                if n.link.type() == h5cpp._node.LinkType.SOFT:
                    o.linkType = "SOFT"
                    o.linkTarget = str( n.link.target().object_path)
                elif n.link.type() == h5cpp._node.LinkType.HARD:
                    o.linkType = "HARD"
                    o.linkTarget = None
                    
                self._datasetObjs.append( o)
        return 
    #
    # display is with indentations
    #
    #
    # pni
    #
    def _displayGroup( self, group): 
        pniReader._depth += 2
        #print( "%s %s %s" % ( " " * pniReader._depth, group.type, group.link.path))
        self._displayLines.append( "%s %s %s" % ( " " * pniReader._depth, group.type, group.link.path))
        for a in group.attributes:
            temp = repr(a.read())
            if len( temp) > 60:
                temp = temp[:60] + "..."
            self._displayLines.append( "%s   Attr %s %s" % ( " " * pniReader._depth, a.name, temp))
        
        for ni in range(group.nodes.size):
            try:
                n = group.nodes[ni]
            except Exception:
                self._displayLines.append(
                    "node for %s does not exist" % group.links[ni].path)
                continue
            if n.type == h5cpp._node.Type.GROUP:
                self._displayGroup( n)
            elif n.type == h5cpp._node.Type.DATASET:
                self._displayDataset( n)
            else:
                self._displayLines.append( "%s node %s %s" % ( " " * pniReader._depth, type( n), n.link.path))
                self._displayLines.append( " *** node unidentified")
        
        pniReader._depth -= 2
        return

    #
    # pni
    #
    def _displayDataset( self, ds):
        """
        class 'pninexus.h5cpp._node.Dataset'
        """
        if ds.link.type() == h5cpp._node.LinkType.HARD:
            self._displayLines.append( "%s   %s %s HARD" % 
                                       ( " " * pniReader._depth, ds.type, ds.link.path))
        else: 
            self._displayLines.append( "%s   %s %s SOFT %s" % 
                                       ( " " * pniReader._depth, ds.type, ds.link.path, 
                                         ds.link.target().object_path))
        for a in ds.attributes:
            temp = repr( a.read())
            if len( temp) > 60:
                temp = temp[:60] + "..."
            self._displayLines.append( "%s     Attr %s %s" % ( " " * pniReader._depth, a.name, temp))
        return
#
# *** h5py
#
class h5pyReader( genericNxsReader):
    """
    class to read NeXus/HDF5 files using h5py
    o = h5pyReader( "tst_05671.nxs")
    o.display()
    o.getAttributeNames()
    o.getAttributeObjs()
    o.getAttributeValue()
    o.getDataset()
    o.getDatasetNames()
    o.getDatasetNames1D()
    o.getDatasetNamesInfo()
    o.getDatasetObjs()
    """
    _depth = 0 # used for display

    def __init__( self, fileName): 

        if not _os.path.exists( fileName): 
            raise Exception( "h5pyReader.__init__: %s does not exist" % fileName)

        if _sys.version_info.major > 2:
            super().__init__()
        else: 
            super( h5pyReader, self).__init__()
        self._root = h5py.File( fileName, 'r')
        return

    #
    # h5py
    #
    def _getDatasetObjs( self, group):
        """
        returns a list of objects (datasets, attributes)
        """
        for attr in group.attrs.keys(): 
            temp = group.attrs[ attr]
            attr = nxsAttribute( group.name, attr)
            if type( temp) is bytes: 
                attr.value = temp.decode( "utf-8")
            else: 
                attr.value = temp
            self._attributeObjs.append( attr)

        for n in group.values():
            if isinstance( n, h5py.Group): 
                self._getDatasetObjs( n)
            elif n:
                if n.attrs is not None:
                    for attr in n.attrs.keys():
                        temp = n.attrs[ attr]
                        attrTemp = nxsAttribute( n.name, attr)
                        if type( temp) is bytes:
                            attrTemp.value = temp.decode( "utf-8")
                        else:
                            attrTemp.value = temp
                        self._attributeObjs.append( attrTemp)
                o = nxsDataset( n.name)
                o.data = n[()]
                o.obj = n

                if isinstance( n, h5py.Group): 
                    linkInfo = n.get( n.name, getlink=True)        
                else: 
                    linkInfo= n.parent.get( n.name, getlink=True)        

                if isinstance( linkInfo, h5py.HardLink): 
                    o.linkType = "HARD"
                    o.linkTarget = None
                elif isinstance( linkInfo, h5py.SoftLink): 
                    o.linkType = "SOFT"
                    o.linkTarget = linkInfo.path
                else: 
                    o.linkType = "EXTERNAL"
                    o.linkTarget = None

                self._datasetObjs.append( o)
        return 

    #
    # h5py
    #
    def _displayGroup( self, group): 
        # 
        h5pyReader._depth += 2
        
        if group.name == "/": 
            self._displayLines.append( "%s %s Group HARD" % 
                                       ( " " * h5pyReader._depth, group.name))
        else:
            self._displayLines.append( "%s %s Group %s" % 
                                       ( " " * h5pyReader._depth, group.name, self._getLinkInfo( group)))

        for attr in group.attrs.keys(): 
            temp = repr( group.attrs[ attr])
            if len( temp) > 60:
               temp = temp[:60] + "..."
            self._displayLines.append( "%s     Attr %s %s group %s" % 
                                       ( " " * h5pyReader._depth, attr, temp, group.name))
        
        for n in group.values():
            if isinstance( n, h5py.Group): 
                self._displayGroup( n)
            else: 
                self._displayDataset( n)
        
        h5pyReader._depth -= 2
        return

    #
    # h5py
    #
    def _getLinkInfo( self, obj): 
        """
        Distinguish between HARD/SOFT/EXTERNAL link
        """
        if isinstance( obj, h5py.Group): 
            linkInfo = obj.get( obj.name, getlink=True)        
        else: 
            linkInfo= obj.parent.get( obj.name, getlink=True)        

        if isinstance( linkInfo, h5py.HardLink): 
            return "HARD"
        elif isinstance( linkInfo, h5py.SoftLink): 
            return "SOFT %s" % linkInfo.path
        else: 
            return "%s, %s" % ( linkInfo.filename, linkInfo.path)
        
    #
    # h5py
    #
    def _displayDataset( self, ds):
        """
        """

        self._displayLines.append( "%s   %s Dataset %s" % 
                                   ( " " * h5pyReader._depth, ds.name, self._getLinkInfo( ds)))
       
        for attr in ds.attrs.keys(): 
            temp = ds.attrs[ attr]
            temp1 = repr( temp)
            if len( temp1) > 50: 
                temp1 =temp1[:50] + "..."
            self._displayLines.append( "%s     Attr %s %s" % ( " " * h5pyReader._depth, attr, temp1))
        return
        

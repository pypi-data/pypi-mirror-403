#!/usr/bin/env python
"""
the fioReader reads .fio, dat and .nxs files
"""
import os as _os
import string as _string
import numpy as np
import math as _math
from . import nxsReader
from . import TgUtils
from HasyUtils.pyqtSelector import *
import pyqtgraph as _pg

class fioColumn:
    '''
    the class represents a column of a FIO file. The first column is the
    x-axis which is used by all columns, name_in, e.g. test_00001_C1
    '''
    def __init__(self, name_in):
        #
        # test_00001_c1
        #
        self.name = name_in
        lst = self.name.split('_')
        if len(lst) > 1:
            #
            # c1
            #
            self.deviceName = lst[-1]
            if self.deviceName.find( "0") == 0:
                self.deviceName = "ScanName"
        else:
            self.deviceName = "n.n."
        self.x = []
        self.y = []
        return

class fioImage:
    '''
    the class represents 2D data read from a NeXusw file
    '''
    def __init__(self, name_in):
        #
        # test_00001_c1
        #
        self.name = name_in
        self.data = None
        return

class fioReader:
    '''
    represents an entire file with several columns
    input:   name of the .fio file (or .dat, .iint, .nxs. h5)
             flagMCA: if True, the x-axis are channel numbers
    returns: object containing: 
        self.comments
        self.user_comments
        self.parameters
        self.columns
        self.fileName

    The string 'None' appearing in a column is interpreted as '0.'
    '''
    def __init__(self, fileName, flagMCA = False, flagPNI=False):
        '''
        flagMCA: don't be too smart and try to guess it. 
        '''
        self.comments = []
        self.user_comments = []
        self.parameters = {}
        self.columns = []
        self.images = [] # from .nxs files
        self.fileName = fileName
        self.flagMCA = flagMCA
        self.flagPNI = flagPNI
        self.isImage = None # one column from .fio file
        
        #
        # /home/p12user/dirName/gen_00001.fio -> gen_00001
        #
        self.scanName = self.fileName.split("/")[-1].split(".")[0]
        if fileName.endswith( '.fio'):
            self._readFio()
        elif fileName.endswith( '.asc'):
            self._readDat()
        elif fileName.endswith( '.dat') or fileName.endswith( '.asc'):
            inp = open( self.fileName, 'r')
            line = inp.readline()
            inp.close()
            #
            # numpy files have comment lines starting wit '#'
            #
            if line.find( '#') >= 0:
                self._readNpDat()
            else:
                self._readDat()
        elif fileName.endswith( '.iint'):
            self._readIint()
        elif fileName.endswith( '.nxs'):
            self._readNxs()
        else: 
            raise ValueError( "fioReader.fioReader.__init__: format not identified, %s" % fileName)

        return

    def _readFio( self):
        '''
        !
        ! user comments
        !
        %c
        comments
        %p
        parameterName = parameterValue
        %d
        Col 1 AU_ALO_14_0001  FLOAT 
        Col 2 AU_ALO_14_0001  FLOAT 
        Col 3 AU_ALO_14_0001_RING  FLOAT 
        data data data etc.
        '''
        try:
            inp = open( self.fileName, 'r')
        except IOError as e:
            raise ValueError( "fioReader.fioReader._readFio: failed to open %s" % self.fileName)
        lines = inp.readlines()
        inp.close()
        flagComment = 0
        flagParameter = 0
        flagData = 0
        lineCount = 0
        for line in lines:
            line = line.strip()
            if len( line) == 0:
                continue
            if line.find( "!") == 0:
                self.user_comments.append( line)
                flagComment, flagParameter, flagData = False, False, False
            elif line.find( "%c") == 0:
                flagComment, flagParameter, flagData = True, False, False
                continue
            elif line.find( "%p") == 0:
                flagComment, flagParameter, flagData = False, True, False
                continue
            elif line.find( "%d") == 0:
                flagComment, flagParameter, flagData = False, False, True
                continue
            #
            if flagComment:
                self.comments.append( line)
            #
            # parName = parValue
            #
            if flagParameter:
                lst = line.split( "=")
                self.parameters[lst[0].strip()] = lst[1].strip()
            if not flagData:
                continue
            #
            # height and width indicate that we are reading an image
            #
            if self.isImage is None: 
                if 'width' in self.parameters and 'height' in self.parameters: 
                    self.isImage = True
                else: 
                    self.isImage = False
            lst = line.split()
            if lst[0] == "Col":
                #
                # the 'Col 1 ...' description does not create a
                # new FIO_dataset because it contains the x-axis for all
                #
                if not self.flagMCA and not self.isImage:
                    #
                    # the first column contains the independent variable (motor position)
                    #
                    if lst[1] == "1":
                        self.motorName = lst[2]
                    else:
                        self.columns.append( fioColumn( lst[2]))
                #
                # MCA and image files have one colum only
                #
                else:
                    if self.isImage: 
                        self.motorName = lst[2]
                    if self.flagMCA: 
                        self.motorName = "Channels"
                    self.columns.append( fioColumn( lst[2]))
            else:
                if not self.flagMCA and not self.isImage:
                    for i in range(1, len( self.columns) + 1):
                        self.columns[i-1].x.append( float(lst[0]))
                        #
                        # some column may be 'None' - try to continue anyway
                        #
                        if lst[i].lower() == 'none':
                            self.columns[i-1].y.append( float( 0.))
                        else:
                            self.columns[i-1].y.append( float( lst[i]))
                elif self.flagMCA:
                    for i in range(0, len( self.columns)):
                        self.columns[i].x.append( float( lineCount))
                        #
                        # some column may be 'None' - try to continue anyway
                        #
                        if lst[i].lower() == 'none':
                            self.columns[i].y.append( float( 0.))
                        else:
                            self.columns[i].y.append( float( lst[i]))
                #
                # image, one column only
                #
                elif self.isImage:
                    self.columns[0].x.append( float( lst[0]))

            lineCount += 1
        if self.isImage:
            if len( self.columns) != 1: 
                raise ValueError(" fioReader.reasdFio: isImage and len( self.columns) != 1")
            if len( self.columns[0].y) != 0:
                raise ValueError(" fioReader.readFio: isImage and len( self.columns[0].y) is not 0")
            if int(self.parameters[ 'width']) * int(self.parameters[ 'height']) != len( self.columns[0].x): 
                raise ValueError(" fioReader.reasdFio: isImage and width*height != len(x)")
            xlocal = np.asarray( self.columns[0].x, dtype=np.float64)
            self.columns[0].x = xlocal[:]
            
        return True

    def _handle1DNxs( self, o): 
        #
        # 1D data
        #
        hsh1D = o.getData1D()
        if not hsh1D: 
            return 

        lst = o.getMotorNames()
        if len( lst) != 1: 
            raise ValueError( "fioReader.fioReader._readNxs: len( MotorList) != 1, instead %d" % len( lst))
        #
        # /scan/instrument/collection/mono1           
        # motorName == 'mono1'
        #
        # the corresponding key in hsh1D is /scan/instrument/collection/mono1 
        # (because 2D data need the full path, they all end with 'data'
        #
        self.motorName = lst[0] 
        motorNameFull = None
        for elm in hsh1D: 
            if elm.find( self.motorName) != -1: 
                motorNameFull = elm
                break
        if motorNameFull is None: 
            x = None
        else:
            x = hsh1D[ motorNameFull]

        count = 0
        for k in list( hsh1D.keys()): 
            if motorNameFull is not None and k == motorNameFull:
                continue
            self.columns.append( fioColumn( k))
            if x is None: 
                self.columns[ count].x = np.arange( 0, len( hsh1D[k]), 1, hsh1D[k].dtype)
            else: 
                self.columns[ count].x = x[:]
            self.columns[ count].y = hsh1D[ k]
            count += 1
        return

    def _handle2DNxs( self, o): 
        #
        # 2D data
        #
        hsh2D = o.getData2D()

        for k in list( hsh2D.keys()):
            ima = fioImage( k)
            ima.data = hsh2D[ k]
            self.images.append( ima) 
        return

    def _readNxs(self):
        '''
        '''
        try:
            if self.flagPNI:
                o = nxsReader.pniReader( self.fileName)
            else:
                o = nxsReader.h5pyReader( self.fileName)
        except IOError as e:
            raise ValueError( "fioReader.fioReader._readNxs: failed to open %s" % self.fileName)

        self.comments.append( o.getScanCommand())
        self._handle1DNxs( o)
        self._handle2DNxs( o) 
        return True

    def _readDat( self):
        '''
        !
        ! user comments
        !
        data data data etc.
        '''
        #print( "readDat: reading %s" % self.fileName)
        try:
            inp = open( self.fileName, 'r')
        except IOError as e:
            raise ValueError( "fioReader.fioReader._readDat: failed to open %s" % self.fileName)
        lines = inp.readlines()
        inp.close()
        flagFirstDataLine = False
        count = 0
        self.motorName = "position"
        for line in lines:
            line = line.strip()
            if line.find( "!") == 0:
                self.user_comments.append( line)
                continue

            lst = line.split()
            #
            # we found our first data line, determine 
            # how many columns we need
            #
            if not flagFirstDataLine:
                flagFirstDataLine = True
                if not self.flagMCA:
                    for i in range( 1, len( lst)):
                        self.columns.append( fioColumn( "scan%d" % i))
                else: 
                    for i in range( 1, len( lst) + 1):
                        self.columns.append( fioColumn( "scan%d" % i))

            if not self.flagMCA:
                for i in range(1, len( lst)):
                    try: 
                        self.columns[i-1].x.append( float( lst[0]))
                    except Exception as e:
                        print( "Exception at line %d, %s" % (count, self.fileName))
                        print( "--> %s " % line)
                        print( repr(e))
                        #
                        # we don't append x, so do not append y either
                        #
                        continue
                    try:
                        #
                        # really bad hack for reading Msp files, atof() does this also
                        #
                        if lst[i] == "*.*e-07": 
                            self.columns[i-1].y.append( 0.)
                        else: 
                            self.columns[i-1].y.append( float( lst[i]))
                    except Exception as e:
                        print( "Exception at line %d, %s" % (count, self.fileName))
                        print( "--> %s" % line)
                        print( repr(e))
                        #
                        # x has already been appended, so append also y
                        #
                        self.columns[i-1].y.append( 0.)
            else:
                for i in range(len( lst)):
                    try: 
                        self.columns[i].x.append( float( count)) 
                    except Exception as e:
                        print( "Exception at line %d, %s" % (count, self.fileName))
                        print( "--> %s" % line)
                        print( repr(e))
                        #
                        # we don't append x, so do not append y either
                        #
                        continue
                    try:
                        self.columns[i].y.append( float( lst[i]))
                    except Exception as e:
                        print( "Exception at line %d, %s" % (count, self.fileName))
                        print( "--> %s" % line)
                        print( repr(e))
                        #
                        # x has already been appended, so append also y
                        #
                        self.columns[i].y.append( 0.)
            count += 1
        return True

    def _readNpDat( self):
        '''
        # EXAFS scan at P64 beamline
        # Scan time - 60.75 s
        # Scan mode - continuous
        # 
        # 1 - Monochromator position, eV
        # 2 - mu transmition sample
        # 3 - mu transmition reference
        # 4 - mu fluorescence
        # 5 - Undulator position, eV
        # 6 - i_0
        # 7 - i_1
        # 8 - i_2
        # 9 - i_pips
        # 10 - timestamp, s
        data data data etc.
        '''
        #print( "readNpDat: reading %s" % self.fileName)
        try:
            inp = open( self.fileName, 'r')
        except IOError as e:
            raise ValueError( "fioReader.fioReader._readNpDat: failed to open %s" % self.fileName)
        lines = inp.readlines()
        inp.close()

        firstColumnDescription = False
        for line in lines:
            line = line.strip()
            if line.find( "#") == 0:
                lst = line.split()
                if len( lst) > 2 and lst[2] == '-': 
                    colName = '_'.join(lst[3:])
                    #
                    # the x-axis is common 
                    #
                    if not firstColumnDescription: 
                        firstColumnDescription = True
                        self.motorName = colName
                        continue
                    if colName.find( ',') >= 0:
                        colName = _string.replace( colName, ',', '_')
                    self.columns.append( fioColumn( colName)) 
                else:
                    self.user_comments.append( line)
                continue

            lst = line.split()
            for i in range(1, len( lst)):
                try: 
                    self.columns[i-1].x.append( float( lst[0]))
                except Exception as e:
                    print( "Exception at line %d, %s" % (count, self.fileName))
                    print( "--> %s" % line)
                    print( repr(e))
                    #
                    # we don't append x, so do not append y either
                    #
                    continue
                try:
                    self.columns[i-1].y.append( float( lst[i]))
                except Exception as e:
                    print( "Exception at line %d, %s" % (count, self.fileName))
                    print( "--> %s" % line)
                    print( repr(e))
                    #
                    # x has already been appended, so append also y
                    #
                    self.columns[i-1].y.append( 0.)
        return True

    def _readIint( self):
        '''
        read iint result files, Sonia Francoual, Christoph Rosemann
        # colName1, colName2, etc.
        data data data etc.
        '''
        #print( "readDat: reading %s" % self.fileName)
        try:
            inp = open( self.fileName, 'r')
        except IOError as e:
            raise ValueError( "fioReader.fioReader._readIint: failed to open %s" % self.fileName)
        lines = inp.readlines()
        inp.close()
        flagFirstDataLine = False
        count = 1
        lineCount = 0
        colNames = []
        #
        # in .iint files column names may appear twice
        #
        colNamesUsed = []
        for line in lines:
            line = line.strip()
            #
            # '# scannumber	m0_center	m0_center_stderr	m0_amplitude'
            #
            if line.find( "#") == 0:
                colNames = line[1:].strip().split()
                continue

            lst = line.split()
            #
            # we found our first data line, determine 
            # how many columns we need
            #
            if not flagFirstDataLine:
                flagFirstDataLine = True
                for i in range( 1, len( lst)):
                    if len( colNames) > 0:
                        if colNames[i - 1] not in colNamesUsed:
                            self.columns.append( fioColumn( colNames[i - 1]))
                            colNamesUsed.append( colNames[ i - 1])
                        else:
                            self.columns.append( fioColumn( colNames[i - 1] + "_"))
                            colNamesUsed.append( colNames[ i - 1] + "_")
                    else:
                        self.columns.append( fioColumn( "scan%d" % i))

            if not self.flagMCA:
                for i in range(1, len( lst)):
                    try: 
                        self.columns[i-1].x.append( float( lst[0]))
                    except Exception as e:
                        print( "Exception at line %d, %s" % (count, self.fileName))
                        print( "--> %s" % line)
                        print( repr(e))
                        #
                        # we don't append x, so do not append y either
                        #
                        continue
                    try:
                        self.columns[i-1].y.append( float( lst[i]))
                    except Exception as e:
                        print( "Exception at line %d, %s" % (count, self.fileName))
                        print( "--> %s" % line)
                        print( repr(e))
                        #
                        # x has already been appended, so append also y
                        #
                        self.columns[i-1].y.append( 0.)
            else:
                for i in range(len( lst)):
                    try: 
                        self.columns[i].x.append( float( lineCount))
                    except Exception as e:
                        print( "Exception at line %d, %s" % (count, self.fileName))
                        print( "--> %s" % line)
                        print( repr(e))
                        #
                        # we don't append x, so do not append y either
                        #
                        continue
                    try:
                        self.columns[i].y.append( float( lst[i]))
                    except Exception as e:
                        print( "Exception at line %d, %s" % (count, self.fileName))
                        print( "--> %s" % line)
                        print( repr(e))
                        #
                        # x has already been appended, so append also y
                        #
                        self.columns[i].y.append( 0.)
            lineCount = 0
            count += 1
        return True

class fioObj():
    '''
    creates an empty object representing an .fio file
      - write() returns the filename

    Example:
      import HasyUtils
      import numpy as np
      o = HasyUtils.fioObj( fileName = "/home/p99user/temp/test.fio", 
                            scanName = "cu",
                            motorName = "eh_mot12")
      o.parameters[ 'energy'] = 8980 
      o.comments.append( "Copper")
      col = HasyUtils.fioColumn( 'signal')
      col.x = np.linspace( 0, 1, 5)
      col.y = np.random.random_sample( 6)
      o.columns.append( col)
      fileName = o.write()
    .
    '''
    def __init__( self, namePrefix = None, fileName = None, scanName = None, scanDir = None, motorName = None):
        if namePrefix is not None:
            if fileName is not None:
                raise Exception( "fioReader.fioObj", "specify namePrefix OR fileName")
            if scanName is not None:
                raise Exception( "fioReader.fioObj", "specify namePrefix OR scanName")            
            self.scanName = TgUtils.createScanName( namePrefix, scanDir)
            if scanDir is not None:
                self.fileName = "%s/%s.fio" % ( scanDir, self.scanName)
            else:
                self.fileName = "%s.fio" % ( self.scanName)
        else:
            if scanName is None:
                scanName = TgUtils.createScanName( "hasylab", scanDir)
            if fileName is None:
                fileName = scanName + ".fio"
            self.fileName = fileName
            if scanDir is not None:
                self.fileName = "%s/%s" % (scanDir, self.fileName)
            self.scanName = scanName

        if motorName is None:
            motorName = "position"
        self.motorName = motorName

        self.columns = []
        self.comments = []
        self.user_comments = []
        self.parameters = { 'ScanName': self.scanName}

    def write( self):
        return fioWriter( self)

def fioWriter( fioObj):
    """
    input: fioObj
      fioObj.columns        fioObj.fileName       fioObj.scanName       fioObj.motorName
      fioObj.comments       fioObj.parameters     fioObj.user_comments  
    """
    if _os.path.exists( fioObj.fileName):
        raise Exception( "fioWriter", "%s exists already" % fioObj.fileName)

    try: 
        out = open( fioObj.fileName, 'w')
    except Exception as e: 
        print( "fioReader.fioWriter: failed to w-open %s" % fioObj.fileName)
        print( repr( e))
        return None
    #
    # write user comments
    #
    if len(fioObj.user_comments) > 0:
        for line in fioObj.user_comments:
            out.write( "! %s\n" % line)
    #
    # write comments
    #
    if len(fioObj.comments) > 0:
        out.write( "!\n")
        out.write( "! Comments\n")
        out.write( "!\n")
        out.write( "%c\n")
        for line in fioObj.comments:
            out.write( "%s\n" % line)
    #
    # write parameters
    #
    out.write( "!\n")
    out.write( "! Parameter\n")
    out.write( "!\n")
    out.write( "%p\n")
    for k in list( fioObj.parameters.keys()):
        out.write( "%s = %s\n" % (k, fioObj.parameters[k]))
    #
    # write data
    #
    if len(fioObj.columns) > 0:
        out.write( "!\n")
        out.write( "! Data\n")
        out.write( "!\n")
        out.write( "%d\n")
        out.write( " Col 1 %s DOUBLE\n" % ( fioObj.motorName)) 
        for i in range( len(fioObj.columns)):
            #
            # images have one column only
            #
            if fioObj.columns[i].y is not None: 
                out.write( " Col %d %s DOUBLE\n" % ( (i+2), fioObj.columns[i].name)) 
        for i in range( len(fioObj.columns[0].x)):
            out.write( " %s" % ( '{}'.format(fioObj.columns[0].x[i])))
            for j in range( len(fioObj.columns)):
                #
                # Images have one column only
                #
                if fioObj.columns[j].y is not None: 
                    out.write( " %s" % ( '{}'.format(fioObj.columns[j].y[i])))
            out.write( "\n")

    out.close()
    #print( "fioWriter: created %s " % fioObj.fileName)
    return fioObj.fileName

_appFioPlotter = None
_winFioPlotter = None

def fioPlotter( fileName):
    '''
    plots the contents of a fio file
    '''
    global _appFioPlotter, _winFioPlotter

    if _appFioPlotter is None:
        _appFioPlotter = QApplication.instance()
        if _appFioPlotter is None:
            _pg.setConfigOption( 'background', 'w')
            _pg.setConfigOption( 'foreground', 'k')
            _appFioPlotter = _pg.mkQApp()
    
    if _winFioPlotter is None:
        _winFioPlotter = _pg.GraphicsWindow( title="The fioPlotter")
        _winFioPlotter.resize( 1000, 800)
        _winFioPlotter.setBackground( _pg.mkColor( 'w'))
    _winFioPlotter.clear()
    fioObj = fioReader( fileName)
    length = len(fioObj.columns)
    nCol = int(_math.ceil(_math.sqrt(length)))
    _winFioPlotter.addLabel( fioObj.scanName, row = 1, col = 1)
    for i in range( 1, length + 1):
        r = int( _math.floor(float( i)/float( nCol)) + 1)
        c = i % nCol + 1
        plt = _winFioPlotter.addPlot( row=r, col=c)
        plt.setContentsMargins( 10, 10, 10, 10)
        plt.showGrid( x = True, y = True)
        plt.setTitle( title = fioObj.columns[i-1].name)
        plt.plot( fioObj.columns[i-1].x, fioObj.columns[i-1].y, pen = (0, 0, 255))
    _appFioPlotter.processEvents()

    return True

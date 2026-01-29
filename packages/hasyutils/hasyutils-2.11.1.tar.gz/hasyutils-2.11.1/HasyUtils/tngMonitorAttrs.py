#!/usr/bin/env python
# ---
# putting things together: 
#   self.layout_grid.addWidget( chan.win, chan.row, chan.col)
#
#   self:      QtGui.QMainWindow
#   chan.win:  pyqtgraph.GraphicsWindow()
#
import sys, os, argparse, math, time
try:
    import PyTango
except:
    pass
import numpy as np
import HasyUtils
from HasyUtils.pyqtSelector import *
import pyqtgraph as pg

ACTIVITY_SYMBOLS = ['|', '/', '-', '\\', '|', '/', '-', '\\'] 
startTime = None
ATTRIBUTES = [
    'sys/tg_test/1/double_scalar',
    #'petra/globals/keyword/BeamCurrent',
    ]

app = None

def getTime():
    '''
    make the time stamps human readable
    '''
    global startTime
    if startTime is None:
        startTime = time.time()
        return 0.
    return (time.time() - startTime)


class changeScanDir( QMainWindow):
    def __init__( self, parent = None):
        super( changeScanDir, self).__init__( parent)
        self.parent = parent
        self.setWindowTitle( "Change ScanDir")
        self.prepareWidgets()
        #
        # Menu Bar
        #
        self.menuBar = QMenuBar()
        self.setMenuBar( self.menuBar)
        self.prepareMenuBar()
        self.prepareStatusBar()
        self.show()

    def prepareMenuBar( self):
        self.fileMenu = self.menuBar.addMenu('&File')
        self.exitAction = QAction('E&xit', self)        
        self.exitAction.setStatusTip('Exit application')
        self.exitAction.triggered.connect(QApplication.quit)
        self.fileMenu.addAction( self.exitAction)

        #
        # the activity menubar: help and activity
        #
        self.menuBarActivity = QMenuBar( self.menuBar)
        self.menuBar.setCornerWidget( self.menuBarActivity, QtCore.Qt.TopRightCorner)

        #
        # Help menu (bottom part)
        #
        self.helpMenu = self.menuBarActivity.addMenu('Help')
        self.widgetAction = self.helpMenu.addAction(self.tr("Widget"))
        self.widgetAction.triggered.connect( self.cb_helpWidget)

        self.activityIndex = 0
        self.activity = self.menuBarActivity.addMenu( "|")

    def cb_helpWidget(self):
        w = HelpBox(self, self.tr("HelpWidget"), self.tr(
            "<p><b>ScanDir</b><br>"
                ))
        w.show()

    def prepareStatusBar( self):
        #
        # Status Bar
        #
        self.statusBar = QStatusBar()
        self.setStatusBar( self.statusBar)

        self.apply = QPushButton(self.tr("&Apply")) 
        self.statusBar.addPermanentWidget( self.apply) # 'permanent' to shift it right
        self.apply.clicked.connect( self.cb_applyScanDir)
        self.apply.setShortcut( "Alt+a")

        self.exit = QPushButton(self.tr("E&xit")) 
        self.statusBar.addPermanentWidget( self.exit) # 'permanent' to shift it right
        self.exit.clicked.connect( self.close )
        self.exit.setShortcut( "Alt+x")
        
    def prepareWidgets( self):
        w = QWidget()
        self.layout_v = QVBoxLayout()
        w.setLayout( self.layout_v)
        self.setCentralWidget( w)
        hBox = QHBoxLayout()
        self.scanDirLabel = QLabel( "ScanDir %s" % self.parent.scanDir)
        hBox.addWidget( self.scanDirLabel)
        self.scanDirLine = QLineEdit()
        self.scanDirLine.setAlignment( QtCore.Qt.AlignRight)
        hBox.addWidget( self.scanDirLine)
        self.layout_v.addLayout( hBox)

    def cb_applyScanDir( self):
        self.parent.scanDir = self.scanDirLine.text()
        self.scanDirLine.clear()
        self.scanDirLabel.setText( "ScanDir %s" % self.parent.scanDir)
        self.parent.scanDirBtn.setText( self.parent.scanDir)
        self.parent.logWidget.append( "New ScanDir %s" % self.parent.scanDir)

class Channel():
    xScaleFactor = 1
    def __init__( self, parent, name, nrow, ncol, index):
        #
        # haso1107d1:10000/sys/tg_test/1/double_scalar
        #
        lst = name.split( ' ')
        self.name = lst[0]
        if len( lst) == 2:
            self.alias = lst[1]
        else:
            self.alias = lst[0]

        self.parent = parent

        self.x = np.linspace( 0, 1, self.parent.np)
        self.y = np.linspace( 0, 1, self.parent.np)
        self.count = 0
        self.countTotal = 0
        self.startTime = getTime()
        #
        # nrow, ncol, index define the position in the graphics viewport
        # (nrow, ncol, index) -> (row, col)
        # e.g.: 
        #   ( 2, 2, 1) -> ( 0, 0)
        #   ( 2, 2, 2) -> ( 1, 0)
        #   ( 2, 2, 3) -> ( 0, 1)
        #   ( 2, 2, 4) -> ( 1, 1)
        #
        self.row = int((index - 1) % nrow)
        self.col = int( math.floor( float(index - 1)/float( nrow)))
        #
        # each channel has its own graphics window because the plot are
        # distributed across the screen by a QGridLayout()
        #
        #self.win = pg.GraphicsWindow( title="Monitoring Tango Attributes")
        self.plotWidget = self.parent.graphicsLayoutWidget.addPlot( row = self.row, col = self.col)
        self.plot = self.plotWidget.plot()
        self.plotWidget.showGrid( x = True, y = True)
        self.plotWidget.setTitle( title = self.alias)
        self.plotWidget.enableAutoRange( x = True, y = True)        
        self.plot.clear()
        self.plot.setData( self.x, self.y)

        lst = self.name.split( '/')
        self.devName = '/'.join(lst[:-1])
        self.attrName = lst[-1]
        try:
            self.proxy = PyTango.DeviceProxy( self.devName)
        except Exception as e:
            raise Exception( "Channel.constructor %s" % repr( e))

    def updateChannel( self):
        countDisplay = self.count
        xMin = ( self.x[0] - self.x[ countDisplay - 1])
        try:
            xT = np.array( self.x[0:countDisplay], copy = True)
        except Exception as e:
            print( "*** updateChannel: caught an exception")
            print( repr(e))
            
        xNow = self.x[ self.count - 1]
        i = 0
        for elm in self.x[0:self.count]:
            xT[i] = elm - xNow
            xT[i] = xT[i]/float( Channel.xScaleFactor)
            i += 1
        try:
            self.plot.clear()
            self.plot.setData( xT[ 0:countDisplay],
                               self.y[ 0:countDisplay], pen = (255, 0, 0))
        except Exception as e:
            print( "*** plot.clear() or plot.setData: threw an exception")
            print( repr(e))

    def addValue( self, x, y):

        #
        # re-scaling the x-axis depends on the number of points used, 
        # for example: if NP == 2000 and updateTime == 0.1 it does
        # not make sense to use hours as units
        #
        if self.count < self.parent.np:
            if (x - self.startTime ) < 120:
                pass
            elif (x - self.startTime ) < 3600:
                Channel.xScaleFactor = 60
            else:
                Channel.xScaleFactor = 3600

        self.countTotal += 1
        if self.count == self.parent.np:
            try:
                self.x = np.roll( self.x, -1)
                self.y = np.roll( self.y, -1)
            except Exception as e:
                print( "addValue: caught an exception")
                print( repr( e))

            self.x[ self.parent.np - 1] = x
            self.y[ self.parent.np - 1] = y
        else:
            self.x[ self.count] = x
            self.y[ self.count] = y
            self.count += 1

        self.updateChannel()

    def readAttr( self):
        try: 
            argout = self.proxy.read_attribute( self.attrName).value
        except Exception as e: 
            print( "tngMonitorAttrs.channel, readAttr %s trouble reading %s" % (self.proxy.name(), self.name))
            print( repr( e))
            argout = None
        return argout
#
# ===
#
class monitorMenu( QMainWindow):
    '''
    QMainWindow is the main class of the SardanaMotorMenu application
    '''
    def __init__( self, app = None , attrs = None, updateTime = None, np = None, parent = None, title = None):
        super( monitorMenu, self).__init__( parent)

        if app is None:
            raise( Exception( "tngMonitorAttrs.monitorMenu", 
                              "tngMonitorAttrs.monitorMenu: please create a QApplication outside"))
            
        self.app = app
        self.title = title
        if self.title is not None: 
            self.setWindowTitle( self.title)

        if np is None:
            np = 2000
        self.np = np
        if updateTime is None:
            updateTime = 1.
        self.updateTime = updateTime
        
        geo = QDesktopWidget().screenGeometry(-1)
        # size
        self.setGeometry( geo.width() - 680, 30, 650, 500)

        # background/foreground have to be set before the channels are defined
        pg.setConfigOption( 'background', 'w')
        pg.setConfigOption( 'foreground', 'k')

        self.updateTime = updateTime
        self.countMain = 0
        self.startTimeFreq = getTime()

        self.checkAttrSyntax( attrs)
        self.attrs = attrs
        length = float( len( attrs))
        nrow = math.ceil( math.sqrt( length))
        ncol = math.ceil( length/nrow)

        self.scanDir = os.getenv( "HOME")

        # used by cb_postscript
        self.lastFileWritten = None

        self.prepareWidgets()

        self.channels = []
        count = 1
        for attr in self.attrs:
            self.channels.append( Channel( self, attr, ncol, nrow, count))
            count += 1

        self.menuBar = QMenuBar()
        self.setMenuBar( self.menuBar)
        self.prepareMenuBar()

        #
        # Status Bar
        #
        self.statusBar = QStatusBar()
        self.setStatusBar( self.statusBar)
        self.prepareStatusBar()

        self.updateCount = 0

        self.refreshFunc = self.refreshGraphics

        self.paused = False
        self.updateTimer = QtCore.QTimer(self)
        self.updateTimer.timeout.connect( self.cb_refreshMain)
        self.updateTimer.start( int( self.updateTime*1000))

    #
    # the central widgets
    #
    def prepareWidgets( self):
        self.main_widget = QWidget(self)
        self.setCentralWidget(self.main_widget)
        self.layout_v = QVBoxLayout()
        self.main_widget.setLayout( self.layout_v)
        self.graphicsLayoutWidget = pg.GraphicsLayoutWidget(show=True)
        self.layout_v.addWidget( self.graphicsLayoutWidget)

        self.labelTimeStamp = QLabel( " timeStamp")
        hBox = QHBoxLayout()
        hBox.addStretch()            
        hBox.addWidget( self.labelTimeStamp)
        hBox.addStretch()            
        self.labelFreq = QLabel( "")
        hBox.addWidget( self.labelFreq)
        self.layout_v.addLayout( hBox)

        self.logWidget = QTextEdit()
        self.logWidget.setMaximumHeight( 50)
        self.logWidget.setReadOnly( 1)
        self.layout_v.addWidget( self.logWidget)

    #
    # the menu bar
    #
    def prepareMenuBar( self): 

        self.fileMenu = self.menuBar.addMenu('&File')

        self.writeFileAction = QAction('Write .fio file', self)        
        self.writeFileAction.setStatusTip('Write .fio file')
        self.writeFileAction.triggered.connect( self.cb_writeFile)
        self.fileMenu.addAction( self.writeFileAction)

        self.postscriptAction = QAction('Postscript', self)        
        self.postscriptAction.setStatusTip('Create postscript output from last .fio file')
        self.postscriptAction.triggered.connect( self.cb_postscript)
        self.fileMenu.addAction( self.postscriptAction)

        self.exitAction = QAction('E&xit', self)        
        self.exitAction.setStatusTip('Exit application')
        #self.exitAction.triggered.connect( QApplication.quit)
        self.exitAction.triggered.connect( self.cb_close)
        self.fileMenu.addAction( self.exitAction)

        #
        # the activity menubar: help and activity
        #
        self.menuBarActivity = QMenuBar( self.menuBar)
        self.menuBar.setCornerWidget( self.menuBarActivity, QtCore.Qt.TopRightCorner)

        self.helpMenu = self.menuBarActivity.addMenu('Help')
        self.helpWidget = self.helpMenu.addAction(self.tr("Widget"))
        self.helpWidget.triggered.connect( self.cb_helpWidget)

        self.activityIndex = 0
        self.activity = self.menuBarActivity.addMenu( "|")
    #
    # the status bar
    #
    def prepareStatusBar( self): 

        self.updateTimeComboBox = QComboBox()
        self.updateTimeComboBox.setToolTip( "The update time") 
        count = 0
        for st in [ "0.1", "0.5", "1.0", "2.0", "5.0", "10.0", "60."]:
            self.updateTimeComboBox.addItem( st)
            #
            # initialize the sample time comboBox to the current value
            #
            if float( st) == self.updateTime:
                self.updateTimeComboBox.setCurrentIndex( count)
            count += 1
        self.statusBar.addWidget( QLabel( " Update time [s]"))
        self.statusBar.addWidget( self.updateTimeComboBox) 
        self.updateTimeComboBox.currentIndexChanged.connect( self.cb_updateTime)

        self.statusBar.addWidget( QLabel("ScanDir")) # 'permanent' to shift it right
        self.scanDirBtn = QPushButton( self.scanDir)
        self.statusBar.addWidget( self.scanDirBtn) 
        self.scanDirBtn.clicked.connect( self.cb_scanDir)
        self.scanDirBtn.setShortcut( "Alt+s")

        self.w_clear = QPushButton(self.tr("Clear")) 
        self.w_clear.setToolTip( "Clear log widget")
        self.statusBar.addPermanentWidget( self.w_clear) # 'permanent' to shift it right
        self.w_clear.clicked.connect( self.logWidget.clear)

        self.pausedBtn = QPushButton(self.tr("&Pause")) 
        self.statusBar.addPermanentWidget( self.pausedBtn) # 'permanent' to shift it right
        self.pausedBtn.clicked.connect( self.cb_paused)
        self.pausedBtn.setShortcut( "Alt+p")

        self.exit = QPushButton(self.tr("&Exit")) 
        self.statusBar.addPermanentWidget( self.exit) # 'permanent' to shift it right
        #self.exit.clicked.connect( QApplication.quit)
        self.exit.clicked.connect( self.cb_close)
        self.exit.setShortcut( "Alt+x")

    def cb_close( self): 
        #print( "+++tngMonitorAttrs.cb_close") 
        self.close()

    def closeEvent( self, e):
        #print( "+++tngMonitorAttrs.closeEvent") 
        return 
    #
    #
    #
    def checkAttrSyntax( self, attrLst): 
        '''
        make sure that the attribute names are valid
        '''

        for elm in attrLst:
            lst = elm.split( '/')
            if elm.find( ':') > 0: 
                if len( lst) < 5: 
                    print( "TngMonitorAttrs.checkAttrSyntax: bad syntax %s" % elm)
                    print( "  forgot to specify the attribute name within the device?")
                    sys.exit( 255)
                elif len( lst) < 5: 
                    print( "TngMonitorAttrs.checkAttrSyntax: bad attribute name syntax %s" % elm)
                    print( "  too many tokens.")
                    sys.exit( 255)
            else:
                if len( lst) < 4: 
                    print( "TngMonitorAttrs.checkAttrSyntax: bad syntax %s" % elm)
                    print( "  forgot to specify the attribute name within the device?")
                    sys.exit( 255)
                elif len( lst) < 4: 
                    print( "TngMonitorAttrs.checkAttrSyntax: bad attribute name syntax %s" % elm)
                    print( "  too many tokens.")
                    sys.exit( 255)

        return 
    #
    # the callback functions
    #
    def cb_scanDir( self):
        o = changeScanDir( self)
        o.show()
        return o

    def cb_writeFile( self):
        if not self.paused:
            self.logWidget.append( "writeFile: error, application not paused")
            return

        try:
            o = HasyUtils.fioObj( namePrefix = "tma", scanDir = self.scanDir)
        except Exception as e:
            print( "TngMonitorAttrs.cb_writeFile: caught an exeption")
            print( repr( e))
            return
        for chan in self.channels:
            col = HasyUtils.fioColumn( chan.name.split( "/")[-1])
            col.x = chan.x[0:chan.count]
            col.y = chan.y[0:chan.count]
            o.columns.append( col)
        try:
            self.lastFileWritten= o.write()
        except Exception as e:
            print( "cb_writeFile caught an exception")
            print( repr( e))
            return
        self.logWidget.append( "created %s" % self.lastFileWritten)

    def cb_postscript( self):
        if self.lastFileWritten is None:
            print( "no .fio file created so far")
            return
        dirName = "./"
        fName = self.lastFileWritten
        if self.lastFileWritten.find( '/') != -1:
            dirName = self.lastFileWritten.rpartition( '/')[0]
            fName = self.lastFileWritten.split( '/')[-1]

        cmd = "cd %s && /usr/local/experiment/Spectra/bin/gra_main_vme -e \"read/scan/fio %s;display/vp;post/nocon/nolog\"" % (dirName, fName)
        os.system( cmd)
        self.logWidget.append( "created %s/laser.ps" % dirName)
        self.logWidget.append( "close gv to continue operation")
        self.logWidget.update()
        app.processEvents()
        os.system( "cd %s && /usr/bin/gv laser.ps" % dirName)

    def cb_helpWidget(self):
        QMessageBox.about(self, self.tr("Help Widget"), self.tr(
                "<h3> TngMonitorAttrs</h3>"
                "Monitor selected Tango Attributes"
                "<ul>"
                "<li> Use 'TngMonitorAttrs.py -f attr.lis to read attributes from a file</li>"
                "<li> To produce a postscript file:</li>"
                "<ul>"
                "<li> Select ScanDir</li>"
                "<li> Pause data taking</li>"
                "<li> File menu: Create a .fio file </li>"
                "<li> File menu: Postscript </li>"
                "<li> Close gv to continue data taking </li>"
                "</ul>"
                "</ul>"
                ))

    def cb_updateTime( self):
        self.updateTime = float( self.updateTimeComboBox.currentText())
        self.countMain = 0
        self.startTimeFreq = getTime()

    def cb_paused( self):
        if self.paused: 
            self.paused = False
            self.updateTimer.start( int( self.updateTime*1000))
            self.pausedBtn.setText( "&Pause")
        else:
            self.paused = True
            self.updateTimer.stop()
            self.pausedBtn.setText( "Un&pause")

    def refreshGraphics( self):
        for chan in self.channels:
            chan.addValue( getTime(), chan.readAttr()) 

    def cb_refreshMain( self):

        if self.isMinimized(): 
            return
        
        self.countMain += 1
        freq = float( self.countMain)/(getTime() - self.startTimeFreq)
        self.labelFreq.setText( "%5.2f Hz, %d/%d" % (freq, self.channels[0].count, self.np))

        self.activityIndex += 1
        if self.activityIndex > (len( ACTIVITY_SYMBOLS) - 1):
            self.activityIndex = 0
        self.activity.setTitle( ACTIVITY_SYMBOLS[ self.activityIndex])
        self.updateTimer.stop()

        self.refreshFunc()

        if Channel.xScaleFactor == 1:
            self.labelTimeStamp.setText( 'time [seconds] %s' % 
                                         time.strftime("%d %b %Y %H:%M:%S", time.localtime()))
        elif Channel.xScaleFactor == 60:
            self.labelTimeStamp.setText( 'time [minutes] %s' % 
                                         time.strftime("%d %b %Y %H:%M:%S", time.localtime()))
        else:
            self.labelTimeStamp.setText( 'time [hours] %s' % 
                                         time.strftime("%d %b %Y %H:%M:%S", time.localtime()))

        self.updateTimer.start( int( self.updateTime*1000))



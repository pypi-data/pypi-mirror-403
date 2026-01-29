#!/usr/bin/env python
 
"""PyQt4 port of the layouts/basiclayout example from Qt v4.x"""

import sys, os, time
#from PyQt4 import QtCore, QtGui
from taurus.external.qt import QtGui, QtCore 
import taurus
from taurus.qt.qtgui.application import TaurusApplication 
#from threading import Thread
from optparse import OptionParser
import HasyUtils
import PyTango
#import thread
import signal

PORT = 7660

msgBuf = []

class Dialog(QtGui.QDialog):
    classVar = 12345
    def __init__(self, parent=None):
        QtGui.QDialog.__init__(self, parent)
        
        self.createMenubar()
        self.LogWidget = QtGui.QTextEdit()
        self.LogWidget.setReadOnly( 1)

        self.createBottomLine()

        geo = QtGui.QDesktopWidget().screenGeometry(-1)
        self.setGeometry( geo.width() - 680, 300, 650, 500)

        mainLayout = QtGui.QVBoxLayout()
        mainLayout.setMenuBar(self.menuBar)
        mainLayout.addWidget(self.LogWidget)
        mainLayout.addLayout(self.bottomLayout)

        self.setLayout(mainLayout)


        self.timer = QtCore.QTimer()
        self.timer.timeout.connect( self._cb_timeout)
        self.timer.start( 200)
        
        self.setWindowTitle(self.tr("Sardana Info Viewer"))

        lst = HasyUtils.getDoorNames()
        if len( lst) != 3:
            print( "No. of Doors != 3, %d " % len(lst))
            sys.exit( 255)

        self.door = PyTango.DeviceProxy( lst[0])
        self.door.subscribe_event('Info', PyTango.EventType.CHANGE_EVENT, cbInfo)
        
        self.show()

    def closeEvent( self, event):
        reply = QtGui.QMessageBox.question(self, 'Message',
                                           "Are you sure to quit?", QtGui.QMessageBox.Yes | 
                                           QtGui.QMessageBox.No, QtGui.QMessageBox.No)

        if reply == QtGui.QMessageBox.Yes:
            event.accept()
        else:
            event.ignore()
        
    def clearLogWidget( self):
        self.LogWidget.clear()

    def createBottomLine( self):
        #
        # exit
        #
        self.exitButton = QtGui.QPushButton(self.tr("E&xit"))
        self.exitButton.setShortcut( QtGui.QKeySequence( self.tr( "Alt+X")))
        self.exitButton.clicked.connect( self.close)
        #
        # Clear log
        #
        self.clearLogButton = QtGui.QPushButton(self.tr("&Clear log"))
        self.clearLogButton.clicked.connect( self.clearLogWidget)

        self.bottomLayout = QtGui.QHBoxLayout()
        self.bottomLayout.addStretch(1)
        self.bottomLayout.addWidget(self.clearLogButton)
        self.bottomLayout.addWidget(self.exitButton)

    def createMenubar(self):
        self.menuBar = QtGui.QMenuBar()
        
        self.fileMenu = QtGui.QMenu(self.tr("&File"), self)
        
        self.helpMenu = QtGui.QMenu(self.tr("&Help"), self)
        self.helpNewsAction = self.helpMenu.addAction(self.tr("&News"))
        self.helpNewsAction.triggered.connect( self.cb_helpNews)
        
        self.exitAction = self.fileMenu.addAction(self.tr("E&xit"))
        self.exitAction.triggered.connect( self.close)
        
        self.menuBar.addMenu(self.fileMenu)
        self.menuBar.addMenu(self.helpMenu)


    def cb_helpNews(self):
        QtGui.QMessageBox.about(self, self.tr("Help News"), self.tr(
                "<h3> Sardana Info Viewer News</h3>"
                "9.7.2015 first entry"
                "<p>"
                "9.7.2015 another entry"
                ))

    def _cb_timeout(self):
        global msgBuf
        if len( msgBuf) == 0:
            return
        while len(msgBuf) > 0:
            msg = msgBuf.pop(0)
            if msg.lower().find( 'exit') >= 0:
                print( "received 'exit'")
                sys.exit()
            elif msg.lower().find( 'clear') >= 0:
                self.clearLogWidget()
            else:
                dialog.LogWidget.append( msg)

def cbInfo( *args): 
    global msgBuf

    if args is None or args[0] is None or args[0].attr_value is None or args[0].attr_value.value is None:
        return

    for line in args[0].attr_value.value:
        msgBuf.append( "%s" % line)
    # print('Info_EVENT_RECEIVED: %s' % str(args[0].attr_value.value))
    return

if __name__ == "__main__":
    options = None
    usage = "%prog -t <testName>"
    parser = OptionParser(usage=usage)
    parser.add_option("-t", action="store", type="string", dest="testName", help="just a test")
    (options, args) = parser.parse_args()

    
    if options.testName is None:
        pass
        
    i = 0
    for elm in sys.argv:
        if sys.argv[i] == '-t':
            del sys.argv[i+1]
            del sys.argv[i]
            break
        i += 1 

    if os.getenv( "DISPLAY") != ':0':
        TaurusApplication.setStyle( 'Cleanlooks')

    app = TaurusApplication(sys.argv)

    dialog = Dialog()

    sys.exit(dialog.exec_())

#!/usr/bin/env python
 
"""PyQt4 port of the layouts/basiclayout example from Qt v4.x"""

import sys, os, time
from HasyUtils.pyqtSelector import *
import taurus
from optparse import OptionParser
import HasyUtils
import PyTango
import signal

PORT = 7660

msgBuf = []

class Dialog(QDialog):
    classVar = 12345
    def __init__(self, msg = None, parent=None):
        QDialog.__init__(self, parent)
        
        self.createMenubar()
        self.LogWidget = QTextEdit()
        self.LogWidget.setReadOnly( 1)

        self.createBottomLine()

        geo = QDesktopWidget().screenGeometry(-1)
        self.setGeometry( geo.width() - 680, 300, 650, 500)

        mainLayout = QVBoxLayout()
        mainLayout.setMenuBar(self.menuBar)
        mainLayout.addWidget(self.LogWidget)
        mainLayout.addLayout(self.bottomLayout)

        self.setLayout(mainLayout)

        self.timer = QtCore.QTimer()
        self.timer.timeout.connect( self._cb_timeout)
        self.timer.start( 200)
        
        self.setWindowTitle(self.tr("Sardana Message Window"))

        self.door = PyTango.DeviceProxy( HasyUtils.getLocalDoorNames()[0])
        self.door.subscribe_event('Info', PyTango.EventType.CHANGE_EVENT, cbInfo)
        
        self.show()

    def closeEvent( self, event):
        reply = QMessageBox.question(self, 'Message',
                                           "Are you sure to quit?", QMessageBox.Yes | 
                                           QMessageBox.No, QMessageBox.No)

        if reply == QMessageBox.Yes:
            event.accept()
        else:
            event.ignore()
        
    def clearLogWidget( self):
        self.LogWidget.clear()

    def createBottomLine( self):
        #
        # exit
        #
        self.exitButton = QPushButton(self.tr("E&xit"))
        self.exitButton.setShortcut( "Alt+x")
        self.exitButton.clicked.connect( self.cb_close)
        #
        # Clear log
        #
        self.clearLogButton = QPushButton(self.tr("&Clear log"))
        self.clearLogButton.clicked.connect( self.clearLogWidget)

        self.bottomLayout = QHBoxLayout()
        self.bottomLayout.addStretch(1)
        self.bottomLayout.addWidget(self.clearLogButton)
        self.bottomLayout.addWidget(self.exitButton)

    def createMenubar(self):
        self.menuBar = QMenuBar()
        
        self.fileMenu = QMenu(self.tr("&File"), self)
        
        self.helpMenu = QMenu(self.tr("&Help"), self)
        self.helpNewsAction = self.helpMenu.addAction(self.tr("&News"))
        self.helpNewsAction.triggered.connect( self.cb_helpNews)

        
        self.exitAction = self.fileMenu.addAction(self.tr("E&xit"))
        self.exitAction.triggered.connect( self.cb_close)
        
        self.menuBar.addMenu(self.fileMenu)
        self.menuBar.addMenu(self.helpMenu)


    def cb_helpNews(self):
        QMessageBox.about(self, self.tr("Help News"), self.tr(
                "<h3> Sardana Message Window News</h3>"
                "9.7.2015 first entry"
                "<p>"
                "9.7.2015 another entry"
                ))

    def cb_close( self): 
        self.close()
        
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

    if args[0].attr_value.value is None:
        #msgBuf.append( "empty")
        return

    for line in args[0].attr_value.value:
        msgBuf.append( "+++%s" % line)
    # print('Info_EVENT_RECEIVED: %s' % str(args[0].attr_value.value))

if __name__ == "__main__":
    options = None
    usage = "%prog -t <testName>"
    parser = OptionParser(usage=usage)
    parser.add_option("-t", action="store", type="string", dest="testName", help="just a test")
    (options, args) = parser.parse_args()

    
    if options.testName is None:
        pass
        
    i = 0
    msg = None
    for elm in sys.argv:
        if sys.argv[i] == '-t':
            del sys.argv[i+1]
            del sys.argv[i]
            
        i += 1 
    app = TaurusApplication(sys.argv)

    dialog = Dialog( msg)

    sys.exit(dialog.exec_())

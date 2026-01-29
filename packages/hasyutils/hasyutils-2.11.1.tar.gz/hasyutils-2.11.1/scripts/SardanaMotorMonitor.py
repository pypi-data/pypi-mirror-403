#!/usr/bin/env python

import PyTango 
import HasyUtils
import sys, json, time, os
import taurus.qt.qtgui.panel
import taurus.qt.qtgui.application
from taurus.external.qt import Qt
from taurus.external.qt import QtCore
from taurus.qt.qtgui.application import TaurusApplication
from taurus.qt.qtgui.display import TaurusLabel
from taurus.core.taurushelper import changeDefaultPollingPeriod

MOTOR_MAX = 35

timeOut = 500
pollingPeriod = 1000
#
# motorDict is a dictionary of MotorBlocks
#
motorDict = {}

class MotorBlock():
    def __init__( self, devDct):
        #print( "MotorBlock", repr( devDct))
        self.name_pool = devDct[ 'name']        # d1_mot01        pool alias
        try:
            self.proxy_pool = PyTango.DeviceProxy( "%s/%s" % (devDct[ 'hostname'], devDct[ 'name']))
        except Exception as e:
            self.proxy_pool = None
        try:
            self.name_ts = devDct[ 'device']   # p09/motor/d1.01 tango device name
            self.proxy_ts = PyTango.DeviceProxy( "%s/%s" % (devDct[ 'hostname'], devDct[ 'device']))       
            sts = self.proxy_ts.state()
        except: 
            print( "MotorBlock: no proxy to %s" % self.name_ts)
            self.name_ts = None
            self.proxy_ts = None

        self.status = None
        self.eventId = None
#
# motorHBoxLines is a dictionary of motorHBoxLine entries
#
motorHBoxLines = {}

app = None
energyLine = None

class motorHBoxLine( Qt.QHBoxLayout):
    '''
    creates a horizontal line of three label widgets, for 
    motor name, actual value and the setpoint
    '''
    def __init__( self, nameIn): 
        Qt.QHBoxLayout.__init__( self)
        #if not HasyUtils.getDeviceNameByAlias( nameIn):
        #    print( "motorHBoxLine", nameIn, "return immediately")
        #    return None
        proxy = motorDict[ nameIn].proxy_ts
        name = motorDict[ nameIn].name_ts
        if proxy  is None:
            proxy = motorDict[ nameIn].proxy_pool
            name =  motorDict[ nameIn].name_pool
        self.nameLabel = TaurusLabel()
        self.nameLabel.setText( nameIn)
        self.actualLabel = TaurusLabel()
        self.setpointLabel = TaurusLabel()
        self.nameLabel.setMinimumWidth( 60)
        self.actualLabel.setMinimumWidth( 100)
        self.actualLabel.setModel( name + "/position")
        self.actualLabel.setBgRole( 'state')
        self.setpointLabel.setMinimumWidth( 80)

        attr = proxy.read_attribute( "position")
        self.setpointLabel.setText( str( attr.w_value))

        self.addWidget( self.nameLabel)
        self.addWidget( self.actualLabel)
        self.addWidget( self.setpointLabel)


class hLine( Qt.QFrame):
    def __init__( self, width):
        Qt.QFrame.__init__( self)
        self.setFrameShape( Qt.QFrame.HLine)
        self.setLineWidth( width)
        
class MotorMonitorPanel( Qt.QWidget):
    def __init__( self):
        global energyLine
        Qt.QWidget.__init__( self)

        self.name = "ThePanel"
        self.timer = QtCore.QTimer(self)
        self.timer.timeout.connect( self.cb_timeout)
        #self.connect( self.timer, QtCore.SIGNAL("timeout()"), self.cb_timeout)
        self.timer.start( timeOut)
        self.setWindowTitle( "MotorMonitor")

        self.setGeometry( 300, 300, 400, 500) # ax, ay, aw, ah
        #
        # use online.xml to find the motors
        #
        allDevices = HasyUtils.getOnlineXML()
        if allDevices:
            for dev in allDevices:
                if (dev['module'].lower() == 'motor_tango' or 
                    dev['type'].lower() == 'stepping_motor'):
                    mb = MotorBlock( dev)
                    if mb.proxy_ts:
                        motorDict[ dev[ 'name']] = MotorBlock( dev)
        #
        # the diffractometer devices are not mentioned explicitly in online.xml
        #
        lst = HasyUtils.getLocalPoolNames()
        if len( lst) > 0:
            pool = PyTango.DeviceProxy( HasyUtils.getLocalPoolNames()[0])
            for mot in pool.MotorList:
                poolDct = json.loads( mot)
                name = poolDct['name']
                if name in motorDict.keys():
                    #print( "name already in motorDict", name)
                    pass
                else:
                    #print( " name NOT in motorDict", name, repr( poolDct))
                    #
                    # source: haso107d1:10000/pm/e6cctrl/1/Position
                    #
                    dev = {}
                    dev[ 'name'] = name
                    dev[ 'type'] = 'type_tango'
                    dev[ 'module'] = 'motor_tango'
                    dev[ 'control'] = 'tango'
                    # source: haso107d1:10000/pm/e6cctrl/1/Position
                    lst = poolDct[ 'source'].split( '/')
                    dev[ 'hostname'] = lst[0]
                    dev[ 'device'] = "/".join( lst[1:-1])
                    mb = MotorBlock( dev)
                    if mb.proxy_ts:
                        motorDict[ dev[ 'name']] = MotorBlock( dev)
        if not motorDict:
            print( "no motors found")
            sys.exit( 255)
            return

        self.door = PyTango.DeviceProxy( HasyUtils.getLocalDoorNames()[0])
        #
        # the grand vertical layout
        #
        self.vboxGrand = Qt.QVBoxLayout()
        #
        # the energy line
        #
        if 'mnchrmtr' in motorDict:
            energyLine = motorHBoxLine( 'mnchrmtr')
            if energyLine:
                energyLine.nameLabel.setText( "Energy")
                self.vboxGrand.addLayout( energyLine)
                self.vboxGrand.addWidget( hLine( 1))
        #
        # the motor lines
        #
        self.vboxMotorLines = Qt.QVBoxLayout()
        self.vboxGrand.addLayout( self.vboxMotorLines)
        self.vboxGrand.addStretch(1)
        #
        # the macroserver status line
        #
        #self.doorLine = Qt.QHBoxLayout()
        #self.statusLineMS = TaurusLabel( 'MS: Idle')
        #self.doorLine.addWidget( self.statusLineMS)
        #self.doorLine.addStretch(1)
        #self.vboxGrand.addWidget( hLine( 1))
        #self.vboxGrand.addLayout( self.doorLine)

        #
        # the bottom line
        #
        self.bottomLine = Qt.QHBoxLayout()
        #
        # exit button
        #
        self.exitButton = Qt.QPushButton(self.tr("E&xit")) 
        self.exitButton.clicked.connect( app.quit)
        #self.connect( self.exitButton, QtCore.SIGNAL("clicked()"), app.quit)
        #
        # stopMove button
        #
        self.stopMoveButton = Qt.QPushButton(self.tr("&Stop Move")) 
        self.stopMoveButton.clicked.connect( self.cb_stopMove)
        #self.connect( self.stopMoveButton, QtCore.SIGNAL("clicked()"), self.cb_stopMove)
        #
        # stopMacro button
        #
        self.stopMacroButton = Qt.QPushButton(self.tr("Stop Macro")) 
        self.stopMacroButton.clicked.connect( self.cb_stopMacro)
        #self.connect( self.stopMacroButton, QtCore.SIGNAL("clicked()"), self.cb_stopMacro)

        self.bottomLine.addWidget( self.stopMoveButton)
        self.bottomLine.addWidget( self.stopMacroButton)
        self.bottomLine.addStretch(1)
        self.bottomLine.addWidget( self.exitButton) 

        self.vboxGrand.addWidget( hLine( 1))
        self.vboxGrand.addLayout( self.bottomLine)

        self.setLayout(self.vboxGrand)
        #
        # the names of the motors which are displayed
        #
        self.displayedNames = []
        
        self.motorListMoving = []
    #
    # this might be very risky - ctrlc
    #
    #def updateStatusLineMS( self): 
    #    a = HasyUtils.getMacroServerStatusInfo()
    #    if a == "Idle":
    #        self.statusLineMS.setText( "MS: " + a)
    #        self.statusLineMS.setStyleSheet( "QLabel {background-color : rgb( 0, 255, 0); color : black;}")
    #        return
    #    self.statusLineMS.setText( "MS: " + a )
    #    self.statusLineMS.setStyleSheet( "QLabel {background-color : LightSkyBlue; color : black;}")

    def findMovingMotors( self):
        global pollingPeriod
        #
        # haso107d1: this function takes about 25 msecs.
        #
        self.motorListMoving = []
        for key in motorDict.keys():
            if not motorDict[ key].proxy_ts is None:
                if motorDict[key].proxy_ts.state() == PyTango.DevState.MOVING:
                    #print( "%s -> %s (ts) " % ( key, repr( motorDict[ key].proxy_ts.state())))
                    self.motorListMoving.append( key)
            else:
                if motorDict[key].proxy_pool.state() == PyTango.DevState.MOVING:
                    #print( "%s -> %s" % ( key, repr( motorDict[ key].proxy_pool.state())))
                    self.motorListMoving.append( key)
        if len( self.motorListMoving) > 0:
            if len( self.motorListMoving) > MOTOR_MAX:
                print( "SardanaMotorMonitor: list of moving motors %d too long, max.: %d " % 
                       (len( self.motorListMoving), MOTOR_MAX)) 
                return False
            if pollingPeriod == 1000:
                pollingPeriod = 200
                changeDefaultPollingPeriod( pollingPeriod)
            return True

        if pollingPeriod == 200:
            pollingPeriod = 1000
            changeDefaultPollingPeriod( pollingPeriod)
        return False
        

    def cb_timeout(self):
        #self.updateStatusLineMS()
        if not self.findMovingMotors():
            return
        count = 0

        for motorName in self.motorListMoving:
            if motorName in motorHBoxLines:
                continue
            motorHBoxLines[motorName] = motorHBoxLine( motorName)
            self.vboxMotorLines.addLayout( motorHBoxLines[motorName])
            self.displayedNames.append( motorName)
            #
            # if we display more that MOTOR_MAX lines, delete the first line
            #
            if len( self.displayedNames) > MOTOR_MAX:
                name = self.displayedNames[0]
                layout = motorHBoxLines[name]
                #
                # a widget is really deleted, if it has no parent
                #
                for i in reversed( range( layout.count())):
                   layout.itemAt(i).widget().setParent(None) 
                del motorHBoxLines[name]
                del self.displayedNames[0]

        #
        # update the setpoint
        #
        if not energyLine is None:
            attr = motorDict[ 'mnchrmtr'].proxy_ts.read_attribute( "position")
            energyLine.setpointLabel.setText( "%6.2f" % attr.w_value)
        for motorName in motorHBoxLines.keys():
            attr = motorDict[ motorName].proxy_ts.read_attribute( "position")
            try:
                motorHBoxLines[ motorName].setpointLabel.setText( "%6.2f" % attr.w_value )
            except Exception as e:
                print( "cb_timeout, trouble with %s" % motorName)

    def cb_stopMove( self):
        for motorName in self.motorListMoving:
            motorDict[ motorName].proxy_ts.stopmove()

    def cb_stopMacro( self):
        self.door.StopMacro()

def main():
    global app 

    if os.getenv( "DISPLAY") != ':0':
        TaurusApplication.setStyle( 'Cleanlooks')
    app = TaurusApplication(sys.argv)
    panel = MotorMonitorPanel()

    panel.show()
    sys.exit(app.exec_())

if __name__ == "__main__":
    main()

 

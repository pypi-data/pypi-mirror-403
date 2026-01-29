#!/usr/bin/env python
"""
The SardanaAlarmMonitor is an application for popping up alarm windows 
when certain conditions are not full filled. The conditions have to be 
defined in a file called AlarmFunctions.py placed in a directory belonging 
to the PYTHONPATH or where the SardanaAlarmMonitor.py script is placed. 

"""
import sys

from taurus.external.qt import Qt
from taurus.external.qt import QtCore
from taurus.qt.qtgui.application import TaurusApplication
from taurus.qt.qtgui.plot import TaurusTrend
from taurus.qt.qtgui.container import TaurusWidget
from taurus.qt.qtgui.base import TaurusBaseComponent, TaurusBaseWidget
from taurus.qt.qtgui.util.ui import UILoadable
from taurus.qt.qtgui.display import TaurusLabel

import PyTango

import AlarmFunctions

timeOut = 500

window_up = []

class MainAlarmViewerWindow(TaurusWidget):
    
    
    def __init__(self, parent=None):

        TaurusWidget.__init__(self, parent)
        self.call__init__(TaurusBaseComponent, self.__class__.__name__)
        self.timer = QtCore.QTimer(self)
        self.connect( self.timer, QtCore.SIGNAL("timeout()"), self.cb_timeout)
        self.timer.start(timeOut)

        hBox = Qt.QVBoxLayout()
        
        self.label = []
        self.window_up = []
        self.w = []
        
        ilabel = 0
        global window_up
        
        for alarm_test in  list(AlarmFunctions.func_dict.keys()):
            if not callable( alarm_test): 
                continue
            self.label.append(TaurusLabel())
            self.window_up.append(0)
            window_up.append(0)
            hBox.addWidget(self.label[ilabel])
            hBox.addStretch()
            self.label[ilabel].setText(AlarmFunctions.func_dict[alarm_test][0])
            palette = self.label[ilabel].palette()
            palette.setColor(self.label[ilabel].foregroundRole(), Qt.Qt.blue);
            self.label[ilabel].setPalette(palette);
            self.w.append(alarm(AlarmFunctions.func_dict[alarm_test][1], ilabel))
            ilabel = ilabel + 1

        self.setLayout(hBox)
    
    def cb_timeout(self):
        global window_up
        for i in range(0, len( list(AlarmFunctions.func_dict.keys()))):
            func_name = list(AlarmFunctions.func_dict.keys())[i]
            func = getattr(AlarmFunctions, func_name)
            if func() and (self.window_up[i] == 0 or window_up[i] == 0):
                palette = self.label[i].palette()
                palette.setColor(self.label[i].foregroundRole(), Qt.Qt.red);
                self.label[i].setPalette(palette);
                self.window_up[i] = 1
                window_up[i] = 1
                self.w[i].show()
            elif not func() and (self.window_up[i] == 1 or window_up[i] == 1):
                palette = self.label[i].palette()
                palette.setColor(self.label[i].foregroundRole(), Qt.Qt.blue);
                self.label[i].setPalette(palette);
                self.window_up[i] = 0
                window_up[i] = 0
                self.w[i].close()
import os
module_path = os.path.split(os.path.abspath(__file__))[0]

@UILoadable(with_ui="ui")
class alarm(TaurusWidget):
      
    def __init__(self, text, index, parent=None):
        TaurusWidget.__init__(self, parent)
        self.loadUi(os.path.join(module_path,"alarm.ui")) # Loads alarm.ui
        self.ui.alarm_label.setText(text)
        palette = self.ui.alarm_label.palette()
        palette.setColor(self.ui.alarm_label.foregroundRole(), Qt.Qt.red);
        self.ui.alarm_label.setPalette(palette);

        self.index = index
        self.connect(self.ui.closealarm_button, Qt.SIGNAL("clicked()"), self.close_window)

    def close_window(self):
        global window_up
        self.close()
        window_up[self.index] = 0

        
    
        
def AlarmViewer():
    from taurus.qt.qtgui.application import TaurusApplication
    import taurus.core
    
    parser = taurus.core.util.argparse.get_taurus_parser()
    parser.set_usage("%prog [options] <model>")
    parser.set_description('Alarm states')
    
    app = TaurusApplication(cmd_line_parser=parser, app_name="Alarm Viewer", app_version=taurus.Release.version)
    args = app.get_command_line_args()
    
    w = MainAlarmViewerWindow()
    
    w.show()
    sys.exit(app.exec_())

if __name__ == "__main__":
    AlarmViewer()




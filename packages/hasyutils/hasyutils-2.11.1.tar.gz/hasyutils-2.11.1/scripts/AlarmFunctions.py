#!/usr/bin/env python
'''
this file is used by
  /home/kracht/Misc/hasyutils/scripts/SardanaAlarmMonitor.py
'''
import PyTango

# Function_name: ("Label", "Alarm message")

func_dict = {"mytest1": ("Motor1 position", "Motor 1 above allowed position (10)"),
              "mytest2": ("Motor2 position", "Motor 2 above allowed position (12)")}



def mytest1():
    motor_proxy = PyTango.DeviceProxy("p09/motor/exp.01")
    pos = motor_proxy.Position
    if pos > 10:
        return True
    else:
        return False
    
def mytest2():
    motor_proxy = PyTango.DeviceProxy("p09/motor/exp.02")
    pos = motor_proxy.Position
    if pos > 12:
        return True
    else:
        return False

def mytest3():
    motor_proxy = PyTango.DeviceProxy("p09/motor/exp.01")
    pos = motor_proxy.Position
    if pos > 10:
        return True
    else:
        return False

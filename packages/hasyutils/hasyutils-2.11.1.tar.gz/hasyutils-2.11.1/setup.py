#!/usr/bin/python
# this scipt is executed with
#
from distutils.core import setup

PACKAGE_NAME = "hasyutils"

#
(major, minor, patch) = (2, 11, 1)
#
# this is the source version
#
version = "%s.%s.%s" % (major, minor, patch)

setup(name=PACKAGE_NAME,
      version=version,
      author="Thorsten Kracht",
      author_email="fs-ec@desy.de",
      url="https://gitlab.desy.de/fs-ec/hasyutils",
      #
      # beware: MANIFEST somehow memorizes the script names (can be deleted)
      #
      scripts=['scripts/alarm.ui',
               'scripts/ECMonitor.py',
               'scripts/HasyUtilsMain.py',
               'scripts/MotorLogger.py',
               'scripts/nxsreader.py',
               'scripts/SardanaAIO.py',
               'scripts/SardanaAlarmMonitor.py',
               'scripts/SardanaChMg.py',
               'scripts/SardanaClearSCAs.py',
               'scripts/SardanaConvert.py',
               'scripts/SardanaDeleteMotorGroups.py',
               'scripts/SardanaDiag.py',
               'scripts/SardanaInfoViewer.py',
               'scripts/SardanaIVP.py',
               'scripts/SardanaLimitsFromTS2Pool.py',
               'scripts/SardanaMacroExecutor.py',
               'scripts/SardanaChat.py',
               'scripts/SardanaMacroTester.py',
               'scripts/SardanaMotorMonitor.py',
               'scripts/SardanaRestartBoth.py',
               'scripts/SardanaRestartMacroServer.py',
               'scripts/SardanaRestartPool.py',
               'scripts/SardanaShutdown.py',
               'scripts/SardanaStartMacroServer.py',
               'scripts/SardanaAdjustLimits.py',
               'scripts/SardanaCheckOnlineXml.py',
               'scripts/SardanaStartPool.py',
               'scripts/SardanaStartup.py',
               'scripts/SardanaStatus.py',
               'scripts/SardanaStopBoth.py',
               'scripts/SardanaStopMacroServer.py',
               'scripts/SardanaStopPool.py',
               'scripts/SardanaStopMacro.py',
               'scripts/nxs_ifc.py',
               'scripts/nxsclient.py',
               'scripts/TngEigerCLI.py',
               'scripts/TngUtility.py',
               'scripts/TngMonitorAttrs.py',
               ],
      packages=['HasyUtils'])

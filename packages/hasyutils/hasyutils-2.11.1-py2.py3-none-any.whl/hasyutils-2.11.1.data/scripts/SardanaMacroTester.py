#!python
#
import sys, os
import glob
import PyTango
import inspect
import HasyUtils
import sardana.macroserver.macro as ms
import argparse
import traceback
import importlib 

#
# The types: Type.Moveable, Type.Float, Type.String, etc.
#
ms.Type = HasyUtils.TypeNames()

class LoadedMacros:
    """
    contains the loaded macros: pathName, macro_lib and classes
    """
    def __init__( self):
        self.pathName = []
        self.macro_libs = []
        self.classObjs = []

    def add( self, pathName, module, showFull = False):
        """
        n.n.
        """
        self.pathName.append( pathName)
        self.macro_libs.append( module.__name__)

        lst = []
        for name, obj in inspect.getmembers( module):
            #
            # obj:            <class 'petra_macros.wait_for_petra'>
            # obj.__module__: petra_macros
            # obj.__name__:   wait_for_petra
            #
            # we are only interested in conflicts between Macro classes
            #
            if inspect.isclass(obj) and \
                    issubclass( obj, ms.Macro) and \
                    obj.__name__ != 'Macro' and \
                    obj.__name__ != 'MacroFunc' and \
                    obj.__name__ != 'iMacro':                    
                if showFull:
                    print( "   adding %s " % (obj.__name__))
                lst.append(obj)
        #
        # append the list of a moduls class objects 
        #
        self.classObjs.append( lst)

    def searchConflictingMacroLib( self, macro_lib, pathName):
        """
        Search the loaded macro_libs for macro_lib. 
        Return True, if a conflict has been found.
        """
        argout = False
        if macro_lib in self.macro_libs:
            index = self.macro_libs.index( macro_lib)
            print( "*** conflicting Macro lib: %s.py from %s" % (macro_lib, pathName))
            print( "  exists also in %s" % (self.pathName[ index]))
            argout = True
        return argout

    def searchConflictingClasses( self, module, pathName, macro_lib):
        """
        Compare classes contained in module against classes loaded so far.
        Return True, if at least one conflict has been found.
        """
        argout = False
        lst = []
        for name, obj in inspect.getmembers( module):
            if inspect.isclass(obj):
                lst.append(obj)
        for elm in lst:
            for classObjs in self.classObjs:
                for cls in classObjs:
                    #
                    # obj:            <class 'petra_macros.wait_for_petra'>
                    # obj.__module__: petra_macros
                    # obj.__name__:   wait_for_petra
                    #
                    # 8.6.2023: change to case sensitive comparison
                    #
                    if elm.__name__ == cls.__name__:                    
                        index = self.classObjs.index( classObjs)
                        print( "\n*** conflicting class %s" % (elm))
                        print( "  when loading %s/%s.py " % (pathName, macro_lib))
                        print( "  class '%s' already imported from" % (elm.__name__))
                        print( "  %s/%s.py " % (self.pathName[index], self.macro_libs[index]))
                        argout = True
        return argout

class MacroTester:

    def __init__( self, showFull):

        self.showFull = showFull

        lst = HasyUtils.getMacroServerNames()
        if len( lst) != 1:
            print( "No. of MacroServers != 1 %s" % repr( lst))
            sys.exit(255)

        try:
            self.ms = PyTango.DeviceProxy( lst[0])
        except:
            print( "failed to create a proxy to %s" % lst[0])
            sys.exit()

        tempVec = self.ms.get_property( "MacroPath")['MacroPath']
        self.macroPath = []
        for temp in tempVec: 
            self.macroPath.append( temp)
        if os.path.exists( "/usr/lib/python3/dist-packages/sardana/macroserver/macros"):
            self.macroPath.insert( 0, "/usr/lib/python3/dist-packages/sardana/macroserver/macros")

        self.pythonPath = self.ms.get_property( "PythonPath")['PythonPath']

        sys.path.extend( self.pythonPath)


    def run( self):

        loadedMacros = LoadedMacros()
        flagConflict = False
        
        for pathName in self.macroPath:
            if not os.path.isdir( pathName):
                print( "*** directory %s does not exist" % pathName)
                continue

            if self.showFull or True:
                print( "--- visiting %s" % pathName)

            os.chdir( pathName)
            if pathName not in sys.path: 
                sys.path.insert( 0, pathName)
            fileList = glob.glob( "*.py")
            mfile = None
            for f in fileList:
                if self.showFull:
                    print( "looking at %s" % f)

                macro_lib = f.split('.')[0]
                if macro_lib == "__init__":
                    continue
                if loadedMacros.searchConflictingMacroLib( macro_lib, pathName):
                    flagConflict = True
                if self.showFull:
                    print( "  importing %s.py" % ( macro_lib),)
                try:
                    m = importlib.import_module( macro_lib)
                    if loadedMacros.searchConflictingClasses( m, pathName, macro_lib):
                        flagConflict = True
                        
                    loadedMacros.add( pathName, m, self.showFull)
                    if self.showFull:
                        print( "--> OK")
                except Exception as e:
                    print( "\n*** Failed to import %s/%s.py" % (pathName, macro_lib))
                    #print(traceback.format_exc())
                    #print( " %s" % sys.exc_info()[0])
                    print( " %s" % repr(e))
                    # 6.11.2024: too mauch output
                    #exc_type, exc_value, exc_traceback = sys.exc_info()
                    #traceback.print_tb(exc_traceback, limit=None, file=sys.stdout)
                    flagConflict = True
                finally:
                    if mfile is not None:
                        mfile.close()
                self.findStringMacro( macro_lib)

        if not flagConflict:
            print( " ... all is well")

    def findStringMacro( self, libName): 
        tempString = open('%s.py' % libName).read()
        #
        # 'Macro' for classes, 'macro' for functions
        #
        if not 'macro' in tempString.lower():
            print( "%s.py does not contain 'macro'" % libName)
            if not '__name__' in tempString:
                print( "%s.py is directly executable, does not contain '__name__'" % libName)

    def single( self, filename):
        """
        examine a single file
        """
        pathName = None
        macro_lib = None
        mfile = None
        lst = filename.rsplit( "/", 1)
        if len(lst) == 1:
            pathName = ""
            macro_lib = lst[0]
        elif len(lst) == 2:
            pathName = lst[0]
            macro_lib = lst[1]
        else:
            print( "something is wrong with %s" % filename)
            return

        if macro_lib.find( ".py") > 0:
            macro_lib = macro_lib.split('.')[0]

        if "." not in sys.path: 
            sys.path.insert( 0, ".")
        if pathName not in sys.path:
            sys.path.append( pathName)
        try:
            m = importlib.import_module( macro_lib)
            for name, obj in inspect.getmembers( m):
                if inspect.isclass(obj):
                    print( "class %s" %(obj))
        except Exception as e:
            print( "\n*** Failed to import %s" % (pathName))
            print( " %s" % sys.exc_info()[0])
            print( " %s" % repr(e))
        finally:
            if mfile is not None:
                mfile.close()

if __name__ == '__main__':
    parser = argparse.ArgumentParser( 
        formatter_class = argparse.RawDescriptionHelpFormatter,
        description=
"import all macros from MacroPath and report\n\
  - Python errors \n\
  - conflicting macro library names \n\
  - conflicting class names\
",
        epilog='''\
Examples:
  SardanaMacroTester.py 
    show only errors and conflicts
  SardanaMacroTester.py -a
    show all loaded macros and errors and conflicts
  SardanaMacroTester.py -f fName.py
    examine a single file, perform only Python
    ''')
    parser.add_argument('-a', dest="showFull", action="store_true", help='show all loaded macros')
    parser.add_argument('-f', dest="filename", help='examine a single file')
    args = parser.parse_args()

    o = MacroTester( args.showFull)
    if args.filename:
        o.single( args.filename)
    else:
        o.run()


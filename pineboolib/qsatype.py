# -*- coding: utf-8 -*-

from __future__ import unicode_literals
import os, fnmatch, re
import datetime, weakref
from lxml import etree
from io import StringIO

from PyQt5 import QtCore, QtGui, QtWidgets

# Cargar toda la API de Qt para que sea visible.
from PyQt5.QtGui import *
from PyQt5.QtCore import *
from PyQt5.QtCore import QIODevice

from pineboolib import qsaglobals
from pineboolib import flcontrols
from pineboolib.fllegacy import FLFormSearchDB as FLFormSearchDB_legacy
from pineboolib.flcontrols import FLTable, QLineEdit
from pineboolib.fllegacy import FLSqlQuery as FLSqlQuery_Legacy
from pineboolib.fllegacy import FLSqlCursor as FLSqlCursor_Legacy
from pineboolib.fllegacy import FLTableDB as FLTableDB_Legacy
from pineboolib.fllegacy import FLUtil as FLUtil_Legacy
from pineboolib.fllegacy import FLReportViewer as FLReportViewer_Legacy

from pineboolib.utils import filedir

from pineboolib import decorators
import traceback
from PyQt5.Qt import QWidget

class StructMyDict(dict):

     def __getattr__(self, name):
         try:
             return self[name]
         except KeyError as e:
             raise AttributeError(e)

     def __setattr__(self, name, value):
         self[name] = value
         
def Function(args, source):
    # Leer código QS embebido en Source
    # asumir que es una funcion anónima, tal que: 
    #  -> function($args) { source }
    # compilar la funcion y devolver el puntero
    qs_source = """
function anon(%s) {
    %s
} """ % (args,source)
    print("Compilando QS en línea: ", qs_source)
    from pineboolib.flparser import flscriptparse
    from pineboolib.flparser import postparse
    from pineboolib.flparser.pytnyzer import write_python_file, string_template
    import io
    prog = flscriptparse.parse(qs_source)
    tree_data = flscriptparse.calctree(prog, alias_mode = 0)
    ast = postparse.post_parse(tree_data)
    tpl = string_template
    
    f1 = io.StringIO()

    write_python_file(f1,ast,tpl)
    pyprog = f1.getvalue()
    print("Resultado: ", pyprog)
    glob = {}
    loc = {}
    exec(pyprog, glob, loc)
    # ... y lo peor es que funciona. W-T-F.
    
    return loc["anon"]

def Object(x=None):
    if x is None: x = {}
    return StructMyDict(x)

#def Array(x=None):
    #try:
        #if x is None: return {}
        #else: return list(x)
    #except TypeError:
        #return [x]
        
class Array(object):
    
    dict_ = None
    key_ = None
    
    def __init__(self, data = None):
        if not data:
            self.dict_ = {}
        elif isinstance(data, int):
            self.dict_ = {} # dimensiones por ahora a cero
        else:
            self.dict_ = data
    
    def __setitem__(self, key, value):
        #if isinstance(key, int):
            #key = str(key)
        self.dict_[key] = value
        
            
        
    def __getitem__(self, key):
        #if isinstance(key, int):
            #key = str(key)
        #print("QSATYPE.DEBUG: Array.getItem() " ,key,  self.dict_[key])
        return self.dict_[key]
    
    def __getattr__(self, k):
        if k == 'length': 
            return len(self.dict_)

       

def Boolean(x=False): return bool(x)

def FLSqlQuery(*args):
    #if not args: return None
    query_ = FLSqlQuery_Legacy.FLSqlQuery(*args)
        
        
    return query_

def FLUtil(*args):
    return FLUtil_Legacy.FLUtil(*args)

def AQUtil(*args):
    return FLUtil_Legacy.FLUtil(*args)

def FLSqlCursor(action=None):
    if action is None: return None
    return FLSqlCursor_Legacy.FLSqlCursor(action)

def FLTableDB(*args):
    if not args: return None
    return FLTableDB_Legacy.FLTableDB(*args)

FLListViewItem = QtWidgets.QListView
QTable = FLTable
Color = QtGui.QColor
QColor = QtGui.QColor
QDateEdit = QtWidgets.QDateEdit

                    

@decorators.NotImplementedWarn
def FLPosPrinter(*args, **kwargs):
    class flposprinter:
        pass
    return flposprinter()

@decorators.BetaImplementation
def FLReportViewer():
    return FLReportViewer_Legacy.FLReportViewer()


class FLDomDocument(object):
    
    parser = None
    tree = None
    root_ = None
    string_ = None
    
    def __init__(self):
        self.parser = etree.XMLParser(recover=True, encoding='utf-8')
        self.string_ = None
        

    def setContent(self, value):
        try:
            self.string_ = value
            if value.startswith('<?'):
                value = re.sub(r'^\<\?.*?\?\>','', value, flags=re.DOTALL)
            self.tree = etree.fromstring(value, self.parser)
            #self.root_ = self.tree.getroot()
            return True
        except:
            return False
    
    @decorators.NotImplementedWarn
    def namedItem(self, name):
        return True

    def toString(self, value = None):
        return self.string_
    
    
        
    
        

@decorators.NotImplementedWarn
def FLCodBar(*args, **kwargs):
    class flcodbar:
        def nameToType(self, name):
            return name
        def pixmapError(self):
            return QtGui.QPixmap()
        def pixmap(self):
            return QtGui.QPixmap()
        def validBarcode(self):
            return None
    return flcodbar()

def print_stack(maxsize=1):
    for tb in traceback.format_list(traceback.extract_stack())[1:-2][-maxsize:]:
        print(tb.rstrip())

def check_gc_referrers(typename, w_obj, name):
    import threading, time
    def checkfn():
        import gc
        time.sleep(2)
        gc.collect()
        obj = w_obj()
        if not obj: return
        # TODO: Si ves el mensaje a continuación significa que "algo" ha dejado
        # ..... alguna referencia a un formulario (o similar) que impide que se destruya
        # ..... cuando se deja de usar. Causando que los connects no se destruyan tampoco
        # ..... y que se llamen referenciando al código antiguo y fallando.
        print("HINT: Objetos referenciando %r::%r (%r) :" % (typename, obj, name))
        for ref in gc.get_referrers(obj):           
            if isinstance(ref, dict): 
                x = []
                for k,v in ref.items():
                    if v is obj:
                        k = "(**)" + k
                        x.insert(0,k)
                    else:
                        x.append(k)    
                print(" - ", repr(x[:48]))
            else:
                if "<frame" in str(repr(ref)): continue
                print(" - ", repr(ref))

        
    threading.Thread(target = checkfn).start()
    

class FormDBWidget(QtWidgets.QWidget):

    closed =  QtCore.pyqtSignal()
    cursor_ = None
    
    def __init__(self, action, project, parent = None):
        super(FormDBWidget, self).__init__(parent)
        self._action = action
        self.cursor_ = FLSqlCursor(action.name)
        self._prj = project
        self._class_init()
        
    def __del__(self):
        print("FormDBWidget: Borrando form para accion %r" % self._action.name)
        

    def _class_init(self):
        pass
    
    def closeEvent(self, event):
        can_exit = True
        print("FormDBWidget: closeEvent para accion %r" % self._action.name)
        check_gc_referrers("FormDBWidget:"+self.__class__.__name__, weakref.ref(self), self._action.name)
        if hasattr(self, 'iface'):
            check_gc_referrers("FormDBWidget.iface:"+self.iface.__class__.__name__, weakref.ref(self.iface), self._action.name)
            del self.iface.ctx 
            del self.iface 
        
        if can_exit:
            self.closed.emit()
            event.accept() # let the window close
        else:
            event.ignore()
            
    def child(self, childName):
        try:
            ret = self.findChild(QtWidgets.QWidget, childName)
        except RuntimeError as rte:
            # FIXME: A veces intentan buscar un control que ya está siendo eliminado.
            # ... por lo que parece, al hacer el close del formulario no se desconectan sus señales.
            print("ERROR: Al buscar el control %r encontramos el error %r" % (childName,rte))
            print_stack(8)
            import gc
            gc.collect()
            print("HINT: Objetos referenciando FormDBWidget::%r (%r) : %r" % (self, self._action.name, gc.get_referrers(self)))
            if hasattr(self, 'iface'):
                print("HINT: Objetos referenciando FormDBWidget.iface::%r : %r" % (self.iface, gc.get_referrers(self.iface)))
            ret = None
        else:
            if ret is None:
                print("WARN: No se encontró el control %r" % childName)
        #else:
        #    print("DEBUG: Encontrado el control %r: %r" % (childName, ret))
        return ret

    def cursor(self):
        cursor = None
        try:
            if self.parentWidget():
                cursor = getattr(self.parentWidget(),"cursor_", None)

            if cursor and not cursor is self.cursor_ :
                return cursor
        except Exception:
            # FIXME: A veces parentWidget existía pero fue eliminado. Da un error
            # ... en principio debería ser seguro omitir el error.
            pass
        return self.cursor_

def FLFormSearchDB(name):
    widget = FLFormSearchDB_legacy.FLFormSearchDB(name)
    widget.setWindowModality(QtCore.Qt.ApplicationModal)
    widget.load()
    widget.cursor_.setContext(widget.iface)
    return widget

class Date(object):
    
    date_ = None
    time_ = None
    
    def __init__(self):
        super(Date, self).__init__()
        self.date_ = QtCore.QDate.currentDate()
        self.time_ = QtCore.QTime.currentTime()
    
    def toString(self, *args, **kwargs):
        texto = "%s-%s-%sT%s:%s:%s" % (self.date_.toString("yyyy"),self.date_.toString("MM"),self.date_.toString("dd"),self.time_.toString("hh"),self.time_.toString("mm"),self.time_.toString("ss"))
        return texto
    
    def getYear(self):
        return self.date_.year()
    
    def getMonth(self):
        return self.date_.month()
    
    def getDay(self):
        return self.date_.day()
    
    def getHours(self):
        return self.time_.hour()
    
    def getMinutes(self):
        return self.time_.minute()
    
    def getSeconds(self):
        return self.time_.second()
    
    def getMilliseconds(self):
        return self.time_.msec()

@decorators.NotImplementedWarn
class Process(object):
    
    def __init__(self):
        pass


@decorators.BetaImplementation
class RadioButton(QtWidgets.QRadioButton):
    pass
        


class Dialog(QtWidgets.QDialog):
    _layout = None
    buttonBox = None
    OKButtonText = None
    cancelButtonText = None
    OKButton = None
    cancelButton = None

    def __init__(self, title, f, desc=None):
        #FIXME: f no lo uso , es qt.windowsflg
        super(Dialog, self).__init__()
        self.setWindowTitle(title)
        self.setWindowModality(QtCore.Qt.ApplicationModal)
        self._layout = QtWidgets.QVBoxLayout()
        self.setLayout(self._layout)
        self.buttonBox = QtWidgets.QDialogButtonBox()
        self.OKButton = QtWidgets.QPushButton("&Aceptar")
        self.cancelButton = QtWidgets.QPushButton("&Cancelar")
        self.buttonBox.addButton(self.OKButton, QtWidgets.QDialogButtonBox.AcceptRole)
        self.buttonBox.addButton(self.cancelButton, QtWidgets.QDialogButtonBox.RejectRole)
        self.OKButton.clicked.connect(self.accept)
        self.cancelButton.clicked.connect(self.reject)


    def add(self, _object):
        self._layout.addWidget(_object)

    def exec_(self):
        if (self.OKButtonText):
            self.OKButton.setText(self.OKButtonText)
        if (self.cancelButtonText):
            self.cancelButton.setText(self.cancelButtonText)
        self._layout.addWidget(self.buttonBox)

        return super(Dialog, self).exec_()

class GroupBox(QtWidgets.QGroupBox):
    def __init__(self):
        super(GroupBox, self).__init__()
        self._layout = QtWidgets.QHBoxLayout()
        self.setLayout(self._layout)

    def add(self, _object):     
        self._layout.addWidget(_object)

class CheckBox(QtWidgets.QCheckBox):
    pass

class Dir(object):
    path_ = None
    home = None 
    
    def __init__(self, path):
        self.path_ = path
        self.home = filedir("..")
    
    def entryList(self, patron):
        p = os.walk(self.path_)
        retorno = []
        for file in os.listdir(self.path_):
            if fnmatch.fnmatch(file, patron):
                retorno.append(file)
        return retorno

class File(QtCore.QFile):
    fichero = None
    mode = None
        
    ReadOnly = QIODevice.ReadOnly
    WriteOnly = QIODevice.WriteOnly
    ReadWrite = QIODevice.ReadWrite
    
    def __init__(self, rutaFichero):
        self.fichero = rutaFichero
        super(File, self).__init__(rutaFichero)
    
    #def open(self, mode):
    #    super(File, self).open(self.fichero, mode)
    
    def read(self):
        in_ = QTextStream(self)
        return in_.readAll()
   
    
        

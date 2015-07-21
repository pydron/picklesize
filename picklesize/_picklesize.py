import types
import pickle
import sys
import copy_reg

#: Maps type to a function that takes two parameters:
#: * The object
#: * The :class:`PickleSize` instance.
#: Has to return the number of bytes needed to pickle the given object.
custom_estimators = {}

class PlaceHolder(object):
    """
    Instances of this class cause the estimate to increase by a set amount
    instead of the space it would actually require to store the instance.
    This can be used to correctly estimate the pickle size of large objects
    without actually constructing the object if there is some alternative
    way of estimating the size of it.
    """
    def __init__(self, size):
        self.size = size
        
    def __repr__(self):
        return "PlaceHolder(%r)" % self.size

class PickleSize(object):
    
    def picklesize(self, obj, protocol=0):
        
        if protocol < 0:
            protocol = 2
        if protocol != 2:
            raise ValueError("PickleSize only support pickle protocol 2.")
        self._protocol = protocol
        
        self._seen = {}
        
        return 3 + self._traverse(obj)
    
    
    def _traverse(self, obj):
        
        obj_id = id(obj)
        ref = self._seen.get(obj_id, None)
        if ref is not None:
            return self._encode_int(ref)
                
        obj_type = type(obj)
        handler = self._handlers.get(obj_type, None)
        
        if isinstance(handler, (int, long)):
            return handler
        
        if handler is not None:
            return handler(self, obj, obj_type, obj_id)
        
        custom_handler = custom_estimators.get(obj_type, None)
        if custom_handler is not None:
            return custom_handler(obj, self)

        return self._Generic(obj, obj_type, obj_id)
            
    def _memorize(self, obj_id):
        assert obj_id not in self._seen
        
        ref = len(self._seen)
        self._seen[obj_id] = ref
        
        return self._encode_int(ref)
        
    def _encode_int(self, value):
        if value <= 0xFF:
            return 2
        else:
            return 5
        
    def _IntType(self, value, obj_type, obj_id):
        if value >= 0:
            if value <= 0xFF:
                return 2;
            elif value <= 0xFFFF:
                return 3;
        return 5;
        
    def _LongType(self, value, obj_type, obj_id):
        data = pickle.encode_long(value)
        n = len(data)
        if n <= 0xFF:
            return 2 + n
        else:
            return 5 + n
        
    def _StringType(self, obj, obj_type, obj_id):
        n = len(obj)
        if n <= 0xFF:
            size = 2 + n
        else:
            size = 5 + n
        return size + self._memorize(obj_id)

    def _UnicodeType(self, obj, obj_type, obj_id):
        n = len(obj.encode("utf-8"))
        return 5 + n + self._memorize(obj_id)
        
    def _TupleType(self, obj, obj_type, obj_id):
        n = len(obj)
        if n == 0:
            return 1
        
        if n <= 3:
            size = sum(self._traverse(e) for e in obj)
            if obj in self._seen:
                # one of the elements already encoded this tuple
                size += n # n times POP
                size += self._encode_int(self._seen[id(obj)]) # GET from 'seen'
            else:
                # encodes number of elements
                size += 1
                size += self._memorize(obj_id)
            return size
        
        size = 1 + sum(self._traverse(e) for e in obj)
        if obj in self._seen:
            # one of the elements already encoded this tuple
            size += 1 # pop
            size += self._encode_int(self._seen[id(obj)]) # GET from 'seen'
        else:
            size += 1
            size += self._memorize(obj_id)
        return size
    
    def _ListType(self, obj, obj_type, obj_id):
        size = 1 + self._memorize(obj_id)
        for e in obj:
            size += self._traverse(e)
        size += self._batch_append_overhead(len(obj))
        return size
    
    def _batch_append_overhead(self, n):
        batch = pickle.Pickler._BATCHSIZE
        
        batchcount = n / batch
        size = 2*batchcount # MARK and APPENDS
        
        reminder = n % batch
        if reminder == 1:
            size += 1
        elif reminder > 1:
            size += 2
            
        return size
    
    def _DictType(self, obj, obj_type, obj_id):
        size = 1 + self._memorize(obj_id)
        for k, v in obj.iteritems():
            size += self._traverse(k) + self._traverse(v)
        size += self._batch_append_overhead(len(obj))
        return size
            
    def _InstanceType(self, obj, obj_type, obj_id):
            
        if hasattr(obj, '__getinitargs__'):
            initargs = obj.__getinitargs__()
            len(initargs)
        else:
            initargs = ()

        size = 1 + self._traverse(obj.__class__)
        for initarg in initargs:
            size += self._traverse(initarg)
            
        size += 1 + self._memorize(obj_id)

        if hasattr(obj, "__getstate__"):
            attributes = obj.__getstate__()
        else:
            attributes = obj.__dict__

        size += self._traverse(attributes)
        return size + 1
    
    def _ModuleElementType(self, obj, obj_type, obj_id, name=None):
        if name is None:
            name = obj.__name__

        modulename = getattr(obj, "__module__", None)
        if modulename is None:
            modulename = pickle.whichmodule(obj, name)

        try:
            __import__(modulename)
            module = sys.modules[modulename]
            same_as_obj = getattr(module, name)
        except (ImportError, KeyError, AttributeError):
            raise pickle.PicklingError(
                "Can't pickle %r: it's not found as %s.%s" %
                (obj, modulename, name))
        else:
            if same_as_obj is not obj:
                raise pickle.PicklingError(
                    "Can't pickle %r: it's not the same object as %s.%s" %
                    (obj, modulename, name))

        code = copy_reg._extension_registry.get((modulename, name))
        if code:
            assert code > 0
            if code <= 0xFF:
                size = 2
            elif code <= 0xFFFF:
                size = 3
            else:
                size = 5
        else:
            size = 3 + len(modulename) + len(name)
            size += self._memorize(obj_id)

        return size
    
    def _PlaceHolderType(self, obj, obj_type, obj_id):
        return obj.size
    
    def _Generic(self, obj, obj_type, obj_id):
        
        reducer = copy_reg.dispatch_table.get(obj_type)
        if reducer:
            reduced_obj = reducer(obj)
        else:
            try:
                ismetaclass = issubclass(obj_type, types.TypeType)
            except TypeError:
                ismetaclass = False
            if ismetaclass:
                return self._ModuleElementType(obj, obj_type, obj_id)

            reducer = getattr(obj, "__reduce_ex__", None)
            if reducer:
                reduced_obj = reducer(self._protocol)
            else:
                reducer = getattr(obj, "__reduce__", None)
                if reducer:
                    reduced_obj = reducer()
                else:
                    raise pickle.PicklingError("Can't pickle %r object: %r" %
                                        (obj_type.__name__, obj))

        if isinstance(reduced_obj, basestring):
            return self._ModuleElementType(obj, obj_type, obj_id, name=reduced_obj)

        if type(reduced_obj) is not types.TupleType:
            raise pickle.PicklingError("%s must return string or tuple" % reduce)

        l = len(reduced_obj)
        if not (2 <= l <= 5):
            raise pickle.PicklingError("Tuple returned by %s must have "
                                "two to five elements" % reduce)


        return self.save_reduce(obj=obj, *reduced_obj)
        
    def save_reduce(self, factory_function, args, state=None,
                    listitems=None, dictitems=None, obj=None):

        if not isinstance(args, types.TupleType):
            raise pickle.PicklingError("args from reduce() should be a tuple")

        if not hasattr(factory_function, '__call__'):
            raise pickle.PicklingError("func from reduce should be callable")

        if getattr(factory_function, "__name__", "") == "__newobj__":
            
            cls = args[0]
            if not hasattr(cls, "__new__"):
                raise pickle.PicklingError(
                    "args[0] from __newobj__ args has no __new__")
            if obj is not None and cls is not obj.__class__:
                raise pickle.PicklingError(
                    "args[0] from __newobj__ args has the wrong class")
            args = args[1:]
            
            size = 1
            size += self._traverse(cls)
            size += self._traverse(args)
        else:
            size = 1
            size += self._traverse(factory_function)
            size += self._traverse(args)

        if obj is not None:
            size += self._memorize(id(obj))

        if listitems is not None:
            for e in listitems:
                size += self._traverse(e)
            size += self._batch_append_overhead(len(listitems))

        if dictitems is not None:
            for k,v in dictitems.iteritems():
                size += self._traverse(k)
                size += self._traverse(v)
            size += self._batch_append_overhead(len(dictitems))

        if state is not None:
            size += self._traverse(state)
            size += 1
            
        return size

    _handlers = {
        types.NoneType:1,
        types.TypeType:_ModuleElementType,
        types.BooleanType:1,
        types.IntType:_IntType,
        types.LongType:_LongType,
        types.FloatType:9,
        types.StringType:_StringType,
        types.UnicodeType:_UnicodeType,
        types.TupleType:_TupleType,
        types.ListType:_ListType,
        types.DictType:_DictType,
        types.FunctionType:_ModuleElementType,
        types.ClassType:_ModuleElementType,
        types.InstanceType:_InstanceType,
        types.BuiltinFunctionType:_ModuleElementType,
        PlaceHolder:_PlaceHolderType
    }
    

def picklesize(obj, protocol=0):
    return PickleSize().picklesize(obj, protocol)


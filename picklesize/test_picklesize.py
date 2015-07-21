'''
Created on 20.07.2015

@author: stefan
'''
import unittest
import pickle
import picklesize
import copy_reg


class TestEstimator(unittest.TestCase):
    
    def setUp(self):
        self.target = picklesize.PickleSize()

    def compare(self, obj):
        data = pickle.dumps(obj, protocol=pickle.HIGHEST_PROTOCOL)
        expected = len(data)
        
        actual = self.target.picklesize(obj, pickle.HIGHEST_PROTOCOL)
        
        self.assertEqual(expected, actual, "Wrong estimate (%s instead of %s) for %r." % 
                         (actual, expected, obj))

    def test_None(self):
        self.compare(None)

    def test_True(self):
        self.compare(True)
        
    def test_False(self):
        self.compare(False)
        
    def test_int(self):
        self.compare(0)
        self.compare(1)
        
        self.compare(0xFF-1)
        self.compare(0xFF)
        self.compare(0xFF+1)
        
        self.compare(0xFFFF-1)
        self.compare(0xFFFF)
        self.compare(0xFFFF+1)
        
        self.compare(-0xFF-1)
        self.compare(-0xFF)
        self.compare(-0xFF+1)
        self.compare(-0xFFFF-1)
        self.compare(-0xFFFF)
        self.compare(-0xFFFF+1)
        
    def test_long(self):
        self.compare(0L)
        self.compare(1L)
        self.compare(10L**100)
        self.compare(10L**1000)
        
    def test_float(self):
        self.compare(0.0)
        self.compare(-42.42)
        
    def test_string(self):
        self.compare("")
        self.compare(255*"x")
        self.compare(256*"x")
        self.compare(257*"x")
        
    def test_unicode(self):
        self.compare(u"")
        self.compare(255*u"x")
        self.compare(256*u"x")
        self.compare(257*u"x")
        
    def test_tuple(self):
        self.compare(tuple())
        self.compare((1,))
        self.compare((1,2))
        self.compare((1,2,3))
        self.compare((1,2,3,4))

    def test_list(self):
        self.compare([])
        self.compare([1])
        self.compare(999*[1])
        self.compare(1000*[1])
        self.compare(1001*[1])
        self.compare(1002*[1])
        self.compare(5412*[1])
        
    def test_dict(self):
        self.compare({})
        self.compare({1:2})
        self.compare({1:1, 2:2})

    def test_instance(self):
        self.compare(OldStyle_WithAttribs())
        self.compare(OldStyle_WithInit())

    def test_Type(self):
        self.compare(long)
        self.compare(OldStyle_WithAttribs)
        self.compare(global_function)
        self.compare(max)
        
    def test_Ref(self):
        x = "abc"
        self.compare([x,x])
        
    def test_Reducer(self):
        self.compare(NewStyle_Reducer())
        
    def test_NewStyleInstance(self):
        self.compare(NewStyle_WithAttribs())
        
    def test_numpy(self):
        import numpy as np
        
        self.compare(np.ones((10,10)))
        self.compare(np.ones((10,10))[0:5,:])
        self.compare(np.ones((10,10))[:,0:5])

    def test_numpy_multiple_arrays(self):
        import numpy as np
        self.compare([np.ones((10,10)), np.ones((10,10))])

class OldStyle_WithAttribs():
    def __init__(self):
        self.a = 12
        self.b = 42

class OldStyle_WithInit():
    def __getinitargs__(self):
        return (1,2,3)
    
class NewStyle_Reducer(object):
    pass

class NewStyle_WithAttribs(object):
    def __init__(self):
        self.a = 12
        self.b = 42

def tuple_reducer(obj):
    return (NewStyle_Reducer, tuple())

copy_reg.pickle(NewStyle_Reducer, tuple_reducer)

def global_function():
    pass
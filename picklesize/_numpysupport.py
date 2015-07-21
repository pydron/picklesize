import _picklesize

try:
    import numpy.core.multiarray
    

    def estimate_ndarray(obj, est):
        
        # During pickle, the actual data will be stored in a string of
        # `n` bytes.
        n = obj.nbytes
        
        # The size of this string depends on how pickle encodes the length
        if n <= 0xFF:
            size = 2 + n
        else:
            size = 5 + n
        # We assume that the string would be unique. This is quite likely
        # Since numpy probably creates it on the fly.
        dummy = object()
        size += est._memorize(dummy, id(dummy))
        
        placeholder = _picklesize.PlaceHolder(size)
        
        reconstruct = numpy.core.multiarray._reconstruct
        
        # This is almost identical to::
        #   zero_tuple = (0, )
        # With one difference, python 2.7.? is smart enough to see that
        # (0, ) is constant and will therefore only create one instance
        # for this function and use that one for every call. But we want this
        # tuple to have a different `id` every time because numpy's reducer
        # is also returning a unique instance every time. The difference
        # is only three bytes, but we might as well do it right.
        # This code is sufficiently complicated to stop the compiler
        # from seeing it as a constant.
        zero_tuple = ((lambda:0)(), )
        
        args = (numpy.ndarray, zero_tuple, 'b')
        state = (1, obj.shape, obj.dtype, numpy.isfortran(obj), placeholder)

        size = est.save_reduce(reconstruct, args, state=state, obj=obj)
        return size
    
    # Register
    _picklesize.custom_estimators[numpy.ndarray] = estimate_ndarray

    
except ImportError:
    pass






__all__ = []
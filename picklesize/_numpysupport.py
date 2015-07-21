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
        size += est._memorize(id(object()))
        
        placeholder = _picklesize.PlaceHolder(size)
        
        reconstruct = numpy.core.multiarray._reconstruct
        args = (numpy.ndarray, (0,), 'b')
        state = (1, obj.shape, obj.dtype, numpy.isfortran(obj), placeholder)
        
        return est.save_reduce(reconstruct, args, state=state, obj=obj)
    
    # Register
    _picklesize.custom_estimators[numpy.ndarray] = estimate_ndarray

    
except ImportError:
    pass






__all__ = []
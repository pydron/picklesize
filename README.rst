

picklesize - Calculates the pickled size of an object
=============================================================

Sometimes it is handy to know how much space an object will need when it
will be serialized with `pickle` without actually pickling it. Especially
when the object is large, pickling can be slow and memory consuming.

This library can calculate the exact space requirement without actually
pickling it. It still has to make a pass through the object tree, which
takes time, especially with many small objects. The major advantage is that
it won't take significant memory. 

`picklesize` has special support for `numpy` arrays to calculate the
size without the `array`->`str`->`file` procedure of regular pickling that
requires at least two copy operations.

-----
Usage
-----

The API is kept similar to the one of `pickle`::

	import picklesize
	nbytes = picklesize.picklesize(obj, protocol=pickle.HIGHEST_PROTOCOL)
	
Currently only protocol `2` (better known as `pickle.HIGHEST_PROTOCOL` )
is supported.

-----------------------------------
Bug Reports and other contributions
-----------------------------------

This project is hosted here `picklesize github page
<https://github.com/smurn/picklesize>`_.
 



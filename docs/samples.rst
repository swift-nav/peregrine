==========================================
Sample data handling (`peregrine.samples`)
==========================================

.. currentmodule:: peregrine

The `peregrine.samples` module provides functions for handling sample data
files. Currently only binary sample data stored as an 8-bit signed integer
array is supported.

Samples data files
==================

Saving samples
--------------

Samples can be saved to a file using the :func:`samples.save_samples` function. Its usage is best illustrated by an example:

.. ipython::

  In [21]: import numpy as np

  In [22]: import peregrine.samples

  In [23]: samples = np.arange(-7, 8)

  In [24]: samples
  Out[24]: array([-7, -6, -5, -4, -3, -2, -1,  0,  1,  2,  3,  4,  5,  6,  7])

  In [26]: len(samples)
  Out[26]: 15

  In [25]: peregrine.samples.save_samples("samples_file", samples)

Loading samples
---------------

Samples can be loaded from a file using the :func:`samples.load_samples` function.

By default the whole file is read in:

.. ipython::

  In [28]: peregrine.samples.load_samples("samples_file")
  Out[28]: array([-7, -6, -5, -4, -3, -2, -1,  0,  1,  2,  3,  4,  5,  6,  7], dtype=int8)

Or an explicit number of samples can be specified. When an explicit number is
specified, `load_samples` will always return that number of samples or if that
number of samples cannot be read then an exception will be raised:

.. ipython::

  In [29]: peregrine.samples.load_samples("samples_file", 10)
  Out[29]: array([-7, -6, -5, -4, -3, -2, -1,  0,  1,  2], dtype=int8)

  @verbatim
  In [30]: peregrine.samples.load_samples("samples_file", 16)
  ---------------------------------------------------------------------------
  EOFError                                  Traceback (most recent call last)
    ...
  EOFError: Failed to read 16 samples from file 'samples_file'

A number of samples at the beginning of the file can be discarded using the
`num_skip` parameter:

.. ipython::

  In [32]: peregrine.samples.load_samples("samples_file", -1, 5)
  Out[32]: array([-2, -1,  0,  1,  2,  3,  4,  5,  6,  7], dtype=int8)

  In [33]: peregrine.samples.load_samples("samples_file", 5, 5)
  Out[33]: array([-2, -1,  0,  1,  2], dtype=int8)


Reference / API
===============

peregrine.samples Module
------------------------

.. automodule:: peregrine.samples

  .. autosummary:: save_samples
  .. autosummary:: load_samples

  .. rubric:: Functions

  .. autofunction:: save_samples

  .. autofunction:: load_samples


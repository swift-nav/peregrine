
================================================
Interactive usage (:mod:`peregrine.interactive`)
================================================

In addition to being a stand-alone tool, Peregrine is designed with interactive use in mind. Working from an interactive session such as `IPython <http://ipython.org/>`_ provides a great environment for exploring GNSS data sets and rapidly prototyping new algorithms.

We particularly recommend using the `IPython notebook frontend <http://ipython.org/ipython-doc/dev/interactive/htmlnotebook.html>`_ with pylab::

  ipython notebook --pylab inline

Peregrine functions and classes are arranged within a heirarchy of modules and
submodules grouping similar functionality together. This provides a logical
structure when writing scripts but when working interactively it is more
convenient to have all the commonly used functions available from within the
same namespace, such that they can all be imported together.

The :mod:`peregrine.interactive` module provides this unified namespace and
also configures the python :mod:`logging` module (which is used for reporting
throughout the library) for output into the interactive session.

.. note::
  Throughout this documentation there are many examples which take the form of
  an interactive session. In these examples we will always use the explicit
  full module path for clarity. Of course, you can save yourself some typing by
  using the :mod:`peregrine.interactive` namespace instead.

.. note::
  The :mod:`peregrine.interactive` namespace is intended as a convenience for
  use in interactive sessions, if you are writing a script it is recommended
  that you use full module paths.

peregrine.interactive Module
----------------------------

.. automodule:: peregrine.interactive


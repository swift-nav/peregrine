# Copyright (C) 2012 Swift Navigation Inc.
#
# This source is subject to the license found in the file 'LICENSE' which must
# be be distributed together with this source. All other rights reserved.
#
# THIS CODE AND INFORMATION IS PROVIDED "AS IS" WITHOUT WARRANTY OF ANY KIND,
# EITHER EXPRESSED OR IMPLIED, INCLUDING BUT NOT LIMITED TO THE IMPLIED
# WARRANTIES OF MERCHANTABILITY AND/OR FITNESS FOR A PARTICULAR PURPOSE.

"""
The :mod:`peregrine.interactive` module sets up a default logging configuration
and imports the most commonly used Peregrine functions and classes into one
namespace. This is designed to provide a convenient environment for use in
interactive sessions such as from within `IPython <http://ipython.org/>`_.

It is designed to be star imported as follows::

  from peregrine.interactive import *

:mod:`peregrine.interactive` Functions
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

:mod:`peregrine.interactive` defines the following functions:

.. currentmodule:: peregrine.interactive

.. autosummary:: configure_logging

Included Functions
^^^^^^^^^^^^^^^^^^

The following classes, functions and attributes from other modules are
available in the interactive namespace:

"""

def configure_logging():
  """ Configure python :mod:`logging` for use in an interactive session."""
  import logging
  logging.basicConfig(
    level=logging.DEBUG,
    format="\033[2K\r%(asctime)s [%(levelname)s] %(name)s: %(message)s"
  )
configure_logging()

from peregrine.acquisition import *
from peregrine.samples import *
from peregrine.include.generateCAcode import caCodes
from peregrine.analysis.acquisition import *
from peregrine.analysis.samples import *

# Some may find this to be in very bad taste but we are going to alter our own
# docstring to automatically provide a summary of the functions and classes
# available in the interactive namespace.

# First find all the local variables (including functions, classes etc.) that
# have a module starting with 'peregrine', i.e. they are part of our library.
l = dict(locals())
peregrine_items = {}
for k, v in l.iteritems():
  if hasattr(v, '__module__'):
    if v.__module__.startswith('peregrine'):
      if not v.__module__ in peregrine_items:
        peregrine_items[v.__module__] = []
      peregrine_items[v.__module__] += [k]
# Remove items defined here in interactive, we will document them explicitly in
# the docstring.
del peregrine_items['peregrine.interactive']
# Now add autosummaries to our docstring grouping items from the same module
# together.
for mod in sorted(peregrine_items.iterkeys()):
  __doc__ += ".. currentmodule:: %s\n\n" % mod
  __doc__ += ".. rubric:: Included from :mod:`%s`:\n\n" % mod
  for name in sorted(peregrine_items[mod]):
    __doc__ += ".. autosummary:: %s\n\n" % name

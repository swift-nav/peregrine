# Copyright (C) 2012 Swift Navigation Inc.
#
# This source is subject to the license found in the file 'LICENSE' which must
# be be distributed together with this source. All other rights reserved.
#
# THIS CODE AND INFORMATION IS PROVIDED "AS IS" WITHOUT WARRANTY OF ANY KIND,
# EITHER EXPRESSED OR IMPLIED, INCLUDING BUT NOT LIMITED TO THE IMPLIED
# WARRANTIES OF MERCHANTABILITY AND/OR FITNESS FOR A PARTICULAR PURPOSE.

"""
Peregrine makes extensive use of the python :mod:`logging` module. This module
contains convenience functions for configuring the :mod:`logging` module for
various common use scenarios.

"""

import sys
import logging

def default_logging_config():
  """
  Setup default :mod:`logging` configuration.

  A verbose setup outputting all messages including the ``logging.DEBUG`` level
  to ``stdout``.

  """
  # Configure logging.
  # Note: An ANSI escape sequence is used to clear the line in case a
  # progressbar is running but this won't work in Windows.
  logging.basicConfig(
    level=logging.DEBUG,
    stream=sys.stdout,
    format="\033[2K\r %(asctime)s [%(levelname)s] %(name)s: %(message)s"
  )

def docs_logging_config():
  """
  Setup :mod:`logging` configuration for use in the documentation.

  For use from within IPython examples in the Sphinx doccumentation. Outputs to
  ``stdout`` with a simpler format string that doesn't include the time or
  date.

  This function removes all the existing root handlers before adding its own.

  .. note::
    Sphinx IPython mode redirects ``sys.stdout`` at some point after modules
    are loaded. You should call this function after the redirection has
    occurred otherwise logging output will still end up in the console, not the
    documentation.

  This function can be called from within a documentation IPython example as
  follows::

    .. ipython::

      @suppress
      In [22]: import peregrine.log; peregrine.log.docs_logging_config()

  """
  # Remove any existing handlers.
  if len(logging.root.handlers) != 0:
    for handler in logging.root.handlers:
      logging.root.removeHandler(handler)

  # Setup our new configuration.
  logging.basicConfig(
    level=logging.DEBUG,
    stream=sys.stdout,
    format="[%(levelname)s] %(name)s: %(message)s"
  )


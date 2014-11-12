#!/usr/bin/env python

"""
============
Installation
============

Requirements
============

Peregrine makes use of the following packages:

- `Python <http://www.python.org/>`_ 2.6 or 2.7

- `Numpy <http://www.numpy.org/>`_ 1.6 or later

- `FFTW3 <http://www.fftw.org/>`_

- `pyFFTW <http://pypi.python.org/pypi/pyFFTW>`_ 0.8.2 or later

- [Optional] `progressbar <http://code.google.com/p/python-progressbar/>`_ to 
  display a progress indication in the terminal whilst running.

- [Optional] `matplotlib <http://matplotlib.org/>`_ to support generation 
  of plots.

On Ubuntu these can be installed from the repositories::

    $ sudo apt-get install python-numpy python-fftw python-matplotlib 
    libfftw3-dev

    $ pip install git+https://github.com/fnoble/python-progressbar.git

Additionally, Peregrine depends on the libswiftnav libraries and Python
bindings, see each the packages for installation instructions:

- `libswiftnav <https://github.com/swift-nav/libswiftnav>`_

- `libswiftnav-python <https://github.com/swift-nav/libswiftnav-python>`_

.. note::
  Peregrine makes use of some extensions to the progressbar library that are
  not yet merged upstream. For now you can install our `development version
  <https://github.com/fnoble/python-progressbar/>`_ as follows::

    $ pip install git+https://github.com/fnoble/python-progressbar.git

Installing Peregrine
====================

Obtaining the source
--------------------

The peregrine source and release tarballs are available from GitHub,
https://github.com/swift-nav/peregrine.

The latest development version of peregrine can be cloned from GitHub
using this command::

   $ git clone git://github.com/swift-nav/peregrine.git

Building and Installing
-----------------------

.. note::
  `pyFFTW <http://pypi.python.org/pypi/pyFFTW>`_ requires `FFTW3
  <http://www.fftw.org/>`_ which should be available through your operating
  system package manager. For Mac OS X we recommend using `Homebrew
  <http://mxcl.github.com/homebrew/>`_.

.. note::
  Installation requires `Distribute <http://pypi.python.org/pypi/distribute>`_,
  if your python installation doesn't provide this it will automatically be
  installed.

To install Peregrine (from the root of the source tree)::

    $ python setup.py install

This will download and install any required python modules from `PyPI
<http://pypi.python.org/>`_.

Building documentation
----------------------

.. note::
    The latest version of Peregrine's documentation should be available online
    at http://docs.swift-nav.com/peregrine.

Building the documentation requires the Peregrine source code and some
additional packages:

    - `Sphinx <http://sphinx.pocoo.org>`_ (and its dependencies) 1.0 or later
    - `numpydoc <http://pypi.python.org/pypi/numpydoc>`_ 0.4 or later
    - `matplotlib <http://matplotlib.org/>`_ 1.1 or later
    - `ipython <http://ipython.org/>`_ 0.13.1 or later

These packages can be installed on Ubuntu 12.04 or later::

    $ sudo apt-get install python-sphinx python-matplotlib ipython
    $ sudo pip install numpydoc

To build the Peregrine documentation, execute the following commands::

    $ cd docs
    $ make html

The documentation will be built in the ``docs/_build/html`` directory, and can
be read by pointing a web browser to ``docs/_build/html/index.html``.

"""

from version import get_git_version

setup_args = dict(
  name = 'Peregrine',
  version = get_git_version(),
  description = 'Peregrine software GNSS receiver',
  license = 'GPLv3',
  url = 'http://www.swift-nav.com',

  author = 'Swift Navigation Inc.',
  maintainer = 'Fergus Noble',
  maintainer_email = 'fergus@swift-nav.com',

  packages = [
    'peregrine',
    'peregrine.include',
    'peregrine.analysis'
  ],

  entry_points = {
    'console_scripts': [
      'peregrine = peregrine.run:main',
      'peregrine-analyze-samples = peregrine.analysis.samples:main',
      'peregrine-show-acq = peregrine.analysis.acquisition:main',
    ]
  },

  install_requires = [
    'swiftnav',
    'pyFFTW >= 0.8.2',
    'numpy >= 1.6',
  ],
  extras_require = {
    'progress': ['progressbar >= 2.3'],
    'plot': ['matplotlib >= 1.1'],
  }
)

if __name__ == "__main__":
  # Bootstrap Distribute if the user doesn't have it
  from distribute_setup import use_setuptools
  use_setuptools()

  from setuptools import setup

  setup(**setup_args)

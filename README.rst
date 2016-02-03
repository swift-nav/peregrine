****************************************
Peregrine
****************************************


-----

|build|

-----

Peregrine is a fast and flexible open-source software GNSS receiver. It can be
used as a standalone application to post-process GNSS data all the way to PVT
solutions or as from within `IPython <http://ipython.org/>` as a toolkit for
GNSS data exploration.

Peregrine is written in `Python <http://www.python.org/>` for flexibility and
ease of development and uses the `libswiftnav` C library for speed.

Full documentation available online at http://docs.swift-nav.com/peregrine.

============
Installation
============

Requirements
============

You can automatically install dependencies using::

    $ ./deps.sh

Peregrine makes use of the following packages:

- `Python <http://www.python.org/>`_ 2.6 or 2.7

- `Numpy <http://www.numpy.org/>`_ 1.6 or later

- `FFTW3 <http://www.fftw.org/>`_

- `pyFFTW <http://pypi.python.org/pypi/pyFFTW>`_ 0.8.2 or later

Peregrine can also be used interactively with `IPython <http://ipython.org/>`_
and requires an additional two packages:

- [Optional] `progressbar <http://code.google.com/p/python-progressbar/>`_ to
  display a progress indication in the terminal whilst running.

- [Optional] `matplotlib <http://matplotlib.org/>`_ to support generation
  of plots.

On Ubuntu these can be installed from the repositories::

    $ sudo apt-get install python-numpy python-fftw python-matplotlib libfftw3-dev
    $ pip install git+https://github.com/fnoble/python-progressbar.git

.. note::

  Peregrine makes use of some extensions to the progressbar library that are
  not yet merged upstream. For now you can install our `development version
  <https://github.com/fnoble/python-progressbar/>`_ as shown in the command
  above.

Additionally, Peregrine depends on the libswiftnav libraries and Python
bindings, see each of the packages for installation instructions:

- `libswiftnav <https://github.com/swift-nav/libswiftnav>`_

Installing Peregrine
====================

Obtaining the source
--------------------

The peregrine source are available from GitHub,
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

To install Peregrine (from the root of the source tree)::

    $ python setup.py install

This will download and install any required python modules from `PyPI
<http://pypi.python.org/>`_.

Peregrine also supports a developer mode that creates a symbolic link from the
source location to the install location. This enables you to modify Peregrine
without having to `install` it every time. It can be installed by::

    $ python setup.py develop


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
    - `Latex <https://www.tug.org/texlive/>`_
    - `dvipng <http://www.ctan.org/pkg/dvipng>`_ 1.14 or later

These packages can be installed on Ubuntu 12.04 or later::

    $ sudo apt-get install python-sphinx python-matplotlib ipython texlive-full dvipng
    $ sudo pip install numpydoc

To build the Peregrine documentation, execute the following commands::

    $ cd docs
    $ make html

The documentation will be built in the ``docs/_build/html`` directory, and can
be read by pointing a web browser to ``docs/_build/html/index.html``.

.. |build| image:: https://img.shields.io/travis/swift-nav/peregrine/master.svg?style=flat-square&label=build
    :target: https://travis-ci.org/swift-nav/peregrine/
    :alt: Build status of the master branch on Unix

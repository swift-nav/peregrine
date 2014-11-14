==========================================
Acquisition (:mod:`peregrine.acquisition`)
==========================================

.. currentmodule:: peregrine.acquisition

The :mod:`peregrine.acquisition` module provides functions and classes related to GNSS satellite acquisition. It is accompanied by the :mod:`peregrine.analysis.acquisition` module which provides functions for tabulating, plotting and analysing acquisition results.


Basic Acquisition
=================

The core of the :mod:`peregrine.acquisition` module is the :class:`Acquisition`
class. This class is instanitated with a set of samples and a few parameters
such as the sampling rate. It then pre-computes a number of intermediate
quantities that will later be used in acquisition. The :class:`Acquisition`
class then exposes a number of methods that are used to perform an acquisition.

In the following example we load some sample data from a file and initialise an
:class:`Acquisition` object. In this example our sample data has a sampling
frequency of 16.368 MHz, has an intermediate frequency of 4.092 MHz and there
are 16,368 samples per code (we are working with the GPS C/A code which has a
length of 1,023 chips at a chipping rate of 1.023 MHz).

.. ipython::

  In [1]: import peregrine.acquisition

  In [1]: import peregrine.samples

  In [2]: import peregrine.analysis.acquisition

  In [2]: samps = peregrine.samples.load_samples("../tests/test_samples.dat")

  In [2]: acq = peregrine.acquisition.Acquisition(samps, 16.368e6, 4.092e6, 16368)

We will now perform a basic two stage acquisition using the default parameters using the :meth:`Acquisition.acquisition` method.

.. ipython::

  @suppress
  In [2]: import peregrine.log; peregrine.log.docs_logging_config()

  In [2]: res = acq.acquisition(show_progress=False); res

The :meth:`Acquisition.acquisition` method returns a list of
:class:`AcquisitionResult` objects, one for each of the PRNs attempted.

If the acquisition Signal to Noise Ratio (SNR) was greater than a given
threshold then the satellite is considered acquired and a finer grained search
is performed in carrier frequency space to refine the estimate of the
satellite's Doppler shift frequency. The status of the
:class:`AcquisitionResult` object is updated to indicate that the satellite was
successfully acquired.

The frequencies and PRNs that are included in the acquisition search can be
customised with optional parameters to the :meth:`Acquisition.acquisition`
method. See the method documentation for details.

Now using the :func:`peregrine.analysis.acquisition.acq_table` and
:func:`peregrine.analysis.acquisition.snr_bars` functions we can visualise the
results of the acquisition.

.. ipython::

  In [13]: peregrine.analysis.acquisition.acq_table(res)

  @savefig acq_analysis_snr_bars.png width=75% align=center
  In [13]: peregrine.analysis.acquisition.snr_bars(res);


Acquisition results files
=========================

Acquisition results can be saved and loaded from a file using the
:func:`load_acq_results` and :func:`save_acq_results` functions.

.. ipython::

  In [22]: peregrine.acquisition.save_acq_results("foo.acq_results", res)

  In [22]: res2 = peregrine.acquisition.load_acq_results("foo.acq_results")

  In [13]: peregrine.analysis.acquisition.acq_table(res2)


Command-line utility
====================

A command-line utility is provided to display the contents of an acquisition
results file using the functions from the :mod:`peregrine.analysis.acquisition`
module. This command prints an acquisition table using
:func:`peregrine.analysis.acquisition.acq_table` and plots the acquisition SNRs
using :func:`peregrine.analysis.acquisition.snr_bars`.

The command is used as follows::

  $ peregrine-show-acq path/to/file.acq_results

More usage information can be found by running::

  $ peregrine-show-acq --help


Advanced Acquisition
====================

Some users may want finer grained control over the acquisition process, in
which case the :class:`Acquisition` class provides lower level methods that are
used internally by :meth:`Acquisition.acquisition`.

The :meth:`Acquisition.acquire` method performs an acquisition with a single
code over a range of carrier frequencies and code phases and returns an array
of the correlation powers at each point.

.. ipython::

  In [22]: import numpy as np

  In [22]: from peregrine.include.generateCAcode import caCodes

  In [22]: freqs = np.arange(-7000, 7000, 500) # Doppler shifts

  In [22]: powers = acq.acquire(caCodes[14], freqs + acq.IF); powers # PRN 15

The :mod:`peregrine.analysis.acquisition` module also has functions for
visualising the results of :meth:`Acquisition.acquire`.

.. ipython::

  @savefig acq_analysis_acq_plot_3d.png width=75% align=center
  In [22]: peregrine.analysis.acquisition.acq_plot_3d(powers, freqs, 16368)

.. ipython::

  @savefig acq_analysis_peak_plot.png width=75% align=center
  In [22]: peregrine.analysis.acquisition.peak_plot(powers, freqs, 16368)

The peak location and Signal to Noise ratio can be estimated using the
:meth:`Acquisition.find_peak` method.

.. ipython::

  In [22]: code_phase, doppler, snr = acq.find_peak(freqs, powers)

  In [22]: (code_phase, doppler, snr)

The :meth:`Acquisition.acquire` method uses a code phase parallel search over a
list of frequencies and therefore is able to determine the code phase precisely
(to within one sample). Because only a short segment of data is used the
frequency resolution achievable is low and it is not an efficient way to search
over many carrier frequencies.

The :meth:`Acquisition.interpolate` method is provided to refine the carrier
frequency estimate of an acquisition performed using
:meth:`Acquisition.acquire` using an interpolation based method. It performs 
the search at a given code phase so the code phase must first be found using
:meth:`Acquisition.acquire`.

Reference / API
===============

:mod:`peregrine.acquisition` Module
-----------------------------------

.. automodule:: peregrine.acquisition

  .. rubric:: Classes

  .. autosummary::
    :toctree: api

    Acquisition
    AcquisitionResult

  .. rubric:: Functions

  .. autosummary::
    :toctree: api

    load_acq_results
    save_acq_results


:mod:`peregrine.analysis.acquisition` Module
--------------------------------------------

.. automodule:: peregrine.analysis.acquisition

  .. rubric:: Functions

  .. autosummary::
    :toctree: api

    acq_table
    snr_bars
    peak_plot
    acq_plot_3d


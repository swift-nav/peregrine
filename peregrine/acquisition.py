# Copyright (C) 2012 Swift Navigation Inc.
#
# This source is subject to the license found in the file 'LICENSE' which must
# be be distributed together with this source. All other rights reserved.
#
# THIS CODE AND INFORMATION IS PROVIDED "AS IS" WITHOUT WARRANTY OF ANY KIND,
# EITHER EXPRESSED OR IMPLIED, INCLUDING BUT NOT LIMITED TO THE IMPLIED
# WARRANTIES OF MERCHANTABILITY AND/OR FITNESS FOR A PARTICULAR PURPOSE.

"""
The :mod:`peregrine.acquisition` module contains classes and functions related
to satellite acquisition.

"""

import numpy as np
import pyfftw
import cPickle

from include.generateCAcode import caCodes

import logging
logger = logging.getLogger(__name__)

DEFAULT_WISDOM_FILE = "fftw_wisdom"
"""The default filename used for FFTW wisdom files."""

DEFAULT_THRESHOLD = 20.0
"""The default correlation power to consider an acquisition successful."""

# Import progressbar if it is available.
_progressbar_available = True
try:
  import progressbar
except ImportError:
  _progressbar_available = False


class Acquisition:
  """
  Functions for performing satellite acquisitions on a set of samples.

  The :class:`Acquisition` class pre-computes and stores a number of variables
  given the sample data and its parameters so that repeated acquisitions using
  the same parameters and samples (but different codes and carrier frequencies)
  are performed as efficiently as possible.

  Parameters
  ----------
  samples : :class:`numpy.ndarray` or `None`
    Array of samples to use for acquisition. Can be `None` but in this case
    `init_samples` *must* be called with an array of samples before any other
    acquisition functions are used.
  sampling_freq : float
    The sampling frequency of the samples in Hz.
  IF : float
    The receiver intermediate frequency used when capturing the samples.
  samples_per_code : float
    The number of samples corresponding to one code length.
  code_length : int, optional
    The number of chips in the chipping code. Defaults to the GPS C/A code
    value of 1023.
  wisdom_file : string or `None`, optional
    The filename from which to load and save FFTW `Wisdom
    <http://www.fftw.org/doc/Words-of-Wisdom_002dSaving-Plans.html>`_,
    pre-calculated data about how to most efficiently perform the FFT
    operations required on the current hardware. Using FFTW wisdom greatly
    reduces the time required to perform an acquisition. If `wisdom_file` is
    `None` then no wisdom file is loaded or saved.

  """

  def __init__(self,
               samples,
               sampling_freq,
               IF,
               samples_per_code,
               code_length=1023,
               n_codes_coarse=4,
               wisdom_file=DEFAULT_WISDOM_FILE):

    self.sampling_freq = sampling_freq
    self.IF = IF
    self.samples_per_code = int(round(samples_per_code))
    self.n_coarse = n_codes_coarse * self.samples_per_code
    self.code_length = code_length
    self.samples_per_chip = float(samples_per_code) / code_length

    # Try to load saved FFTW wisdom.
    if wisdom_file is not None:
      try:
        self.load_wisdom(wisdom_file)
      except IOError:
        logger.warning("Couldn't open FFTW wisdom file, "
                       "the first run might take longer than usual.")

    if samples is not None:
      self.init_samples(samples)

    # Setup acquisition:

    # Allocate aligned arrays for the code FFT.
    self.code = pyfftw.n_byte_align_empty((self.n_coarse), 16,
                                          dtype=np.complex128)
    self.code_ft = pyfftw.n_byte_align_empty((self.n_coarse), 16,
                                             dtype=np.complex128)
    # Create an FFTW transforms which will execute the code FFT.
    self.code_fft = pyfftw.FFTW(self.code, self.code_ft)

    # Allocate aligned arrays for the inverse FFT.
    self.corr_ft1 = pyfftw.n_byte_align_empty((self.n_coarse), 16,
                                              dtype=np.complex128)
    self.corr1 = pyfftw.n_byte_align_empty((self.n_coarse), 16,
                                           dtype=np.complex128)
    self.corr_ft2 = pyfftw.n_byte_align_empty((self.n_coarse), 16,
                                              dtype=np.complex128)
    self.corr2 = pyfftw.n_byte_align_empty((self.n_coarse), 16,
                                           dtype=np.complex128)

    # Setup FFTW transforms for inverse FFT.
    self.corr_ifft1 = pyfftw.FFTW(self.corr_ft1, self.corr1,
                                  direction='FFTW_BACKWARD')
    self.corr_ifft2 = pyfftw.FFTW(self.corr_ft2, self.corr2,
                                  direction='FFTW_BACKWARD')

    # Save FFTW wisdom for later
    if wisdom_file is not None:
      self.save_wisdom(wisdom_file)

  def init_samples(self, samples):
    """
    Update the samples used for acquisition.

    This function pre-calculates some values that are used later in
    acquisition. This function can be called to replace the samples used for
    acquisition with another set having the same sampling frequency, IF etc.

    .. warning: If no samples were provided when the class was instantiated
                then this method *must* be called before calling any other
                acquisition functions.

    Parameters
    ----------
    samples : :class:`numpy.ndarray`
      Array of samples to use for acquisition.

    """
    self.samples = samples

    # Create two short sets of data to correlate with
    self.short_samples1 = samples[0:self.n_coarse]
    self.short_samples2 = samples[self.n_coarse:2*self.n_coarse]

    # Pre-compute Fourier transforms of the two short signals
    self.short_samples1_ft = np.fft.fft(self.short_samples1)
    self.short_samples2_ft = np.fft.fft(self.short_samples2)

  def interpolate(self, S_0, S_1, S_2, interpolation='gaussian'):
    """
    Use interpolation to refine an FFT frequency estimate.

    .. image:: /_static/interpolation_diagram.png
      :align: center
      :alt: Interpolation diagram

    For an FFT bin spacing of :math:`\delta f`, the input frequency is
    estimated as:

    .. math:: f_{in} \\approx \delta f (k + \Delta)

    Where :math:`k` is the FFT bin with the maximum magnitude and
    :math:`\Delta \in [-\\frac{1}{2}, \\frac{1}{2}]` is a correction found by
    interpolation.

    **Parabolic interpolation:**

    .. math:: \Delta = \\frac{1}{2} \\frac{S[k+1] - S[k-1]}{2S[k] - S[k-1] - S[k+1]}

    Where :math:`S[n]` is the magnitude of FFT bin :math:`n`.

    **Gaussian interpolation:**

    .. math:: \Delta = \\frac{1}{2} \\frac{\ln(S[k+1]) - \ln(S[k-1])}{2\ln(S[k]) - \ln(S[k-1]) - \ln(S[k+1])}

    The Gaussian interpolation method gives better results, especially when
    used with a Gaussian window function, at the expense of computational
    complexity. See [1]_ for detailed comparison.


    Parameters
    ----------
    S_0 : float
      :math:`S[k-1]`, i.e. the magnitude of FFT bin one before the maxima.
    S_1 : float
      :math:`S[k]` i.e. the magnitude of the maximum FFT.
    S_2 : float
      :math:`S[k+1]`, i.e. the magnitude of FFT bin one after the maxima.

    Returns
    -------
    out : float
      The fractional number of FFT bins :math:`\Delta` that the interpolated
      maximum is from the maximum point :math:`S[k]`.

    References
    ----------

    .. [1] Gasior, M. et al., "Improving FFT frequency measurement resolution
       by parabolic and Gaussian spectrum interpolation" AIP Conf.Proc. 732
       (2004) 276-285 `CERN-AB-2004-023-BDI
       <http://cdsweb.cern.ch/record/738182>`_

    """
    if interpolation == 'parabolic':
      # Parabolic interpolation.
      return 0.5 * (S_2 - S_0) / (2*S_1 - S_0 - S_2)
    elif interpolation == 'gaussian':
      # Gaussian interpolation.
      ln_S_0 = np.log(S_0)
      ln_S_1 = np.log(S_1)
      ln_S_2 = np.log(S_2)
      return 0.5 * (ln_S_2 - ln_S_0) / (2*ln_S_1 - ln_S_0 - ln_S_2)
    elif interpolation == 'none':
      return 0
    else:
      raise ValueError("Unknown interpolation mode '%s'", interpolation)

  def acquire(self, code, freqs, progress_callback=None):
    """
    Perform an acquisition with a given code.

    Perform a code-phase parallel acquisition with a given code over a set of
    carrier frequencies.

    Parameters
    ----------
    code : :class:`numpy.ndarray`, shape(`code_length`,)
      A numpy array containing the code to acquire. Should contain one element
      per chip with value +/- 1.
    freqs : iterable
      A list of carrier frequencies in Hz to search over.
    progress_callback : callable or `None`, optional
      A function that is called to report on the progress of the acquisition.
      Can be `None`. The function should have the following signature::

        progress_callback(current_step_number, total_number_of_steps)

    Returns
    -------
    out : :class:`numpy.ndarray`, shape(len(`freqs`), `samples_per_code`)
      2D array containing correlation powers at different frequencies and code
      phases. Code phase axis is in samples from zero to `samples_per_code`.

    """
    # Allocate array to hold results.
    results = np.empty((len(freqs), self.samples_per_code))

    # Upsample the code to our sampling frequency.
    code_indicies = np.arange(1.0, self.n_coarse + 1.0) / \
                    self.samples_per_chip
    code_indicies = np.remainder(np.asarray(code_indicies, np.int), self.code_length)
    self.code[:] = code[code_indicies]

    # Find the conjugate Fourier transform of the code which will be used to
    # perform the correlation.
    self.code_fft.execute()
    code_ft_conj = np.conj(self.code_ft)

    for n, freq in enumerate(freqs):
      # Report on our progress
      if progress_callback:
        progress_callback(n + 1, len(freqs))

      # Shift the signal in the frequency domain to remove the carrier
      # i.e. mix down to baseband.
      shift = int(float(freq) * len(self.short_samples1_ft) /
                  self.sampling_freq)
      short_samples1_ft_bb = np.append(self.short_samples1_ft[shift:],
                                       self.short_samples1_ft[:shift])
      short_samples2_ft_bb = np.append(self.short_samples2_ft[shift:],
                                       self.short_samples2_ft[:shift])

      # Multiplication in frequency <-> correlation in time.
      self.corr_ft1[:] = short_samples1_ft_bb * code_ft_conj
      self.corr_ft2[:] = short_samples2_ft_bb * code_ft_conj

      # Perform inverse Fourier transform to obtain correlation results.
      self.corr_ifft1.execute()
      self.corr_ifft2.execute()

      # Find the correlation amplitude.
      acq_mag1 = np.abs(self.corr1[:self.samples_per_code])
      acq_mag2 = np.abs(self.corr2[:self.samples_per_code])

      # Use the signal with the largest correlation peak as the result as one
      # of the signals may contain a nav bit edge. Square the result to find
      # the correlation power.
      if (np.max(acq_mag1) > np.max(acq_mag2)):
        results[n] = np.square(acq_mag1)
      else:
        results[n] = np.square(acq_mag2)

    return results

  def find_peak(self, freqs, results, interpolation='gaussian'):
    """
    Find the peak within an set of acquisition results.

    Finds the point in the acquisition results array with the greatest
    correlation power and determines the code phase and carrier frequency
    corresponding to that point. The Signal-to-Noise Ratio (SNR) of the peak is
    also estimated.

    Parameters
    ----------
    freqs : iterable
      List of frequencies mapping the results frequency index to a value in Hz.
    results : :class:`numpy.ndarray`, shape(len(`freqs`), `samples_per_code`)
      2D array containing correlation powers at different frequencies and code
      phases. Code phase axis is in samples from zero to `samples_per_code`.

    Returns
    -------
    out : (float, float, float)
      | The tuple
      |   `(code_phase, carrier_freq, SNR)`
      | Where `code_phase` is in chips, `carrier_freq` is in Hz and `SNR` is
        (currently) in arbitrary units.

    """
    # Find the results index of the maximum.
    freq_index, cp_samples = np.unravel_index(results.argmax(),
                                              results.shape)

    if freq_index > 1 and freq_index < len(freqs)-1:
      delta = self.interpolate(
        results[freq_index-1][cp_samples],
        results[freq_index][cp_samples],
        results[freq_index+1][cp_samples],
        interpolation
      )
      if delta > 0:
        freq = freqs[freq_index] + (freqs[freq_index+1] - freqs[freq_index]) * delta
      else:
        freq = freqs[freq_index] - (freqs[freq_index-1] - freqs[freq_index]) * delta
    else:
      freq = freqs[freq_index]

    code_phase = float(cp_samples) / self.samples_per_chip

    # Calculate SNR for the peak.
    snr = np.max(results) / np.mean(results)

    return (code_phase, freq, snr)

  def acquisition(self,
                  prns=range(32),
                  start_doppler=-7000,
                  stop_doppler=7000,
                  doppler_step=None,
                  threshold=DEFAULT_THRESHOLD,
                  show_progress=True):
    """
    Perform an acquisition for a given list of PRNs.

    Perform an acquisition for a given list of PRNs across a range of Doppler
    frequencies.

    This function returns :class:`AcquisitionResult` objects containing the
    location of the acquisition peak for PRNs that have an acquisition
    Signal-to-Noise ratio (SNR) greater than `threshold`.

    This calls `acquire` to find the precise code phase and a carrier frequency
    estimate to within `doppler_step` Hz and then uses interpolation to refine
    the carrier frequency estimate.

    Parameters
    ----------
    prns : iterable
      List of PRNs to acquire.
    start_doppler : float, optional
      Start of Doppler frequency search range in Hz. This value is included in
      the search.
    stop_doppler : float, optional
      End of Doppler frequency search range in Hz. This value is not included
      in the search.
    doppler_step : float, optional
      Doppler frequency step to use when performing the coarse Doppler
      frequency search.
    threshold : float, optional
      Threshold SNR value for a satellite to be considered acquired.
    show_progress : bool, optional
      When `True` a progress bar will be printed showing acquisition status and
      estimated time remaining.

    Returns
    -------
    out : [AcquisitionResult]
      A list of :class:`AcquisitionResult` objects, one per PRN in `prns`.

    """
    logger.info("Acquisition starting")

    # If the Doppler step is not specified, compute it from the coarse
    # acquisition length.
    if doppler_step is None:
      # TODO: Work out the best frequency bin spacing.
      # This is slightly sub-optimal if power is split between two bins,
      # perhaps you could peak fit or look at pairs of bins to get true peak
      # magnitude.
      doppler_step = self.sampling_freq / self.n_coarse

    freqs = np.arange(start_doppler, stop_doppler, doppler_step) + self.IF

    # If progressbar is not available, disable show_progress.
    if show_progress and not _progressbar_available:
      show_progress = False
      logger.warning("show_progress = True but progressbar module not found.")

    # Setup our progress bar if we need it
    if show_progress:
      widgets = ['  Acquisition ',
                 progressbar.Attribute('prn', '(PRN: %02d)', '(PRN --)'), ' ',
                 progressbar.Percentage(), ' ',
                 progressbar.ETA(), ' ',
                 progressbar.Bar()]
      pbar = progressbar.ProgressBar(widgets=widgets,
                                     maxval=len(prns)*len(freqs))
      pbar.start()
    else:
      pbar = None

    acq_results = []
    for n, prn in enumerate(prns):
      if pbar:
        def progress_callback(freq_num, num_freqs):
          pbar.update(n*len(freqs) + freq_num, attr={'prn': prn + 1})
      else:
        progress_callback = None

      coarse_results = self.acquire(caCodes[prn], freqs,
                                    progress_callback=progress_callback)
      code_phase, carr_freq, snr = self.find_peak(freqs, coarse_results)

      # If the result is above the threshold, then we have acquired the
      # satellite.
      status = '-'
      if (snr > threshold):
        status = 'A'

      # Save properties of the detected satellite signal
      acq_result = AcquisitionResult(prn,
                                     carr_freq,
                                     carr_freq - self.IF,
                                     code_phase,
                                     snr,
                                     status)
      acq_results.append(acq_result)

      # If the acquisition was successful, log it
      if (snr > threshold):
        logger.debug("Acquired %s" % acq_result)

    # Acquisition is finished

    # Stop printing progress bar
    if pbar:
      pbar.finish()

    logger.info("Acquisition finished")
    acquired_prns = [ar.prn + 1 for ar in acq_results if ar.status == 'A']
    logger.info("Acquired %d satellites, PRNs: %s.",
                len(acquired_prns), acquired_prns)

    return acq_results

  def load_wisdom(self, wisdom_file=DEFAULT_WISDOM_FILE):
    """Load saved FFTW wisdom from file."""
    with open(wisdom_file, 'rb') as f:
      wisdom = cPickle.load(f)
      pyfftw.import_wisdom(wisdom)

  def save_wisdom(self, wisdom_file=DEFAULT_WISDOM_FILE):
    """Save FFTW wisdom to file."""
    with open(wisdom_file, 'wb') as f:
      cPickle.dump(pyfftw.export_wisdom(), f, protocol=cPickle.HIGHEST_PROTOCOL)


class AcquisitionResult:
  """
  Stores the acquisition parameters of a single satellite.

  Parameters
  ----------
  prn : int
    PRN of the satellite.
  carr_freq : float
    Carrier frequency in Hz.
  doppler : float
    Doppler frequency in Hz,
    i.e. `carr_freq` - receiver intermediate frequency.
  code_phase : float
    Code phase in chips.
  snr : float
    Signal-to-Noise Ratio.
  status : {'A', '-'}
    The acquisition status of the satellite:
      * `'A'` : The satellite has been successfully acquired.
      * `'-'` : The acquisition was not successful, the SNR was below the
                acquisition threshold.

  """

  __slots__ = ('prn', 'carr_freq', 'doppler', 'code_phase', 'snr', 'status')

  def __init__(self, prn, carr_freq, doppler, code_phase, snr, status):
    self.prn = prn
    self.snr = snr
    self.carr_freq = carr_freq
    self.doppler = doppler
    self.code_phase = code_phase
    self.status = status

  def __str__(self):
    return "PRN %2d SNR %6.2f @ CP %6.1f, %+8.2f Hz %s" % \
        (self.prn + 1, self.snr, self.code_phase, self.doppler, self.status)

  def __repr__(self):
    return "<AcquisitionResult %s>" % self.__str__()


def save_acq_results(filename, acq_results):
  """
  Save a set of acquisition results to a file.

  Parameters
  ----------
  filename : string
    Filename to save acquisition results to.
  acq_results : [:class:`AcquisitionResult`]
    List of :class:`AcquisitionResult` objects to save.

  """
  with open(filename, 'wb') as f:
    cPickle.dump(acq_results, f, protocol=cPickle.HIGHEST_PROTOCOL)

def load_acq_results(filename):
  """
  Load a set of acquisition results from a file.

  Parameters
  ----------
  filename : string
    Filename to load acquisition results from.

  Returns
  -------
  acq_results : [:class:`AcquisitionResult`]
    List of :class:`AcquisitionResult` objects loaded from the file.

  """
  with open(filename, 'rb') as f:
    return cPickle.load(f)


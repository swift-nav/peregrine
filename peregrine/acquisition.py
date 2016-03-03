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
import defaults

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
  sampling_freq : float, optional
    The sampling frequency of the samples in Hz.
  IF : float, optional
    The receiver intermediate frequency used when capturing the samples.
  samples_per_code : float, optional
    The number of samples corresponding to one code length.
  code_length : int, optional
    The number of chips in the chipping code.
  offsets : int, optional
    Offsets, in units of code length (1ms), to use when performing long
    integrations to avoid clobbering by nav bit edges.
    If None, will try to figure out some suitable ones.
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
               code_length=defaults.code_length,
               n_codes_integrate=4,
               offsets = None,
               wisdom_file=DEFAULT_WISDOM_FILE):

    self.sampling_freq = sampling_freq
    self.IF = IF
    self.samples_per_code = int(round(samples_per_code))
    self.n_integrate = n_codes_integrate * self.samples_per_code
    self.code_length = code_length
    self.samples_per_chip = float(samples_per_code) / code_length

    if offsets is None:
      if n_codes_integrate <= 10:
        offsets = [0, self.n_integrate]
      elif n_codes_integrate <= 13:
        offsets = [0, 2*(n_codes_integrate - 10)*self.samples_per_code,
                   self.n_integrate]
      elif n_codes_integrate <= 15:
        offsets = [0, (n_codes_integrate - 10) * self.samples_per_code,
                   2*(n_codes_integrate - 10) * self.samples_per_code,
                   self.n_integrate]
      else:
        raise ValueError("Integration interval too long to guess nav-declobber "
                         + "offsets. Specify them or generalize the technique.")
    self.offsets = offsets

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
    self.code = pyfftw.n_byte_align_empty((self.n_integrate), 16,
                                          dtype=np.complex128)
    self.code_ft = pyfftw.n_byte_align_empty((self.n_integrate), 16,
                                             dtype=np.complex128)
    # Create an FFTW transforms which will execute the code FFT.
    self.code_fft = pyfftw.FFTW(self.code, self.code_ft)

    # Allocate aligned arrays for the inverse FFT.
    self.corr_ft = pyfftw.n_byte_align_empty((self.n_integrate), 16,
                                              dtype=np.complex128)
    self.corr = pyfftw.n_byte_align_empty((self.n_integrate), 16,
                                           dtype=np.complex128)

    # Setup FFTW transforms for inverse FFT.
    self.corr_ifft = pyfftw.FFTW(self.corr_ft, self.corr,
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

    # Create some short sets of data to correlate with
    self.short_samples = [samples[off:(off + self.n_integrate)]
                          for off in self.offsets]

    # Pre-compute Fourier transforms of the short signals
    self.short_samples_ft = [np.fft.fft(samps) for samps in self.short_samples]

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
    results = np.empty((len(self.offsets), len(freqs), self.samples_per_code))

    # Upsample the code to our sampling frequency.
    code_indices = np.arange(1.0, self.n_integrate + 1.0) / \
                    self.samples_per_chip
    code_indices = np.remainder(np.asarray(code_indices, np.int), self.code_length)
    self.code[:] = code[code_indices]

    # Find the conjugate Fourier transform of the code which will be used to
    # perform the correlation.
    self.code_fft.execute()
    code_ft_conj = np.conj(self.code_ft)

    acq_mag = []
    for n, freq in enumerate(freqs):
      # Report on our progress
      if progress_callback:
        progress_callback(n + 1, len(freqs))

      # Shift the signal in the frequency domain to remove the carrier
      # i.e. mix down to baseband.
      shift = int((float(freq) * len(self.short_samples_ft[0]) /
                  self.sampling_freq) + 0.5)

      # Search over the possible nav bit offset intervals
      for offset_i in range(len(self.offsets)):
        short_samples_ft_bb = np.append(self.short_samples_ft[offset_i][shift:],
                                        self.short_samples_ft[offset_i][:shift])

        # Multiplication in frequency <-> correlation in time.
        self.corr_ft[:] = short_samples_ft_bb * code_ft_conj

        # Perform inverse Fourier transform to obtain correlation results.
        self.corr_ifft.execute()
        acq_mag = np.abs(self.corr[:self.samples_per_code])
        results[offset_i][n] = np.square(acq_mag)

    # Choose the nav-bit-declobber sample interval with the best correlation
    max_indices = np.unravel_index(results.argmax(), results.shape)
    return results[max_indices[0]]


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
                  doppler_priors = None,
                  doppler_search = 7000,
                  doppler_step = None,
                  threshold=DEFAULT_THRESHOLD,
                  show_progress=True,
                  multi=True
  ):
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
    prns : iterable, optional
      List of PRNs to acquire. Default: 0..31 (0-indexed)
    doppler_prior: list of floats, optional
      List of expected Doppler frequencies in Hz (one per PRN).  Search will be
      centered about these.  If None, will search around 0 for all PRNs.
    doppler_search: float, optional
      Maximum frequency away from doppler_prior to search.  Default: 7000
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
    from peregrine.parallel_processing import parmap

    # If the Doppler step is not specified, compute it from the coarse
    # acquisition length.
    if doppler_step is None:
      # TODO: Work out the best frequency bin spacing.
      # This is slightly sub-optimal if power is split between two bins,
      # perhaps you could peak fit or look at pairs of bins to get true peak
      # magnitude.
      doppler_step = self.sampling_freq / self.n_integrate

    if doppler_priors is None:
      doppler_priors = np.zeros_like(prns)


    # If progressbar is not available, disable show_progress.
    if show_progress and not _progressbar_available:
      show_progress = False
      logger.warning("show_progress = True but progressbar module not found.")

    # Setup our progress bar if we need it
    if show_progress and not multi:
      widgets = ['  Acquisition ',
                 progressbar.Attribute('prn', '(PRN: %02d)', '(PRN --)'), ' ',
                 progressbar.Percentage(), ' ',
                 progressbar.ETA(), ' ',
                 progressbar.Bar()]
      pbar = progressbar.ProgressBar(widgets=widgets,
                                     maxval=int(len(prns) *
                                     (2 * doppler_search / doppler_step + 1)))
      pbar.start()
    else:
      pbar = None

    def do_acq(n):
      prn = prns[n]
      doppler_prior = doppler_priors[n]
      freqs = np.arange(doppler_prior - doppler_search,
                        doppler_prior + doppler_search, doppler_step) + self.IF
      if pbar:
        def progress_callback(freq_num, num_freqs):
          pbar.update(n*len(freqs) + freq_num, attr={'prn': prn + 1})
      else:
        progress_callback = None

      coarse_results = self.acquire(caCodes[prn], freqs,
                                    progress_callback=progress_callback)


      code_phase, carr_freq, snr = self.find_peak(freqs, coarse_results,
                                                  interpolation = 'gaussian')

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
                                     status,
                                     'l1ca')

      # If the acquisition was successful, log it
      if (snr > threshold):
        logger.debug("Acquired %s" % acq_result)

      return acq_result

    if multi:
      acq_results = parmap(do_acq, range(len(prns)), show_progress=show_progress)
    else:
      acq_results = map(do_acq, range(len(prns)))

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
  signal : {'l1ca', 'l2c'}
    The type of the signal: L1C/A or L2C
  sample_channel : IQ channel index
  sample_index : Index of sample when acquisition succeeded
  """

  __slots__ = ('prn', 'carr_freq', 'doppler', \
               'code_phase', 'snr', 'status', 'signal')

  def __init__(self, prn, carr_freq, doppler, code_phase, snr, status, signal,
               sample_channel = 0,
               sample_index = 0):
    self.prn = prn
    self.snr = snr
    self.carr_freq = carr_freq
    self.doppler = doppler
    self.code_phase = code_phase
    self.status = status
    self.signal = signal
    self.sample_channel = sample_channel
    self.sample_index = sample_index

  def __str__(self):
    return "PRN %2d (%s) SNR %6.2f @ CP %6.1f, %+8.2f Hz %s" % \
        (self.prn + 1, self.signal, self.snr, self.code_phase, \
         self.doppler, self.status)

  def __repr__(self):
    return "<AcquisitionResult %s>" % self.__str__()

  def __eq__(self, other):
    return self._equal(other)

  def __ne__(self, other):
    return not self._equal(other)

  def _equal(self, other):
    """
    Compare equality between self and another :class:`AcquisitionResult` object.

    Parameters
    ----------
    other : :class:`AcquisitionResult` object
      The :class:`AcquisitionResult` to test equality against.

    Return
    ------
    out : bool
      True if the passed :class:`AcquisitionResult` object is identical.
    
    """
    if set(self.__dict__.keys()) != set(other.__dict__.keys()):
      return False

    for k in self.__dict__.keys():
      if isinstance(self.__dict__[k], float):
        if abs(self.__dict__[k] - other.__dict__[k]) > 1e-6:
          return False
      elif self.__dict__[k] != other.__dict__[k]:
        return False

    return True

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

def print_scores(acq_results, pred, pred_dopp = None):
  if pred_dopp is None:
    pred_dopp = np.zeros_like(pred)

  print "PRN\tPred'd\tAcq'd\tError\tSNR"
  n_match = 0
  worst_dopp_err = 0
  sum_dopp_err = 0
  sum_abs_dopp_err = 0

  for i, prn in enumerate(pred):
      print "%2d\t%+6.0f" % (prn + 1, pred_dopp[i]),
      if acq_results[i].status == 'A':
          n_match += 1
          dopp_err = acq_results[i].doppler - pred_dopp[i]
          sum_dopp_err += dopp_err
          sum_abs_dopp_err += abs(dopp_err)
          if abs(dopp_err) > abs(worst_dopp_err):
              worst_dopp_err = dopp_err
          print "\t%+6.0f\t%+5.0f\t%5.1f" % (
              acq_results[i].doppler, dopp_err, acq_results[i].snr)
      else:
          print

  print "Found %d of %d, mean doppler error = %+5.0f Hz, mean abs err = %4.0f Hz, worst = %+5.0f Hz"\
        % (n_match, len(pred),
           sum_dopp_err/max(1, n_match), sum_abs_dopp_err/max(1, n_match), worst_dopp_err)

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
import pickle

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

# Only define our progressbar extensions if progressbar is available.
if _progressbar_available:
  class _AcqProgressBar(progressbar.ProgressBar):
    """Extends ProgressBar to store the PRN being processed."""
    __slots__ = ('prn')

    def __init__(self, *args, **kwargs):
      self.prn = None
      progressbar.ProgressBar.__init__(self, *args, **kwargs)

    def update(self, value, prn=None):
      if prn is not None:
        self.prn = prn
      progressbar.ProgressBar.update(self, value)


  class _PRNWidget(progressbar.Widget):
    """Widget to display the PRN being processed."""
    TIME_SENSITIVE = True

    def update(self, pbar):
      if pbar.prn:
        return "PRN %d" % pbar.prn
      else:
        return "PRN -"


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
  n_codes_fine : int, optional
    The number of whole code lengths of sample data to use when performing a
    fine carrier frequency search. This is proportional to the frequency
    resolution available. See :func:`fine_carrier`.
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
               n_codes_fine=8,
               wisdom_file=DEFAULT_WISDOM_FILE):

    self.sampling_freq = sampling_freq
    self.IF = IF
    self.samples_per_code = int(round(samples_per_code))
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
    self.code = pyfftw.n_byte_align_empty((self.samples_per_code), 16,
                                          dtype=np.complex128)
    self.code_ft = pyfftw.n_byte_align_empty((self.samples_per_code), 16,
                                             dtype=np.complex128)
    # Create an FFTW transforms which will execute the code FFT.
    self.code_fft = pyfftw.FFTW(self.code, self.code_ft)

    # Allocate aligned arrays for the inverse FFT.
    self.corr_ft1 = pyfftw.n_byte_align_empty((self.samples_per_code), 16,
                                              dtype=np.complex128)
    self.corr1 = pyfftw.n_byte_align_empty((self.samples_per_code), 16,
                                           dtype=np.complex128)
    self.corr_ft2 = pyfftw.n_byte_align_empty((self.samples_per_code), 16,
                                              dtype=np.complex128)
    self.corr2 = pyfftw.n_byte_align_empty((self.samples_per_code), 16,
                                           dtype=np.complex128)

    # Setup FFTW transforms for inverse FFT.
    self.corr_ifft1 = pyfftw.FFTW(self.corr_ft1, self.corr1,
                                  direction='FFTW_BACKWARD')
    self.corr_ifft2 = pyfftw.FFTW(self.corr_ft2, self.corr2,
                                  direction='FFTW_BACKWARD')

    # Setup fine carrier frequency search:

    # Number of samples to use for fine carrier frequency search.
    self.n_fine = n_codes_fine * self.samples_per_code
    # Pre-calculate the window function used for the fine FFT.
    self.fine_fft_window = np.hanning(self.n_fine)
    # Use next highest power of 2 for fine FFT size.
    self.n_fine_fft = 2**int(np.ceil(np.log2(self.n_fine)))

    # Allocate an aligned array for the fine FFT input,
    # this will contain the samples with the code wiped-off.
    self.fine_wiped = pyfftw.n_byte_align_empty((self.n_fine_fft), 16,
                                                dtype=np.complex128)
    # The fine FFT input is padded so make sure it is zeroed.
    self.fine_wiped[:] = 0
    # Allocate aligned array for the fine FFT result.
    self.fine_wiped_ft = pyfftw.n_byte_align_empty((self.n_fine_fft), 16,
                                                   dtype=np.complex128)
    # Create an FFTW transforms which will execute the fine FFT.
    self.fine_fft = pyfftw.FFTW(self.fine_wiped, self.fine_wiped_ft)

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
    self.short_samples1 = samples[0:self.samples_per_code]
    self.short_samples2 = samples[self.samples_per_code:2*self.samples_per_code]

    # Pre-compute Fourier transforms of the two short signals
    self.short_samples1_ft = np.fft.fft(self.short_samples1)
    self.short_samples2_ft = np.fft.fft(self.short_samples2)

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
    code_indicies = np.arange(1.0, self.samples_per_code + 1.0) / \
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
      acq_mag1 = np.abs(self.corr1)
      acq_mag2 = np.abs(self.corr2)

      # Use the signal with the largest correlation peak as the result as one
      # of the signals may contain a nav bit edge. Square the result to find
      # the correlation power.
      if (np.max(acq_mag1) > np.max(acq_mag1)):
        results[n] = np.square(acq_mag1)
      else:
        results[n] = np.square(acq_mag2)

    return results

  def find_peak(self, freqs, results):
    """
    Find the peak within an set of acquisition results.

    Finds the point in the acquisition results array with the greatest
    correlation power and determines the code phase and carrier frequency
    corresponding to that point. The Signal-to-Noise Ratio (SNR) of the peak is
    also estimated.

    Parameters
    ----------
    freqs : iterable
      List of frequencies mapping the results frequncy index to a value in Hz.
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
    # Convert to natural units.
    freq = freqs[freq_index]
    code_phase = float(cp_samples) / self.samples_per_chip

    # Calculate SNR for the peak.
    snr = np.max(results) / np.mean(results)

    return (code_phase, freq, snr)

  def fine_carrier(self, code, code_phase, interpolation='gaussian'):
    """
    Perform a fine carrier frequency search at a given code phase.

    Without interpolation this yeilds a frequency estimate to within one FFT
    bin. The interpolation methods and the frequency estimate improvement they
    yeild are discussed in [1]_.

    The FFT input is zero-padded up to the nearest power of two, so the FFT
    frequency bin spacing is given by::

      2 * sampling_freq / 2**ceil(log2(samples_per_code * n_codes_fine)

    Parameters
    ----------
    code : :class:`numpy.ndarray`
      An array containing the code to use, one element per chip
      with value +/- 1.
    code_phase : float
      The code phase in chips.
    interpolation : {'gaussian', 'parabolic', 'none'}, optional
      Takes the values 'gaussian', 'parabolic' or 'none'.  When not 'none' the
      carrier frequency estimate is refined by interpolating between FFT bins
      with the specified type of fit.

    Returns
    -------
    out : float
      The carrier frequency estimate in Hz.

    References
    ----------

    .. [1] Gasior, M. et al., "Improving FFT frequency measurement resolution
       by parabolic and Gaussian spectrum interpolation" AIP Conf.Proc. 732
       (2004) 276-285 `CERN-AB-2004-023-BDI
       <http://cdsweb.cern.ch/record/738182>`_

    """
    # Upsample the code to our sampling frequency and number of samples.
    code_indicies = np.arange(1.0, self.n_fine + 1.0) / self.samples_per_chip
    code_indicies = np.remainder(np.asarray(code_indicies, np.int), self.code_length)
    long_code = code[code_indicies]

    # Index into our samples to a point where the code phase is zero and grab
    # n_fine samples, removing any DC offset.
    code_phase_samples = code_phase * self.samples_per_chip
    fine_samples = self.samples[code_phase_samples:][:self.n_fine]
    fine_samples -= np.mean(fine_samples)
    # Perform a code 'wipe-off' by multiplying by a replica code
    # (i.e. upsampled and at the same code phase)
    # This leaves us with just the carrier.
    self.fine_wiped[:self.n_fine] = fine_samples * long_code

    # Apply window fuction to reduce spectral leakage.
    self.fine_wiped[:self.n_fine] *= self.fine_fft_window

    # Perform the FFT to find the carrier frequency.
    self.fine_fft.execute()
    # Find amplitude only looking at unique points in the FFT.
    # TODO: Can probably just use a real FFT here!
    unique_pts = int(np.ceil((self.n_fine_fft + 1) / 2))
    carrier_fft = np.abs(self.fine_wiped_ft[:unique_pts])

    # Find the location of the maximum in the FFT.
    max_index = np.argmax(carrier_fft)

    # Use interpolation to refine frequency estimate
    # See: Improving FFT frequency measurement resolution by parabolic
    #      and Gaussian spectrum interpolation - Gasior, M. et al.
    #      AIP Conf.Proc. 732 (2004) 276-285 CERN-AB-2004-023-BDI

    if interpolation == 'parabolic':
      # Parabolic interpolation.
      k_0 = carrier_fft[max_index - 1]
      k_1 = carrier_fft[max_index]
      k_2 = carrier_fft[max_index + 1]
      max_index += 0.5 * (k_2 - k_0) / (2*k_1 - k_0 - k_2)
    elif interpolation == 'gaussian':
      # Gaussian interpolation.
      ln_k_0 = np.log(carrier_fft[max_index - 1])
      ln_k_1 = np.log(carrier_fft[max_index])
      ln_k_2 = np.log(carrier_fft[max_index + 1])
      max_index += 0.5 * (ln_k_2 - ln_k_0) / (2*ln_k_1 - ln_k_0 - ln_k_2)
    elif interpolation == 'none':
      pass
    else:
      raise ValueError("Unknown interpolation mode '%s'", interpolation)

    carrier_freq = max_index * self.sampling_freq / self.n_fine_fft

    return carrier_freq

  def acquisition(self,
                  prns=range(32),
                  start_doppler=-7000,
                  stop_doppler=7000,
                  doppler_step=500,
                  threshold=DEFAULT_THRESHOLD,
                  show_progress=True):
    """
    Perform a two stage acquisition for a given list of PRNs.

    Perform a two stage acquisition for a given list of PRNs across a range of
    Doppler frequencies.

    This function returns :class:`AcquisitionResult` objects contatining the
    location of the acquisition peak for PRNs that have an acquisition
    Signal-to-Noise ratio (SNR) greater than `threshold`.

    This function performs a two-stage acquisition. The first stage calls
    `acquire` to find the precise code phase and a carrier frequency estimate
    to within `doppler_step` Hz. The second stage calls `fine_carrier` to
    refine the carrier frequency estimate with a fine resolution carrier
    frequency search.

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
      A list of :class:`AcquisitionResult` objects, one per successfully
      acquired satellite.

    """
    logger.info("Acquisition starting")

    freqs = np.arange(start_doppler, stop_doppler, doppler_step) + self.IF

    # If progressbar is not available, disable show_progress.
    if show_progress and not _progressbar_available:
      show_progress = False
      logger.warning("show_progress = True but progressbar module not found.")

    # Setup our progress bar if we need it
    if show_progress:
      widgets = ['  Acquisition (',
                 _PRNWidget(), '): ',
                 progressbar.Percentage(), ' ',
                 progressbar.ETA(), ' ',
                 progressbar.Bar()]
      pbar = _AcqProgressBar(widgets=widgets,
                             maxval=len(prns)*len(freqs))
      pbar.start()
    else:
      pbar = None

    acq_results = []
    for n, prn in enumerate(prns):
      if pbar:
        def progress_callback(freq_num, num_freqs):
          pbar.update(n*len(freqs) + freq_num, prn + 1)
      else:
        progress_callback = None

      coarse_results = self.acquire(caCodes[prn], freqs,
                                    progress_callback=progress_callback)
      code_phase, carr_freq, snr = self.find_peak(freqs, coarse_results)

      # If the result is above the threshold,
      # then we have acquired the satellite
      if (snr > threshold):
        carr_freq_fine = self.fine_carrier(caCodes[prn], code_phase)

        # Save properties of the detected satellite signal
        acq_result = AcquisitionResult(prn,
                                       carr_freq_fine,
                                       carr_freq_fine - self.IF,
                                       code_phase,
                                       snr)
        acq_results.append(acq_result)
        logger.debug("Acquired %s" % acq_result)

    # Acquisition is finished

    # Stop printing progress bar
    if pbar:
      pbar.finish()

    logger.info("Acquisition finished")
    logger.info("Acquired %d satellites, PRNs: %s.", len(acq_results),
                [ar.prn + 1 for ar in acq_results])

    return acq_results

  def load_wisdom(self, wisdom_file=DEFAULT_WISDOM_FILE):
    """Load saved FFTW wisdom from file."""
    with open(wisdom_file, 'rb') as f:
      wisdom = pickle.load(f)
      pyfftw.import_wisdom(wisdom)

  def save_wisdom(self, wisdom_file=DEFAULT_WISDOM_FILE):
    """Save FFTW wisdom to file."""
    with open(wisdom_file, 'wb') as f:
      pickle.dump(pyfftw.export_wisdom(), f)


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

  """

  __slots__ = ('prn', 'carr_freq', 'doppler', 'code_phase', 'snr')

  def __init__(self, prn, carr_freq, doppler, code_phase, snr):
    self.prn = prn
    self.snr = snr
    self.carr_freq = carr_freq
    self.doppler = doppler
    self.code_phase = code_phase

  def __str__(self):
    return "PRN %2d SNR %6.2f @ CP %6.1f, %+8.2f Hz" % (self.prn + 1,
                                                        self.snr,
                                                        self.code_phase,
                                                        self.doppler)

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
    pickle.dump(acq_results, f)

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
    return pickle.load(f)


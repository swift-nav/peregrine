# Copyright (C) 2012 Swift Navigation Inc.
#
# This source is subject to the license found in the file 'LICENSE' which must
# be be distributed together with this source. All other rights reserved.
#
# THIS CODE AND INFORMATION IS PROVIDED "AS IS" WITHOUT WARRANTY OF ANY KIND,
# EITHER EXPRESSED OR IMPLIED, INCLUDING BUT NOT LIMITED TO THE IMPLIED
# WARRANTIES OF MERCHANTABILITY AND/OR FITNESS FOR A PARTICULAR PURPOSE.

import numpy as np
import pyfftw
import pickle
import progressbar

from include.makeCaTable import makeCaTable
from include.generateCAcode import caCodes

import logging
logger = logging.getLogger(__name__)

class _AcqProgressBar(progressbar.ProgressBar):
  """Extends ProgressBar to store the PRN being processed."""
  __slots__ = ('prn')
  def __init__(self, **kwargs):
    self.prn = None
    progressbar.ProgressBar.__init__(self, **kwargs)
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

def acquisition(longSignal, settings, wisdom_file="fftw_wisdom"):
  logger.info("Acquisition starting")

  # Try to load saved FFTW wisdom
  try:
    with open(wisdom_file, 'rb') as f:
      wisdom = pickle.load(f)
      pyfftw.import_wisdom(wisdom)
  except IOError:
    logger.warning("Couldn't open FFTW wisdom file, this run might take longer than usual.")

  # Number of samples per code period
  samplesPerCode = int(round(settings.samplingFreq / (settings.codeFreqBasis / settings.codeLength)))
  samplesPerCodeChip = int(round(settings.samplingFreq / settings.codeFreqBasis))
  # Create two 1ms sets of data to correlate with
  signal1 = np.array(longSignal[0:samplesPerCode])
  signal2 = np.array(longSignal[samplesPerCode:2*samplesPerCode])
  # Find sampling period
  ts = 1.0/settings.samplingFreq
  # Find phases for the local carrier
  phasePoints = 2*np.pi*ts * np.arange(samplesPerCode)
  # Number of frequency bins for the given acquisition band (500 Hz steps)
  numberOfFrqBins = int(np.floor(settings.acqSearchBand*1e3/500 + 1))
  # Generate all C/A codes and sample them according to the sampling freq
  caCodesTable = np.array(makeCaTable(settings))
  # Initialize arrays
  results = np.zeros((numberOfFrqBins, samplesPerCode))
  # Carrier frequencies of the frequency bins
  frqBins = np.zeros((numberOfFrqBins))
  # Initialize acqResults
  acqResults = []

  n_fine = 8*samplesPerCode
  window = np.hanning(n_fine)
  # Find next highest power of 2
  fine_fftNumPts = 2**int(np.ceil(np.log2(n_fine)))
  xCarrier = pyfftw.n_byte_align_empty((fine_fftNumPts), 16, dtype=np.complex128)
  xCarrier[:] = 0
  xCarrier_ft = pyfftw.n_byte_align_empty(xCarrier.shape, 16, dtype=xCarrier.dtype)
  fine_fft = pyfftw.FFTW(xCarrier, xCarrier_ft)

  # Make aligned arrays for FFTW
  ca_code = pyfftw.n_byte_align_empty((samplesPerCode), 16, dtype=np.complex128)
  ca_code_ft = pyfftw.n_byte_align_empty(ca_code.shape, 16, dtype=ca_code.dtype)

  corr_ft1 = pyfftw.n_byte_align_empty((samplesPerCode), 16, dtype=np.complex128)
  corr1 = pyfftw.n_byte_align_empty((samplesPerCode), 16, dtype=np.complex128)
  corr_ft2 = pyfftw.n_byte_align_empty((samplesPerCode), 16, dtype=np.complex128)
  corr2 = pyfftw.n_byte_align_empty((samplesPerCode), 16, dtype=np.complex128)

  # Setup FFTW transforms
  ca_code_fft = pyfftw.FFTW(ca_code, ca_code_ft)
  corr_ifft1 = pyfftw.FFTW(corr_ft1, corr1, direction='FFTW_BACKWARD')
  corr_ifft2 = pyfftw.FFTW(corr_ft2, corr2, direction='FFTW_BACKWARD')

  # Find Fourier transforms of the two signals
  signal1_ft = np.fft.fft(signal1)
  signal2_ft = np.fft.fft(signal2)

  widgets = ['  Acquisition (',
             _PRNWidget(), '): ',
             progressbar.Percentage(), ' ',
             progressbar.ETA(), ' ',
             progressbar.Bar()]
  pbar = _AcqProgressBar(widgets=widgets,
           maxval=len(settings.acqSatelliteList)*numberOfFrqBins)
  pbar.start()

  for PRN in settings.acqSatelliteList:

    # Find the conjugate Fourier transform of the CA code which will be used to
    # perform the correlation
    ca_code[:] = caCodesTable[PRN]
    ca_code_fft.execute()
    ca_code_ft_conj = np.conj(ca_code_ft)

    for frqBinIndex in range(numberOfFrqBins):
      pbar.update(settings.acqSatelliteList.index(PRN)*numberOfFrqBins +
                  frqBinIndex, PRN)
      #--- Generate carrier wave frequency grid (0.5kHz step) -----------
      frqBins[frqBinIndex] = settings.IF \
                             - settings.acqSearchBand/2*1000 \
                             + 0.5e3*frqBinIndex

      # Shift the signal in the frequency domain to remove the carrier
      # i.e. mix down to baseband
      shift = int((len(signal1_ft) / settings.samplingFreq) * frqBins[frqBinIndex])
      signal1_ft_bb = np.append(signal1_ft[shift:], signal1_ft[:shift])
      signal2_ft_bb = np.append(signal2_ft[shift:], signal2_ft[:shift])

      # Multiplication in frequency <-> correlation in time
      corr_ft1[:] = signal1_ft_bb * ca_code_ft_conj
      corr_ft2[:] = signal2_ft_bb * ca_code_ft_conj

      # Perform inverse Fourier transform to obtain correlation results
      corr_ifft1.execute()
      corr_ifft2.execute()
      # Find the correlation amplitude
      acq_result1 = np.abs(corr1)
      acq_result2 = np.abs(corr2)

      # Use the signal with the largest correlation peak as the result as one of
      # the signals may contain a nav bit edge. Square the result to find the
      # correlation power.
      if (np.max(acq_result1) > np.max(acq_result1)):
        results[frqBinIndex] = np.square(acq_result1)
      else:
        results[frqBinIndex] = np.square(acq_result2)

    # Find the frequency and code phase of the correlation peak
    frequencyBinIndex, codePhase = np.unravel_index(results.argmax(), results.shape)
    # Calculate SNR for the peak
    SNR = np.max(results) / np.mean(results)

    # If the result is above the threshold, then we have acquired the satellite
    if (SNR > settings.acqThreshold):
      # Fine resolution frequency search
      # Generate 8ms long CA code sequence for given PRN
      codeValueIndex = np.arange(1.0, n_fine+1.0) * ts * settings.codeFreqBasis
      codeValueIndex = np.remainder(np.asarray(codeValueIndex, np.int), 1023)
      longCaCode = caCodes[PRN][codeValueIndex]

      # Remove CA code modulation from the original signal
      signal0DC = longSignal[codePhase:][:n_fine]
      signal0DC -= np.mean(signal0DC)
      xCarrier[:n_fine] = signal0DC * longCaCode

      # Apply window fuction to reduce spectral leakage
      xCarrier[:n_fine] *= window

      # Compute the magnitude of the FFT, find the maximum, and the associated carrier frequency
      #fftxc = np.abs(np.fft.fft(xCarrier,n=fftNumPts))
      fine_fft.execute()
      fftxc = np.abs(xCarrier_ft)
      uniqFftPts = int(np.ceil((fine_fftNumPts+1)/2))

      fftMaxIndex = np.argmax(fftxc[:uniqFftPts])

      # Use interpolation to refine frequency estimate
      # See: Improving FFT frequency measurement resolution by parabolic and Gaussian spectrum interpolation
      #      Gasior, M. et al. - AIP Conf.Proc. 732 (2004) 276-285 CERN-AB-2004-023-BDI

      # Parabolic interpolation
      #fftMaxIndex = 0.5 * (fftxc[fftMaxIndex+1] - fftxc[fftMaxIndex-1]) / \
      #    (2*fftxc[fftMaxIndex] - fftxc[fftMaxIndex+1] - fftxc[fftMaxIndex-1])

      # Gaussian interpolation
      ln_k_0 = np.log(fftxc[fftMaxIndex-1])
      ln_k_1 = np.log(fftxc[fftMaxIndex])
      ln_k_2 = np.log(fftxc[fftMaxIndex+1])
      fftMaxIndex += 0.5 * (ln_k_2 - ln_k_0) / (2*ln_k_1 - ln_k_0 - ln_k_1)

      carrFreq = fftMaxIndex * settings.samplingFreq / fine_fftNumPts

      # Save properties of the detected satellite signal
      acq_result = AcquisitionResult(PRN, carrFreq, carrFreq - settings.IF, float(codePhase)/samplesPerCodeChip, SNR)
      acqResults += [acq_result]

      logger.debug("Acquired %s" % acq_result)

  # Acquisition is finished
  pbar.finish()

  # Save FFTW wisdom for later
  with open(wisdom_file, 'wb') as f:
    pickle.dump(pyfftw.export_wisdom(), f)

  logger.info("Acquisition finished")
  logger.info("Acquired %d satellites, PRNs: %s.", len(acqResults),
              [ar.prn+1 for ar in acqResults])

  return acqResults

class AcquisitionResult:
  """Stores the acquisition parameters of a single satellite."""
  __slots__ = ('prn', 'carr_freq', 'doppler', 'code_phase', 'snr')

  def __init__(self, prn, carr_freq, doppler, code_phase, snr):
    """
    Initialise a new AcquisitionResult.

    Args:
      prn: PRN of the satellite.
      carr_freq: Carrier frequency in Hz.
      doppler: Doppler frequency in Hz.
               (carr_freq - receiver intermediate frequency)
      code_phase: Code phase in chips.
      snr: Signal-to-Noise Ratio.

    """
    self.prn = prn
    self.snr = snr
    self.carr_freq = carr_freq
    self.doppler = doppler
    self.code_phase = code_phase

  def __str__(self):
    return "PRN %2d SNR %6.2f @ CP %6.1f, %+8.2f Hz" % (self.prn+1,
                                                        self.snr,
                                                        self.code_phase,
                                                        self.doppler)

  def __repr__(self):
    return "<AcquisitionResult %s>" % self.__str__()

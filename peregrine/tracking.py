# Copyright (C) 2012 Swift Navigation Inc.
#
# This source is subject to the license found in the file 'LICENSE' which must
# be be distributed together with this source. All other rights reserved.
#
# THIS CODE AND INFORMATION IS PROVIDED "AS IS" WITHOUT WARRANTY OF ANY KIND,
# EITHER EXPRESSED OR IMPLIED, INCLUDING BUT NOT LIMITED TO THE IMPLIED
# WARRANTIES OF MERCHANTABILITY AND/OR FITNESS FOR A PARTICULAR PURPOSE.

import numpy as np
from include.generateCAcode import caCodes
from samples import load_samples
import progressbar
import math

import swiftnav.track
import swiftnav.correlate

import logging
logger = logging.getLogger(__name__)

# Import progressbar if it is available.
_progressbar_available = True
try:
  import progressbar
except ImportError:
  _progressbar_available = False


class TrackingLoop(object):
  """
  Abstract base class for a tracking loop.

  Sub-classes should implement :meth:`update` and :meth:`start` and provide
  access to `code_freq` and `carr_freq` attributes or properties.

  The tracking loop should initialise its constant parameters in its `__init__`
  method. :meth:`start` will be called to (re)initialise the tracking loop,
  passing in the initial carrier and code frequencies.

  """
  __slots__ = ('code_freq', 'carr_freq')

  def start(self, code_freq, carr_freq):
    """
    (Re-)initialise the tracking loop.

    Parameters
    ----------
    code_freq : float
      The code phase rate (i.e. frequency).
    carr_freq : float
      The carrier frequency.

    """
    raise NotImplementedError()

  def update(self, e, p, l):
    """
    Tracking loop update step.

    Parameters
    ----------
    e : complex, :math:`I_E + Q_E j`
      The early correlation. The real component contains the in-phase
      correlation and the imaginary component contains the quadrature
      correlation.
    p : complex, :math:`I_P + Q_P j`
      The prompt correlation.
    l : complex, :math:`I_L + Q_L j`
      The late correlation.

    Returns
    -------
    out : (float, float)
      The tuple (code_freq, carrier_freq).

    """
    raise NotImplementedError()

default_loop_filter = swiftnav.track.SimpleTrackingLoop(
  (2, 0.7, 1),     # Code loop parameters
  (25, 0.7, 0.25), # Carrier loop parameters
  1e3              # Loop frequency
)

comp_loop_filter = swiftnav.track.CompTrackingLoop(
  (2, 0.7, 1),     # Code loop parameters
  (25, 0.7, 0.25), # Carrier loop parameters
  1e3,             # Loop frequency
  0.005,           # Tau
  1000             # Gain schedule after 1000 iterations (1s)
)

def track(signal, channel, settings,
          show_progress=True,
          trk=swiftnav.correlate.track_correlate,
          loop_filter=default_loop_filter):
  logger.info("Tracking starting")
  logger.debug("Tracking %d channels, PRNs %s" % (len(channel), [chan.prn+1 for chan in channel]))

  # Create list of tracking channels results (correlations, freqs, etc)
  track_results = []

  # If progressbar is not available, disable show_progress.
  if show_progress and not _progressbar_available:
    show_progress = False
    logger.warning("show_progress = True but progressbar module not found.")

  # Setup our progress bar if we need it
  if show_progress:
    widgets = ['  Tracking ',
               progressbar.Attribute(['chan', 'nchan'],
                                     '(CH: %d/%d)',
                                     '(CH: -/-)'), ' ',
               progressbar.Percentage(), ' ',
               progressbar.ETA(), ' ',
               progressbar.Bar()]
    pbar = progressbar.ProgressBar(widgets=widgets,
                                   maxval=len(channel)*settings.msToProcess,
                                   attr={'nchan': len(channel)})
    pbar.start()
  else:
    pbar = None

  #Do tracking for each channel
  for channelNr in range(len(channel)):
    track_result = TrackResults(settings.msToProcess)
    track_result.PRN = channel[channelNr].prn

    # Convert acquisition SNR to C/N0
    cn0_0 = 10*np.log10(channel[channelNr].snr)
    cn0_0 += 10*np.log10(1000) # Channel bandwidth
    cn0_est = swiftnav.track.CN0Estimator(1e3, cn0_0, 10, 1e3)

    loop_filter.start(settings.codeFreqBasis, channel[channelNr].carr_freq)
    remCodePhase = 0.0
    remCarrPhase = 0.0

    # Get a vector with the C/A code sampled 1x/chip
    caCode = caCodes[channel[channelNr].prn]

    # Add wrapping to either end to be able to do early/late
    caCode = np.concatenate(([caCode[1022]],caCode,[caCode[0]]))

    blksize_ = int(settings.samplingFreq * 1e-3 + 10)
    #number of samples to seek ahead in file
    samplesPerCodeChip = int(round(settings.samplingFreq / settings.codeFreqBasis))
    numSamplesToSkip = settings.skipNumberOfBytes + channel[channelNr].code_phase*samplesPerCodeChip

    #Process the specified number of ms
    for loopCnt in range(settings.msToProcess):
      if pbar:
        pbar.update(loopCnt + channelNr*settings.msToProcess, attr={'chan': channelNr+1})

      codePhaseStep = loop_filter.code_freq/settings.samplingFreq
      rawSignal = signal[numSamplesToSkip:]#[:blksize_]

      I_E, Q_E, I_P, Q_P, I_L, Q_L, blksize, remCodePhase, remCarrPhase = trk(rawSignal, loop_filter.code_freq, remCodePhase, loop_filter.carr_freq, remCarrPhase, caCode, settings)
      numSamplesToSkip += blksize

      E = I_E + Q_E*1.j
      P = I_P + Q_P*1.j
      L = I_L + Q_L*1.j
      loop_filter.update(E, P, L)

      track_result.carrPhase[loopCnt] = remCarrPhase
      track_result.carrFreq[loopCnt] = loop_filter.carr_freq

      track_result.codePhase[loopCnt] = remCodePhase
      track_result.codeFreq[loopCnt] = loop_filter.code_freq

      #Record stuff for postprocessing
      track_result.absoluteSample[loopCnt] = numSamplesToSkip

      track_result.I_E[loopCnt] = I_E
      track_result.I_P[loopCnt] = I_P
      track_result.I_L[loopCnt] = I_L
      track_result.Q_E[loopCnt] = Q_E
      track_result.Q_P[loopCnt] = Q_P
      track_result.Q_L[loopCnt] = Q_L

      track_result.cn0[loopCnt] = cn0_est.update(I_P)

    #Possibility for lock-detection later
    track_result.status = 'T'
    track_results += [track_result]

  if pbar:
    pbar.finish()

  logger.info("Tracking finished")

  return track_results


class TrackResults:
  def __init__(self, n_points):
    self.status = '-'
    self.PRN = None
    self.absoluteSample = np.empty(n_points)
    self.codePhase = np.empty(n_points)
    self.codeFreq = np.empty(n_points)
    self.carrPhase = np.empty(n_points)
    self.carrFreq = np.empty(n_points)
    self.I_E = np.empty(n_points)
    self.I_P = np.empty(n_points)
    self.I_L = np.empty(n_points)
    self.Q_E = np.empty(n_points)
    self.Q_P = np.empty(n_points)
    self.Q_L = np.empty(n_points)
    self.cn0 = np.empty(n_points)


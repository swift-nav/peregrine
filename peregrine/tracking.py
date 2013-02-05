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


def calc_loop_coef(lbw, zeta, k):
  omega_n = lbw*8.0*zeta / (4.0*zeta**2 + 1.0)
  tau1 = k / (omega_n**2)
  tau2 = 2.0 * zeta / omega_n
  return (tau1, tau2)


class LoopFilter:
  def __init__(self, freq, lbw, zeta, k, loop_freq):
    self.freq = freq

    tau1, tau2 = calc_loop_coef(lbw, zeta, k)
    self.igain = 1.0 / (tau1 * loop_freq)
    self.pgain = tau2 / tau1

    self.prev_error = 0

  def update(self, error):
    self.freq += self.pgain * (error - self.prev_error) + \
                 self.igain * error
    self.prev_error = error

    return self.freq


def track(signal, channel, settings, show_progress=True, trk=swiftnav.correlate.track_correlate):
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

    codeFreq = settings.codeFreqBasis
    codeLoop = LoopFilter(codeFreq, 2, 0.7, 1, 1e3)
    remCodePhase = 0.0
    carrFreq = channel[channelNr].carr_freq
    carrLoop = LoopFilter(carrFreq, 25, 0.7, 0.25, 1e3)
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

      codePhaseStep = codeFreq/settings.samplingFreq
      rawSignal = signal[numSamplesToSkip:]#[:blksize_]

      I_E, Q_E, I_P, Q_P, I_L, Q_L, blksize, remCodePhase, remCarrPhase = trk(rawSignal, codeFreq, remCodePhase, carrFreq, remCarrPhase, caCode, settings)
      numSamplesToSkip += blksize

      carrError = math.atan(Q_P/(I_P+1e-10)) / (2.0 * math.pi)
      carrFreq = carrLoop.update(carrError)

      track_result.carrFreq[loopCnt] = carrFreq
      track_result.carrPhase[loopCnt] = remCarrPhase
      track_result.pllDiscr[loopCnt] = carrError

      #Find DLL error and update code NCO
      codeError = -(math.sqrt(I_E*I_E + Q_E*Q_E) - math.sqrt(I_L*I_L + Q_L*Q_L)) / \
                   (math.sqrt(I_E*I_E + Q_E*Q_E) + math.sqrt(I_L*I_L + Q_L*Q_L) + 1e-10)
      codeFreq = codeLoop.update(codeError)

      track_result.codePhase[loopCnt] = remCodePhase
      track_result.codeFreq[loopCnt] = codeFreq
      track_result.dllDiscr[loopCnt] = codeError

      #Record stuff for postprocessing
      track_result.absoluteSample[loopCnt] = numSamplesToSkip

      track_result.I_E[loopCnt] = I_E
      track_result.I_P[loopCnt] = I_P
      track_result.I_L[loopCnt] = I_L
      track_result.Q_E[loopCnt] = Q_E
      track_result.Q_P[loopCnt] = Q_P
      track_result.Q_L[loopCnt] = Q_L

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
    self.dllDiscr     = np.empty(n_points);
    self.pllDiscr     = np.empty(n_points);


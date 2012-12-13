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

import logging
logger = logging.getLogger(__name__)

# Import progressbar if it is available.
_progressbar_available = True
try:
  import progressbar
except ImportError:
  _progressbar_available = False


def calc_loop_coef(lbw, zeta, k):
  omega_n = lbw*8*zeta / (4*zeta**2 + 1)
  tau1 = k / (omega_n**2)
  tau2 = 2.0* zeta / omega_n
  return (tau1, tau2)


def track(signal, channel, settings, show_progress=True, trk=swiftnav.track.track_correlate):
  logger.info("Tracking starting")
  logger.debug("Tracking %d channels, PRNs %s" % (len(channel), [chan.prn+1 for chan in channel]))

  #Create list of tracking channels results (correlations, freqs, etc)
  track_results = [TrackResults(settings.msToProcess) for i in range(len(channel))]
  #Initialize tracking variables
  ##DLL Variables##
  #Define early-late offset
  #Summation interval
  PDIcode = 0.001
  #Filter coefficient values
  (tau1code, tau2code) = calc_loop_coef(settings.dllNoiseBandwidth,
                                        settings.dllDampingRatio, 1.0)
  ##PLL Variables##
  PDIcarr = 0.001
  (tau1carr, tau2carr) = calc_loop_coef(settings.pllNoiseBandwidth,
                                        settings.pllDampingRatio, 0.25)

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
    track_results[channelNr].PRN = channel[channelNr].prn
    #Get a vector with the C/A code sampled 1x/chip
    caCode = caCodes[channel[channelNr].prn]
    #Add wrapping to either end to be able to do early/late
    caCode = np.concatenate(([caCode[1022]],caCode,[caCode[0]]))
    #Initialize phases and frequencies
    codeFreq = settings.codeFreqBasis
    #remCodePhase = 0.0 #residual code phase
    remCodePhase = 0.0 #residual code phase
    carrFreq = channel[channelNr].carr_freq
    carrFreqBasis = channel[channelNr].carr_freq
    remCarrPhase = 0.0 #residual carrier phase

    #code tracking loop parameters
    oldCodeNco = 0.0
    oldCodeError = 0.0

    #carrier/Costas loop parameters
    oldCarrNco = 0.0
    oldCarrError = 0.0

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

      #Find PLL error and update carrier NCO
      #Carrier loop discriminator (phase detector)
      carrError = math.atan(Q_P/(I_P+1e-10)) / (2.0 * math.pi)
      #Carrier loop filter and NCO
      carrNco = oldCarrNco + (tau2carr/tau1carr) * \
                 (carrError-oldCarrError) + carrError*(PDIcarr/tau1carr)
      oldCarrNco = carrNco
      oldCarrError = carrError
      #Modify carrier freq based on NCO
      carrFreq = carrFreqBasis + carrNco
      track_results[channelNr].carrFreq[loopCnt] = carrFreq
      track_results[channelNr].carrPhase[loopCnt] = remCarrPhase

      #Find DLL error and update code NCO
      codeError = (math.sqrt(I_E*I_E + Q_E*Q_E) - math.sqrt(I_L*I_L + Q_L*Q_L)) / \
                   (math.sqrt(I_E*I_E + Q_E*Q_E) + math.sqrt(I_L*I_L + Q_L*Q_L) + 1e-10)
      codeNco = oldCodeNco + (tau2code/tau1code)*(codeError-oldCodeError) \
                   + codeError*(PDIcode/tau1code)
      oldCodeNco = codeNco
      oldCodeError = codeError
      #Code freq based on NCO
      codeFreq = settings.codeFreqBasis - codeNco
      track_results[channelNr].codePhase[loopCnt] = remCodePhase
      track_results[channelNr].codeFreq[loopCnt] = codeFreq

      #Record stuff for postprocessing
      track_results[channelNr].absoluteSample[loopCnt] = numSamplesToSkip

      track_results[channelNr].dllDiscr[loopCnt] = codeError
      track_results[channelNr].dllDiscrFilt[loopCnt] = codeNco
      track_results[channelNr].pllDiscr[loopCnt] = carrError
      track_results[channelNr].pllDiscrFilt[loopCnt] = carrNco

      track_results[channelNr].I_E[loopCnt] = I_E
      track_results[channelNr].I_P[loopCnt] = I_P
      track_results[channelNr].I_L[loopCnt] = I_L
      track_results[channelNr].Q_E[loopCnt] = Q_E
      track_results[channelNr].Q_P[loopCnt] = Q_P
      track_results[channelNr].Q_L[loopCnt] = Q_L

    #Possibility for lock-detection later
    track_results[channelNr].status = 'T'

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
    self.dllDiscrFilt = np.empty(n_points);
    self.pllDiscr     = np.empty(n_points);
    self.pllDiscrFilt = np.empty(n_points);

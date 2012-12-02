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


def track(signal, channel, settings, show_progress=True):
  logger.info("Tracking starting")

  logger.debug("Tracking %d channels, PRNs %s" % (len(channel), [chan.prn+1 for chan in channel]))

  #Create list of tracking channels results (correlations, freqs, etc)
  trackResults = [trackResults_class(settings) for i in range(len(channel))]
  #Initialize tracking variables
  codePeriods = settings.msToProcess
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
    trackResults[channelNr].PRN = channel[channelNr].prn
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

      I_E, Q_E, I_P, Q_P, I_L, Q_L, blksize, remCodePhase, remCarrPhase = swiftnav.track.track_correlate(rawSignal, codeFreq, remCodePhase, carrFreq, remCarrPhase, caCode, settings)
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
      trackResults[channelNr].carrFreq[loopCnt] = carrFreq

      #Find DLL error and update code NCO
      codeError = (math.sqrt(I_E*I_E + Q_E*Q_E) - math.sqrt(I_L*I_L + Q_L*Q_L)) / \
                   (math.sqrt(I_E*I_E + Q_E*Q_E) + math.sqrt(I_L*I_L + Q_L*Q_L) + 1e-10)
      codeNco = oldCodeNco + (tau2code/tau1code)*(codeError-oldCodeError) \
                   + codeError*(PDIcode/tau1code)
      oldCodeNco = codeNco
      oldCodeError = codeError
      #Code freq based on NCO
      codeFreq = settings.codeFreqBasis - codeNco
      trackResults[channelNr].codePhase[loopCnt] = remCodePhase
      trackResults[channelNr].codeFreq[loopCnt] = codeFreq

      #Record stuff for postprocessing
      trackResults[channelNr].absoluteSample[loopCnt] = numSamplesToSkip

      trackResults[channelNr].dllDiscr[loopCnt] = codeError
      trackResults[channelNr].dllDiscrFilt[loopCnt] = codeNco
      trackResults[channelNr].pllDiscr[loopCnt] = carrError
      trackResults[channelNr].pllDiscrFilt[loopCnt] = carrNco

      trackResults[channelNr].I_E[loopCnt] = I_E
      trackResults[channelNr].I_P[loopCnt] = I_P
      trackResults[channelNr].I_L[loopCnt] = I_L
      trackResults[channelNr].Q_E[loopCnt] = Q_E
      trackResults[channelNr].Q_P[loopCnt] = Q_P
      trackResults[channelNr].Q_L[loopCnt] = Q_L

    #Possibility for lock-detection later
    trackResults[channelNr].status = 'T'

  pbar.finish()
  logger.info("Tracking finished")

  return (trackResults, channel)

class trackResults_class:
  def __init__(self,settings):
    self.status = '-'
    self.PRN = 40 #invalid Goldcode number
    self.absoluteSample = np.zeros(settings.msToProcess)
    self.codePhase = np.zeros(settings.msToProcess)
    self.codeFreq = np.inf*np.ones(settings.msToProcess)
    self.carrFreq = np.inf*np.ones(settings.msToProcess)
    self.I_E = np.zeros(settings.msToProcess)
    self.I_P = np.zeros(settings.msToProcess)
    self.I_L = np.zeros(settings.msToProcess)
    self.Q_E = np.zeros(settings.msToProcess)
    self.Q_P = np.zeros(settings.msToProcess)
    self.Q_L = np.zeros(settings.msToProcess)
    self.dllDiscr     = np.inf*np.ones(settings.msToProcess);
    self.dllDiscrFilt = np.inf*np.ones(settings.msToProcess);
    self.pllDiscr     = np.inf*np.ones(settings.msToProcess);
    self.pllDiscrFilt = np.inf*np.ones(settings.msToProcess);

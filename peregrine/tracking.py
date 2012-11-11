#!/usr/bin/python
#--------------------------------------------------------------------------
#                           SoftGNSS v3.0
#
# Copyright (C) Darius Plausinaitis and Dennis M. Akos
# Written by Darius Plausinaitis and Dennis M. Akos
# Converted to Python by Colin Beighley
#--------------------------------------------------------------------------
#This program is free software; you can redistribute it and/or
#modify it under the terms of the GNU General Public License
#as published by the Free Software Foundation; either version 2
#of the License, or (at your option) any later version.
#
#This program is distributed in the hope that it will be useful,
#but WITHOUT ANY WARRANTY; without even the implied warranty of
#MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#GNU General Public License for more details.
#
#You should have received a copy of the GNU General Public License
#along with this program; if not, write to the Free Software
#Foundation, Inc., 51 Franklin Street, Fifth Floor, Boston, MA  02110-1301,
#USA.
#--------------------------------------------------------------------------
import numpy as np
from include.generateCAcode import caCodes
import get_samples
from include.waitbar import Waitbar
import math
from save import save
from include.calcLoopCoef import calcLoopCoef

import swiftnav.track

import logging
logger = logging.getLogger(__name__)

def track(channel, settings):
  logger.info("Tracking starting")
  #Create list of tracking channels results (correlations, freqs, etc)
  trackResults = [trackResults_class(settings) for i in range(len(channel))]
  #Initialize tracking variables
  codePeriods = settings.msToProcess
  ##DLL Variables##
  #Define early-late offset
  #Summation interval
  PDIcode = 0.001
  #Filter coefficient values
  (tau1code, tau2code) = calcLoopCoef(settings.dllNoiseBandwidth,settings.dllDampingRatio,1.0)
  ##PLL Variables##
  PDIcarr = 0.001
  (tau1carr,tau2carr) = calcLoopCoef(settings.pllNoiseBandwidth,settings.pllDampingRatio,0.25)

  progbar = Waitbar(True)

  signal = get_samples.int8(settings.fileName,int(settings.samplingFreq*1e-3*37100), 0)

  #Do tracking for each channel
  for channelNr in range(len(channel)):
    logger.debug("Tracking channel %2d, PRN %2d" % (channelNr, channel[channelNr].PRN))
    trackResults[channelNr].PRN = channel[channelNr].PRN
    #Get a vector with the C/A code sampled 1x/chip
    caCode = caCodes[channel[channelNr].PRN]
    #Add wrapping to either end to be able to do early/late
    caCode = np.concatenate(([caCode[1022]],caCode,[caCode[0]]))
    #Initialize phases and frequencies
    codeFreq = settings.codeFreqBasis
    #remCodePhase = 0.0 #residual code phase
    remCodePhase = 0.0 #residual code phase
    carrFreq = channel[channelNr].carrFreq
    carrFreqBasis = channel[channelNr].carrFreq
    remCarrPhase = 0.0 #residual carrier phase

    #code tracking loop parameters
    oldCodeNco = 0.0
    oldCodeError = 0.0

    #carrier/Costas loop parameters
    oldCarrNco = 0.0
    oldCarrError = 0.0

    blksize_ = int(settings.samplingFreq * 1e-3 + 10)
    #number of samples to seek ahead in file
    numSamplesToSkip = settings.skipNumberOfBytes + channel[channelNr].codePhase

    #Process the specified number of ms
    for loopCnt in range(settings.msToProcess):
      #Update progress every 50 loops
      if loopCnt % 64 == 0:
        progbar.updated(float(loopCnt + channelNr*settings.msToProcess)\
                        / float(len(channel)*settings.msToProcess))
      codePhaseStep = codeFreq/settings.samplingFreq
      rawSignal = signal[:numSamplesToSkip][:blksize_]

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

  logger.info("Tracking finished")

  return (trackResults,channel)

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

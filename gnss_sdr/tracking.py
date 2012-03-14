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
from generateCAcode import generateCAcode
import getSamples
from waitbar import Waitbar

def track(samples, channel, settings):
  #Create list of tracking channels results (correlations, freqs, etc)
  trackResults = [trackResults_class(settings) for i in range(len(channel))]
  #Initialize tracking variables
  codePeriods = settings.msToProcess
  ##DLL Variables##
  #Define early-late offset
  earlyLateSpc = settings.dllCorrelatorSpacing
  #Summation interval
  PDIcode = 0.001
  #Filter coefficient values
  from calcLoopCoef import calcLoopCoef
  (tau1code, tau2code) = calcLoopCoef(settings.dllNoiseBandwidth,settings.dllDampingRatio,0.25)
  ##PLL Variables##
  PDIcarr = 0.001
  (tau1carr,tau2carr) = calcLoopCoef(settings.pllNoiseBandwidth,settings.pllDampingRatio,0.25)
  
  #Progress bar
  progbar = Waitbar(True)
  
  #Do tracking for each channel
  for channelNr in range(len(channel)):
    trackResults[channelNr].PRN = channel[channelNr].PRN
    #Get a vector with the C/A code sampled 1x/chip
    caCode = np.array(generateCAcode(channel[channelNr].PRN))
    #Add wrapping to either end to be able to do early/late
    caCode = np.concatenate(([caCode[1022]],caCode,[caCode[0]]))
    #Initialize phases and frequencies
    codeFreq = settings.codeFreqBasis
    remCodePhase = 0.0 #residual code phase
    carrFreq = channel[channelNr].acquiredFreq
    carrFreqBasis = channel[channelNr].acquiredFreq
    remCarrPhase = 0.0 #residual carrier phase
    
    #code tracking loop parameters
    oldCodeNco = 0.0
    oldCodeError = 0.0
   
    #carrier/Costas loop parameters
    oldCarrNco = 0.0
    oldCarrError = 0.0

    #number of samples to seek ahead in file
    numSamplesToSkip = settings.skipNumberOfBytes + channel[channelNr].codePhase
  
    #Process the specified number of ms
    for loopCnt in range(settings.msToProcess):
      #Update progress bar every 50 loops
      if (np.remainder(loopCnt,50)==0):
        progbar.update((channelNr*settings.msToProcess+loopCnt)/(len(channel)*settings.msToProcess))
      #Update the code phase rate based on code freq and sampling freq
      codePhaseStep = codeFreq/settings.samplingFreq
      blksize = int(np.ceil((settings.codeLength - remCodePhase)/codePhaseStep))
      #Read samples for this integration period
      rawSignal = getSamples.int8(settings.fileName,blksize,numSamplesToSkip)
      numSamplesToSkip = numSamplesToSkip + blksize
      #Define index into early code vector
        tcode = range((remCodePhase-earlyLateSpc))

  return (0,2)

class trackResults_class:
  def __init__(self,settings):
    self.status = '-'
    self.absoluteSample = np.zeros(settings.msToProcess)
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

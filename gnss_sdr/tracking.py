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
import math
from save import save
from calcLoopCoef import calcLoopCoef

import swiftnav.track

def track_correlate_old(rawSignal, codeFreq, remCodePhase, carrFreq, remCarrPhase, caCode, settings):
      earlyLateSpc = settings.dllCorrelatorSpacing
      #Update the code phase rate based on code freq and sampling freq
      codePhaseStep = codeFreq/settings.samplingFreq
      codePhaseStep = codePhaseStep*(10**12) #round it in the same way we are in octave
      codePhaseStep = round(codePhaseStep)
      codePhaseStep = codePhaseStep*(10**(-12))
      blksize = int(math.ceil((settings.codeLength - remCodePhase)/codePhaseStep))
      #Read samples for this integration period
      rawSignal = rawSignal[:blksize]

      #Define index into early code vector
      tcode = np.r_[(remCodePhase-earlyLateSpc) : \
                    (blksize*codePhaseStep+remCodePhase-earlyLateSpc) : \
                    codePhaseStep]
      earlyCode = caCode[np.int_(np.ceil(tcode))]
      #Define index into late code vector
      tcode = np.r_[(remCodePhase+earlyLateSpc) : \
                    (blksize*codePhaseStep+remCodePhase+earlyLateSpc) : \
                    codePhaseStep]
      lateCode = caCode[np.int_(np.ceil(tcode))]
      #Define index into prompt code vector
      tcode = np.r_[(remCodePhase) : \
                    (blksize*codePhaseStep+remCodePhase) : \
                    codePhaseStep]
      promptCode = caCode[np.int_(np.ceil(tcode))]

      remCodePhase = (tcode[blksize-1] + codePhaseStep) - 1023

      #Generate the carrier frequency to mix the signal to baseband
      #time = np.r_[0:blksize+1] / settings.samplingFreq #(seconds)
      time = np.arange(0, (blksize+1) / settings.samplingFreq, 1/settings.samplingFreq) #(seconds)

      #Get the argument to sin/cos functions
      trigarg = (carrFreq * 2.0 * math.pi)*time + remCarrPhase
      remCarrPhase = np.remainder(trigarg[blksize],(2*math.pi))

      #Finally compute the signal to mix the collected data to baseband
      carrCos = np.cos(trigarg[0:blksize])
      carrSin = np.sin(trigarg[0:blksize])

      #Mix signals to baseband
      qBasebandSignal = carrCos*rawSignal
      iBasebandSignal = carrSin*rawSignal

      #Get early, prompt, and late I/Q correlations
      I_E = np.sum(earlyCode * iBasebandSignal)
      Q_E = np.sum(earlyCode * qBasebandSignal)
      I_P = np.sum(promptCode * iBasebandSignal)
      Q_P = np.sum(promptCode * qBasebandSignal)
      I_L = np.sum(lateCode * iBasebandSignal)
      Q_L = np.sum(lateCode * qBasebandSignal)

      return (I_E, Q_E, I_P, Q_P, I_L, Q_L, blksize, remCodePhase, remCarrPhase)

def track(samples, channel, settings):
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

  #Do tracking for each channel
  for channelNr in range(len(channel)):
    trackResults[channelNr].PRN = channel[channelNr].PRN
    #Get a vector with the C/A code sampled 1x/chip
    caCode = np.array(generateCAcode(channel[channelNr].PRN))
    #Add wrapping to either end to be able to do early/late
    caCode = np.concatenate(([caCode[1022]],caCode,[caCode[0]]))
    #Initialize phases and frequencies
    codeFreq = settings.codeFreqBasis
    #remCodePhase = 0.0 #residual code phase
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

    blksize_ = int(settings.samplingFreq * 1e-3 + 10)
    #number of samples to seek ahead in file
    numSamplesToSkip = settings.skipNumberOfBytes + channel[channelNr].codePhase

    #Process the specified number of ms
    for loopCnt in range(settings.msToProcess):
      #Update progress every 50 loops
      if (np.remainder(loopCnt,50)==0):
        progbar.updated(float(loopCnt + channelNr*settings.msToProcess)\
                        / float(len(channel)*settings.msToProcess))
#        print "Channel %d/%d, %d/%d ms" % (channelNr+1,len(channel),loopCnt, settings.msToProcess)
      codePhaseStep = codeFreq/settings.samplingFreq
      rawSignal = np.array(getSamples.int8(settings.fileName,blksize_,numSamplesToSkip))

      I_E, Q_E, I_P, Q_P, I_L, Q_L, blksize, remCodePhase, remCarrPhase = swiftnav.track.track_correlate(rawSignal, codeFreq, remCodePhase, carrFreq, remCarrPhase, caCode, settings)
      #I_E, Q_E, I_P, Q_P, I_L, Q_L, blksize, remCodePhase, remCarrPhase = track_correlate_old(rawSignal, codeFreq, remCodePhase, carrFreq, remCarrPhase, caCode, settings)
      numSamplesToSkip += blksize
      #print remCodePhase, remCarrPhase

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

#      print ("tR[%d].absoluteSample[%d] = %d" % (channelNr,loopCnt,trackResults[channelNr].absoluteSample[loopCnt]))
#
#      print ("tR[%d].dllDiscr[%d]       = %f" % (channelNr,loopCnt,trackResults[channelNr].dllDiscr[loopCnt]))
#      print ("tR[%d].dllDiscrFilt[%d]   = %f" % (channelNr,loopCnt,trackResults[channelNr].dllDiscrFilt[loopCnt]))
#      print ("tR[%d].codeFreq[%d]       = %f" % (channelNr,loopCnt,trackResults[channelNr].codeFreq[loopCnt]))
#      print ("tR[%d].pllDiscr[%d]       = %f" % (channelNr,loopCnt,trackResults[channelNr].pllDiscr[loopCnt]))
#      print ("tR[%d].pllDiscrFilt[%d]   = %f" % (channelNr,loopCnt,trackResults[channelNr].pllDiscrFilt[loopCnt]))
#      print ("tR[%d].carrFreq[%d]       = %f" % (channelNr,loopCnt,trackResults[channelNr].carrFreq[loopCnt]))
#
      #print ("tR[%d].I_E[%d] = %f" % (channelNr,loopCnt,trackResults[channelNr].I_E[loopCnt]))
      #print ("tR[%d].I_P[%d] = %f" % (channelNr,loopCnt,trackResults[channelNr].I_P[loopCnt]))
      #print ("tR[%d].I_L[%d] = %f" % (channelNr,loopCnt,trackResults[channelNr].I_L[loopCnt]))
      #print ("tR[%d].Q_E[%d] = %f" % (channelNr,loopCnt,trackResults[channelNr].Q_E[loopCnt]))
      #print ("tR[%d].Q_P[%d] = %f" % (channelNr,loopCnt,trackResults[channelNr].Q_P[loopCnt]))
      #print ("tR[%d].Q_L[%d] = %f" % (channelNr,loopCnt,trackResults[channelNr].Q_L[loopCnt]))
      #print ""

    #Possibility for lock-detection later
    trackResults[channelNr].status = 'T'

  print ""

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

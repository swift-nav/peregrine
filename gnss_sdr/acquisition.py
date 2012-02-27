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
import pylab
import math
from makeCaTable import makeCaTable
#import sys
#sys.path.append('./include/');
from generateCAcode import generateCAcode

def acquisition(longSignal,settings):

  # Number of samples per code period
  samplesPerCode = int(round(settings.samplingFreq / (settings.codeFreqBasis / settings.codeLength)))
  
  # Create two 1msec vectors of data to correlate with and one with zero DC
  signal1 = np.array(longSignal[0:samplesPerCode])
  signal2 = np.array(longSignal[samplesPerCode:2*samplesPerCode])
  signal0DC = np.array(longSignal - np.mean(longSignal))
  
  # Find sampling period
  ts = 1/settings.samplingFreq

  # Find phases for the local carrier
  phasePoints = np.array([2*math.pi*i*ts for i in range(0,samplesPerCode)])

  # Number of frequency bins for the given acquisition band (500 Hz steps)
  numberOfFrqBins = int(math.floor(settings.acqSearchBand*1e3/500 + 1))

  # Generate all C/A codes and sample them according to the sampling freq
  caCodesTable = np.array(makeCaTable(settings))

  # Initialize arrays
  results = np.zeros((numberOfFrqBins, samplesPerCode))

  # Carrier frequencies of the frequency bins
  frqBins = np.zeros((numberOfFrqBins))

  # Initialize acqResults
  acqResults = [acqResults_class for i in range(32)]

  print "(",
  
#  for PRN in range(32):
  for PRN in range(1):
#    for frqBinIndex in range(numberOfFrqBins):
    caCodeFreqDom = np.conj(np.fft.fft(caCodesTable[PRN]))
    for frqBinIndex in range(0,1):
      #--- Generate carrier wave frequency grid (0.5kHz step) -----------
      frqBins[frqBinIndex] = settings.IF \
                             - settings.acqSearchBand/2*1000 \
                             + 0.5e3*frqBinIndex
      #--- Generate local sine and cosine -------------------------------
      sinCarr = np.sin(frqBins[frqBinIndex]*phasePoints)
      cosCarr = np.cos(frqBins[frqBinIndex]*phasePoints)
      #--- "Remove carrier" from the signal -----------------------------
      I1 = sinCarr*signal1
      Q1 = cosCarr*signal1
      I2 = sinCarr*signal2
      Q2 = cosCarr*signal2
      #--- Convert the baseband signal to frequency domain --------------
      IQfreqDom1 = np.fft.fft(I1 + 1j*Q1);
      IQfreqDom2 = np.fft.fft(I2 + 1j*Q2);
      #--- Multiplication in frequency <--> correlation in time ---------
      convCodeIQ1 = IQfreqDom1*caCodeFreqDom
      convCodeIQ2 = IQfreqDom2*caCodeFreqDom
      #--- Perform IFFT and store correlation results -------------------
      acqRes1 = abs(np.fft.ifft(convCodeIQ1))**2
      acqRes2 = abs(np.fft.ifft(convCodeIQ2))**2
      #--- Check which msec had the greater power and save that, wil
      #blend 1st and 2nd msec but corrects for nav bit
      if (max(acqRes1) > max(acqRes1)):
        results[frqBinIndex] = acqRes1
      else:
        results[frqBinIndex] = acqRes2

    #--- Find the correlation peak and the carrier frequency ----------
    peakSize = 0 
    for i in range(len(results)):
      if (max(results[i]) > peakSize):
        peakSize = max(results[i])
        frequencyBinIndex = i
    #--- Find the code phase of the same correlation peak -------------
    peakSize = 0
    for i in range(len(results.T)):
      if (max(results.T[i]) > peakSize):
        peakSize = max(results.T[i])
        codePhase = i
    #--- Find 1 chip wide C/A code phase exclude range around the peak
    samplesPerCodeChip = int(round(settings.samplingFreq \
                                   / settings.codeFreqBasis))
    excludeRangeIndex1 = codePhase - samplesPerCodeChip
    excludeRangeIndex2 = codePhase + samplesPerCodeChip
    #--- Correct C/A code phase exclude range if the range includes
    #--- array boundaries
    if (excludeRangeIndex1 < 1):
      codePhaseRange = range(excludeRangeIndex2,samplesPerCode+excludeRangeIndex1+1)
    elif (excludeRangeIndex2 >= (samplesPerCode-1)):
      codePhaseRange = range(excludeRangeIndex2-samplesPerCode,excludeRangeIndex1+1)
    else:
      codePhaseRange = np.concatenate((range(0,excludeRangeIndex1+1),range(excludeRangeIndex2,samplesPerCode)))

    #Find the second highest correlation peak in the same freq bin
    secondPeakSize = 0
    for i in codePhaseRange:
      if (secondPeakSize < results[frequencyBinIndex][i]):
        secondPeakSize = results[frequencyBinIndex][i]
    
    #Store result
    acqResults[PRN].peakMetric = peakSize/secondPeakSize
    
    #If the result is above the threshold, then we have acquired the satellite 
#    if (acqResults[PRN].peakMetric > settings.acqThreshold):
      #Fine resolution frequency search
    print PRN,
      #Generate 8msc long C/A codes sequence for given PRN
    caCode = generateCAcode(PRN)
    codeValueIndex = np.array([int(math.floor(ts*i*settings.codeFreqBasis)) for i in \
                                 range(1,8*samplesPerCode+1)])
    longCaCode = [caCode[i] for i in np.remainder(codeValueIndex,1023)]
    #Remove CA code modulation from the original signal
    xCarrier = signal0DC[]*longCaCode

class acqResults_class:
  carrFreq = 0.0
  codePhase = 0.0
  peakMetric = 0.0

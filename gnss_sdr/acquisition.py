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
  phasePoints = [2*math.pi*i*ts for i in range(0,samplesPerCode)]

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

  print "("
  
#  for PRN in range(0,32):
  for PRN in range(0,1):
    for frqBinIndex in range(0,1):
#    for frqBinIndex in range(0,numberOfFrqBins):
      frqBins[frqBinIndex] = settings.IF - settings.acqSearchBand/2*1000 + \
                             0.5e3 * (frqBinIndex - 1)
  
    

class acqResults_class:
  carrFreq = 0.0
  codePhase = 0.0
  peakMetric = 0.0

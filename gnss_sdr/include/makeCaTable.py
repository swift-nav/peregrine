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

from generateCAcode import generateCAcode
import math
import numpy as np

def makeCaTable(settings):

  # Number of samples per code period
  samplesPerCode = int(round(settings.samplingFreq / (settings.codeFreqBasis / settings.codeLength)))
  
  #Find time constants
  ts = 1/settings.samplingFreq
  tc = 1/settings.codeFreqBasis
  
  #Make array of code value indexes to sample code up to our sampling frequency
  codeValueIndex = np.array([int(math.ceil(ts*i/tc)-1) for i in range(1,samplesPerCode+1)])
  codeValueIndex[len(codeValueIndex)-1] = 1022
  
  #Upsample each PRN and return as a 32 x len(codeValueIndex) list
  caCodesTable = [[0 for i in range(0,1023)] for j in range(0,32)]
  for PRN in range(0,32):
    caCode = generateCAcode(PRN)
    caCodesTable[PRN] = [caCode[i] for i in codeValueIndex]

  return caCodesTable

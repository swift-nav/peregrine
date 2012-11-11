# Copyright (C) 2012 Swift Navigation Inc.
#
# This source is subject to the license found in the file 'LICENSE' which must
# be be distributed together with this source. All other rights reserved.
#
# THIS CODE AND INFORMATION IS PROVIDED "AS IS" WITHOUT WARRANTY OF ANY KIND,
# EITHER EXPRESSED OR IMPLIED, INCLUDING BUT NOT LIMITED TO THE IMPLIED
# WARRANTIES OF MERCHANTABILITY AND/OR FITNESS FOR A PARTICULAR PURPOSE.

from generateCAcode import caCodes
import math
import numpy as np

def makeCaTable(settings):

  # Number of samples per code period
  samplesPerCode = int(round(settings.samplingFreq / (settings.codeFreqBasis / settings.codeLength)))
  
  # Make array of code value indexes to sample code up to our sampling frequency
  codeValueIndex = np.arange(1.0, samplesPerCode+1.0) * \
      settings.codeFreqBasis / settings.samplingFreq
  codeValueIndex = np.remainder(np.asarray(codeValueIndex, np.int), 1023)
  
  # Upsample each PRN and return as a 32 x len(codeValueIndex) array
  caCodesTable = np.empty((32, len(codeValueIndex)))
  for PRN in range(0,32):
    caCodesTable[PRN][:] = caCodes[PRN][codeValueIndex]

  return caCodesTable

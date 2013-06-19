# Copyright (C) 2012 Swift Navigation Inc.
#
# This source is subject to the license found in the file 'LICENSE' which must
# be be distributed together with this source. All other rights reserved.
#
# THIS CODE AND INFORMATION IS PROVIDED "AS IS" WITHOUT WARRANTY OF ANY KIND,
# EITHER EXPRESSED OR IMPLIED, INCLUDING BUT NOT LIMITED TO THE IMPLIED
# WARRANTIES OF MERCHANTABILITY AND/OR FITNESS FOR A PARTICULAR PURPOSE.

class initSettings:
  def __init__(self):
    self.plotTrackingLowInds  = range(1)
    self.plotTrackingLowCorr  = True
    self.plotTrackingLowDisc  = True
    self.plotTrackingNumPts   = 200

    self.msToProcess          = 37000
    self.numberOfChannels     = 8
    self.skipNumberOfBytes    = 16368
    #dataType             = 'int8'
    self.IF                   = 4.092e6        #Hz
    self.samplingFreq         = 16.368e6       #Hz
    self.codeFreqBasis        = 1.023e6        #Hz
    self.codeLength           = 1023
  #  samplesPerCode       = int(round(samplingFreq / (codeFreqBasis / codeLength)))
    self.navSolPeriod         = 500    #ms
    self.elevationMask        = 10     #degrees
    self.useTropCorr          = True
    self.truePositionE        = float('NaN')
    self.truePositionN        = float('NaN')
    self.truePositionU        = float('NaN')
    self.c                    = 299792458
    self.startOffset          = 68.802

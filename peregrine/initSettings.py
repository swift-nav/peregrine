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
    self.skipNumberOfBytes    = 0
    #dataType             = 'int8'
    self.IF                   = 4.092e6   # Hz
    self.samplingFreq         = 16.368e6  # Hz
    self.rxFreqTol            = 2.5e-6    # unitless

    self.acqThreshold         = 20.0    # SNR (unitless)
    self.acqSanityCheck       = True    # Check for sats known to be below the horizon
    self.abortIfInsane        = True    # Abort the whole attempt if sanity check fails
    self.cacheDir             = 'cache'

    self.navSolPeriod         = 500    #ms
    self.elevationMask        = 10     #degrees
    self.useTropCorr          = True
    self.truePositionE        = float('NaN')
    self.truePositionN        = float('NaN')
    self.truePositionU        = float('NaN')

    self.codeFreqBasis        = 1.023e6   # Hz #TODO: redundant with gps_settings
    self.codeLength           = 1023      # TODO: redundant with gps_settings

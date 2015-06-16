# Copyright (C) 2012 Swift Navigation Inc.
#
# This source is subject to the license found in the file 'LICENSE' which must
# be be distributed together with this source. All other rights reserved.
#
# THIS CODE AND INFORMATION IS PROVIDED "AS IS" WITHOUT WARRANTY OF ANY KIND,
# EITHER EXPRESSED OR IMPLIED, INCLUDING BUT NOT LIMITED TO THE IMPLIED
# WARRANTIES OF MERCHANTABILITY AND/OR FITNESS FOR A PARTICULAR PURPOSE.

import defaults

class initSettings:
  def __init__(self):

    self.msToProcess          = 39000
    self.skipNumberOfBytes    = 1000+(16368*87)
    self.IF                   = defaults.IF
    self.samplingFreq         = defaults.sampling_freq
    self.codeFreqBasis        = defaults.chipping_rate
    self.codeLength           = defaults.code_length
    self.acqThreshold         = 21.0    # SNR (unitless)
    self.acqSanityCheck       = True    # Check for sats known to be below the horizon
    self.navSanityMaxResid    = 25.0    # meters per SV, normalized nav residuals
    self.abortIfInsane        = True    # Abort the whole attempt if sanity check fails
    self.useCache             = True
    self.cacheDir             = 'cache'
    self.ephemMaxAge          = 4 * 3600.0 # Reject an ephemeris entry if older than this

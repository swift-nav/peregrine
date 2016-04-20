# Copyright (C) 2016 Swift Navigation Inc.
#
# Contact: Valeri Atamaniouk <valeri@swiftnav.com>
# This source is subject to the license found in the file 'LICENSE' which must
# be be distributed together with this source. All other rights reserved.
#
# THIS CODE AND INFORMATION IS PROVIDED "AS IS" WITHOUT WARRANTY OF ANY KIND,
# EITHER EXPRESSED OR IMPLIED, INCLUDING BUT NOT LIMITED TO THE IMPLIED
# WARRANTIES OF MERCHANTABILITY AND/OR FITNESS FOR A PARTICULAR PURPOSE.
'''
Unit tests for IQgen generator main function
'''

from peregrine.iqgen.generate import generateSamples
from peregrine.iqgen.bits.satellite_gps import GPSSatellite
from peregrine.iqgen.bits.satellite_glo import GLOSatellite
from peregrine.iqgen.if_iface import HighRateConfig
from peregrine.iqgen.bits.encoder_other import GPSGLONASSBitEncoder


def test_generateSamples0():
  '''
  Sample generation test:
  - GPS L1/L2 + GLONASS L1/L2
  - Noise sigma defined
  - Band pass filter type
  - No group delays
  - No process spawning
  '''
  outputFile = file('/dev/null', 'wt')
  logFile = file('/dev/null', 'wt')

  sv0 = GPSSatellite(1)
  sv0.setL1CAEnabled(True)
  sv0.setL2CEnabled(True)
  sv1 = GLOSatellite(0)
  sv1.setL1Enabled(True)
  sv1.setL2Enabled(True)
  sv_list = [sv0, sv1]

  outputConfig = HighRateConfig
  encoder = GPSGLONASSBitEncoder(outputConfig)
  time0S = 0.
  nSamples = HighRateConfig.SAMPLE_BATCH_SIZE + 10000
  noiseSigma = 1.
  tcxo = None
  filterType = 'bandpass'
  groupDelays = False
  threadCount = 0

  class Pbar(object):

    def update(self, value):
      pass

  pbar = Pbar()

  # Execute main sample generation function with all supported SV types and
  # bands. An error shall lead to the test failure.
  # This time execution is performed in the test process.
  generateSamples(outputFile,
                  sv_list,
                  encoder,
                  time0S,
                  nSamples,
                  outputConfig,
                  noiseSigma,
                  tcxo,
                  filterType,
                  groupDelays,
                  logFile,
                  threadCount,
                  pbar)


def test_generateSamples1():
  '''
  Sample generation test:
  - GPS L1/L2 + GLONASS L1/L2
  - No noise
  - Low pass filter type
  - No group delays
  - Two process spawning
  '''
  outputFile = file('/dev/null', 'wt')
  logFile = file('/dev/null', 'wt')

  sv0 = GPSSatellite(1)
  sv0.setL1CAEnabled(True)
  sv0.setL2CEnabled(True)
  sv1 = GLOSatellite(0)
  sv1.setL1Enabled(True)
  sv1.setL2Enabled(True)
  sv_list = [sv0, sv1]

  outputConfig = HighRateConfig
  encoder = GPSGLONASSBitEncoder(outputConfig)
  time0S = 0.
  nSamples = 9999
  noiseSigma = None
  tcxo = None
  filterType = 'lowpass'
  groupDelays = False
  threadCount = 2
  pbar = None

  # Execute main sample generation function with all supported SV types and
  # bands. An error shall lead to the test failure.
  # This time execution is performed in a separate process.
  generateSamples(outputFile,
                  sv_list,
                  encoder,
                  time0S,
                  nSamples,
                  outputConfig,
                  noiseSigma,
                  tcxo,
                  filterType,
                  groupDelays,
                  logFile,
                  threadCount,
                  pbar)

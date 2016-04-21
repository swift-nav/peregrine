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
Unit tests for IQgen GLONASS SV type
'''

from peregrine.iqgen.bits.amplitude_base import AmplitudeBase, NoiseParameters
from peregrine.iqgen.bits.doppler_base import DopplerBase

from peregrine.iqgen.bits.satellite_base import Satellite as SVBase
from peregrine.iqgen.bits.satellite_glo import GLOSatellite
from peregrine.iqgen.if_iface import NormalRateConfig
from peregrine.iqgen.bits.message_glo import Message as GLOMessage
import numpy


def test_GLOSv_init():
  '''
  GLONASS SV initialization test
  '''
  sv = GLOSatellite(1)
  assert isinstance(sv, SVBase)
  assert sv.prn == 1
  assert sv.svName == "GLONASS1"
  assert isinstance(sv.amplitude, AmplitudeBase)
  assert isinstance(sv.doppler, DopplerBase)


def test_GLOSV_bands():
  '''
  GLONASS SV band configurations
  '''
  sv = GLOSatellite(1)
  assert not sv.isBandEnabled(NormalRateConfig.GPS.L1, NormalRateConfig)
  assert not sv.isBandEnabled(NormalRateConfig.GPS.L2, NormalRateConfig)
  assert not sv.isBandEnabled(NormalRateConfig.GLONASS.L1, NormalRateConfig)
  assert not sv.isBandEnabled(NormalRateConfig.GLONASS.L2, NormalRateConfig)
  assert not sv.isL1Enabled()
  assert not sv.isL2Enabled()
  sv.setL1Enabled(True)
  assert sv.isBandEnabled(NormalRateConfig.GLONASS.L1, NormalRateConfig)
  assert not sv.isBandEnabled(NormalRateConfig.GLONASS.L2, NormalRateConfig)
  assert sv.isL1Enabled()
  assert not sv.isL2Enabled()
  sv.setL2Enabled(True)
  sv.setL1Enabled(False)
  assert not sv.isBandEnabled(NormalRateConfig.GLONASS.L1, NormalRateConfig)
  assert sv.isBandEnabled(NormalRateConfig.GLONASS.L2, NormalRateConfig)
  assert not sv.isL1Enabled()
  assert sv.isL2Enabled()


def test_GLOSV_messages():
  '''
  GLONASS SV messages test
  '''
  sv = GLOSatellite(1)
  assert sv.l1Message == sv.getL1Message()
  assert sv.l2Message == sv.getL2Message()
  msg = GLOMessage(1)
  sv.setL1Message(msg)
  assert sv.l1Message == sv.getL1Message() == msg
  assert sv.l2Message == sv.getL2Message() == msg
  msg2 = GLOMessage(3)
  sv.setL2Message(msg)
  assert sv.l1Message == sv.getL1Message() != msg2
  assert sv.l2Message == sv.getL2Message() != msg2


def test_GLOSV_str():
  '''
  GLONASS SV string representation
  '''
  sv = GLOSatellite(3)
  value = str(sv)
  assert value.find('GLONASS') >= 0
  assert value.find('3') >= 0


def test_GLOSv_getBatchSignals0():
  '''
  GLONASS SV signal generation: not enabled
  '''
  sv = GLOSatellite(1)
  start = 0.
  stop = start + (100. / float(NormalRateConfig.SAMPLE_RATE_HZ))
  userTimeAll_s = numpy.linspace(
      start, stop, 100, endpoint=False, dtype=numpy.float)
  samples = numpy.zeros((4, 100))
  noiseParams = NoiseParameters(NormalRateConfig.SAMPLE_RATE_HZ, 1.0)
  result = sv.getBatchSignals(userTimeAll_s,
                              samples,
                              NormalRateConfig,
                              noiseParams,
                              NormalRateConfig.GLONASS.L1,
                              False)
  assert len(result) == 0
  assert (samples == 0).all()


def test_GLOSv_getBatchSignals1():
  '''
  GLONASS SV signal generation: not available
  '''
  sv = GLOSatellite(1)
  start = 0.
  stop = start + (100. / float(NormalRateConfig.SAMPLE_RATE_HZ))
  userTimeAll_s = numpy.linspace(
      start, stop, 100, endpoint=False, dtype=numpy.float)
  samples = numpy.zeros((4, 100))
  noiseParams = NoiseParameters(NormalRateConfig.SAMPLE_RATE_HZ, 1.0)
  result = sv.getBatchSignals(userTimeAll_s,
                              samples,
                              NormalRateConfig,
                              noiseParams,
                              NormalRateConfig.GPS.L1,
                              False)
  assert len(result) == 0
  assert (samples == 0).all()


def test_GLOSv_getBatchSignals2():
  '''
  GLONASS SV signal generation: L1
  '''
  sv = GLOSatellite(1)
  start = 0.
  stop = start + (100. / float(NormalRateConfig.SAMPLE_RATE_HZ))
  userTimeAll_s = numpy.linspace(
      start, stop, 100, endpoint=False, dtype=numpy.float)
  samples = numpy.zeros((4, 100))
  noiseParams = NoiseParameters(NormalRateConfig.SAMPLE_RATE_HZ, 1.0)
  sv.setL1Enabled(True)
  result = sv.getBatchSignals(userTimeAll_s,
                              samples,
                              NormalRateConfig,
                              noiseParams,
                              NormalRateConfig.GLONASS.L1,
                              False)
  assert len(result) == 1
  assert result[0]['type'] == 'GLOL1'
  assert result[0]['doppler'] is None
  assert (samples[0] == 0).all()
  assert (samples[1] == 0).all()
  assert (samples[2] != 0).any()
  assert (samples[3] == 0).all()


def test_GLOSv_getBatchSignals3():
  '''
  GLONASS SV signal generation: L2
  '''
  sv = GLOSatellite(1)
  start = 0.
  stop = start + (100. / float(NormalRateConfig.SAMPLE_RATE_HZ))
  userTimeAll_s = numpy.linspace(
      start, stop, 100, endpoint=False, dtype=numpy.float)
  samples = numpy.zeros((4, 100))
  noiseParams = NoiseParameters(NormalRateConfig.SAMPLE_RATE_HZ, 1.0)
  sv.setL2Enabled(True)
  result = sv.getBatchSignals(userTimeAll_s,
                              samples,
                              NormalRateConfig,
                              noiseParams,
                              NormalRateConfig.GLONASS.L2,
                              False)
  assert len(result) == 1
  assert result[0]['type'] == 'GLOL2'
  assert result[0]['doppler'] is None
  assert (samples[0] == 0).all()
  assert (samples[1] == 0).all()
  assert (samples[2] == 0).all()
  assert (samples[3] != 0).any()

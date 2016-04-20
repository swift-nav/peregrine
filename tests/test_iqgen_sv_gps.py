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
Unit tests for IQgen GPS SV type
'''

from peregrine.iqgen.bits.amplitude_base import AmplitudeBase, NoiseParameters
from peregrine.iqgen.bits.doppler_base import DopplerBase

from peregrine.iqgen.bits.satellite_base import Satellite as SVBase
from peregrine.iqgen.bits.satellite_gps import GPSSatellite
from peregrine.iqgen.if_iface import NormalRateConfig
from peregrine.iqgen.bits.message_lnav import Message as LNavMessage
from peregrine.iqgen.bits.message_cnav import Message as CNavMessage
import numpy


def test_GPSSv_init():
  '''
  GPS SV initialization test
  '''
  sv = GPSSatellite(1)
  assert isinstance(sv, SVBase)
  assert sv.prn == 1
  assert sv.svName == "GPS1"
  assert isinstance(sv.amplitude, AmplitudeBase)
  assert isinstance(sv.doppler, DopplerBase)


def test_GPSSV_bands():
  '''
  GPS SV band configurations
  '''
  sv = GPSSatellite(1)
  assert not sv.isBandEnabled(NormalRateConfig.GPS.L1, NormalRateConfig)
  assert not sv.isBandEnabled(NormalRateConfig.GPS.L2, NormalRateConfig)
  assert not sv.isBandEnabled(NormalRateConfig.GLONASS.L1, NormalRateConfig)
  assert not sv.isBandEnabled(NormalRateConfig.GLONASS.L2, NormalRateConfig)
  assert not sv.isL1CAEnabled()
  assert not sv.isL2CEnabled()
  sv.setL1CAEnabled(True)
  assert sv.isBandEnabled(NormalRateConfig.GPS.L1, NormalRateConfig)
  assert not sv.isBandEnabled(NormalRateConfig.GPS.L2, NormalRateConfig)
  assert sv.isL1CAEnabled()
  assert not sv.isL2CEnabled()
  sv.setL2CEnabled(True)
  sv.setL1CAEnabled(False)
  assert not sv.isBandEnabled(NormalRateConfig.GPS.L1, NormalRateConfig)
  assert sv.isBandEnabled(NormalRateConfig.GPS.L2, NormalRateConfig)
  assert not sv.isL1CAEnabled()
  assert sv.isL2CEnabled()


def test_GPSSV_messages():
  '''
  GPS SV messages test
  '''
  sv = GPSSatellite(1)
  assert sv.l1caMessage == sv.getL1CAMessage()
  assert sv.l2cMessage == sv.getL2CMessage()
  lnav = LNavMessage(1)
  cnav = CNavMessage(1)
  sv.setL1CAMessage(lnav)
  sv.setL2CMessage(cnav)
  assert sv.l1caMessage == sv.getL1CAMessage() == lnav
  assert sv.l2cMessage == sv.getL2CMessage() == cnav


def test_GPSSV_l2clCodeType():
  '''
  GPS SV L2CL code variants
  '''
  sv = GPSSatellite(1)
  sv.setL2CLCodeType('0')
  assert sv.l2clCodeType == '0'
  prn = sv.l2clCodeType
  sv.setL2CLCodeType('0')
  assert sv.l2clCodeType == '0' == sv.getL2CLCodeType()
  assert prn == sv.l2clCodeType
  assert (sv.l2cCode.binCode[1::2] == 0).all()
  sv.setL2CLCodeType('1')
  assert sv.l2clCodeType == '1' == sv.getL2CLCodeType()
  assert prn != sv.l2clCodeType
  assert (sv.l2cCode.binCode[1::2] == 1).all()
  prn = sv.l2clCodeType
  sv.setL2CLCodeType('01')
  assert sv.l2clCodeType == '01' == sv.getL2CLCodeType()
  assert prn != sv.l2clCodeType
  assert (sv.l2cCode.binCode[1::4] == 0).all()
  assert (sv.l2cCode.binCode[3::4] == 1).all()


def test_GPSSV_str():
  '''
  GPS SV string representation
  '''
  sv = GPSSatellite(3)
  value = str(sv)
  assert value.find('GPS') >= 0
  assert value.find('3') >= 0


def test_SVBase_getBatchSignals0():
  '''
  GPS SV signal generation: not enabled
  '''
  sv = GPSSatellite(1)
  start = 0.
  stop = start + (100. / float(NormalRateConfig.SAMPLE_RATE_HZ))
  userTimeAll_s = numpy.linspace(
      start, stop, 100, endpoint=False, dtype=numpy.float)
  samples = numpy.zeros((2, 100))
  noiseParams = NoiseParameters(NormalRateConfig.SAMPLE_RATE_HZ, 1.0)
  result = sv.getBatchSignals(userTimeAll_s,
                              samples,
                              NormalRateConfig,
                              noiseParams,
                              NormalRateConfig.GPS.L1,
                              False)
  assert len(result) == 0
  assert (samples == 0).all()


def test_SVBase_getBatchSignals1():
  '''
  GPS SV signal generation: not available
  '''
  sv = GPSSatellite(1)
  start = 0.
  stop = start + (100. / float(NormalRateConfig.SAMPLE_RATE_HZ))
  userTimeAll_s = numpy.linspace(
      start, stop, 100, endpoint=False, dtype=numpy.float)
  samples = numpy.zeros((2, 100))
  noiseParams = NoiseParameters(NormalRateConfig.SAMPLE_RATE_HZ, 1.0)
  result = sv.getBatchSignals(userTimeAll_s,
                              samples,
                              NormalRateConfig,
                              noiseParams,
                              NormalRateConfig.GLONASS.L1,
                              False)
  assert len(result) == 0
  assert (samples == 0).all()


def test_SVBase_getBatchSignals2():
  '''
  GPS SV signal generation: L1 C/A
  '''
  sv = GPSSatellite(1)
  start = 0.
  stop = start + (100. / float(NormalRateConfig.SAMPLE_RATE_HZ))
  userTimeAll_s = numpy.linspace(
      start, stop, 100, endpoint=False, dtype=numpy.float)
  samples = numpy.zeros((2, 100))
  noiseParams = NoiseParameters(NormalRateConfig.SAMPLE_RATE_HZ, 1.0)
  sv.setL1CAEnabled(True)
  result = sv.getBatchSignals(userTimeAll_s,
                              samples,
                              NormalRateConfig,
                              noiseParams,
                              NormalRateConfig.GPS.L1,
                              False)
  assert len(result) == 1
  assert result[0]['type'] == 'GPSL1'
  assert result[0]['doppler'] is None
  assert (samples[0] != 0).any()
  assert (samples[1] == 0).all()


def test_SVBase_getBatchSignals3():
  '''
  GPS SV signal generation: L2C
  '''
  sv = GPSSatellite(1)
  start = 0.
  stop = start + (100. / float(NormalRateConfig.SAMPLE_RATE_HZ))
  userTimeAll_s = numpy.linspace(
      start, stop, 100, endpoint=False, dtype=numpy.float)
  samples = numpy.zeros((2, 100))
  noiseParams = NoiseParameters(NormalRateConfig.SAMPLE_RATE_HZ, 1.0)
  sv.setL2CEnabled(True)
  result = sv.getBatchSignals(userTimeAll_s,
                              samples,
                              NormalRateConfig,
                              noiseParams,
                              NormalRateConfig.GPS.L2,
                              False)
  assert len(result) == 1
  assert result[0]['type'] == 'GPSL2'
  assert result[0]['doppler'] is None
  assert (samples[0] == 0).all()
  assert (samples[1] != 0).any()

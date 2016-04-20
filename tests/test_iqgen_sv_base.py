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
Unit tests for IQgen base SV type
'''

from peregrine.iqgen.bits.amplitude_base import AmplitudeBase, NoiseParameters
from peregrine.iqgen.bits.amplitude_sine import AmplitudeSine
from peregrine.iqgen.bits.doppler_base import DopplerBase
from peregrine.iqgen.bits.doppler_sine import Doppler as DopplerSine
from peregrine.iqgen.if_iface import NormalRateConfig
from peregrine.iqgen.bits.satellite_base import Satellite as SVBase
import numpy


def test_SVBase_init():
  '''
  Base object construction
  '''
  sv = SVBase("TEST_SV")
  assert sv.svName == "TEST_SV"
  assert isinstance(sv.amplitude, AmplitudeBase)
  assert isinstance(sv.doppler, DopplerBase)


def test_SVBase_amplitude():
  '''
  Amplitude control
  '''
  sv = SVBase("TEST_SV")
  amp = AmplitudeSine(AmplitudeBase.UNITS_POWER, 10, 15, 20)
  sv.setAmplitude(amp)
  assert sv.amplitude == amp
  assert sv.getAmplitude() == amp


def test_SVBase_doppler():
  '''
  Doppler control
  '''
  sv = SVBase("TEST_SV")
  doppler = DopplerSine(10000, 55, 10, 15, 20)
  sv.setDoppler(doppler)
  assert sv.doppler == doppler
  assert sv.getDoppler() == doppler
  assert sv.isCodeDopplerIgnored() == doppler.isCodeDopplerIgnored()
  flag = not sv.isCodeDopplerIgnored()
  sv.setCodeDopplerIgnored(flag)
  assert flag == sv.isCodeDopplerIgnored()


def test_SVBase_str():
  '''
  String representation
  '''
  sv = SVBase("TEST_SV")
  value = str(sv)
  assert value.find('TEST_SV') >= 0


def test_SVBase_isBandEnabled():
  '''
  Base SV class: abstract method test 
  '''
  sv = SVBase("TEST_SV")
  try:
    sv.isBandEnabled(NormalRateConfig.GPS.L1, NormalRateConfig)
    assert False
  except NotImplementedError:
    pass


def test_SVBase_getBatchSignals():
  '''
  Base SV class: abstract method test 
  '''
  sv = SVBase("TEST_SV")
  userTimeAll_s = numpy.zeros(1)
  samples = numpy.zeros(1)
  noiseParams = NoiseParameters(NormalRateConfig.SAMPLE_RATE_HZ, 1.0)
  try:
    sv.getBatchSignals(userTimeAll_s,
                       samples,
                       NormalRateConfig,
                       noiseParams,
                       NormalRateConfig.GPS.L1,
                       False)
    assert False
  except NotImplementedError:
    pass

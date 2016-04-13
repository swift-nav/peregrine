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
Unit tests for IQgen TCXO controls
'''

from peregrine.iqgen.bits.tcxo_base import TCXOBase
from peregrine.iqgen.bits.tcxo_poly import TCXOPoly
from peregrine.iqgen.bits.tcxo_sine import TCXOSine
from peregrine.iqgen.if_iface import NormalRateConfig

import numpy
from scipy.constants import pi

EPSILON = 1e-10


def test_TCXOBase_abstract():
  '''
  Unit test for abstract methods in TCXOBase
  '''
  tcxo = TCXOBase()
  try:
    tcxo.computeTcxoTime(10, 20, NormalRateConfig)
    assert False
  except NotImplementedError:
    pass


def test_TCXOPoly_compute0():
  '''
  Unit test for empty TCXOPoly object
  '''
  tcxo = TCXOPoly(())
  time = tcxo.computeTcxoTime(0, 10, NormalRateConfig)
  assert time is None


def test_TCXOPoly_compute1():
  '''
  Unit test for TCXOPoly with linear time shift (10e-6)
  '''
  tcxo = TCXOPoly((1.,))
  time = tcxo.computeTcxoTime(0, 10, NormalRateConfig)
  test_vector = numpy.linspace(0.,
                               10. * 1e-6 / NormalRateConfig.SAMPLE_RATE_HZ,
                               10.,
                               endpoint=False)
  assert (time == test_vector).all()


def test_TCXOPoly_compute2():
  '''
  Unit test for TCXOPoly with linear time shift (10e-6)
  '''
  tcxo = TCXOPoly((1., 1.))
  time = tcxo.computeTcxoTime(0, 10, NormalRateConfig)
  test_vector = numpy.linspace(0.,
                               10. * 1e-6 / NormalRateConfig.SAMPLE_RATE_HZ,
                               10.,
                               endpoint=False)
  test_vector = test_vector * test_vector / 2. + test_vector
  assert (numpy.abs(time - test_vector) < EPSILON).all()


def test_TCXOSine_compute0():
  '''
  Unit test for TCXOSine object: 0.+sin(2*pi*t/0.004)

  The integral output is: (1. - cos(2*pi*t/0.004))*0.004/(2*pi);
  Minimum value: 0
  Maximum value: 0.002/pi
  '''
  tcxo = TCXOSine(0., 1e6, 0.004)
  time = tcxo.computeTcxoTime(
      0, NormalRateConfig.SAMPLE_RATE_HZ * 0.004 + 1, NormalRateConfig)
  assert time[0] == 0.
  assert time[-1] == 0.
  _max = numpy.max(time)
  _min = numpy.min(time)
  assert numpy.abs(_min) < EPSILON
  assert numpy.abs(_max - 0.004 / pi) < EPSILON
  assert time[NormalRateConfig.SAMPLE_RATE_HZ * 0.002] == _max


def test_TCXOSine_compute1():
  '''
  Unit test for TCXOSine object: 1.+sin(2*pi*t/0.004)

  The integral output is: 1.*t + (1. - cos(2*pi*t/0.004))*0.004/(2*pi);
  After removing the time component:
  Minimum value: 0
  Maximum value: 0.002/pi
  '''
  tcxo = TCXOSine(1e6, 1e6, 0.004)
  time = tcxo.computeTcxoTime(
      0, NormalRateConfig.SAMPLE_RATE_HZ * 0.004 + 1, NormalRateConfig)

  # Remove linear time component
  timeX_s = (NormalRateConfig.SAMPLE_RATE_HZ * 0.004 + 1) / \
      NormalRateConfig.SAMPLE_RATE_HZ
  time -= numpy.linspace(0, timeX_s,
                         NormalRateConfig.SAMPLE_RATE_HZ * 0.004 + 1,
                         endpoint=False)
  assert time[0] == 0.
  assert time[-1] == 0.
  _max = numpy.max(time)
  _min = numpy.min(time)
  assert numpy.abs(_min) < EPSILON
  assert numpy.abs(_max - 0.004 / pi) < EPSILON
  assert time[NormalRateConfig.SAMPLE_RATE_HZ * 0.002] == _max


def test_TCXOPoly_str0():
  '''
  String representation test for polynomial amplitude object
  '''
  value = str(TCXOPoly(()))
  assert value.find('()') >= 0
  assert value.find('Poly') >= 0
  value = str(TCXOPoly((1.,)))
  assert value.find('(1.0,)') >= 0
  assert value.find('Poly') >= 0


def test_TXOSine_str0():
  '''
  String representation test for sine amplitude object
  '''
  value = str(TCXOSine(4., 3., 5.))
  assert value.find('4.') >= 0
  assert value.find('3.') >= 0
  assert value.find('5.') >= 0
  assert value.find('Sine') >= 0

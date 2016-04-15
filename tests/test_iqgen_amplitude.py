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
Unit tests for IQgen amplitude controls
'''

from peregrine.iqgen.bits.amplitude_base import AmplitudeBase
from peregrine.iqgen.bits.amplitude_base import NoiseParameters
from peregrine.iqgen.bits.amplitude_poly import AmplitudePoly
from peregrine.iqgen.bits.amplitude_sine import AmplitudeSine
import numpy

EPSILON = 1e-9


def test_AmplitudeBase_units():
  '''
  Generic tests for AmplitudeBase methods
  '''
  ampl = AmplitudeBase(AmplitudeBase.UNITS_SNR)
  assert AmplitudeBase.UNITS_SNR == ampl.getUnits()
  ampl = AmplitudeBase(AmplitudeBase.UNITS_SNR_DB)
  assert AmplitudeBase.UNITS_SNR_DB == ampl.getUnits()


def test_AmplitudeBase_abstract():
  '''
  Generic tests for AmplitudeBase abstract methods
  '''
  ampl = AmplitudeBase(AmplitudeBase.UNITS_SNR_DB)
  noiseParams = NoiseParameters(1e6, 1.)
  userTimeAll_s = numpy.asarray([0., 1.], dtype=numpy.float)
  signal = numpy.asarray([0., 1.], dtype=numpy.float)
  try:
    ampl.computeSNR(noiseParams)
    assert False
  except NotImplementedError:
    pass
  try:
    ampl.applyAmplitude(signal, userTimeAll_s, noiseParams)
    assert False
  except NotImplementedError:
    pass


def test_AmplitudeBase_convertVolts():
  '''
  Generic tests for AmplitudeBase conversion to volts
  '''
  noiseParams = NoiseParameters(1e6, 1.)
  assert 4. == AmplitudeBase.convertUnits2Amp(4.,
                                              AmplitudeBase.UNITS_AMPLITUDE,
                                              noiseParams)
  assert 2. == AmplitudeBase.convertUnits2Amp(4.,
                                              AmplitudeBase.UNITS_POWER,
                                              noiseParams)
  assert 20. == AmplitudeBase.convertUnits2Amp(100,
                                               AmplitudeBase.UNITS_SNR,
                                               noiseParams)
  assert 2. == AmplitudeBase.convertUnits2Amp(0.,
                                              AmplitudeBase.UNITS_SNR_DB,
                                              noiseParams)


def test_AmplitudeBase_convertSNR():
  '''
  Generic tests for AmplitudeBase conversion to volts
  '''
  noiseParams = NoiseParameters(1e6, 1.)
  assert 10. * numpy.log10(4.) == AmplitudeBase.convertUnits2SNR(4.,
                                                                 AmplitudeBase.UNITS_AMPLITUDE,
                                                                 noiseParams)
  assert 10. * numpy.log10(1.) == AmplitudeBase.convertUnits2SNR(4.,
                                                                 AmplitudeBase.UNITS_POWER,
                                                                 noiseParams)
  assert 20. == AmplitudeBase.convertUnits2SNR(100,
                                               AmplitudeBase.UNITS_SNR,
                                               noiseParams)
  assert 15. == AmplitudeBase.convertUnits2SNR(15.,
                                               AmplitudeBase.UNITS_SNR_DB,
                                               noiseParams)


def test_NoiseParameters():
  '''
  Generic tests for NoiseParameters
  '''
  noiseParams = NoiseParameters(1e6, 1.)
  assert 1e6 == noiseParams.getSamplingFreqHz()
  assert 1. == noiseParams.getNoiseSigma()
  assert 1. == noiseParams.getFreqTimesTau()
  assert 2. == noiseParams.getSignalK()


def test_AmplitudePoly_SNR0():
  '''
  Test AmplitudePoly SNR_0 computation (empty polynomial)
  '''
  noiseParams = NoiseParameters(1e6, 1.)
  ampl = AmplitudePoly(AmplitudeBase.UNITS_AMPLITUDE, ())
  SNR = 10. * numpy.log10(noiseParams.getFreqTimesTau() / 4.)
  assert SNR == ampl.computeSNR(noiseParams)


def test_AmplitudePoly_SNR1():
  '''
  Test AmplitudePoly SNR_0 computation (first order polynomial)
  '''
  noiseParams = NoiseParameters(1e6, 1.)
  ampl = AmplitudePoly(AmplitudeBase.UNITS_AMPLITUDE, (1.,))
  SNR = 10. * numpy.log10(noiseParams.getFreqTimesTau() / 4.)
  assert SNR == ampl.computeSNR(noiseParams)


def test_AmplitudePoly_SNR2():
  '''
  Test AmplitudePoly SNR_0 computation  (second order polynomial)
  '''
  noiseParams = NoiseParameters(1e6, 1.)
  ampl = AmplitudePoly(AmplitudeBase.UNITS_AMPLITUDE, (1., 1.))
  SNR = 10. * numpy.log10(noiseParams.getFreqTimesTau() / 4.)
  assert SNR == ampl.computeSNR(noiseParams)


def test_AmplitudePoly_SNR3():
  '''
  Test AmplitudePoly SNR_0 computation  (second order polynomial, power units)
  '''
  noiseParams = NoiseParameters(1e6, 1.)
  ampl = AmplitudePoly(AmplitudeBase.UNITS_POWER, (1., 1.))
  SNR = 10. * numpy.log10(noiseParams.getFreqTimesTau() / 4.)
  assert SNR == ampl.computeSNR(noiseParams)


def test_AmplitudePoly_SNR4():
  '''
  Test AmplitudePoly SNR_0 computation  (second order polynomial, SNR units)
  '''
  noiseParams = NoiseParameters(1e6, 1.)
  ampl = AmplitudePoly(AmplitudeBase.UNITS_SNR, (1., 1.))
  SNR = 10. * numpy.log10(1.)
  assert SNR == ampl.computeSNR(noiseParams)


def test_AmplitudePoly_SNR5():
  '''
  Test AmplitudePoly SNR_0 computation  (second order polynomial, SNR dB units)
  '''
  noiseParams = NoiseParameters(1e6, 1.)
  ampl = AmplitudePoly(AmplitudeBase.UNITS_SNR_DB, (1., 1.))
  SNR = 1.
  assert SNR == ampl.computeSNR(noiseParams)


def test_AmplitudePoly_apply0():
  '''
  Test AmplitudePoly computation (empty polynomial)
  '''
  noiseParams = NoiseParameters(1e6, 1.)
  ampl = AmplitudePoly(AmplitudeBase.UNITS_AMPLITUDE, ())
  userTimeAll_s = numpy.asarray([0., 1.], dtype=numpy.float)
  signal = numpy.asarray([0., 1.], dtype=numpy.float)
  signal = ampl.applyAmplitude(signal, userTimeAll_s, noiseParams)
  assert (numpy.abs(signal - numpy.asarray([0., 1.], dtype=numpy.float))
          < EPSILON).all()


def test_AmplitudePoly_apply1():
  '''
  Test AmplitudePoly computation (zero order polynomial: 1.0)
  '''
  noiseParams = NoiseParameters(1e6, 1.)
  ampl = AmplitudePoly(AmplitudeBase.UNITS_AMPLITUDE, (1.,))
  userTimeAll_s = numpy.asarray([0., 1.], dtype=numpy.float)
  signal = numpy.asarray([0., 1.], dtype=numpy.float)
  signal = ampl.applyAmplitude(signal, userTimeAll_s, noiseParams)
  assert (numpy.abs(signal - numpy.asarray([0., 1.], dtype=numpy.float))
          < EPSILON).all()


def test_AmplitudePoly_apply2():
  '''
  Test AmplitudePoly computation (first order polynomial: 1.0*t+1.0)
  '''
  noiseParams = NoiseParameters(1e6, 1.)
  ampl = AmplitudePoly(AmplitudeBase.UNITS_AMPLITUDE, (1., 1.))
  userTimeAll_s = numpy.asarray([0., 1.], dtype=numpy.float)
  signal = numpy.asarray([0., 1.], dtype=numpy.float)
  signal = ampl.applyAmplitude(signal, userTimeAll_s, noiseParams)
  assert (numpy.abs(signal - numpy.asarray([0., 2.], dtype=numpy.float))
          < EPSILON).all()


def test_AmplitudeSine_SNR0():
  '''
  Test AmplitudeSine SNR_0 computation (1.+2.*sin(2.*pi*t/1.))
  '''
  noiseParams = NoiseParameters(1e6, 1.)
  ampl = AmplitudeSine(AmplitudeBase.UNITS_AMPLITUDE, 1., 2., 1.)
  SNR = 10. * numpy.log10(noiseParams.getFreqTimesTau() / 4.)
  assert numpy.abs(SNR - ampl.computeSNR(noiseParams)) < EPSILON


def test_AmplitudeSine_apply0():
  '''
  Test AmplitudeSine computation (1.+2.*sin(2.*pi*t/4.))
  '''
  noiseParams = NoiseParameters(1e6, 1.)
  ampl = AmplitudeSine(AmplitudeBase.UNITS_AMPLITUDE, 1., 2., 4.)
  userTimeAll_s = numpy.asarray([0., 1., 2.], dtype=numpy.float)
  signal = numpy.asarray([0., 1., 1.], dtype=numpy.float)
  signal = ampl.applyAmplitude(signal, userTimeAll_s, noiseParams)
  assert (numpy.abs(signal - numpy.asarray([0., 3., 1.], dtype=numpy.float))
          < EPSILON).all()


def test_AmplitudePoly_str0():
  '''
  String representation test for polynomial amplitude object
  '''
  value = str(AmplitudePoly(AmplitudeBase.UNITS_SNR, ()))
  assert value.find('=SNR') >= 0
  assert value.find('()') >= 0
  assert value.find('Poly') >= 0
  value = str(AmplitudePoly(AmplitudeBase.UNITS_AMPLITUDE, (1.,)))
  assert value.find('=AMP') >= 0
  assert value.find('(1.0,)') >= 0
  assert value.find('Poly') >= 0


def test_AmplitudeSine_str0():
  '''
  String representation test for sine amplitude object
  '''
  value = str(AmplitudeSine(AmplitudeBase.UNITS_SNR, 4., 3., 5.))
  assert value.find('SNR') >= 0
  assert value.find('4.') >= 0
  assert value.find('3.') >= 0
  assert value.find('5.') >= 0
  assert value.find('Sine') >= 0

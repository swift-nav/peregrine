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
Unit tests for IQgen doppler controls
'''

from peregrine.iqgen.bits.amplitude_poly import AmplitudePoly
from peregrine.iqgen.bits.amplitude_base import NoiseParameters, AmplitudeBase
from peregrine.iqgen.bits.doppler_base import DopplerBase
from peregrine.iqgen.bits.doppler_poly import Doppler as DopplerPoly
from peregrine.iqgen.bits.doppler_poly import zeroDoppler
from peregrine.iqgen.bits.doppler_poly import constDoppler
from peregrine.iqgen.bits.doppler_poly import linearDoppler
from peregrine.iqgen.bits.doppler_sine import Doppler as DopplerSine
from peregrine.iqgen.bits.doppler_sine import sineDoppler
from peregrine.iqgen.bits.message_const import Message
from peregrine.iqgen.bits.signals import GPS
from peregrine.iqgen.bits.prn_gps_l1ca import PrnCode
from peregrine.iqgen.if_iface import NormalRateConfig
import numpy
import scipy.constants

EPSILON = 1e-9


def test_DopplerBase_CDI():
  '''
  Test CDI flag manipulation
  '''
  doppler = DopplerBase()
  assert not doppler.isCodeDopplerIgnored()
  doppler.setCodeDopplerIgnored(True)
  assert doppler.isCodeDopplerIgnored()


def test_DopplerBase_TEC():
  '''
  Test TEC value manipulation
  '''
  doppler = DopplerBase(tec_epm2=50.)
  assert doppler.computeSignalDelayS(1e9) == 40.3 * 50. / 1e18
  doppler.tec_epm2 = 25.
  assert doppler.computeSignalDelayS(1e9) == 40.3 * 25. / 1e18


def test_DopplerBase_Distance():
  '''
  Test distance value manipulation
  '''
  doppler = DopplerBase(distance0_m=0., tec_epm2=0.)
  assert doppler.computeSignalDelayS(1e9) == 0.
  doppler = DopplerBase(distance0_m=1e6, tec_epm2=0.)
  assert doppler.computeSignalDelayS(1e9) == 1e6 / scipy.constants.c


def test_DopplerBase_applySignalDelay():
  '''
  Test signal delay computation
  '''
  doppler = DopplerBase(tec_epm2=50.)
  userTimeAll_s = numpy.asanyarray([1., 2.], dtype=numpy.float)
  res = doppler.applySignalDelays(userTimeAll_s, GPS.L1CA)
  delay_s = 40.3 * 50. / 1e18
  assert (numpy.abs(res + delay_s - userTimeAll_s) < EPSILON).all()


def test_DopplerBase_computeDistance():
  '''
  Test distance computation
  '''
  doppler = DopplerBase(distance0_m=0., tec_epm2=0.)

  try:
    doppler.computeDistanceM(0.)
    assert False
  except NotImplementedError:
    pass


def test_DopplerBase_computeSpeed():
  '''
  Test speed computation
  '''
  doppler = DopplerBase(distance0_m=0., tec_epm2=0.)
  try:
    doppler.computeSpeedMps(0.)
    assert False
  except NotImplementedError:
    pass


def test_DopplerBase_computeBatch():
  '''
  Test signal generation
  '''
  doppler = DopplerBase(distance0_m=0., tec_epm2=0.)
  userTimeAll_s = numpy.asarray([0.])
  amplitude = AmplitudePoly(AmplitudeBase.UNITS_AMPLITUDE, ())
  noiseParams = NoiseParameters(NormalRateConfig.SAMPLE_RATE_HZ, 0.)
  message = Message(1)
  code = PrnCode(1)
  try:
    doppler.computeBatch(userTimeAll_s,
                         amplitude,
                         noiseParams,
                         GPS.L1CA,
                         NormalRateConfig.GPS.L1.INTERMEDIATE_FREQUENCY_HZ,
                         message,
                         code,
                         NormalRateConfig,
                         False)
    assert False
  except NotImplementedError:
    pass


def test_DopplerBase_computeDeltaUserTimeS():
  '''
  Test time delay
  '''
  time_s = DopplerBase.computeDeltaUserTimeS(0., 24.84375e6, NormalRateConfig)
  assert time_s == 1.


def test_DopplerBase_computeDopplerHz():
  '''
  Test doppler in Hz computation
  '''
  dopplerHz = DopplerBase.computeDopplerHz(1e9, 100.)
  assert numpy.abs(dopplerHz == -1e11 / scipy.constants.c) < EPSILON


def test_DopplerBase_computeDataNChipVector0():
  '''
  Test combination of data and code
  '''
  doppler = DopplerBase()
  chipAll_idx = numpy.linspace(0, 1022, 1023, dtype=numpy.long)
  message = Message(1)
  code = PrnCode(1)
  vect = doppler.computeDataNChipVector(chipAll_idx,
                                        GPS.L1CA,
                                        message,
                                        code)

  assert len(vect) == 1023
  assert ((vect < 0) == code.getCodeBits(chipAll_idx)).all()


def test_DopplerBase_computeDataNChipVector1():
  '''
  Test combination of data and code
  '''
  doppler = DopplerBase()
  chipAll_idx = numpy.linspace(0, 1022, 1023, dtype=numpy.long)
  message = Message(-1)
  code = PrnCode(1)
  vect = doppler.computeDataNChipVector(chipAll_idx,
                                        GPS.L1CA,
                                        message,
                                        code)

  assert len(vect) == 1023
  assert ((vect > 0) == code.getCodeBits(chipAll_idx)).all()


def test_DopplerBase_computeDopplerShiftM():
  '''
  Test computation of phase shift in m for a time 
  '''
  doppler = DopplerBase()
  userTimeAll_s = numpy.asarray([0.], dtype=numpy.float)
  try:
    doppler.computeDopplerShiftHz(userTimeAll_s, GPS.L1CA)
    assert False
  except NotImplementedError:
    pass


def test_DopplerBase_computeDopplerShiftHz():
  '''
  Test computation of doppler shift for a time 
  '''
  doppler = DopplerBase()
  userTimeAll_s = numpy.asarray([0.], dtype=numpy.float)
  try:
    doppler.computeDopplerShiftM(userTimeAll_s)
    assert False
  except NotImplementedError:
    pass


def test_Helper_zeroDoppler():
  '''
  Helper method test
  '''
  doppler = zeroDoppler(1000., 77., 1e9)
  assert isinstance(doppler, DopplerPoly)
  assert doppler.distance0_m == 1000.
  assert doppler.tec_epm2 == 77.
  assert doppler.distanceCoeffs is None
  assert doppler.speedPoly is None


def test_Helper_constDoppler():
  '''
  Helper method test
  '''
  doppler = constDoppler(1000., 77., 1e9, 100.)
  assert isinstance(doppler, DopplerPoly)
  assert doppler.distance0_m == 1000.
  assert doppler.tec_epm2 == 77.
  assert len(doppler.distancePoly.coeffs) == 2
  assert len(doppler.speedPoly.coeffs) == 1

  speed_mps = -scipy.constants.c / 1e7
  speedCoeffs = numpy.asarray([speed_mps], dtype=numpy.float)
  distCoeffs = numpy.asarray([speed_mps, 0.], dtype=numpy.float)

  assert (numpy.abs(doppler.distancePoly.coeffs - distCoeffs) < EPSILON).all()
  assert (numpy.abs(doppler.speedPoly.coeffs == speedCoeffs) < EPSILON).all()


def test_Helper_linearDoppler():
  '''
  Helper method test
  '''
  doppler = linearDoppler(1000., 77., 1e9, 100., 100.)
  assert isinstance(doppler, DopplerPoly)
  assert doppler.distance0_m == 1000.
  assert doppler.tec_epm2 == 77.
  assert len(doppler.distancePoly.coeffs) == 3
  assert len(doppler.speedPoly.coeffs) == 2

  speed_mps = -scipy.constants.c / 1e7
  speedCoeffs = numpy.asarray([speed_mps, speed_mps], dtype=numpy.float)
  distCoeffs = numpy.asarray([speed_mps / 2,
                              speed_mps,
                              0.], dtype=numpy.float)

  assert (numpy.abs(doppler.speedPoly.coeffs - speedCoeffs) < EPSILON).all()
  assert (numpy.abs(doppler.distancePoly.coeffs - distCoeffs) < EPSILON).all()


def test_Helper_sineDoppler():
  '''
  Helper method test
  '''
  doppler = sineDoppler(1000., 77., 1e9, 100., 50., 3.)
  assert isinstance(doppler, DopplerSine)
  assert doppler.distance0_m == 1000.
  assert doppler.tec_epm2 == 77.
  assert doppler.period_s == 3.
  assert numpy.abs(doppler.speed0_mps - -scipy.constants.c / 1e7) < EPSILON
  assert numpy.abs(doppler.amplutude_mps - -scipy.constants.c / 2e7) < EPSILON


def test_DopplerSine_computeDistance():
  '''
  Test distance for sine doppler
  '''
  doppler = DopplerSine(1000., 77., 100., 50., 3.)
  assert abs(1000. - doppler.computeDistanceM(0.)) < EPSILON
  assert abs(1250. - doppler.computeDistanceM(1.5)) < EPSILON
  assert abs(1300. - doppler.computeDistanceM(3.)) < EPSILON


def test_DopplerSine_computeSpeed():
  '''
  Test speed for sine doppler
  '''
  doppler = DopplerSine(1000., 77., 100., 50., 4.)
  assert abs(100. - doppler.computeSpeedMps(0.)) < EPSILON
  assert abs(150. - doppler.computeSpeedMps(1.)) < EPSILON
  assert abs(100. - doppler.computeSpeedMps(2.)) < EPSILON
  assert abs(50. - doppler.computeSpeedMps(3.)) < EPSILON
  assert abs(100. - doppler.computeSpeedMps(4.)) < EPSILON


def test_DopplerSine_computeDopplerShift0():
  '''
  Test distance for sine doppler
  '''
  doppler = DopplerSine(1000., 77., 0., 50., 4.)
  userTimeAll_s = numpy.asarray([0., 1., 2., 3.])
  shift = doppler.computeDopplerShiftM(userTimeAll_s)

  pi = scipy.constants.pi
  assert abs(0. - shift[0]) < EPSILON
  assert abs(0. + 50. * 4. / (2. * pi) - shift[1]) < EPSILON
  assert abs(0. + 2. * 50. * 4. / (2. * pi) - shift[2]) < EPSILON
  assert abs(0. + 50. * 4. / (2. * pi) - shift[3]) < EPSILON


def test_DopplerSine_computeDopplerShift1():
  '''
  Test distance for sine doppler
  '''
  doppler = DopplerSine(1000., 77., 1., 50., 4.)
  userTimeAll_s = numpy.asarray([0., 1., 2., 3.])
  shift = doppler.computeDopplerShiftM(userTimeAll_s)

  pi = scipy.constants.pi
  assert abs(0. - shift[0]) < EPSILON
  assert abs(1. + 50. * 4. / (2. * pi) - shift[1]) < EPSILON
  assert abs(2. + 2. * 50. * 4. / (2. * pi) - shift[2]) < EPSILON
  assert abs(3. + 50. * 4. / (2. * pi) - shift[3]) < EPSILON


def test_DopplerSine_computeDopplerShiftHz():
  '''
  Test distance for sine doppler
  '''
  doppler = sineDoppler(1000.,                        # Distance
                        45.,                          # TEC
                        GPS.L1CA.CENTER_FREQUENCY_HZ,  # F
                        100.,                         # Offset Hz
                        50.,                          # Amplitude Hz
                        4.)                           # Period s
  userTimeAll_s = numpy.asarray([0., 1., 2., 3.])
  shift = doppler.computeDopplerShiftHz(userTimeAll_s, GPS.L1CA)

  assert abs(100. - shift[0]) < EPSILON
  assert abs(150. - shift[1]) < EPSILON
  assert abs(100. - shift[2]) < EPSILON
  assert abs(50. - shift[3]) < EPSILON


def test_DopplerPoly_computeDistance0():
  '''
  Test distance for empty polynomial doppler
  '''
  doppler = DopplerPoly(1000., 77., ())
  assert abs(0. - doppler.computeDistanceM(0.)) < EPSILON
  assert abs(0. - doppler.computeDistanceM(1.5)) < EPSILON
  assert abs(0. - doppler.computeDistanceM(3.)) < EPSILON


def test_DopplerPoly_computeDistance1():
  '''
  Test distance for zero order polynomial doppler
  '''
  doppler = DopplerPoly(1000., 77., (1.,))
  assert abs(0. - doppler.computeDistanceM(0.)) < EPSILON
  assert abs(1.5 - doppler.computeDistanceM(1.5)) < EPSILON
  assert abs(3. - doppler.computeDistanceM(3.)) < EPSILON


def test_DopplerPoly_computeDistance2():
  '''
  Test distance for first order polynomial doppler
  '''
  doppler = DopplerPoly(1000., 77., (1., 1.))
  assert abs(0. - doppler.computeDistanceM(0.)) < EPSILON
  assert abs(1.5 - doppler.computeDistanceM(1.)) < EPSILON
  assert abs(7.5 - doppler.computeDistanceM(3.)) < EPSILON


def test_DopplerPoly_computeSpeed0():
  '''
  Test speed for empty polynomial doppler
  '''
  doppler = DopplerPoly(1000., 77., ())
  assert abs(0. - doppler.computeSpeedMps(0.)) < EPSILON
  assert abs(0. - doppler.computeSpeedMps(1.)) < EPSILON
  assert abs(0. - doppler.computeSpeedMps(2.)) < EPSILON


def test_DopplerPoly_computeSpeed1():
  '''
  Test speed for zero order polynomial doppler
  '''
  doppler = DopplerPoly(1000., 77., (1.,))
  assert abs(1. - doppler.computeSpeedMps(0.)) < EPSILON
  assert abs(1. - doppler.computeSpeedMps(1.)) < EPSILON
  assert abs(1. - doppler.computeSpeedMps(2.)) < EPSILON


def test_DopplerPoly_computeSpeed2():
  '''
  Test speed for first order polynomial doppler
  '''
  doppler = DopplerPoly(1000., 77., (1., 1.))
  assert abs(1. - doppler.computeSpeedMps(0.)) < EPSILON
  assert abs(2. - doppler.computeSpeedMps(1.)) < EPSILON
  assert abs(3. - doppler.computeSpeedMps(2.)) < EPSILON


def test_DopplerPoly_computeDopplerShift0():
  '''
  Test distance for empty polynomial doppler
  '''
  doppler = DopplerPoly(1000., 77., ())
  userTimeAll_s = numpy.asarray([0., 1., 2., 3.])
  shift = doppler.computeDopplerShiftM(userTimeAll_s)

  assert abs(0. - shift[0]) < EPSILON
  assert abs(0. - shift[1]) < EPSILON
  assert abs(0. - shift[2]) < EPSILON
  assert abs(0. - shift[3]) < EPSILON


def test_DopplerPoly_computeDopplerShift1():
  '''
  Test distance for zero order polynomial doppler
  '''
  doppler = DopplerPoly(1000., 77., (1.,))
  userTimeAll_s = numpy.asarray([0., 1., 2., 3.])
  shift = doppler.computeDopplerShiftM(userTimeAll_s)

  assert abs(0. - shift[0]) < EPSILON
  assert abs(1. - shift[1]) < EPSILON
  assert abs(2. - shift[2]) < EPSILON
  assert abs(3. - shift[3]) < EPSILON


def test_DopplerPoly_computeDopplerShift2():
  '''
  Test distance for first order polynomial doppler
  '''
  doppler = DopplerPoly(1000., 77., (1., 1.))
  userTimeAll_s = numpy.asarray([0., 1., 2., 3.])
  shift = doppler.computeDopplerShiftM(userTimeAll_s)

  assert abs(0. - shift[0]) < EPSILON
  assert abs(1.5 - shift[1]) < EPSILON
  assert abs(4. - shift[2]) < EPSILON
  assert abs(7.5 - shift[3]) < EPSILON


def test_DopplerPoly_computeDopplerShiftHz0():
  '''
  Test phase shift for empty polynomial doppler
  '''
  doppler = DopplerPoly(1000., 50., ())
  userTimeAll_s = numpy.asarray([0., 1., 2., 3.])
  shift = doppler.computeDopplerShiftHz(userTimeAll_s, GPS.L1CA)

  assert abs(0. - shift[0]) < EPSILON
  assert abs(0. - shift[1]) < EPSILON
  assert abs(0. - shift[2]) < EPSILON
  assert abs(0. - shift[3]) < EPSILON


def test_DopplerPoly_computeDopplerShiftHz1():
  '''
  Test phase shift for zero order polynomial doppler
  '''
  doppler = constDoppler(1000.,                         # Distance
                         45.,                           # TEC
                         GPS.L1CA.CENTER_FREQUENCY_HZ,  # F
                         1.)                            # constant Hz
  userTimeAll_s = numpy.asarray([0., 1., 2., 3.])
  shift = doppler.computeDopplerShiftHz(userTimeAll_s, GPS.L1CA)

  assert abs(1. - shift[0]) < EPSILON
  assert abs(1. - shift[1]) < EPSILON
  assert abs(1. - shift[2]) < EPSILON
  assert abs(1. - shift[3]) < EPSILON


def test_DopplerPoly_computeDopplerShiftHz2():
  '''
  Test phase shift for first order polynomial doppler
  '''
  doppler = linearDoppler(1000.,                         # Distance
                          45.,                           # TEC
                          GPS.L1CA.CENTER_FREQUENCY_HZ,  # F
                          1.,                            # constant Hz
                          1.)                            # acceleration Hz/s
  userTimeAll_s = numpy.asarray([0., 1., 2., 3.])
  shift = doppler.computeDopplerShiftHz(userTimeAll_s, GPS.L1CA)

  assert abs(1. - shift[0]) < EPSILON
  assert abs(2. - shift[1]) < EPSILON
  assert abs(3. - shift[2]) < EPSILON
  assert abs(4. - shift[3]) < EPSILON


def test_DopplerPoly_str0():
  '''
  String representation test for polynomial doppler object
  '''
  value = str(DopplerPoly(1000., 55., ()))
  assert value.find('1000.') >= 0
  assert value.find('55.') >= 0
  assert value.find('()') >= 0
  assert value.find('Poly') >= 0
  value = str(DopplerPoly(1000., 55., (1.,)))
  assert value.find('1000.') >= 0
  assert value.find('55.') >= 0
  assert value.find('(1.0,)') >= 0


def test_DopplerSine_str0():
  '''
  String representation test for sine doppler object
  '''
  value = str(DopplerSine(1000., 55., 4., 3., 5.))
  assert value.find('1000.') >= 0
  assert value.find('55.') >= 0
  assert value.find('4.') >= 0
  assert value.find('3.') >= 0
  assert value.find('5.') >= 0
  assert value.find('Sine') >= 0


def test_DopplerZero_batch():
  '''
  Verifies execution of the batch computation with zero doppler.
  '''
  doppler = zeroDoppler(1000., 50., GPS.L1CA.CENTER_FREQUENCY_HZ)
  userTimeAll_s = numpy.linspace(0.,
                                 NormalRateConfig.SAMPLE_BATCH_SIZE /
                                 NormalRateConfig.SAMPLE_RATE_HZ,
                                 NormalRateConfig.SAMPLE_BATCH_SIZE,
                                 endpoint=False)
  amplitude = AmplitudePoly(AmplitudeBase.UNITS_AMPLITUDE, ())
  noiseParams = NoiseParameters(GPS.L1CA.CENTER_FREQUENCY_HZ, 0.)
  message = Message(1)
  code = PrnCode(1)
  res = doppler.computeBatch(userTimeAll_s,
                             amplitude,
                             noiseParams,
                             GPS.L1CA,
                             NormalRateConfig.GPS.L1.INTERMEDIATE_FREQUENCY_HZ,
                             message,
                             code,
                             NormalRateConfig,
                             True)

  signal1, doppler1 = res

  doppler.setCodeDopplerIgnored(True)
  res = doppler.computeBatch(userTimeAll_s,
                             amplitude,
                             noiseParams,
                             GPS.L1CA,
                             NormalRateConfig.GPS.L1.INTERMEDIATE_FREQUENCY_HZ,
                             message,
                             code,
                             NormalRateConfig,
                             True)
  signal2, doppler2 = res

  assert (signal1 == signal2).all()
  assert (doppler1 == doppler2).all()


def test_DopplerConst_batch():
  '''
  Verifies execution of the batch computation with const doppler.
  '''
  doppler = constDoppler(1000., 50., GPS.L1CA.CENTER_FREQUENCY_HZ, 100.)
  userTimeAll_s = numpy.linspace(10.,
                                 10. +
                                 NormalRateConfig.SAMPLE_BATCH_SIZE /
                                 NormalRateConfig.SAMPLE_RATE_HZ,
                                 NormalRateConfig.SAMPLE_BATCH_SIZE,
                                 endpoint=False)
  amplitude = AmplitudePoly(AmplitudeBase.UNITS_AMPLITUDE, ())
  noiseParams = NoiseParameters(GPS.L1CA.CENTER_FREQUENCY_HZ, 0.)
  message = Message(1)
  code = PrnCode(1)
  res = doppler.computeBatch(userTimeAll_s,
                             amplitude,
                             noiseParams,
                             GPS.L1CA,
                             NormalRateConfig.GPS.L1.INTERMEDIATE_FREQUENCY_HZ,
                             message,
                             code,
                             NormalRateConfig,
                             True)
  signal1, doppler1 = res
  doppler.setCodeDopplerIgnored(True)
  res = doppler.computeBatch(userTimeAll_s,
                             amplitude,
                             noiseParams,
                             GPS.L1CA,
                             NormalRateConfig.GPS.L1.INTERMEDIATE_FREQUENCY_HZ,
                             message,
                             code,
                             NormalRateConfig,
                             True)
  signal2, doppler2 = res
  assert (doppler1 == doppler2).all()
  assert (signal1 != signal2).any()

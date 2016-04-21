# Copyright (C) 2016 Swift Navigation Inc.
#
# Contact: Valeri Atamaniouk <valeri@swiftnav.com>
# This source is subject to the license found in the file 'LICENSE' which must
# be be distributed together with this source. All other rights reserved.
#
# THIS CODE AND INFORMATION IS PROVIDED "AS IS" WITHOUT WARRANTY OF ANY KIND,
# EITHER EXPRESSED OR IMPLIED, INCLUDING BUT NOT LIMITED TO THE IMPLIED
# WARRANTIES OF MERCHANTABILITY AND/OR FITNESS FOR A PARTICULAR PURPOSE.
import sys
'''
Unit tests for IQgen program entry point and utilities
'''

# SV
from peregrine.iqgen.bits.satellite_gps import GPSSatellite
from peregrine.iqgen.bits.satellite_glo import GLOSatellite

# Profiles
from peregrine.iqgen.if_iface import LowRateConfig
from peregrine.iqgen.if_iface import NormalRateConfig
from peregrine.iqgen.if_iface import HighRateConfig
from peregrine.iqgen.if_iface import CustomRateConfig

from peregrine.iqgen.iqgen_main import computeTimeDelay
from peregrine.iqgen.iqgen_main import prepareArgsParser
from peregrine.iqgen.iqgen_main import selectOutputConfig
from peregrine.iqgen.iqgen_main import printOutputConfig
from peregrine.iqgen.iqgen_main import computeEnabledBands
from peregrine.iqgen.iqgen_main import selectEncoder
from peregrine.iqgen.iqgen_main import makeProgressBar
from peregrine.iqgen.bits.doppler_poly import Doppler as DopplerPoly
from peregrine.iqgen.bits.doppler_sine import Doppler as DopplerSine
from peregrine.iqgen.bits.signals import GPS

# Message data
from peregrine.iqgen.bits.message_const import Message as ConstMessage
from peregrine.iqgen.bits.message_zeroone import Message as ZeroOneMessage
from peregrine.iqgen.bits.message_cnav import Message as CNavMessage
from peregrine.iqgen.bits.message_lnav import Message as LNavMessage
from peregrine.iqgen.bits.message_glo import Message as GLOMessage

from peregrine.iqgen.bits.amplitude_poly import AmplitudePoly
from peregrine.iqgen.bits.amplitude_sine import AmplitudeSine

# Bit stream encoders
from peregrine.iqgen.bits.encoder_gps import GPSL1BitEncoder
from peregrine.iqgen.bits.encoder_gps import GPSL2BitEncoder
from peregrine.iqgen.bits.encoder_gps import GPSL1L2BitEncoder
from peregrine.iqgen.bits.encoder_gps import GPSL1TwoBitsEncoder
from peregrine.iqgen.bits.encoder_gps import GPSL2TwoBitsEncoder
from peregrine.iqgen.bits.encoder_gps import GPSL1L2TwoBitsEncoder

from peregrine.iqgen.bits.encoder_glo import GLONASSL1BitEncoder
from peregrine.iqgen.bits.encoder_glo import GLONASSL2BitEncoder
from peregrine.iqgen.bits.encoder_glo import GLONASSL1L2BitEncoder
from peregrine.iqgen.bits.encoder_glo import GLONASSL1TwoBitsEncoder
from peregrine.iqgen.bits.encoder_glo import GLONASSL2TwoBitsEncoder
from peregrine.iqgen.bits.encoder_glo import GLONASSL1L2TwoBitsEncoder

from peregrine.iqgen.bits.encoder_other import GPSGLONASSBitEncoder
from peregrine.iqgen.bits.encoder_other import GPSGLONASSTwoBitsEncoder

# TCXO
from peregrine.iqgen.bits.tcxo_sine import TCXOSine
from peregrine.iqgen.bits.tcxo_poly import TCXOPoly

import argparse
from scipy.constants import c as C


def test_computeTimeDelay0():
  '''
  Utility test
  '''
  doppler = DopplerPoly(distance0_m=0., tec_epm2=0., coeffs=())
  symbolIndex = 0l
  chipIndex = 0l
  signal = GPS.L1CA
  delay = computeTimeDelay(doppler, symbolIndex, chipIndex, signal)
  assert delay == 0.


def test_computeTimeDelay1():
  '''
  Utility test
  '''
  doppler = DopplerPoly(distance0_m=0., tec_epm2=0., coeffs=())
  symbolIndex = 1l
  chipIndex = 0l
  signal = GPS.L1CA
  delay = computeTimeDelay(doppler, symbolIndex, chipIndex, signal)
  assert delay == 0.


def test_argparser_init():
  '''
  Argument parser initialization test
  '''
  parser = prepareArgsParser()
  assert isinstance(parser, argparse.ArgumentParser)


def test_selectOutputConfig0():
  '''
  Output configuration selection test
  '''
  config = selectOutputConfig('low_rate')
  assert config == LowRateConfig


def test_selectOutputConfig1():
  '''
  Output configuration selection test
  '''
  config = selectOutputConfig('normal_rate')
  assert config == NormalRateConfig


def test_selectOutputConfig2():
  '''
  Output configuration selection test
  '''
  config = selectOutputConfig('high_rate')
  assert config == HighRateConfig


def test_selectOutputConfig3():
  '''
  Output configuration selection test
  '''
  config = selectOutputConfig('custom_rate')
  assert config == CustomRateConfig


def test_selectOutputConfig4():
  '''
  Output config selection test
  '''
  try:
    selectOutputConfig('xyz')
    assert False
  except ValueError:
    pass


def test_computeEnabledBands0():
  '''
  Bands selection test
  '''
  bandMap = computeEnabledBands([], NormalRateConfig)
  assert bandMap[NormalRateConfig.GPS.L1.NAME] == False
  assert bandMap[NormalRateConfig.GPS.L2.NAME] == False
  assert bandMap[NormalRateConfig.GLONASS.L1.NAME] == False
  assert bandMap[NormalRateConfig.GLONASS.L2.NAME] == False


def test_computeEnabledBands1():
  '''
  Bands selection test
  '''
  sv0 = GPSSatellite(1)
  sv0.setL1CAEnabled(True)
  sv1 = GLOSatellite(0)
  sv1.setL2Enabled(True)
  bandMap = computeEnabledBands([sv0, sv1], NormalRateConfig)
  assert bandMap[NormalRateConfig.GPS.L1.NAME] == True
  assert bandMap[NormalRateConfig.GPS.L2.NAME] == False
  assert bandMap[NormalRateConfig.GLONASS.L1.NAME] == False
  assert bandMap[NormalRateConfig.GLONASS.L2.NAME] == True


def test_computeEnabledBands2():
  '''
  Bands selection test
  '''
  sv0 = GPSSatellite(1)
  sv0.setL2CEnabled(True)
  sv1 = GLOSatellite(0)
  sv1.setL1Enabled(True)
  bandMap = computeEnabledBands([sv0, sv1], NormalRateConfig)
  assert bandMap[NormalRateConfig.GPS.L1.NAME] == False
  assert bandMap[NormalRateConfig.GPS.L2.NAME] == True
  assert bandMap[NormalRateConfig.GLONASS.L1.NAME] == True
  assert bandMap[NormalRateConfig.GLONASS.L2.NAME] == False


def test_selectEncoder_GPSL1():
  '''
  Encoder selection test
  '''
  enabledBands = {NormalRateConfig.GPS.L1.NAME: True,
                  NormalRateConfig.GPS.L2.NAME: False,
                  NormalRateConfig.GLONASS.L1.NAME: False,
                  NormalRateConfig.GLONASS.L2.NAME: False}
  encoder = selectEncoder('1bit', NormalRateConfig, enabledBands)
  assert isinstance(encoder, GPSL1BitEncoder)


def test_selectEncoder_GPSL2():
  '''
  Encoder selection test
  '''
  enabledBands = {NormalRateConfig.GPS.L1.NAME: False,
                  NormalRateConfig.GPS.L2.NAME: True,
                  NormalRateConfig.GLONASS.L1.NAME: False,
                  NormalRateConfig.GLONASS.L2.NAME: False}
  encoder = selectEncoder('1bit', NormalRateConfig, enabledBands)
  assert isinstance(encoder, GPSL2BitEncoder)


def test_selectEncoder_GPSL1L2():
  '''
  Encoder selection test
  '''
  enabledBands = {NormalRateConfig.GPS.L1.NAME: True,
                  NormalRateConfig.GPS.L2.NAME: True,
                  NormalRateConfig.GLONASS.L1.NAME: False,
                  NormalRateConfig.GLONASS.L2.NAME: False}
  encoder = selectEncoder('1bit', NormalRateConfig, enabledBands)
  assert isinstance(encoder, GPSL1L2BitEncoder)


def test_selectEncoder_GLONASSL1():
  '''
  Encoder selection test
  '''
  enabledBands = {NormalRateConfig.GPS.L1.NAME: False,
                  NormalRateConfig.GPS.L2.NAME: False,
                  NormalRateConfig.GLONASS.L1.NAME: True,
                  NormalRateConfig.GLONASS.L2.NAME: False}
  encoder = selectEncoder('1bit', NormalRateConfig, enabledBands)
  assert isinstance(encoder, GLONASSL1BitEncoder)


def test_selectEncoder_GLONASSL2():
  '''
  Encoder selection test
  '''
  enabledBands = {NormalRateConfig.GPS.L1.NAME: False,
                  NormalRateConfig.GPS.L2.NAME: False,
                  NormalRateConfig.GLONASS.L1.NAME: False,
                  NormalRateConfig.GLONASS.L2.NAME: True}
  encoder = selectEncoder('1bit', NormalRateConfig, enabledBands)
  assert isinstance(encoder, GLONASSL2BitEncoder)


def test_selectEncoder_GLONASSL1L2():
  '''
  Encoder selection test
  '''
  enabledBands = {NormalRateConfig.GPS.L1.NAME: False,
                  NormalRateConfig.GPS.L2.NAME: False,
                  NormalRateConfig.GLONASS.L1.NAME: True,
                  NormalRateConfig.GLONASS.L2.NAME: True}
  encoder = selectEncoder('1bit', NormalRateConfig, enabledBands)
  assert isinstance(encoder, GLONASSL1L2BitEncoder)


def test_selectEncoder_GPSGLONASS():
  '''
  Encoder selection test
  '''
  enabledBands = {NormalRateConfig.GPS.L1.NAME: True,
                  NormalRateConfig.GPS.L2.NAME: False,
                  NormalRateConfig.GLONASS.L1.NAME: True,
                  NormalRateConfig.GLONASS.L2.NAME: False}
  encoder = selectEncoder('1bit', NormalRateConfig, enabledBands)
  assert isinstance(encoder, GPSGLONASSBitEncoder)


def test_selectEncoder_2GPSL1():
  '''
  Encoder selection test
  '''
  enabledBands = {NormalRateConfig.GPS.L1.NAME: True,
                  NormalRateConfig.GPS.L2.NAME: False,
                  NormalRateConfig.GLONASS.L1.NAME: False,
                  NormalRateConfig.GLONASS.L2.NAME: False}
  encoder = selectEncoder('2bits', NormalRateConfig, enabledBands)
  assert isinstance(encoder, GPSL1TwoBitsEncoder)


def test_selectEncoder_2GPSL2():
  '''
  Encoder selection test
  '''
  enabledBands = {NormalRateConfig.GPS.L1.NAME: False,
                  NormalRateConfig.GPS.L2.NAME: True,
                  NormalRateConfig.GLONASS.L1.NAME: False,
                  NormalRateConfig.GLONASS.L2.NAME: False}
  encoder = selectEncoder('2bits', NormalRateConfig, enabledBands)
  assert isinstance(encoder, GPSL2TwoBitsEncoder)


def test_selectEncoder_2GPSL1L2():
  '''
  Encoder selection test
  '''
  enabledBands = {NormalRateConfig.GPS.L1.NAME: True,
                  NormalRateConfig.GPS.L2.NAME: True,
                  NormalRateConfig.GLONASS.L1.NAME: False,
                  NormalRateConfig.GLONASS.L2.NAME: False}
  encoder = selectEncoder('2bits', NormalRateConfig, enabledBands)
  assert isinstance(encoder, GPSL1L2TwoBitsEncoder)


def test_selectEncoder_2GLONASSL1():
  '''
  Encoder selection test
  '''
  enabledBands = {NormalRateConfig.GPS.L1.NAME: False,
                  NormalRateConfig.GPS.L2.NAME: False,
                  NormalRateConfig.GLONASS.L1.NAME: True,
                  NormalRateConfig.GLONASS.L2.NAME: False}
  encoder = selectEncoder('2bits', NormalRateConfig, enabledBands)
  assert isinstance(encoder, GLONASSL1TwoBitsEncoder)


def test_selectEncoder_2GLONASSL2():
  '''
  Encoder selection test
  '''
  enabledBands = {NormalRateConfig.GPS.L1.NAME: False,
                  NormalRateConfig.GPS.L2.NAME: False,
                  NormalRateConfig.GLONASS.L1.NAME: False,
                  NormalRateConfig.GLONASS.L2.NAME: True}
  encoder = selectEncoder('2bits', NormalRateConfig, enabledBands)
  assert isinstance(encoder, GLONASSL2TwoBitsEncoder)


def test_selectEncoder_2GLONASSL1L2():
  '''
  Encoder selection test
  '''
  enabledBands = {NormalRateConfig.GPS.L1.NAME: False,
                  NormalRateConfig.GPS.L2.NAME: False,
                  NormalRateConfig.GLONASS.L1.NAME: True,
                  NormalRateConfig.GLONASS.L2.NAME: True}
  encoder = selectEncoder('2bits', NormalRateConfig, enabledBands)
  assert isinstance(encoder, GLONASSL1L2TwoBitsEncoder)


def test_selectEncoder_2GPSGLONASS():
  '''
  Encoder selection test
  '''
  enabledBands = {NormalRateConfig.GPS.L1.NAME: True,
                  NormalRateConfig.GPS.L2.NAME: False,
                  NormalRateConfig.GLONASS.L1.NAME: True,
                  NormalRateConfig.GLONASS.L2.NAME: False}
  encoder = selectEncoder('2bits', NormalRateConfig, enabledBands)
  assert isinstance(encoder, GPSGLONASSTwoBitsEncoder)


def test_selectEncoder_Err():
  '''
  Encoder selection test
  '''
  enabledBands = {NormalRateConfig.GPS.L1.NAME: False,
                  NormalRateConfig.GPS.L2.NAME: False,
                  NormalRateConfig.GLONASS.L1.NAME: True,
                  NormalRateConfig.GLONASS.L2.NAME: True}
  try:
    selectEncoder('something', NormalRateConfig, enabledBands)
    assert False
  except ValueError:
    pass


def test_params_gps():
  '''
  GPS SV parameters test
  '''
  parser = prepareArgsParser()
  params = [
      '--gps-sv', '1',
  ]
  args = parser.parse_args(params)
  assert isinstance(args.gps_sv, list)
  assert isinstance(args.gps_sv[0], GPSSatellite)
  assert args.gps_sv[0].prn == 1


def test_params_glo():
  '''
  GLONASS SV parameters test
  '''
  parser = prepareArgsParser()
  params = [
      '--glo-sv', '0',
  ]
  args = parser.parse_args(params)
  assert isinstance(args.gps_sv, list)
  assert isinstance(args.gps_sv[0], GLOSatellite)
  assert args.gps_sv[0].prn == 0


def test_params_gps_glo():
  '''
  GPS+GLONASS SV parameters test
  '''
  parser = prepareArgsParser()
  params = [
      '--gps-sv', '1',
      '--glo-sv', '2',
  ]
  args = parser.parse_args(params)
  assert isinstance(args.gps_sv, list)
  assert isinstance(args.gps_sv[0], GPSSatellite)
  assert isinstance(args.gps_sv[1], GLOSatellite)
  assert args.gps_sv[0].prn == 1
  assert args.gps_sv[1].prn == 2


def test_params_band_l1ca():
  '''
  GPS L1 band parameters test
  '''
  parser = prepareArgsParser()
  params = [
      '--gps-sv', '1',
      '--bands', 'l1ca',
  ]
  args = parser.parse_args(params)
  assert args.gps_sv[0].isL1CAEnabled() == True
  assert args.gps_sv[0].isL2CEnabled() == False


def test_params_band_l2c():
  '''
  GPS L2 band parameters test
  '''
  parser = prepareArgsParser()
  params = [
      '--gps-sv', '1',
      '--bands', 'l2c',
  ]
  args = parser.parse_args(params)
  assert args.gps_sv[0].isL1CAEnabled() == False
  assert args.gps_sv[0].isL2CEnabled() == True


def test_params_band_l1ca_l2c():
  '''
  GPS dual band parameters test
  '''
  parser = prepareArgsParser()
  params = [
      '--gps-sv', '1',
      '--bands', 'l1ca+l2c',
  ]
  args = parser.parse_args(params)
  assert args.gps_sv[0].isL1CAEnabled() == True
  assert args.gps_sv[0].isL2CEnabled() == True


def test_params_band_l1():
  '''
  GLONASS L1 band parameters test
  '''
  parser = prepareArgsParser()
  params = [
      '--glo-sv', '1',
      '--bands', 'l1',
  ]
  args = parser.parse_args(params)
  # GLONASS and GPS satellites are all added to the same parameter list: gps_sv
  assert args.gps_sv[0].isL1Enabled() == True
  assert args.gps_sv[0].isL2Enabled() == False


def test_params_band_l2():
  '''
  GLONASS L2 band parameters test
  '''
  parser = prepareArgsParser()
  params = [
      '--glo-sv', '1',
      '--bands', 'l2',
  ]
  args = parser.parse_args(params)
  # GLONASS and GPS satellites are all added to the same parameter list: gps_sv
  assert args.gps_sv[0].isL1Enabled() == False
  assert args.gps_sv[0].isL2Enabled() == True


def test_params_band_l1_l2():
  '''
  GLONASS dual band parameters test
  '''
  parser = prepareArgsParser()
  params = [
      '--glo-sv', '1',
      '--bands', 'l1+l2',
  ]
  args = parser.parse_args(params)
  # GLONASS and GPS satellites are all added to the same parameter list: gps_sv
  assert args.gps_sv[0].isL1Enabled() == True
  assert args.gps_sv[0].isL2Enabled() == True


def test_params_doppler_zero():
  '''
  Zero doppler parameters test
  '''
  parser = prepareArgsParser()
  params = [
      '--gps-sv', '1',
      '--bands', 'l1ca',
      '--doppler-type', 'zero',
  ]
  args = parser.parse_args(params)
  doppler = args.gps_sv[0].getDoppler()
  assert isinstance(doppler, DopplerPoly)
  assert doppler.distance0_m == 0.
  assert doppler.tec_epm2 == 50.
  assert doppler.coeffs == ()


def test_params_doppler_const():
  '''
  Constant doppler parameters test
  '''
  parser = prepareArgsParser()
  params = [
      '--gps-sv', '1',
      '--bands', 'l1ca',
      '--doppler-type', 'const',
      '--doppler-value', '100'
  ]
  args = parser.parse_args(params)
  doppler = args.gps_sv[0].getDoppler()
  assert isinstance(doppler, DopplerPoly)
  assert doppler.distance0_m == 0.
  assert doppler.tec_epm2 == 50.

  speed_mps = -C / float(GPS.L1CA.CENTER_FREQUENCY_HZ) * 100.
  assert doppler.coeffs == (speed_mps, )


def test_params_doppler_linear():
  '''
  Linear doppler parameters test
  '''
  parser = prepareArgsParser()
  params = [
      '--gps-sv', '1',
      '--bands', 'l1ca',
      '--doppler-type', 'linear',
      '--doppler-value', '100',
      '--doppler-speed', '50',
  ]
  args = parser.parse_args(params)
  doppler = args.gps_sv[0].getDoppler()
  speed_mps = -C / float(GPS.L1CA.CENTER_FREQUENCY_HZ) * 100.
  accel_mps2 = -C / float(GPS.L1CA.CENTER_FREQUENCY_HZ) * 50.
  assert isinstance(doppler, DopplerPoly)
  assert doppler.distance0_m == 0.
  assert doppler.tec_epm2 == 50.
  assert doppler.coeffs == (accel_mps2, speed_mps)


def test_params_doppler_sine():
  '''
  Sine doppler parameters test
  '''
  parser = prepareArgsParser()
  params = [
      '--gps-sv', '1',
      '--bands', 'l1ca',
      '--doppler-type', 'sine',
      '--doppler-value', '100',
      '--doppler-amplitude', '50',
      '--doppler-period', '3',
  ]
  args = parser.parse_args(params)
  doppler = args.gps_sv[0].getDoppler()
  assert isinstance(doppler, DopplerSine)
  speed_mps = -C / float(GPS.L1CA.CENTER_FREQUENCY_HZ) * 100.
  assert doppler.distance0_m == 0.
  assert doppler.tec_epm2 == 50.
  assert doppler.period_s == 3.
  assert doppler.amplutude_mps == speed_mps / 2.
  assert doppler.speed0_mps == speed_mps


def test_params_doppler_sine2():
  '''
  Sine doppler parameters test
  '''
  parser = prepareArgsParser()
  params = [
      '--gps-sv', '1',
      '--bands', 'l2c',
      '--doppler-type', 'sine',
      '--doppler-value', '100',
      '--doppler-amplitude', '50',
      '--doppler-period', '3',
  ]
  args = parser.parse_args(params)
  doppler = args.gps_sv[0].getDoppler()
  assert isinstance(doppler, DopplerSine)
  speed_mps = -C / float(GPS.L2C.CENTER_FREQUENCY_HZ) * 100.
  assert doppler.distance0_m == 0.
  assert doppler.tec_epm2 == 50.
  assert doppler.period_s == 3.
  assert doppler.amplutude_mps == speed_mps / 2.
  assert doppler.speed0_mps == speed_mps


def test_params_amplitude_poly_snr_db():
  '''
  Amplitude unit parameters test
  '''
  parser = prepareArgsParser()
  params = [
      '--gps-sv', '1',
      '--bands', 'l1ca',
      '--amplitude-type', 'poly',
      '--amplitude-units', 'snr-db',
  ]
  args = parser.parse_args(params)
  amplitude = args.gps_sv[0].getAmplitude()
  assert isinstance(amplitude, AmplitudePoly)
  assert amplitude.coeffs == ()
  assert amplitude.units == AmplitudePoly.UNITS_SNR_DB


def test_params_amplitude_poly_snr():
  '''
  Amplitude unit parameters test
  '''
  parser = prepareArgsParser()
  params = [
      '--gps-sv', '1',
      '--bands', 'l1ca',
      '--amplitude-type', 'poly',
      '--amplitude-units', 'snr',
  ]
  args = parser.parse_args(params)
  amplitude = args.gps_sv[0].getAmplitude()
  assert isinstance(amplitude, AmplitudePoly)
  assert amplitude.coeffs == ()
  assert amplitude.units == AmplitudePoly.UNITS_SNR


def test_params_amplitude_poly_amp():
  '''
  Amplitude unit parameters test
  '''
  parser = prepareArgsParser()
  params = [
      '--gps-sv', '1',
      '--bands', 'l1ca',
      '--amplitude-type', 'poly',
      '--amplitude-units', 'amplitude',
  ]
  args = parser.parse_args(params)
  amplitude = args.gps_sv[0].getAmplitude()
  assert isinstance(amplitude, AmplitudePoly)
  assert amplitude.coeffs == ()
  assert amplitude.units == AmplitudePoly.UNITS_AMPLITUDE


def test_params_amplitude_poly_power():
  '''
  Amplitude unit parameters test
  '''
  parser = prepareArgsParser()
  params = [
      '--gps-sv', '1',
      '--bands', 'l1ca',
      '--amplitude-type', 'poly',
      '--amplitude-units', 'power',
  ]
  args = parser.parse_args(params)
  amplitude = args.gps_sv[0].getAmplitude()
  assert isinstance(amplitude, AmplitudePoly)
  assert amplitude.coeffs == ()
  assert amplitude.units == AmplitudePoly.UNITS_POWER


def test_params_amplitude_poly_1():
  '''
  Polynomial amplitude parameters test
  '''
  parser = prepareArgsParser()
  params = [
      '--gps-sv', '1',
      '--bands', 'l1ca',
      '--amplitude-type', 'poly',
      '--amplitude-a0', '1',
  ]
  args = parser.parse_args(params)
  amplitude = args.gps_sv[0].getAmplitude()
  assert isinstance(amplitude, AmplitudePoly)
  assert amplitude.coeffs == (1., )


def test_params_amplitude_poly_2():
  '''
  Polynomial amplitude parameters test
  '''
  parser = prepareArgsParser()
  params = [
      '--gps-sv', '1',
      '--bands', 'l1ca',
      '--amplitude-type', 'poly',
      '--amplitude-a0', '1',
      '--amplitude-a1', '2',
  ]
  args = parser.parse_args(params)
  amplitude = args.gps_sv[0].getAmplitude()
  assert isinstance(amplitude, AmplitudePoly)
  assert amplitude.coeffs == (2., 1., )


def test_params_amplitude_poly_3():
  '''
  Polynomial amplitude parameters test
  '''
  parser = prepareArgsParser()
  params = [
      '--gps-sv', '1',
      '--bands', 'l1ca',
      '--amplitude-type', 'poly',
      '--amplitude-a0', '1',
      '--amplitude-a3', '2',
  ]
  args = parser.parse_args(params)
  amplitude = args.gps_sv[0].getAmplitude()
  assert isinstance(amplitude, AmplitudePoly)
  assert amplitude.coeffs == (2., 0., 0., 1., )


def test_params_amplitude_poly_4():
  '''
  Polynomial amplitude parameters test
  '''
  parser = prepareArgsParser()
  params = [
      '--gps-sv', '1',
      '--bands', 'l1ca',
      '--amplitude-type', 'poly',
      '--amplitude-a3', '2',
  ]
  args = parser.parse_args(params)
  amplitude = args.gps_sv[0].getAmplitude()
  assert isinstance(amplitude, AmplitudePoly)
  assert amplitude.coeffs == (2., 0., 0., 0., )


def test_params_amplitude_sine():
  '''
  Sine amplitude parameters test
  '''
  parser = prepareArgsParser()
  params = [
      '--gps-sv', '1',
      '--bands', 'l1ca',
      '--amplitude-type', 'sine',
      '--amplitude-a0', '1',
      '--amplitude-a1', '2',
      '--amplitude-period', '3',
  ]
  args = parser.parse_args(params)
  amplitude = args.gps_sv[0].getAmplitude()
  assert isinstance(amplitude, AmplitudeSine)
  assert amplitude.amplitude == 2.
  assert amplitude.initial == 1.
  assert amplitude.period_s == 3.


def test_params_doppler_code_tracking_0():
  '''
  Doppler code tracking flag test
  '''
  parser = prepareArgsParser()
  params = [
      '--gps-sv', '1',
      '--bands', 'l1ca',
  ]
  args = parser.parse_args(params)
  doppler = args.gps_sv[0].getDoppler()
  assert doppler.isCodeDopplerIgnored() == False


def test_params_doppler_code_tracking_1():
  '''
  Doppler code tracking flag test
  '''
  parser = prepareArgsParser()
  params = [
      '--gps-sv', '1',
      '--bands', 'l1ca',
      '--ignore-code-doppler', '1'
  ]
  args = parser.parse_args(params)
  doppler = args.gps_sv[0].getDoppler()
  assert doppler.isCodeDopplerIgnored() == True


def test_parameters_TCXO0():
  '''
  TCXO parameter test
  '''
  parser = prepareArgsParser()
  params = [
      '--tcxo-type', 'sine',
      '--tcxo-a0', '0',
      '--tcxo-a1', '1',
      '--tcxo-period', '3']
  args = parser.parse_args(params)
  assert isinstance(args.tcxo, TCXOSine)


def test_parameters_TCXO1():
  '''
  TCXO parameter test
  '''
  parser = prepareArgsParser()
  params = [
      '--tcxo-type', 'poly',
      '--tcxo-a1', '1']
  args = parser.parse_args(params)
  assert isinstance(args.tcxo, TCXOPoly)


def test_parameters_TCXO2():
  '''
  TCXO parameter error test
  '''
  parser = prepareArgsParser()
  params = [
      '--tcxo-type', 'abc',
      '--tcxo-a0', '0',
      '--tcxo-a1', '1']
  try:
    parser.parse_args(params)
    assert False
  except:
    pass


def test_parameters_msgtype0():
  '''
  All Zero message test
  '''
  parser = prepareArgsParser()
  params = [
      '--gps-sv', '1',
      '--message-type', 'zero']
  args = parser.parse_args(params)
  assert isinstance(args.gps_sv[0].getL1CAMessage(), ConstMessage)
  assert args.gps_sv[0].getL1CAMessage().bitValue == 1


def test_parameters_msgtype1():
  '''
  All One message test
  '''
  parser = prepareArgsParser()
  params = [
      '--gps-sv', '1',
      '--message-type', 'one']
  args = parser.parse_args(params)
  assert isinstance(args.gps_sv[0].getL1CAMessage(), ConstMessage)
  assert args.gps_sv[0].getL1CAMessage().bitValue == -1


def test_parameters_msgtype2():
  '''
  Zero+One message test
  '''
  parser = prepareArgsParser()
  params = [
      '--gps-sv', '1',
      '--message-type', 'zero+one']
  args = parser.parse_args(params)
  assert isinstance(args.gps_sv[0].getL1CAMessage(), ZeroOneMessage)


def test_parameters_msgtype3():
  '''
  GPS CRC messages test
  '''
  parser = prepareArgsParser()
  params = [
      '--gps-sv', '1',
      '--message-type', 'crc']
  args = parser.parse_args(params)
  assert isinstance(args.gps_sv[0].getL1CAMessage(), LNavMessage)
  assert isinstance(args.gps_sv[0].getL2CMessage(), CNavMessage)


def test_parameters_msgtype4():
  '''
  GLONASS CRC message test
  '''
  parser = prepareArgsParser()
  params = [
      '--glo-sv', '0',
      '--message-type', 'crc']
  args = parser.parse_args(params)
  assert isinstance(args.gps_sv[0].getL1Message(), GLOMessage)


def test_printOutput():
  '''
  Plain configuration output test
  '''
  parser = prepareArgsParser()
  params = [
      '--gps-sv', '1',
      '--bands', 'l1ca+l2c',
      '--glo-sv', '1',
      '--bands', 'l1+l2',
  ]
  args = parser.parse_args(params)
  # Sanity check: the function shall execute without errors with all possible
  # SV types
  printOutputConfig(NormalRateConfig, args)


def test_progressBar_stdout():
  '''
  Progress bar utility test
  '''
  pbar = makeProgressBar('stdout', 100)
  assert pbar is not None
  assert pbar.fd == sys.stdout
  pbar.finish()


def test_progressBar_stderr():
  '''
  Progress bar utility test
  '''
  pbar = makeProgressBar('stderr', 100)
  assert pbar is not None
  assert pbar.fd == sys.stderr
  pbar.finish()


def test_progressBar_none():
  '''
  Progress bar utility test
  '''
  pbar = makeProgressBar('none', 100)
  assert pbar is None

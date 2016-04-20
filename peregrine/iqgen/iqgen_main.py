#!/usr/bin/env python
# Copyright (C) 2016 Swift Navigation Inc.
# Contact: Valeri Atamaniouk <valeri@swiftnav.com>
#
# This source is subject to the license found in the file 'LICENSE' which must
# be be distributed together with this source. All other rights reserved.
#
# THIS CODE AND INFORMATION IS PROVIDED "AS IS" WITHOUT WARRANTY OF ANY KIND,
# EITHER EXPRESSED OR IMPLIED, INCLUDING BUT NOT LIMITED TO THE IMPLIED
# WARRANTIES OF MERCHANTABILITY AND/OR FITNESS FOR A PARTICULAR PURPOSE.

"""
The :mod:`peregrine.iqgen.iqgen_main` module contains classes and functions
related to parameter processing.

"""
import sys
import time
import argparse
import scipy.constants
import numpy
import json
import logging
try:
  import progressbar
  hasProgressBar = True
except:
  hasProgressBar = False

from peregrine.iqgen.bits.satellite_gps import GPSSatellite
from peregrine.iqgen.bits.satellite_glo import GLOSatellite

# Doppler objects
from peregrine.iqgen.bits.doppler_poly import zeroDoppler
from peregrine.iqgen.bits.doppler_poly import constDoppler
from peregrine.iqgen.bits.doppler_poly import linearDoppler
from peregrine.iqgen.bits.doppler_sine import sineDoppler

# Amplitude objects
from peregrine.iqgen.bits.amplitude_poly import AmplitudePoly
from peregrine.iqgen.bits.amplitude_sine import AmplitudeSine
from peregrine.iqgen.bits.amplitude_base import AmplitudeBase

# TCXO objects
from peregrine.iqgen.bits.tcxo_poly import TCXOPoly
from peregrine.iqgen.bits.tcxo_sine import TCXOSine

# from signals import GPS, GPS_L2C_Signal, GPS_L1CA_Signal
import peregrine.iqgen.bits.signals as signals

from peregrine.iqgen.if_iface import LowRateConfig
from peregrine.iqgen.if_iface import NormalRateConfig
from peregrine.iqgen.if_iface import HighRateConfig
from peregrine.iqgen.if_iface import CustomRateConfig

# Message data
from peregrine.iqgen.bits.message_const import Message as ConstMessage
from peregrine.iqgen.bits.message_zeroone import Message as ZeroOneMessage
from peregrine.iqgen.bits.message_block import Message as BlockMessage
from peregrine.iqgen.bits.message_cnav import Message as CNavMessage
from peregrine.iqgen.bits.message_lnav import Message as LNavMessage
from peregrine.iqgen.bits.message_glo import Message as GLOMessage

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

from peregrine.iqgen.generate import generateSamples

from peregrine.iqgen.bits.satellite_factory import factoryObject as satelliteFO
from peregrine.iqgen.bits.tcxo_factory import factoryObject as tcxoFO

from peregrine.log import default_logging_config

logger = logging.getLogger(__name__)

AMP_MAP = {'amplitude': AmplitudeBase.UNITS_AMPLITUDE,
           'power': AmplitudeBase.UNITS_POWER,
           'snr': AmplitudeBase.UNITS_SNR,
           'snr-db': AmplitudeBase.UNITS_SNR_DB}


def computeTimeDelay(doppler, symbol_index, chip_index, signal):
  '''
  Helper function to compute signal delay to match given symbol and chip
  indexes.

  Parameters
  ----------
  doppler : object
    Doppler object
  symbol_index : long
    Index of the symbol or pseudosymbol
  chip_index : long
    Chip index
  signal : object
    Signal object

  Returns
  -------
  float
     User's time in seconds when the user starts receiving the given symbol
     and code.
  '''
  if symbol_index == 0 and chip_index == 0:
    return 0.

  symbolDelay_s = (1. / signal.SYMBOL_RATE_HZ) * symbol_index
  chipDelay_s = (1. / signal.CODE_CHIP_RATE_HZ) * chip_index
  distance_m = doppler.computeDistanceM(symbolDelay_s + chipDelay_s)
  return distance_m / scipy.constants.c


def computeDistanceDelay(delay_symbols, delay_chips, signal):
  '''
  Helper function to compute signal delay to match given symbol and chip
  delays.

  Parameters
  ----------
  delay_symbols : float, optional
    Delay in symbols
  delay_chips : float, optional
    Delay in chips
  signal : object
    Signal object

  Returns
  -------
  float
     User's time in seconds when the user starts receiving the given symbol
     and code.
  '''

  if delay_symbols is not None:
    symbolDelay_s = (1. / signal.SYMBOL_RATE_HZ) * delay_symbols
  else:
    symbolDelay_s = 0.
  if delay_chips is not None:
    chipDelay_s = (1. / signal.CODE_CHIP_RATE_HZ) * delay_chips
  else:
    chipDelay_s = 0.
  return (symbolDelay_s + chipDelay_s) * scipy.constants.c


def prepareArgsParser():
  '''
  Constructs command line argument parser.

  Returns
  -------
  object
    Command line argument parser object.
  '''
  class AddSv(argparse.Action):

    def __init__(self, option_strings, dest, nargs=None, **kwargs):
      super(AddSv, self).__init__(option_strings, dest, **kwargs)

    def __call__(self, parser, namespace, values, option_string=None):
      # Initialize SV list if not yet done
      if namespace.gps_sv is None:
        namespace.gps_sv = []

      # Add SV to the tail of the list.
      if option_string == '--gps-sv':
        sv = GPSSatellite(int(values))
      elif option_string == '--glo-sv':
        sv = GLOSatellite(int(values))
      else:
        raise ValueError("Option value is not supported: %s" % option_string)
      namespace.gps_sv.append(sv)

      # Reset all configuration parameters
      namespace.l2cl_code_type = '01'
      namespace.ignore_code_doppler = False

      # Doppler
      namespace.doppler_type = "zero"
      namespace.doppler_value = 0.
      namespace.doppler_speed = 0.
      namespace.distance = None
      namespace.tec = 50.
      namespace.doppler_amplitude = 0.
      namespace.doppler_period = 1.
      namespace.symbol_delay = None
      namespace.chip_delay = None

      # Source message data
      namespace.message_type = "zero"
      namespace.message_file = None

      # Amplitude parameters
      namespace.amplitude_type = "poly"
      namespace.amplitude_unis = "snr-db"
      namespace.amplitude_a0 = None
      namespace.amplitude_a1 = None
      namespace.amplitude_a2 = None
      namespace.amplitude_a3 = None
      namespace.amplitude_period = None

  class UpdateSv(argparse.Action):

    def __init__(self, option_strings, dest, nargs=None, **kwargs):
      super(UpdateSv, self).__init__(option_strings, dest, **kwargs)

    def __call__(self, parser, namespace, values, option_string=None):
      sv_list = getattr(namespace, "gps_sv")
      if sv_list is None:
        raise ValueError("No SV specified")
      setattr(namespace, self.dest, values)
      # super(UpdateSv, self).__call__(parser, namespace, values, option_string)
      self.doUpdate(sv_list[len(sv_list) - 1], parser, namespace, values,
                    option_string)

    def doUpdate(self, sv, parser, namespace, values, option_string):
      pass

  class UpdateBands(UpdateSv):

    def __init__(self, option_strings, dest, nargs=None, **kwargs):
      super(UpdateBands, self).__init__(option_strings, dest, **kwargs)

    def doUpdate(self, sv, parser, namespace, values, option_string):
      l1caEnabled = False
      l2cEnabled = False
      if namespace.bands == "l1ca" or namespace.bands == 'l1':
        l1caEnabled = True
      elif namespace.bands == "l2c" or namespace.bands == 'l2':
        l2cEnabled = True
      elif namespace.bands == "l1ca+l2c" or namespace.bands == 'l1+l2':
        l1caEnabled = True
        l2cEnabled = True
      else:
        raise ValueError()
      if isinstance(sv, GPSSatellite):
        sv.setL2CLCodeType(namespace.l2cl_code_type)
        sv.setL1CAEnabled(l1caEnabled)
        sv.setL2CEnabled(l2cEnabled)
      elif isinstance(sv, GLOSatellite):
        sv.setL1Enabled(l1caEnabled)
        sv.setL2Enabled(l2cEnabled)
      else:
        raise ValueError("Unsupported object type in SV list")

  class UpdateDopplerType(UpdateSv):

    def __init__(self, option_strings, dest, nargs=None, **kwargs):
      super(UpdateDopplerType, self).__init__(option_strings, dest, **kwargs)

    def doUpdate(self, sv, parser, namespace, values, option_string):
      if isinstance(sv, GPSSatellite):
        if sv.l1caEnabled:
          signal = signals.GPS.L1CA
        elif sv.l2cEnabled:
          signal = signals.GPS.L2C
        else:
          raise ValueError("Signal band must be specified before doppler")
      elif isinstance(sv, GLOSatellite):
        if sv.isL1Enabled():
          frequency_hz = signals.GLONASS.L1S[sv.prn].CENTER_FREQUENCY_HZ
        elif sv.isL2Enabled():
          frequency_hz = signals.GLONASS.L2S[sv.prn].CENTER_FREQUENCY_HZ
        else:
          raise ValueError("Signal band must be specified before doppler")
      else:
        raise ValueError("Signal band must be specified before doppler")

      frequency_hz = signal.CENTER_FREQUENCY_HZ

      # Select distance: either from a distance parameter or from delays
      if namespace.symbol_delay is not None or namespace.chip_delay is not None:
        distance = computeDistanceDelay(namespace.symbol_delay,
                                        namespace.chip_delay,
                                        signal)
      else:
        distance = namespace.distance if namespace.distance is not None else 0.

      if namespace.doppler_type == "zero":
        doppler = zeroDoppler(distance, namespace.tec, frequency_hz)
      elif namespace.doppler_type == "const":
        doppler = constDoppler(distance,
                               namespace.tec,
                               frequency_hz,
                               namespace.doppler_value)
      elif namespace.doppler_type == "linear":
        doppler = linearDoppler(distance,
                                namespace.tec,
                                frequency_hz,
                                namespace.doppler_value,
                                namespace.doppler_speed)
      elif namespace.doppler_type == "sine":
        doppler = sineDoppler(distance,
                              namespace.tec,
                              frequency_hz,
                              namespace.doppler_value,
                              namespace.doppler_amplitude,
                              namespace.doppler_period)
      else:
        raise ValueError("Unsupported doppler type")
      sv.doppler = doppler

  class DisableCodeDoppler(UpdateSv):

    def __init__(self, option_strings, dest, nargs=None, **kwargs):
      super(DisableCodeDoppler, self).__init__(option_strings, dest, **kwargs)

    def doUpdate(self, sv, parser, namespace, values, option_string):
      print "CD=", namespace.ignore_code_doppler, values, option_string
      sv.setCodeDopplerIgnored(namespace.ignore_code_doppler)

  class UpdateAmplitudeType(UpdateSv):

    def __init__(self, option_strings, dest, nargs=None, **kwargs):
      super(UpdateAmplitudeType, self).__init__(option_strings, dest, **kwargs)

    def doUpdate(self, sv, parser, namespace, values, option_string):
      amplitude_units = AMP_MAP[namespace.amplitude_units]

      if namespace.amplitude_type == "poly":
        coeffs = []
        hasHighOrder = False

        srcA = [namespace.amplitude_a3, namespace.amplitude_a2,
                namespace.amplitude_a1, namespace.amplitude_a0]
        for a in srcA:
          if a is not None:
            coeffs.append(a)
            hasHighOrder = True
          elif hasHighOrder:
            coeffs.append(0.)
        amplitude = AmplitudePoly(amplitude_units, tuple(coeffs))
      elif namespace.amplitude_type == "sine":
        initial = 1.
        ampl = 0.5
        period_s = 1.
        if namespace.amplitude_a0 is not None:
          initial = namespace.amplitude_a0
        if namespace.amplitude_a1 is not None:
          ampl = namespace.amplitude_a1
        if namespace.amplitude_period is not None:
          period_s = namespace.amplitude_period

        amplitude = AmplitudeSine(amplitude_units, initial, ampl, period_s)
      else:
        raise ValueError("Unsupported amplitude type")
      sv.setAmplitude(amplitude)

  class UpdateTcxoType(argparse.Action):

    def __init__(self, option_strings, dest, nargs=None, **kwargs):
      super(UpdateTcxoType, self).__init__(option_strings, dest, **kwargs)

    def __call__(self, parser, namespace, values, option_string=None):
      setattr(namespace, self.dest, values)

      if namespace.tcxo_type == "poly":
        coeffs = []
        hasHighOrder = False

        srcA = [namespace.tcxo_a3, namespace.tcxo_a2,
                namespace.tcxo_a1, namespace.tcxo_a0]
        for a in srcA:
          if a is not None:
            coeffs.append(a)
            hasHighOrder = True
          elif hasHighOrder:
            coeffs.append(0.)
        tcxo = TCXOPoly(coeffs)
      elif namespace.tcxo_type == "sine":
        initial = 0.
        ampl = 0.5
        period_s = 1.
        if namespace.tcxo_a0 is not None:
          ampl = namespace.tcxo_a0
        if namespace.tcxo_a1 is not None:
          ampl = namespace.tcxo_a1
        if namespace.tcxo_period is not None:
          period_s = namespace.tcxo_period

        tcxo = TCXOSine(initial, ampl, period_s)
      else:
        raise ValueError("Unsupported TCXO type")
      namespace.tcxo = tcxo

  class UpdateMessageType(UpdateSv):

    def __init__(self, option_strings, dest, nargs=None, **kwargs):
      super(UpdateMessageType, self).__init__(option_strings, dest, **kwargs)

    def doUpdate(self, sv, parser, namespace, values, option_string):
      if namespace.message_type == "zero":
        messageL1 = ConstMessage(1)
        messageL2 = messageL1
      elif namespace.message_type == "one":
        messageL1 = ConstMessage(-1)
        messageL2 = messageL1
      elif namespace.message_type == "zero+one":
        messageL1 = ZeroOneMessage()
        messageL2 = messageL1
      elif namespace.message_type == "crc":
        if isinstance(sv, GPSSatellite):
          messageL1 = LNavMessage(sv.prn)
          messageL2 = CNavMessage(sv.prn)
        elif isinstance(sv, GLOSatellite):
          messageL1 = GLOMessage(sv.prn)
          messageL2 = GLOMessage(sv.prn)
        else:
          raise ValueError(
              "Message type is not supported for a satellite type")
      else:
        raise ValueError("Unsupported message type")
      if isinstance(sv, GPSSatellite):
        sv.setL1CAMessage(messageL1)
        sv.setL2CMessage(messageL2)
      elif isinstance(sv, GLOSatellite):
        sv.setL1Message(messageL1)
        sv.setL2Message(messageL2)
      else:
        raise ValueError("Unsupported object type in SV list")

  class UpdateMessageFile(UpdateSv):

    def __init__(self, option_strings, dest, nargs=None, **kwargs):
      super(UpdateMessageFile, self).__init__(option_strings, dest, **kwargs)

    def doUpdate(self, sv, parser, namespace, values, option_string):
      data = numpy.fromfile(namespace.message_file, dtype=numpy.uint8)
      namespace.message_file.close()
      data = numpy.unpackbits(data)
      data = numpy.asarray(data, dtype=numpy.int8)
      data <<= 1
      data -= 1
      numpy.negative(data, out=data)
      message = BlockMessage(data)

      if isinstance(sv, GPSSatellite):
        sv.setL1CAMessage(message)
        sv.setL2CMessage(message)
      elif isinstance(sv, GLOSatellite):
        sv.setL1Message(message)
        sv.setL2Message(message)
      else:
        raise ValueError("Unsupported object type in SV list")

  class SaveConfigAction(argparse.Action):

    def __init__(self, option_strings, dest, nargs=None, **kwargs):
      super(SaveConfigAction, self).__init__(option_strings, dest, **kwargs)

    def __call__(self, parser, namespace, values, option_string=None):

      gps_sv = namespace.gps_sv

      encoded_gps_sv = [satelliteFO.toMapForm(sv) for sv in gps_sv]

      data = {'type': 'Namespace',
              'gps_sv': encoded_gps_sv,
              'profile': namespace.profile,
              'encoder': namespace.encoder,
              'generate': namespace.generate,
              'noise_sigma': namespace.noise_sigma,
              'filter_type': namespace.filter_type,
              'tcxo': tcxoFO.toMapForm(namespace.tcxo),
              'group_delays': namespace.group_delays
              }
      json.dump(data, values, indent=2)
      values.close()
      namespace.no_run = True

  class LoadConfigAction(argparse.Action):

    def __init__(self, option_strings, dest, nargs=None, **kwargs):
      super(LoadConfigAction, self).__init__(option_strings, dest, **kwargs)

    def __call__(self, parser, namespace, values, option_string=None):
      loaded = json.load(values)
      namespace.profile = loaded['profile']
      namespace.encoder = loaded['encoder']
      namespace.generate = loaded['generate']
      namespace.noise_sigma = loaded['noise_sigma']
      namespace.filter_type = loaded['filter_type']
      namespace.tcxo = tcxoFO.fromMapForm(loaded['tcxo'])
      namespace.gps_sv = [
          satelliteFO.fromMapForm(sv) for sv in loaded['gps_sv']]
      namespace.group_delays = loaded['group_delays']
      values.close()

  parser = argparse.ArgumentParser(
      description="Signal generator", usage='%(prog)s [options]')
  parser.add_argument('--gps-sv',
                      default=[],
                      help='Enable GPS satellite',
                      action=AddSv)
  parser.add_argument('--glo-sv',
                      default=[],
                      help='Enable GLONASS satellite',
                      action=AddSv)
  parser.add_argument('--bands',
                      default="l1ca",
                      choices=["l1ca", "l2c", "l1ca+l2c", "l1", "l2", "l1+l2"],
                      help="Signal bands to enable",
                      action=UpdateBands)
  dopplerGrp = parser.add_argument_group("Doppler Control",
                                         "Doppler control parameters")
  dopplerGrp.add_argument('--doppler-type',
                          default="zero",
                          choices=["zero", "const", "linear", "sine"],
                          help="Configure doppler type",
                          action=UpdateDopplerType)
  dopplerGrp.add_argument('--doppler-value',
                          type=float,
                          help="Doppler shift in hertz (initial)",
                          action=UpdateDopplerType)
  dopplerGrp.add_argument('--doppler-speed',
                          type=float,
                          help="Doppler shift change in hertz/second",
                          action=UpdateDopplerType)

  delayGrp = parser.add_argument_group("Signal Delay Control",
                                       "Signal delay control parameters")
  # Common delays: ionosphere
  delayGrp.add_argument('--tec',
                        type=float,
                        help="Ionosphere TEC for signal delay"
                        " (electrons per meter^2)",
                        action=UpdateDopplerType)
  # Distance control over direct parameter
  delayGrp.add_argument('--distance',
                        type=float,
                        help="Distance in meters for signal delay (initial)",
                        action=UpdateDopplerType)
  # Distance control over delays
  delayGrp.add_argument('--symbol-delay',
                        type=float,
                        help="Initial symbol index",
                        action=UpdateDopplerType)
  delayGrp.add_argument('--chip-delay',
                        type=float,
                        help="Initial chip index",
                        action=UpdateDopplerType)
  dopplerGrp.add_argument('--doppler-amplitude',
                          type=float,
                          help="Doppler change amplitude (hertz)",
                          action=UpdateDopplerType)
  dopplerGrp.add_argument('--doppler-period',
                          type=float,
                          help="Doppler change period (seconds)",
                          action=UpdateDopplerType)
  dopplerGrp.add_argument('--ignore-code-doppler',
                          type=bool,
                          help="Disable doppler for code and data processing",
                          action=DisableCodeDoppler)
  amplitudeGrp = parser.add_argument_group("Amplitude Control",
                                           "Amplitude control parameters")
  amplitudeGrp.add_argument('--amplitude-type',
                            default="poly",
                            choices=["poly", "sine"],
                            help=
                              "Configure amplitude type: polynomial or sine.",
                            action=UpdateAmplitudeType)
  amplitudeGrp.add_argument('--amplitude-units',
                            default="snr-db",
                            choices=["snr-db", "snr", "amplitude", "power"],
                            help="Configure amplitude units: SNR in dB; SNR;"
                                 " amplitude; power.",
                            action=UpdateAmplitudeType)
  amplitudeGrp.add_argument('--amplitude-a0',
                            type=float,
                            help="Amplitude coefficient (a0 for polynomial;"
                            " offset for sine)",
                            action=UpdateAmplitudeType)
  amplitudeGrp.add_argument('--amplitude-a1',
                            type=float,
                            help="Amplitude coefficient (a1 for polynomial,"
                            " amplitude for size)",
                            action=UpdateAmplitudeType)
  amplitudeGrp.add_argument('--amplitude-a2',
                            type=float,
                            help="Amplitude coefficient (a2 for polynomial)",
                            action=UpdateAmplitudeType)
  amplitudeGrp.add_argument('--amplitude-a3',
                            type=float,
                            help="Amplitude coefficient (a3 for polynomial)",
                            action=UpdateAmplitudeType)
  amplitudeGrp.add_argument('--amplitude-period',
                            type=float,
                            help="Amplitude period in seconds for sine",
                            action=UpdateAmplitudeType)
  messageGrp = parser.add_argument_group("Message Data Control",
                                         "Message data control parameters")
  messageGrp.add_argument('--message-type', default="zero",
                          choices=["zero", "one", "zero+one", "crc"],
                          help="Message type",
                          action=UpdateMessageType)
  messageGrp.add_argument('--message-file',
                          type=argparse.FileType('rb'),
                          help="Source file for message contents.",
                          action=UpdateMessageFile)
  messageGrp.add_argument('--l2cl-code-type',
                          default='01',
                          choices=['01', '1', '0'],
                          help="GPS L2 CL code type",
                          action=UpdateBands)
  parser.add_argument('--filter-type',
                      default='none',
                      choices=['none', 'lowpass', 'bandpass'],
                      help="Enable filter")
  parser.add_argument('--noise-sigma',
                      type=float,
                      default=1.,
                      help="Noise sigma for noise generation")
  tcxoGrp = parser.add_argument_group("TCXO Control",
                                      "TCXO control parameters")

  tcxoGrp.add_argument('--tcxo-type',
                       choices=["poly", "sine"],
                       help="TCXO drift type",
                       action=UpdateTcxoType)
  tcxoGrp.add_argument('--tcxo-a0',
                       type=float,
                       help="TCXO a0 coefficient for polynomial TCXO drift"
                       " or initial shift for sine TCXO drift",
                       action=UpdateTcxoType)
  tcxoGrp.add_argument('--tcxo-a1',
                       type=float,
                       help="TCXO a1 coefficient for polynomial TCXO drift"
                       " or amplitude for sine TCXO drift",
                       action=UpdateTcxoType)
  tcxoGrp.add_argument('--tcxo-a2',
                       type=float,
                       help="TCXO a2 coefficient for polynomial TCXO drift",
                       action=UpdateTcxoType)
  tcxoGrp.add_argument('--tcxo-a3',
                       type=float,
                       help="TCXO a3 coefficient for polynomial TCXO drift",
                       action=UpdateTcxoType)
  tcxoGrp.add_argument('--tcxo-period',
                       type=float,
                       help="TCXO period in seconds for sine TCXO drift",
                       action=UpdateTcxoType)
  parser.add_argument('--group-delays',
                      type=bool,
                      help=
                        "Enable/disable group delays simulation between bands")
  parser.add_argument('--debug',
                      type=argparse.FileType('wb'),
                      help="Debug output file")
  parser.add_argument('--generate',
                      type=float,
                      default=3.,
                      help="Amount of data to generate, in seconds")
  parser.add_argument('--encoder',
                      default="2bits",
                      choices=["1bit", "2bits"],
                      help="Output data format")
  parser.add_argument('--output',
                      type=argparse.FileType('wb'),
                      help="Output file name")
  parser.add_argument('--profile',
                      default="normal_rate",
                      choices=["low_rate", "normal_rate", "high_rate",
                               "custom_rate"],
                      help="Output profile configuration")
  parser.add_argument('-j', '--jobs',
                      type=int,
                      default=0,
                      help="Use parallel threads")

  parser.add_argument('--save-config',
                      type=argparse.FileType('wt'),
                      help="Store configuration into file (implies --no-run)",
                      action=SaveConfigAction)

  parser.add_argument('--load-config',
                      type=argparse.FileType('rt'),
                      help="Restore configuration from file",
                      action=LoadConfigAction)

  parser.add_argument('--no-run',
                      action="store_true",
                      default=False,
                      help="Do not generate output.")

  if sys.stdout.isatty():
    progress_bar_default = 'stdout'
  elif sys.stderr.isatty():
    progress_bar_default = 'stderr'
  else:
    progress_bar_default = 'none'
  parser.add_argument("--progress-bar",
                      metavar='FLAG',
                      choices=['stdout', 'stderr', 'none'],
                      default=progress_bar_default,
                      help="Show progress bar. Default is '%s'" %
                      progress_bar_default)

  parser.set_defaults(tcxo=TCXOPoly(()))

  return parser


def selectOutputConfig(profileName):
  if profileName == "low_rate":
    outputConfig = LowRateConfig
  elif profileName == "normal_rate":
    outputConfig = NormalRateConfig
  elif profileName == "high_rate":
    outputConfig = HighRateConfig
  elif profileName == "custom_rate":
    outputConfig = CustomRateConfig
  else:
    raise ValueError()
  return outputConfig


def printOutputConfig(outputConfig, args):
  '''
  Configuration print
  '''
  print "Output configuration:"
  print "  Description:     ", outputConfig.NAME
  print "  Sampling rate:   ", outputConfig.SAMPLE_RATE_HZ
  print "  Batch size:      ", outputConfig.SAMPLE_BATCH_SIZE
  print "  GPS L1 IF:       ", outputConfig.GPS.L1.INTERMEDIATE_FREQUENCY_HZ
  print "  GPS L2 IF:       ", outputConfig.GPS.L2.INTERMEDIATE_FREQUENCY_HZ
  print "  GLONASS L1[0] IF:",\
    outputConfig.GLONASS.L1.INTERMEDIATE_FREQUENCIES_HZ[0]
  print "  GLONASS L2[0] IF:",\
    outputConfig.GLONASS.L2.INTERMEDIATE_FREQUENCIES_HZ[0]
  print "Other parameters:"
  print "  TCXO:           ", args.tcxo
  print "  noise sigma:    ", args.noise_sigma
  print "  satellites:     ", [sv.getName() for sv in args.gps_sv]
  print "  group delays:    ", args.group_delays


def computeEnabledBands(signalSources, outputConfig):
  '''
  Computes enabled bands from the signal source list

  Parameters
  ----------
  signalSources : array-like
    List of SV objects to query
  outputConfig : object
    Output configuration object with bands

  Returns
  -------
  map
    Map with band names as keys and boolean flags as values
  '''
  result = {}
  bands = [outputConfig.GPS.L1,
           outputConfig.GPS.L2,
           outputConfig.GLONASS.L1,
           outputConfig.GLONASS.L2]
  for band in bands:
    bandEnabled = False
    for sv in signalSources:
      if sv.isBandEnabled(band, outputConfig):
        bandEnabled = True
        break
    result[band.NAME] = bandEnabled

  return result


def selectEncoder(encoderType, outputConfig, enabledBands):
  '''
  Selects an appropriate encoder based on enabled bands and configuration

  Parameters
  ----------
  encoderType : string
    User-requested sample encoding format
  outputConfig : object
    Band configuration
  enabledBands : map
    Map contains flags for supported bands
  '''
  enabledGPSL1 = enabledBands[outputConfig.GPS.L1.NAME]
  enabledGPSL2 = enabledBands[outputConfig.GPS.L2.NAME]
  enabledGLONASSL1 = enabledBands[outputConfig.GLONASS.L1.NAME]
  enabledGLONASSL2 = enabledBands[outputConfig.GLONASS.L2.NAME]

  enabledGPS = enabledGPSL1 or enabledGPSL2
  enabledGLONASS = enabledGLONASSL1 or enabledGLONASSL2
  # Configure data encoder
  if encoderType == "1bit":
    if enabledGPS and enabledGLONASS:
      encoder = GPSGLONASSBitEncoder(outputConfig)
    elif enabledGPS:
      if enabledGPSL1 and enabledGPSL2:
        encoder = GPSL1L2BitEncoder(outputConfig)
      elif enabledGPSL2:
        encoder = GPSL2BitEncoder(outputConfig)
      else:
        encoder = GPSL1BitEncoder(outputConfig)
    elif enabledGLONASS:
      if enabledGLONASSL1 and enabledGLONASSL2:
        encoder = GLONASSL1L2BitEncoder(outputConfig)
      elif enabledGLONASSL2:
        encoder = GLONASSL2BitEncoder(outputConfig)
      else:
        encoder = GLONASSL1BitEncoder(outputConfig)
  elif encoderType == "2bits":
    if enabledGPS and enabledGLONASS:
      encoder = GPSGLONASSTwoBitsEncoder(outputConfig)
    elif enabledGPS:
      if enabledGPSL1 and enabledGPSL2:
        encoder = GPSL1L2TwoBitsEncoder(outputConfig)
      elif enabledGPSL2:
        encoder = GPSL2TwoBitsEncoder(outputConfig)
      else:
        encoder = GPSL1TwoBitsEncoder(outputConfig)
    elif enabledGLONASS:
      if enabledGLONASSL1 and enabledGLONASSL2:
        encoder = GLONASSL1L2TwoBitsEncoder(outputConfig)
      elif enabledGLONASSL2:
        encoder = GLONASSL2TwoBitsEncoder(outputConfig)
      else:
        encoder = GLONASSL1TwoBitsEncoder(outputConfig)
  else:
    raise ValueError("Encoder type is not supported")

  return encoder


def makeProgressBar(progressBarOutput, nSamples):
  '''
  Helper for initializing progress bar object

  Parameters
  ----------
  progressBarOutput : string
    Output object type for progress bar. Can be 'stderr' or 'stdout'.
  nSamples : long
    Total number of samples for object initialization

  Returns
  -------
  progressbar.ProgressBar or None
    Returns ProgressBar object if enabled, or None
  '''
  pbar = None
  if hasProgressBar:
    if progressBarOutput == 'stdout':
      show_progress = True
      progress_fd = sys.stdout
    elif progressBarOutput == 'stderr':
      show_progress = True
      progress_fd = sys.stderr
    else:
      show_progress = False
      progress_fd = -1
    if show_progress:
      widgets = ['Generating ',
                 progressbar.Counter(), ' ',
                 progressbar.Percentage(), ' ',
                 progressbar.ETA(), ' ',
                 progressbar.Bar()]
      pbar = progressbar.ProgressBar(widgets=widgets,
                                     maxval=nSamples,
                                     fd=progress_fd).start()
  return pbar


def main(args=None):
  default_logging_config()

  parser = prepareArgsParser()
  args = parser.parse_args(args)

  if args.no_run:
    return 0

  if args.output is None:
    parser.print_help()
    return 0

  outputConfig = selectOutputConfig(args.profile)
  printOutputConfig(outputConfig, args)

  # Check which signals are enabled on each of satellite to select proper
  # output encoder
  enabledBands = computeEnabledBands(args.gps_sv, outputConfig)

  enabledGPSL1 = enabledBands[outputConfig.GPS.L1.NAME]
  enabledGPSL2 = enabledBands[outputConfig.GPS.L2.NAME]

  # Configure data encoder
  encoder = selectEncoder(args.encoder, outputConfig, enabledBands)

  if enabledGPSL1:
    signal = signals.GPS.L1CA
  elif enabledGPSL2:
    signal = signals.GPS.L2C
  else:
    signal = signals.GPS.L1CA

  # Compute time delay for the needed bit/chip number
  # This delay is computed for the first satellite
  initial_symbol_idx = 0  # Initial symbol index
  initial_chip_idx = 0  # Initial chip index
  if args.chip_delay is not None:
    initial_chip_idx = args.chip_delay
  if args.symbol_delay is not None:
    initial_chip_idx = args.symbol_delay

  time0_s = computeTimeDelay(args.gps_sv[0].doppler,
                             initial_symbol_idx,
                             initial_chip_idx,
                             signal)
  logger.debug("Computed symbol/chip delay={} seconds".format(time0_s))

  startTime_s = time.time()
  n_samples = long(outputConfig.SAMPLE_RATE_HZ * args.generate)

  logger.debug("Generating {} samples for {} seconds".
               format(n_samples, args.generate))

  pbar = makeProgressBar(args.progress_bar, n_samples)

  generateSamples(args.output,
                  args.gps_sv,
                  encoder,
                  time0_s,
                  n_samples,
                  outputConfig,
                  tcxo=args.tcxo,
                  noiseSigma=args.noise_sigma,
                  filterType=args.filter_type,
                  groupDelays=args.group_delays,
                  logFile=args.debug,
                  threadCount=args.jobs,
                  pbar=pbar)
  args.output.close()
  if pbar is not None:
    pbar.finish()

  duration_s = time.time() - startTime_s
  ratio = n_samples / duration_s
  logger.debug("Total time = {} sec. Ratio={} samples per second".
               format(duration_s, ratio))

if __name__ == '__main__':
  main()

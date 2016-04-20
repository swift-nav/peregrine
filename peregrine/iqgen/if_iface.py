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
The :mod:`peregrine.iqgen.if_iface` module contains classes and functions
related to radio interface parameters

"""

from peregrine.defaults import freq_profile_peregrine
from peregrine.defaults import freq_profile_low_rate
from peregrine.defaults import freq_profile_normal_rate

# Fixed band names
GPS_L1_NAME = "GPS_L1"
GPS_L2_NAME = "GPS_L2"
GLONASS_L1_NAME = "GLO_L1"
GLONASS_L2_NAME = "GLO_L2"
GALILEO_E1_NAME = 'GALILEO_E1'
GALILEO_E5B_NAME = 'GALILEO_E5b'
GALILEO_E6_NAME = 'GALILEO_E6'
BEIDOU_B1_NAME = 'BEIDOU_B1'
BEIDOU_B2_NAME = 'BEIDOU_B2'
BEIDOU_B3_NAME = 'BEIDOU_B3'

# Fixed band names
GPS_L1_NAME = "GPS_L1"
GPS_L2_NAME = "GPS_L2"
GLONASS_L1_NAME = "GLO_L1"
GLONASS_L2_NAME = "GLO_L2"
GALILEO_E1_NAME = 'GALILEO_E1'
GALILEO_E5B_NAME = 'GALILEO_E5b'
GALILEO_E6_NAME = 'GALILEO_E6'
BEIDOU_B1_NAME = 'BEIDOU_B1'
BEIDOU_B2_NAME = 'BEIDOU_B2'
BEIDOU_B3_NAME = 'BEIDOU_B3'


class LowRateConfig(object):
  '''
  Output control configuration for quick tests.

  Attributes
  ----------
  NAME : string
    Configuration name
  SAMPLE_RATE_HZ : float
    Sample rate in hertz for data generation.
  SAMPLE_BATCH_SIZE : int
    Size of the sample batch in samples.
  N_GROUPS : int
    Number of groups in the configuration
  GROUP_DELAYS: tuple(float * 4)
    Group delays for the configuration
  GPS : object
    GPS band information
  Galileo : object
    Galileo band information
  Beidou : object
    Beidou band information
  GLONASS : object
    Glonass band information
  '''
  NAME = "Low rate configuration for fast tests"
  SAMPLE_RATE_HZ = 24.84375e5
  SAMPLE_BATCH_SIZE = 100000
  N_GROUPS = 4
  GROUP_DELAYS = (0., 0., 0., 0.)

  class GPS(object):

    class L1(object):
      INTERMEDIATE_FREQUENCY_HZ = freq_profile_low_rate['GPS_L1_IF']
      INDEX = 0
      NAME = GPS_L1_NAME

    class L2(object):
      INTERMEDIATE_FREQUENCY_HZ = freq_profile_low_rate['GPS_L2_IF']
      INDEX = 1
      NAME = GPS_L2_NAME

  class GLONASS(object):

    class L1(object):
      INTERMEDIATE_FREQUENCIES_HZ = \
          [float(1200000 + b * 562500) for b in range(7)] + \
          [float(1200000 + b * 562500) for b in range(-7, 0)]
      INDEX = 2
      NAME = GLONASS_L1_NAME

    class L2(object):
      INTERMEDIATE_FREQUENCIES_HZ = \
          [float(1100000 + b * 437500) for b in range(7)] + \
          [float(1100000 + b * 437500) for b in range(-7, 0)]
      INDEX = 3
      NAME = GLONASS_L2_NAME

  class Galileo(object):

    class E1(object):
      INTERMEDIATE_FREQUENCY_HZ = 14.58e5
      INDEX = 0
      NAME = GALILEO_E1_NAME

    class E6(object):
      INTERMEDIATE_FREQUENCY_HZ = 43.75e5
      INDEX = 2
      NAME = GALILEO_E6_NAME

    class E5b(object):
      INTERMEDIATE_FREQUENCY_HZ = 27.86e5
      INDEX = 3
      NAME = GALILEO_E5B_NAME

  class Beidou(object):

    class B1(object):
      INTERMEDIATE_FREQUENCY_HZ = 28.902e5
      INDEX = 0
      NAME = BEIDOU_B1_NAME

    class B2:
      INTERMEDIATE_FREQUENCY_HZ = 27.86e5
      INDEX = 3
      NAME = BEIDOU_B2_NAME

    class B3(object):
      INTERMEDIATE_FREQUENCY_HZ = 33.52e5
      INDEX = 2
      NAME = BEIDOU_B3_NAME


class NormalRateConfig(object):
  '''
  Output control configuration for normal tests.

  Attributes
  ----------
  NAME : string
    Configuration name
  SAMPLE_RATE_HZ : float
    Sample rate in hertz for data generation.
  SAMPLE_BATCH_SIZE : int
    Size of the sample batch in samples.
  N_GROUPS : int
    Number of groups in the configuration
  GROUP_DELAYS: tuple(float * 4)
    Group delays for the configuration
  GPS : object
    GPS band information
  Galileo : object
    Galileo band information
  Beidou : object
    Beidou band information
  GLONASS : object
    Glonass band information
  '''
  NAME = "Normal rate configuration equivalent to decimated data output"
  SAMPLE_RATE_HZ = 24.84375e6
  SAMPLE_BATCH_SIZE = 100000
  N_GROUPS = LowRateConfig.N_GROUPS
  GROUP_DELAYS = LowRateConfig.GROUP_DELAYS

  class GPS(object):
    '''
    Parameters for GPS bands data generation.
    '''
    class L1(object):
      INTERMEDIATE_FREQUENCY_HZ = freq_profile_normal_rate['GPS_L1_IF']
      INDEX = 0
      NAME = GPS_L1_NAME

    class L2(object):
      INTERMEDIATE_FREQUENCY_HZ = freq_profile_normal_rate['GPS_L2_IF']
      INDEX = 1
      NAME = GPS_L2_NAME

  class GLONASS(object):

    class L1(object):
      INTERMEDIATE_FREQUENCIES_HZ = \
          [float(12000000l + b * 562500l) for b in range(7)] + \
          [float(12000000l + b * 562500l) for b in range(-7, 0)]
      INDEX = 2
      NAME = GLONASS_L1_NAME

    class L2(object):
      INTERMEDIATE_FREQUENCIES_HZ = \
          [float(11000000l + b * 437500l) for b in range(7)] + \
          [float(11000000l + b * 437500l) for b in range(-7, 0)]
      INDEX = 3
      NAME = GLONASS_L2_NAME

  class Galileo(object):

    class E1(object):
      INTERMEDIATE_FREQUENCY_HZ = 14.58e6
      INDEX = 0
      NAME = GALILEO_E1_NAME

    class E6(object):
      INTERMEDIATE_FREQUENCY_HZ = 43.75e6
      INDEX = 2
      NAME = GALILEO_E6_NAME

    class E5b(object):
      INTERMEDIATE_FREQUENCY_HZ = 27.86e6
      INDEX = 3
      NAME = GALILEO_E5B_NAME

  class Beidou(object):

    class B1(object):
      INTERMEDIATE_FREQUENCY_HZ = 28.902e6
      INDEX = 0
      NAME = BEIDOU_B1_NAME

    class B2:
      INTERMEDIATE_FREQUENCY_HZ = 27.86e6
      INDEX = 3
      NAME = BEIDOU_B2_NAME

    class B3(object):
      INTERMEDIATE_FREQUENCY_HZ = 33.52e6
      INDEX = 2
      NAME = BEIDOU_B3_NAME


class HighRateConfig(object):
  '''
  Output control configuration for high data rate tests.

  Attributes
  ----------
  NAME : string
    Configuration name
  SAMPLE_RATE_HZ : float
    Sample rate in hertz for data generation.
  SAMPLE_BATCH_SIZE : int
    Size of the sample batch in samples.
  N_GROUPS : int
    Number of groups in the configuration
  GROUP_DELAYS: tuple(float * 4)
    Group delays for the configuration
  GPS : object
    GPS band information
  Galileo : object
    Galileo band information
  Beidou : object
    Beidou band information
  GLONASS : object
    Glonass band information
  '''
  NAME = "High rate configuration equivalent to full rate data output"
  SAMPLE_RATE_HZ = 99.375e6
  SAMPLE_BATCH_SIZE = 100000
  N_GROUPS = NormalRateConfig.N_GROUPS
  GROUP_DELAYS = NormalRateConfig.GROUP_DELAYS

  GPS = NormalRateConfig.GPS
  GLONASS = NormalRateConfig.GLONASS
  Galileo = NormalRateConfig.Galileo
  Beidou = NormalRateConfig.Beidou


class CustomRateConfig(object):
  '''
  Output control configuration for comparison tests.

  Attributes
  ----------
  NAME : string
    Configuration name
  SAMPLE_RATE_HZ : float
    Sample rate in hertz for data generation.
  SAMPLE_BATCH_SIZE : int
    Size of the sample batch in samples.
  N_GROUPS : int
    Number of groups in the configuration
  GROUP_DELAYS: tuple(float * 4)
    Group delays for the configuration
  GPS : object
    GPS band information
  '''
  NAME = "Custom configuration for fast tests"
  SAMPLE_RATE_HZ = freq_profile_peregrine['sampling_freq']
  SAMPLE_BATCH_SIZE = 100000
  N_GROUPS = NormalRateConfig.N_GROUPS
  GROUP_DELAYS = NormalRateConfig.GROUP_DELAYS

  class GPS(object):

    class L1(object):
      INTERMEDIATE_FREQUENCY_HZ = freq_profile_peregrine['GPS_L1_IF']
      INDEX = 0
      NAME = GPS_L1_NAME

    class L2(object):
      INTERMEDIATE_FREQUENCY_HZ = freq_profile_peregrine['GPS_L2_IF']
      INDEX = 1
      NAME = GPS_L2_NAME

  class GLONASS(object):

    class L1(object):
      INTERMEDIATE_FREQUENCIES_HZ = \
          [float(6000000l + b * 562500l) for b in range(7)] + \
          [float(6000000l + b * 562500l) for b in range(-7, 0)]
      INDEX = 2
      NAME = GLONASS_L1_NAME

    class L2(object):
      INTERMEDIATE_FREQUENCIES_HZ = \
          [float(6000000l + b * 437500l) for b in range(7)] + \
          [float(6000000l + b * 437500l) for b in range(-7, 0)]
      INDEX = 3
      NAME = GLONASS_L2_NAME

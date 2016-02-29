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
  GPS : object
    GPS band information
  Galileo : object
    Galileo band information
  Beidou : object
    Beidou band information
  Glonass : object
    Glonass band information
  '''
  NAME = "Low rate configuration for fast tests"
  SAMPLE_RATE_HZ = 24.84375e5
  SAMPLE_BATCH_SIZE = 100000

  class GPS(object):

    class L1(object):
      INTERMEDIATE_FREQUENCY_HZ = 14.58e5
      INDEX = 0

    class L2(object):
      INTERMEDIATE_FREQUENCY_HZ = 7.4e+5
      INDEX = 1

  class Glonass(object):

    class L1(object):
      INTERMEDIATE_FREQUENCY_HZ = 12e5
      INDEX = 1

    class L2(object):
      INTERMEDIATE_FREQUENCY_HZ = 11e5
      INDEX = 2

  class Galileo(object):

    class E1(object):
      INTERMEDIATE_FREQUENCY_HZ = 14.58e5
      INDEX = 0

    class E6(object):
      INTERMEDIATE_FREQUENCY_HZ = 43.75e5
      INDEX = 2

    class E5b(object):
      INTERMEDIATE_FREQUENCY_HZ = 27.86e5
      INDEX = 3

  class Beidou(object):

    class B1(object):
      INTERMEDIATE_FREQUENCY_HZ = 28.902e5
      INDEX = 0

    class B2:
      INTERMEDIATE_FREQUENCY_HZ = 27.86e5
      INDEX = 3

    class B3(object):
      INTERMEDIATE_FREQUENCY_HZ = 33.52e5
      INDEX = 2


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
  GPS : object
    GPS band information
  Galileo : object
    Galileo band information
  Beidou : object
    Beidou band information
  Glonass : object
    Glonass band information
  '''
  NAME = "Normal rate configuration equivalent to decimated data output"
  SAMPLE_RATE_HZ = 24.84375e6
  SAMPLE_BATCH_SIZE = 100000

  class GPS(object):
    '''
    Parameters for GPS bands data generation.
    '''
    class L1(object):
      INTERMEDIATE_FREQUENCY_HZ = 14.58e+6
      INDEX = 0

    class L2(object):
      INTERMEDIATE_FREQUENCY_HZ = 7.4e+6
      INDEX = 1

  class Glonass(object):

    class L1(object):
      INTERMEDIATE_FREQUENCY_HZ = 12e6
      INDEX = 1

    class L2(object):
      INTERMEDIATE_FREQUENCY_HZ = 11e6
      INDEX = 2

  class Galileo(object):

    class E1(object):
      INTERMEDIATE_FREQUENCY_HZ = 14.58e6
      INDEX = 0

    class E6(object):
      INTERMEDIATE_FREQUENCY_HZ = 43.75e6
      INDEX = 2

    class E5b(object):
      INTERMEDIATE_FREQUENCY_HZ = 27.86e6
      INDEX = 3

  class Beidou(object):

    class B1(object):
      INTERMEDIATE_FREQUENCY_HZ = 28.902e6
      INDEX = 0

    class B2:
      INTERMEDIATE_FREQUENCY_HZ = 27.86e6
      INDEX = 3

    class B3(object):
      INTERMEDIATE_FREQUENCY_HZ = 33.52e6
      INDEX = 2


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
  GPS : object
    GPS band information
  '''
  NAME = "High rate configuration equivalent to full rate data output"
  SAMPLE_RATE_HZ = 99.375e6
  SAMPLE_BATCH_SIZE = 100000

  GPS = NormalRateConfig.GPS
  Glonass = NormalRateConfig.Glonass
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
  GPS : object
    GPS band information
  '''
  NAME = "Custom configuration for fast tests"
  SAMPLE_RATE_HZ = freq_profile_peregrine['sampling_freq']
  SAMPLE_BATCH_SIZE = 100000

  class GPS(object):

    class L1(object):
      INTERMEDIATE_FREQUENCY_HZ = freq_profile_peregrine['GPS_L1_IF']
      INDEX = 0

    class L2(object):
      INTERMEDIATE_FREQUENCY_HZ = freq_profile_peregrine['GPS_L2_IF']
      INDEX = 1

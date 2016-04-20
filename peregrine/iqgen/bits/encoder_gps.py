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
The :mod:`peregrine.iqgen.bits.encoder_gps` module contains classes and
functions related to generating GPS signal output.

"""

from peregrine.iqgen.bits.encoder_1bit import BandBitEncoder
from peregrine.iqgen.bits.encoder_1bit import TwoBandsBitEncoder
from peregrine.iqgen.bits.encoder_2bits import BandTwoBitsEncoder
from peregrine.iqgen.bits.encoder_2bits import TwoBandsTwoBitsEncoder


class GPSL1BitEncoder(BandBitEncoder):
  '''
  Generic single bit encoder for GPS L1 C/A signal
  '''

  def __init__(self, outputConfig):
    '''
    Constructs GPS L1 C/A band single bit encoder object.

    Parameters
    ----------
    outputConfig : object
      Output parameters object.
    '''
    super(GPSL1BitEncoder, self).__init__(outputConfig.GPS.L1.INDEX)


class GPSL2BitEncoder(BandBitEncoder):
  '''
  Generic single bit encoder for GPS L2 Civil signal
  '''

  def __init__(self, outputConfig):
    '''
    Constructs GPS L2 C band single bit encoder object.

    Parameters
    ----------
    outputConfig : object
      Output parameters object.
    '''
    super(GPSL2BitEncoder, self).__init__(outputConfig.GPS.L2.INDEX)


class GPSL1L2BitEncoder(TwoBandsBitEncoder):
  '''
  Generic single bit encoder for GPS L1 C/A and L2 Civil signals
  '''

  def __init__(self, outputConfig):
    '''
    Constructs GPS L1 C/A and L2 C dual band single bit encoder object.

    Parameters
    ----------
    outputConfig : object
      Output parameters object.
    '''
    super(GPSL1L2BitEncoder, self).__init__(outputConfig.GPS.L1.INDEX,
                                            outputConfig.GPS.L2.INDEX)


class GPSL1TwoBitsEncoder(BandTwoBitsEncoder):
  '''
  Generic single bit encoder for GPS L1 C/A signal
  '''

  def __init__(self, outputConfig):
    '''
    Constructs GPS L1 C/A band single bit encoder object.

    Parameters
    ----------
    outputConfig : object
      Output parameters object.
    '''
    super(GPSL1TwoBitsEncoder, self).__init__(outputConfig.GPS.L1.INDEX)


class GPSL2TwoBitsEncoder(BandTwoBitsEncoder):
  '''
  Generic single bit encoder for GPS L2 Civil signal
  '''

  def __init__(self, outputConfig):
    '''
    Constructs GPS L2 C band single bit encoder object.

    Parameters
    ----------
    outputConfig : object
      Output parameters object.
    '''
    super(GPSL2TwoBitsEncoder, self).__init__(outputConfig.GPS.L2.INDEX)


class GPSL1L2TwoBitsEncoder(TwoBandsTwoBitsEncoder):
  '''
  Generic single bit encoder for GPS L1 C/A and L2 Civil signals
  '''

  def __init__(self, outputConfig):
    '''
    Constructs GPS L1 C/A and L2 C dual band single bit encoder object.

    Parameters
    ----------
    outputConfig : object
      Output parameters object.
    '''
    super(GPSL1L2TwoBitsEncoder, self).__init__(outputConfig.GPS.L1.INDEX,
                                                outputConfig.GPS.L2.INDEX)

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
The :mod:`peregrine.iqgen.bits.encoder_glo` module contains classes and
functions related to generating GLONASS signal output.

"""

from peregrine.iqgen.bits.encoder_1bit import BandBitEncoder
from peregrine.iqgen.bits.encoder_1bit import TwoBandsBitEncoder
from peregrine.iqgen.bits.encoder_2bits import BandTwoBitsEncoder
from peregrine.iqgen.bits.encoder_2bits import TwoBandsTwoBitsEncoder


class GLONASSL1BitEncoder(BandBitEncoder):
  '''
  Generic single bit encoder for GLPNASS L1 signal
  '''

  def __init__(self, outputConfig):
    '''
    Constructs GLONASS L1 band single bit encoder object.

    Parameters
    ----------
    outputConfig : object
      Output parameters object.
    '''
    super(GLONASSL1BitEncoder, self).__init__(outputConfig.GLONASS.L1.INDEX)


class GLONASSL2BitEncoder(BandBitEncoder):
  '''
  Generic single bit encoder for GLONASS L2 signal
  '''

  def __init__(self, outputConfig):
    '''
    Constructs GLONASS L2 band single bit encoder object.

    Parameters
    ----------
    outputConfig : object
      Output parameters object.
    '''
    super(GLONASSL2BitEncoder, self).__init__(outputConfig.GLONASS.L2.INDEX)


class GLONASSL1L2BitEncoder(TwoBandsBitEncoder):
  '''
  Generic single bit encoder for GLONASS L1 and L2 signals
  '''

  def __init__(self, outputConfig):
    '''
    Constructs GLONASS L1 and L2 dual band single bit encoder object.

    Parameters
    ----------
    outputConfig : object
      Output parameters object.
    '''
    super(GLONASSL1L2BitEncoder, self).__init__(outputConfig.GLONASS.L1.INDEX,
                                                outputConfig.GLONASS.L2.INDEX)


class GLONASSL1TwoBitsEncoder(BandTwoBitsEncoder):
  '''
  Generic single bit encoder for GLONASS L1 signal
  '''

  def __init__(self, outputConfig):
    '''
    Constructs GLONASS L1 band single bit encoder object.

    Parameters
    ----------
    outputConfig : object
      Output parameters object.
    '''
    super(GLONASSL1TwoBitsEncoder, self).__init__(
        outputConfig.GLONASS.L1.INDEX)


class GLONASSL2TwoBitsEncoder(BandTwoBitsEncoder):
  '''
  Generic single bit encoder for GLONASS L2 Civil signal
  '''

  def __init__(self, outputConfig):
    '''
    Constructs GLONASS L2 C band single bit encoder object.

    Parameters
    ----------
    outputConfig : object
      Output parameters object.
    '''
    super(GLONASSL2TwoBitsEncoder, self).__init__(
        outputConfig.GLONASS.L2.INDEX)


class GLONASSL1L2TwoBitsEncoder(TwoBandsTwoBitsEncoder):
  '''
  Generic single bit encoder for GLONASS L1 and L2 signals
  '''

  def __init__(self, outputConfig):
    '''
    Constructs GLONASS L1 and L2 dual band single bit encoder object.

    Parameters
    ----------
    outputConfig : object
      Output parameters object.
    '''
    super(GLONASSL1L2TwoBitsEncoder, self).__init__(outputConfig.GLONASS.L1.INDEX,
                                                    outputConfig.GLONASS.L2.INDEX)

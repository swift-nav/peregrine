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
The :mod:`peregrine.iqgen.bits.encoder_other` module contains classes and
functions related to generating combined signal output.

"""

from peregrine.iqgen.bits.encoder_1bit import FourBandsBitEncoder
from peregrine.iqgen.bits.encoder_2bits import FourBandsTwoBitsEncoder


class GPSGLONASSBitEncoder(FourBandsBitEncoder):
  '''
  Generic single bit encoder for GPS and GLINASS signals (4 bands)
  '''

  def __init__(self, outputConfig):
    '''
    Constructs four band single bit encoder object.

    Parameters
    ----------
    outputConfig : object
      Output parameters object.
    '''
    super(GPSGLONASSBitEncoder, self).__init__(outputConfig.GPS.L2.INDEX,
                                               outputConfig.GLONASS.L2.INDEX,
                                               outputConfig.GLONASS.L1.INDEX,
                                               outputConfig.GPS.L1.INDEX)


class GPSGLONASSTwoBitsEncoder(FourBandsTwoBitsEncoder):
  '''
  Generic dual bit encoder for GPS and GLONASS signals (four bands)
  '''

  def __init__(self, outputConfig):
    '''
    Constructs four band dual bit encoder object.

    Parameters
    ----------
    outputConfig : object
      Output parameters object.
    '''
    super(GPSGLONASSTwoBitsEncoder, self).__init__(outputConfig.GPS.L2.INDEX,
                                                   outputConfig.GLONASS.L2.INDEX,
                                                   outputConfig.GLONASS.L1.INDEX,
                                                   outputConfig.GPS.L1.INDEX)

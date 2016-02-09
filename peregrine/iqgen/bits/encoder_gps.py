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

from peregrine.iqgen.bits.encoder_base import Encoder
from peregrine.iqgen.bits.encoder_1bit import BandBitEncoder
from peregrine.iqgen.bits.encoder_2bits import BandTwoBitsEncoder


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


class GPSL1L2BitEncoder(Encoder):
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
    super(GPSL1L2BitEncoder, self).__init__()
    self.l1Index = outputConfig.GPS.L1.INDEX
    self.l2Index = outputConfig.GPS.L2.INDEX

  def addSamples(self, sample_array):
    '''
    Extracts samples of the supported band and coverts them into bit stream.

    Parameters
    ----------
    sample_array : numpy.ndarray((4, N))
      Sample vectors ordered by band index.

    Returns
    -------
    numpy.ndarray(dtype=numpy.uint8)
      Array of type uint8 containing the encoded data.
    '''
    band1_bits = BandBitEncoder.convertBand(sample_array[self.l1Index])
    band2_bits = BandBitEncoder.convertBand(sample_array[self.l2Index])
    n_samples = len(band1_bits)

    self.ensureExtraCapacity(n_samples * 2)
    start = self.n_bits
    end = start + 2 * n_samples

    self.bits[start + 0:end:2] = band1_bits
    self.bits[start + 1:end:2] = band2_bits
    self.n_bits = end

    if (self.n_bits >= Encoder.BLOCK_SIZE):
      return self.encodeValues()
    else:
      return Encoder.EMPTY_RESULT


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


class GPSL1L2TwoBitsEncoder(Encoder):
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
    super(GPSL1L2TwoBitsEncoder, self).__init__()
    self.l1Index = outputConfig.GPS.L1.INDEX
    self.l2Index = outputConfig.GPS.L2.INDEX

  def addSamples(self, sample_array):
    '''
    Extracts samples of the supported band and coverts them into bit stream.

    Parameters
    ----------
    sample_array : numpy.ndarray((4, N))
      Sample vectors ordered by band index.

    Returns
    -------
    numpy.ndarray(dtype=numpy.uint8)
      Array of type uint8 containing the encoded data.
    '''
    band1_samples = sample_array[self.l1Index]
    band2_samples = sample_array[self.l2Index]
    n_samples = len(band1_samples)

    # Signal signs and amplitude
    signs1, amps1 = BandTwoBitsEncoder.convertBand(band1_samples)
    signs2, amps2 = BandTwoBitsEncoder.convertBand(band2_samples)

    self.ensureExtraCapacity(n_samples * 4)

    bits = self.bits
    start = self.n_bits
    end = start + 4 * n_samples
    bits[start + 0:end:4] = signs1
    bits[start + 1:end:4] = amps1
    bits[start + 2:end:4] = signs2
    bits[start + 3:end:4] = amps2
    self.n_bits = end

    if (self.n_bits >= Encoder.BLOCK_SIZE):
      return self.encodeValues()
    else:
      return Encoder.EMPTY_RESULT

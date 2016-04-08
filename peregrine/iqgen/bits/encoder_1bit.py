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
The :mod:`peregrine.iqgen.bits.encoder_1bit` module contains classes and
functions related to generating single bit signal output.

"""

from peregrine.iqgen.bits.encoder_base import Encoder


class BandBitEncoder(Encoder):
  '''
  Base class for single bit encoding.
  '''

  def __init__(self, bandIndex):
    '''
    Initializes encoder object.

    Parameters
    ----------
    bandIndex : int
      Index of the band in the generated sample matrix.
    '''
    super(BandBitEncoder, self).__init__()
    self.bandIndex = bandIndex

  def addSamples(self, sample_array):
    '''
    Extracts samples of the supported band and coverts them into bit stream.

    Parameters
    ----------
    sample_array : numpy.ndarray((4, N))
      Sample vectors ordered by band index.

    Returns
    -------
    numpy.ndarray((N), dtype=numpy.uint8)
      Array of type uint8 containing the encoded data.
    '''
    band_samples = sample_array[self.bandIndex]
    n_samples = len(band_samples)

    self.ensureExtraCapacity(n_samples)
    start = self.n_bits
    end = start + n_samples
    self.bits[start:end] = BandBitEncoder.convertBand(band_samples)
    self.n_bits = end

    if (self.n_bits >= Encoder.BLOCK_SIZE):
      return self.encodeValues()

    return Encoder.EMPTY_RESULT

  @staticmethod
  def convertBand(band_samples):
    '''
    Helper method for converting sampled signal band into output bits.

    The samples are compared to 0. Positive values yield value of False.

    Parameters
    ----------
    band_samples : numpy.ndarray((N))
      Vector of signal samples

    Returns
    -------
    signs : numpy.ndarray((N), dtype=numpy.bool)
      Boolean vector of sample signs
    '''
    return band_samples < 0


class TwoBandsBitEncoder(Encoder):
  '''
  Generic single bit encoder for two band signals
  '''

  def __init__(self, band1, band2):
    '''
    Constructs GPS L1 C/A and L2 C dual band single bit encoder object.

    Parameters
    ----------
    outputConfig : object
      Output parameters object.
    '''
    super(TwoBandsBitEncoder, self).__init__()
    self.l1Index = band1
    self.l2Index = band2

  def addSamples(self, sample_array):
    '''
    Extracts samples of the supported band and converts them into bit stream.

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


class FourBandsBitEncoder(Encoder):
  '''
  Generic single bit encoder for two band signals
  '''

  def __init__(self, band1, band2, band3, band4):
    '''
    Constructs GPS L1 C/A and L2 C dual band single bit encoder object.

    Parameters
    ----------
    outputConfig : object
      Output parameters object.
    '''
    super(FourBandsBitEncoder, self).__init__()
    self.bandIndexes = [band1, band2, band3, band4]

  def addSamples(self, sample_array):
    '''
    Extracts samples of the supported band and converts them into bit stream.

    Parameters
    ----------
    sample_array : numpy.ndarray((4, N))
      Sample vectors ordered by band index.

    Returns
    -------
    numpy.ndarray(shape=(4, N/2), dtype=numpy.uint8)
      Array of type uint8 containing the encoded data.
    '''
    n_samples = len(sample_array[0])
    self.ensureExtraCapacity(n_samples * 4)
    start = self.n_bits
    end = start + 4 * n_samples

    for band in range(4):
      bandIndex = self.bandIndexes[band]
      band_bits = BandBitEncoder.convertBand(sample_array[bandIndex])
      self.bits[start + band:end:4] = band_bits

    self.n_bits = end

    if (self.n_bits >= Encoder.BLOCK_SIZE):
      return self.encodeValues()
    else:
      return Encoder.EMPTY_RESULT

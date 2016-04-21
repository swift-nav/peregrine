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
The :mod:`peregrine.iqgen.bits.encoder_2bits` module contains classes and
functions related to generating two bits signal output.

"""

import numpy

from peregrine.iqgen.bits.encoder_base import Encoder


class BandTwoBitsEncoder(Encoder):
  '''
  Base class for two bits encoding.
  '''
  # Minimum is 1.2 dB. Can be up to 3.5 dB.
  # See Global Positioning System: Theory and Applications
  ATT_LVL_DB = 1.2

  def __init__(self, bandIndex):
    '''
    Initializes encoder object.

    Parameters
    ----------
    bandIndex : int
      Index of the band in the generated sample matrix.
    '''
    super(BandTwoBitsEncoder, self).__init__(BandTwoBitsEncoder.ATT_LVL_DB)
    self.bandIndex = bandIndex

  @staticmethod
  def convertBand(band_samples):
    '''
    Helper method for converting sampled signal band into output bits.

    For the sign, the samples are compared to 0. Positive values yield sign of
    True.

    The method builds a power histogram from signal samples. After a histogram
    is built, the 67% power boundary is located. All samples, whose power is
    lower, than the boundary, are reported as False.

    Parameters
    ----------
    band_samples : numpy.ndarray
      Vector of signal samples

    Returns
    -------
    signs : numpy.ndarray(dtype=numpy.bool)
      Boolean vector of sample signs: True for positive, False for negative
    amps : numpy.ndarray(dtype=numpy.bool)
      Boolean vector of sample power: True for high power, False for low power
    '''

    # Signal power is a square of the amplitude
    power = numpy.square(band_samples)
    totalPower = numpy.sum(power)
    totalPowerLimit = totalPower * 0.67

    # Build histogram to find 67% power
    totalBins = 30
    hist, edges = numpy.histogram(power,
                                  bins=totalBins,
                                  density=False)
    avg = (edges[:-1] + edges[1:]) * 0.5
    powers = numpy.cumsum(hist * avg)
    idx = numpy.searchsorted(powers, totalPowerLimit, side="right")
    powerLimit = avg[idx]

    # Signal sign
    signs = band_samples > 0
    amps = power >= powerLimit

    return signs, amps

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
    band_samples = sample_array[self.bandIndex]
    n_samples = len(band_samples)

    # Signal signs and amplitude
    signs, amps = self.convertBand(band_samples)

    self.ensureExtraCapacity(n_samples * 2)

    bits = self.bits
    start = self.n_bits
    end = start + n_samples * 2
    bits[start + 0:end:2] = signs
    bits[start + 1:end:2] = amps
    self.n_bits = end

    if (self.n_bits >= Encoder.BLOCK_SIZE):
      return self.encodeValues()
    else:
      return Encoder.EMPTY_RESULT


class TwoBandsTwoBitsEncoder(Encoder):
  '''
  Generic single bit encoder for GPS L1 C/A and L2 Civil signals
  '''

  def __init__(self, bandIndex1, bandIndex2):
    '''
    Constructs GPS L1 C/A and L2 C dual band single bit encoder object.

    Parameters
    ----------
    outputConfig : object
      Output parameters object.
    '''
    super(TwoBandsTwoBitsEncoder, self).__init__(BandTwoBitsEncoder.ATT_LVL_DB)
    self.l1Index = bandIndex1
    self.l2Index = bandIndex2

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


class FourBandsTwoBitsEncoder(Encoder):
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
    super(FourBandsTwoBitsEncoder, self).__init__(
        BandTwoBitsEncoder.ATT_LVL_DB)
    self.bandIndexes = [band1, band2, band3, band4]

  def addSamples(self, sample_array):
    '''
    Extracts samples of the supported bands and converts them into bit stream.

    Parameters
    ----------
    sample_array : numpy.ndarray((4, N))
      Sample vectors ordered by band index.

    Returns
    -------
    numpy.ndarray(dtype=numpy.uint8)
      Array of type uint8 containing the encoded data.
    '''
    n_samples = len(sample_array[0])
    self.ensureExtraCapacity(n_samples * 8)
    start = self.n_bits
    end = start + 8 * n_samples
    bits = self.bits

    for band in range(4):
      bandIndex = self.bandIndexes[band]
      # Signal signs and amplitude
      signs, amps = BandTwoBitsEncoder.convertBand(sample_array[bandIndex])
      bits[start + band * 2 + 0:end:8] = signs
      bits[start + band * 2 + 1:end:8] = amps

    self.n_bits = end

    if (self.n_bits >= Encoder.BLOCK_SIZE):
      return self.encodeValues()
    else:
      return Encoder.EMPTY_RESULT

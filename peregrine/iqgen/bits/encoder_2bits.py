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

  def __init__(self, bandIndex):
    '''
    Initializes encoder object.

    Parameters
    ----------
    bandIndex : int
      Index of the band in the generated sample matrix.
    '''
    super(BandTwoBitsEncoder, self).__init__()
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

    # Build histrogram to find 67% power
    hist, edges = numpy.histogram(power,
                                  bins=10,
                                  density=True)
    lastPower = 0.
    powerLimit = 0.
    for i in range(10):
      # Approximate power of samples in the bin
      entryPower = hist[i] * (edges[i] + edges[i + 1]) / 2.
      newPower = lastPower + entryPower
      if newPower > totalPowerLimit:
        powerLimit = edges[i]
        break
      else:
        lastPower = newPower

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

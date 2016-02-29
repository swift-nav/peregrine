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
The :mod:`peregrine.iqgen.bits.encoder_base` module contains classes and
functions related to generating signal output.

"""

import numpy


class Encoder(object):
  '''
  Base encode class.

  Encoder accepts sequence of signal arrays as input and produces byte arrays
  as output.
  '''
  # Block size for encode. Must be a multiple of 8.
  BLOCK_SIZE = 1024 * 8

  EMPTY_RESULT = numpy.ndarray(0, dtype=numpy.uint8)  # Internal empty array

  def __init__(self, bufferSize=1000):
    '''
    Constructs encoder.

    Parameters
    ----------
    bufferSize : int, optional
      Size of the internal buffer to batch-process samples
    '''
    self.bits = numpy.ndarray(bufferSize, dtype=numpy.int8)
    self.n_bits = 0

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
    return Encoder.EMPTY_RESULT

  def flush(self):
    '''
    Flushes the data in the buffer.

    Returns
    -------
    ndarray
      Array of type uint8 containing the encoded data.
    '''
    if self.n_bits > 0 and self.n_bits % 8 != 0:
      self.bits += (8 - self.n_bits % 8)
    res = numpy.packbits(self.bits[0:self.n_bits])
    self.n_bits = 0
    return res

  def encodeValues(self):
    '''
    Converts buffered bit data into packed array.

    The method coverts multiple of 8 bits into single output byte.

    Returns
    -------
    ndarray
      Array of type uint8 containing the encoded data.
    '''
    n_bytes = self.n_bits / 8
    n_offset = n_bytes * 8
    n_left = self.n_bits - n_offset
    res = numpy.packbits(self.bits[0: n_offset])
    self.bits[0:n_left] = self.bits[n_offset:n_offset + n_left]
    self.n_bits = n_left
    return res

  def ensureExtraCapacity(self, extraBits):
    '''
    Method verifies that current array has sufficient capacity to hold
    additional bits.

    Parameters
    ----------
    extraBits : int
      Number of extra bits to reserve space for
    '''
    if len(self.bits) < self.n_bits + extraBits:
      self.bits.resize(self.n_bits + extraBits)

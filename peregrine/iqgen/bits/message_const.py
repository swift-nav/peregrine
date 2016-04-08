# Copyright (C) 2016 Swift Navigation Inc.
# Contact: Valeri Atamaniouk <valeri@swiftnav.com>
#
# This source is subject to the license found in the file 'LICENSE' which must
# be be distributed together with this source. All other rights reserved.
#
# THIS CODE AND INFORMATION IS PROVIDED "AS IS" WITHOUT WARRANTY OF ANY KIND,
# EITHER EXPRESSED OR IMPLIED, INCLUDING BUT NOT LIMITED TO THE IMPLIED
# WARRANTIES OF MERCHANTABILITY AND/OR FITNESS FOR A PARTICULAR PURPOSE.

import numpy

"""
The :mod:`peregrine.iqgen.bits.message_const` module contains classes and 
functions related to non-changing symbol contents.

"""


class Message(object):
  '''
  Message consisting of same bits
  '''

  def __init__(self, bitValue):
    '''
    Initializes object.

    Parameters
    ----------
    bitValue : int
      Value for the bits. 1 for 0 bits, -1 for 1 bits.
    '''
    super(Message, self).__init__()
    self.bitValue = bitValue
    self.binValue = 1 if bitValue < 0 else 0

  def __str__(self, *args, **kwargs):
    '''
    Formats object as string literal

    Returns
    -------
    string
      String representation of the object
    '''
    return "Const: bit value=%d" % self.binValue

  def getDataBits(self, dataAll_idx):
    '''
    Generates vector of data bits corresponding to input index

    Parameters
    ----------
    dataAll_idx : numpy.ndarray(dtype=numpy.int64)
      Vector of bit indexes

    Returns
    -------
    numpy.ndarray(dtype=numpy.uint8)
      Vector of data bits
    '''
    result = numpy.ndarray(len(dataAll_idx), dtype=numpy.uint8)
    result.fill(self.binValue)
    return result

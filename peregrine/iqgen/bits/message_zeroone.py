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
The :mod:`peregrine.iqgen.bits.message_zeroone` module contains classes and
functions related to symbol contents that flips the value every other bit.

"""

import numpy


class Message(object):
  '''
  Message that contains zeros and ones
  '''

  def __init__(self):
    '''
    Constructs object.
    '''
    super(Message, self).__init__()
    self.bits = numpy.asarray([0, 1], dtype=numpy.uint8)

  def __str__(self, *args, **kwargs):
    '''
    Formats object as string literal

    Returns
    -------
    string
      String representation of the object
    '''
    return "ZeroOne"

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
    # numpy.take degrades performance a lot over time.
    # return numpy.take(self.bits, dataAll_idx , mode='wrap')
    return self.bits[dataAll_idx & 1]

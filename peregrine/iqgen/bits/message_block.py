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
The :mod:`peregrine.iqgen.bits.message_block` module contains classes and
functions related to providing predefined symbol contents.

"""
import numpy


class Message(object):
  '''
  Message that is a block of bits
  '''

  def __init__(self, messageData):
    '''
    Constructs message object.

    Parameters
    ----------
    messageData : array-like
      Array with message bits. Bit 0 is encoded with 1, bit 1 is encoded with -1
    '''
    super(Message, self).__init__()
    self.messageData = messageData[:]
    self.messageLen = len(self.messageData)
    tmp = numpy.asarray(self.messageData, dtype=numpy.uint8)
    tmp *= -2
    tmp -= 1
    self.bits = tmp.astype(numpy.uint8)

  def __str__(self, *args, **kwargs):
    '''
    Formats object as string literal

    Returns
    -------
    string
      String representation of the object
    '''
    return "Block: length=%d" % len(self.bits)

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
    return self.bits[dataAll_idx % self.messageLen]

  def getBit(self, bitIndex):
    '''
    Provides bit at a given index

    Parameters
    ----------
    bitIndex : long
      Bit index

    Returns
    -------
    int
      Bit value: 1 for bit 0 and -1 for bit 1
    '''

    return self.messageData[bitIndex % self.messageLen]

# Copyright (C) 2016 Swift Navigation Inc.
# Contact: Valeri Atamaniouk <valeri@swiftnav.com>
#
# This source is subject to the license found in the file 'LICENSE' which must
# be be distributed together with this source. All other rights reserved.
#
# THIS CODE AND INFORMATION IS PROVIDED "AS IS" WITHOUT WARRANTY OF ANY KIND,
# EITHER EXPRESSED OR IMPLIED, INCLUDING BUT NOT LIMITED TO THE IMPLIED
# WARRANTIES OF MERCHANTABILITY AND/OR FITNESS FOR A PARTICULAR PURPOSE.

'''
The :mod:`peregrine.iqgen.bits.message_cnav` module contains classes and 
functions related to generating stub GPS CNAV messages.
'''

import numpy
from swiftnav.cnav_msg import CNavRawMsg
import logging
G1 = 0171  # generator polinomial for p1
G2 = 0133  # generator polinomial for p2

logger = logging.getLogger(__name__)


def generate27Vector(g1, g2):
  '''
  Helper method for convolution encoder lookup table generation.

  Parameters
  ----------
  g1 : int
    First polynomial coefficient
  g2 : int
    Second polynomial coefficient

  Results
  -------
  numpy.ndvector(shape=(128,2),dtype=numpy.uint8)
    Lookup matrix for convolution encoder
  '''

  def parity6(value):
    '''
    Helper for computing parity of 6-bit value.

    Parameters
    ----------
    value : int
      6-bit integer value

    Results
    -------
    int
      Parity bit: 0 or 1.
    '''
    return (0x6996 >> ((value ^ (value >> 4)) & 15)) & 1

  vectorG = numpy.ndarray((128, 2), dtype=numpy.uint8)
  for i in range(128):
    vectorG[i][0] = parity6(i & g1)
    vectorG[i][1] = parity6(i & g2)

  return vectorG


class ConvEncoder27(object):
  '''
  Convolution encoder class.

  Standard 2-7 convolution encoder implementation.
  '''

  DEFAULT_VECTOR_G = generate27Vector(G1, G2)

  def __init__(self, g1=G1, g2=G2, state=0):
    self.g1 = g1
    self.g2 = g2
    self.state = state
    vectorG = ConvEncoder27.DEFAULT_VECTOR_G if g1 == G1 and g2 == G2 \
        else generate27Vector(g1, g2)
    self.vectorG = vectorG

  def encode(self, bitArray):
    '''
    Encodes source bit array.

    This method updates the encoder state during processing.

    Parameters
    ----------
    bitArray : array-like
      Array of bit values. Can be integers or booleans.
    Returns
    -------
    numpy.ndarray(shape(len(bitArray)), dtype=numpy.uint8)
      Encoded output
    '''
    result = numpy.ndarray((len(bitArray) * 2), dtype=numpy.uint8)
    state = self.state
    dstIndex = 0
    vectorG = self.vectorG

    for srcBit in bitArray:
      state = (srcBit << 6) | (state >> 1)
      result[dstIndex:dstIndex + 2] = vectorG[state]
      dstIndex += 2

    self.state = state
    return result


class Message(object):
  '''
  GPS LNAV message block.

  The object provides proper-formatted CNAV messages with random contents.
  '''

  def __init__(self, prn, tow0=2, n_msg=0, n_prefixBits=50):
    '''
    Constructs message object.

    Parameters
    ----------
    prn : int
      Satellite PRN
    tow0 : int
      Time of week in 6-second units for the first message
    n_msg : int, optional
      Number of messages to generate for output
    n_prefixBits : int, optional
      Number of bits to issue before the first message
    '''
    super(Message, self).__init__()

    if tow0 & 1:
      logger.error("Initial ToW is not multiple of 2")

    self.prn = prn
    self.tow0 = tow0
    self.n_msg0 = n_msg
    self.n_prefixBits = n_prefixBits

    self.encoder = ConvEncoder27()
    self.msgCount = 0
    self.messageLen = n_prefixBits * 2
    self.symbolData = numpy.zeros(self.messageLen, dtype=numpy.uint8)

    prefixBits = numpy.zeros(self.n_prefixBits, dtype=numpy.uint8)
    prefixBits[0::2] = 1
    self.symbolData[:] = self.encoder.encode(prefixBits)
    self.nextTow = tow0
    self.addMessages(n_msg)

  def __str__(self, *args, **kwargs):
    '''
    Formats object as string literal

    Returns
    -------
    string
      String representation of the object
    '''
    return "GPS CNAV: prn=%d pref=%d tow=%d" % \
           (self.prn, self.n_prefixBits, self.nextTow)

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

    lastIdx = dataAll_idx[-1]
    if lastIdx >= self.messageLen:
      # Grow data bits
      delta = lastIdx - self.messageLen + 1
      newMsgCount = delta / 600
      if delta % 600:
        newMsgCount += 1
      self.addMessages(newMsgCount)

    # numpy.take degrades performance a lot over time.
    # return numpy.take(self.symbolData, dataAll_idx , mode='wrap')
    return self.symbolData[dataAll_idx]

  def addMessages(self, newMsgCount):
    '''
    Generate additional CNAV messages

    This method generates and encodes additional CNAV messages. The message
    contents is encoded using 2-7 convolution encoder and added to the internal
    buffer.

    Parameters
    ----------
    newMsgCount : int
      Number of messages to generate
    '''
    newMessageLen = newMsgCount * 600 + self.messageLen
    newSymbolData = numpy.ndarray(newMessageLen, dtype=numpy.uint8)
    newSymbolData[:self.messageLen] = self.symbolData
    for i in range(self.messageLen, newMessageLen, 600):
      logger.info("Generating CNAV message: prn=%d tow=%d msg_id=%d" %
                  (self.prn, self.nextTow, 0))
      cnav_msg = CNavRawMsg.generate(self.prn, 0, self.nextTow)
      self.nextTow += 2
      if self.nextTow == 7 * 24 * 60 * 10:
        self.nextTow = 0
      encoded = self.encoder.encode(cnav_msg)
      newSymbolData[i:i + 600] = encoded
    self.messageLen = newMessageLen
    self.symbolData = newSymbolData
    self.msgCount += newMsgCount

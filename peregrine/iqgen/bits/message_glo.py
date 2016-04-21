# -*- coding: utf-8 -*-
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
The :mod:`peregrine.iqgen.bits.message_glo` module contains classes and
functions related to generating stub GLONASS messages.
'''

import numpy
import logging
from swiftnav.bits import parity

logger = logging.getLogger(__name__)


def __computeHammingCoefficients():
  '''
  The method prepares bit masks for parity computations according to GLONASS
  ICD.

  Returns
  -------
  numpy.ndarray(shape=(8, 11), dtype=numpy.uint8)
    Bit masks for message bytes
  '''

  B = [None] * 8
  # C1 = β1 ⊕ [ Σi bi] mod 2
  # i  = 9, 10, 12, 13, 15, 17, 19, 20, 22, 24, 26, 28, 30, 32, 34, 35, 37, 39,
  #      41, 43, 45, 47, 49, 51, 53, 55, 57, 59, 61, 63, 65, 66, 68, 70, 72, 74,
  #      76, 78, 80, 82, 84.
  B[0] = (9, 10, 12, 13, 15, 17, 19, 20, 22, 24, 26, 28, 30, 32, 34, 35, 37, 39,
          41, 43, 45, 47, 49, 51, 53, 55, 57, 59, 61, 63, 65, 66, 68, 70, 72, 74,
          76, 78, 80, 82, 84)
  # C2 = β2 ⊕ [ Σj bj] mod 2
  # j  = 9, 11, 12, 14, 15, 18, 19, 21, 22, 25, 26, 29, 30, 33, 34, 36, 37, 40,
  #      41, 44, 45, 48, 49, 52, 53, 56, 57, 60, 61, 64, 65, 67, 68, 71, 72, 75,
  #      76, 79, 80, 83, 84.
  B[1] = (9, 11, 12, 14, 15, 18, 19, 21, 22, 25, 26, 29, 30, 33, 34, 36, 37, 40,
          41, 44, 45, 48, 49, 52, 53, 56, 57, 60, 61, 64, 65, 67, 68, 71, 72, 75,
          76, 79, 80, 83, 84)
  # C3 = β3 ⊕ [Σ k b k ] mod 2
  # k  = 10-12, 16-19, 23-26, 31-34, 38-41, 46-49, 54-57, 62-65, 69-72, 77-80,
  #      85.
  B[2] = tuple(range(10, 12 + 1) + range(16, 19 + 1) + range(23, 26 + 1) +
               range(31, 34 + 1) + range(38, 41 + 1) + range(46, 49 + 1) +
               range(54, 57 + 1) + range(62, 65 + 1) + range(69, 72 + 1) +
               range(77, 80 + 1) + [85])
  # C4 = β4 ⊕ [Σl bl]mod 2
  # l  = 13-19, 27-34, 42-49, 58-65, 73-80.
  B[3] = tuple(range(13, 19 + 1) + range(27, 34 + 1) + range(42, 49 + 1) +
               range(58, 65 + 1) + range(73, 80 + 1))
  # C5 = β5 ⊕ [Σ m b m ] mod 2
  # m  = 20-34, 50-65, 81-85.
  B[4] = tuple(range(20, 34 + 1) + range(50, 65 + 1) + range(81, 85 + 1))
  #            65
  # C6 = β6 ⊕ [Σ bn] mod 2
  #            n=35
  B[5] = tuple(range(36, 65 + 1))
  #             85
  #  C7 = β7 ⊕ [Σ bp] mod 2
  #             p=66
  B[6] = tuple(range(66, 85 + 1))
  #       8               85
  # CΣ = [Σ βq ] mod 2 ⊕ [Σ bq] mod 2
  #       q=1             q=9
  B[7] = tuple(range(2, 85 + 1))

  data = numpy.ndarray(shape=(8, 85), dtype=numpy.uint8)
  data.fill(0)
  for j in range(8):
    for i in B[j]:
      data[j][-i] = 1
  return numpy.packbits(data, axis=1)


def __computeTimeMark():
  '''
  Method produces time mark array.
  Time mark is a shortened PR code, of 30 bits, computed from polynomial:
  1 + x^3 + x^5, or 0b111110001101110101000010010110

  Returns
  -------
  numpy.array(30, dtype=numpy.uint8)
    Bit array of GLONASS time mark
  '''
  # 30 bits: 111110001101110101000010010110
  TM = [1, 1, 1, 1, 1, 0, 0, 0, 1, 1, 0, 1, 1, 1, 0,
        1, 0, 1, 0, 0, 0, 0, 1, 0, 0, 1, 0, 1, 1, 0]
  return numpy.asarray(TM, dtype=numpy.uint8)

# Hamming code masks, see
#   Edition 5.1 2008 ICD L1, L2 GLONASS
#   Russian Institute of Space Device Engineering
_HAMMING_COEFFS = __computeHammingCoefficients()
# Time mark: 30 bits, see
#   Edition 5.1 2008 ICD L1, L2 GLONASS
#   Russian Institute of Space Device Engineering
_TIME_MARK = __computeTimeMark()


class Message(object):
  '''
  GLONASS message generator
  '''

  def __init__(self, prn, tow0=1, n_msg=0, n_prefixBits=50):
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
    self.prn = prn
    self.n_prefixBits = n_prefixBits
    self.n_msg0 = n_msg
    self.tow0 = tow0
    self.messageCount = 0
    self.messageLen = n_prefixBits
    self.nextTk_h = tow0 / (60 * 60) % (60 * 60 * 24)
    self.nextTk_m = tow0 / 60 % 60
    self.nextTk_30s = 1 if tow0 / 30 % 2 else 0

    self.nextMsgId = 1
    self.messageBits = numpy.zeros(n_prefixBits, dtype=numpy.uint8)
    self.messageBits[1::2] = 1
    self.a8 = numpy.ndarray(1, dtype=numpy.uint8)
    self.addMessages(n_msg)

  def __str__(self, *args, **kwargs):
    '''
    Formats object as string literal

    Returns
    -------
    string
      String representation of the object
    '''
    return "GLONASSS: prn=%d pref=%d tod=%02d:%02d:%02d" % \
           (self.prn, self.n_prefixBits, self.nextTk_h, self.nextTk_m,
            30 if self.nextTk_30s else 0)

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
      newMsgCount = delta / 200
      if delta % 200:
        newMsgCount += 1
      self.addMessages(newMsgCount)

    # numpy.take degrades performance a lot over time.
    # return numpy.take(self.symbolData, dataAll_idx , mode='wrap')
    return self.messageBits[dataAll_idx]

  def addMessages(self, newMsgCount):
    '''
    Generate additional GLONASS messages

    This method generates and encodes additional LNAV messages. The message
    contents is added to the internal buffer.

    Parameters
    ----------
    newMsgCount : int
      Number of messages to generate
    '''
    newMessageLen = newMsgCount * 200 + self.messageLen
    newMessageData = numpy.ndarray(newMessageLen, dtype=numpy.uint8)
    newMessageData[:self.messageLen] = self.messageBits
    for i in range(self.messageLen, newMessageLen, 200):
      if self.nextMsgId == 1:
        logger.info("Starting new GLONASS frame: prn=%d frame tod=%02d:%02d:%02d" %
                    (self.prn,
                     self.nextTk_h, self.nextTk_m,
                     30 if self.nextTk_30s == 1 else 0))
      logger.debug("Generating GLONASS string: prn=%d msg=%d" %
                   (self.prn, self.nextMsgId))
      glo_msg = self.generateGloMessage()
      # First 170 symbols are 85 bits of message
      # Meander sequence: as per ICD, each data bit is added to 1/0 sequence
      newMessageData[i:i + 85 * 2:2] = glo_msg ^ 1
      newMessageData[i + 1:i + 85 * 2:2] = glo_msg
      # Last 30 symbols is the time mark
      newMessageData[i + 170:i + 200] = _TIME_MARK
    self.messageLen = newMessageLen
    self.messageBits = newMessageData
    self.messageCount += newMsgCount

  def generateGloMessage(self):
    '''
    Produces additional GLONASS message.
    Currently the method generates only type 1 GLONASS strings with ToD.

    Returns
    -------
    numpy.ndarray(shape=85, dtype=numpy.uint8)
      Message bits.
    '''
    msgData = numpy.zeros(85, dtype=numpy.uint8)

    if self.nextMsgId == 1:
      self.fillString1(msgData)
    else:
      self.fillString2_15(msgData)

    self.nextMsgId += 1
    if self.nextMsgId == 16:
      self.nextMsgId = 1

      # Frame has changed - the frame length is 30 seconds
      self.nextTk_30s += 1
      while self.nextTk_30s >= 2:
        self.nextTk_30s -= 2
        self.nextTk_m += 1
      while self.nextTk_m >= 60:
        self.nextTk_m -= 60
        self.nextTk_h += 1
      while self.nextTk_h >= 24:
        self.nextTk_h -= 24

    self.updateParity(msgData)

    return msgData

  def fillString1(self, msgData):
    msgData[0] = 0                                     # idle chip
    msgData[1:5] = self.getBits(0b0001, 4)             # m[4]
    # [2] - Reserved
    msgData[7:9] = self.getBits(0b00, 2)               # P1[2]

    msgData[9:14] = self.getBits(self.nextTk_h, 5)     # Tk[12]
    msgData[14:20] = self.getBits(self.nextTk_m, 6)    # Tk[12]
    msgData[26:27] = self.getBits(self.nextTk_30s, 1)  # Tk[12]
    msgData[28::2] = 1  # Zero + one everywhere

  def fillString2_15(self, msgData):
    msgData[1::2] = 1  # Zero + one everywhere

  def getBits(self, value, nBits):
    '''
    Converts integer into bit array

    Parameters
    ----------
    value : int
      Integer value
    nBits : number of bits to produce

    Returns
    -------
    numpy.ndarray(shape=(`nBits`), dtype=numpy.uint8)
      Parameter `value` represented as a bit array
    '''
    if nBits <= 8:
      self.a8[0] = value
      result = numpy.unpackbits(self.a8)
    else:  # pragma: no cover
      assert False
    return result[-nBits:]

  def updateParity(self, dataBits):
    '''
    Updates data bits and computes parity.

    When 85 bits are provided, they are used for parity computation and for
    bit inversion.

    Parameters
    ----------
    dataBits : numpy.ndarray(dtype=numpy.uint8)
      85 element array
    '''
    packed = numpy.packbits(dataBits)
    assert len(packed) == 11

    hc = _HAMMING_COEFFS
    for bIdx in range(8):
      p = 0
      for i in range(11):
        p ^= parity(packed[i] & hc[bIdx][i])
      dataBits[-(bIdx + 1)] = p
      packed[10] |= p << bIdx

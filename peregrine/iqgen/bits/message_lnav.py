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
The :mod:`peregrine.iqgen.bits.message_lnav` module contains classes and
functions related to generating stub GPS LNAV messages.
'''

import numpy
import logging
from swiftnav.bits import parity

logger = logging.getLogger(__name__)


class Message(object):
  '''
  GPS LNAV message generator
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
    self.nextTow = tow0
    self.nextMsgId = 0
    self.messageBits = numpy.zeros(n_prefixBits, dtype=numpy.uint8)
    words = (n_prefixBits + 29) / 30
    if words:
      tmp = numpy.zeros(words * 30, dtype=numpy.uint8)
      tmp[1::2] = 1
      if words > 1:
        self.updateParity(tmp[0:30])
        for i in range(1, words - 1):
          self.updateParity(tmp[i * 30 - 2: i * 30 + 30])
        self.updateParity(tmp[words * 30 - 32: words * 30], True)
      else:
        self.updateParity(tmp[0: 30], True)
    self.messageBits[:] = tmp[-n_prefixBits:]
    self.msgCount = 0
    self.a8 = numpy.ndarray(1, dtype=numpy.uint8)
    self.a32 = numpy.ndarray(1, dtype=numpy.dtype('>u4'))

  def __str__(self, *args, **kwargs):
    '''
    Formats object as string literal

    Returns
    -------
    string
      String representation of the object
    '''
    return "GPS LNAV: prn=%d pref=%d tow=%d" % \
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
      newMsgCount = delta / 300
      if delta % 300:
        newMsgCount += 1
      self.addMessages(newMsgCount)

    # numpy.take degrades performance a lot over time.
    # return numpy.take(self.symbolData, dataAll_idx , mode='wrap')
    return self.messageBits[dataAll_idx]

  def addMessages(self, newMsgCount):
    '''
    Generate additional LNAV messages

    This method generates and encodes additional LNAV messages. The message
    contents is added to the internal buffer.

    Parameters
    ----------
    newMsgCount : int
      Number of messages to generate
    '''
    newMessageLen = newMsgCount * 300 + self.messageLen
    newMessageData = numpy.ndarray(newMessageLen, dtype=numpy.uint8)
    newMessageData[:self.messageLen] = self.messageBits
    for i in range(self.messageLen, newMessageLen, 300):
      logger.info("Generating LNAV message: prn=%d tow=%d msg_id=%d" %
                  (self.prn, self.nextTow, self.nextMsgId))
      lnav_msg = self.generateLNavMessage()
      newMessageData[i:i + 300] = lnav_msg
    self.messageLen = newMessageLen
    self.messageBits = newMessageData
    self.msgCount += newMsgCount

  def generateLNavMessage(self):
    '''
    Produces additional GPS LNAV message.

    Returns
    -------
    numpy.ndarray(shape=300, dtype=numpy.uint8)
      Message bits.
    '''
    msgData = numpy.zeros(300, dtype=numpy.uint8)
    msgData[1::2] = 1  # Zero + one everywhere

    # TLM word
    self.fillTlmWord(msgData[0:30], 0)
    self.updateParity(msgData[0:30])
    # logger.debug("TLM: %s" % msgData[0:30])

    # TOW word
    self.fillTowWord(msgData[30:60], self.nextTow)
    self.nextTow += 1
    if self.nextTow == 7 * 24 * 60 * 10:
      self.nextTow = 0
    self.updateParity(msgData[28:60], True)
    # logger.debug("TOW: %s" % msgData[30:60])

    self.updateParity(msgData[58:90])
    self.updateParity(msgData[88:120])
    self.updateParity(msgData[118:150])
    self.updateParity(msgData[148:180])
    self.updateParity(msgData[178:210])
    self.updateParity(msgData[208:240])
    self.updateParity(msgData[238:270])
    self.updateParity(msgData[268:300], True)

    return msgData

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
    else:
      self.a32[0] = value
      result = numpy.unpackbits(self.a32.view(dtype=numpy.uint8))
    return result[-nBits:]

  def fillTlmWord(self, wordBits, msgId=0):
    '''
    Fills in TLM word contents.

    Parameters
    ----------
    wordBits : numpy.ndarray(shape=30, type=numpy.uint8)
      Destination array
    '''
    wordBits[0:8] = self.getBits(0b10001011, 8)  # Preamble
    wordBits[8:22] = self.getBits(msgId, 14)  # TML message
    wordBits[22] = 0  # Reserved
    wordBits[23] = 0  # Integrity
    return

  def fillTowWord(self, wordBits, tow):
    '''
    Fills in TOW word contents.

    Parameters
    ----------
    wordBits : numpy.ndarray(shape=30, type=numpy.uint8)
      Destination array
    '''
    wordBits[0:17] = self.getBits(tow, 17)  # TOW count in 6 second units
    wordBits[17] = 0  # Alert Flag
    wordBits[18] = 0  # Anti-Spoof flag
    wordBits[19:22] = self.getBits(0, 3)  # Sub-frame ID
    return

  def updateParity(self, dataBits, resolve=False):
    '''
    Updates data bits and computes parity.

    When 32 bits are provided, they are used for parity computation and for
    bit inversion.

    Parameters
    ----------
    dataBits : numpy.ndarray(dtype=numpy.uint8)
      30 or 32 element array
    resolve: bool, optional
      When specified, bits d23 and d24 of the GPS word are updated to ensure
      that parity bits d29 and d30 are zeros.
    '''
    packed = numpy.packbits(dataBits)
    acc = (packed[0] << 24) | (packed[1] << 16) | \
          (packed[2] << 8) | packed[3]
    if len(dataBits) == 30:
      acc >>= 2
    elif acc & 0x40000000:
      acc ^= 0x3FFFFFC0
      dataBits[-30:-6] ^= 1

    # D29 = D30*^d1^d3^d5^d6^d7^d9^d10^d14^d15^d16^d17^d18^d21^d22^d24
    d29 = parity(acc & 0b01101011101100011111001101000000)
    # D30 = D29*^d3^d5^d6^d8^d9^d10^d11^d13^d15^d19^d22^d23^d24
    d30 = parity(acc & 0b10001011011110101000100111000000)

    if resolve:
      if d29:
        acc ^= 0x80
        d29 = False
        d30 = not d30
        dataBits[-8] ^= 1
      if d30:
        acc ^= 0x40
        d30 = False
        dataBits[-7] ^= 1

    # D25 = D29*^d1^d2^d3^d5^d6^d10^d11^d12^d13^d14^d17^d18^d20^d23
    dataBits[-6] = parity(acc & 0b10111011000111110011010010000000)
    # D26 = D30*^d2^d3^d4^d6^d7^d11^d12^d13^d14^d15^d18^d19^d21^d24
    dataBits[-5] = parity(acc & 0b01011101100011111001101001000000)
    # D27 = D29*^d1^d3^d4^d5^d7^d8^d12^d13^d14^d15^d16^d19^d20^d22
    dataBits[-4] = parity(acc & 0b10101110110001111100111000000000)
    # D28 = D30*^d2^d4^d5^d6^d8^d9^d13^d14^d15^d16^d17^d20^d21^d23
    dataBits[-3] = parity(acc & 0b01010111011000111110011010000000)
    # D29 = D30*^d1^d3^d5^d6^d7^d9^d10^d14^d15^d16^d17^d18^d21^d22^d24
    dataBits[-2] = d29
    # D30 = D29*^d3^d5^d6^d8^d9^d10^d11^d13^d15^d19^d22^d23^d24
    dataBits[-1] = d30

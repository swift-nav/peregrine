# Copyright (C) 2016 Swift Navigation Inc.
#
# Contact: Valeri Atamaniouk <valeri@swiftnav.com>
# This source is subject to the license found in the file 'LICENSE' which must
# be be distributed together with this source. All other rights reserved.
#
# THIS CODE AND INFORMATION IS PROVIDED "AS IS" WITHOUT WARRANTY OF ANY KIND,
# EITHER EXPRESSED OR IMPLIED, INCLUDING BUT NOT LIMITED TO THE IMPLIED
# WARRANTIES OF MERCHANTABILITY AND/OR FITNESS FOR A PARTICULAR PURPOSE.

'''
Unit tests for IQgen GPS message types
'''

from peregrine.iqgen.bits.message_lnav import Message as LNavMessage
from peregrine.iqgen.bits.message_cnav import Message as CNavMessage
import numpy


def test_LNavMessage_init0():
  '''
  GPS LNav message construction: epoch
  '''
  msg = LNavMessage(1, tow0=0, n_msg=0, n_prefixBits=0)
  assert msg.n_msg0 == 0
  assert msg.prn == 1
  assert msg.tow0 == 0
  assert msg.nextMsgId == 0
  assert msg.nextTow == 0
  assert msg.n_prefixBits == 0
  assert msg.messageCount == 0
  assert msg.messageLen == 0
  assert isinstance(msg.messageBits, numpy.ndarray)


def test_LNavMessage_init1():
  '''
  GPS LNav message construction: message prefetch
  '''
  msg = LNavMessage(1, tow0=1, n_msg=3, n_prefixBits=0)
  assert msg.n_msg0 == 3
  assert msg.prn == 1
  assert msg.tow0 == 1
  assert msg.nextMsgId == 3
  assert msg.nextTow == 4
  assert msg.n_prefixBits == 0
  assert msg.messageCount == 3
  assert msg.messageLen == 900
  assert isinstance(msg.messageBits, numpy.ndarray)


def test_LNavMessage_init2():
  '''
  GPS LNav message construction: message prefetch and prefix bits
  '''
  msg = LNavMessage(1, tow0=1, n_msg=1, n_prefixBits=30)
  assert msg.n_msg0 == 1
  assert msg.prn == 1
  assert msg.tow0 == 1
  assert msg.nextMsgId == 1
  assert msg.nextTow == 2
  assert msg.n_prefixBits == 30
  assert msg.messageCount == 1
  assert msg.messageLen == 330
  assert isinstance(msg.messageBits, numpy.ndarray)


def test_LNavMessage_init3():
  '''
  GPS LNav message construction:  prefix bits
  '''
  msg = LNavMessage(1, tow0=1, n_msg=0, n_prefixBits=70)
  assert msg.n_msg0 == 0
  assert msg.prn == 1
  assert msg.tow0 == 1
  assert msg.nextMsgId == 0
  assert msg.nextTow == 1
  assert msg.n_prefixBits == 70
  assert msg.messageCount == 0
  assert msg.messageLen == 70
  assert isinstance(msg.messageBits, numpy.ndarray)


def test_LNavMessage_init4():
  '''
  GPS LNav message construction:  prefix bits
  '''
  msg = LNavMessage(1, tow0=100800 - 1, n_msg=1, n_prefixBits=0)
  assert msg.n_msg0 == 1
  assert msg.prn == 1
  assert msg.tow0 == 100799
  assert msg.nextMsgId == 1
  assert msg.nextTow == 0
  assert msg.n_prefixBits == 00
  assert msg.messageCount == 1
  assert msg.messageLen == 300
  assert isinstance(msg.messageBits, numpy.ndarray)


def test_LNavMessage_getDataBits0():
  '''
  GPS LNav message: fetch data bits
  '''
  dataAll_idx = numpy.linspace(0, 299, 300, dtype=numpy.long)
  msg = LNavMessage(1, tow0=1, n_msg=1, n_prefixBits=30)
  bits = msg.getDataBits(dataAll_idx)
  assert isinstance(bits, numpy.ndarray)
  assert bits.shape == (300,)
  assert (bits == msg.messageBits[:300]).all()


def test_LNavMessage_getDataBits1():
  '''
  GPS LNav message: fetch data bits
  '''
  dataAll_idx = numpy.linspace(150, 449, 300, dtype=numpy.long)
  msg = LNavMessage(1, tow0=1, n_msg=1, n_prefixBits=30)
  bits = msg.getDataBits(dataAll_idx)
  assert isinstance(bits, numpy.ndarray)
  assert bits.shape == (300,)
  assert (bits == msg.messageBits[150:450]).all()


def test_LNavMessage_updateParity0():
  '''
  GPS LNav: parity of empty message
  '''
  msg = LNavMessage(1, tow0=0, n_msg=0, n_prefixBits=0)
  bits = msg.getBits(0b00000000000000000000000000000000, 32)
  msg.updateParity(bits, False)
  assert (bits == 0).all()


def test_LNavMessage_updateParity_d30():
  '''
  GPS LNav: parity of D30 bit
  '''
  msg = LNavMessage(1, tow0=0, n_msg=0, n_prefixBits=0)
  bits = msg.getBits(0b00100000000000000000000000000000, 32)
  bits2 = msg.getBits(0b00100000000000000000000000101010, 32)
  msg.updateParity(bits, False)
  assert (bits == bits2).all()


def test_LNavMessage_updateParity_d29():
  '''
  GPS LNav: parity of D29 bit
  '''
  msg = LNavMessage(1, tow0=0, n_msg=0, n_prefixBits=0)
  bits = msg.getBits(0b00010000000000000000000000000000, 32)
  bits2 = msg.getBits(0b00010000000000000000000000110100, 32)
  msg.updateParity(bits, False)
  assert (bits == bits2).all()


def test_LNavMessage_updateParity_d28():
  '''
  GPS LNav: parity of D28 bit
  '''
  msg = LNavMessage(1, tow0=0, n_msg=0, n_prefixBits=0)
  bits = msg.getBits(0b00001000000000000000000000000000, 32)
  bits2 = msg.getBits(0b00001000000000000000000000111011, 32)
  msg.updateParity(bits, False)
  assert (bits == bits2).all()


def test_LNavMessage_updateParity_d27():
  '''
  GPS LNav: parity of D27 bit
  '''
  msg = LNavMessage(1, tow0=0, n_msg=0, n_prefixBits=0)
  bits = msg.getBits(0b00001000000000000000000000000000, 32)
  bits2 = msg.getBits(0b00001000000000000000000000111011, 32)
  msg.updateParity(bits, False)
  assert (bits == bits2).all()


def test_LNavMessage_updateParity_d26():
  '''
  GPS LNav: parity of D26 bit
  '''
  msg = LNavMessage(1, tow0=0, n_msg=0, n_prefixBits=0)
  bits = msg.getBits(0b00000100000000000000000000000000, 32)
  bits2 = msg.getBits(0b00000100000000000000000000011100, 32)
  msg.updateParity(bits, False)
  assert (bits == bits2).all()


def test_LNavMessage_updateParity_d25():
  '''
  GPS LNav: parity of D25 bit
  '''
  msg = LNavMessage(1, tow0=0, n_msg=0, n_prefixBits=0)
  bits = msg.getBits(0b00000010000000000000000000000000, 32)
  bits2 = msg.getBits(0b00000010000000000000000000101111, 32)
  msg.updateParity(bits, False)
  assert (bits == bits2).all()


def test_LNavMessage_updateParity_d24():
  '''
  GPS LNav: parity of D24 bit
  '''
  msg = LNavMessage(1, tow0=0, n_msg=0, n_prefixBits=0)
  bits = msg.getBits(0b00000001000000000000000000000000, 32)
  bits2 = msg.getBits(0b00000001000000000000000000110111, 32)
  msg.updateParity(bits, False)
  assert (bits == bits2).all()


def test_LNavMessage_updateParity_d23():
  '''
  GPS LNav: parity of D23 bit
  '''
  msg = LNavMessage(1, tow0=0, n_msg=0, n_prefixBits=0)
  bits = msg.getBits(0b00000000100000000000000000000000, 32)
  bits2 = msg.getBits(0b00000000100000000000000000011010, 32)
  msg.updateParity(bits, False)
  assert (bits == bits2).all()


def test_LNavMessage_updateParity_d22():
  '''
  GPS LNav: parity of D22 bit
  '''
  msg = LNavMessage(1, tow0=0, n_msg=0, n_prefixBits=0)
  bits = msg.getBits(0b00000000010000000000000000000000, 32)
  bits2 = msg.getBits(0b00000000010000000000000000001101, 32)
  msg.updateParity(bits, False)
  assert (bits == bits2).all()


def test_LNavMessage_updateParity_d21():
  '''
  GPS LNav: parity of D21 bit
  '''
  msg = LNavMessage(1, tow0=0, n_msg=0, n_prefixBits=0)
  bits = msg.getBits(0b00000000001000000000000000000000, 32)
  bits2 = msg.getBits(0b00000000001000000000000000000111, 32)
  msg.updateParity(bits, False)
  assert (bits == bits2).all()


def test_LNavMessage_updateParity_d20():
  '''
  GPS LNav: parity of D20 bit
  '''
  msg = LNavMessage(1, tow0=0, n_msg=0, n_prefixBits=0)
  bits = msg.getBits(0b00000000000100000000000000000000, 32)
  bits2 = msg.getBits(0b00000000000100000000000000100011, 32)
  msg.updateParity(bits, False)
  assert (bits == bits2).all()


def test_LNavMessage_updateParity_d19():
  '''
  GPS LNav: parity of D19 bit
  '''
  msg = LNavMessage(1, tow0=0, n_msg=0, n_prefixBits=0)
  bits = msg.getBits(0b00000000000010000000000000000000, 32)
  bits2 = msg.getBits(0b00000000000010000000000000110001, 32)
  msg.updateParity(bits, False)
  assert (bits == bits2).all()


def test_LNavMessage_updateParity_d18():
  '''
  GPS LNav: parity of D18 bit
  '''
  msg = LNavMessage(1, tow0=0, n_msg=0, n_prefixBits=0)
  bits = msg.getBits(0b00000000000001000000000000000000, 32)
  bits2 = msg.getBits(0b00000000000001000000000000111000, 32)
  msg.updateParity(bits, False)
  assert (bits == bits2).all()


def test_LNavMessage_updateParity_d17():
  '''
  GPS LNav: parity of D17 bit
  '''
  msg = LNavMessage(1, tow0=0, n_msg=0, n_prefixBits=0)
  bits = msg.getBits(0b00000000000000100000000000000000, 32)
  bits2 = msg.getBits(0b00000000000000100000000000111101, 32)
  msg.updateParity(bits, False)
  assert (bits == bits2).all()


def test_LNavMessage_updateParity_d16():
  '''
  GPS LNav: parity of D16 bit
  '''
  msg = LNavMessage(1, tow0=0, n_msg=0, n_prefixBits=0)
  bits = msg.getBits(0b00000000000000010000000000000000, 32)
  bits2 = msg.getBits(0b00000000000000010000000000111110, 32)
  msg.updateParity(bits, False)
  assert (bits == bits2).all()


def test_LNavMessage_updateParity_d15():
  '''
  GPS LNav: parity of D15 bit
  '''
  msg = LNavMessage(1, tow0=0, n_msg=0, n_prefixBits=0)
  bits = msg.getBits(0b00000000000000001000000000000000, 32)
  bits2 = msg.getBits(0b00000000000000001000000000011111, 32)
  msg.updateParity(bits, False)
  assert (bits == bits2).all()


def test_LNavMessage_updateParity_d14():
  '''
  GPS LNav: parity of D14 bit
  '''
  msg = LNavMessage(1, tow0=0, n_msg=0, n_prefixBits=0)
  bits = msg.getBits(0b00000000000000000100000000000000, 32)
  bits2 = msg.getBits(0b00000000000000000100000000001110, 32)
  msg.updateParity(bits, False)
  assert (bits == bits2).all()


def test_LNavMessage_updateParity_d13():
  '''
  GPS LNav: parity of D13 bit
  '''
  msg = LNavMessage(1, tow0=0, n_msg=0, n_prefixBits=0)
  bits = msg.getBits(0b00000000000000000010000000000000, 32)
  bits2 = msg.getBits(0b00000000000000000010000000100110, 32)
  msg.updateParity(bits, False)
  assert (bits == bits2).all()


def test_LNavMessage_updateParity_d12():
  '''
  GPS LNav: parity of D12 bit
  '''
  msg = LNavMessage(1, tow0=0, n_msg=0, n_prefixBits=0)
  bits = msg.getBits(0b00000000000000000001000000000000, 32)
  bits2 = msg.getBits(0b00000000000000000001000000110010, 32)
  msg.updateParity(bits, False)
  assert (bits == bits2).all()


def test_LNavMessage_updateParity_d11():
  '''
  GPS LNav: parity of D11 bit
  '''
  msg = LNavMessage(1, tow0=0, n_msg=0, n_prefixBits=0)
  bits = msg.getBits(0b00000000000000000000100000000000, 32)
  bits2 = msg.getBits(0b00000000000000000000100000011001, 32)
  msg.updateParity(bits, False)
  assert (bits == bits2).all()


def test_LNavMessage_updateParity_d10():
  '''
  GPS LNav: parity of D10 bit
  '''
  msg = LNavMessage(1, tow0=0, n_msg=0, n_prefixBits=0)
  bits = msg.getBits(0b00000000000000000000010000000000, 32)
  bits2 = msg.getBits(0b00000000000000000000010000101100, 32)
  msg.updateParity(bits, False)
  assert (bits == bits2).all()


def test_LNavMessage_updateParity_d9():
  '''
  GPS LNav: parity of D9 bit
  '''
  msg = LNavMessage(1, tow0=0, n_msg=0, n_prefixBits=0)
  bits = msg.getBits(0b00000000000000000000001000000000, 32)
  bits2 = msg.getBits(0b00000000000000000000001000011110, 32)
  msg.updateParity(bits, False)
  assert (bits == bits2).all()


def test_LNavMessage_updateParity_d8():
  '''
  GPS LNav: parity of D8 bit
  '''
  msg = LNavMessage(1, tow0=0, n_msg=0, n_prefixBits=0)
  bits = msg.getBits(0b0000000000000000000000100000000, 32)
  bits2 = msg.getBits(0b0000000000000000000000100000011, 32)
  msg.updateParity(bits, False)
  assert (bits == bits2).all()


def test_LNavMessage_updateParity1():
  '''
  GPS LNav: inversion of parity
  '''
  msg = LNavMessage(1, tow0=0, n_msg=0, n_prefixBits=0)
  bits = msg.getBits(0b01000000000000000000000000000000, 32)
  bits2 = msg.getBits(0b01111111111111111111111111010101, 32)
  msg.updateParity(bits, False)
  assert (bits == bits2).all()


def test_LNavMessage_updateParity2():
  '''
  GPS LNav: D29' contribution
  '''
  msg = LNavMessage(1, tow0=0, n_msg=0, n_prefixBits=0)
  bits = msg.getBits(0b10000000000000000000000000000000, 32)
  bits2 = msg.getBits(0b10000000000000000000000000101001, 32)
  msg.updateParity(bits, False)
  assert (bits == bits2).all()


def test_LNavMessage_updateParity_D22D23p0():
  '''
  GPS LNav: parity of empty message with D22/D23 patch
  '''
  msg = LNavMessage(1, tow0=0, n_msg=0, n_prefixBits=0)
  bits = msg.getBits(0b00000000000000000000000000000000, 32)
  bits2 = msg.getBits(0b00000000000000000000000000000000, 32)
  msg.updateParity(bits, True)
  assert (bits == bits2).all()


def test_LNavMessage_updateParity_D22D23p1():
  '''
  GPS LNav: parity of message with D22/D23 patch
  '''
  msg = LNavMessage(1, tow0=0, n_msg=0, n_prefixBits=0)
  bits = msg.getBits(0b01000000000000000000000000000000, 32)
  bits2 = msg.getBits(0b01111111111111111111111110000100, 32)
  msg.updateParity(bits, True)
  assert (bits == bits2).all()


def test_LNavMessage_updateParity_D22D23p2():
  '''
  GPS LNav: parity of message with D22/D23 patch
  '''
  msg = LNavMessage(1, tow0=0, n_msg=0, n_prefixBits=0)
  bits = msg.getBits(0b10101010101010101010101110101010, 32)
  bits2 = msg.getBits(0b10101010101010101010101101101000, 32)
  msg.updateParity(bits, True)
  assert (bits == bits2).all()


def test_LNavMessage_str():
  '''
  GPS LNav message: string representation
  '''
  msg = LNavMessage(1, tow0=1, n_msg=1, n_prefixBits=30)
  value = str(msg)
  assert value.find('LNAV') >= 0


def test_CNavMessage_init0():
  '''
  GPS LNav message construction: empty
  '''
  msg = CNavMessage(1, tow0=0, n_msg=0, n_prefixBits=0)
  assert msg.n_msg0 == 0
  assert msg.prn == 1
  assert msg.tow0 == 0
  assert msg.nextTow == 0
  assert msg.n_prefixBits == 0
  assert msg.messageLen == 0
  assert msg.messageCount == 0
  assert isinstance(msg.symbolData, numpy.ndarray)


def test_CNavMessage_init1():
  '''
  GPS LNav message construction: prefix only
  '''
  msg = CNavMessage(1, tow0=1, n_msg=0, n_prefixBits=30)
  assert msg.n_msg0 == 0
  assert msg.prn == 1
  assert msg.tow0 == 1
  assert msg.nextTow == 1
  assert msg.n_prefixBits == 30
  assert msg.messageLen == 60
  assert msg.messageCount == 0
  assert isinstance(msg.symbolData, numpy.ndarray)
  assert msg.symbolData.shape == (60,)


def test_CNavMessage_init2():
  '''
  GPS LNav message construction: 2 messages + prefix
  '''
  msg = CNavMessage(1, tow0=2, n_msg=2, n_prefixBits=30)
  assert msg.n_msg0 == 2
  assert msg.prn == 1
  assert msg.tow0 == 2
  assert msg.nextTow == 6
  assert msg.n_prefixBits == 30
  assert msg.messageLen == 1260
  assert msg.messageCount == 2
  assert isinstance(msg.symbolData, numpy.ndarray)
  assert msg.symbolData.shape == (1260,)


def test_CNavMessage_init3():
  '''
  GPS LNav message construction: ToW rollover
  '''
  msg = CNavMessage(1, tow0=100800 - 2, n_msg=1, n_prefixBits=30)
  assert msg.n_msg0 == 1
  assert msg.prn == 1
  assert msg.tow0 == 100798
  assert msg.nextTow == 0
  assert msg.n_prefixBits == 30
  assert msg.messageLen == 660
  assert msg.messageCount == 1
  assert isinstance(msg.symbolData, numpy.ndarray)
  assert msg.symbolData.shape == (660,)


def test_CNavMessage_getDataBits0():
  '''
  GPS CNav message: fetch data bits
  '''
  dataAll_idx = numpy.linspace(0, 299, 300, dtype=numpy.long)
  msg = CNavMessage(1, tow0=2, n_msg=1, n_prefixBits=30)
  bits = msg.getDataBits(dataAll_idx)
  assert isinstance(bits, numpy.ndarray)
  assert bits.shape == (300,)
  assert (bits == msg.symbolData[:300]).all()


def test_CNavMessage_getDataBits1():
  '''
  GPS CNav message: fetch data bits
  '''
  dataAll_idx = numpy.linspace(500, 799, 300, dtype=numpy.long)
  msg = CNavMessage(1, tow0=2, n_msg=1, n_prefixBits=30)
  bits = msg.getDataBits(dataAll_idx)
  assert isinstance(bits, numpy.ndarray)
  assert bits.shape == (300,)
  assert (bits == msg.symbolData[500:800]).all()
  assert msg.messageCount == 2


def test_CNavMessage_str():
  '''
  GPS CNav message: string representation
  '''
  msg = CNavMessage(1, tow0=2, n_msg=1, n_prefixBits=30)
  value = str(msg)
  assert value.find('CNAV') >= 0

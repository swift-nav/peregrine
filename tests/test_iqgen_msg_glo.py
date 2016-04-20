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
Unit tests for IQgen GLONASS message types
'''

from peregrine.iqgen.bits.message_glo import Message as GLOMessage
import numpy


def test_GLOMessage_init0():
  '''
  GLONASS message: test construction of an empty message
  '''
  msg = GLOMessage(prn=0, tow0=0, n_msg=0, n_prefixBits=0)
  assert msg.prn == 0
  assert msg.tow0 == 0
  assert msg.n_msg0 == 0
  assert msg.n_prefixBits == 0

  assert isinstance(msg.messageBits, numpy.ndarray)
  assert msg.messageBits.shape == (0,)
  assert msg.messageCount == 0
  assert msg.messageLen == 0

  assert msg.nextMsgId == 1
  assert msg.nextTk_h == 0
  assert msg.nextTk_m == 0
  assert msg.nextTk_30s == 0


def test_GLOMessage_init1():
  '''
  GLONASS message: test construction with prefix
  '''
  msg = GLOMessage(prn=0, tow0=0, n_msg=0, n_prefixBits=50)
  assert msg.prn == 0
  assert msg.tow0 == 0
  assert msg.n_msg0 == 0
  assert msg.n_prefixBits == 50

  assert isinstance(msg.messageBits, numpy.ndarray)
  assert msg.messageBits.shape == (50,)
  assert msg.messageCount == 0
  assert msg.messageLen == 50

  assert msg.nextMsgId == 1
  assert msg.nextTk_h == 0
  assert msg.nextTk_m == 0
  assert msg.nextTk_30s == 0


def test_GLOMessage_init2():
  '''
  GLONASS message: test construction with message
  '''

  msg = GLOMessage(prn=0, tow0=0, n_msg=1, n_prefixBits=0)
  assert msg.prn == 0
  assert msg.tow0 == 0
  assert msg.n_msg0 == 1
  assert msg.n_prefixBits == 00

  assert isinstance(msg.messageBits, numpy.ndarray)
  assert msg.messageBits.shape == (200,)
  assert msg.messageCount == 1
  assert msg.messageLen == 200

  assert msg.nextMsgId == 2
  assert msg.nextTk_h == 0
  assert msg.nextTk_m == 0
  assert msg.nextTk_30s == 0


def test_GLOMessage_init3():
  '''
  GLONASS message: test time step
  '''
  msg = GLOMessage(prn=0, tow0=0, n_msg=15, n_prefixBits=0)
  assert msg.prn == 0
  assert msg.tow0 == 0
  assert msg.n_msg0 == 15
  assert msg.n_prefixBits == 00

  assert isinstance(msg.messageBits, numpy.ndarray)
  assert msg.messageBits.shape == (3000,)
  assert msg.messageCount == 15
  assert msg.messageLen == 3000

  assert msg.nextMsgId == 1
  assert msg.nextTk_h == 0
  assert msg.nextTk_m == 0
  assert msg.nextTk_30s == 1


def test_GLOMessage_init4():
  '''
  GLONASS message: test time stamp roll over
  '''
  msg = GLOMessage(
      prn=0, tow0=(23 * 60 + 59) * 60 + 30, n_msg=0, n_prefixBits=0)
  assert msg.prn == 0
  assert msg.tow0 == 86370
  assert msg.n_msg0 == 0
  assert msg.n_prefixBits == 00

  assert isinstance(msg.messageBits, numpy.ndarray)
  assert msg.messageBits.shape == (0,)
  assert msg.messageCount == 0
  assert msg.messageLen == 0

  assert msg.nextMsgId == 1
  assert msg.nextTk_h == 23
  assert msg.nextTk_m == 59
  assert msg.nextTk_30s == 1

  msg.addMessages(15)

  assert msg.messageBits.shape == (3000,)
  assert msg.messageCount == 15
  assert msg.messageLen == 3000

  assert msg.nextMsgId == 1
  assert msg.nextTk_h == 0
  assert msg.nextTk_m == 0
  assert msg.nextTk_30s == 0


def test_GLOMessage_getDataBits0():
  '''
  GLONASS message: test getting bits
  '''
  msg = GLOMessage(prn=0, tow0=0, n_msg=1, n_prefixBits=0)
  dataAll_idx = numpy.linspace(150, 449, 300, dtype=numpy.long)
  bits = msg.getDataBits(dataAll_idx)
  assert isinstance(bits, numpy.ndarray)
  assert bits.shape == (300,)
  assert (bits == msg.messageBits[150:450]).all()


def test_GLOMessage_str():
  '''
  GLONASS message: test string representation
  '''
  msg = GLOMessage(prn=0, tow0=0, n_msg=0, n_prefixBits=0)
  value = str(msg)
  assert value.find('prn=0') >= 0
  assert value.find('tod=00:00:00') >= 0
  assert value.find('pref=0') >= 0

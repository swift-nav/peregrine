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
Unit tests for IQgen common message types
'''

from peregrine.iqgen.bits.message_const import Message as MessageConst
from peregrine.iqgen.bits.message_block import Message as MessageBlock
from peregrine.iqgen.bits.message_zeroone import Message as MessageZeroOne
import numpy


def testMessageConst_init0():
  '''
  Test constant message construction
  '''
  message = MessageConst(1)
  assert message.binValue == 0
  assert message.bitValue == 1


def testMessageConst_init1():
  '''
  Test constant message construction
  '''
  message = MessageConst(-1)
  assert message.binValue == 1
  assert message.bitValue == -1


def testMessageConst_getDataBits0():
  '''
  Test constant message data bits lookup
  '''
  message = MessageConst(-1)
  dataAll_idx = numpy.asarray([0, 1, 2, 6], dtype=numpy.long)
  bits = message.getDataBits(dataAll_idx)
  assert bits.shape == (4,)
  assert bits.dtype == numpy.uint8
  assert (bits == 1).all()


def testMessageConst_str0():
  '''
  Test constant message string representation
  '''
  message = MessageConst(-1)
  value = str(message)
  assert value.find('Const') >= 0
  assert value.find('value=1') >= 0


def testMessageConst_str1():
  '''
  Test constant message string representation
  '''
  message = MessageConst(1)
  value = str(message)
  assert value.find('Const') >= 0
  assert value.find('value=0') >= 0


def testMessageConst_getDataBits1():
  '''
  Test constant message data bits lookup
  '''
  message = MessageConst(1)
  dataAll_idx = numpy.asarray([0, 1, 2, 6], dtype=numpy.long)
  bits = message.getDataBits(dataAll_idx)
  assert bits.shape == (4,)
  assert bits.dtype == numpy.uint8
  assert (bits == 0).all()


def testMessageZeroOne_init():
  '''
  Test zero+one message construction
  '''
  message = MessageZeroOne()
  assert message.bits.shape == (2,)
  assert message.bits[0] == 0
  assert message.bits[1] == 1


def testMessageZeroOne_getDataBits():
  '''
  Test zero+one message data bits lookup
  '''
  message = MessageZeroOne()
  dataAll_idx = numpy.asarray([x for x in range(10)], dtype=numpy.long)
  bits = message.getDataBits(dataAll_idx)
  assert bits.shape == (10,)
  assert bits.dtype == numpy.uint8
  assert (bits[0::2] == 0).all()
  assert (bits[1::2] == 1).all()


def testMessageZeroOne_str0():
  '''
  Test zero+one message string representation
  '''
  message = MessageZeroOne()
  value = str(message)
  assert value.find('ZeroOne') >= 0


def testMessageBlock_init():
  '''
  Test constant message construction
  '''
  msgData = numpy.ndarray(10, dtype=numpy.int8)
  msgData[0::2].fill(1)
  msgData[1::2].fill(0)
  message = MessageBlock(msgData)
  assert message.bits.shape == (10,)
  assert message.bits.dtype == numpy.uint8
  assert message.messageLen == 10


def testMessageBlock_getDataBits0():
  '''
  Test block message data bits lookup
  '''
  dataAll_idx = numpy.asarray([x for x in range(10)], dtype=numpy.long)
  msgData = numpy.ndarray(10, dtype=numpy.int8)
  msgData[0::2].fill(1)
  msgData[1::2].fill(-1)
  message = MessageBlock(msgData)
  bits = message.getDataBits(dataAll_idx)
  assert bits.shape == (10,)
  assert bits.dtype == numpy.uint8
  assert (bits[0::2] == 0).all()
  assert (bits[1::2] == 1).all()


def testMessageBlock_getDataBits1():
  '''
  Test block message data bits lookup
  '''
  dataAll_idx = numpy.asarray([x for x in range(0, 20, 2)], dtype=numpy.long)
  msgData = numpy.ndarray(10, dtype=numpy.int8)
  msgData[0::2].fill(1)
  msgData[1::2].fill(-1)
  message = MessageBlock(msgData)
  bits = message.getDataBits(dataAll_idx)
  assert bits.shape == (10,)
  assert bits.dtype == numpy.uint8
  assert (bits == 0).all()


def testMessageBlock_str():
  '''
  Test block message string representation
  '''
  msgData = numpy.ndarray(10, dtype=numpy.int8)
  msgData[0::2].fill(1)
  msgData[1::2].fill(-1)
  message = MessageBlock(msgData)
  value = str(message)
  assert value.find('Block') >= 0
  assert value.find('length=10') >= 0

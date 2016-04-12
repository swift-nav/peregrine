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
The :mod:`peregrine.iqgen.bits.messager_factory` module contains classes and
functions related to object factory for message objects.

"""

from peregrine.iqgen.bits.message_block import Message as BlockMessage
from peregrine.iqgen.bits.message_cnav import Message as CNAVMessage
from peregrine.iqgen.bits.message_const import Message as ConstMessage
from peregrine.iqgen.bits.message_lnav import Message as LNAVMessage
from peregrine.iqgen.bits.message_zeroone import Message as ZeroOneMessage


class ObjectFactory(object):
  '''
  Object factory for message objects.
  '''

  def __init__(self):
    super(ObjectFactory, self).__init__()

  def toMapForm(self, obj):
    t = type(obj)
    if t is BlockMessage:
      return self.__BlockMessage_ToMap(obj)
    elif t is CNAVMessage:
      return self.__CNAVMessage_ToMap(obj)
    elif t is ConstMessage:
      return self.__ConstMessage_ToMap(obj)
    elif t is LNAVMessage:
      return self.__LNAVMessage_ToMap(obj)
    elif t is ZeroOneMessage:
      return self.__ZeroOneMessage_ToMap(obj)
    else:
      raise ValueError("Invalid object type")

  def fromMapForm(self, data):
    t = data['type']
    if t == 'BlockMessage':
      return self.__MapTo_BlockMessage(data)
    elif t == 'CNAVMessage':
      return self.__MapTo_CNAVMessage(data)
    elif t == 'ConstMessage':
      return self.__MapTo_ConstMessage(data)
    elif t == 'LNAVMessage':
      return self.__MapTo_LNAVMessage(data)
    elif t == 'ZeroOneMessage':
      return self.__MapTo_ZeroOneMessage(data)
    else:
      raise ValueError("Invalid object type")

  def __BlockMessage_ToMap(self, obj):
    data = {'type': 'BlockMessage',
            'data': obj.messageData}
    return data

  def __CNAVMessage_ToMap(self, obj):
    data = {'type': 'CNAVMessage',
            'prn': obj.prn,
            'n_prefixBits': obj.n_prefixBits,
            'n_msg0': obj.n_msg0,
            'tow0': obj.tow0}
    return data

  def __ConstMessage_ToMap(self, obj):
    data = {'type': 'ConstMessage',
            'bitValue': obj.bitValue}
    return data

  def __LNAVMessage_ToMap(self, obj):
    data = {'type': 'LNAVMessage',
            'prn': obj.prn,
            'n_prefixBits': obj.n_prefixBits,
            'n_msg0': obj.n_msg0,
            'tow0': obj.tow0}
    return data

  def __ZeroOneMessage_ToMap(self, obj):
    data = {'type': 'ZeroOneMessage'}
    return data

  def __MapTo_BlockMessage(self, data):
    messageData = data['data']
    return BlockMessage(messageData)

  def __MapTo_CNAVMessage(self, data):
    prn = data['prn']
    n_prefixBits = data['n_prefixBits']
    n_msg0 = data['n_msg0']
    tow0 = data['tow0']
    return CNAVMessage(prn=prn,
                       tow0=tow0,
                       n_msg=n_msg0,
                       n_prefixBits=n_prefixBits)

  def __MapTo_ConstMessage(self, data):
    bitValue = data['bitValue']
    return ConstMessage(bitValue)

  def __MapTo_LNAVMessage(self, data):
    prn = data['prn']
    n_prefixBits = data['n_prefixBits']
    n_msg0 = data['n_msg0']
    tow0 = data['tow0']
    return LNAVMessage(prn=prn,
                       tow0=tow0,
                       n_msg=n_msg0,
                       n_prefixBits=n_prefixBits)

  def __MapTo_ZeroOneMessage(self, data):
    return ZeroOneMessage()

factoryObject = ObjectFactory()

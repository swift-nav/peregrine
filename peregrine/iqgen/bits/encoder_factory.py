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
The :mod:`peregrine.iqgen.bits.encoder_factory` module contains classes and
functions related to object factory for output encoder objects.

"""

from peregrine.iqgen.bits.encoder_gps import GPSL1BitEncoder
from peregrine.iqgen.bits.encoder_gps import GPSL2BitEncoder
from peregrine.iqgen.bits.encoder_gps import GPSL1L2BitEncoder
from peregrine.iqgen.bits.encoder_gps import GPSL1TwoBitsEncoder
from peregrine.iqgen.bits.encoder_gps import GPSL2TwoBitsEncoder
from peregrine.iqgen.bits.encoder_gps import GPSL1L2TwoBitsEncoder


class ObjectFactory(object):
  '''
  Object factory for encoder objects.
  '''

  def __init__(self):
    super(ObjectFactory, self).__init__()

  def toMapForm(self, obj):
    t = type(obj)
    if t is GPSL1BitEncoder:
      return self.__GPSL1BitEncoder_ToMap(obj)
    elif t is GPSL2BitEncoder:
      return self.__GPSL2BitEncoder_ToMap(obj)
    elif t is GPSL1L2BitEncoder:
      return self.__GPSL1L2BitEncoder_ToMap(obj)
    elif t is GPSL1TwoBitsEncoder:
      return self.__GPSL1TwoBitsEncoder_ToMap(obj)
    elif t is GPSL2TwoBitsEncoder:
      return self.__GPSL2TwoBitsEncoder_ToMap(obj)
    elif t is GPSL1L2TwoBitsEncoder:
      return self.__GPSL1L2TwoBitsEncoder_ToMap(obj)
    else:
      raise ValueError("Invalid object type")

  def fromMapForm(self, data):
    t = data['type']
    if t == 'GPSL1BitEncoder':
      return self.__MapTo_GPSL1BitEncoder(data)
    elif t == 'GPSL2BitEncoder':
      return self.__MapTo_GPSL2BitEncoder(data)
    elif t == 'GPSL2BitEncoder':
      return self.__MapTo_GPSL1L2BitEncoder(data)
    elif t == 'GPSL1TwoBitsEncoder':
      return self.__MapTo_GPSL1TwoBitsEncoder(data)
    elif t == 'GPSL2TwoBitsEncoder':
      return self.__MapTo_GPSL2TwoBitsEncoder(data)
    elif t == 'GPSL1L2TwoBitsEncoder':
      return self.__MapTo_GPSL1L2TwoBitsEncoder(data)
    else:
      raise ValueError("Invalid object type")

  def __GPSL1BitEncoder_ToMap(self, obj):
    data = {'type': 'GPSL1BitEncoder'}
    return data

  def __GPSL2BitEncoder_ToMap(self, obj):
    data = {'type': 'GPSL2BitEncoder'}
    return data

  def __GPSL1L2BitEncoder_ToMap(self, obj):
    data = {'type': 'GPSL1L2BitEncoder'}
    return data

  def __GPSL1TwoBitsEncoder_ToMap(self, obj):
    data = {'type': 'GPSL1TwoBitsEncoder'}
    return data

  def __GPSL2TwoBitsEncoder_ToMap(self, obj):
    data = {'type': 'GPSL2TwoBitsEncoder'}
    return data

  def __GPSL1L2TwoBitsEncoder_ToMap(self, obj):
    data = {'type': 'GPSL1L2TwoBitsEncoder'}
    return data

  def __MapTo_GPSL1BitEncoder(self, data):
    return GPSL1BitEncoder()

  def __MapTo_GPSL2BitEncoder(self, data):
    return GPSL2BitEncoder()

  def __MapTo_GPSL1L2BitEncoder(self, data):
    return GPSL1L2BitEncoder()

  def __MapTo_GPSL1TwoBitsEncoder(self, data):
    return GPSL1TwoBitsEncoder()

  def __MapTo_GPSL2TwoBitsEncoder(self, data):
    return GPSL2TwoBitsEncoder()

  def __MapTo_GPSL1L2TwoBitsEncoder(self, data):
    return GPSL1L2TwoBitsEncoder()

factoryObject = ObjectFactory()

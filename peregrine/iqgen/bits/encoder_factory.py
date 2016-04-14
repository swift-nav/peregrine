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
from peregrine.iqgen.bits.encoder_glo import GLONASSL1BitEncoder
from peregrine.iqgen.bits.encoder_glo import GLONASSL2BitEncoder
from peregrine.iqgen.bits.encoder_glo import GLONASSL1L2BitEncoder
from peregrine.iqgen.bits.encoder_glo import GLONASSL1TwoBitsEncoder
from peregrine.iqgen.bits.encoder_glo import GLONASSL2TwoBitsEncoder
from peregrine.iqgen.bits.encoder_glo import GLONASSL1L2TwoBitsEncoder
from peregrine.iqgen.bits.encoder_other import GPSGLONASSBitEncoder
from peregrine.iqgen.bits.encoder_other import GPSGLONASSTwoBitsEncoder


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
    elif t is GLONASSL1BitEncoder:
      return self.__GLONASSL1BitEncoder_ToMap(obj)
    elif t is GLONASSL2BitEncoder:
      return self.__GLONASSL2BitEncoder_ToMap(obj)
    elif t is GLONASSL1L2BitEncoder:
      return self.__GLONASSL1L2BitEncoder_ToMap(obj)
    elif t is GLONASSL1TwoBitsEncoder:
      return self.__GLONASSL1TwoBitsEncoder_ToMap(obj)
    elif t is GLONASSL2TwoBitsEncoder:
      return self.__GLONASSL2TwoBitsEncoder_ToMap(obj)
    elif t is GLONASSL1L2TwoBitsEncoder:
      return self.__GLONASSL1L2TwoBitsEncoder_ToMap(obj)
    elif t is GPSGLONASSBitEncoder:
      return self.__GPSGLONASSBitEncoder_ToMap(obj)
    elif t is GPSGLONASSTwoBitsEncoder:
      return self.__GPSGLONASSTwoBitsEncoder_ToMap(obj)
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
    elif t == 'GLONASSL1BitEncoder':
      return self.__MapTo_GLONASSL1BitEncoder(data)
    elif t == 'GLONASSL2BitEncoder':
      return self.__MapTo_GLONASSL2BitEncoder(data)
    elif t == 'GLONASSL2BitEncoder':
      return self.__MapTo_GLONASSL1L2BitEncoder(data)
    elif t == 'GLONASSL1TwoBitsEncoder':
      return self.__MapTo_GLONASSL1TwoBitsEncoder(data)
    elif t == 'GLONASSL2TwoBitsEncoder':
      return self.__MapTo_GLONASSL2TwoBitsEncoder(data)
    elif t == 'GLONASSL1L2TwoBitsEncoder':
      return self.__MapTo_GLONASSL1L2TwoBitsEncoder(data)
    elif t == 'GPSGLONASSBitEncoder':
      return self.__MapTo_GPSGLONASSBitEncoder(data)
    elif t == 'GPSGLONASSTwoBitsEncoder':
      return self.__MapTo_GPSGLONASSTwoBitsEncoder(data)
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

  def __GLONASSL1BitEncoder_ToMap(self, obj):
    data = {'type': 'GLONASSL1BitEncoder'}
    return data

  def __GLONASSL2BitEncoder_ToMap(self, obj):
    data = {'type': 'GLONASSL2BitEncoder'}
    return data

  def __GLONASSL1L2BitEncoder_ToMap(self, obj):
    data = {'type': 'GLONASSL1L2BitEncoder'}
    return data

  def __GLONASSL1TwoBitsEncoder_ToMap(self, obj):
    data = {'type': 'GLONASSL1TwoBitsEncoder'}
    return data

  def __GLONASSL2TwoBitsEncoder_ToMap(self, obj):
    data = {'type': 'GLONASSL2TwoBitsEncoder'}
    return data

  def __GLONASSL1L2TwoBitsEncoder_ToMap(self, obj):
    data = {'type': 'GLONASSL1L2TwoBitsEncoder'}
    return data

  def __GPSGLONASSBitEncoder_ToMap(self, obj):
    data = {'type': 'GPSGLONASSBitEncoder'}
    return data

  def __GPSGLONASSTwoBitsEncoder_ToMap(self, obj):
    data = {'type': 'GPSGLONASSTwoBitsEncoder'}
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

  def __MapTo_GLONASSL1BitEncoder(self, data):
    return GLONASSL1BitEncoder()

  def __MapTo_GLONASSL2BitEncoder(self, data):
    return GLONASSL2BitEncoder()

  def __MapTo_GLONASSL1L2BitEncoder(self, data):
    return GLONASSL1L2BitEncoder()

  def __MapTo_GLONASSL1TwoBitsEncoder(self, data):
    return GLONASSL1TwoBitsEncoder()

  def __MapTo_GLONASSL2TwoBitsEncoder(self, data):
    return GLONASSL2TwoBitsEncoder()

  def __MapTo_GLONASSL1L2TwoBitsEncoder(self, data):
    return GLONASSL1L2TwoBitsEncoder()

factoryObject = ObjectFactory()

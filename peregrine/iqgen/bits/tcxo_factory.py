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
The :mod:`peregrine.iqgen.bits.amplitude_factory` module contains classes and
functions related to object factory for amplitude objects.

"""

from peregrine.iqgen.bits.tcxo_poly import TCXOPoly as PolyTcxo
from peregrine.iqgen.bits.tcxo_sine import TCXOSine as SineTcxo


class ObjectFactory(object):
  '''
  Object factory for amplitude objects.
  '''

  def __init__(self):
    super(ObjectFactory, self).__init__()

  def toMapForm(self, obj):
    t = type(obj)
    if t is PolyTcxo:
      return self.__PolyTcxo_ToMap(obj)
    elif t is SineTcxo:
      return self.__SineTcxo_ToMap(obj)
    else:
      raise ValueError("Invalid object type")

  def fromMapForm(self, data):
    t = data['type']
    if t == 'PolyTcxo':
      return self.__MapTo_PolyTcxo(data)
    elif t == 'SineTcxo':
      return self.__MapTo_SineTcxo(data)
    else:
      raise ValueError("Invalid object type")

  def __PolyTcxo_ToMap(self, obj):
    data = {'type': 'PolyTcxo', 'coeffs': obj.coeffs}
    return data

  def __SineTcxo_ToMap(self, obj):
    data = {'type': 'SineTcxo',
            'initial_ppm': obj.initial_ppm,
            'amplitude_ppm': obj.amplitude_ppm,
            'period_s': obj.period_s}
    return data

  def __MapTo_PolyTcxo(self, data):
    coeffs = data['coeffs']
    return PolyTcxo(coeffs)

  def __MapTo_SineTcxo(self, data):
    initial_ppm = data['initial_ppm']
    amplitude_ppm = data['amplitude_ppm']
    period_s = data['period_s']
    return SineTcxo(initial_ppm, amplitude_ppm, period_s)

factoryObject = ObjectFactory()

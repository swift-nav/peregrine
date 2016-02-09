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

from peregrine.iqgen.bits.amplitude_poly import AmplitudePoly as PolyAmplitude
from peregrine.iqgen.bits.amplitude_sine import AmplitudeSine as SineAmplitude


class ObjectFactory(object):
  '''
  Object factory for amplitude objects.
  '''

  def __init__(self):
    super(ObjectFactory, self).__init__()

  def toMapForm(self, obj):
    t = type(obj)
    if t is PolyAmplitude:
      return self.__PolyAmplitude_ToMap(obj)
    elif t is SineAmplitude:
      return self.__SineAmplitude_ToMap(obj)
    else:
      raise ValueError("Invalid object type")

  def fromMapForm(self, data):
    t = data['type']
    if t == 'PolyAmplitude':
      return self.__MapTo_PolyAmplitude(data)
    elif t == 'SineAmplitude':
      return self.__MapTo_SineAmplitude(data)
    else:
      raise ValueError("Invalid object type")

  def __PolyAmplitude_ToMap(self, obj):
    data = {'type': 'PolyAmplitude', 'coeffs': obj.coeffs}
    return data

  def __SineAmplitude_ToMap(self, obj):
    data = {'type': 'SineAmplitude',
            'initial': obj.initial,
            'amplitude': obj.amplitude,
            'period': obj.period_s}
    return data

  def __MapTo_PolyAmplitude(self, data):
    coeffs = data['coeffs']
    return PolyAmplitude(coeffs)

  def __MapTo_SineAmplitude(self, data):
    initial = data['initial']
    amplitude = data['amplitude']
    period = data['period']
    return SineAmplitude(initial, amplitude, period)

factoryObject = ObjectFactory()

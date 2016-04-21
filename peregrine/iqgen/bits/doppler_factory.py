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
The :mod:`peregrine.iqgen.bits.doppler_factory` module contains classes and
functions related to object factory for doppler control objects.

"""

from peregrine.iqgen.bits.doppler_poly import Doppler as PolyDoppler
from peregrine.iqgen.bits.doppler_sine import Doppler as SineDoppler


class ObjectFactory(object):
  '''
  Object factory for doppler control objects.
  '''

  def __init__(self):
    super(ObjectFactory, self).__init__()

  def toMapForm(self, obj):
    t = type(obj)
    if t is PolyDoppler:
      return self.__PolyDoppler_ToMap(obj)
    elif t is SineDoppler:
      return self.__SineDoppler_ToMap(obj)
    else:
      raise ValueError("Invalid object type")

  def fromMapForm(self, data):
    t = data['type']
    if t == 'PolyDoppler':
      return self.__MapTo_PolyDoppler(data)
    elif t == 'SineDoppler':
      return self.__MapTo_SineDoppler(data)
    else:
      raise ValueError("Invalid object type")

  def __PolyDoppler_ToMap(self, obj):
    data = {'type': 'PolyDoppler',
            'distance0_m': obj.distance0_m,
            'tec_epm2': obj.tec_epm2,
            'coeffs': obj.coeffs}
    return data

  def __SineDoppler_ToMap(self, obj):
    data = {'type': 'SineDoppler',
            'distance0_m': obj.distance0_m,
            'tec_epm2': obj.tec_epm2,
            'speed0_mps': obj.speed0_mps,
            'amplutude_mps': obj.amplutude_mps,
            'period_s': obj.period_s}
    return data

  def __MapTo_PolyDoppler(self, data):
    distance0_m = data['distance0_m']
    tec_epm2 = data['tec_epm2']
    coeffs = data['coeffs']
    return PolyDoppler(distance0_m=distance0_m,
                       tec_epm2=tec_epm2,
                       coeffs=coeffs)

  def __MapTo_SineDoppler(self, data):
    distance0_m = data['distance0_m']
    tec_epm2 = data['tec_epm2']
    speed0_mps = data['speed0_mps']
    amplutude_mps = data['amplutude_mps']
    period_s = data['period_s']
    return SineDoppler(distance0_m=distance0_m,
                       tec_epm2=tec_epm2,
                       speed0_mps=speed0_mps,
                       amplutude_mps=amplutude_mps,
                       period_s=period_s)

factoryObject = ObjectFactory()

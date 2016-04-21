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
The :mod:`peregrine.iqgen.bits.satellite_factory` module contains classes and
functions related to object factory for satellite objects.

"""

from peregrine.iqgen.bits.satellite_gps import GPSSatellite
from peregrine.iqgen.bits.amplitude_factory import factoryObject as amplitudeOF
from peregrine.iqgen.bits.doppler_factory import factoryObject as dopplerOF
from peregrine.iqgen.bits.message_factory import factoryObject as messageOF


class ObjectFactory(object):
  '''
  Object factory for satellite types.
  '''

  def __init__(self):
    super(ObjectFactory, self).__init__()

  def toMapForm(self, obj):
    t = type(obj)
    if t is GPSSatellite:
      return self.__GPSSatellite_ToMap(obj)
    else:
      raise ValueError("Invalid object type")

  def fromMapForm(self, data):
    t = data['type']
    if t == 'GPSSatellite':
      return self.__MapTo_GPSSatellite(data)
    else:
      raise ValueError("Invalid object type")

  def __GPSSatellite_ToMap(self, obj):
    data = {'type': 'GPSSatellite',
            'prn': obj.prn,
            'amplitude': amplitudeOF.toMapForm(obj.getAmplitude()),
            'l1caEnabled': obj.isL1CAEnabled(),
            'l2cEnabled': obj.isL2CEnabled(),
            'l1caMessage': messageOF.toMapForm(obj.getL1CAMessage()),
            'l2cMessage': messageOF.toMapForm(obj.getL2CMessage()),
            'doppler': dopplerOF.toMapForm(obj.getDoppler()),
            'l2clCodeType': obj.getL2CLCodeType(),
            'codeDopplerIgnored': obj.isCodeDopplerIgnored()
            }
    return data

  def __MapTo_GPSSatellite(self, data):
    prn = data['prn']
    doppler = dopplerOF.fromMapForm(data['doppler'])
    amplitude = amplitudeOF.fromMapForm(data['amplitude'])
    l1caEnabled = data['l1caEnabled']
    l2cEnabled = data['l2cEnabled']
    l1caMessage = messageOF.fromMapForm(data['l1caMessage'])
    l2cMessage = messageOF.fromMapForm(data['l2cMessage'])
    clCodeType = data['l2clCodeType']
    codeDopplerIgnored = data['codeDopplerIgnored']
    satellite = GPSSatellite(prn)
    satellite.setAmplitude(amplitude)
    satellite.setDoppler(doppler)
    satellite.setL1CAEnabled(l1caEnabled)
    satellite.setL2CEnabled(l2cEnabled)
    satellite.setL1CAMessage(l1caMessage)
    satellite.setL2CMessage(l2cMessage)
    satellite.setL2CLCodeType(clCodeType)
    satellite.setCodeDopplerIgnored(codeDopplerIgnored)
    return satellite

factoryObject = ObjectFactory()

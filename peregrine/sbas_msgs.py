#!/usr/bin/env python

# Copyright (C) 2015 Swift Navigation Inc.
#
# This source is subject to the license found in the file 'LICENSE' which must
# be be distributed together with this source. All other rights reserved.
#
# THIS CODE AND INFORMATION IS PROVIDED "AS IS" WITHOUT WARRANTY OF ANY KIND,
# EITHER EXPRESSED OR IMPLIED, INCLUDING BUT NOT LIMITED TO THE IMPLIED
# WARRANTIES OF MERCHANTABILITY AND/OR FITNESS FOR A PARTICULAR PURPOSE.
import pprint
from collections import OrderedDict

pp = pprint.PrettyPrinter(indent=2)


class SbasMsg:
  def __init__(self, bitstring):
    self.bitstring = bitstring
    self.crc = 0
    self.preamble = bitstring[:8]
    self.type = int(self.bitstring[8:8 + 6], 2)

  def bitstring(self):
    return self.bitstring


class SbasMsgGeo(SbasMsg):
  def __init__(self, bitstring):
    SbasMsg.__init__(self, bitstring)
    self.full_name = 'GEO Navigation Message'
    self.data = {}
    self.fields = [
      ('IOD', 8, 1, False),
      ('TOA', 13, 16, False),
      ('URA', 4, 1, False),

      ('X', 30, 0.08, True),
      ('Y', 30, 0.08, True),
      ('Z', 25, 0.4, True),

      ('X - Rate of Change', 17, 0.000625, True),
      ('Y - Rate of Change', 17, 0.000625, True),
      ('Z - Rate of Change', 18, 0.004, True),

      ('X - Accelaration', 10, 0.0000125, True),
      ('Y - Acceleration', 10, 0.0000125, True),
      ('Z - Acceleration', 10, 0.0000625, True),

      ('Time Offset', 12, pow(2, -31), True),
      ('Time Drift', 8, pow(2, -40), True)
    ]

  def __str__(self):
    s = self.full_name + " has content: \n"
    s += pprint.pformat(self.data, indent=2)
    return s

  def process(self):
    offset = 0
    for ix, field in enumerate(self.fields):
      val = int(self.bitstring[offset: offset + field[1]], 2)
      if field[3]:  # 2's complement
        if val & (1 << (field[1] - 1)):  # MSB set
          val = -((1 << field[1]) - val)
      self.data[field[0]] = val * field[2]  # Scale factor
      offset += field[1]


class SbasMsgNull(SbasMsg):
  def __init__(self, bitstring):
    SbasMsg.__init__(self, bitstring)
    self.full_name = 'Null Message'

  def __str__(self):
    return self.full_name


class SbasMsgLTC(SbasMsg):
  def __init__(self, bitstring):
    SbasMsg.__init__(self, bitstring)
    self.full_name = 'Long Term Satellite Error Corrections'

  def __str__(self):
    return self.full_name


class SbasMsgFC(SbasMsg):
  def __init__(self, bitstring):
    SbasMsg.__init__(self, bitstring)
    self.full_name = 'Fast Correction'

  def __str__(self):
    return self.full_name


class SbasMsgFCDF(SbasMsg):
  def __init__(self, bitstring):
    SbasMsg.__init__(self, bitstring)
    self.full_name = 'Fast Correction Degradation Factor'

  def __str__(self):
    return self.full_name


class SbasMsgCECM(SbasMsg):
  def __init__(self, bitstring):
    SbasMsg.__init__(self, bitstring)
    self.full_name = 'Clock-Ephemeris Covariance Matrix'

  def __str__(self):
    return self.full_name


class SbasMsgIDC(SbasMsg):
  def __init__(self, bitstring):
    SbasMsg.__init__(self, bitstring)
    self.full_name = 'Ionospheric Delay Corrections'

  def __str__(self):
    return self.full_name


class SbasMsgIGPM(SbasMsg):
  def __init__(self, bitstring):
    SbasMsg.__init__(self, bitstring)
    self.full_name = 'Ionospheric Grid Point Mask'

  def __str__(self):
    return self.full_name


class SbasMsgM(SbasMsg):
  def __init__(self, bitstring):
    SbasMsg.__init__(self, bitstring)
    self.full_name = 'PRN Mask Assignments'

  def __str__(self):
    return self.full_name


class SbasMsgAlm(SbasMsg):
  def __init__(self, bitstring):
    SbasMsg.__init__(self, bitstring)
    self.full_name = 'GEO Almanacs'

  def __str__(self):
    return self.full_name


class SbasMsgDegParam(SbasMsg):
  def __init__(self, bitstring):
    SbasMsg.__init__(self, bitstring)
    self.full_name = 'Degradation Parameters'

  def __str__(self):
    return self.full_name

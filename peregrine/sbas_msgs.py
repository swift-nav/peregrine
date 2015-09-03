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

pp = pprint.PrettyPrinter(indent=2)


class SbasMsg:
  def __init__(self, bitstring):
    self.bitstring = bitstring[8 + 6:]
    self.crc = 0
    self.preamble = bitstring[:8]
    self.type = int(bitstring[8:8 + 6], 2)

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

  def process(self):
    pass

  def __str__(self):
    s = self.full_name + " has content: \n"
    s += 'NULL'
    return s


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
    self.data = []

  def process(self):
    for idx in range(1, 211):
      if self.bitstring[idx - 1] == '1':
        self.data += ['PRN ' + str(idx)]

  def __str__(self):
    s = self.full_name + " has content: \n"
    s += pprint.pformat(self.data, indent=2)
    return s


class SbasMsgAlm(SbasMsg):
  def __init__(self, bitstring):
    SbasMsg.__init__(self, bitstring)
    self.full_name = 'GEO Almanacs'
    self.data = {}
    self.fields = [
      ('Data ID', 2, 1, False),
      ('PRN', 8, 1, False),
      ('Health', 8, 1, False),

      ('X', 15, 2600, True),
      ('Y', 15, 2600, True),
      ('Z', 9, 26000, True),

      ('X - Rate of Change', 3, 10, True),
      ('Y - Rate of Change', 3, 10, True),
      ('Z - Rate of Change', 4, 40.96, True),

      ('Time-of-Day', 11, 64, False)
    ]

  def process(self):
    offset = 0
    for idx in range(1, 4):
      tmp = {}
      for ix, field in enumerate(self.fields[:-1]):
        val = int(self.bitstring[offset: offset + field[1]], 2)
        if field[3]:  # 2's complement
          if val & (1 << (field[1] - 1)):  # MSB set
            val = -((1 << field[1]) - val)
        tmp[field[0]] = val * field[2]  # Scale factor
        offset += field[1]
      self.data['PRN ' + str(tmp['PRN'])] = tmp
    tod = self.fields[len(self.fields) - 1]
    offset_tod = tod[1]
    tod_val = self.bitstring[offset: offset + offset_tod]
    val = int(tod_val, 2)
    self.data[tod[0]] = val

  def __str__(self):
    s = self.full_name + " has content: \n"
    s += pprint.pformat(self.data, indent=2)
    return s


class SbasMsgDegParam(SbasMsg):
  def __init__(self, bitstring):
    SbasMsg.__init__(self, bitstring)
    self.full_name = 'Degradation Parameters'
    self.data = {}
    self.fields =[
      ('B_rcc', 10, 0.002, False),
      ('C_ltc_lsb', 10, 0.002, False),
      ('C_ltc_v1', 10, 0.00005, False),
      ('I_ltc_v1', 9, 1, False),
      ('C_ltc_v0', 10, 0.002, False),
      ('I_ltc_v0', 9, 1, False),
      ('C_geo_lsb', 10, 0.0005, False),
      ('C_geo_v', 10, 0.00005, False),
      ('I_geo', 9, 1, False),
      ('C_er', 6, 0.5, False),
      ('C_iono_step', 10, 0.001, False),
      ('I_iono', 9, 1, False),
      ('C_iono_ramp', 10, 0.000005, False),
      ('RSS_UDRE', 1, 1, False),
      ('RSS_iono', 1, 1, False),
      ('C_covariance', 7, 0.1, False)
    ]

  def process(self):
    offset = 0
    for ix, field in enumerate(self.fields):
      val = int(self.bitstring[offset: offset + field[1]], 2)
      if field[3]:  # 2's complement
        if val & (1 << (field[1] - 1)):  # MSB set
          val = -((1 << field[1]) - val)
      self.data[field[0]] = val * field[2]  # Scale factor
      offset += field[1]

  def __str__(self):
    s = self.full_name + " has content: \n"
    s += pprint.pformat(self.data, indent=2)
    return s

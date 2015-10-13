#!/usr/bin/env python
# coding=utf-8

# Copyright (C) 2015 Swift Navigation Inc.
#
# This source is subject to the license found in the file 'LICENSE' which must
# be be distributed together with this source. All other rights reserved.
#
# THIS CODE AND INFORMATION IS PROVIDED "AS IS" WITHOUT WARRANTY OF ANY KIND,
# EITHER EXPRESSED OR IMPLIED, INCLUDING BUT NOT LIMITED TO THE IMPLIED
# WARRANTIES OF MERCHANTABILITY AND/OR FITNESS FOR A PARTICULAR PURPOSE.
import pprint
from crc24 import *

pp = pprint.PrettyPrinter(indent=2)


def bits2byte(bstring):
  bts = []
  res = []
  i = b_len = len(bstring)
  while i % 8 != 0:
    i += 1
  rem = i - b_len
  for i in range(0, rem):
    bts += [0]
  for i in range(0, b_len):
    bts += [int(bstring[i])]
  for i in range(0, len(bts), 8):
    byte_string = bts[i: i + 8]
    byte_string.reverse()
    val = 0
    for j in range(0, 8):
      if byte_string[j] == 1:
        val += pow(2, j)
    res += [val]
  return res


def getbitu(buff, pos, l):
  bits = 0
  for i in range(0, pos + l):
    bits = (bits << 1) + ((buff[i / 8] >> (7 - i % 8)) & 1)
  return bits


class SbasMsg:
  def __init__(self, bitstring):
    self.preamble_bitstring = bitstring[:8]
    self.type_bitstring = bitstring[8: 8 + 6]
    self.msg_bitstring = bitstring[8 + 6: 226]
    self.crc_bitstring = bitstring[226: 226 + 24]
    self.type = int(bitstring[8: 8 + 6], 2)
    self.crc = 0
    self.computed_crc = 0

  def check_crc(self):
    crc_bytearray = bits2byte(self.crc_bitstring)
    msg_bytearray = bits2byte(self.preamble_bitstring + self.type_bitstring + self.msg_bitstring)
    computed_crc = crc24(msg_bytearray, len(msg_bytearray))
    if len(crc_bytearray) < 3:
      raise ValueError("Msg incomplete!")
    msg_crc = getbitu(crc_bytearray, 0, 24)
    if computed_crc != msg_crc:
      raise ValueError("Msg CRC is bad!")
    else:
      self.crc = hex(msg_crc)
      self.computed_crc = hex(computed_crc)
      return True

  def bitstring(self):
    return self.preamble_bitstring + self.msg_bitstring + self.crc_bitstring


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

      ('X - Acceleration', 10, 0.0000125, True),
      ('Y - Acceleration', 10, 0.0000125, True),
      ('Z - Acceleration', 10, 0.0000625, True),

      ('Time Offset', 12, pow(2, -31), True),
      ('Time Drift', 8, pow(2, -40), True)
    ]

  def __str__(self):
    s = self.full_name + " has content: \n"
    s += pprint.pformat(self.data, indent=2)
    return s

  def __eq__(self, other):
    return self.__dict__ == other.__dict__

  def process(self):
    SbasMsg.check_crc(self)
    offset = 0
    for ix, field in enumerate(self.fields):
      val = int(self.msg_bitstring[offset: offset + field[1]], 2)
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
    SbasMsg.check_crc(self)

  def __str__(self):
    return self.full_name

  def __eq__(self, other):
    return self.__dict__ == other.__dict__


class SbasMsgT(SbasMsg):
  def __init__(self, bitstring):
    SbasMsg.__init__(self, bitstring)
    self.full_name = 'Test Message'

  def process(self):
    SbasMsg.check_crc(self)

  def __str__(self):
    return self.full_name

  def __eq__(self, other):
    return self.__dict__ == other.__dict__


class SbasMsgSM(SbasMsg):
  def __init__(self, bitstring):
    SbasMsg.__init__(self, bitstring)
    self.full_name = 'Service Message'

  def process(self):
    SbasMsg.check_crc(self)

  def __str__(self):
    return self.full_name

  def __eq__(self, other):
    return self.__dict__ == other.__dict__


class SbasMsgMC(SbasMsg):
  def __init__(self, bitstring):
    SbasMsg.__init__(self, bitstring)
    self.full_name = 'Mixed Fast Correction/GPS Long Term Satellite Error Corrections'

  def process(self):
    SbasMsg.check_crc(self)

  def __str__(self):
    return self.full_name

  def __eq__(self, other):
    return self.__dict__ == other.__dict__


class SbasMsgII(SbasMsg):
  def __init__(self, bitstring):
    SbasMsg.__init__(self, bitstring)
    self.full_name = 'Integrity Information'

  def process(self):
    SbasMsg.check_crc(self)

  def __str__(self):
    return self.full_name

  def __eq__(self, other):
    return self.__dict__ == other.__dict__


class SbasMsgLTC(SbasMsg):
  def __init__(self, bitstring):
    SbasMsg.__init__(self, bitstring)
    self.full_name = 'Long Term Satellite Error Corrections'

  def process(self):
    SbasMsg.check_crc(self)

  def __str__(self):
    return self.full_name

  def __eq__(self, other):
    return self.__dict__ == other.__dict__


class SbasMsgFC(SbasMsg):
  def __init__(self, bitstring):
    SbasMsg.__init__(self, bitstring)
    self.full_name = 'Fast Correction'

  def process(self):
    SbasMsg.check_crc(self)

  def __str__(self):
    return self.full_name

  def __eq__(self, other):
    return self.__dict__ == other.__dict__


class SbasMsgFCDF(SbasMsg):
  def __init__(self, bitstring):
    SbasMsg.__init__(self, bitstring)
    self.full_name = 'Fast Correction Degradation Factor'

  def process(self):
    SbasMsg.check_crc(self)

  def __str__(self):
    return self.full_name

  def __eq__(self, other):
    return self.__dict__ == other.__dict__


class SbasMsgCECM(SbasMsg):
  def __init__(self, bitstring):
    SbasMsg.__init__(self, bitstring)
    self.full_name = 'Clock-Ephemeris Covariance Matrix'

  def process(self):
    SbasMsg.check_crc(self)

  def __str__(self):
    return self.full_name

  def __eq__(self, other):
    return self.__dict__ == other.__dict__


class SbasMsgIDC(SbasMsg):
  def __init__(self, bitstring):
    SbasMsg.__init__(self, bitstring)
    self.full_name = 'Ionospheric Delay Corrections'

  def process(self):
    SbasMsg.check_crc(self)

  def __str__(self):
    return self.full_name

  def __eq__(self, other):
    return self.__dict__ == other.__dict__


class SbasMsgIGPM(SbasMsg):
  def __init__(self, bitstring):
    SbasMsg.__init__(self, bitstring)
    self.full_name = 'Ionospheric Grid Point Mask'

  def process(self):
    SbasMsg.check_crc(self)

  def __str__(self):
    return self.full_name

  def __eq__(self, other):
    return self.__dict__ == other.__dict__


class SbasMsgTime(SbasMsg):
  def __init__(self, bitstring):
    SbasMsg.__init__(self, bitstring)
    self.full_name = 'SBAS Network Time/UTC Offset Parameters'
    self.data = {}
    self.fields = [
      ('A_1wnt', 24, pow(2, -50), True),
      ('A_0wnt', 32, pow(2, -3), False),
      ('t_0t', 8, pow(2, 12), False),

      ('WN_t', 8, 1, False),
      ('DT_ls', 8, 1, True),
      ('WN_lsf', 8, 1, False),

      ('DN', 8, 1, True),
      ('DT_lsf', 8, 1, True),

      ('UTC Standard Identifier ', 3, 1, False),
      ('GPS Time-of-Week – TOW', 20, 1, False),
      ('GPS Week Number ', 10, 1, False)
    ]

  def __str__(self):
    s = self.full_name + " has content: \n"
    s += pprint.pformat(self.data, indent=2)
    return s

  def process(self):
    SbasMsg.check_crc(self)
    offset = 0
    for ix, field in enumerate(self.fields):
      val = int(self.msg_bitstring[offset: offset + field[1]], 2)
      if field[3]:  # 2's complement
        if val & (1 << (field[1] - 1)):  # MSB set
          val = -((1 << field[1]) - val)
      self.data[field[0]] = val * field[2]  # Scale factor
      offset += field[1]

  def __eq__(self, other):
    return self.__dict__ == other.__dict__


class SbasMsgIT(SbasMsg):
  def __init__(self, bitstring):
    SbasMsg.__init__(self, bitstring)
    self.full_name = 'Internal Test'

  def process(self):
    SbasMsg.check_crc(self)

  def __str__(self):
    return self.full_name

  def __eq__(self, other):
    return self.__dict__ == other.__dict__


class SbasMsgM(SbasMsg):
  def __init__(self, bitstring):
    SbasMsg.__init__(self, bitstring)
    self.full_name = 'PRN Mask Assignments'
    self.data = []

  def process(self):
    SbasMsg.check_crc(self)
    for idx in range(1, 211):
      if self.msg_bitstring[idx - 1] == '1':
        self.data += ['PRN ' + str(idx)]

  def __str__(self):
    s = self.full_name + " has content: \n"
    s += pprint.pformat(self.data, indent=2)
    return s

  def __eq__(self, other):
    return self.__dict__ == other.__dict__


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
    SbasMsg.check_crc(self)
    offset = 0
    for idx in range(1, 4):
      tmp = {}
      for ix, field in enumerate(self.fields[:-1]):
        val = int(self.msg_bitstring[offset: offset + field[1]], 2)
        if field[3]:  # 2's complement
          if val & (1 << (field[1] - 1)):  # MSB set
            val = -((1 << field[1]) - val)
        tmp[field[0]] = val * field[2]  # Scale factor
        offset += field[1]
      self.data['PRN ' + str(tmp['PRN'])] = tmp
    tod = self.fields[len(self.fields) - 1]
    offset_tod = tod[1]
    tod_val = self.msg_bitstring[offset: offset + offset_tod]
    val = int(tod_val, 2)
    self.data[tod[0]] = val

  def __str__(self):
    s = self.full_name + " has content: \n"
    s += pprint.pformat(self.data, indent=2)
    return s

  def __eq__(self, other):
    return self.__dict__ == other.__dict__


class SbasMsgDegParam(SbasMsg):
  def __init__(self, bitstring):
    SbasMsg.__init__(self, bitstring)
    self.full_name = 'Degradation Parameters'
    self.data = {}
    self.fields = [
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
    SbasMsg.check_crc(self)
    offset = 0
    for ix, field in enumerate(self.fields):
      val = int(self.msg_bitstring[offset: offset + field[1]], 2)
      if field[3]:  # 2's complement
        if val & (1 << (field[1] - 1)):  # MSB set
          val = -((1 << field[1]) - val)
      self.data[field[0]] = val * field[2]  # Scale factor
      offset += field[1]

  def __str__(self):
    s = self.full_name + " has content: \n"
    s += pprint.pformat(self.data, indent=2)
    return s

  def __eq__(self, other):
    return self.__dict__ == other.__dict__

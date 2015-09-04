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


tbl_CRC24Q = [
  0x000000, 0x864CFB, 0x8AD50D, 0x0C99F6, 0x93E6E1, 0x15AA1A, 0x1933EC, 0x9F7F17,
  0xA18139, 0x27CDC2, 0x2B5434, 0xAD18CF, 0x3267D8, 0xB42B23, 0xB8B2D5, 0x3EFE2E,
  0xC54E89, 0x430272, 0x4F9B84, 0xC9D77F, 0x56A868, 0xD0E493, 0xDC7D65, 0x5A319E,
  0x64CFB0, 0xE2834B, 0xEE1ABD, 0x685646, 0xF72951, 0x7165AA, 0x7DFC5C, 0xFBB0A7,
  0x0CD1E9, 0x8A9D12, 0x8604E4, 0x00481F, 0x9F3708, 0x197BF3, 0x15E205, 0x93AEFE,
  0xAD50D0, 0x2B1C2B, 0x2785DD, 0xA1C926, 0x3EB631, 0xB8FACA, 0xB4633C, 0x322FC7,
  0xC99F60, 0x4FD39B, 0x434A6D, 0xC50696, 0x5A7981, 0xDC357A, 0xD0AC8C, 0x56E077,
  0x681E59, 0xEE52A2, 0xE2CB54, 0x6487AF, 0xFBF8B8, 0x7DB443, 0x712DB5, 0xF7614E,
  0x19A3D2, 0x9FEF29, 0x9376DF, 0x153A24, 0x8A4533, 0x0C09C8, 0x00903E, 0x86DCC5,
  0xB822EB, 0x3E6E10, 0x32F7E6, 0xB4BB1D, 0x2BC40A, 0xAD88F1, 0xA11107, 0x275DFC,
  0xDCED5B, 0x5AA1A0, 0x563856, 0xD074AD, 0x4F0BBA, 0xC94741, 0xC5DEB7, 0x43924C,
  0x7D6C62, 0xFB2099, 0xF7B96F, 0x71F594, 0xEE8A83, 0x68C678, 0x645F8E, 0xE21375,
  0x15723B, 0x933EC0, 0x9FA736, 0x19EBCD, 0x8694DA, 0x00D821, 0x0C41D7, 0x8A0D2C,
  0xB4F302, 0x32BFF9, 0x3E260F, 0xB86AF4, 0x2715E3, 0xA15918, 0xADC0EE, 0x2B8C15,
  0xD03CB2, 0x567049, 0x5AE9BF, 0xDCA544, 0x43DA53, 0xC596A8, 0xC90F5E, 0x4F43A5,
  0x71BD8B, 0xF7F170, 0xFB6886, 0x7D247D, 0xE25B6A, 0x641791, 0x688E67, 0xEEC29C,
  0x3347A4, 0xB50B5F, 0xB992A9, 0x3FDE52, 0xA0A145, 0x26EDBE, 0x2A7448, 0xAC38B3,
  0x92C69D, 0x148A66, 0x181390, 0x9E5F6B, 0x01207C, 0x876C87, 0x8BF571, 0x0DB98A,
  0xF6092D, 0x7045D6, 0x7CDC20, 0xFA90DB, 0x65EFCC, 0xE3A337, 0xEF3AC1, 0x69763A,
  0x578814, 0xD1C4EF, 0xDD5D19, 0x5B11E2, 0xC46EF5, 0x42220E, 0x4EBBF8, 0xC8F703,
  0x3F964D, 0xB9DAB6, 0xB54340, 0x330FBB, 0xAC70AC, 0x2A3C57, 0x26A5A1, 0xA0E95A,
  0x9E1774, 0x185B8F, 0x14C279, 0x928E82, 0x0DF195, 0x8BBD6E, 0x872498, 0x016863,
  0xFAD8C4, 0x7C943F, 0x700DC9, 0xF64132, 0x693E25, 0xEF72DE, 0xE3EB28, 0x65A7D3,
  0x5B59FD, 0xDD1506, 0xD18CF0, 0x57C00B, 0xC8BF1C, 0x4EF3E7, 0x426A11, 0xC426EA,
  0x2AE476, 0xACA88D, 0xA0317B, 0x267D80, 0xB90297, 0x3F4E6C, 0x33D79A, 0xB59B61,
  0x8B654F, 0x0D29B4, 0x01B042, 0x87FCB9, 0x1883AE, 0x9ECF55, 0x9256A3, 0x141A58,
  0xEFAAFF, 0x69E604, 0x657FF2, 0xE33309, 0x7C4C1E, 0xFA00E5, 0xF69913, 0x70D5E8,
  0x4E2BC6, 0xC8673D, 0xC4FECB, 0x42B230, 0xDDCD27, 0x5B81DC, 0x57182A, 0xD154D1,
  0x26359F, 0xA07964, 0xACE092, 0x2AAC69, 0xB5D37E, 0x339F85, 0x3F0673, 0xB94A88,
  0x87B4A6, 0x01F85D, 0x0D61AB, 0x8B2D50, 0x145247, 0x921EBC, 0x9E874A, 0x18CBB1,
  0xE37B16, 0x6537ED, 0x69AE1B, 0xEFE2E0, 0x709DF7, 0xF6D10C, 0xFA48FA, 0x7C0401,
  0x42FA2F, 0xC4B6D4, 0xC82F22, 0x4E63D9, 0xD11CCE, 0x575035, 0x5BC9C3, 0xDD8538
]


def crc24(buff, l):
  crc = 0
  for i in range(0, l):
    crc = ((crc << 8) & 0xFFFFFF) ^ tbl_CRC24Q[(crc >> 16) ^ buff[i]]
  return crc


class SbasMsg:
  def __init__(self, bitstring):
    self.preamble_bitstring = bitstring[:8]
    self.type_bitstring = bitstring[8: 8 + 6]
    self.msg_bitstring = bitstring[8 + 6: 226]
    self.crc_bitstring = bitstring[226: 226 + 24]
    self.type = int(bitstring[8: 8 + 6], 2)

  def process(self):
    crc_bytearray = bits2byte(self.crc_bitstring)
    msg_bytearray = bits2byte(self.preamble_bitstring + self.type_bitstring + self.msg_bitstring)
    computed_crc = crc24(msg_bytearray, len(msg_bytearray))
    if len(crc_bytearray) < 3:
      raise ValueError("Msg incomplete!")
    msg_crc = getbitu(crc_bytearray, 0, 24)
    if computed_crc != msg_crc:
      raise ValueError("Msg CRC is bad!")
    else:
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
    SbasMsg.process(self)
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
    SbasMsg.process(self)

  def __str__(self):
    s = self.full_name + " has content: \n"
    s += 'NULL'
    return s

  def __eq__(self, other):
    return self.__dict__ == other.__dict__


class SbasMsgLTC(SbasMsg):
  def __init__(self, bitstring):
    SbasMsg.__init__(self, bitstring)
    self.full_name = 'Long Term Satellite Error Corrections'

  def process(self):
    raise NotImplementedError

  def __str__(self):
    return self.full_name

  def __eq__(self, other):
    return self.__dict__ == other.__dict__


class SbasMsgFC(SbasMsg):
  def __init__(self, bitstring):
    SbasMsg.__init__(self, bitstring)
    self.full_name = 'Fast Correction'

  def process(self):
    raise NotImplementedError

  def __str__(self):
    return self.full_name

  def __eq__(self, other):
    return self.__dict__ == other.__dict__


class SbasMsgFCDF(SbasMsg):
  def __init__(self, bitstring):
    SbasMsg.__init__(self, bitstring)
    self.full_name = 'Fast Correction Degradation Factor'

  def process(self):
    raise NotImplementedError

  def __str__(self):
    return self.full_name

  def __eq__(self, other):
    return self.__dict__ == other.__dict__


class SbasMsgCECM(SbasMsg):
  def __init__(self, bitstring):
    SbasMsg.__init__(self, bitstring)
    self.full_name = 'Clock-Ephemeris Covariance Matrix'

  def process(self):
    raise NotImplementedError

  def __str__(self):
    return self.full_name

  def __eq__(self, other):
    return self.__dict__ == other.__dict__


class SbasMsgIDC(SbasMsg):
  def __init__(self, bitstring):
    SbasMsg.__init__(self, bitstring)
    self.full_name = 'Ionospheric Delay Corrections'

  def process(self):
    raise NotImplementedError

  def __str__(self):
    return self.full_name

  def __eq__(self, other):
    return self.__dict__ == other.__dict__


class SbasMsgIGPM(SbasMsg):
  def __init__(self, bitstring):
    SbasMsg.__init__(self, bitstring)
    self.full_name = 'Ionospheric Grid Point Mask'

  def process(self):
    raise NotImplementedError

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
    SbasMsg.process(self)
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
    raise NotImplementedError

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
    SbasMsg.process(self)
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
    SbasMsg.process(self)
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

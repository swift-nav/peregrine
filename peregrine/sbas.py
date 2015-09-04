#!/usr/bin/env python

# Copyright (C) 2015 Swift Navigation Inc.
#
# This source is subject to the license found in the file 'LICENSE' which must
# be be distributed together with this source. All other rights reserved.
#
# THIS CODE AND INFORMATION IS PROVIDED "AS IS" WITHOUT WARRANTY OF ANY KIND,
# EITHER EXPRESSED OR IMPLIED, INCLUDING BUT NOT LIMITED TO THE IMPLIED
# WARRANTIES OF MERCHANTABILITY AND/OR FITNESS FOR A PARTICULAR PURPOSE.

import sys
import argparse
import re
from sbas_msgs import *


def bits(f):
  bbytes = (ord(b) for b in f.read())
  for b in bbytes:
    for i in xrange(8):
      yield (b >> (7 - i)) & 1


def process_all_preambles(self):
  locations = {sense: {'first': [m.start() for m in re.finditer(self.sbas_preambles[sense][0], self.bitstring)],
                       'second': [m.start() for m in re.finditer(self.sbas_preambles[sense][1], self.bitstring)],
                       'third': [m.start() for m in re.finditer(self.sbas_preambles[sense][2], self.bitstring)]}
               for sense in ['normal', 'inverse']}
  for sense in ['normal', 'inverse']:
    for loc in locations[sense]['first']:
      if self.bitstring[loc + 250:loc + 250 + 8] == self.sbas_preambles[sense][1]:
        if self.bitstring[loc + 500: loc + 508] == self.sbas_preambles[sense][2]:
          for i in range(loc, loc + (250 * 3), 250):
            b = self.bitstring[i:i + 250]
            if sense == 'inverse':
              b = ''.join(map(lambda c: chr(ord(c) ^ 1), b))
            m_type = int(b[8:8 + 6], 2)
            verify = SbasMsg(b)
            try:
              verify.process()
            except ValueError as e:
              self.count_bad += 1
              pass
            try:
              msg = self.type_to_class[m_type](b)
              try:
                msg.process()
                self.count_good += 1
                self.messages += [msg]
              except NotImplementedError:
                pass
            except:
              pass


def process_any_preamble(self):
  locations = {sense: {'first': [m.start() for m in re.finditer(self.sbas_preambles[sense][0], self.bitstring)],
                       'second': [m.start() for m in re.finditer(self.sbas_preambles[sense][1], self.bitstring)],
                       'third': [m.start() for m in re.finditer(self.sbas_preambles[sense][2], self.bitstring)]}
               for sense in ['normal', 'inverse']}
  for sense in ['normal', 'inverse']:
    print sense
    for l in ['first', 'second', 'third']:
      print l
      for loc in locations[sense][l]:
        b = self.bitstring[loc:loc + 250]
        if sense == 'inverse':
          b = ''.join(map(lambda c: chr(ord(c) ^ 1), b))
        m_type = int(b[8:8 + 6], 2)
        verify = SbasMsg(b)
        try:
          verify.process()
        except ValueError as e:
          self.count_bad += 1
          pass
        try:
          msg = self.type_to_class[m_type](b)
          try:
            msg.process()
            self.count_good += 1
            self.messages += [msg]
            print msg.preamble_bitstring
          except NotImplementedError:
            pass
        except:
          pass

def is_inverse(val):
  if val == '10101100' or val == '01100101' or val == '00111001':
    return True
  return False

def process_new(self):
  p_to_loc = {
    '01010011': [],
    '10011010': [],
    '11000110': [],
    '10101100': [],
    '01100101': [],
    '00111001': []
  }
  for idx, value in enumerate(p_to_loc):
    for m in re.finditer(value, self.bitstring):
      p_to_loc[value] += [m.start()]
  for idx, value in enumerate(p_to_loc):
    locations = p_to_loc[value]
    for loc in locations:
      b = self.bitstring[loc:loc + 250]
      if is_inverse(value) is True:
        b = ''.join(map(lambda c: chr(ord(c) ^ 1), b))
      m_type = int(b[8:8 + 6], 2)
      verify = SbasMsg(b)
      try:
        verify.process()
      except ValueError as e:
        self.count_bad += 1
        pass
      try:
        msg = self.type_to_class[m_type](b)
        try:
          msg.process()
          self.count_good += 1
          self.messages += [msg]
        except NotImplementedError:
          pass
      except:
        pass

class Sbas:
  frame_len = 250
  preamble_len = 8
  sbas_preambles = {
    'normal': ['01010011', '10011010', '11000110'],
    'inverse': ['10101100', '01100101', '00111001']
  }
  type_to_class = {
    1: SbasMsgM,
    2: SbasMsgFC,
    3: SbasMsgFC,
    4: SbasMsgFC,
    5: SbasMsgFC,
    7: SbasMsgFCDF,
    9: SbasMsgGeo,
    10: SbasMsgDegParam,
    12: SbasMsgTime,
    18: SbasMsgIGPM,
    17: SbasMsgAlm,
    25: SbasMsgLTC,
    26: SbasMsgIDC,
    28: SbasMsgCECM,
    62: SbasMsgIT,
    63: SbasMsgNull
  }

  def __init__(self, sbas_file, prn):
    try:
      self.file = open(sbas_file, 'rb')
    except IOError as e:
      print str(e)
      sys.exit(1)

    self.prn = prn
    self.count_good = 0
    self.count_bad = 0
    self.bitstring = ''
    self.p_function = process_any_preamble

    for b in bits(self.file):
      self.bitstring += str(b)
    self.messages = []


parser = argparse.ArgumentParser(description='Utility to decode SBAS binary files')


def get_args():
  parser.add_argument("file", help="the data file to process")
  parser.add_argument('-p', '--prn', nargs=1, help='PRN of the satellite')
  parser.add_argument('-c', '--check', nargs=1, help='Type of function to check for preambles [all,any]')
  return parser.parse_args()


def main():
  args = get_args()
  prn = args.prn
  check = args.check

  if args.file is None:
    parser.print_help()
    sys.exit(1)

  if check is None:
    parser.print_help()
    sys.exit(1)

  check = check[0]
  sbas_proc = Sbas(args.file, prn)
  if check == 'all':
    sbas_proc.p_function = process_all_preambles
  elif check == 'any':
    sbas_proc.p_function = process_any_preamble
  elif check == 'new':
    sbas_proc.p_function = process_new
  else:
    parser.print_help()
    sys.exit(1)
  sbas_proc.p_function(sbas_proc)

  for msg in sbas_proc.messages:
    print msg

  print str(args.file) + " has " + str(sbas_proc.count_good) + " good messages and " + \
      str(sbas_proc.count_bad) + " bad messages!"


if __name__ == '__main__':
  main()

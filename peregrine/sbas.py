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
    18: SbasMsgIGPM,
    17: SbasMsgAlm,
    25: SbasMsgLTC,
    26: SbasMsgIDC,
    28: SbasMsgCECM,
    63: SbasMsgNull
  }

  def __init__(self, sbas_file, prn):
    try:
      self.file = open(sbas_file, 'rb')
    except IOError as e:
      print str(e)
      sys.exit(1)
    self.prn = prn
    self.count = 0
    self.bitstring = ''
    for b in bits(self.file):
      self.bitstring += str(b)
    self.messages = []

  def process(self):
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

              msg = self.type_to_class[m_type](b)

              self.count += 1
              self.messages += [msg]

              if msg.type == 9 or msg.type == 17 or msg.type == 1 or msg.type == 63 or msg.type == 10:
                msg.process()
                print msg
                print


parser = argparse.ArgumentParser(description='Utility to decode SBAS binary files')


def get_args():
  parser.add_argument("file", help="the data file to process")
  parser.add_argument('-p', '--prn', nargs=1, help='PRN of the satellite')
  return parser.parse_args()


def main():
  args = get_args()
  file = args.file
  prn = args.prn
  if args.file is None:
    parser.print_help()
    sys.exit(1)
  sbas_proc = Sbas(args.file, prn)
  sbas_proc.process()
  print str(file) + " has " + str(sbas_proc.count) + " messages."


if __name__ == '__main__':
    main()

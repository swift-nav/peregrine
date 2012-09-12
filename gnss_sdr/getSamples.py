#!/usr/bin/python
#--------------------------------------------------------------------------
#                           SoftGNSS v3.0
#
# Copyright (C) Darius Plausinaitis and Dennis M. Akos
# Written by Darius Plausinaitis and Dennis M. Akos
# Converted to Python by Colin Beighley
#--------------------------------------------------------------------------
#This program is free software; you can redistribute it and/or
#modify it under the terms of the GNU General Public License
#as published by the Free Software Foundation; either version 2
#of the License, or (at your option) any later version.
#
#This program is distributed in the hope that it will be useful,
#but WITHOUT ANY WARRANTY; without even the implied warranty of
#MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#GNU General Public License for more details.
#
#You should have received a copy of the GNU General Public License
#along with this program; if not, write to the Free Software
#Foundation, Inc., 51 Franklin Street, Fifth Floor, Boston, MA  02110-1301,
#USA.
#--------------------------------------------------------------------------

import numpy

def ascii_int8(fileName, numReadSamples, numSkipSamples):
  f = open(fileName, 'r')
  samps = map(int, f.readlines())
  for s in samps:
    if not s in [-7, -5, -3, -1, 1, 3, 5, 7]:
      raise Exception("Sample out of range")
  return samps[numSkipSamples:numSkipSamples+numReadSamples]

def uint8(fileName, numReadSamples, numSkipSamples):
  signmag_dict = {0: 1,  \
                  1: 3,  \
                  2: 5,  \
                  3: 7,  \
                  4: -1, \
                  5: -3, \
                  6: -5, \
                  7: -7}
  f = open(fileName, 'r')
  f.seek(numSkipSamples)
  samps_uint8 = f.read(numReadSamples)
  samps = [signmag_dict[ord(i)] for i in samps_uint8]
  for s in samps:
    if not s in [-7, -5, -3, -1, 1, 3, 5, 7]:
      raise Exception("Sample out of range")
  return samps

def int8(fileName,numReadSamples,numSkipSamples):

  #Open file and seek to appropriate sample
  f = open(fileName,'r')
  f.seek(numSkipSamples)
  data = numpy.fromfile(f, dtype=numpy.int8, count=numReadSamples)
  f.close()
  count = len(data)

  if (count < numReadSamples):
    raise Exception("Couldn't read %d of samples from sample file" % (numReadSamples))

  return data

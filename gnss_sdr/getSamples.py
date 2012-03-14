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

def int8(fileName,numReadSamples,numSkipSamples):

  #Plot raw data
  f = open(fileName,'r')
  f.seek(numSkipSamples)

  #Find number of samples per code period
  data_byte = f.read(numReadSamples)
  f.close()
  count = len(data_byte)

  if (count < numReadSamples):
    raise Exception("Couldn't read %d of samples from sample file" % (numReadSamples))

  #Convert to ints
  data = [0]*count
  for i in range(0,count):
    ord_dbi = ord(data_byte[i])
    #data[i] positive or zero
    if (ord_dbi >= 0) and (ord_dbi < 8):
      data[i] = ord_dbi
    #data[i] negative
    elif (ord_dbi > 247) and (ord_dbi < 256):
      data[i] = -256 + ord_dbi
    else:
      raise Exception("Encountered an unknown char in sample file")

  return data

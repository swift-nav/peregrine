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
import numpy as np
from findPreambles import findPreambles
from ephemeris import ephemeris
import corrs2bits

def navigation(trackResults, settings):
  numGoodSats = 0
  for i in range(len(trackResults)):
    if (trackResults[i].status == 'T'):
      numGoodSats = numGoodSats + 1
  if (numGoodSats < 4):
    raise Exception('Too few satellites to calculate nav solution')
  ##TODO : check lengths of all trackResults prompt correlations?
  if (len(trackResults[0].I_P) < 36000):
    raise Exception('Length of tracking too short to calculate nav solution')

  (subFrameStart, activeChnList) = findPreambles(trackResults,settings)
  
  #Pass 1500 nav bits (5 subframes), starting at a subframe preamble, to ephemeris.py to get ephemeris
  eph = [[] for i in range(32)]
#  for channelNr in activeChnList:
  ##TODO : CHANGE FOR LOOP BACK TO OVER activeChnList##
  for channelNr in [0]:
    #Get 1500 nav bits starting at a subframe
    navBitsIndices = np.r_[subFrameStart[channelNr]:subFrameStart[channelNr]+(1500*20)]
    navBits = corrs2bits.unsigned(trackResults[channelNr].I_P[navBitsIndices])
    #Get the last parity bit of the previous subFrame 
    #subFrame's first 24 bits are XOR'd with it before transmission
    D30starIndices = np.r_[subFrameStart[channelNr]-20:subFrameStart[channelNr]]
    D30star = corrs2bits.unsigned(trackResults[channelNr].I_P[D30starIndices])
    #Extract ephemeris from the 5 subFrames
    (eph[trackResults[channelNr].PRN], TOW) = ephemeris(navBits,D30star)

  ##TODO : remove below statement
  (navSolutions, eph) = (0,0)
  return (navSolutions, eph)

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
import matplotlib.pyplot as plt
from navPartyChk import navPartyChk

def findPreambles(trackResults, settings):
  #Preamble search can be delayed to a later point in the track
  #results to avoid noise due to tracking loop transients
  searchStartOffset = 0 
  #Initialize the firstSubFrame array
  firstSubFrame = ['-' for i in range(len(trackResults))]
  #Generate the preamble pattern (50 Hz)
  preamble_bits = [1,-1,-1,-1,1,-1,1,1]
  #Upsample to 1KHz (tracking loop speed) 
  preamble_ms = np.repeat(preamble_bits,20) 
  #Make a list of channels excluding the channels that are not tracking
  activeChnList = []
  for i in range(len(trackResults)):
    if (trackResults[i].status == 'T'):
      activeChnList.append(i)
  #Correlate tracking bits with preamble
  for channelNr in activeChnList[-1:-len(activeChnList)-1:-1]:
    bits = trackResults[channelNr].I_P[\
              np.r_[0+searchStartOffset:len(trackResults[channelNr].I_P)]]
    #Hard limit the prompt correlation output to +1/-1
    #if bits[n] = 0, then sign(bits[n]) = 0, but we don't care about
    #that case because we can't assume bit parity from a correlation of 0
    bits = np.sign(bits)
    #Correlate preamble with the tracking output - convolution reverses vector that is convolved with
    tlmXcorrResult = np.correlate(bits, preamble_ms,mode='valid')
    index = None
    index2 = None
    #40 = 2 * 20 ms/bit = 40 to give enough room to get parity bits from previous subframe
    #1200 = 2*30 * 20 ms/bit: to give room to get (TLM & HOW), and to account for
    #'valid' not searching last 159 shifts of upsampled preamble with bits
    convSearchRange = np.r_[40:len(bits)-1200] 
    #Find where preamble starts
    #153 from (8 preamble bits * 20 bits/ms) 160 minus a
    #little slop for slight misalignment
    index = np.nonzero(np.array(np.greater(np.abs(\
               tlmXcorrResult[convSearchRange]),153),dtype=int))[0] + searchStartOffset + 40
    #Analyze detected preambles
    for i in range(len(index)-1):
      #Find distance in time between this occurance and the other 'preambles'
      #If 6000ms (6s), then validate the parities of two words to verify
      index2 = index - index[i]
      #If we find preambles 6000 ms apart, check the preambles of the TLM and HOW
      if any(np.equal(index2,6000)):
        tlmstar = corrs2navbits(trackResults[channelNr].I_P[index[i]-40:index[i]])
        tlm = corrs2navbits(trackResults[channelNr].I_P[index[i]:index[i] + 20*30])
        howstar = corrs2navbits(trackResults[channelNr].I_P[index[i]+20*30-40:index[i]+20*30])
        how = corrs2navbits(trackResults[channelNr].I_P[index[i] + 20*30:index[i]+20*60])
        #Check the parity of the TLM and HOW words
        if (navPartyChk(tlmstar,tlm) != 0) and (navPartyChk(howstar,how) != 0):
          #Parity was okay. Record the preamble start position. Skip the rest of
          #the preamble pattern checking for this channel and process next channel.
          firstSubFrame[channelNr] = index[i]
          break

    #Reject channels for which we can't find and validate preamble
    if firstSubFrame[channelNr] == '-':
      activeChnList.pop(channelNr)

  return (firstSubFrame, activeChnList)

def corrs2navbits(corrs):
  bits = np.sign(np.sum(np.reshape(corrs,(len(corrs)/20,20)),1))
  return bits

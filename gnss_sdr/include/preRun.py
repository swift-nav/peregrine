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

#from operator import itemgetter

def preRun(acqResults,settings):
  numToTrack = min(len(acqResults),settings.numberOfChannels)
  #Initialize list of tracking channel initial states
  channel = [track_chan_init_state() for i in range(numToTrack)]
  #Sort acqResults by peak strength
  acqResults_sorted = sorted(acqResults,reverse=True)
  #acqResults_sorted = sorted(acqResults,reverse=False,key=itemgetter(0))
  #Assign highest peaks from acquisition to track chan init list
  for i in range(numToTrack):
    channel[i].PRN = acqResults_sorted[i][3]
    channel[i].codePhase = acqResults_sorted[i][2]
    channel[i].acquiredFreq = acqResults_sorted[i][1]
    channel[i].status = 'T'
  return channel
  
class track_chan_init_state:
  def __init__(self):
    self.PRN          = 0
    self.acquiredFreq = 0.0
    self.codePhase    = 0
    self.status       = '-'

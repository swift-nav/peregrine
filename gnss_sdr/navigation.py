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
from initSettings import initSettings
from calculatePseudorange import calculatePseudorange
from satpos import satpos

def navigation(trackResults, settings):

  numGoodSats = 0
  for i in range(len(trackResults)):
    if (trackResults[i].status == 'T'):
      numGoodSats = numGoodSats + 1
  if (numGoodSats < 4):
    raise Exception('Too few satellites to calculate nav solution')
  #TODO : check lengths of all trackResults prompt correlations?
  if (len(trackResults[0].I_P) < 36000):
    raise Exception('Length of tracking too short to calculate nav solution')

  (subFrameStart, activeChnList) = findPreambles(trackResults,settings)

  #Pass 1500 nav bits (5 subframes), starting at a subframe preamble, 
  #to ephemeris.py to get ephemeris
  eph = [[] for i in range(32)]
  for channelNr in reversed(activeChnList):
    #Get 1500 nav bits starting at a subframe
    navBitsIndices = np.r_[subFrameStart[channelNr]:subFrameStart[channelNr]+(1500*20)]
    navBits = corrs2bits.unsigned(trackResults[channelNr].I_P[navBitsIndices])
    #Get the last parity bit of the previous subFrame 
    #subFrame's first 24 bits are XOR'd with it before transmission
    D30starIndices = np.r_[subFrameStart[channelNr]-20:subFrameStart[channelNr]]
    D30star = corrs2bits.unsigned(trackResults[channelNr].I_P[D30starIndices])
    #Extract ephemeris from the 5 subFrames
    (eph[trackResults[channelNr].PRN], TOW) = ephemeris(navBits,D30star)
    #TODO : Implement better way to determine if satellite is usable (health, accuracy)
    #Exclude satellite if for some reason ephemeris parameters weren't assigned
    #(subframe ID's 1-3 weren't assigned?)
    if (eph[trackResults[channelNr].PRN].IODC==0 and 
          eph[trackResults[channelNr].PRN].IODC_sf2==0 and 
            eph[trackResults[channelNr].PRN].IODC_sf3==0):
      activeChnList.pop(channelNr)
  #If we don't have enough satellites after rejecting those whose ephemerides failed
  #to extract properly, then we can't calculate the nav solution
  if len(activeChnList) < 4:
    raise Exception('Not enough satellites after extracting ephemerides to calculate nav solution')
  #TODO : include support for an initial position here and associated elevation mask
  #Include all satellites for first iteration of the nav solution
  satElev = np.ones(len(activeChnList))*90

  readyChnList = activeChnList[:]

  transmitTime = TOW

  msToProcessNavigation = np.int(np.floor((settings.msToProcess-max(subFrameStart))/settings.navSolPeriod))
  navSolutions = navSolutions_class(msToProcessNavigation)

  for currMeasNr in range(1):
#  for currMeasNr in range(msToProcessNavigation):
    if currMeasNr == 0: #append indexes to arrays that need them appended
      for i in range(len(activeChnList)):
        navSolutions.channel.rawP[]
    activeChnList = gThanMask(satElev)
    for i in activeChnList:
      navSolutions.channel.PRN[i].append(trackResults[i].PRN)
    navSolutions.channel.el[currMeasNr] = [[] for i in range(len(activeChnList))]
    navSolutions.channel.az[currMeasNr] = [[] for i in range(len(activeChnList))]

    #Find pseudoranges
    for channelNumber in activeChnList:
      navSolutions.channel.rawP[channelNumber][currMeasNr] = calculatePseudorange(trackResults, \
                                      [i + settings.navSolPeriod * (currMeasNr) for i in subFrameStart], \
                                      channelNumber, \
                                      settings)

    #Find satellite positions and clock corrections
    (satPositions, satClkCorr) = satpos(transmitTime, \
                                        [trackResults[i].PRN for i in activeChnList], \
                                        eph, \
                                        settings)

    #Find receiver position
    #We can only calculate solution if >= 4 satellites are found
    if len(activeChnList) > 3:
      #Calculate receiver position
      (xyzdt, \
        navSolutions.channel.el, \
        navSolutions.channel.az, \
        navSolutions.DOP[currMeasNr]) = leastSquarePos(satPositions, navSolutions.channel.rawP[np.r_[activeChnList]][currMeasNr] + satClkCorr*settings.c, settings)
      
      

  #TODO : remove below statement
  (navSolutions, eph) = (0,0)
  return (navSolutions, eph)

#TODO: update gThanMask so it accounts for elevation mask being changed during runtime, or find better way 
#to apply elevation mask than this function (preferable) - use map or filter or some such function(s)?
def gThanMask(elevationDegrees):
  settings = initSettings()
  aboveMaskIndices = []
  for i in range(len(elevationDegrees)):
    if elevationDegrees[i] > settings.elevationMask:
      aboveMaskIndices.append(i)
  return np.array(aboveMaskIndices)

class navSolutions_class:
  def __init__(self,length):
    self.channel   = navChannel_class(length)
    self.DOP       = [[] for i in range(length)]
    self.utmZone   = [[] for i in range(length)]
    self.X         = [[] for i in range(length)]
    self.Y         = [[] for i in range(length)]
    self.Z         = [[] for i in range(length)]
    self.dt        = [[] for i in range(length)]
    self.latitude  = [[] for i in range(length)]
    self.longitude = [[] for i in range(length)]
    self.height    = [[] for i in range(length)]
    self.E         = [[] for i in range(length)]
    self.N         = [[] for i in range(length)]
    self.U         = [[] for i in range(length)]

class navChannel_class:
  def __init__(self,length):
    self.PRN =  [[] for i in range(length)]
    self.rawP = [[] for i in range(length)]
    self.el =   [[] for i in range(length)]
    self.az =   [[] for i in range(length)]
    self.correctedP = [[] for i in range(length)]

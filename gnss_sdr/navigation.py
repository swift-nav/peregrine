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
from initSettings import initSettings
from calculatePseudorange import calculatePseudorange
from satpos import satpos
import swiftnav.nav_msg
import swiftnav.track
import swiftnav.pvt

def navigation(trackResults, settings):

  goodChannels = [n for n, tr in enumerate(trackResults) if tr.status == 'T']
  numGoodSats = len(goodChannels)
  if numGoodSats < 4:
    raise Exception('Too few satellites to calculate nav solution')

  for chan in goodChannels:
    if len(trackResults[chan].I_P) < 36000:
      raise Exception('Length of tracking too short to calculate nav solution')

  navMsgs = [swiftnav.nav_msg.NavMsg() for c in goodChannels]
  towIndicies = [[] for c in goodChannels]
  for n, chan in enumerate(goodChannels):
    for i, cpi in enumerate(trackResults[chan].I_P):
      tow = navMsgs[n].update(cpi)
      if tow:
        towIndicies[n] = (i, tow)

    # Ditch channels that dont give us a valid ephemeris
    if not navMsgs[n].eph_valid:
      print "Ditching chan ", (chan, trackResults[chan].PRN)
      goodChannels.pop(chan)

  print [(chan, trackResults[chan].PRN) for chan in goodChannels]
  if len(goodChannels) < 4:
    raise Exception('Not enough satellites after extracting ephemerides to calculate nav solution')

  #ms = 30000
  navSolutions = []
  for ms in range(10000, 35000, 200):
    #print "------------------------------------------"
    #print ms
    cms = []
    for chan in goodChannels:
      i, tow_e = towIndicies[chan]
      tow = tow_e + (ms - i)
      cm = swiftnav.track.ChannelMeasurement(
        trackResults[chan].PRN,
        trackResults[chan].codePhase[ms],
        trackResults[chan].codeFreq[ms],
        0,
        trackResults[chan].carrFreq[ms] - settings.IF,
        tow,
        trackResults[chan].absoluteSample[ms] / settings.samplingFreq,
        #trackResults[chan].absoluteSample[ms] / samplesPerCode,
        100
      )
      cms += [cm]
    #for cm in cms:
      #print cm

    nms = swiftnav.track.calc_navigation_measurement(ms/1000.0, cms, navMsgs)
    #for nm in nms:
      #print nm

    llh = swiftnav.pvt.foo(nms)
    print "%f,%f,%f" % (57.2957795*llh[0], 57.2957795*llh[1], llh[2])
    navSolutions += [llh]

  return navSolutions

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

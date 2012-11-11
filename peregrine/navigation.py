# Copyright (C) 2012 Swift Navigation Inc.
#
# This source is subject to the license found in the file 'LICENSE' which must
# be be distributed together with this source. All other rights reserved.
#
# THIS CODE AND INFORMATION IS PROVIDED "AS IS" WITHOUT WARRANTY OF ANY KIND,
# EITHER EXPRESSED OR IMPLIED, INCLUDING BUT NOT LIMITED TO THE IMPLIED
# WARRANTIES OF MERCHANTABILITY AND/OR FITNESS FOR A PARTICULAR PURPOSE.

import numpy as np
from initSettings import initSettings
import datetime
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

    s = swiftnav.pvt.calc_PVT(nms)
    # TODO: Fix this to properly deal with week number rollover.
    wn = 1024 + navMsgs[0].gps_week_num()
    t = datetime.datetime(1980, 1, 5) + \
        datetime.timedelta(weeks=wn) + \
        datetime.timedelta(seconds=s.tow)
    navSolutions += [(s,t)]

  return navSolutions

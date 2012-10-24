#!/usr/bin/env python
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

import argparse
from initSettings import initSettings
import getSamples
from acquisition import acquisition
import pickle
from include.preRun import preRun
from include.preRun import track_chan_init_state
from include.showChannelStatus import showChannelStatus
from datetime import datetime
from tracking import track

#Initialize constants, settings
settings = initSettings()

parser = argparse.ArgumentParser()
parser.add_argument("file", help="the sample data file to process")
parser.add_argument("-a", "--skip-acquisition", help="use previously saved acquisition results", action="store_true")
parser.add_argument("-t", "--skip-tracking", help="use previously saved tracking results", action="store_true")
parser.add_argument("-n", "--skip-navigation", help="use previously saved navigation results", action="store_true")
args = parser.parse_args()
settings.fileName = args.file

#Do acquisition
#Get 11ms of acquisition samples for fine frequency estimation
samplesPerCode = int(round(settings.samplingFreq / (settings.codeFreqBasis / settings.codeLength)))
if args.skip_acquisition:
  print "\nLoading old acquisition results ...",
  acqResults = pickle.load(open("acqResults.pickle","rb"))
  print "done"
else:
  print "\nAcquiring satellites ...",
  acqSamples = getSamples.int8(settings.fileName,11*samplesPerCode,settings.skipNumberOfBytes)
  acqResults = acquisition(acqSamples,settings)
  pickle.dump(acqResults,open("acqResults.pickle","wb"))

#Do tracking
#Find if any satellites were acquired
acqSuccessful = False
#for i in settings.acqSatelliteList:
for i in range(32-1,-1,-1):
  if acqResults[i][0] > settings.acqThreshold:
    acqSuccessful = True
  else: #if satellite wasn't found, pop it off the list
    acqResults.pop(i)
#If any satellites were acquired, set up tracking channels
if acqSuccessful:
  channel = preRun(acqResults,settings)
else:
  print "No satellites acquired, not continuing to tracking"
  pylab.show()

showChannelStatus(channel,settings)

#Track the acquired satellites
if args.skip_tracking:
  print "\nLoading old tracking results ... ",
  (trackResults,channel) = pickle.load(open("trackResults.pickle","rb"))
  print "done"
else:
  startTime = datetime.now()
  print "\nTracking started at", startTime
  (trackResults, channel) = track(channel, settings)
  pickle.dump((trackResults, channel),open("trackResults.pickle","wb"))
  print "Tracking Done. Elapsed time =", (datetime.now() - startTime)

#Do navigation
if args.skip_navigation:
  #print "\nLoading old navigation results ... ",
  #(navSolutions, eph) = pickle.load(open("navResults.pickle","rb"))
  print "done"
else:
  from navigation import navigation
  startTime = datetime.now()
  print "\nNavigation started at", startTime
  navSolutions = navigation(trackResults, settings)
  print navSolutions
  #pickle.dump(navSolutions,open("navResults.pickle","wb"))
  print "Navigation Done. Elapsed time =", (datetime.now() - startTime)

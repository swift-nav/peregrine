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

import sys
from initSettings import initSettings
import pylab
from probeData import probeData
import getSamples
from acquisition import acquisition
import pickle
from plotAcquisition import plotAcquisition
from preRun import preRun
from preRun import track_chan_init_state
from showChannelStatus import showChannelStatus
from datetime import datetime
from tracking import track
from plotTrackingLow import plotTrackingLow
from plotTrackingHigh import plotTrackingHigh
from navigation import navigation

#Add ./geofunctions and ./include to search directory for import calls
sys.path.append('./include/');
sys.path.append('./geoFunctions/');
print '\nWelcome to:   softGNSS'
print 'An open source GNSS SDR software project initiated by:'
print '              Danish GPS Center/Aalborg University'
print 'The code was improved by GNSS Laboratory/University of Colorado'
print 'and converted to Python by Colin Beighley (colinbeighley@gmail.com).'
print 'The software receiver softGNSS comes with ABSOLUTELY NO WARRANTY;'
print 'for details please read license details in the file license.txt. This'
print 'is free software  you  are  welcome  to  redistribute  it under'
print 'the terms described in the license.\n'

#Initialize constants, settings
settings = initSettings()

#Generate plot of raw data
if settings.plotSignal:
  print "Plotting data", settings.fileName
  probeFigure = probeData(settings)
  pylab.draw()

#Do acquisition
#Get 11ms of acquisition samples for fine frequency estimation
samplesPerCode = int(round(settings.samplingFreq / (settings.codeFreqBasis / settings.codeLength)))
acqSamples = getSamples.int8(settings.fileName,11*samplesPerCode,settings.skipNumberOfBytes)
if settings.skipAcquisition:
  print "\nLoading old acquisition results ...",
  acqResults = pickle.load(open("acqResults.pickle","rb"))
  print "done"
else:
  print "\nAcquiring satellites ...",
  acqResults = acquisition(acqSamples,settings)
  pickle.dump(acqResults,open("acqResults.pickle","wb"))
  print "done"
if settings.plotAcquisition:
  acqFigure = plotAcquisition(acqResults,settings)
  pylab.draw()

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
#if acqSuccessful:
#  channel = preRun(acqResults,settings)
#else:
#  print "No satellites acquired, not continuing to tracking"
#  pylab.show()
#Use Octave results instead
channel = [track_chan_init_state() for i in range(8)]
channel[0].PRN = 20; channel[0].acquiredFreq = 9547426.3420104980; channel[0].codePhase = 35228; channel[0].status = 'T';
channel[1].PRN = 17; channel[1].acquiredFreq = 9548236.7477416992; channel[1].codePhase = 4357; channel[1].status = 'T';
channel[2].PRN = 21; channel[2].acquiredFreq = 9549684.5512390137; channel[2].codePhase = 28111; channel[2].status = 'T';
channel[3].PRN = 14; channel[3].acquiredFreq = 9549921.2989807129; channel[3].codePhase = 19953; channel[3].status = 'T';
channel[4].PRN = 25; channel[4].acquiredFreq = 9545013.3361816406; channel[4].codePhase = 10460; channel[4].status = 'T';
channel[5].PRN = 5; channel[5].acquiredFreq = 9544312.1986389160; channel[5].codePhase = 11834; channel[5].status = 'T';
channel[6].PRN = 2; channel[6].acquiredFreq = 9549903.0876159668; channel[6].codePhase = 17842; channel[6].status = 'T';
channel[7].PRN = 8; channel[7].acquiredFreq = 9550831.8672180176; channel[7].codePhase = 26519; channel[7].status = 'T';
showChannelStatus(channel,settings)
pylab.draw()

#Track the signal
trackSamples = getSamples.int8(settings.fileName,settings.msToProcess,11*samplesPerCode) #11*samplesPerCode is number of samples used in acquisition
if settings.skipTracking:
  print "\nLoading old tracking results ... ",
  (trackResults,channel) = pickle.load(open("trackResults.pickle","rb"))
  print "done"
else:
  startTime = datetime.now()
  print "\nTracking started at", startTime
  (trackResults, channel) = track(trackSamples, channel, settings)
  pickle.dump((trackResults, channel),open("trackResults.pickle","wb"))
  print "Tracking Done. Elapsed time =", (datetime.now() - startTime)
if settings.plotTrackingLow:
  trackLowFigures = plotTrackingLow(trackResults,settings)
if settings.plotTrackingHigh:
  trackHighFigure = plotTrackingHigh(channel,trackResults,settings)

#Do navigation
if settings.skipNavigation:
  print "\nLoading old navigation results ... ",
  (navSolutions, eph) = pickle.load(open("navResults.pickle","rb"))
  print "done"
else:
  startTime = datetime.now()
  print "\nNavigation started at", startTime
  (navSolutions, eph) = navigation(trackResults, settings)
  pickle.dump((navSolutions, eph),open("navResults.pickle","wb"))
  print "Navigation Done. Elapsed time =", (datetime.now() - startTime)

pylab.show()

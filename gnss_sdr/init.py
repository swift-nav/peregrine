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
#Add ./geofunctions and ./include to search directory for import calls
sys.path.append('./include/');
sys.path.append('./geoFunctions/');
print '\nWelcome to:   softGNSS'
print 'An open source GNSS SDR software project initiated by:'
print '              Danish GPS Center/Aalborg University'
print 'The code was improved by GNSS Laboratory/University of Colorado.'
print 'The software receiver softGNSS comes with ABSOLUTELY NO WARRANTY;'
print 'for details please read license details in the file license.txt. This'
print 'is free software  you  are  welcome  to  redistribute  it under'
print 'the terms described in the license.\n'

#Initialize constants, settings
from initSettings import initSettings
settings = initSettings

#Generate plot of raw data
import pylab
from probeData import probeData
print "Probing data", settings.fileName
probeFigure = probeData(settings)
#pylab.draw()

#Do acquisition
import getSamples
from acquisition import acquisition
print "\nAcquiring satellites...\n"
#Get 11ms of acquisition samples for fine frequency estimation
samplesPerCode = int(round(settings.samplingFreq / (settings.codeFreqBasis / settings.codeLength)))
acqSamples = getSamples.int8(settings.fileName,11*samplesPerCode,settings.skipNumberOfBytes)
import pickle
if settings.skipAcquisition:
  acqResults = pickle.load(open("acqResults.p","rb"))
else:
  acqResults = acquisition(acqSamples,settings)
  pickle.dump(acqResults,open("acqResults.p","wb"))
from plotAcquisition import plotAcquisition
acqFigure = plotAcquisition(acqResults,settings)
print "Acquisition finished"
#pylab.draw()

#Do tracking
#Find if any satellites were acquired
acqSuccessful = False
for i in range(32): #Add PRN number to each results
    acqResults[i].append(i)
#for i in settings.acqSatelliteList:
for i in range(32-1,-1,-1):
  if acqResults[i][0] > settings.acqThreshold:
    acqSuccessful = True
  else: #if satellite wasn't found, pop it off the list
    acqResults.pop(i)
#If any satellites were acquired, set up tracking channels
#from preRun import preRun
#if acqSuccessful:
#  channel = preRun(acqResults,settings)
#else:
#  print "No satellites acquired, not continuing to tracking"
#  pylab.show()
#Use Octave results instead
from preRun import track_chan_init_state
channel = [track_chan_init_state() for i in range(8)]
channel[0].PRN = 20; channel[0].acquiredFreq = 9547426.3420104980; channel[0].codePhase = 35228; channel[0].status = 'T';
channel[1].PRN = 17; channel[1].acquiredFreq = 9548236.7477416992; channel[1].codePhase = 4357; channel[1].status = 'T';
channel[2].PRN = 21; channel[2].acquiredFreq = 9549684.5512390137; channel[2].codePhase = 28111; channel[2].status = 'T';
channel[3].PRN = 14; channel[3].acquiredFreq = 9549921.2989807129; channel[3].codePhase = 19953; channel[3].status = 'T';
channel[4].PRN = 25; channel[4].acquiredFreq = 9545013.3361816406; channel[4].codePhase = 10460; channel[4].status = 'T';
channel[5].PRN = 5; channel[5].acquiredFreq = 9544312.1986389160; channel[5].codePhase = 11834; channel[5].status = 'T';
channel[6].PRN = 2; channel[6].acquiredFreq = 9549903.0876159668; channel[6].codePhase = 17842; channel[6].status = 'T';
channel[7].PRN = 8; channel[7].acquiredFreq = 9550831.8672180176; channel[7].codePhase = 26519; channel[7].status = 'T';
#for i in range(len(channel)):
#  print "\n%d" % (i)
#  print "channel[%d].PRN = %d" % (i,channel[i].PRN)
#  print "channel[%d].acquiredFreq = %8.10f" % (i,channel[i].acquiredFreq)
#  print "channel[%d].codePhase = %f" % (i,channel[i].codePhase)
#  print "settings.IF = %d" % (settings.IF)
#  print "doppler = %d" % (settings.IF-channel[i].acquiredFreq)
from showChannelStatus import showChannelStatus
showChannelStatus(channel,settings)

#Track the signal
trackSamples = getSamples.int8(settings.fileName,settings.msToProcess,11*samplesPerCode) #11*samplesPerCode is number of samples used in acquisition
from datetime import datetime
startTime = datetime.now()
print "\nTracking started at", startTime
from tracking import track
(trackResults, channel) = track(trackSamples, channel, settings)
print "Tracking Done. Elapsed time =", (datetime.now() - startTime)

#pylab.show()

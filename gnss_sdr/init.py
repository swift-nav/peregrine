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
fig1 = probeData(settings)
pylab.draw()

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
plotAcquisition(acqResults,settings)

#pylab.show()

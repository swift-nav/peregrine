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
class initSettings:
  def __init__(self):
    self.plotSignal           = False
    self.plotAcquisition      = False
    self.plotTrackingHigh     = True
    self.plotTrackingLow      = False
    self.plotNavigation       = True

    self.plotTrackingLowInds  = range(1)
    self.plotTrackingLowCorr  = True
    self.plotTrackingLowDisc  = True
    self.plotTrackingNumPts   = 200

    self.skipAcquisition      = True
    self.skipTracking         = True
    self.skipNavigation       = False

    self.msToProcess          = 37000
    self.numberOfChannels     = 8
    self.skipNumberOfBytes    = 16368
    #dataType             = 'int8'
    self.fileName             = '../gnss_signal_records/GPSdata-DiscreteComponents-fs38_192-if9_55.bin'
    self.IF                   = 9.548e6        #Hz
    self.samplingFreq         = 38.192e6       #Hz
    self.codeFreqBasis        = 1.023e6        #Hz
    self.codeLength           = 1023
  #  samplesPerCode       = int(round(samplingFreq / (codeFreqBasis / codeLength)))
    self.acqSatelliteList     = range(0,32,1)
    self.acqSearchBand        = 14     #KHz
    self.acqThreshold         = 2.5
    self.dllDampingRatio      = 0.7
    self.dllNoiseBandwidth    = 2      #Hz
    self.dllCorrelatorSpacing = 0.5    #chips
    self.pllDampingRatio      = 0.7
    self.pllNoiseBandwidth    = 25     #Hz
    self.navSolPeriod         = 500    #ms
    self.elevationMask        = 10     #degrees
    self.useTropCorr          = True
    self.truePositionE        = float('NaN')
    self.truePositionN        = float('NaN')
    self.truePositionU        = float('NaN')
    self.c                    = 299792458
    self.startOffset          = 68.802

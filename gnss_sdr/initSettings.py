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
  msToProcess          = 8
  numberOfChannels     = 8
  skipNumberOfBytes    = 0
  #dataType             = 'int8'
  fileName             = '../gnss_signal_records/GPSdata-DiscreteComponents-fs38_192-if9_55.bin'
  IF                   = 9.548e6        #Hz
  samplingFreq         = 38.192e6       #Hz
#  fileName             = '../gnss_signal_records/GPSdata-DiscreteComponents-fs16_368-if4_092.bin'
#  IF                   = 4.092e6        #Hz
#  samplingFreq         = 16.368e6       #Hz
#  samplingPeriod       = 1/samplingFreq #seconds
  codeFreqBasis        = 1.023e6        #Hz
  codeLength           = 1023
  skipAcquisition      = True
#  skipAcquisition      = False
#  samplesPerCode       = int(round(samplingFreq / (codeFreqBasis / codeLength)))
  acqSatelliteList     = range(0,32,1)
  acqSearchBand        = 14     #KHz
  acqThreshold         = 2.5
  dllDampingRatio      = 0.7
  dllNoiseBandwidth    = 2      #Hz
  dllCorrelatorSpacing = 0.5    #chips
  pllDampingRatio      = 0.7
  pllNoiseBandwidth    = 25     #Hz
  navSolPeriod         = 500    #ms
  elevationMask        = 10     #degrees
  useTropCorr          = True
  truePositionE        = float('NaN')
  truePositionN        = float('NaN')
  truePositionU        = float('NaN')
  plotTracking         = True
  c                    = 299792458
  startOffset          = 68.802

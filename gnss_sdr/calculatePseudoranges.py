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

def calculatePseudoranges.py(trackResults,msOfTheSignal,channelList,settings):
  travelTime = np.inf*np.ones(settings.numberOfChannels)
  samplesPerCode = round(settings.samplingFreq \
                     / (settings.codeFreqBasis / settings.CodeLength))
  travelTime = [trackResults[i].absoluteSample(msOfTheSignal[i]) \
                 / samplesPerCode for i in channelList]
  minimum = np.floor(min(travelTime))
  travelTime = travelTime - minimum + settings.startOffset
  pseudoranges = tuple([i*(settings.c/1000) for i in travelTime])
  return pseudoranges

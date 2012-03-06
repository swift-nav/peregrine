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

def track(samples, channel, settings):
  #Create list of tracking channels results (correlations, freqs, etc)
  trackResults = [trackResults_class(settings) for i in range(len(channel))]
  #Initialize tracking variables
  codePeriods = settings.msToProcess
  ##DLL Variables##
  #Define early-late offset
  earlyLateSpc = settings.dllCorrelatorSpacing
  #Summation interval
  PDIcode = 0.001
  #Filter coefficient values
  from calcLoopCoef import calcLoopCoef
  (tau1code, tau2code) = calcLoopCoef(settings.dllNoiseBandwidth,settings.dllDampingRatio,0.25)
  ##PLL Variables##
  PDIcarr = 0.001
  (tau1carr,tau2carr) = calcLoopCoef(settings.pllNoiseBandwidth,settings.pllDampingRatio,0.25)
  
  #Progress bar
  from waitbar import Waitbar
  progbar = Waitbar(True)
  
  #Do tracking for each channel
  for channelNr in range(len(channel)):
    trackResults[channelNr].PRN = channel[channelNr].PRN
#    trackResults[channelNr].
  print "HI"
  return (0,2)

class trackResults_class:
  def __init__(self,settings):
    self.status = '-'
    self.absoluteSample = np.zeros(settings.msToProcess)
    self.codeFreq = np.inf*np.ones(settings.msToProcess)
    self.carrFreq = np.inf*np.ones(settings.msToProcess)
    self.I_E = np.zeros(settings.msToProcess)
    self.I_P = np.zeros(settings.msToProcess)
    self.I_L = np.zeros(settings.msToProcess)
    self.Q_E = np.zeros(settings.msToProcess)
    self.Q_P = np.zeros(settings.msToProcess)
    self.Q_L = np.zeros(settings.msToProcess)
    self.dllDiscr     = np.inf*np.ones(settings.msToProcess);
    self.dllDiscrFilt = np.inf*np.ones(settings.msToProcess);
    self.pllDiscr     = np.inf*np.ones(settings.msToProcess);
    self.pllDiscrFilt = np.inf*np.ones(settings.msToProcess);

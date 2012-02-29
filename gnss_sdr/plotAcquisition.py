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
import matplotlib.pyplot as plt

def plotAcquisition(acqResults,settings):
  acqResults = np.array(acqResults)
  plt.figure(101)
  plt.hold(True)
  barplot = []
  for i in range(32):
    if (acqResults[i][0] > settings.acqThreshold):
      barplot.append(plt.bar(i,acqResults[i][0],color='g'))
      there = i
    else:
      barplot.append(plt.bar(i,acqResults[i][0],color='r'))
      nthere = i
  plt.legend((barplot[there],barplot[nthere]),('Green - SV acq\'d', 'Red - SV not acq\'d'))
  plt.axis([0,32,0,max(np.array(acqResults).T[0])*1.2])
        
  plt.title('Acquisition results')
  plt.xlabel('PRN number')
  plt.ylabel('Acquisition metric')
   
  return barplot

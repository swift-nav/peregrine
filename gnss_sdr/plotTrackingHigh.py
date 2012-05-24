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

def plotTrackingHigh(channel, trackResults, settings):
  fig = plt.figure()
  fig.clf()
  if (settings.plotTrackingNumPts > len(trackResults[0].pllDiscr)):
    x_pts = [i*0.001 for i in range(len(trackResults[0].pllDiscr))] 
  else:
    x_pts = [i*0.001 for i in range(settings.plotTrackingNumPts)] 
  colors = [(0,0,0),\
            (0,0,1),\
            (0,1,0),\
            (0,1,1),\
            (1,0,0),\
            (1,0,1),\
            (1,1,0),\
            (0,0,0.5),\
            (0,0.5,0),\
            (0,0.5,0.5),\
            (0.5,0,0),\
            (0.5,0,0.5),\
            (0.5,0.5,0),\
            (0.5,0.5,0.5)]
  plt.title("Prompt correlation magnitude of each channel")
  plt.xlabel("Time")
  plt.hold(True)
  
  for channelNr in range(len(trackResults)):
    plt.plot(x_pts,\
             np.sqrt(np.square(trackResults[channelNr].I_P[0:len(x_pts)])\
               + np.square(trackResults[channelNr].Q_P[0:len(x_pts)])),\
             color=colors[channelNr], label=("PRN %2d" % (channel[channelNr].PRN)))
  plt.legend()
  plt.hold(False)

  return fig

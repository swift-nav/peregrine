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

def plotTracking(channelList, trackResults, settings):
  fig = [[]]
#  for channelNr in channelList:
  for channelNr in range(1):
    fig[channelNr].append(plt.figure(channelNr + 200))
    fig[channelNr][0].clf()
    plt.figtext(0.02,0.95,"Channel %d (PRN %d) Tracking Results : I/Q Diagram, PLL Disc, and DLL Disc" % (channelNr,trackResults[channelNr].PRN))
    fig[channelNr][0].add_subplot(3,2,1);
    plt.plot(trackResults[channelNr].I_P, trackResults[channelNr].Q_P,'.')

    fig[channelNr].append(plt.figure(channelNr + 250))
    fig[channelNr][1].clf()
    plt.figtext(0.02,0.95,"Channel %d (PRN %d) Tracking Results : Correlations" % (channelNr,trackResults[channelNr].PRN))
    fig[channelNr][1].add_subplot(2,1,1);

  return fig

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

def plotTrackingLow(trackResults, settings):
  fig = []
  if (settings.plotTrackingNumPts > len(trackResults[0].I_P)):
    x_pts = [i*0.001 for i in range(len(trackResults[0].I_P))]
  else:
    x_pts = [i*0.001 for i in range(settings.plotTrackingNumPts)]

  for channelNr in settings.plotTrackingLowInds:
    fig.append([])
    if settings.plotTrackingLowDisc:
      fig[channelNr].append(plt.figure(channelNr + 200))
      fig[channelNr][-1].clf()
      plt.figtext(0.02,0.95,"Channel %d (PRN %d) Tracking Results : I/Q Diagram, PLL Disc, and DLL Disc" % (channelNr,trackResults[channelNr].PRN))

      fig[channelNr][-1].add_subplot(3,2,1)
      plt.plot(trackResults[channelNr].I_P[0:len(x_pts)], trackResults[channelNr].Q_P[0:len(x_pts)],'.')
      plt.ylabel('IQ Diagram\nQuadrature')
      plt.xlabel('In-phase')

      fig[channelNr][-1].add_subplot(3,2,3)
      plt.plot(x_pts,trackResults[channelNr].pllDiscr[0:len(x_pts)],'b.')
      plt.ylabel('PLL Discriminant')
      plt.xlabel('Time')

      fig[channelNr][-1].add_subplot(3,2,4)
      plt.plot(x_pts,trackResults[channelNr].pllDiscrFilt[0:len(x_pts)],'r.')
      plt.ylabel('Filtered PLL Discriminant')
      plt.xlabel('Time')

      fig[channelNr][-1].add_subplot(3,2,5)
      plt.plot(x_pts,trackResults[channelNr].dllDiscr[0:len(x_pts)],'b.')
      plt.ylabel('DLL Discriminant')
      plt.xlabel('Time')

      fig[channelNr][-1].add_subplot(3,2,6)
      plt.plot(x_pts,trackResults[channelNr].dllDiscrFilt[0:len(x_pts)],'r.')
      plt.ylabel('Filtered DLL Discriminant')
      plt.xlabel('Time')

    if settings.plotTrackingLowCorr:
      fig[channelNr].append(plt.figure(channelNr + 250))
      fig[channelNr][-1].clf()
      plt.figtext(0.02,0.95,"Channel %d (PRN %d) Tracking Results : Correlations" % (channelNr,trackResults[channelNr].PRN))

      fig[channelNr][-1].add_subplot(2,1,1);
      plt.plot(x_pts,trackResults[channelNr].I_P[0:len(x_pts)],'b')
      plt.ylabel('IP Correlation')
      plt.xlabel('Time')

      fig[channelNr][-1].add_subplot(2,1,2);
      plt.hold(True)
      plt.plot(x_pts,np.sqrt(np.square(trackResults[channelNr].I_E[0:len(x_pts)])\
                           + np.square(trackResults[channelNr].Q_E[0:len(x_pts)])),'y')
      plt.plot(x_pts,np.sqrt(np.square(trackResults[channelNr].I_P[0:len(x_pts)])\
                           + np.square(trackResults[channelNr].Q_P[0:len(x_pts)])),'b')
      plt.plot(x_pts,np.sqrt(np.square(trackResults[channelNr].I_L[0:len(x_pts)])\
                           + np.square(trackResults[channelNr].Q_L[0:len(x_pts)])),'r')
      plt.ylabel('Early / Prompt / Late Power')
      plt.xlabel('Time')
      plt.hold(False)

  return fig

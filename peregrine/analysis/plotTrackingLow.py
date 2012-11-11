#!/usr/bin/env python
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
sys.path.append("..")

import initSettings
import argparse
import numpy as np
import pylab
import pickle

def plotTrackingLow(trackResults, settings):
  fig = []
  if (settings.plotTrackingNumPts > len(trackResults[0].I_P)):
    x_pts = [i*0.001 for i in range(len(trackResults[0].I_P))]
  else:
    x_pts = [i*0.001 for i in range(settings.plotTrackingNumPts)]

  for channelNr in settings.plotTrackingLowInds:
    fig.append([])
    if settings.plotTrackingLowDisc:
      fig[channelNr].append(pylab.figure())
      fig[channelNr][-1].clf()
      pylab.figtext(0.02,0.95,"Channel %d (PRN %d) Tracking Results : I/Q Diagram, PLL Disc, and DLL Disc" % (channelNr,trackResults[channelNr].PRN))

      fig[channelNr][-1].add_subplot(3,2,1)
      pylab.plot(trackResults[channelNr].I_P[0:len(x_pts)], trackResults[channelNr].Q_P[0:len(x_pts)],'.')
      pylab.ylabel('IQ Diagram\nQuadrature')
      pylab.xlabel('In-phase')

      fig[channelNr][-1].add_subplot(3,2,3)
      pylab.plot(x_pts,trackResults[channelNr].pllDiscr[0:len(x_pts)],'b.')
      pylab.ylabel('PLL Discriminant')
      pylab.xlabel('Time')

      fig[channelNr][-1].add_subplot(3,2,4)
      pylab.plot(x_pts,trackResults[channelNr].pllDiscrFilt[0:len(x_pts)],'r.')
      pylab.ylabel('Filtered PLL Discriminant')
      pylab.xlabel('Time')

      fig[channelNr][-1].add_subplot(3,2,5)
      pylab.plot(x_pts,trackResults[channelNr].dllDiscr[0:len(x_pts)],'b.')
      pylab.ylabel('DLL Discriminant')
      pylab.xlabel('Time')

      fig[channelNr][-1].add_subplot(3,2,6)
      pylab.plot(x_pts,trackResults[channelNr].dllDiscrFilt[0:len(x_pts)],'r.')
      pylab.ylabel('Filtered DLL Discriminant')
      pylab.xlabel('Time')

    if settings.plotTrackingLowCorr:
      fig[channelNr].append(pylab.figure())
      fig[channelNr][-1].clf()
      pylab.figtext(0.02,0.95,"Channel %d (PRN %d) Tracking Results : Correlations" % (channelNr,trackResults[channelNr].PRN))

      fig[channelNr][-1].add_subplot(2,1,1);
      pylab.plot(x_pts,trackResults[channelNr].I_P[0:len(x_pts)],'b')
      pylab.ylabel('IP Correlation')
      pylab.xlabel('Time')

      fig[channelNr][-1].add_subplot(2,1,2);
      pylab.hold(True)
      pylab.plot(x_pts,np.sqrt(np.square(trackResults[channelNr].I_E[0:len(x_pts)])\
                           + np.square(trackResults[channelNr].Q_E[0:len(x_pts)])),'y')
      pylab.plot(x_pts,np.sqrt(np.square(trackResults[channelNr].I_P[0:len(x_pts)])\
                           + np.square(trackResults[channelNr].Q_P[0:len(x_pts)])),'b')
      pylab.plot(x_pts,np.sqrt(np.square(trackResults[channelNr].I_L[0:len(x_pts)])\
                           + np.square(trackResults[channelNr].Q_L[0:len(x_pts)])),'r')
      pylab.ylabel('Early / Prompt / Late Power')
      pylab.xlabel('Time')
      pylab.hold(False)

  return fig

if __name__ == "__main__":
  settings = initSettings.initSettings()
  parser = argparse.ArgumentParser()
  parser.add_argument("file", help="the tracking results file to analyse")
  args = parser.parse_args()
  settings.fileName = args.file
  with open(settings.fileName, "rb") as f:
    trackResults, channel = pickle.load(f)
    fig = plotTrackingLow(trackResults, settings)
  pylab.show()

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

def plotAcquisition(acqResults,settings):
  acqResults = np.array(acqResults)
  pylab.figure()
  pylab.hold(True)
  barplot = []
  sat_not_there = None
  sat_there = None
  for i in range(32):
    if (acqResults[i][0] > settings.acqThreshold):
      barplot.append(pylab.bar(i,acqResults[i][0],color='g'))
      sat_there = i
    else:
      barplot.append(pylab.bar(i,acqResults[i][0],color='r'))
      sat_not_there = i
  if not sat_there is None and not sat_not_there is None:
    pylab.legend((barplot[sat_there],barplot[sat_not_there]),('Green - SV acq\'d', 'Red - SV not acq\'d'))
  pylab.axis([0,32,0,max(np.array(acqResults).T[0])*1.2])

  pylab.title('Acquisition results')
  pylab.xlabel('PRN number')
  pylab.ylabel('Acquisition metric')

  return barplot

if __name__ == "__main__":
  settings = initSettings.initSettings()
  parser = argparse.ArgumentParser()
  parser.add_argument("file", help="the acquisition results file to analyse")
  args = parser.parse_args()
  settings.fileName = args.file
  with open(settings.fileName, "rb") as f:
    acqResults = pickle.load(f)
    fig = plotAcquisition(acqResults, settings)
  pylab.show()

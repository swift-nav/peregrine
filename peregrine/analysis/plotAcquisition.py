#!/usr/bin/env python

# Copyright (C) 2012 Swift Navigation Inc.
#
# This source is subject to the license found in the file 'LICENSE' which must
# be be distributed together with this source. All other rights reserved.
#
# THIS CODE AND INFORMATION IS PROVIDED "AS IS" WITHOUT WARRANTY OF ANY KIND,
# EITHER EXPRESSED OR IMPLIED, INCLUDING BUT NOT LIMITED TO THE IMPLIED
# WARRANTIES OF MERCHANTABILITY AND/OR FITNESS FOR A PARTICULAR PURPOSE.

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

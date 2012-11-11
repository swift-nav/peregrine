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

def plotTrackingHigh(trackResults, settings):
  fig = pylab.figure()
  fig.clf()
  if (settings.plotTrackingNumPts > len(trackResults[0].I_P)):
    x_pts = [i*0.001 for i in range(len(trackResults[0].I_P))]
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
  pylab.title("Prompt correlation magnitude of each channel")
  pylab.xlabel("Time")
  pylab.hold(True)

  for channelNr in range(len(trackResults)):
    pylab.plot(x_pts,\
             np.sqrt(np.square(trackResults[channelNr].I_P[0:len(x_pts)])\
               + np.square(trackResults[channelNr].Q_P[0:len(x_pts)])),\
             color=colors[channelNr], label=("PRN %2d" % (trackResults[channelNr].PRN)))
  pylab.legend()
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
    fig = plotTrackingHigh(trackResults, settings)
  pylab.show()

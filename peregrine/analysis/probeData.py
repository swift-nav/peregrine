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
import pylab
import math
import numpy
import matplotlib
import get_samples

def probeData(settings):
  samplesPerCode = int(round(settings.samplingFreq / (settings.codeFreqBasis / settings.codeLength)))

  samples = get_samples.int8(settings.fileName,10*samplesPerCode,settings.skipNumberOfBytes)

  #Initialize figure
  fig = pylab.figure()
  pylab.clf()

  #X axis
  timeScale = [x*(1/settings.samplingFreq) for x in \
               range(0,int(round((5e-3 + 1/settings.samplingFreq)*settings.samplingFreq)))]
  #Time domain plot
  pylab.subplot(2,2,1)
  plot_max = int(round(samplesPerCode/50))
  pylab.plot([1000*i for i in timeScale[0:plot_max]],samples[0:plot_max])
  pylab.title('Time domain plot')
  pylab.xlabel('Time (ms)')
  pylab.ylabel('Amplitude')

  #Frequency domain plot
  (Pxx,freqs) = matplotlib.mlab.psd(x = samples-numpy.mean(samples),\
                                                    noverlap = 1024,\
                                                        NFFT = 2048,\
                                     Fs = settings.samplingFreq/1e6)
  pylab.subplot(2,2,2)
  pylab.semilogy(freqs,Pxx)
  pylab.title('Frequency Domain Plot')
  pylab.xlabel('Frequency (MHz)')
  pylab.ylabel('Magnitude')

  #Histogram
  pylab.subplot(2,2,3)
  xticks = pylab.unique(samples)
  pylab.hist(samples,len(xticks))
  axis = pylab.axis()
  pylab.axis([min(samples),max(samples),axis[2],axis[3]])
  xticks = pylab.unique(pylab.round_(xticks))
  pylab.xticks(xticks)
  pylab.title('Histogram');

  return fig

if __name__ == "__main__":
  settings = initSettings.initSettings()
  parser = argparse.ArgumentParser()
  parser.add_argument("file", help="the sample data file to analyse")
  args = parser.parse_args()
  settings.fileName = args.file
  fig = probeData(settings)
  pylab.show()

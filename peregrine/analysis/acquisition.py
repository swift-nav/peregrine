#!/usr/bin/env python

# Copyright (C) 2012 Swift Navigation Inc.
#
# This source is subject to the license found in the file 'LICENSE' which must
# be be distributed together with this source. All other rights reserved.
#
# THIS CODE AND INFORMATION IS PROVIDED "AS IS" WITHOUT WARRANTY OF ANY KIND,
# EITHER EXPRESSED OR IMPLIED, INCLUDING BUT NOT LIMITED TO THE IMPLIED
# WARRANTIES OF MERCHANTABILITY AND/OR FITNESS FOR A PARTICULAR PURPOSE.

import numpy as np
import matplotlib.pyplot as plt
from operator import attrgetter

from peregrine.acquisition import AcquisitionResult, DEFAULT_THRESHOLD

def snr_bars(acq_results, threshold=DEFAULT_THRESHOLD, ax=None, show_missing=True):
  """
  Display the acquisition Signal to Noise Ratios as a bar chart.

  """
  if ax is None:
    fig = plt.figure()
    fig.set_size_inches(10, 4)
    ax = fig.add_subplot(111)

  if show_missing:
    prns = [r.prn for r in acq_results]
    missing = [prn for prn in range(31) if not prn in prns]
    acq_results = acq_results[:] + \
                  [AcquisitionResult(prn, 0, 0, 0, 0) for prn in missing]

  acq_results.sort(key=attrgetter('prn'))

  for n, result in enumerate(acq_results):
    if (result.status == 'A'):
      colour = '#FFAAAA'
    else:
      colour = '0.8'
    ax.bar(n-0.5, result.snr, color=colour, width=1)

  ax.plot([-0.5, len(acq_results)-0.5], [threshold, threshold],
          linestyle='dashed', color='black')
  ax.set_xticks(range(len(acq_results)))
  ax.set_xticklabels(['%02d' % (r.prn+1) for r in acq_results])

  ax.set_title('Acquisition results')
  ax.text(0.01, 0.97, 'threshold = %.1f' % threshold,
     horizontalalignment='left',
     verticalalignment='top',
     transform = ax.transAxes)
  ax.set_ylabel('Acquisition metric')

  yticks = ax.get_yticks()
  dist = np.abs(yticks - threshold).min()
  if dist >= 0.25*(yticks[1] - yticks[0]):
    ax.set_yticks(np.append(yticks, threshold))

  ax.set_xbound(-0.5, len(acq_results)-0.5)
  ax.set_xlabel('PRN')

  return ax

def peak_plot(ar, freqs, samples_per_code, code_length=1023.0):
  samples_per_chip = samples_per_code / code_length

  fig = plt.figure()
  fig.set_size_inches(10, 10)
  ax1 = fig.add_subplot(221)
  ax2 = fig.add_subplot(222)
  ax3 = fig.add_subplot(223)
  ax4 = fig.add_subplot(224)

  peak = np.unravel_index(ar.argmax(), ar.shape)
  ar_detail = ar[peak[0]-5:peak[0]+5, peak[1]-50:peak[1]+50]

  code_phases = np.arange(samples_per_code) / samples_per_chip

  ax1.plot(code_phases, ar[peak[0],:])
  ax1.set_title("Code phase cross-section")
  ax1.set_xlabel("Code phase (chips)")
  ax1.set_ylabel("Correlation magnitude")
  ax1.set_xbound(0, code_length)
  ax1.set_xticks([0, code_phases[peak[1]], code_length])
  ax1.set_xticklabels(['0', code_phases[peak[1]], '%.0f' % code_length])

  ax2.plot(freqs, ar[:,peak[1]])
  ax2.set_title("Carrier frequency cross-section")
  ax2.set_xlabel("Doppler shift (Hz)")
  ax2.set_ylabel("Correlation magnitude")
  ax2.set_xbound(freqs[0], freqs[-1])
  ax2.set_xticks([freqs[0], freqs[peak[0]], freqs[-1]])

  ax3.plot(code_phases[peak[1]-50:peak[1]+50],
           ar[peak[0],peak[1]-50:peak[1]+50])
  ax3.set_title("Code phase cross-section detail")
  ax3.set_xlabel("Code phase (chips)")
  ax3.set_ylabel("Correlation magnitude")
  ax3.set_xbound(code_phases[peak[1]-50], code_phases[peak[1]+50])

  ax4.imshow(ar_detail, aspect='auto', cmap=plt.cm.coolwarm,
             extent=(code_phases[peak[1]-50],
                     code_phases[peak[1]+50],
                     freqs[peak[0]-5],
                     freqs[peak[0]+5]),
             interpolation='nearest')
  ax4.set_title("Peak detail")
  ax4.set_xlabel("Code phase (chips)")
  ax4.set_ylabel("Doppler shift (Hz)")

  fig.tight_layout()

def acq_plot_3d(ar, freqs, samples_per_code, code_length=1023.0):
  from mpl_toolkits.mplot3d import Axes3D

  samples_per_chip = samples_per_code / code_length

  fig = plt.figure()
  ax = fig.add_subplot(111, projection='3d')

  code_phases = np.arange(samples_per_code) / samples_per_chip
  X, Y = np.meshgrid(code_phases, freqs)

  ax.plot_surface(X[:], Y[:], ar[:], cmap=plt.cm.coolwarm, linewidth=0)
  ax.set_title("Acquisition")
  ax.set_xlabel("Code phase (chips)")
  ax.set_xbound(0, code_length)
  ax.set_ylabel("Doppler shift (Hz)")
  ax.set_ybound(freqs[0], freqs[-1])
  ax.set_zlabel("Correlation magnitude")

  fig.tight_layout()

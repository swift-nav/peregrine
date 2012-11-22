#!/usr/bin/env python

# Copyright (C) 2012 Swift Navigation Inc.
#
# This source is subject to the license found in the file 'LICENSE' which must
# be be distributed together with this source. All other rights reserved.
#
# THIS CODE AND INFORMATION IS PROVIDED "AS IS" WITHOUT WARRANTY OF ANY KIND,
# EITHER EXPRESSED OR IMPLIED, INCLUDING BUT NOT LIMITED TO THE IMPLIED
# WARRANTIES OF MERCHANTABILITY AND/OR FITNESS FOR A PARTICULAR PURPOSE.

"""Functions for analysing and plotting acquisition results."""

import numpy as np
import matplotlib.pyplot as plt
from operator import attrgetter

from peregrine.acquisition import AcquisitionResult, DEFAULT_THRESHOLD

__all__ = ['acq_table', 'snr_bars', 'peak_plot', 'acq_plot_3d']

def acq_table(acq_results, show_all=False):
  """
  Print a table of acquisition results.

  Parameters
  ----------
  acq_results : [:class:`peregrine.acquisition.AcquisitionResult`]
    List of :class:`peregrine.acquisition.AcquisitionResult` objects.
  show_all : bool, optional
    If `True` then even satellites which have not been acquired will be shown
    in the table.

  """
  for ar in acq_results:
    if ar.status == 'A':
      if show_all:
        print '*',
      print ar
    elif show_all:
      print ' ',
      print ar


def snr_bars(acq_results,
             threshold=DEFAULT_THRESHOLD, ax=None, show_missing=True):
  """
  Display the acquisition Signal to Noise Ratios as a bar chart.

  This function is useful for visualising the output of
  :meth:`peregrine.acquisition.Acquisition.acquisition` or saved acquisition
  results files loaded with :func:`peregrine.acquisition.load_acq_results`.

  Parameters
  ----------
  acq_results : [:class:`peregrine.acquisition.AcquisitionResult`]
    List of :class:`peregrine.acquisition.AcquisitionResult` objects to plot
    bars for. If the `status` field of the
    :class:`peregrine.acquisition.AcquisitionResult` object is ``'A'``, i.e.
    the satellite has been acquired, then the bar will be highlighted.
  theshold : {float, `None`}, optional
    If not `None` then an acquisition theshold of this value will be indicated
    on the plot. Defaults to the value of
    :attr:`peregrine.acquisition.DEFAULT_THRESHOLD`.
  ax : :class:`matplotlib.axes.Axes`, optional
    If `ax` is not `None` then the bar chart will be plotted on the supplied
    :class:`matplotlib.axes.Axes` object rather than as a new figure.
  show_missing : bool, optional
    If `True` then the bar chart will show empty spaces for all PRNs not
    included in `acq_results`, otherwise only the PRNs in `acq_results` will be
    plotted.

  Returns
  -------
  out : :class:`matplotlib.axes.Axes`
    The `Axes` object that the bar chart was drawn to.

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

  ax.set_xticks(range(len(acq_results)))
  ax.set_xticklabels(['%02d' % (r.prn+1) for r in acq_results])

  ax.set_title('Acquisition results')
  ax.set_ylabel('Acquisition metric')

  if threshold is not None:
    ax.plot([-0.5, len(acq_results)-0.5], [threshold, threshold],
            linestyle='dashed', color='black')

    ax.text(0.01, 0.97, 'threshold = %.1f' % threshold,
       horizontalalignment='left',
       verticalalignment='top',
       transform = ax.transAxes)

    yticks = ax.get_yticks()
    dist = np.abs(yticks - threshold).min()
    if dist >= 0.25*(yticks[1] - yticks[0]):
      ax.set_yticks(np.append(yticks, threshold))

  ax.set_xbound(-0.5, len(acq_results)-0.5)
  ax.set_xlabel('PRN')

  return ax

def peak_plot(ar, freqs, samples_per_code, code_length=1023.0):
  """
  Visualise the peak in a table of acquisition correlation powers.

  Display, in various ways, the peak in a 2D array of acquisition correlation
  powers against code phase and Doppler shift.

  This is useful for visualising the output of
  :meth:`peregrine.acquisition.Acquisition.acquire`.

  Parameters
  ----------
  ar : :class:`numpy.ndarray`, shape(len(`freqs`), `samples_per_code`)
    2D array containing correlation powers at different frequencies and code
    phases. Code phase axis is in samples from zero to `samples_per_code`.
  freqs : iterable
    List of frequencies mapping the results frequency index to a value in Hz.
  samples_per_code : float
    The number of samples corresponding to one code length.
  code_length : int, optional
    The number of chips in the chipping code. Defaults to the GPS C/A code
    value of 1023.

  """
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

  ax1.plot(code_phases, ar[peak[0],:], color='black')
  ax1.set_title("Code phase cross-section")
  ax1.set_xlabel("Code phase (chips)")
  ax1.set_ylabel("Correlation magnitude")
  ax1.set_xbound(0, code_length)
  ax1.set_xticks([0, code_phases[peak[1]], code_length])
  ax1.set_xticklabels(['0', code_phases[peak[1]], '%.0f' % code_length])

  ax2.plot(freqs, ar[:,peak[1]], color='black')
  ax2.set_title("Carrier frequency cross-section")
  ax2.set_xlabel("Doppler shift (Hz)")
  ax2.set_ylabel("Correlation magnitude")
  ax2.set_xbound(freqs[0], freqs[-1])
  ax2.set_xticks([freqs[0], freqs[peak[0]], freqs[-1]])

  ax3.plot(code_phases[peak[1]-50:peak[1]+50],
           ar[peak[0],peak[1]-50:peak[1]+50], color='black')
  ax3.set_title("Code phase cross-section detail")
  ax3.set_xlabel("Code phase (chips)")
  ax3.set_ylabel("Correlation magnitude")
  ax3.set_xbound(code_phases[peak[1]-50], code_phases[peak[1]+50])

  ax4.imshow(ar_detail, aspect='auto', cmap=plt.cm.RdYlBu_r,
             extent=(code_phases[peak[1]-50],
                     code_phases[peak[1]+50],
                     freqs[peak[0]-5],
                     freqs[peak[0]+5]),
             interpolation='bilinear')
  ax4.set_title("Peak detail")
  ax4.set_xlabel("Code phase (chips)")
  ax4.set_ylabel("Doppler shift (Hz)")

  fig.tight_layout()

def acq_plot_3d(ar, freqs, samples_per_code, code_length=1023.0):
  """
  Display a 3D plot of correlation power against code phase and Doppler shift.

  This is useful for visualising the output of
  :meth:`peregrine.acquisition.Acquisition.acquire`.

  Parameters
  ----------
  ar : :class:`numpy.ndarray`, shape(len(`freqs`), `samples_per_code`)
    2D array containing correlation powers at different frequencies and code
    phases. Code phase axis is in samples from zero to `samples_per_code`.
  freqs : iterable
    List of frequencies mapping the results frequency index to a value in Hz.
  samples_per_code : float
    The number of samples corresponding to one code length.
  code_length : int, optional
    The number of chips in the chipping code. Defaults to the GPS C/A code
    value of 1023.

  """
  from mpl_toolkits.mplot3d import Axes3D

  samples_per_chip = samples_per_code / code_length

  fig = plt.figure()
  ax = fig.add_subplot(111, projection='3d')

  code_phases = np.arange(samples_per_code) / samples_per_chip
  X, Y = np.meshgrid(code_phases, freqs)

  ax.plot_surface(X[:], Y[:], ar[:], cmap=plt.cm.RdYlBu_r, linewidth=0)
  ax.set_title("Acquisition")
  ax.set_xlabel("Code phase (chips)")
  ax.set_xbound(0, code_length)
  ax.set_ylabel("Doppler shift (Hz)")
  ax.set_ybound(freqs[0], freqs[-1])
  ax.set_zlabel("Correlation magnitude")

  fig.tight_layout()


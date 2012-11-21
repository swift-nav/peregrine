#!/usr/bin/env python

# Copyright (C) 2012 Swift Navigation Inc.
#
# This source is subject to the license found in the file 'LICENSE' which must
# be be distributed together with this source. All other rights reserved.
#
# THIS CODE AND INFORMATION IS PROVIDED "AS IS" WITHOUT WARRANTY OF ANY KIND,
# EITHER EXPRESSED OR IMPLIED, INCLUDING BUT NOT LIMITED TO THE IMPLIED
# WARRANTIES OF MERCHANTABILITY AND/OR FITNESS FOR A PARTICULAR PURPOSE.

"""Functions for analysing and plotting sample data."""

import numpy as np
import matplotlib
import matplotlib.pyplot as plt
import matplotlib.mlab as mlab

__all__ = ['hist', 'psd', 'summary']

# Globally change the matplotlib font settings,
# someone is going to complain about this eventually...
matplotlib.rc('mathtext', fontset='stixsans')

def hist(samples, ax=None, value_range=None, bin_width=1.0):
  """
  Plot a histogram of the sample values.

  Parameters
  ----------
  samples : array_like
    The sample data to be analysed.
  ax : :class:`matplotlib.axes.Axes`, optional
    If `ax` is not `None` then the histogram will be plotted on the supplied
    :class:`matplotlib.axes.Axes` object rather than as a new figure.
  value_range : (int, int), optional
    Tuple (`min`, `max`) specifying the range of possible values in the input
    data, this defines the range of the histogram. If `value_range` is `None`
    then (min(`samples`), max(`samples`) is used.
  bin_width : float, optional
    Together with `value_range` this determines how the histogram is binned.
    Bins are sized closest to `bin_width` such that an integer number of bins
    spans `value_range`. The default value of ``1`` is suitable for integer
    data.

  Returns
  -------
  out : :class:`matplotlib.axes.Axes`
    The `Axes` object that the histogram was drawn to.

  """
  if ax is None:
    fig = plt.figure()
    ax = fig.add_subplot(111)

  if value_range is not None:
    min_val, max_val = value_range
  else:
    max_val = np.max(samples)
    min_val = np.min(samples)

  n_bins =  1 + np.round(float(max_val - min_val) / bin_width)
  bins = np.linspace(min_val-bin_width/2.0, max_val+bin_width/2.0, n_bins+1)

  ticks = np.linspace(min_val, max_val, n_bins)

  ax.hist(samples, bins=bins, color='0.9')

  ax.set_title('Histogram')
  ax.set_xlabel('Sample value')
  ax.set_xticks(ticks)
  ax.set_xbound(min_val-bin_width, max_val+bin_width)
  ax.set_ylabel('Count')
  y_min, y_max = ax.get_ybound()
  ax.set_ybound(0, y_max*1.1)
  ax.ticklabel_format(style='sci', scilimits=(0,0), axis='y')

  return ax

def psd(samples, sampling_freq=None, ax=None):
  """
  Plot the Power Spectral Density (PSD) of the sample data.

  Parameters
  ----------
  samples : array_like
    The sample data to be analysed.
  sampling_freq : float, optional
    The sampling frequency of the data. If this is specified then the plot
    abscissa labeled with values in Hz. If `sampling_freq` is `None` then the
    plot will be labeled in units of the sampling frequency.
  ax : :class:`matplotlib.axes.Axes`, optional
    If `ax` is not `None` then the histogram will be plotted on the supplied
    :class:`matplotlib.axes.Axes` object rather than as a new figure.

  Returns
  -------
  out : :class:`matplotlib.axes.Axes`
    The `Axes` object that the PSD plot was drawn to.

  """
  if ax is None:
    fig = plt.figure()
    ax = fig.add_subplot(111)

  ax.set_title('Power Spectral Density')
  ax.set_ylabel('Power Spectral Density ($\mathrm{Hz}^{-1}$)')

  if sampling_freq is None:
    ax.set_xlabel('Frequency (Hz/$f_s$)')
    sampling_freq = 1.0
  else:
    ax.ticklabel_format(style='sci', scilimits=(0,0), axis='x')
    ax.set_xlabel('Frequency (Hz)')

  Pxx, freqs = mlab.psd(samples,
                        Fs=sampling_freq,
                        detrend=mlab.detrend_mean,
                        NFFT=2048,
                        noverlap=1024)

  ax.semilogy(freqs, Pxx, color='black')
  ax.set_xbound(0, sampling_freq/2.0)

  return ax

def summary(samples, sampling_freq=None):
  """
  Plot a summary sample data analysis, including the other plots as subplots.

  Specifically it plots:
   * The Power Spectral Density plot given by :func:`psd`.
   * The histogram given by :func:`hist`.

  Parameters
  ----------
  samples : array_like
    The sample data to be analysed.
  sampling_freq : float, optional
    The sampling frequency of the data. If `sampling_freq` is `None` then the
    plots will be labeled in units of the sampling frequency.

  """
  fig = plt.figure()
  ax1 = fig.add_subplot(121)
  ax2 = fig.add_subplot(122)

  hist(samples, ax=ax1)
  psd(samples, sampling_freq, ax=ax2)

  fig.set_size_inches(10, 4, forward=True)
  fig.tight_layout()

def main():
  import argparse
  import peregrine.samples

  parser = argparse.ArgumentParser()
  parser.add_argument("file", help="the sample data file to analyse")
  parser.add_argument("-n", "--num-samples", type=int, default=65536,
                      help="number of samples to use, defaults to 65536")
  args = parser.parse_args()

  samples = peregrine.samples.load_samples(args.file, args.num_samples)
  summary(samples)

  plt.show()

if __name__ == "__main__":
  main()

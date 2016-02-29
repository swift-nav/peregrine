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

import logging
logger = logging.getLogger(__name__)

ANALYSIS_MAX_LEN = 2000000

def hist(samples, ax=None, value_range=None, bin_width=1.0, max_len=ANALYSIS_MAX_LEN):
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
  max_len: float, optional
    Maximum number of samples to analyse. If `len(samples)` is greater than
    `max_len` then `samples` will first be truncated to `max_len` samples. If
    `None` then the whole array will be used.

  Returns
  -------
  out : :class:`matplotlib.axes.Axes`
    The `Axes` object that the histogram was drawn to.

  """
  if max_len is not None and len(samples) > max_len:
    logger.debug("Truncating to %d samples." % max_len)
    samples = samples[:max_len]

  if ax is None:
    fig = plt.figure()
    ax = fig.add_subplot(111)

  if value_range is not None:
    min_val, max_val = value_range
  else:
    max_val = np.max(samples)
    min_val = np.min(samples)

  n_bins = 1 + np.round(float(max_val) - float(min_val) / bin_width)
  bins = np.linspace(min_val - bin_width / 2.0, max_val + bin_width / 2.0, n_bins + 1)

  ticks = np.linspace(min_val, max_val, n_bins)

  ax.hist(samples, bins=bins, color='0.9')

  ax.set_title('Histogram')
  ax.set_xlabel('Sample value')
  if len(ticks) < 22:
    ax.set_xticks(ticks)
  ax.set_xbound(min_val - bin_width, max_val + bin_width)
  ax.set_ylabel('Count')
  y_min, y_max = ax.get_ybound()
  ax.set_ybound(0, y_max * 1.1)
  ax.ticklabel_format(style='sci', scilimits=(0, 0), axis='y')

  return ax

def psd(samples, sampling_freq=None, ax=None, max_len=ANALYSIS_MAX_LEN):
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
  max_len: float, optional
    Maximum number of samples to analyse. If `len(samples)` is greater than
    `max_len` then `samples` will first be truncated to `max_len` samples. If
    `None` then the whole array will be used.

  Returns
  -------
  out : :class:`matplotlib.axes.Axes`
    The `Axes` object that the PSD plot was drawn to.

  """
  if max_len is not None and len(samples) > max_len:
    logger.debug("Truncating to %d samples." % max_len)
    samples = samples[:max_len]

  if ax is None:
    fig = plt.figure()
    ax = fig.add_subplot(111)

  ax.set_title('Power Spectral Density')

  if sampling_freq is None:
    ax.set_xlabel('Frequency (Hz/$f_s$)')
    ax.set_ylabel('Power Spectral Density ($f_s \cdot \mathrm{Hz}^{-1}$)')
    sampling_freq = 1.0
  else:
    ax.ticklabel_format(style='sci', scilimits=(0, 0), axis='x')
    ax.set_xlabel('Frequency (Hz)')
    ax.set_ylabel('Power Spectral Density ($\mathrm{Hz}^{-1}$)')

  Pxx, freqs = mlab.psd(samples,
                        Fs=sampling_freq,
                        detrend=mlab.detrend_mean,
                        NFFT=2048,
                        noverlap=1024)

  ax.semilogy(freqs, Pxx, color='black')
  ax.set_xbound(0, sampling_freq / 2.0)

  return ax

def summary(samples, sampling_freq=None, max_len=ANALYSIS_MAX_LEN):
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
  max_len: float, optional
    Maximum number of samples to analyse. If `len(samples)` is greater than
    `max_len` then `samples` will first be truncated to `max_len` samples. If
    `None` then the whole array will be used.

  """
  fig = plt.figure()
  ax1 = fig.add_subplot(121)
  ax2 = fig.add_subplot(122)

  hist(samples[0], ax=ax1, max_len=max_len)
  psd(samples[0], sampling_freq, ax=ax2, max_len=max_len)

  fig.set_size_inches(10, 4, forward=True)
  fig.tight_layout()

def main():
  import argparse
  import peregrine.samples
  from peregrine.log import default_logging_config
  default_logging_config()

  parser = argparse.ArgumentParser()
  parser.add_argument("file", help="the sample data file to analyse")
  parser.add_argument("-n", "--num-samples", type=int, default=65536,
                      help="number of samples to use, defaults to 65536")
  parser.add_argument("-f", "--format", type=str, default="piksi",
                      help="Sample file format: "
                      + "'int8', '1bit', '1bitrev' or 'piksi' (default)")
  args = parser.parse_args()

  samples = peregrine.samples.load_samples(args.file, args.num_samples, file_format=args.format)
  summary(samples)

  plt.show()

if __name__ == "__main__":
  main()

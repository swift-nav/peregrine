# Copyright (C) 2016 Swift Navigation Inc.
# Contact: Valeri Atamaniouk <valeri@swiftnav.com>
#
# This source is subject to the license found in the file 'LICENSE' which must
# be be distributed together with this source. All other rights reserved.
#
# THIS CODE AND INFORMATION IS PROVIDED "AS IS" WITHOUT WARRANTY OF ANY KIND,
# EITHER EXPRESSED OR IMPLIED, INCLUDING BUT NOT LIMITED TO THE IMPLIED
# WARRANTIES OF MERCHANTABILITY AND/OR FITNESS FOR A PARTICULAR PURPOSE.

"""
The :mod:`peregrine.iqgen.amplitude_base` module contains classes and functions
related to base implementation of amplitude class.

"""


class AmplitudeBase(object):
  '''
  Amplitude control for a signal source.
  '''

  def __init__(self):
    '''
    Constructs base object for amplitude control.
    '''
    super(AmplitudeBase, self).__init__()

  def applyAmplitude(self, signal, userTimeAll_s):
    '''
    Applies amplitude modulation to signal.

    Parameters
    ----------
    signal : numpy.ndarray
      Signal sample vector. Each element defines signal amplitude in range
      [-1; +1]. This vector is modified in place.
    userTimeAll_s : numpy.ndarray
      Sample time vector. Each element defines sample time in seconds.

    Returns
    -------
    numpy.ndarray
      Array with output samples
    '''
    raise NotImplementedError()

  def computeMeanPower(self):
    '''
    Computes mean signal power.

    Returns
    -------
    float
      Mean signal power for the configured amplitude
    '''
    raise NotImplementedError()

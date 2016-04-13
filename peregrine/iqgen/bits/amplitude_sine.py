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
The :mod:`peregrine.iqgen.amplitude_sine` module contains classes and functions
related to implementation of sine-based amplitude class.

"""

from peregrine.iqgen.bits.amplitude_base import AmplitudeBase

import numpy
import scipy.constants


class AmplitudeSine(AmplitudeBase):
  '''
  Amplitude control with sine modulation over time.
  '''

  def __init__(self, units, initial, amplitude, period_s):
    '''
    Constructs sine amplitude control object.

    Parameters
    initial : float
      Initial amplitude value (median)
    amplitude : float
      Amplitude of change
    period_s : float
      Period of change in seconds
    '''
    super(AmplitudeSine, self).__init__(units)
    self.initial = initial
    self.amplitude = amplitude
    self.period_s = period_s
    self.c = 2. * scipy.constants.pi / period_s

  def __str__(self):
    '''
    Constructs literal presentation of object.

    Returns
    -------
    string
      Literal presentation of object
    '''
    return "AmplitudeSine(units={}, base={}, amp={}, p={} s)".\
        format(self.units, self.initial, self.amplitude, self.period_s)

  def applyAmplitude(self, signal, userTimeAll_s, noiseParams):
    '''
    Applies amplitude modulation to signal.

    Parameters
    ----------
    signal : numpy.ndarray
      Signal sample vector. Each element defines signal amplitude in range
      [-1; +1]. This vector is modified in place.
    userTimeAll_s : numpy.ndarray
      Sample time vector. Each element defines sample time in seconds.
    noiseParams : NoiseParameters
      Noise parameters to adjust signal amplitude level.

    Returns
    -------
    numpy.ndarray
      Array with output samples
    '''

    ampAll = numpy.sin(userTimeAll_s * self.c) * self.amplitude + self.initial

    ampAll = AmplitudeBase.convertUnits2Amp(ampAll,
                                            self.units,
                                            noiseParams)
    signal *= ampAll

    return signal

  def computeSNR(self, noiseParams):
    '''
    Computes signal to noise ratio in dB.

    noiseParams : NoiseParameters
      Noise parameter container

    Returns
    -------
    float
      SNR in dB
    '''
    value = self.initial
    return AmplitudeBase.convertUnits2SNR(value, self.units, noiseParams)

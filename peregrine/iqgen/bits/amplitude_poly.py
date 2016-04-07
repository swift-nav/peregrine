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
The :mod:`peregrine.iqgen.amplitude_poly` module contains classes and functions
related to implementation of polynomial-based amplitude class.

"""

from peregrine.iqgen.bits.amplitude_base import AmplitudeBase

import numpy


class AmplitudePoly(AmplitudeBase):
  '''
  Amplitude control with polynomial dependency over time.
  '''

  def __init__(self, coeffs):
    '''
    Constructs polynomial amplitude control object.

    Parameters
    coeffs : array-like
      Polynomial coefficients
    '''
    super(AmplitudePoly, self).__init__()

    self.coeffs = tuple([x for x in coeffs])
    if len(coeffs) > 0:
      self.poly = numpy.poly1d(coeffs)
    else:
      self.poly = None

  def __str__(self):
    '''
    Constructs literal presentation of object.

    Returns
    -------
    string
      Literal presentation of object
    '''
    return "AmplitudePoly(c={})".format(self.coeffs)

  def applyAmplitude(self, signal, userTimeAll_s):
    '''
    Applies amplitude modulation to signal.

    This method applies polynomial modulation.

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

    poly = self.poly
    if poly is not None:
      amplitudeVector = poly(userTimeAll_s)
      signal *= amplitudeVector

    return signal

  def computeMeanPower(self):
    '''
    Computes mean signal power.

    Returns
    -------
    float
      Mean signal power for the configured amplitude
    '''
    poly = self.poly
    if poly is not None:
      result = numpy.square(poly(0.))
    else:
      result = 1.
    return result

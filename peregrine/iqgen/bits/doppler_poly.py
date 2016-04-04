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
The :mod:`peregrine.iqgen.bits.oppler_poly` module contains classes and
functions related to generation of signals with polynomial-based movement.

"""

import numpy
import scipy.constants
from peregrine.iqgen.bits.doppler_base import DopplerBase


class Doppler(DopplerBase):
  '''
  Doppler control for an object that has constant acceleration. Such signal has
  constant doppler value with a possible sign invert.
  '''

  TWO_PI = scipy.constants.pi * 2

  def __init__(self, distance0_m, tec_epm2, coeffs):
    '''
    Constructs doppler control object for linear acceleration.

    Parameters
    ----------
    distance0_m : float
      Distance to object in meters at time 0.
    tec_epm2 : float
      Total free electron content integrated along line of sight to the object
      in electrons per m^2.
    coeffs : array-like
      Phase shift coefficients. Phase chift will be computed as:
      C_n*t^n + C_(n-1)^(n-1) + ... + C_2*t^2 + C_1*t + C_0
      C_n..C_0 - values for speed of light
    '''
    super(Doppler, self).__init__(distance0_m=distance0_m,
                                  tec_epm2=tec_epm2)
    self.coeffs = tuple([x for x in coeffs])
    self.n_coeffs = len(coeffs)
    self.speedPoly = None
    self.distancePoly = None
    if self.n_coeffs > 0:
      new_coeffs = []
      self.n_coeffs += 1
      for idx, c in enumerate(coeffs):
        order = self.n_coeffs - idx - 1
        new_coeffs.append(c / order)
      new_coeffs.append(0.)
      self.distancePoly = numpy.poly1d(new_coeffs)
      self.distanceCoeffs = new_coeffs
      if self.n_coeffs > 1:
        self.speedPoly = numpy.poly1d(coeffs)
    else:
      self.distanceCoeffs = None

  def __str__(self):
    '''
    Constructs literal presentation of object.

    Returns
    -------
    string
      Literal presentation of object
    '''
    return "DopplerPoly(coeffs={}, distance0_m={}," \
           " tec_epm2={} codeDopplerIgnored={})". \
           format(self.coeffs, self.distance0_m,
                  self.tec_epm2, self.codeDopplerIgnored)

  def computeDistanceM(self, svTime_s):
    '''
    Computes doppler shift in meters.

    Parameters
    ----------
    svTime_s : float
      Time in seconds at which distance is computed. Please note that  is not
      a time of the observer.

    Returns
    -------
    float
      Distance to satellite in meters.
    '''
    poly = self.distancePoly
    if poly is not None:
      return poly(svTime_s)  # self.coeffs[cnt - 1]
    else:
      return 0.

  def computeSpeedMps(self, svTime_s):
    '''
    Computes speed along the vector to satellite in meters per second.

    Parameters
    ----------
    svTime_s : float
      Time in seconds at which speed is computed. Please note that  is not
      a time of the observer.

    Returns
    -------
    float
      Speed of satellite in meters per second.
    '''
    poly = self.speedPoly
    if poly is not None:
      return poly(svTime_s)
    else:
      return 0.

  def computeDopplerShiftM(self, userTimeAll_s):
    '''
    Method to compute metric doppler shift

    Parameters
    ----------
    userTimeAll_s : numpy.ndarray(shape=(1, nSamples), dtype=numpy.float)
      Time vector for sample timestamps in seconds

    Returns
    -------
    numpy.ndarray(shape=(1, nSamples), dtype=numpy.float)
      Computed doppler shift in meters
    '''
    distancePoly = self.distancePoly
    if distancePoly is not None:
      # Slower, but simple
      doppler_m = distancePoly(userTimeAll_s)
    else:
      # No phase shift
      doppler_m = numpy.zeros_like(userTimeAll_s)
    return doppler_m

  def computeDopplerShiftHz(self, userTimeAll_s, carrierSignal):
    '''
    Method to compute doppler shift in Hz.

    Parameters
    ----------
    userTimeAll_s : numpy.ndarray(shape=(1, nSamples), dtype=numpy.float)
      Time vector for sample timestamps in seconds
    carrierSignal : object
      Carrier signal parameters

    Returns
    -------
    numpy.ndarray(shape=(1, nSamples), dtype=numpy.float)
      Computed doppler frquency shift in hertz
    '''
    speedPoly = self.speedPoly
    if speedPoly is not None:
      # Slower, but simple
      c0 = -carrierSignal.CENTER_FREQUENCY_HZ / scipy.constants.c
      doppler_hz = speedPoly(userTimeAll_s) * c0
    else:
      # No phase shift
      doppler_hz = numpy.zeros_like(userTimeAll_s)
    return doppler_hz


def linearDoppler(distance0_m,
                  tec_epm2,
                  frequency_hz,
                  doppler0_hz,
                  dopplerChange_hzps):
  '''
  Makes an object that corresponds to linear doppler change.

  Parameters
  ----------
  distance0_m : float
    Initial distance to object.
  doppler0_hz : float
    Initial doppler shift in hz.
  frequency_hz
    Carrier frequency in Hz.
  dopplerChange_hzps : float
    Doppler shift rate in Hz per second.

  Returns
  -------
  Doppler
    object that implments constant acceleration logic.
  '''
  speed0_mps = -scipy.constants.c / frequency_hz * doppler0_hz
  accel_mps2 = -scipy.constants.c / frequency_hz * dopplerChange_hzps

  return Doppler(distance0_m=distance0_m,
                 tec_epm2=tec_epm2,
                 coeffs=(accel_mps2, speed0_mps))


def constDoppler(distance0_m, tec_epm2, frequency_hz, doppler_hz):
  '''
  Makes an object that corresponds to a constant doppler value.

  Parameters
  ----------
  distance0_m : float
    Initial distance to object.
  frequency_hz : float
    Carrier frequency in Hz.
  doppler_hz : float
    Doppler shift in Hz.

  Returns
  -------
  Doppler
    Object that implements constant speed logic.
  '''
  speed_mps = -scipy.constants.c / frequency_hz * doppler_hz
  return Doppler(distance0_m=distance0_m, tec_epm2=tec_epm2, coeffs=(speed_mps,))


def zeroDoppler(distance_m, tec_epm2, frequency_hz):
  '''
  Makes an object that corresponds to zero doppler change.

  Parameters
  ----------
  distance0_m : float
    Initial distance to object.
  doppler0_hz : float
    Initial doppler shift in hz.
  frequency_hz
    Carrier frequency in Hz.
  dopplerChange_hzps : float
    Doppler shift rate in Hz per second.

  Returns
  -------
  Doppler
    object that implments constant acceleration logic.
  '''
  return Doppler(distance0_m=distance_m, tec_epm2=tec_epm2, coeffs=())

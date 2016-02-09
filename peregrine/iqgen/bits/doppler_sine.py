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
The :mod:`peregrine.iqgen.bits.doppler_sine` module contains classes and
functions related to generation of signals with circular changing doppler.

"""

from peregrine.iqgen.bits.doppler_base import DopplerBase

import scipy.constants
import numpy


class Doppler(DopplerBase):
  '''
  Doppler control for an object that has peridic acceleration.
  '''

  TWO_PI = scipy.constants.pi * 2.

  def __init__(self, distance0_m,  tec_epm2, speed0_mps, amplutude_mps, period_s):
    '''
    Constructs doppler control object for linear acceleration.

    Parameters
    ----------
    distance0_m : float
      Distance to object in meters at time 0.
    tec_epm2 : float
      Total free electron content integrated along line of sight to the object
      in electrons per m^2.
    speed0_mps : float
      Speed of satellite at time 0 in meters per second.
    amplutude_mps : float
      Amplitude of change
    period_s : float
      Period of change
    '''
    super(Doppler, self).__init__(distance0_m=distance0_m,
                                  tec_epm2=tec_epm2)
    self.speed0_mps = speed0_mps
    self.amplutude_mps = amplutude_mps
    self.period_s = period_s

  def __str__(self):
    '''
    Constructs literal presentation of object.

    Returns
    -------
    string
      Literal presentation of object
    '''
    return "SineDoppler(distance0_m={}, tec_epm2={}," \
           " speed0_mps={}, amplitude_mps={}, period_s={}," \
           " codeDopplerIgnored={})".\
        format(self.distance0_m, self.tec_epm2, self.speed0_mps,
               self.amplutude_mps, self.period_s, self.codeDopplerIgnored)

  def __repr__(self):
    '''
    Constructs python expression presentation of object.

    Returns
    -------
    string
      Python expression presentation of object
    '''
    return "Doppler({}, {}, {}, {}, {})".format(self.distance0_m,
                                                self.tec_epm2,
                                                self.speed0_mps,
                                                self.amplutude_mps,
                                                self.period_s)

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
    return self.distance0_m + self.speed0_mps * svTime_s + \
        self.amplutude_mps * \
        (1 - numpy.cos(Doppler.TWO_PI * svTime_s / self.period_s))

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
    return self.speed0_mps + self.amplutude_mps * \
        numpy.sin(Doppler.TWO_PI * svTime_s / self.period_s)

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
    D_0 = self.speed0_mps
    D_1 = self.amplutude_mps * self.period_s / self.twoPi
    D_2 = self.twoPi / self.period_s

    doppler_m = numpy.cos(D_2 * userTimeAll_s)
    doppler_m -= 1.
    doppler_m *= -D_1
    if D_0:
      doppler_m += D_0 * userTimeAll_s

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
    D_0 = self.speed0_mps
    D_1 = self.amplutude_mps
    D_2 = self.twoPi / self.period_s

    doppler_hz = numpy.sin(D_2 * userTimeAll_s) * D_1
    if D_0:
      doppler_hz += D_0
    doppler_hz *= -carrierSignal.CENTER_FREQUENCY_HZ / scipy.constants.c
    return doppler_hz


def sineDoppler(distance0_m, tec_epm2, frequency_hz, doppler0_hz, dopplerAmplitude_hz, dopplerPeriod_s):
  '''
  Makes an object that corresponds to linear doppler change.

  Parameters
  ----------
  distance0_m : float
    Initial distance to object.
  frequency_hz
    Carrier frequency in Hz.
  doppler0_hz : float
    Initial doppler shift in hz.
  dopplerAmplitude_hz : float
    Doppler change amplitude in Hz
  dopplerPeriod_s : float
    Doppler change period in seconds

  Returns
  -------
  Doppler
    object that implments constant acceleration logic.
  '''
  dopplerCoeff = -scipy.constants.c / frequency_hz
  speed0_mps = dopplerCoeff * doppler0_hz
  amplitude_mps = dopplerCoeff * dopplerAmplitude_hz

  return Doppler(distance0_m, tec_epm2, speed0_mps, amplitude_mps, dopplerPeriod_s)

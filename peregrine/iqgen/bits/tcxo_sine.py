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
The :mod:`peregrine.iqgen.bits.tcxo_sine` module contains class definitions
for TCXO control that can describe TCXO frequency drift as a periodic (sine)
function.

"""

from peregrine.iqgen.bits.tcxo_base import TCXOBase
import numpy
import scipy.constants


class TCXOSine(TCXOBase):
  '''
  Sine TCXO control class.
  '''

  def __init__(self, initial_ppm, amplitude_ppm, period_s):
    '''
    Constructs TCXO control object.

    Parameters
    ----------
    initial_ppm : float
      Initial drift in ppm
    amplitude_ppm : float
      Drift amplitude in ppm
    period_s : float
      Drift period in seconds
    '''
    super(TCXOSine, self).__init__()

    self.initial_ppm = initial_ppm
    self.amplitude_ppm = amplitude_ppm
    self.period_s = period_s
    self.c0 = -2. * scipy.constants.pi * amplitude_ppm * 1e-6
    self.c1 = 2. * scipy.constants.pi / period_s
    self.c2 = initial_ppm * 1e-6

  def __str__(self, *args, **kwargs):
    '''
    Provides string representation of the object
    '''
    return "TCXOSine: initial_ppm=%f amplitude_ppm=%f period_s=%f" % \
           (self.initial_ppm, self.amplitude_ppm, self.period_s)

  def __repr__(self):
    '''
    Provides string representation of the object
    '''
    return "TCXOSine(%f, %f, %f)" % \
           (self.initial_ppm, self.amplitude_ppm, self.period_s)

  def computeTcxoTime(self, fromSample, toSample, outputConfig):
    '''
    Method generates time vector for the given sample index range depending on
    TCXO behaviour.

    Parameters
    ----------
    fromSample : int
      Index of the first sample.
    toSample: int
      Index of the last sample plus 1.
    outputConfig : object
      Output configuration

    Returns
    -------
    numpy.ndarray(shape=(toSample - fromSample), dtype=numpy.float)
      Vector of the shifted time stamps for the given TCXO controller.
    '''
    c0 = self.c0
    c1 = self.c1
    c2 = self.c2
    time0_s = fromSample / outputConfig.SAMPLE_RATE_HZ
    timeX_s = toSample / outputConfig.SAMPLE_RATE_HZ

    timeAll_s = numpy.linspace(time0_s * c1,
                               timeX_s * c1,
                               toSample - fromSample,
                               endpoint=False,
                               dtype=numpy.float)

    result = numpy.cos(timeAll_s)
    result += -1.
    result *= c0
    if c2:
      result += timeAll_s * c2

    return result

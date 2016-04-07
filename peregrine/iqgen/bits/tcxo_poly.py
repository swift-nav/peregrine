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
The :mod:`peregrine.iqgen.bits.tcxo_poly` module contains class definitions
for TCXO control that can describe TCXO frequency drift as a polynome.

"""

from peregrine.iqgen.bits.tcxo_base import TCXOBase
import numpy


class TCXOPoly(TCXOBase):
  '''
  Polynomial TCXO control class.
  '''

  def __init__(self, coeffs):
    '''
    Constructs TCXO control object.

    Parameters
    ----------
    coeffs : array-like
      Coefficients for TCXO polynome. These coeffificens define a TCXO drift
      over time in ppm.
    '''
    super(TCXOPoly, self).__init__()
    self.coeffs = coeffs[:]
    if coeffs:
      # Recompute drift coefficients from speed of drift into distance of drift
      new_coeffs = []
      power_c = len(coeffs)
      for idx, val in enumerate(coeffs):
        power = power_c - idx
        new_coeffs.append(val * 1e-6 / power)
      new_coeffs.append(0)
      self.poly = numpy.poly1d(new_coeffs)
    else:
      self.poly = None

  def __str__(self, *args, **kwargs):
    '''
    Provides string representation of the object
    '''
    return "TCXOPoly: coeffs=%s" % str(self.coeffs)

  def __repr__(self):
    '''
    Provides string representation of the object
    '''
    return "TCXOPoly(%s)" % repr(self.coeffs)

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
    poly = self.poly

    if poly:
      time0_s = fromSample / outputConfig.SAMPLE_RATE_HZ
      timeX_s = toSample / outputConfig.SAMPLE_RATE_HZ
      timeAll_s = numpy.linspace(time0_s,
                                 timeX_s,
                                 toSample - fromSample,
                                 endpoint=False,
                                 dtype=numpy.float)
      result = poly(timeAll_s)
    else:
      result = None

    return result

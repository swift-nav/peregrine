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
The :mod:`peregrine.iqgen.bits.filter_base` module contains classes and
functions related to generated signal attenuation.

"""

from scipy.signal import lfilter


class FilterBase(object):

  def __init__(self, passBandAtt_dbhz, stopBandAtt_dbhz):
    '''
    Parameters
    ----------
    passBandAtt_dbhz : float
      Pass band attenutation in dB*Hz
    stopBandAtt_dbhz: float
      Stop band attenutation in dB*Hz
    '''
    self.passBandAtt_dbhz = passBandAtt_dbhz
    self.stopBandAtt_dbhz = stopBandAtt_dbhz
    self.a = None
    self.b = None
    self.zi = None

  def getPassBandAtt(self):
    '''
    Returns
    -------
    float
      Pass band attenuation in dB*Hz.
    '''
    return self.passBandAtt_dbhz

  def getStopBandAtt(self):
    '''
    Returns
    -------
    float
      Pass band attenuation in dB*Hz.
    '''
    return self.stopBandAtt_dbhz

  def filter(self, data):
    '''
    Performs noise reduction using Chebyshev type 2 IIR filter.

    Parameters
    ----------
    data : array-like
      Data samples before LPF processing

    Returns
    -------
    array-like
      Data samples after LPF processing
    '''
    data_out, zo = lfilter(self.b, self.a, data, zi=self.zi)
    self.zi = zo
    return data_out

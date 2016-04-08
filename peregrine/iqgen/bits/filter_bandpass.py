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
The :mod:`peregrine.iqgen.bits.low_pass_filter` module contains classes and
functions related to generated signal attenuation.

"""

from scipy.signal.signaltools import lfiltic
from scipy.signal import cheby2, cheb2ord
from peregrine.iqgen.bits.filter_base import FilterBase


class BandPassFilter(FilterBase):
  '''
  Chebyshev type 2 band-pass filter.
  '''

  def __init__(self, outputConfig, frequency_hz, bw_hz=1e6):
    '''
    Initialize filter object.

    Parameters
    ----------
    outputConfig : object
      Output configuration parameters object
    frequency_hz : float
      Intermediate frequency in hertz
    bw_hz : float, optional
      Noise bandwidth in hertz
    '''
    super(BandPassFilter, self).__init__(3., 40.)

    self.bw_hz = bw_hz
    self.frequency_hz = frequency_hz
    passBand_hz = bw_hz * 0.5 / outputConfig.SAMPLE_RATE_HZ
    stopBand_hz = bw_hz * 0.6 / outputConfig.SAMPLE_RATE_HZ
    mult = 2. / outputConfig.SAMPLE_RATE_HZ
    order, wn = cheb2ord(wp=[(frequency_hz - passBand_hz) * mult,
                             (frequency_hz + passBand_hz) * mult],
                         ws=[(frequency_hz - stopBand_hz) * mult,
                             (frequency_hz + stopBand_hz) * mult],
                         gpass=self.passBandAtt_dbhz,
                         gstop=self.stopBandAtt_dbhz,
                         analog=False)

    b, a = cheby2(order,  # Order of the filter
                  # Minimum attenuation required in the stop band in dB
                  self.stopBandAtt_dbhz,
                  wn,
                  btype="bandpass",
                  analog=False,
                  output='ba')

    self.a = a
    self.b = b
    self.zi = lfiltic(self.b, self.a, [])

  def __str__(self, *args, **kwargs):
    return "BandPassFilter(center=%f, bw=%f, pb=%f, sp=%f)" % \
           (self.frequency_hz, self.bw_hz,
            self.passBandAtt_dbhz, self.stopBandAtt_dbhz)

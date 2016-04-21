# Copyright (C) 2016 Swift Navigation Inc.
#
# Contact: Valeri Atamaniouk <valeri@swiftnav.com>
# This source is subject to the license found in the file 'LICENSE' which must
# be be distributed together with this source. All other rights reserved.
#
# THIS CODE AND INFORMATION IS PROVIDED "AS IS" WITHOUT WARRANTY OF ANY KIND,
# EITHER EXPRESSED OR IMPLIED, INCLUDING BUT NOT LIMITED TO THE IMPLIED
# WARRANTIES OF MERCHANTABILITY AND/OR FITNESS FOR A PARTICULAR PURPOSE.


'''
Unit tests for IQgen LP/BP filter types
'''

from peregrine.iqgen.bits.filter_base import FilterBase
from peregrine.iqgen.bits.filter_lowpass import LowPassFilter
from peregrine.iqgen.bits.filter_bandpass import BandPassFilter
from peregrine.iqgen.if_iface import CustomRateConfig
import numpy
from scipy.constants import pi as PI


def test_FilterBase_init():
  '''
  Test base filter construction and methods
  '''
  flt = FilterBase(passBandAtt_dbhz=3., stopBandAtt_dbhz=20.)
  assert flt.passBandAtt_dbhz == 3.
  assert flt.stopBandAtt_dbhz == 20.
  assert flt.getPassBandAtt() == 3.
  assert flt.getStopBandAtt() == 20.
  assert flt.a is None
  assert flt.b is None
  assert flt.zi is None


# def test_LowPassFilter_init():
#   '''
#   Test low pass filter
#   '''
#   config = CustomRateConfig
#   freqHz = config.GPS.L1.INTERMEDIATE_FREQUENCY_HZ
#   flt = LowPassFilter(config, freqHz)

#   assert isinstance(flt.a, numpy.ndarray)
#   assert isinstance(flt.b, numpy.ndarray)
#   assert isinstance(flt.zi, numpy.ndarray)
#   # Filter must have all roots in the range (-1; +1)
#   assert numpy.all(numpy.abs(numpy.roots(flt.a)) < 1)


# def test_LowPassFilter_filter():
#   '''
#   Verify that LPF is correctly lowers signal power for frequencies
#   '''
#   config = CustomRateConfig
#   freqHz = config.GPS.L1.INTERMEDIATE_FREQUENCY_HZ
#   flt = LowPassFilter(config, freqHz)
#   n_samples = 10000
#   time0_s = 0.
#   time1_s = time0_s + (float(n_samples) /
#                        float(config.SAMPLE_RATE_HZ))
#   sampleTimeAll_s = numpy.linspace(time0_s, time1_s,
#                                    n_samples,
#                                    endpoint=False,
#                                    dtype=numpy.float)

#   # Normal frequency signal: shall be ~-3Db
#   signal1 = numpy.cos(2. * PI * sampleTimeAll_s * (freqHz + 0e6))
#   # Low frequency signal: shall be ~-3Db
#   signal2 = numpy.cos(2. * PI * sampleTimeAll_s * (freqHz - 2e6))
#   # High frequency signal: shall be ~-40Db
#   signal3 = numpy.cos(2. * PI * sampleTimeAll_s * (freqHz + 2e6))

#   # Original signal powers
#   A10 = numpy.mean(numpy.abs(signal1)) ** 2
#   A20 = numpy.mean(numpy.abs(signal2)) ** 2
#   A30 = numpy.mean(numpy.abs(signal3)) ** 2

#   filtSignal1 = flt.filter(signal1)
#   filtSignal2 = flt.filter(signal2)
#   filtSignal3 = flt.filter(signal3)

#   # Filtered signal powers
#   A11 = numpy.mean(numpy.abs(filtSignal1)) ** 2
#   A21 = numpy.mean(numpy.abs(filtSignal2)) ** 2
#   A31 = numpy.mean(numpy.abs(filtSignal3)) ** 2

#   # Compute SNR in dB
#   snr1 = 10. * numpy.log10(A11 / A10)
#   snr2 = 10. * numpy.log10(A21 / A20)
#   snr3 = 10. * numpy.log10(A31 / A30)

#   assert snr1 >= -flt.getPassBandAtt() * 1.05
#   assert snr2 >= -flt.getPassBandAtt() * 1.05
#   assert snr3 <= -flt.getStopBandAtt() * 0.95


# def test_BandPassFilter_init():
#   '''
#   Test band pass filter
#   '''
#   config = CustomRateConfig
#   freqHz = config.GPS.L1.INTERMEDIATE_FREQUENCY_HZ
#   flt = BandPassFilter(config, freqHz)

#   assert isinstance(flt.a, numpy.ndarray)
#   assert isinstance(flt.b, numpy.ndarray)
#   assert isinstance(flt.zi, numpy.ndarray)
#   # Filter must have all roots in the range (-1; +1)
#   assert numpy.all(numpy.abs(numpy.roots(flt.a)) < 1)


# def test_BandPassFilter_filter():
#   '''
#   Verify that BPF lowers out of band frequencies and keeps band frequency.
#   '''
#   config = CustomRateConfig
#   freqHz = config.GPS.L1.INTERMEDIATE_FREQUENCY_HZ
#   flt = BandPassFilter(config, freqHz)

#   n_samples = 10000
#   time0_s = 0.
#   time1_s = time0_s + (float(n_samples) /
#                        float(config.SAMPLE_RATE_HZ))
#   sampleTimeAll_s = numpy.linspace(time0_s, time1_s,
#                                    n_samples,
#                                    endpoint=False,
#                                    dtype=numpy.float)

#   # Normal frequency signal: shall be ~-3Db
#   signal1 = numpy.cos(2. * PI * sampleTimeAll_s * (freqHz + 0e6))
#   # Low frequency signal: shall be ~-40Db
#   signal2 = numpy.cos(2. * PI * sampleTimeAll_s * (freqHz - 3e6))
#   # High frequency signal: shall be ~-40Db
#   signal3 = numpy.cos(2. * PI * sampleTimeAll_s * (freqHz + 3e6))

#   # Original signal powers
#   A10 = numpy.mean(numpy.abs(signal1)) ** 2
#   A20 = numpy.mean(numpy.abs(signal2)) ** 2
#   A30 = numpy.mean(numpy.abs(signal3)) ** 2

#   filtSignal1 = flt.filter(signal1)
#   filtSignal2 = flt.filter(signal2)
#   filtSignal3 = flt.filter(signal3)

#   # Filtered signal powers
#   A11 = numpy.mean(numpy.abs(filtSignal1)) ** 2
#   A21 = numpy.mean(numpy.abs(filtSignal2)) ** 2
#   A31 = numpy.mean(numpy.abs(filtSignal3)) ** 2

#   # Compute SNR in dB
#   snr1 = 10. * numpy.log10(A11 / A10)
#   snr2 = 10. * numpy.log10(A21 / A20)
#   snr3 = 10. * numpy.log10(A31 / A30)

#   assert snr1 >= -flt.getPassBandAtt() * 1.05
#   assert snr2 <= -flt.getStopBandAtt() * 0.95
#   assert snr3 <= -flt.getStopBandAtt() * 0.95


# def test_LowPassFilter_str():
#   '''
#   Test low pass filter str()
#   '''
#   config = CustomRateConfig
#   freqHz = config.GPS.L1.INTERMEDIATE_FREQUENCY_HZ
#   flt = LowPassFilter(config, freqHz)
#   value = str(flt)
#   assert value.find('LowPass') >= 0


# def test_BandPassFilter_str():
#   '''
#   Test band pass filter str()
#   '''
#   config = CustomRateConfig
#   freqHz = config.GPS.L1.INTERMEDIATE_FREQUENCY_HZ
#   flt = BandPassFilter(config, freqHz)
#   value = str(flt)
#   assert value.find('BandPass') >= 0

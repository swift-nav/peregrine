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
Unit tests for IQgen signal definitions
'''

from peregrine.iqgen.bits.signals import GPS
from peregrine.iqgen.bits.signals import GLONASS
from scipy.constants import c as C


def test_GPSL1():
  '''
  Test GPS L1 signal methods
  '''
  doppler = -10. / C * GPS.L1CA.CENTER_FREQUENCY_HZ
  assert GPS.L1CA.calcDopplerShiftHz(1000., 10.) == doppler
  assert GPS.L1CA.getCodeChipIndex(0.) == 0
  assert GPS.L1CA.getCodeChipIndex(0.5) == 511500
  assert GPS.L1CA.getSymbolIndex(0.) == 0
  assert GPS.L1CA.getSymbolIndex(0.5) == 25


def test_GPSL2():
  '''
  Test GPS L2 signal methods
  '''
  doppler = -10. / C * GPS.L2C.CENTER_FREQUENCY_HZ
  assert GPS.L2C.calcDopplerShiftHz(1000., 10.) == doppler
  assert GPS.L2C.getCodeChipIndex(0.) == 0
  assert GPS.L2C.getCodeChipIndex(0.5) == 511500
  assert GPS.L2C.getSymbolIndex(0.) == 0
  assert GPS.L2C.getSymbolIndex(0.5) == 25


def test_GLONASS_common():
  '''
  Test common GLONASS signal methods
  '''
  assert GLONASS.getCodeChipIndex(0.) == 0
  assert GLONASS.getCodeChipIndex(0.5) == 511000 / 2
  assert GLONASS.getSymbolIndex(0.) == 0
  assert GLONASS.getSymbolIndex(0.5) == 50


def test_GLONASSL1():
  '''
  Test GLONASS L1 signal methods
  '''
  doppler = -10. / C * GLONASS.L1S[0].CENTER_FREQUENCY_HZ
  assert GLONASS.L1S[0].calcDopplerShiftHz(1000., 10.) == doppler
  assert GLONASS.L1S[0].getCodeChipIndex(0.) == 0
  assert GLONASS.L1S[0].getCodeChipIndex(0.5) == 511000 / 2
  assert GLONASS.L1S[0].getSymbolIndex(0.) == 0
  assert GLONASS.L1S[0].getSymbolIndex(0.5) == 50


def test_GLONASSL2():
  '''
  Test GLONASS L2 signal methods
  '''
  doppler = -10. / C * GLONASS.L2S[0].CENTER_FREQUENCY_HZ
  assert GLONASS.L2S[0].calcDopplerShiftHz(1000., 10.) == doppler
  assert GLONASS.L2S[0].getCodeChipIndex(0.) == 0
  assert GLONASS.L2S[0].getCodeChipIndex(0.5) == 511000 / 2
  assert GLONASS.L2S[0].getSymbolIndex(0.) == 0
  assert GLONASS.L2S[0].getSymbolIndex(0.5) == 50

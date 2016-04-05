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
The :mod:`peregrine.iqgen.bits.signals` module contains classes and functions
related to common satellite signal definitions and operations.

"""

import scipy.constants


def _calcDopplerShiftHz(frequency_hz, distance_m, velocity_mps):
  '''
  Utility to compute doppler shift from ditance and velocity for a band
  frequency.

  Parameters
  ----------
  frequency_hz : float
    Band frequency in hertz
  distance_m : float
    Distance to satellite in meters
  velocity_m : float
    Satellite velocity in meters per second.

  Return
  ------
  float
    Doppler shift in hertz
  '''
  doppler_hz = -velocity_mps * frequency_hz / scipy.constants.c
  return doppler_hz


class GPS:
  '''
  GPS signal parameters and utilities.
  '''

  class L1CA:
    '''
    GPS L1 C/A parameters and utilities.
    '''
    SYMBOL_RATE_HZ = 50
    CENTER_FREQUENCY_HZ = 1575.42e6
    CODE_CHIP_RATE_HZ = 1023000
    CHIP_TO_SYMBOL_DIVIDER = 20460

    @staticmethod
    def calcDopplerShiftHz(distance_m, velocity_mps):
      '''
      Converts relative speed into doppler value for GPS L1 C/A band.

      Parameters
      ----------
      distance_m : float
        Distance in meters
      velocity_mps : float
        Relative speed in meters per second.

      Returns
      -------
      float
        Doppler shift in Hz.
      '''
      return _calcDopplerShiftHz(GPS.L1CA.CENTER_FREQUENCY_HZ,
                                 distance_m, velocity_mps)

    @staticmethod
    def getSymbolIndex(svTime_s):
      '''
      Computes symbol index.

      Parameters
      ----------
      svTime_s : float
        SV time in seconds

      Returns
      -------
      long
        Symbol index
      '''
      return long(svTime_s * GPS.L1CA.SYMBOL_RATE_HZ)

    @staticmethod
    def getCodeChipIndex(svTime_s):
      '''
      Computes code chip index.

      Parameters
      ----------
      svTime_s : float
        SV time in seconds

      Returns
      -------
      long
        Code chip index
      '''
      return long(svTime_s * GPS.L1CA.CODE_CHIP_RATE_HZ)

  class L2C:
    '''
    GPS L2 C parameters and utilities.
    '''

    SYMBOL_RATE_HZ = 50
    CENTER_FREQUENCY_HZ = 1227.60e6
    CODE_CHIP_RATE_HZ = 1023000
    CHIP_TO_SYMBOL_DIVIDER = 20460

    @staticmethod
    def calcDopplerShiftHz(distance_m, velocity_mps):
      '''
      Converts relative speed into doppler value for GPS L2 C band.

      Parameters
      ----------
      distance_m : float
        Distance in meters
      velocity_mps : float
        Relative speed in meters per second.

      Returns
      -------
      float
        Doppler shift in Hz.
      '''
      return _calcDopplerShiftHz(GPS.L2C.CENTER_FREQUENCY_HZ,
                                 distance_m, velocity_mps)

    @staticmethod
    def getSymbolIndex(svTime_s):
      '''
      Computes symbol index.

      Parameters
      ----------
      svTime_s : float
        SV time in seconds

      Returns
      -------
      long
        Symbol index
      '''
      return long(svTime_s * GPS.L2C.SYMBOL_RATE_HZ)

    @staticmethod
    def getCodeChipIndex(svTime_s):
      '''
      Computes code chip index.

      Parameters
      ----------
      svTime_s : float
        SV time in seconds

      Returns
      -------
      long
        Code chip index
      '''
      return long(svTime_s * GPS.L2C.CODE_CHIP_RATE_HZ)

# GLONASS L1
GLONASS_L1_CENTER_FREQUENCY_HZ = 1602000
GLONASS_L1_FREQUENCY_STEP_HZ = 562500

# GLONASS L2
GLONASS_L2_CENTER_FREQUENCY_HZ = 1246000
GLONASS_L2_FREQUENCY_STEP_HZ = 437500

# GLONASS L1 and L2 common
GLONASS_SYMBOL_RATE_HZ = 100
GLONASS_CODE_CHIP_RATE_HZ = 511000
GLONASS_CHIP_TO_SYMBOL_DIVIDER = 5110


class GLONASS:
  '''
  GLONASS signal parameters and utilities.
  '''

  # See ICD L1, L2 GLONASS
  #
  # No. of  | Nominal value of | Nominal value of
  # channel | frequency in L1  | frequency in L2
  #         | sub-band, MHz    | sub-band, MHz
  # --------+------------------+------------------
  #    06   |     1605.3750    |    1248.6250
  #    05   |     1604.8125    |    1248.1875
  #    04   |     1604.2500    |    1247.7500
  #    03   |     1603.6875    |    1247.3125
  #    02   |     1603.1250    |    1246.8750
  #    01   |     1602.5625    |    1246.4375
  #    00   |     1602.0000    |    1246.0000
  #   -01   |     1601.4375    |    1245.5625
  #   -02   |     1600.8750    |    1245.1250
  #   -03   |     1600.3125    |    1244.6875
  #   -04   |     1599.7500    |    1244.2500
  #   -05   |     1599.1875    |    1243.8125
  #   -06   |     1598.6250    |    1243.3750
  #   -07   |     1598.0625    |    1242.9375

  @staticmethod
  def getSymbolIndex(svTime_s):
    '''
    Computes symbol index.

    Parameters
    ----------
    svTime_s : float
      SV time in seconds

    Returns
    -------
    long
      Symbol index
    '''
    return long(float(svTime_s) * float(GLONASS.SYMBOL_RATE_HZ))

  @staticmethod
  def getCodeChipIndex(svTime_s):
    '''
    Computes code chip index.

    Parameters
    ----------
    svTime_s : float
      SV time in seconds

    Returns
    -------
    long
      Code chip index
    '''
    return long(float(svTime_s) * float(GLONASS.CODE_CHIP_RATE_HZ))

  class _L1:
    '''
    GLONASS L1 frequency object for a single sub-band

    Attributes
    ----------
    SUB_BAND
      Sub-band index in the range [-7, 6] 
    SYMBOL_RATE_HZ
      Symbol rate for GLONASS L1
    CENTER_FREQUENCY_HZ
      Center frequency for GLONASS L1 sub-band
    CODE_CHIP_RATE_HZ
      Code chip rate in Hz
    CHIP_TO_SYMBOL_DIVIDER
      Divider for converting chips to symbols
    '''

    def __init__(self, subBand):
      assert subBand >= -7 and subBand < 7

      self.SUB_BAND = subBand
      self.SYMBOL_RATE_HZ = GLONASS_SYMBOL_RATE_HZ
      self.CENTER_FREQUENCY_HZ = float(GLONASS_L1_CENTER_FREQUENCY_HZ +
                                       subBand * GLONASS_L1_FREQUENCY_STEP_HZ)
      self.CODE_CHIP_RATE_HZ = GLONASS_CODE_CHIP_RATE_HZ
      self.CHIP_TO_SYMBOL_DIVIDER = GLONASS_CHIP_TO_SYMBOL_DIVIDER

    def calcDopplerShiftHz(self, distance_m, velocity_mps):
      '''
      Converts relative speed into doppler value for GPS L2 C band.

      Parameters
      ----------
      distance_m : float
        Distance in meters
      velocity_mps : float
        Relative speed in meters per second.

      Returns
      -------
      float
        Doppler shift in Hz.
      '''
      return _calcDopplerShiftHz(self.CENTER_FREQUENCY_HZ,
                                 distance_m, velocity_mps)

  class _L2:
    '''
    GLONASS L2 frequency object for a single sub-band

    Attributes
    ----------
    SUB_BAND
      Sub-band index in the range [-7, 6] 
    SYMBOL_RATE_HZ
      Symbol rate for GLONASS L2
    CENTER_FREQUENCY_HZ
      Center frequency for GLONASS L2 sub-band
    CODE_CHIP_RATE_HZ
      Code chip rate in Hz
    CHIP_TO_SYMBOL_DIVIDER
      Divider for converting chips to symbols
    '''

    def __init__(self, subBand):
      assert subBand >= -7 and subBand < 7

      self.SUB_BAND = subBand
      self.SYMBOL_RATE_HZ = GLONASS_SYMBOL_RATE_HZ
      self.CENTER_FREQUENCY_HZ = float(GLONASS_L2_CENTER_FREQUENCY_HZ +
                                       subBand * GLONASS_L2_FREQUENCY_STEP_HZ)
      self.CODE_CHIP_RATE_HZ = GLONASS_CODE_CHIP_RATE_HZ
      self.CHIP_TO_SYMBOL_DIVIDER = GLONASS_CHIP_TO_SYMBOL_DIVIDER

    def calcDopplerShiftHz(self, distance_m, velocity_mps):
      '''
      Converts relative speed into doppler value for GPS L2 C band.

      Parameters
      ----------
      distance_m : float
        Distance in meters
      velocity_mps : float
        Relative speed in meters per second.

      Returns
      -------
      float
        Doppler shift in Hz.
      '''
      return _calcDopplerShiftHz(self.CENTER_FREQUENCY_HZ,
                                 distance_m, velocity_mps)

  L1S = [_L1(b) for b in range(7)] + [_L1(b) for b in range(-7, 0)]
  L2S = [_L2(b) for b in range(7)] + [_L2(b) for b in range(-7, 0)]

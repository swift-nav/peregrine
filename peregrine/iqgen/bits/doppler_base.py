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
The :mod:`peregrine.iqgen.doppler_base` module contains classes and functions
related to base implementation of doppler class.

"""

import scipy.constants
import numpy


class DopplerBase(object):
  '''
  Doppler control for a signal source that moves with a constant speed.
  '''

  def __init__(self, distance0_m=0., tec_epm2=50.,  dtype=numpy.longdouble):
    '''
    Constructs doppler base object for movement control.

    Parameters
    ----------
    distance0_m : float
      Distance to object in meters at time 0.
    tec_epm2 : float
      Total free electron content integrated along line of sight to the object
      in electrons per m^2.
    dtype : object, optional
      Numpy type for sample computations.
    '''
    super(DopplerBase, self).__init__()
    self.distance0_m = distance0_m
    self.tec_epm2 = tec_epm2
    self.dtype = dtype
    self.codeDopplerIgnored = False
    self.twoPi = scipy.constants.pi * 2.

  def isCodeDopplerIgnored(self):
    '''
    Checks if the code is ignoring doppler control.

    Returns
    -------
    bool
      When True, the sample generator ignores doppler shift for data and code
      processing.
    '''
    return self.codeDopplerIgnored

  def setCodeDopplerIgnored(self, value):
    '''
    Changes doppler control for data and code processing

    Parameters
    ----------
    value : bool
      True - ignore doppler for code and data processing, False - apply doppler.
    '''
    self.codeDopplerIgnored = value

  def computeSignalDelayS(self, frequency_hz):
    '''
    Computes delay in seconds for an epoch time (time 0) for a given carrier
    frequency.

    The method computes signal delay, which is a sum of the following
    parameters:
    - Distance to object divided per speed of light
    - Ionospheric delay according to TEC value for the given frequency
    - Tropospheric delay

    Parameters
    ----------
    frequency_hz : float
      Signal frequency in hertz.

    Returns
    -------
    float
      Signal delay in seconds. 
    '''
    distanceDelay_s = self.distance0_m / scipy.constants.c
    ionoDelay_s = 40.3 * self.tec_epm2 / numpy.square(frequency_hz)
    delay_s = distanceDelay_s + ionoDelay_s
    return delay_s

  def applySignalDelays(self, userTimeAll_s, carrierSignal):
    '''
    Modifies time vector in accordance to signal delays due to distance and
    atmospheric delays.

    Parameters
    ----------
    userTimeAll_s : numpy.ndvector(shape=(n), dtype=numpy.float)
      Vector of time stamps for which samples are generated
    carrierSignal : object
      Signal parameters object

    Returns
    -------
    numpy.ndvector(shape=(n), dtype=numpy.float)
      Vector of sample time stamps updated according to computed delays.
    '''
    signalDelay_s = self.computeSignalDelayS(carrierSignal.CENTER_FREQUENCY_HZ)
    return userTimeAll_s - signalDelay_s

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
    raise NotImplementedError()

  def computeSpeedMps(self, svTime_s):
    '''
    Computes speed along the vecto2r to satellite in meters per second.

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
    raise NotImplementedError()

  def computeBatch(self,
                   userTimeAll_s,
                   amplitude,
                   carrierSignal,
                   ifFrequency_hz,
                   message,
                   code,
                   outputConfig,
                   debug):
    '''
    Computes signal samples for the doppler object.

    Parameters
    ----------
    userTimeAll_s : numpy.ndarray(dtype=numpy.float)
      Sample timestamps in seconds
    amplitude : float
      Signal amplitude object.
    carrierSignal : object
      Carrier frequency object
    ifFrequency_hz: float
      Intermediate frequency in hertz
    message : object
      Message object for providing access to symbols
    code : object
      PRN code object for providing access to chips
    debug : bool
      Debug flag

    Returns
    -------
    signal : numpy.ndarray(n_samples, dtype=float)
      Generated samples
    userTimeX_s : float
      End of interval time in seconds
    chipAll_idx : numpy.ndarray(n_samples, dtype=float)
      Code chip phases for the samples
    chips : numpy.ndarray(n_samples, dtype=int)
      Code combined with data
    '''

    userTimeAll_s = self.applySignalDelays(userTimeAll_s, carrierSignal)

    # Computing doppler coefficients
    twoPi = self.twoPi

    # Sine wave phase without doppler
    phaseAll = userTimeAll_s * (twoPi * ifFrequency_hz)
    # Get doppler shift in meters
    doppler_m = self.computeDopplerShiftM(userTimeAll_s)
    # Doppler for carrier center frequency
    carrFreqRatio = -carrierSignal.CENTER_FREQUENCY_HZ / scipy.constants.c
    phaseAll += doppler_m * (carrFreqRatio * twoPi)

    # Convert phase to signal value and multiply by amplitude
    signal = scipy.cos(phaseAll)

    if amplitude:
      amplitude.applyAmplitude(signal, userTimeAll_s)

    # PRN and data index computation
    chipAll_idx = userTimeAll_s * carrierSignal.CODE_CHIP_RATE_HZ
    if self.codeDopplerIgnored:
      pass
    else:
      # Computing doppler coefficients
      chipFreqRatio = -carrierSignal.CODE_CHIP_RATE_HZ / scipy.constants.c
      chipAll_idx += doppler_m * chipFreqRatio

    chips = self.computeDataNChipVector(chipAll_idx,
                                        carrierSignal,
                                        message,
                                        code)

    # Combine data and sine wave
    signal *= chips

    # Generate debug data
    doppler_hz = self.computeDopplerShiftHz(userTimeAll_s,
                                            carrierSignal) if debug else None
    return (signal, doppler_hz)

  @staticmethod
  def computeDeltaUserTimeS(userTime0_s, n_samples, outputConfig):
    '''
    Helper for computing generation interval duration in seconds.

    Parameters
    ----------
    userTime0_s : float
      Generation interval start
    n_samples : int
      Number of samples in the generation interval
    outputConfig : object
      Output configuration.

    Returns
    -------
    float
      Generation interval duration in seconds
    '''
    deltaUserTime_s = float(n_samples) / outputConfig.SAMPLE_RATE_HZ
    return deltaUserTime_s

  @staticmethod
  def computeDopplerHz(frequency_hz, speed_mps):
    '''
    Generic method for doppler shift computation.

    Parameters
    ----------
    frequency_hz : float
      Frequency in hertz for which doppler is computed.
    speed_mps : float
      Speed in meters per second for which doppler is computed.

    Returns
    -------
    float
      Doppler shift value in hertz.
    '''
    doppler_hz = -frequency_hz / scipy.constants.c * speed_mps
    return doppler_hz

  def computeDataNChipVector(self, chipAll_idx, carrierSignal, message, code):
    '''
    Helper for computing vector that combines data and code chips.

    Parameters
    ----------
    chipAll_idx : ndarray
      vector of chip phases
    carrierSignal : object
      Signal description object
    messge : object
      Data bits source
    code : objects
      Code chips source

    Returns
    -------
    ndarray
      Array of code chips multiplied with data bits
    '''

    chipAll_long = chipAll_idx.astype(numpy.long)
    dataBits = message.getDataBits(
        chipAll_long / carrierSignal.CHIP_TO_SYMBOL_DIVIDER)
    result = code.combineData(chipAll_long, dataBits)

    return result

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
    raise NotImplementedError("Metric doppler computation is not implemented")

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
    raise NotImplementedError("Metric doppler computation is not implemented")

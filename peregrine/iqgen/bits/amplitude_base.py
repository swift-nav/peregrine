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
The :mod:`peregrine.iqgen.amplitude_base` module contains classes and functions
related to base implementation of amplitude class.

"""

import numpy


class NoiseParameters(object):
  '''
  Container class for holding noise generation parameters.
  '''

  def __init__(self, samplingFreqHz, noiseSigma):
    '''
    Parameters
    ----------
    samplingFreqHz : float or long
      Sampling frequency in Hz
    noiseSigma : float
      Noise Sigma value
    '''
    super(NoiseParameters, self).__init__()
    self.samplingFreqHz = samplingFreqHz
    self.noiseSigma = noiseSigma

    # Compute coefficient for 1ms integration
    self.signalK = noiseSigma * 2. * \
        numpy.sqrt(1000000. / float(samplingFreqHz))

    self.freqTimeTau = 1e-6 * float(samplingFreqHz)

  def getSamplingFreqHz(self):
    '''
    Get sampling frequency.

    Returns
    -------
    float or long
      Sampling frequency in Hz
    '''
    return self.samplingFreqHz

  def getNoiseSigma(self):
    '''
    Get noise Sigma.

    Returns
    -------
    float
      Noise sigma value
    '''
    return self.noiseSigma

  def getFreqTimesTau(self):
    '''
    Get sampling integration parameter.

    Returns
    -------
    float
      Integration parameter of the sampling frequency times integration time.
    '''
    return self.freqTimeTau

  def getSignalK(self):
    '''
    Get amplification coefficient for SNR at 0 dB.

    Returns
    -------
    float
      Signal amplification coefficient for SNR at 0 dB.
    '''
    return self.signalK


class AmplitudeBase(object):
  '''
  Amplitude control for a signal source.

  Attributes
  ----------
  UNITS_AMPLITUDE : string
    Type of object for measuring signal in amplitude. SNR is dependent on
    amplitude square.
  UNITS_POWER : string
    Type of object for measuring signal in power. SNR is linearly dependent on
    power.
  UNITS_SNR : string
    Type of object for measuring signal in SNR.
  UNITS_SNR_DB : string
    Type of object for measuring signal in SNR dB.

  '''

  UNITS_AMPLITUDE = 'AMP'
  UNITS_POWER = 'PWR'
  UNITS_SNR = 'SNR'
  UNITS_SNR_DB = 'SNR_DB'

  def __init__(self, units):
    '''
    Constructs base object for amplitude control.

    Parameters
    ----------
    units : string
      Object units. Can be one of the supported values:
      - AmplitudeBase::UNITS_AMPLITUDE -- Amplitude units
      - AmplitudeBase::UNITS_SNR_DB -- SNR in dB
      - AmplitudeBase::UNITS_SNR -- SNR
      - AmplitudeBase::UNITS_POWER -- Power units
    '''
    super(AmplitudeBase, self).__init__()
    self.units = units

  def getUnits(self):
    '''
    Provides access to units.

    Returns
    -------
    string
      Amplitude units
    '''
    return self.units

  def applyAmplitude(self, signal, userTimeAll_s, noiseParams=None):
    '''
    Applies amplitude modulation to signal.

    Parameters
    ----------
    signal : numpy.ndarray
      Signal sample vector. Each element defines signal amplitude in range
      [-1; +1]. This vector is modified in place.
    userTimeAll_s : numpy.ndarray
      Sample time vector. Each element defines sample time in seconds.
    noiseParams : NoiseParameters
      Noise parameters to adjust signal amplitude level.

    Returns
    -------
    numpy.ndarray
      Array with output samples
    '''
    raise NotImplementedError()

  def computeSNR(self, noiseParams):
    '''
    Computes signal to noise ratio in dB.

    Parameters
    ----------
    noiseParams : NoiseParameters
      Noise parameter container

    Returns
    -------
    float
      SNR in dB
    '''
    raise NotImplementedError()

  @staticmethod
  def convertUnits2SNR(value, units, noiseParams):
    '''
    Converts signal units to SNR in dB

    Parameters
    ----------
    noiseParams : NoiseParameters
      Noise parameter container

    Returns
    -------
    float
      SNR in dB
    '''

    noiseSigma = noiseParams.getNoiseSigma()
    freqTimesTau = noiseParams.getFreqTimesTau()

    if units == AmplitudeBase.UNITS_AMPLITUDE:
      power = numpy.square(value)
      snr = freqTimesTau * power / (4. * noiseSigma * noiseSigma)
      snrDb = 10 * numpy.log10(snr)
    elif units == AmplitudeBase.UNITS_POWER:
      power = value
      snr = freqTimesTau * power / (4. * noiseSigma * noiseSigma)
      snrDb = 10 * numpy.log10(snr)
    elif units == AmplitudeBase.UNITS_SNR:
      snr = value
      snrDb = 10 * numpy.log10(snr)
    elif units == AmplitudeBase.UNITS_SNR_DB:
      snrDb = value
    else:  # pragma: no cover
      assert False
    return snrDb

  @staticmethod
  def convertUnits2Amp(value, units, noiseParams):
    '''
    Converts signal units to amplitude

    Parameters
    ----------
    noiseParams : NoiseParameters
      Noise parameter container

    Returns
    -------
    float
      SNR in dB
    '''

    noiseSigma = noiseParams.getNoiseSigma()
    freqTimesTau = noiseParams.getFreqTimesTau()

    if units == AmplitudeBase.UNITS_AMPLITUDE:
      amp = value
    elif units == AmplitudeBase.UNITS_POWER:
      amp = numpy.sqrt(value)
    elif units == AmplitudeBase.UNITS_SNR:
      snr = value
      amp = numpy.sqrt(4. * snr / freqTimesTau) * noiseSigma
    elif units == AmplitudeBase.UNITS_SNR_DB:
      snrDb = value
      snr = 10. ** (0.1 * snrDb)
      amp = numpy.sqrt(4. * snr / freqTimesTau) * noiseSigma
    else:  # pragma: no cover
      assert False
    return amp

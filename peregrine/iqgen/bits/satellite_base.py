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
The :mod:`peregrine.iqgen.bits.satellite_base` module contains classes and
functions related to satellite base object.

"""
from peregrine.iqgen.bits.doppler_poly import zeroDoppler
from peregrine.iqgen.bits.amplitude_poly import AmplitudePoly
from peregrine.iqgen.bits.amplitude_base import AmplitudeBase


class Satellite(object):
  '''
  Satellite object.

  Satellite object combines speed/position computation and data generation for
  all supported bands.
  '''

  def __init__(self, svName):
    '''
    Constructor.

    Parameters
    ----------
    svName : string
      Satellite name
    '''
    super(Satellite, self).__init__()
    self.svName = svName
    self.doppler = zeroDoppler(0., 0., 1.)
    self.amplitude = AmplitudePoly(AmplitudeBase.UNITS_AMPLITUDE, ())

  def getDoppler(self):
    '''
    Returns doppler object.

    Returns
    -------
    object
      Doppler control object
    '''
    return self.doppler

  def setDoppler(self, doppler):
    '''
    Changes doppler object.

    Parameters
    -------
    doppler : object
      Doppler control object
    '''
    self.doppler = doppler

  def getName(self):
    '''
    Returns satellite name.

    Returns
    -------
    string
      Satellite name
    '''
    return self.svName

  def setAmplitude(self, amplitude):
    '''
    Changes amplitude

    Parameters
    ----------
    amplitude : float
      amplitude value for signal generation
    '''
    self.amplitude = amplitude

  def getAmplitude(self):
    '''
    Provides amplitude object

    Returns
    -------
    object
      Amplitude object
    '''
    return self.amplitude

  def __str__(self):
    '''
    Returns string representation of SV object
    '''
    return self.getName()

  def getBatchSignals(self,
                      userTimeAll_s,
                      samples,
                      outputConfig,
                      noiseParams,
                      band,
                      debug):
    '''
    Generates signal samples.

    Parameters
    ----------
    userTimeAll_s : numpy.ndarray(n_samples, dtype=numpy.float64)
      Vector of observer's timestamps in seconds for the interval start.
    samples : numpy.ndarray((4, n_samples))
      Array to which samples are added.
    outputConfig : object
      Output configuration object.
    noiseParams : NoiseParameters
      Noise parameters object.
    band : Band
      Band description object.
    debug : bool
      Debug flag

    Returns
    -------
    list
      Debug information
    '''
    raise NotImplementedError()

  def isBandEnabled(self, band, outputConfig):
    '''
    Checks if particular band is supported and enabled.

    Parameters
    ----------
    band : Band
      Band description object.
    outputConfig : object
      Output configuration

    Returns:
    bool
      True, if the band is supported and enabled; False otherwise.
    '''
    return False

  def isCodeDopplerIgnored(self):
    '''
    Checks if code doppler is ignored

    Returns
    -------
    bool
      True, when code doppler is ignored, False otherwise
    '''
    return self.doppler.isCodeDopplerIgnored()

  def setCodeDopplerIgnored(self, flag):
    '''
    Checks if code doppler is ignored

    Parameters
    ----------
    flag : bool
      Flag to control code doppler: True - to ignore code doppler, 
      False - normal operation 

    '''
    self.doppler.setCodeDopplerIgnored(flag)

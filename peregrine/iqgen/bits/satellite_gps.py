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
The :mod:`peregrine.iqgen.bits.satellite_gps` module contains classes and
functions related to GPS satellite configuration.

"""
import peregrine.iqgen.bits.signals as signals
from peregrine.iqgen.bits.message_const import Message
from peregrine.iqgen.bits.prn_gps_l1ca import PrnCode as GPS_L1CA_Code
from peregrine.iqgen.bits.prn_gps_l2c import PrnCode as GPS_L2C_Code
from peregrine.iqgen.bits.satellite_base import Satellite

import numpy

DEFAULT_MESSAGE = Message(1)


class GPSSatellite(Satellite):
  '''
  GPS satellite object.
  '''

  def __init__(self, prnNo):
    '''
    Constructs satellite object

    Parameters
    ----------
    prnNo : int
      GPS satellite number for selecting PRN.
    '''
    super(GPSSatellite, self).__init__("GPS{}".format(prnNo))
    self.prn = prnNo
    self.l2clCodeType = '01'
    self.l1caCode = GPS_L1CA_Code(prnNo)
    self.l2cCode = GPS_L2C_Code(prnNo, self.l2clCodeType)
    self.l1caEnabled = False
    self.l2cEnabled = False
    self.l1caMessage = DEFAULT_MESSAGE
    self.l2cMessage = DEFAULT_MESSAGE
    self.time0S = 0.
    self.pr0M = 0.
    self.phaseShift = 0.

  def setL1CAEnabled(self, enableFlag):
    '''
    Enables or disable GPS L1 C/A sample generation

    Parameters
    ----------
    enableFlag : boolean
      Flag to enable (True) or disable (False) GPS L1 C/A samples
    '''
    self.l1caEnabled = enableFlag

  def isL1CAEnabled(self):
    '''
    Tests if L1 C/A signal generation is enabled

    Returns
    -------
    bool
      True, when L1 C/A signal generation is enabled, False otherwise
    '''
    return self.l1caEnabled

  def setL2CEnabled(self, enableFlag):
    '''
    Enables or disable GPS L2 C sample generation

    Parameters
    ----------
    enableFlag : boolean
      Flag to enable (True) or disable (False) GPS L2 C samples
    '''
    self.l2cEnabled = enableFlag

  def isL2CEnabled(self):
    '''
    Tests if L2 C signal generation is enabled

    Returns
    -------
    bool
      True, when L2 C signal generation is enabled, False otherwise
    '''
    return self.l2cEnabled

  def setL2CLCodeType(self, clCodeType):
    if self.l2clCodeType != clCodeType:
      self.l2cCode = GPS_L2C_Code(self.prn, clCodeType)
      self.l2clCodeType = clCodeType

  def getL2CLCodeType(self):
    return self.l2clCodeType

  def setL1CAMessage(self, message):
    '''
    Configures data source for L1 C/A signal.

    Parameters
    ----------
    message : object
      Message object that will provide symbols for L1 C/A signal.
    '''
    self.l1caMessage = message

  def setL2CMessage(self, message):
    '''
    Configures data source for L2 C signal.

    Parameters
    ----------
    message : object
      Message object that will provide symbols for L2 C signal.
    '''
    self.l2cMessage = message

  def getL1CAMessage(self):
    '''
    Returns configured message object for GPS L1 C/A band

    Returns
    -------
    object
      L1 C/A message object
    '''
    return self.l1caMessage

  def getL2CMessage(self):
    '''
    Returns configured message object for GPS L2 C band

    Returns
    -------
    object
      L2 C message object
    '''
    return self.l2cMessage

  def getBatchSignals(self, userTimeAll_s, samples, outputConfig, debug):
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
    debug : bool
      Debug flag

    Returns
    -------
    list
      Debug information
    '''
    result = []
    if (self.l1caEnabled):
      intermediateFrequency_hz = outputConfig.GPS.L1.INTERMEDIATE_FREQUENCY_HZ
      frequencyIndex = outputConfig.GPS.L1.INDEX
      values = self.doppler.computeBatch(userTimeAll_s,
                                         self.amplitude,
                                         signals.GPS.L1CA,
                                         intermediateFrequency_hz,
                                         self.l1caMessage,
                                         self.l1caCode,
                                         outputConfig,
                                         debug)
      numpy.add(samples[frequencyIndex],
                values[0],
                out=samples[frequencyIndex])
      debugData = {'type': "GPSL1", 'doppler': values[1]}
      result.append(debugData)
    if (self.l2cEnabled):
      intermediateFrequency_hz = outputConfig.GPS.L2.INTERMEDIATE_FREQUENCY_HZ
      frequencyIndex = outputConfig.GPS.L2.INDEX
      values = self.doppler.computeBatch(userTimeAll_s,
                                         self.amplitude,
                                         signals.GPS.L2C,
                                         intermediateFrequency_hz,
                                         self.l2cMessage,
                                         self.l2cCode,
                                         outputConfig,
                                         debug)
      numpy.add(samples[frequencyIndex],
                values[0],
                out=samples[frequencyIndex])
      debugData = {'type': "GPSL2", 'doppler': values[1]}
      result.append(debugData)
    return result

  def isBandEnabled(self, bandIndex, outputConfig):
    '''
    Checks if particular band is supported and enabled.

    Parameters
    ----------
    bandIndex : int
      Signal band index
    outputConfig : object
      Output configuration

    Returns:
    bool
      True, if the band is supported and enabled; False otherwise.
    '''
    result = None
    if bandIndex == outputConfig.GPS.L1.INDEX:
      result = self.isL1CAEnabled()
    elif bandIndex == outputConfig.GPS.L2.INDEX:
      result = self.isL2CEnabled()
    else:
      result = False
    return result

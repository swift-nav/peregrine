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
The :mod:`peregrine.iqgen.bits.satellite_glo` module contains classes and
functions related to GLONASS satellite configuration.

"""
import peregrine.iqgen.bits.signals as signals
from peregrine.iqgen.bits.message_const import Message
from peregrine.iqgen.bits.prn_glo_l1l2 import PrnCode as GLO_CA_Code
from peregrine.iqgen.bits.satellite_base import Satellite

import numpy

DEFAULT_MESSAGE = Message(1)


class GLOSatellite(Satellite):
  '''
  GLONASS satellite object.
  '''

  def __init__(self, prnNo):
    '''
    Constructs satellite object

    Parameters
    ----------
    prnNo : int
      GPS satellite number for selecting PRN.
    '''
    super(GLOSatellite, self).__init__("GLONASS{}".format(prnNo))
    self.prn = prnNo
    self.caCode = GLO_CA_Code(prnNo)
    self.l1Enabled = False
    self.l2Enabled = False
    self.l1Message = DEFAULT_MESSAGE
    self.l2Message = DEFAULT_MESSAGE
    self.time0S = 0.
    self.pr0M = 0.
    self.phaseShift = 0.

  def setL1Enabled(self, enableFlag):
    '''
    Enables or disable GLONASS L1 C/A sample generation

    Parameters
    ----------
    enableFlag : boolean
      Flag to enable (True) or disable (False) GPS L1 C/A samples
    '''
    self.l1Enabled = enableFlag

  def isL1Enabled(self):
    '''
    Tests if L1 C/A signal generation is enabled

    Returns
    -------
    bool
      True, when L1 C/A signal generation is enabled, False otherwise
    '''
    return self.l1Enabled

  def setL2Enabled(self, enableFlag):
    '''
    Enables or disable GLONASS L2 C sample generation

    Parameters
    ----------
    enableFlag : boolean
      Flag to enable (True) or disable (False) GPS L2 C samples
    '''
    self.l2Enabled = enableFlag

  def isL2Enabled(self):
    '''
    Tests if L2 C signal generation is enabled

    Returns
    -------
    bool
      True, when L2 C signal generation is enabled, False otherwise
    '''
    return self.l2Enabled

  def setL1Message(self, message):
    '''
    Configures data source for L1 C/A signal.

    Parameters
    ----------
    message : object
      Message object that will provide symbols for L1 C/A signal.
    '''
    self.l1Message = message

  def setL2Message(self, message):
    '''
    Configures data source for L2 C signal.

    Parameters
    ----------
    message : object
      Message object that will provide symbols for L2 C signal.
    '''
    self.l2Message = message

  def getL1Message(self):
    '''
    Returns configured message object for GPS L1 C/A band

    Returns
    -------
    object
      L1 C/A message object
    '''
    return self.l1Message

  def getL2Message(self):
    '''
    Returns configured message object for GPS L2 C band

    Returns
    -------
    object
      L2 C message object
    '''
    return self.l2Message

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
    if (self.l1Enabled):
      band = outputConfig.GLONASS.L1
      intermediateFrequency_hz = band.INTERMEDIATE_FREQUENCIES_HZ[self.prn]
      frequencyIndex = band.INDEX
      values = self.doppler.computeBatch(userTimeAll_s,
                                         self.amplitude,
                                         signals.GLONASS.L1S[self.prn],
                                         intermediateFrequency_hz,
                                         self.l1Message,
                                         self.caCode,
                                         outputConfig,
                                         debug)
      numpy.add(samples[frequencyIndex],
                values[0],
                out=samples[frequencyIndex])
      debugData = {'type': "GLOL1", 'doppler': values[1]}
      result.append(debugData)
    if (self.l2Enabled):
      band = outputConfig.GLONASS.L2
      intermediateFrequency_hz = band.INTERMEDIATE_FREQUENCIES_HZ[self.prn]
      frequencyIndex = band.INDEX
      values = self.doppler.computeBatch(userTimeAll_s,
                                         self.amplitude,
                                         signals.GLONASS.L2S[self.prn],
                                         intermediateFrequency_hz,
                                         self.l2Message,
                                         self.caCode,
                                         outputConfig,
                                         debug)
      numpy.add(samples[frequencyIndex],
                values[0],
                out=samples[frequencyIndex])
      debugData = {'type': "GLOL2", 'doppler': values[1]}
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
    if bandIndex == outputConfig.GLONASS.L1.INDEX:
      result = self.isL1Enabled()
    elif bandIndex == outputConfig.GLONASS.L2.INDEX:
      result = self.isL2Enabled()
    else:
      result = False
    return result

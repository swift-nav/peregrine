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
The :mod:`peregrine.iqgen.bits.tcxo_base` module contains base class definitions
for TCXO control.

"""


class TCXOBase(object):
  '''
  Base class for TCXO control. The class computes time shifts of TCXO depending
  on external conditions like temperature, vibration, etc.
  '''

  def __init__(self):
    super(TCXOBase, self).__init__()

  def computeTcxoTime(self, fromSample, toSample, outputConfig):
    '''
    Method generates time vector for the given sample index range depending on
    TCXO behaviour.

    Parameters
    ----------
    fromSample : int
      Index of the first sample.
    toSample: int
      Index of the last sample plus 1.
    outputConfig : object
      Output configuration

    Returns
    -------
    numpy.ndarray(shape=(toSample - fromSample), dtype=numpy.float)
      Vector of the shifted time stamps for the given TCXO controller.
    '''
    raise NotImplementedError()

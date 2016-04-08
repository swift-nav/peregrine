# Copyright (C) 2016 Swift Navigation Inc.
# Contact: Valeri Atamaniouk <valeri@swiftnav.com>
#
# This source is subject to the license found in the file 'LICENSE' which must
# be be distributed together with this source. All other rights reserved.
#
# THIS CODE AND INFORMATION IS PROVIDED "AS IS" WITHOUT WARRANTY OF ANY KIND,
# EITHER EXPRESSED OR IMPLIED, INCLUDING BUT NOT LIMITED TO THE IMPLIED
# WARRANTIES OF MERCHANTABILITY AND/OR FITNESS FOR A PARTICULAR PURPOSE.

import numpy

"""
The :mod:`peregrine.iqgen.bits.prn_gps_l1ca` module contains classes and
functions related to GPS L1 C/A PRN processing

"""

import peregrine.include.generateCAcode

caCodes = peregrine.include.generateCAcode.caCodes


class PrnCode(object):
  '''
  GPS L1 C/A code object
  '''
  CODE_LENGTH = 1023
  CODE_FREQUENCY_HZ = 1023e3

  def __init__(self, prnNo):
    '''
    Initializes object.

    Parameters
    ----------
    prnNo : int
      SV identifier
    '''
    super(PrnCode, self).__init__()
    self.caCode = caCodes[prnNo - 1][:]
    tmp = numpy.asarray(self.caCode, dtype=numpy.int8)
    tmp -= 1
    tmp /= -2
    self.binCode = tmp
    self.prnNo = prnNo
    self.bitLookup = numpy.asarray([1, -1], dtype=numpy.int8)

  def getCodeBits(self, chipIndex_all):
    '''
    Parameters
    ----------
    chipIndex_all : numpy.ndarray(dtype=numpy.long)
      Vector of chip indexes

    Returns
    -------
    numpy.ndarray(dtype=numpy.uint8)
      Vector of code chip bits
    '''
    # numpy.take degrades performance a lot over time.
    # return numpy.take(self.binCode, chipIndex_all, mode='wrap')
    return self.binCode[chipIndex_all % len(self.binCode)]

  def combineData(self, chipIndex_all, dataBits):
    '''
    Mixes in code chip and data

    Parameters
    ----------
    chipIndex_all : numpy.ndarray(dtype=numpy.long)
      Chip indexes
    dataBits : numpy.ndarray(dtype=numpy.uint8)
      Data bits

    Returns
    -------
    numpy.ndarray(dtype=numpy.int8)
      Vector of data bits modulated by chips
    '''
    chipBits = self.getCodeBits(chipIndex_all)
    combined = numpy.bitwise_xor(chipBits, dataBits)
    # numpy.take degrades performance a lot over time.
    # result = numpy.take(self.bitLookup, combined)
    result = self.bitLookup[combined]
    return result

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
The :mod:`peregrine.iqgen.bits.prn_gps_l2c` module contains classes and
functions related to GPS L2C PRN processing

"""

import numpy

from peregrine.include.generateL2CMcode import L2CMCodes

caCodes = (L2CMCodes < 0).astype(numpy.uint8)


class PrnCode(object):
  '''
  Combined GPS L2 CM and CL code object
  '''

  class CM_Code(object):
    '''
    GPS L2 Civil Medium code object
    '''
    CODE_LENGTH = 10230
    CODE_FREQUENCY_HZ = 511.5e3

    def __init__(self, prnNo):
      '''
      Initializes object.

      Parameters
      ----------
      prnNo : int
        SV identifier
      '''
      super(PrnCode.CM_Code, self).__init__()
      self.binCode = caCodes[prnNo - 1]

    def getCodeBits(self):
      return self.binCode

  class CL_Code(object):
    '''
    GPS L2 Civil Long code object
    '''
    CODE_LENGTH = 767250
    CODE_FREQUENCY_HZ = 511.5e3

    def __init__(self, prnNo, codeType):
      '''
      Initializes object.

      Parameters
      ----------
      prnNo : int
        SV identifier
      codeType : string
        Type of the code: '01', '1', '0'
      '''
      super(PrnCode.CL_Code, self).__init__()
      self.binCode = numpy.ndarray(PrnCode.CL_Code.CODE_LENGTH,
                                   dtype=numpy.bool)
      if codeType == '01':
        self.binCode.fill(False)
        self.binCode[1::2].fill(True)
      elif codeType == '1':
        self.binCode.fill(True)
      elif codeType == '0':
        self.binCode.fill(False)
      else:
        raise ValueError('Unsupported GPS L2 CL generator type %s ' %
                         str(codeType))

    def getCodeBits(self):
      return self.binCode

  CODE_LENGTH = CL_Code.CODE_LENGTH * 2
  CODE_FREQUENCY_HZ = 1023e3

  def __init__(self, prnNo, clCodeType):
    '''
    Initializes object.

    Parameters
    ----------
    prnNo : int
      SV identifier
    clCodeType : string
      Type of the code: '01', '1', '0'
    '''
    super(PrnCode, self).__init__()
    cl = PrnCode.CL_Code(prnNo, clCodeType)
    cm = PrnCode.CM_Code(prnNo)
    self.bitLookup = numpy.asarray([1, -1], dtype=numpy.int8)
    tmp = numpy.ndarray(PrnCode.CL_Code.CODE_LENGTH * 2, dtype=numpy.uint8)
    tmp[1::2] = cl.getCodeBits()
    for i in range(0, PrnCode.CL_Code.CODE_LENGTH * 2, PrnCode.CM_Code.CODE_LENGTH * 2):
      tmp[i:i + PrnCode.CM_Code.CODE_LENGTH * 2:2] = cm.getCodeBits()
    self.binCode = tmp
    self.prnNo = prnNo

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
    return self.binCode[chipIndex_all % PrnCode.CODE_LENGTH]

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
    oddChips = chipIndex_all & 1 == 0
    oddChipDataBits = dataBits & oddChips
    combined = numpy.bitwise_xor(chipBits, oddChipDataBits)
    result = self.bitLookup[combined]
    return result

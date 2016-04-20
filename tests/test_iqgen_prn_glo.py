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
Unit tests for IQgen GLONASS PRNs types
'''

from peregrine.iqgen.bits.prn_glo_l1l2 import PrnCode as GLOPrnCode
from peregrine.iqgen.bits.prn_glo_l1l2 import caCode as GLOCACode
import numpy


def test_GLOPrn_init():
  '''
  GLONASS L1/L2 PRN object init
  '''
  code = GLOPrnCode(0)

  assert code.prnNo == 0
  assert (code.bitLookup == [1, -1]).all()
  assert (code.binCode == GLOCACode).all()


def test_GLOPrn_combineData0():
  '''
  GLONASS L1/L2 C/A PRN data combination
  '''
  code = GLOPrnCode(1)
  dataBits = numpy.zeros(511, dtype=numpy.uint8)
  chipIndex_all = numpy.linspace(0, 510, 511, dtype=numpy.long)
  data = code.combineData(chipIndex_all, dataBits)
  assert ((data < 0) == GLOCACode).all()


def test_GPSL1Prn_combineData1():
  '''
  GLONASS L1/L2 C/A PRN data combination
  '''
  code = GLOPrnCode(1)
  dataBits = numpy.zeros(511, dtype=numpy.uint8)
  dataBits[1::2] = 1
  chipIndex_all = numpy.linspace(0, 510, 511, dtype=numpy.long)
  data = code.combineData(chipIndex_all, dataBits)
  assert ((data[1::2] > 0) == GLOCACode[1::2]).all()
  assert ((data[::2] < 0) == GLOCACode[::2]).all()

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
Unit tests for IQgen GPS PRNs types
'''

from peregrine.iqgen.bits.prn_gps_l1ca import PrnCode as GPSL1PrnCode
from peregrine.iqgen.bits.prn_gps_l1ca import caCodes as GPSL1CACodes
from peregrine.iqgen.bits.prn_gps_l2c import PrnCode as GPSL2PrnCode
from peregrine.iqgen.bits.prn_gps_l2c import caCodes as GPSL2CMCodes
import numpy


def test_GPSL1Prn_init():
  '''
  GPS L1 C/A PRN object init
  '''
  code = GPSL1PrnCode(1)

  assert code.prnNo == 1
  assert (code.bitLookup == [1, -1]).all()
  assert (code.binCode == GPSL1CACodes[0]).all()


def test_GPSL1Prn_combineData0():
  '''
  GPS L1 C/A PRN data combination
  '''
  code = GPSL1PrnCode(1)
  dataBits = numpy.zeros(1023, dtype=numpy.uint8)
  chipIndex_all = numpy.linspace(0, 1022, 1023, dtype=numpy.long)
  data = code.combineData(chipIndex_all, dataBits)
  assert ((data < 0) == GPSL1CACodes[0]).all()


def test_GPSL1Prn_combineData1():
  '''
  GPS L1 C/A PRN data combination
  '''
  code = GPSL1PrnCode(1)
  dataBits = numpy.zeros(1023, dtype=numpy.uint8)
  dataBits[1::2] = 1
  chipIndex_all = numpy.linspace(0, 1022, 1023, dtype=numpy.long)
  data = code.combineData(chipIndex_all, dataBits)
  assert ((data[::2] < 0) == GPSL1CACodes[0][::2]).all()
  assert ((data[1::2] > 0) == GPSL1CACodes[0][1::2]).all()


def test_GPSL2Prn_init0():
  '''
  GPS L2 C object init (CL=0)
  '''
  code = GPSL2PrnCode(1, '0')
  assert code.prnNo == 1
  assert (code.bitLookup == [1, -1]).all()
  assert (code.binCode[1::2] == 0).all()

  for i in range(0, 767250, 10230):
    assert (code.binCode[i * 2:(i + 10230) * 2:2] == GPSL2CMCodes[0]).all()


def test_GPSL2Prn_init1():
  '''
  GPS L2 C object init (CL=1)
  '''
  code = GPSL2PrnCode(1, '1')
  assert code.prnNo == 1
  assert (code.bitLookup == [1, -1]).all()
  assert (code.binCode[1::2] == 1).all()
  for i in range(0, 767250, 10230):
    assert (code.binCode[i * 2:(i + 10230) * 2:2] == GPSL2CMCodes[0]).all()


def test_GPSL2Prn_init01():
  '''
  GPS L2 C object init (CL=0/1)
  '''
  code = GPSL2PrnCode(1, '01')
  assert code.prnNo == 1
  assert (code.bitLookup == [1, -1]).all()
  assert (code.binCode[1::4] == 0).all()
  assert (code.binCode[3::4] == 1).all()
  for i in range(0, 767250, 10230):
    assert (code.binCode[i * 2:(i + 10230) * 2:2] == GPSL2CMCodes[0]).all()


def test_GPSL2Prn_init_f():
  '''
  GPS L2 C object init (CL=error)
  '''
  try:
    GPSL2PrnCode(1, '02')
    assert False
  except ValueError:
    pass


def test_GPSL2Prn_combineData0():
  '''
  GPS L2 C data combination (CL=0)
  '''
  code = GPSL2PrnCode(1, '0')
  dataBits = numpy.zeros(10230 * 2, dtype=numpy.uint8)
  chipIndex_all = numpy.linspace(0, 20459, 20460, dtype=numpy.long)
  data = code.combineData(chipIndex_all, dataBits)
  binData = (data < 0).astype(numpy.uint8)
  assert binData.shape == (20460, )
  assert (binData[1::2] == 0).all()
  assert (binData[::2] == GPSL2CMCodes[0]).all()


def test_GPSL2Prn_combineData1():
  '''
  GPS L2 C data combination (CL=1)
  '''
  code = GPSL2PrnCode(1, '1')
  dataBits = numpy.zeros(10230 * 2, dtype=numpy.uint8)
  chipIndex_all = numpy.linspace(0, 20459, 20460, dtype=numpy.long)
  data = code.combineData(chipIndex_all, dataBits)
  binData = (data < 0).astype(numpy.uint8)
  assert binData.shape == (20460, )
  assert (binData[1::2] == 1).all()
  assert (binData[::2] == GPSL2CMCodes[0]).all()


def test_GPSL2Prn_combineData01():
  '''
  GPS L2 C data combination (CL=0/1)
  '''
  code = GPSL2PrnCode(1, '01')
  dataBits = numpy.zeros(10230 * 2, dtype=numpy.uint8)
  chipIndex_all = numpy.linspace(0, 20459, 20460, dtype=numpy.long)
  data = code.combineData(chipIndex_all, dataBits)
  binData = (data < 0).astype(numpy.uint8)
  assert binData.shape == (20460, )
  assert (binData[1::4] == 0).all()
  assert (binData[3::4] == 1).all()
  assert (binData[::2] == GPSL2CMCodes[0]).all()


def test_GPSL2Prn_combineData02():
  '''
  GPS L2 C data combination (CL=0/1)
  '''
  code = GPSL2PrnCode(1, '01')
  dataBits = numpy.zeros(10230 * 2, dtype=numpy.uint8)
  dataBits.fill(1)
  chipIndex_all = numpy.linspace(0, 20459, 20460, dtype=numpy.long)
  data = code.combineData(chipIndex_all, dataBits)
  binData = (data < 0).astype(numpy.uint8)
  assert binData.shape == (20460, )
  assert (binData[1::4] == 0).all()
  assert (binData[3::4] == 1).all()
  assert (binData[::2] != GPSL2CMCodes[0]).all()

# Copyright (C) 2016 Swift Navigation Inc.
#
# This source is subject to the license found in the file 'LICENSE' which must
# be be distributed together with this source. All other rights reserved.
#
# THIS CODE AND INFORMATION IS PROVIDED "AS IS" WITHOUT WARRANTY OF ANY KIND,
# EITHER EXPRESSED OR IMPLIED, INCLUDING BUT NOT LIMITED TO THE IMPLIED
# WARRANTIES OF MERCHANTABILITY AND/OR FITNESS FOR A PARTICULAR PURPOSE.

from test_acquisition import run_acq_test
from peregrine import defaults


def test_custom_rate():
  run_acq_test(-4000, 0, [1], defaults.FORMAT_2BITS_X1_GPS_L1, 'custom_rate')


def test_low_rate():
  run_acq_test(-2000, 0, [2], defaults.FORMAT_2BITS_X1_GPS_L1, 'low_rate')


def test_normal_rate():
  run_acq_test(2000, 0, [3], defaults.FORMAT_2BITS_X1_GPS_L1, 'normal_rate')


# Takes long time to complete in Travis CI test and
# therefore fails
# def test_high_rate():
#  run_acq_test(2000, 0, [4], defaults.FORMAT_2BITS_X1_GPS_L1, 'high_rate')

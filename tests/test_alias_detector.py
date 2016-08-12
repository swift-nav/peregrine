# Copyright (C) 2016 Swift Navigation Inc.
#
# This source is subject to the license found in the file 'LICENSE' which must
# be be distributed together with this source. All other rights reserved.
#
# THIS CODE AND INFORMATION IS PROVIDED "AS IS" WITHOUT WARRANTY OF ANY KIND,
# EITHER EXPRESSED OR IMPLIED, INCLUDING BUT NOT LIMITED TO THE IMPLIED
# WARRANTIES OF MERCHANTABILITY AND/OR FITNESS FOR A PARTICULAR PURPOSE.

import numpy as np
from peregrine import alias_detector

def get_error(ad, expected_err_hz):
  angle = expected_err_hz * 2 * np.pi * 0.001
  rotation = np.exp(1j * angle)

  ad.reinit()

  iq = rotation
  ad.first(iq)

  for i in range(ad.acc_len):
    ad.second(iq)
    ad.first(iq)
    iq *= rotation
    iq /= abs(iq)

  return ad.get_err_hz()

def test_alias_detect():
  '''
  Alias lock detector test
  '''

  ad_l1ca = alias_detector.AliasDetector()
  ad_l2c = alias_detector.AliasDetector()

  meas_err_hz = [-75, -80, -25, -30, 0, 20, 25, 65, 75]
  true_err_hz = [-75, -75, -25, -25, 0, 25, 25, 75, 75]

  for ad in [ad_l1ca, ad_l2c]:
    for i, err_hz in enumerate(meas_err_hz):
      assert true_err_hz[i] == get_error(ad, err_hz)

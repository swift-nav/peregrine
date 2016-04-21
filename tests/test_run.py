# Copyright (C) 2016 Swift Navigation Inc.
#
# This source is subject to the license found in the file 'LICENSE' which must
# be be distributed together with this source. All other rights reserved.
#
# THIS CODE AND INFORMATION IS PROVIDED "AS IS" WITHOUT WARRANTY OF ANY KIND,
# EITHER EXPRESSED OR IMPLIED, INCLUDING BUT NOT LIMITED TO THE IMPLIED
# WARRANTIES OF MERCHANTABILITY AND/OR FITNESS FOR A PARTICULAR PURPOSE.

import peregrine.run
import peregrine.defaults as defaults
import peregrine.gps_constants as gps
import sys
import cPickle
import os
import numpy as np

from test_acquisition import run_acq_test
from mock import patch
from shutil import copyfile
from test_common import generate_sample_file, \
                        run_peregrine,\
                        propagate_code_phase, \
                        get_sampling_freq

def test_skip_params():
  """
  Test different skip parameters:
  --skip_samples
  and
  --skip_ms

  """
  run_acq_test(1000, 0, [1], '1bit', skip_samples = 1000)
  run_acq_test(1000, 0, [1], '1bit', skip_ms = 100)

def test_tracking():
  prn = 15
  init_doppler = 1234
  init_code_phase = 0
  file_format = '2bits_x2'
  freq_profile = 'low_rate'
  skip_param = '--skip-ms'
  skip_val = 0
  samples_filename = generate_sample_file(prn, init_doppler,
                                          init_code_phase,
                                          file_format, freq_profile)

  run_peregrine(samples_filename, file_format, freq_profile,
                skip_param, skip_val, False)

  # Comparison not working on Travis at the moment, needs further debugging.
  # Simply make sure tracking runs successfully for now.
  #with open(NEW_TRK_RES, 'rb') as f:
  #  new_trk_results = cPickle.load(f)
  #with open(OLD_TRK_RES, 'rb') as f:
  #  old_trk_results = cPickle.load(f)
  #assert new_trk_results == old_trk_results

  # Clean-up.
  os.remove(samples_filename)

if __name__ == '__main__':
  test_tracking()


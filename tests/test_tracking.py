# -*- coding: utf-8 -*-
# Copyright (C) 2016 Swift Navigation Inc.
# Contact: Pasi Miettinen <pasi.miettinen@exafore.com>
#
# This source is subject to the license found in the file 'LICENSE' which must
# be be distributed together with this source. All other rights reserved.
#
# THIS CODE AND INFORMATION IS PROVIDED "AS IS" WITHOUT WARRANTY OF ANY KIND,
# EITHER EXPRESSED OR IMPLIED, INCLUDING BUT NOT LIMITED TO THE IMPLIED
# WARRANTIES OF MERCHANTABILITY AND/OR FITNESS FOR A PARTICULAR PURPOSE.

from test_common import generate_sample_file,\
                        run_peregrine,\
                        propagate_code_phase,\
                        get_sampling_freq
from test_acquisition import get_acq_result_file_name

import cPickle
import os


def get_track_result_file_name(sample_file, prn):
  sample_file, sample_file_extension = os.path.splitext(sample_file)
  return sample_file + (".PRN-%d.%s" % (prn, 'l1ca')) +\
         sample_file_extension + '.track_results'


def run_track_test(init_doppler, init_code_phase,
                   prns, file_format,
                   freq_profile='low_rate',
                   skip_samples=None, skip_ms=None):

  if skip_samples is not None:
    skip_param = '--skip-samples'
    skip_val = skip_samples
  elif skip_ms is not None:
    skip_param = '--skip-ms'
    skip_val = skip_ms
  else:
    skip_param = '--skip-ms'
    skip_val = 0

  for prn in prns:
    samples_filename = generate_sample_file(prn, init_doppler,
                                   init_code_phase,
                                   file_format, freq_profile, generate=10)

    run_peregrine(samples_filename, file_format, freq_profile,
                  skip_param, skip_val, skip_tracking=False)

    code_phase = propagate_code_phase(init_code_phase,
                   get_sampling_freq(freq_profile),
                   skip_param, skip_val)

    check_track_results(samples_filename, prn, init_doppler, code_phase)

    # Clean-up.
    os.remove(get_acq_result_file_name(samples_filename))
    os.remove(get_track_result_file_name(samples_filename, prn))
    os.remove(samples_filename)


def check_track_results(filename, prn, doppler, code_phase):
  with open(get_track_result_file_name(filename, prn), 'rb') as f:
    track_results = cPickle.load(f)

    print "result = ", track_results
    lock_ratio = float((track_results.lock_detect_outp == 1).sum()) /\
                 len(track_results.lock_detect_outp)
    print "lock_ratio = ", lock_ratio
    assert lock_ratio > 0.1
    assert (track_results.prn + 1) == prn
    #assert track_results.status == 'T'


def test_tracking():
  """
  Test GPS L1C/A tracking
  """
  prns = range(1, 33, 5)

  # Test with different initial Doppler values
  for doppler in [-1000, 0, 1000]:
    run_track_test(doppler, 0, prns, '2bits_x2')

  # Test with different initial code phases
  # for code_phase in [0, 310, 620, 967]:
  #   run_acq_test(-2345, code_phase, prns, '2bits')

if __name__ == '__main__':
  test_tracking()

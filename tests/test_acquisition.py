# Copyright (C) 2016 Swift Navigation Inc.
#
# This source is subject to the license found in the file 'LICENSE' which must
# be be distributed together with this source. All other rights reserved.
#
# THIS CODE AND INFORMATION IS PROVIDED "AS IS" WITHOUT WARRANTY OF ANY KIND,
# EITHER EXPRESSED OR IMPLIED, INCLUDING BUT NOT LIMITED TO THE IMPLIED
# WARRANTIES OF MERCHANTABILITY AND/OR FITNESS FOR A PARTICULAR PURPOSE.

from test_common import generate_sample_file, \
                        run_peregrine,\
                        propagate_code_phase, \
                        get_sampling_freq

import os
import peregrine.acquisition as acq


def get_acq_result_file_name(sample_file):
  return sample_file + '.acq_results'


def run_acq_test(init_doppler, init_code_phase,
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
                                   file_format, freq_profile)

    run_peregrine(samples_filename, file_format, freq_profile,
                  skip_param, skip_val)

    code_phase = propagate_code_phase(init_code_phase,
                   get_sampling_freq(freq_profile),
                   skip_param, skip_val)

    if skip_val == 0:
      check_acq_results(samples_filename, prn, init_doppler, code_phase)

    # Clean-up.
    os.remove(get_acq_result_file_name(samples_filename))
    os.remove(samples_filename)


def check_acq_results(filename, prn, doppler, code_phase):
  acq_results = acq.load_acq_results(
                    get_acq_result_file_name(filename))

  acq_results = sorted(acq_results,
                       lambda x, y: -1 if x.snr > y.snr else 1)

  assert len(acq_results) != 0

  result = acq_results[0]
  print "result = ", result
  assert (result.prn + 1) == prn

  # check doppler phase estimation
  doppler_diff = abs(abs(result.doppler) - abs(doppler))
  print "doppler_diff = ", doppler_diff
  assert doppler_diff < 100.0

  # check code phase estimation
  code_phase_diff = abs(abs(result.code_phase) - abs(code_phase))
  print "code_phase_diff = ", code_phase_diff
  assert code_phase_diff < 1.0


#def test_acquisition():
#  """
#  Test GPS L1C/A acquisition
#  """
#  prns = range(1, 33, 5)
#
#  # Test with different initial Doppler values
#  for doppler in [-1000, 0, 1000]:
#    run_acq_test(doppler, 0, prns, '2bits')
#
#  # Test with different initial code phases
#  # for code_phase in [0, 310, 620, 967]:
#  #   run_acq_test(-2345, code_phase, prns, '2bits')

def test_acqusition_prn1_m1000():
  """
  Test GPS L1C/A acquisition
  """
  run_acq_test(-1000., 0., [1], '2bits')


def test_acqusition_prn32_0():
  """
  Test GPS L1C/A acquisition
  """
  run_acq_test(0., 0., [32], '2bits')


def test_acqusition_prn5_p1000():
  """
  Test GPS L1C/A acquisition
  """
  run_acq_test(1000., 0., [5], '2bits')


def test_skip_params():
  """
  Test different skip parameters:
  --skip_samples
  and
  --skip_ms

  """
  run_acq_test(1000, 0, [1], '1bit', skip_samples=1000)
  run_acq_test(1000, 0, [1], '1bit', skip_ms=50)

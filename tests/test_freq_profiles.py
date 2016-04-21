from test_acquisition import run_acq_test
from test_common import generate_piksi_sample_file
from peregrine.gps_constants import L1CA
from peregrine.samples import load_samples

import peregrine.defaults as defaults
import os

def test_freq_profiles():
  #run_acq_test(-4000, 0, [1], '2bits', 'custom_rate')
  run_acq_test(-2000, 0, [2], '2bits', 'low_rate')
  run_acq_test(2000, 0, [3], '2bits', 'normal_rate')
  run_acq_test(4000, 0, [4], '2bits', 'high_rate')

if __name__ == '__main__':
  test_freq_profiles()

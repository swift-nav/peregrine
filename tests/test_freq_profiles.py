from test_acquisition import run_acq_test
from test_common import generate_piksi_sample_file
from peregrine.gps_constants import L1CA
from peregrine.samples import load_samples

import peregrine.defaults as defaults
import os

# def test_custom_rate():
#   run_acq_test(-4000, 0, [1], '2bits', 'custom_rate')

def test_low_rate():
  run_acq_test(-2000, 0, [2], '2bits', 'low_rate')

def test_normal_rate():
  run_acq_test(2000, 0, [3], '2bits', 'normal_rate')

# Takes long time to complete in Travis CI test and
# therefore fails
# def test_high_rate():
#   run_acq_test(2000, 0, [4], '2bits', 'high_rate')

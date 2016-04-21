from test_acquisition import run_acq_test
from test_common import generate_piksi_sample_file
from peregrine.gps_constants import L1CA
from peregrine.samples import load_samples

import peregrine.defaults as defaults
import os

SAMPLE_FILE_NAME = 'sample_data_in_piksi_format.bin'

def test_file_formats():
  """
  Test different file formats:
  '1bit'
  '1bit_x2'
  '2bits'
  '2bits_x2'
  '2bits_x4'
  """
  run_acq_test(1000, 0, [1], '1bit')
  run_acq_test(1000, 0, [1], '1bit_x2')
  run_acq_test(1000, 0, [1], '2bits')
  run_acq_test(1000, 0, [1], '2bits_x2')
  run_acq_test(1000, 0, [1], '2bits_x4')

  # test 'piksi' format
  val = generate_piksi_sample_file(SAMPLE_FILE_NAME)
  samples = {
    'samples_total': -1,
    'sample_index': 0,
    L1CA: {}
  }
  for num in [-1, defaults.processing_block_size]:
    load_samples(samples, SAMPLE_FILE_NAME, num, 'piksi')
    index = 0
    for s in samples[L1CA]['samples']:
      assert s == val[index]
      index = (index + 1) % len(val)
  # clean-up
  os.remove(SAMPLE_FILE_NAME)

if __name__ == '__main__':
  test_file_formats()

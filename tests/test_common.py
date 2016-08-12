# Copyright (C) 2016 Swift Navigation Inc.
#
# This source is subject to the license found in the file 'LICENSE' which must
# be be distributed together with this source. All other rights reserved.
#
# THIS CODE AND INFORMATION IS PROVIDED "AS IS" WITHOUT WARRANTY OF ANY KIND,
# EITHER EXPRESSED OR IMPLIED, INCLUDING BUT NOT LIMITED TO THE IMPLIED
# WARRANTIES OF MERCHANTABILITY AND/OR FITNESS FOR A PARTICULAR PURPOSE.

import peregrine.run
import sys
import peregrine.iqgen.iqgen_main as iqgen
import peregrine.defaults as defaults
import peregrine.gps_constants as gps
import peregrine.glo_constants as glo
import numpy as np

from mock import patch


def fileformat_to_bands(file_format):
  profile = defaults.file_encoding_profile[file_format]
  bands = []
  for p in profile:
    if p == defaults.sample_channel_GPS_L1:
      bands += [gps.L1CA]
    elif p == defaults.sample_channel_GPS_L2:
      bands += [gps.L2C]
    elif p == defaults.sample_channel_GLO_L1:
      bands += [glo.GLO_L1]
    elif p == defaults.sample_channel_GLO_L2:
      bands += [glo.GLO_L2]
  return bands


def get_skip_params(skip_samples, skip_ms):
  if skip_samples is not None:
    skip_param = '--skip-samples'
    skip_val = skip_samples
  elif skip_ms is not None:
    skip_param = '--skip-ms'
    skip_val = skip_ms
  else:
    skip_param = '--skip-ms'
    skip_val = 0
  return (skip_param, skip_val)


def generate_2bits_x4_sample_file(filename):
  sample_block_size = 4  # [bits]
  s_file = np.memmap(filename, offset=0, dtype=np.uint8, mode='r')

  num_samples = len(s_file) * 8 / sample_block_size

  # Compute total data block size to ignore bits in the tail.
  rounded_len = num_samples * sample_block_size

  bits = np.unpackbits(s_file)
  samples = np.empty((4, num_samples), dtype=np.uint8)

  n_bits = 2  # number of bits per sample
  channel_lookup = [0, 3, 1, 2]
  for rx in range(2):
    # Construct multi-bit sample values
    chan = bits[rx * n_bits:rounded_len:sample_block_size]
    for bit in range(1, n_bits):
      chan <<= 1
      chan += bits[rx * n_bits + bit:rounded_len:sample_block_size]
    samples[channel_lookup[rx]][:] = chan
  # Store the result back to the same file
  packed = np.zeros(num_samples, dtype=np.uint8)
  packed[:] = samples[3] << 6
  packed |= samples[0] & 3
  with open(filename, 'wb') as f:
    packed.tofile(f)

  return samples


def generate_piksi_sample_file(filename):
  samples_lookup = [
      0b11111100,
      0b11011000,
      0b10110100,
      0b10010000,
      0b00000000,
      0b00100100,
      0b01001000,
      0b01101100
  ]
  samples_lookup_values = [
      -7, -7, -5, -5, -3, -3, -1, -1, 1, 1, 3, 3, 5, 5, 7, 7
  ]
  num_samples = int(1e6)
  packed = np.zeros(num_samples, dtype=np.uint8)
  for i in range(num_samples):
    packed[i] = samples_lookup[i % len(samples_lookup)]
  with open(filename, 'wb') as f:
    packed.tofile(f)

  return samples_lookup_values


def generate_sample_file(gps_sv_prn, init_doppler,
                         init_code_phase, file_format,
                         freq_profile, generate=.1):
  sample_file = 'iqgen-data-samples.bin'
  params = ['iqgen_main']
  bands = fileformat_to_bands(file_format)

  if gps.L1CA in bands or gps.L2C in bands:
    params += ['--gps-sv', str(gps_sv_prn)]

    if file_format == defaults.FORMAT_1BIT_X1_GPS_L1:
      encoder = '1bit'
      params += ['--bands', 'l1ca']
    elif file_format == defaults.FORMAT_1BIT_X2_GPS_L1L2:
      encoder = '1bit'
      params += ['--bands', 'l1ca+l2c']
    elif file_format == defaults.FORMAT_2BITS_X1_GPS_L1:
      encoder = '2bits'
      params += ['--bands', 'l1ca']
    elif file_format == defaults.FORMAT_2BITS_X2_GPS_L1L2:
      encoder = '2bits'
      params += ['--bands', 'l1ca+l2c']
    elif file_format == defaults.FORMAT_2BITS_X4_GPS_L1L2_GLO_L1L2:
      encoder = '2bits'
      params += ['--bands', 'l1ca+l2c']
    else:
      assert False
  elif glo.GLO_L1 in bands or glo.GLO_L2 in bands:
    params += ['--glo-sv', str(gps_sv_prn)]

    if file_format == defaults.FORMAT_1BIT_X1_GLO_L1:
      encoder = '1bit'
      params += ['--bands', 'l1']
    elif file_format == defaults.FORMAT_1BIT_X1_GLO_L2:
      encoder = '1bit'
      params += ['--bands', 'l2']
    elif file_format == defaults.FORMAT_1BIT_X2_GLO_L1L2:
      encoder = '1bit'
      params += ['--bands', 'l1+l2']
    elif file_format == defaults.FORMAT_2BITS_X1_GLO_L1:
      encoder = '2bits'
      params += ['--bands', 'l1']
    elif file_format == defaults.FORMAT_2BITS_X2_GLO_L1L2:
      encoder = '2bits'
      params += ['--bands', 'l1+l2']
    elif file_format == defaults.FORMAT_2BITS_X4_GPS_L1L2_GLO_L1L2:
      encoder = '2bits'
      params += ['--bands', 'l1+l2']
    else:
      assert False
  else:
    assert False

  params += ['--encoder', encoder]
  params += ['--doppler-type', 'const']
  params += ['--doppler-value', str(init_doppler)]
  params += ['--message-type', 'crc']
  params += ['--chip-delay', str(-init_code_phase)]
  params += ['--symbol-delay', '0']
  params += ['--amplitude-type', 'poly']
  params += ['--amplitude-units', 'snr-db']
  params += ['--amplitude-a0', '-5']
  params += ['--generate', str(generate)]
  params += ['--output', sample_file]
  params += ['--profile', freq_profile]
  params += ['-j 4']
  print params
  with patch.object(sys, 'argv', params):
    iqgen.main()

  if file_format == '2bits_x4':
    generate_2bits_x4_sample_file(sample_file)

  return sample_file


def run_peregrine(file_name, file_format, freq_profile,
                  skip_param, skip_val,
                  skip_tracking=True,
                  skip_navigation=True,
                  short_long_cycles=False):

  parameters = [
      'peregrine',
      '--file', file_name,
      '--file-format', file_format,
      '--profile', freq_profile,
      skip_param, str(skip_val),
      '--progress-bar', 'stdout'
  ]
  if skip_tracking:
    parameters += ['-t']

  if skip_navigation:
    parameters += ['-n']

  if short_long_cycles:
    parameters += ['--short-long-cycles']

  # Replace argv with args to skip tracking and navigation.
  with patch.object(sys, 'argv', parameters):
    print "sys.argv = ", sys.argv
    peregrine.run.main()


def propagate_code_phase(code_phase, sampling_freq, skip_param, skip_val):
  if skip_param == '--skip-samples':
    skip_samples = skip_val
  else:
    samples_per_ms = sampling_freq / 1e3
    skip_samples = skip_val * samples_per_ms

  samples_per_chip = sampling_freq / gps.l1ca_chip_rate
  code_phase += skip_samples / samples_per_chip

  return code_phase


def get_sampling_freq(freq_profile_name):
  freq_profile = defaults.freq_profile_lookup[freq_profile_name]
  return freq_profile['sampling_freq']

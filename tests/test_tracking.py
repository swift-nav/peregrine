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

from peregrine.gps_constants import l1, l2, L1CA, L2C
from test_common import generate_sample_file, fileformat_to_bands,\
                        get_skip_params, run_peregrine
from test_acquisition import get_acq_result_file_name
from peregrine.analysis import tracking_loop
from peregrine.tracking import TrackingLoop, NavBitSync, NavBitSyncSBAS,\
                               NBSLibSwiftNav, NBSSBAS, NBSMatchBit,\
                               NBSHistogram, NBSMatchEdge

import cPickle
import csv
import os
import sys

from mock import patch


def run_tracking_loop(prn, signal, dopp, phase, file_name, file_format,
                      freq_profile, skip_val, norun=False, l2chandover=False,
                      pipelining=None, short_long_cycles=None):
  parameters = [
    'tracking_loop',
    '-P', str(prn),
    '-p', str(phase),
    '-d', str(dopp),
    '-S', signal,
    '--file', file_name,
    '--file-format', file_format,
    '--profile', freq_profile,
    '--skip-samples', str(skip_val)
  ]

  if pipelining:
    parameters += ['--pipelining', str(pipelining)]
  elif short_long_cycles:
    parameters += ['--short-long-cycles', str(short_long_cycles)]

  if norun:
    parameters.append('--no-run')

  if l2chandover:
    parameters.append('--l2c-handover')

  # Replace argv with args to skip tracking and navigation.
  with patch.object(sys, 'argv', parameters):
    print "sys.argv = ", sys.argv
    tracking_loop.main()


def get_track_result_file_name(sample_file, prn, band):
  sample_file, sample_file_extension = os.path.splitext(sample_file)
  return (sample_file + (".PRN-%d.%s" % (prn, band)) +
         sample_file_extension + '.track_results',
         "track.PRN-%d.%s.csv" % (prn, band))


def get_peregrine_tr_res_file_name(sample_file, prn, band):
  per_fn, tr_loop_fn = get_track_result_file_name(sample_file, prn, band)
  return per_fn


def get_tr_loop_res_file_name(sample_file, prn, band):
  per_fn, tr_loop_fn = get_track_result_file_name(sample_file, prn, band)
  return tr_loop_fn


def run_track_test(samples_file, expected_lock_ratio, init_doppler,
                   init_code_phase, prn, file_format, freq_profile,
                   skip_samples=None, skip_ms=None,
                   pipelining=None, short_long_cycles=None):

  bands = fileformat_to_bands(file_format)

  skip_param, skip_val = get_skip_params(skip_samples, skip_ms)

  run_peregrine(samples_file, file_format, freq_profile,
                skip_param, skip_val, skip_tracking=False,
                pipelining=pipelining, short_long_cycles=short_long_cycles)

  for band in bands:
    dopp_ratio = 1
    if band == "l2c":
      dopp_ratio = l2 / l1
    run_tracking_loop(prn, band, init_doppler * dopp_ratio, init_code_phase,
                      samples_file, file_format, freq_profile, 0,
                      pipelining=pipelining,
                      short_long_cycles=short_long_cycles)

  #code_phase = propagate_code_phase(init_code_phase,
                 #get_sampling_freq(freq_profile),
                 #skip_param, skip_val)

  check_per_track_results(expected_lock_ratio, samples_file, prn, bands,
                          pipelining, short_long_cycles)

  check_tr_loop_track(expected_lock_ratio, samples_file, prn, bands,
                      pipelining, short_long_cycles)

  # Clean-up.
  os.remove(get_acq_result_file_name(samples_file))
  for band in bands:
    os.remove(get_peregrine_tr_res_file_name(samples_file, prn, band))
    os.remove(get_tr_loop_res_file_name(samples_file, prn, band))


def check_per_track_results(expected_lock_ratio, filename, prn, bands,
                            pipelining, short_long_cycles):
  ret = {}
  print "Peregrine tracking:"
  for band in bands:
    ret[band] = {}
    with open(get_peregrine_tr_res_file_name(filename, prn, band), 'rb') as f:
      lock_detect_outp_sum = 0
      lock_detect_outp_len = 0
      while True:
        try:
          track_results = cPickle.load(f)
          assert (track_results.prn + 1) == prn
          assert track_results.status == 'T'
          assert track_results == track_results
          lock_detect_outp_sum += (track_results.lock_detect_outp == 1).sum()
          lock_detect_outp_len += len(track_results.lock_detect_outp)
          assert track_results.resize(1) == track_results.resize(1)
        except EOFError:
          break
      print "band =", band
      lock_ratio = float(lock_detect_outp_sum) / lock_detect_outp_len
      print "lock_ratio =", lock_ratio
      if (not short_long_cycles and not pipelining) or band != L2C:
        assert lock_ratio >= expected_lock_ratio
      ret[band]['lock_ratio'] = lock_ratio
  return ret


def check_tr_loop_track(expected_lock_ratio, filename, prn, bands,
                        pipelining, short_long_cycles):
  ret = {}
  print "Tracking loop:"
  for band in bands:
    ret[band] = {}
    with open(get_tr_loop_res_file_name(filename, prn, band), 'rb') as f:
      reader = csv.reader(f)
      hdr = reader.next()
      ldo_idx = hdr.index("lock_detect_outp")
      lock_detect_outp_sum = 0
      lock_detect_outp_len = 0
      for row in reader:
        lock_detect_outp_len += 1
        lock_detect_outp_sum += int(row[ldo_idx])
      print "band =", band
      lock_ratio = float(lock_detect_outp_sum) / lock_detect_outp_len
      print "lock_ratio =", lock_ratio
      if (not short_long_cycles and not pipelining) or band != L2C:
        assert lock_ratio >= expected_lock_ratio
      ret[band]['lock_ratio'] = lock_ratio
  return ret


def test_tracking():
  """
  Test GPS L1C/A and L2C tracking
  """

  prn = 1
  init_doppler = 555
  init_code_phase = 0
  file_format = '2bits_x2'
  freq_profile = 'low_rate'

  samples = generate_sample_file(prn, init_doppler,
                                 init_code_phase,
                                 file_format, freq_profile, generate=5)

  run_track_test(samples, 0.6, init_doppler, init_code_phase, prn, file_format,
    freq_profile)
  run_track_test(samples, 0.3, init_doppler, init_code_phase, prn, file_format,
    freq_profile, pipelining=0.5)
  run_track_test(samples, 0.3, init_doppler, init_code_phase, prn, file_format,
    freq_profile, short_long_cycles=0.5)

  os.remove(samples)

  # test --no-run
  run_tracking_loop(1, L1CA, 0, 0, 'dummy', '2bits_x2', 'low_rate', 0,
                    norun=True)

  # Test with different initial code phases
  # for code_phase in [0, 310, 620, 967]:
  #   run_acq_test(-2345, code_phase, prns, '2bits')

  try:
    TrackingLoop().start(None, None,)
    assert False
  except NotImplementedError:
    pass

  try:
    TrackingLoop().update(None, None, None)
    assert False
  except NotImplementedError:
    pass

  try:
    NavBitSync().update_bit_sync(0, 0)
    assert False
  except NotImplementedError:
    pass

  nvb = NavBitSync()
  # Test ._equal
  nvb.synced = True
  assert NavBitSync() != nvb
  nvb.dummy = 'dummy'
  assert NavBitSync() != nvb

  # Test constructors
  assert NBSMatchBit()
  assert NavBitSyncSBAS()
  assert NBSSBAS()
  assert NBSLibSwiftNav()
  assert NBSHistogram()
  assert NBSMatchEdge()


if __name__ == '__main__':
  test_tracking()

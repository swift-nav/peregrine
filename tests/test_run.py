# Copyright (C) 2016 Swift Navigation Inc.
#
# This source is subject to the license found in the file 'LICENSE' which must
# be be distributed together with this source. All other rights reserved.
#
# THIS CODE AND INFORMATION IS PROVIDED "AS IS" WITHOUT WARRANTY OF ANY KIND,
# EITHER EXPRESSED OR IMPLIED, INCLUDING BUT NOT LIMITED TO THE IMPLIED
# WARRANTIES OF MERCHANTABILITY AND/OR FITNESS FOR A PARTICULAR PURPOSE.

import peregrine.run
import peregrine.iqgen.iqgen_main as iqgen
import sys
import os
import peregrine.acquisition as acq
import peregrine.gps_constants as gps
import peregrine.glo_constants as glo

from mock import patch

SAMPLES_PATH = 'tests/test_data/'
# todo: the gpsl1ca_ci_samples.piksi_format.acq_results
# should replace the old file with the same name at the
# remote server, where the script takes it from.
# For now, let's use the local version.
#RES_PATH = SAMPLES_PATH + '/results/'
RES_PATH = 'tests/'

SAMPLES_FNAME = 'gpsl1ca_ci_samples.piksi_format'

SAMPLES = SAMPLES_PATH + SAMPLES_FNAME

OLD_TRK_RES = RES_PATH + SAMPLES_FNAME + '.track_results'
OLD_NAV_RES = RES_PATH + SAMPLES_FNAME + '.nav_results'

# run.py deposits results in same location as samples
NEW_TRK_RES = SAMPLES_PATH + SAMPLES_FNAME + '.track_results'
NEW_NAV_RES = SAMPLES_PATH + SAMPLES_FNAME + '.nav_results'


def generate_sample_file(gps_sv_prn, glo_ch, init_doppler, init_code_phase):
  sample_file = 'iqgen-data-samples.bin'
  freq_profile = 'normal_rate'
  params = ['iqgen_main']
  # GPS
  params += ['--gps-sv', str(gps_sv_prn)]
  params += ['--bands', 'l1ca']
  params += ['--doppler-type', 'const']
  params += ['--doppler-value', str(init_doppler)]
  params += ['--tec', '0']
  params += ['--distance', '0']
  params += ['--chip_delay', str(init_code_phase)]
  params += ['--amplitude-type', 'poly']
  params += ['--amplitude-units', 'snr-db']
  params += ['--amplitude-a0', '-17']
  # GLO
  params += ['--glo-sv', str(glo_ch)]
  params += ['--bands', 'l1']
  params += ['--doppler-type', 'const']
  params += ['--doppler-value', str(init_doppler)]
  params += ['--tec', '0']
  params += ['--distance', '0']
  params += ['--message-type', 'crc']
  params += ['--chip_delay', str(init_code_phase)]
  params += ['--amplitude-type', 'poly']
  params += ['--amplitude-units', 'snr-db']
  params += ['--amplitude-a0', '-17']
  # common
  params += ['--generate', '1']
  params += ['--encoder', '2bits']
  params += ['--output', sample_file]
  params += ['--profile', freq_profile]
  params += ['-j', '4']
  print params
  with patch.object(sys, 'argv', params):
    iqgen.main()

  return {'sample_file': sample_file,
          'file_format': '2bits_x4',
          'freq_profile': freq_profile}


def get_acq_result_file_name(sample_file):
  return sample_file + '.acq_results'


def run_acq_test(init_doppler, init_code_phase):
  for ch in xrange(-7, 6):
    prn = (ch + 8) * 2
    samples = generate_sample_file(prn, ch, init_doppler, init_code_phase)

    # Replace argv with args to skip tracking and navigation.
    with patch.object(sys, 'argv',
                      ['peregrine',
                       '--file', samples['sample_file'],
                       '--file-format', samples['file_format'],
                       '--profile', samples['freq_profile'],
                       '-t', '-n']):

      try:
        peregrine.run.main()
      except SystemExit:
        # Thrown if track and nav results files are not present and we
        # supplied command line args to skip tracking and navigation.
        pass

      acq_results = acq.load_acq_results(
                        get_acq_result_file_name(samples['sample_file']))

      glo_res = []
      gps_res = []
      for res in acq_results:
        if isinstance(res, acq.GloAcquisitionResult):
          glo_res.append(res)
        else:
          gps_res.append(res)
      glo_res = sorted(glo_res, lambda x, y: -1 if x.snr > y.snr else 1)
      gps_res = sorted(gps_res, lambda x, y: -1 if x.snr > y.snr else 1)

      def check_result(res):
        assert len(res) != 0

        result = res[0]
        print "result = ", result
        if isinstance(result, acq.GloAcquisitionResult):
          assert (result.prn) == ch
          code_length = glo.glo_code_len
        else:
          assert (result.prn + 1) == prn
          code_length = gps.l1ca_code_length

        # check doppler phase estimation
        doppler_diff = abs(abs(result.doppler) - abs(init_doppler))
        print "doppler_diff = ", doppler_diff
        assert doppler_diff < 200.0

        # check code phase estimation
        code_phase = result.code_phase
        if code_phase > code_length / 2:
          code_phase = code_phase - code_length
        code_phase_diff = abs(abs(code_phase) - abs(init_code_phase))
        print "code_phase_diff = ", code_phase_diff
        assert code_phase_diff < 1.0

      check_result(glo_res)
      check_result(gps_res)

      # Clean-up.
      os.remove(get_acq_result_file_name(samples['sample_file']))
      os.remove(samples['sample_file'])


def test_acquisition():
  run_acq_test(775, 0)

# def test_tracking():

#   # Replace argv with args to skip acquisition and navigation.
#   with patch.object(sys, 'argv', ['peregrine', SAMPLES, '-a', '-n']):

#     # Copy reference acq results to use in order to skip acquisition.
#     copyfile(OLD_ACQ_RES, NEW_ACQ_RES)

#     try:
#       peregrine.run.main()
#     except SystemExit:
#       # Thrown if nav results file is not present and we supplied
#       # command line arg to skip navigation.
#       pass

#     # Comparison not working on Travis at the moment, needs further debugging.
#     # Simply make sure tracking runs successfully for now.
#     #with open(NEW_TRK_RES, 'rb') as f:
#     #  new_trk_results = cPickle.load(f)
#     #with open(OLD_TRK_RES, 'rb') as f:
#     #  old_trk_results = cPickle.load(f)
#     #assert new_trk_results == old_trk_results

#     # Clean-up.
#     os.remove(NEW_ACQ_RES)
#     #os.remove(NEW_TRK_RES)

# if __name__ == '__main__':
#   test_acquisition()

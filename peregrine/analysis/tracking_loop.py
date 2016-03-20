# Copyright (C) 2016 Swift Navigation Inc.
# Contact: Adel Mamin <adelm@exafore.com>
#
# This source is subject to the license found in the file 'LICENSE' which must
# be be distributed together with this source. All other rights reserved.
#
# THIS CODE AND INFORMATION IS PROVIDED "AS IS" WITHOUT WARRANTY OF ANY KIND,
# EITHER EXPRESSED OR IMPLIED, INCLUDING BUT NOT LIMITED TO THE IMPLIED
# WARRANTIES OF MERCHANTABILITY AND/OR FITNESS FOR A PARTICULAR PURPOSE.

import os
import argparse
from peregrine.samples import load_samples
from peregrine.acquisition import AcquisitionResult
from peregrine import defaults
from peregrine.log import default_logging_config
import peregrine.tracking as tracking
from peregrine.gps_constants import L1CA, L2C
from peregrine.initSettings import initSettings

def main():
  default_logging_config()

  parser = argparse.ArgumentParser()
  parser.add_argument("file",
                      help="the sample data file to process")

  parser.add_argument("-f", "--file-format",
                      help="the format of the sample data file "
                      "('piksi', 'int8', '1bit', '1bitrev', "
                      "'1bit_x2', '2bits', '2bits_x2', '2bits_x4')")

  parser.add_argument("-t", "--ms-to-track",
                      help="the number of milliseconds to track."
                      "(-1: use all available data",
                      default="-1")

  parser.add_argument("-s", "--sampling-freq",
                      help="sampling frequency [Hz]. ")

  parser.add_argument("--profile",
                      help="L1C/A & L2C IF + sampling frequency profile"
                      "('peregrine'/'custom_rate', 'low_rate', "
                      "'normal_rate' (piksi_v3), 'high_rate')",
                      default='peregrine')

  parser.add_argument("-P", "--prn",
                      help="PRN to track. ")

  parser.add_argument("-p", "--code-phase",
                      help="code phase [chips]. ")

  parser.add_argument("-d", "--carr-doppler",
                      help="carrier Doppler frequency [Hz]. ")

  parser.add_argument("-o", "--output-file", default="track.csv",
                      help="Track results file name. "
                      "Default: %s" % "track.csv")

  parser.add_argument("-S", "--signal",
                      choices=[L1CA, L2C],
                      help="Signal type (l1ca / l2c)")

  parser.add_argument("--l2c-handover",
                      action='store_true',
                      help="Perform L2C handover",
                      default=False)

  parser.add_argument('--l1ca-profile',
                      help='L1 C/A stage profile',
                      choices=defaults.l1ca_stage_profiles.keys())

  parser.add_argument("--pipelining",
                      type=float,
                      nargs='?',
                      help="FPGA pipelining coefficient",
                      const=defaults.pipelining_k,
                      default=None)

  parser.add_argument("--skip-samples", default=0,
                      help="How many samples to skip")

  args = parser.parse_args()

  if args.file is None:
    parser.print_help()
    return

  skip_samples = int(args.skip_samples)

  if args.profile == 'peregrine' or args.profile == 'custom_rate':
    freq_profile = defaults.freq_profile_peregrine
  elif args.profile == 'low_rate':
    freq_profile = defaults.freq_profile_low_rate
  elif args.profile == 'normal_rate':
    freq_profile = defaults.freq_profile_normal_rate
  elif args.profile == 'high_rate':
    freq_profile = defaults.freq_profile_high_rate
  else:
    raise NotImplementedError()

  isL1CA = (args.signal == L1CA)
  isL2C = (args.signal == L2C)

  if isL1CA:
    signal = L1CA
    IF = freq_profile['GPS_L1_IF']
  elif isL2C:
    signal = L2C
    IF = freq_profile['GPS_L2_IF']
  else:
    raise NotImplementedError()

  if args.l2c_handover and not isL2C:
    l2c_handover = True
  else:
    l2c_handover = False

  if args.sampling_freq is not None:
    sampling_freq = float(args.sampling_freq)  # [Hz]
  else:
    sampling_freq = freq_profile['sampling_freq']  # [Hz]

  # Initialize constants, settings
  settings = initSettings(freq_profile)

  settings.fileName = args.file

  carr_doppler = float(args.carr_doppler)
  code_phase = float(args.code_phase)
  prn = int(args.prn) - 1

  ms_to_track = int(args.ms_to_track)

  if args.pipelining is not None:
    tracker_options = {'mode': 'pipelining', 'k': args.pipelining}
  else:
    tracker_options = None

  acq_result = AcquisitionResult(prn = prn,
                    snr = 25, # dB
                    carr_freq = IF + carr_doppler,
                    doppler = carr_doppler,
                    code_phase = code_phase,
                    status = 'A',
                    signal = signal,
                    sample_index = 0)

  if args.l1ca_profile:
    profile = defaults.l1ca_stage_profiles[args.l1ca_profile]
    stage2_coherent_ms = profile[1]['coherent_ms']
    stage2_params = profile[1]['loop_filter_params']
  else:
    stage2_coherent_ms = None
    stage2_params = None

  samples = {L1CA: {'IF': freq_profile['GPS_L1_IF']},
              L2C: {'IF': freq_profile['GPS_L2_IF']},
             'samples_total': -1,
             'sample_index': 0}

  samples = load_samples(samples = samples,
                         sample_index = 0,
                         filename = args.file,
                         file_format = args.file_format)

  if ms_to_track < 0:
    # use all available data
    ms_to_track = int(1e3 * samples['samples_total'] / sampling_freq)

  print "==================== Tracking parameters ============================="
  print "File:                                   %s" % args.file
  print "File format:                            %s" % args.file_format
  print "PRN to track [1-32]:                    %s" % args.prn
  print "Time to process [ms]:                   %s" % ms_to_track
  print "L1 IF [Hz]:                             %f" % freq_profile['GPS_L1_IF']
  print "L2 IF [Hz]:                             %f" % freq_profile['GPS_L2_IF']
  print "Sampling frequency [Hz]:                %f" % sampling_freq
  print "Initial carrier Doppler frequency [Hz]: %s" % carr_doppler
  print "Initial code phase [chips]:             %s" % code_phase
  print "Signal:                                 %s" % args.signal
  print "L1 stage profile:                       %s" % args.l1ca_profile
  print "Tracker options:                        %s" % str(tracker_options)
  print "======================================================================"

  tracker = tracking.Tracker(samples = samples,
                    channels = [acq_result],
                    ms_to_track = ms_to_track,
                    sampling_freq = sampling_freq,  # [Hz]
                    l2c_handover = l2c_handover,
                    stage2_coherent_ms = stage2_coherent_ms,
                    stage2_loop_filter_params = stage2_params,
                    tracker_options = tracker_options,
                    output_file = args.output_file)
  tracker.start()
  condition = True
  while condition:
    sample_index = tracker.run_channels(samples)
    if sample_index == samples['sample_index']:
      condition = False
    else:
      samples = load_samples(samples = samples,
                             sample_index = sample_index,
                             filename = args.file,
                             file_format = args.file_format)
  tracker.stop()

if __name__ == '__main__':
  main()

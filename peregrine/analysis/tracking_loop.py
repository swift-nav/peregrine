#!/usr/bin/env python

# Copyright (C) 2016 Swift Navigation Inc.
# Contact: Adel Mamin <adelm@exafore.com>
#
# This source is subject to the license found in the file 'LICENSE' which must
# be be distributed together with this source. All other rights reserved.
#
# THIS CODE AND INFORMATION IS PROVIDED "AS IS" WITHOUT WARRANTY OF ANY KIND,
# EITHER EXPRESSED OR IMPLIED, INCLUDING BUT NOT LIMITED TO THE IMPLIED
# WARRANTIES OF MERCHANTABILITY AND/OR FITNESS FOR A PARTICULAR PURPOSE.

import argparse
import sys
from peregrine.samples import load_samples
from peregrine.acquisition import AcquisitionResult
from peregrine import defaults
from peregrine.log import default_logging_config
from peregrine.tracking import Tracker
from peregrine.gps_constants import L1CA, L2C
from peregrine.initSettings import initSettings


def main():
  default_logging_config()

  parser = argparse.ArgumentParser()

  if sys.stdout.isatty():
    progress_bar_default = 'stdout'
  elif sys.stderr.isatty():
    progress_bar_default = 'stderr'
  else:
    progress_bar_default = 'none'

  parser.add_argument("--progress-bar",
                      metavar='FLAG',
                      choices=['stdout', 'stderr', 'none'],
                      default=progress_bar_default,
                      help="Show progress bar. Default is '%s'" %
                      progress_bar_default)

  inputCtrl = parser.add_argument_group('Data Source',
                                        'Data source configuration')
  inputCtrl.add_argument("file",
                         help="The sample data file to process")

  inputCtrl.add_argument("-f", "--file-format",
                         choices=['piksi', 'int8', '1bit', '1bitrev',
                                  '1bit_x2', '2bits', '2bits_x2', '2bits_x4'],
                         metavar='FORMAT',
                         help="The format of the sample data file "
                         "('piksi', 'int8', '1bit', '1bitrev', "
                         "'1bit_x2', '2bits', '2bits_x2', '2bits_x4')")

  inputCtrl.add_argument("-t", "--ms-to-track",
                         metavar='MS',
                         help="the number of milliseconds to track."
                         "(-1: use all available data",
                         default="-1")

  inputCtrl.add_argument("--skip-samples",
                         default=0,
                         metavar='N_SAMPLES',
                         help="How many samples to skip")

  inputCtrl.add_argument("-s",
                         "--sampling-freq",
                         metavar='FREQ',
                         help="Sampling frequency [Hz]. ")

  inputCtrl.add_argument("--profile",
                         choices=['peregrine', 'custom_rate', 'low_rate',
                                  'normal_rate', 'piksi_v3', 'high_rate'],
                         metavar='PROFILE',
                         help="L1C/A & L2C IF + sampling frequency profile"
                         "('peregrine'/'custom_rate', 'low_rate', "
                         "'normal_rate', 'piksi_v3', 'high_rate')",
                         default='peregrine')

  signalParam = parser.add_argument_group('Signal tracking',
                                          'Parameters for satellite vehicle'
                                          ' signal')

  signalParam.add_argument("-P", "--prn",
                           help="PRN to track. ")

  signalParam.add_argument("-p", "--code-phase",
                           metavar='CHIPS',
                           help="Code phase [chips]. ")

  signalParam.add_argument("-d", "--carr-doppler",
                           metavar='DOPPLER',
                           help="carrier Doppler frequency [Hz]. ")

  signalParam.add_argument("-S", "--signal",
                           choices=[L1CA, L2C],
                           metavar='BAND',
                           help="Signal type (l1ca / l2c)")
  signalParam.add_argument("--l2c-handover",
                           action='store_true',
                           help="Perform L2C handover",
                           default=False)
  signalParam.add_argument('--l1ca-profile',
                           metavar='PROFILE',
                           help='L1 C/A stage profile. Controls coherent'
                                ' integration time and tuning parameters: %s.' %
                                str(defaults.l1ca_stage_profiles.keys()),
                           choices=defaults.l1ca_stage_profiles.keys())

  fpgaSim = parser.add_argument_group('FPGA simulation',
                                      'FPGA delay control simulation')
  fpgaExcl = fpgaSim.add_mutually_exclusive_group(required=False)
  fpgaExcl.add_argument("--pipelining",
                        type=float,
                        nargs='?',
                        metavar='PIPELINING_K',
                        help="Use FPGA pipelining simulation. Supply optional "
                        " coefficient (%f)" % defaults.pipelining_k,
                        const=defaults.pipelining_k,
                        default=None)

  fpgaExcl.add_argument("--short-long-cycles",
                        type=float,
                        nargs='?',
                        metavar='PIPELINING_K',
                        help="Use FPGA short-long cycle simulation. Supply"
                        " optional pipelining coefficient (0.)",
                        const=0.,
                        default=None)

  outputCtrl = parser.add_argument_group('Output parameters',
                                         'Parameters that control output'
                                         ' data stream.')
  outputCtrl.add_argument("-o", "--output-file",
                          default="track.csv",
                          help="Track results file name. Default: %s" %
                               "track.csv")

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
    tracker_options = {'mode': 'pipelining',
                       'k': args.pipelining}
  elif args.short_long_cycles is not None:
    tracker_options = {'mode': 'short-long-cycles',
                       'k': args.short_long_cycles}
  else:
    tracker_options = None

  acq_result = AcquisitionResult(prn=prn,
                                 snr=25,  # dB
                                 carr_freq=IF + carr_doppler,
                                 doppler=carr_doppler,
                                 code_phase=code_phase,
                                 status='A',
                                 signal=signal,
                                 sample_index=skip_samples)

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
             'sample_index': skip_samples}

  load_samples(samples=samples,
               filename=args.file,
               file_format=args.file_format)

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

  tracker = Tracker(samples=samples,
                    channels=[acq_result],
                    ms_to_track=ms_to_track,
                    sampling_freq=sampling_freq,  # [Hz]
                    l2c_handover=l2c_handover,
                    stage2_coherent_ms=stage2_coherent_ms,
                    stage2_loop_filter_params=stage2_params,
                    tracker_options=tracker_options,
                    output_file=args.output_file,
                    progress_bar_output=args.progress_bar)
  tracker.start()
  condition = True
  while condition:
    sample_index = tracker.run_channels(samples)
    if sample_index == samples['sample_index']:
      condition = False
    else:
      samples['sample_index'] = sample_index
      load_samples(samples=samples,
                   filename=args.file,
                   file_format=args.file_format)
  tracker.stop()

if __name__ == '__main__':
  main()

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

from peregrine.samples import load_samples
from peregrine.acquisition import AcquisitionResult
from peregrine import defaults
from peregrine.log import default_logging_config
from peregrine.tracking import Tracker
from peregrine.gps_constants import L1CA, L2C
from peregrine.glo_constants import GLO_L1, GLO_L2, glo_l1_step, glo_l2_step
from peregrine.run import populate_peregrine_cmd_line_arguments
from peregrine.tracking_loop import TrackingLoop3, TrackingLoop3b, TrackingLoop2b


def main():
  default_logging_config()

  parser = argparse.ArgumentParser()

  signalParam = populate_peregrine_cmd_line_arguments(parser)

  signalParam.add_argument("-P", "--prn",
                           help="PRN to track. ")

  signalParam.add_argument("-p", "--code-phase",
                           metavar='CHIPS',
                           help="Code phase [chips]. ")

  signalParam.add_argument("-d", "--carr-doppler",
                           metavar='DOPPLER',
                           help="carrier Doppler frequency [Hz]. ")

  signalParam.add_argument("-S", "--signal",
                           choices=[L1CA, L2C, GLO_L1, GLO_L2],
                           metavar='BAND',
                           help="Signal type (l1ca, l2c, glo_l1, glo_l2)")
  signalParam.add_argument("--l2c-handover",
                           action='store_true',
                           help="Perform L2C handover",
                           default=False)

  outputCtrl = parser.add_argument_group('Output parameters',
                                         'Parameters that control output'
                                         ' data stream.')
  outputCtrl.add_argument("-o", "--output-file",
                          default="track.csv",
                          help="Track results file name. Default: %s" %
                               "track.csv")

  args = parser.parse_args()

  if args.no_run:
    return 0

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

  isL1CA = (args.signal == L1CA)
  isL2C = (args.signal == L2C)
  isGLO_L1 = (args.signal == GLO_L1)
  isGLO_L2 = (args.signal == GLO_L2)

  if isL1CA:
    signal = L1CA
    IF = freq_profile['GPS_L1_IF']
    prn = int(args.prn) - 1
  elif isL2C:
    signal = L2C
    IF = freq_profile['GPS_L2_IF']
    prn = int(args.prn) - 1
  elif isGLO_L1:
    signal = GLO_L1
    IF = freq_profile['GLO_L1_IF'] + glo_l1_step * int(args.prn)
    prn = int(args.prn)
  elif isGLO_L2:
    signal = GLO_L2
    IF = freq_profile['GLO_L2_IF'] + glo_l2_step * int(args.prn)
    prn = int(args.prn)
  else:
    raise NotImplementedError()

  if args.l2c_handover and not isL2C:
    l2c_handover = True
  else:
    l2c_handover = False

  sampling_freq = freq_profile['sampling_freq']  # [Hz]

  carr_doppler = float(args.carr_doppler)
  code_phase = float(args.code_phase)

  ms_to_process = int(args.ms_to_process)

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
             GLO_L1: {'IF': freq_profile['GLO_L1_IF']},
             GLO_L2: {'IF': freq_profile['GLO_L2_IF']},
             'samples_total': -1,
             'sample_index': skip_samples}

  load_samples(samples=samples,
               filename=args.file,
               file_format=args.file_format)

  if ms_to_process < 0:
    # use all available data
    ms_to_process = 1e3 * samples['samples_total'] / sampling_freq

  print "==================== Tracking parameters ============================="
  print "File:                                   %s" % args.file
  print "File format:                            %s" % args.file_format
  print "PRN to track [1-32]:                    %s" % args.prn
  print "Time to process [s]:                    %s" % (ms_to_process / 1e3)
  print "GPS L1 IF [Hz]:                         %f" % freq_profile['GPS_L1_IF']
  print "GPS L2 IF [Hz]:                         %f" % freq_profile['GPS_L2_IF']
  print "GLO L1 IF [Hz]:                         %f" % freq_profile['GLO_L1_IF']
  print "GLO L2 IF [Hz]:                         %f" % freq_profile['GLO_L2_IF']
  print "Sampling frequency [Hz]:                %f" % sampling_freq
  print "Initial carrier Doppler frequency [Hz]: %s" % carr_doppler
  print "Initial code phase [chips]:             %s" % code_phase
  print "Signal:                                 %s" % args.signal
  print "L1 stage profile:                       %s" % args.l1ca_profile
  print "Tracker options:                        %s" % str(tracker_options)
  print "L2C handover:                           %s" % str(l2c_handover)
  print "======================================================================"

  tracker = Tracker(samples=samples,
                    channels=[acq_result],
                    ms_to_track=ms_to_process,
                    sampling_freq=sampling_freq,  # [Hz]
                    l2c_handover=l2c_handover,
                    stage2_coherent_ms=stage2_coherent_ms,
                    stage2_loop_filter_params=stage2_params,
                    tracker_options=tracker_options,
                    output_file=args.output_file,
                    progress_bar_output=args.progress_bar)
#                    loop_filter_class=TrackingLoop2b)
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

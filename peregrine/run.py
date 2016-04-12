#!/usr/bin/env python

# Copyright (C) 2012 Swift Navigation Inc.
#
# This source is subject to the license found in the file 'LICENSE' which must
# be be distributed together with this source. All other rights reserved.
#
# THIS CODE AND INFORMATION IS PROVIDED "AS IS" WITHOUT WARRANTY OF ANY KIND,
# EITHER EXPRESSED OR IMPLIED, INCLUDING BUT NOT LIMITED TO THE IMPLIED
# WARRANTIES OF MERCHANTABILITY AND/OR FITNESS FOR A PARTICULAR PURPOSE.

import sys
import argparse
import cPickle
import logging
import numpy as np
from operator import attrgetter

from peregrine.samples import load_samples
from peregrine.acquisition import Acquisition, load_acq_results,\
                                  save_acq_results
from peregrine.navigation import navigation
import peregrine.tracking as tracking
from peregrine.log import default_logging_config
from peregrine import defaults
from peregrine.initSettings import initSettings
from peregrine.gps_constants import L1CA, L2C, GLO_L1


def unpickle_iter(filenames):
  try:
    f = [open(filename, "r") for filename in filenames]

    while True:
      yield [cPickle.load(fh) for fh in f]

  except EOFError:
    raise StopIteration

  finally:
    for fh in f:
      fh.close()


def main():
  default_logging_config()

  parser = argparse.ArgumentParser()
  parser.add_argument("file",
                      help="the sample data file to process")
  parser.add_argument("--skip-glonass",
                      help="skip glonass",
                      action="store_true")
  parser.add_argument("-a", "--skip-acquisition",
                      help="use previously saved acquisition results",
                      action="store_true")
  parser.add_argument("-t", "--skip-tracking",
                      help="use previously saved tracking results",
                      action="store_true")
  parser.add_argument("-n", "--skip-navigation",
                      help="use previously saved navigation results",
                      action="store_true")
  parser.add_argument("--ms-to-process",
                      help="the number of milliseconds to process."
                      "(-1: use all available data",
                      default="-1")
  parser.add_argument("--profile",
                      help="L1C/A & L2C IF + sampling frequency profile"
                      "('peregrine'/'custom_rate', 'low_rate', "
                      "'normal_rate' (piksi_v3), 'high_rate')",
                      default='peregrine')
  parser.add_argument("-f", "--file-format", default=defaults.file_format,
                      help="the format of the sample data file "
                      "('piksi', 'int8', '1bit', '1bitrev', "
                      "'1bit_x2', '2bits', '2bits_x2', '2bits_x4')")
  parser.add_argument('--l1ca-profile',
                      help='L1 C/A stage profile',
                      choices=defaults.l1ca_stage_profiles.keys())
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

  fpgaSim = parser.add_argument_group('FPGA simulation',
                                      'FPGA delay control simulation')

  fpgaSim.add_argument("--pipelining",
                       type=float,
                       nargs='?',
                       help="Use FPGA pipelining simulation. Supply optional "
                       " coefficient (%f)" % defaults.pipelining_k,
                       const=defaults.pipelining_k,
                       default=None)

  fpgaSim.add_argument("--short-long-cycles",
                       type=float,
                       nargs='?',
                       help="Use FPGA short-long cycle simulation. Supply"
                       " optional pipelining coefficient (0.)",
                       const=0.,
                       default=None)
  args = parser.parse_args()

  if args.file is None:
    parser.print_help()
    return

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

  if args.l1ca_profile:
    profile = defaults.l1ca_stage_profiles[args.l1ca_profile]
    stage2_coherent_ms = profile[1]['coherent_ms']
    stage2_params = profile[1]['loop_filter_params']
  else:
    stage2_coherent_ms = None
    stage2_params = None

  if args.pipelining is not None:
    tracker_options = {'mode': 'pipelining', 'k': args.pipelining}
  else:
    tracker_options = None

  settings = initSettings(freq_profile)
  settings.fileName = args.file

  ms_to_process = int(args.ms_to_process)

  samplesPerCode = int(round(settings.samplingFreq /
                             (settings.codeFreqBasis / settings.codeLength)))

  gloSamplesPerCode = int(round(settings.samplingFreq /
                                 (settings.gloCodeFreqBasis /
                                  settings.gloCodeLength)))

  samples = {L1CA: {'IF': freq_profile['GPS_L1_IF']},
             L2C: {'IF': freq_profile['GPS_L2_IF']},
             GLO_L1: {'IF': freq_profile['GLO_L1_IF']},
             'samples_total': -1,
             'sample_index': settings.skipNumberOfBytes}

  # Do acquisition
  acq_results_file = args.file + ".acq_results"
  if args.skip_acquisition:
    logging.info("Skipping acquisition, loading saved acquisition results.")
    try:
      acq_results = load_acq_results(acq_results_file)
    except IOError:
      logging.critical("Couldn't open acquisition results file '%s'.",
                       acq_results_file)
      sys.exit(1)
  else:
    # Get 11ms of acquisition samples for fine frequency estimation
    load_samples(samples=samples,
                 num_samples=11 * max(samplesPerCode, gloSamplesPerCode),
                 filename=args.file,
                 file_format=args.file_format)

    acq = Acquisition(samples[L1CA]['samples'],
                      freq_profile['sampling_freq'],
                      freq_profile['GPS_L1_IF'],
                      defaults.code_period * freq_profile['sampling_freq'])
    acq_results = acq.acquisition(progress_bar_output=args.progress_bar)

    if not args.skip_glonass:
      acq = Acquisition(samples[GLO_L1]['samples'],
                        freq_profile['sampling_freq'],
                        freq_profile['GLO_L1_IF'],
                        defaults.glo_code_period *
                          freq_profile['sampling_freq'],
                        code_length=settings.gloCodeLength)
      acq_results = acq.acquisition(bandcode=GLO_L1,
                                     progress_bar_output=args.progress_bar)

    print "Acquisition is over!"

    try:
      save_acq_results(acq_results_file, acq_results)
      logging.debug("Saving acquisition results as '%s'" % acq_results_file)
    except IOError:
      logging.error("Couldn't save acquisition results file '%s'.",
                    acq_results_file)

  # Filter out non-acquired satellites.
  acq_results = [ar for ar in acq_results if ar.status == 'A']

  if len(acq_results) == 0:
    logging.critical("No satellites acquired!")
    sys.exit(1)

  acq_results.sort(key=attrgetter('snr'), reverse=True)

  # Track the acquired satellites
  track_results_file = args.file + ".track_results"
  if args.skip_tracking:
    logging.info("Skipping tracking, loading saved tracking results.")
    try:
      with open(track_results_file, 'rb') as f:
        track_results = cPickle.load(f)
    except IOError:
      logging.critical("Couldn't open tracking results file '%s'.",
                       track_results_file)
      sys.exit(1)
  else:
    load_samples(samples=samples,
                 filename=args.file,
                 file_format=args.file_format)

    if ms_to_process < 0:
      ms_to_process = int(
          1e3 * samples['samples_total'] / freq_profile['sampling_freq'])

    tracker = tracking.Tracker(samples=samples,
                               channels=acq_results,
                               ms_to_track=ms_to_process,
                               sampling_freq=freq_profile[
                                   'sampling_freq'],  # [Hz]
                               stage2_coherent_ms=stage2_coherent_ms,
                               stage2_loop_filter_params=stage2_params,
                               tracker_options=tracker_options,
                               output_file=args.file,
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
    fn_results = tracker.stop()

    logging.debug("Saving tracking results as '%s'" % fn_results)

  # Do navigation
  nav_results_file = args.file + ".nav_results"
  if not args.skip_navigation:
    track_results_generator = lambda: unpickle_iter(fn_results)
    for track_results in track_results_generator():
      nav_solns = navigation(track_results_generator, settings)
      nav_results = []
      for s, t in nav_solns:
        nav_results += [(t, s.pos_llh, s.vel_ned)]
      if len(nav_results):
        print "First nav solution: t=%s lat=%.5f lon=%.5f h=%.1f vel_ned=(%.2f, %.2f, %.2f)" % (
            nav_results[0][0],
            np.degrees(nav_results[0][1][0]), np.degrees(
                nav_results[0][1][1]), nav_results[0][1][2],
            nav_results[0][2][0], nav_results[0][2][1], nav_results[0][2][2])
        with open(nav_results_file, 'wb') as f:
          cPickle.dump(nav_results, f, protocol=cPickle.HIGHEST_PROTOCOL)
        print "and %d more are cPickled in '%s'." % (len(nav_results) - 1,
                                                     nav_results_file)
      else:
        print "No navigation results."

if __name__ == '__main__':
  main()

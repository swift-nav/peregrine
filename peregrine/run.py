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
import json
import numpy as np
from operator import attrgetter

from peregrine.samples import load_samples
from peregrine.acquisition import Acquisition, load_acq_results, save_acq_results
from peregrine.navigation import navigation
import peregrine.tracking as tracking
from peregrine.log import default_logging_config
from peregrine import defaults
import peregrine.gps_constants as gps
from peregrine.tracking_file_utils import removeTrackingOutputFiles
from peregrine.tracking_file_utils import TrackingResults
from peregrine.tracking_file_utils import createTrackingDumpOutputFileName


class SaveConfigAction(argparse.Action):

  def __init__(self, option_strings, dest, nargs=None, **kwargs):
    super(SaveConfigAction, self).__init__(option_strings, dest, **kwargs)

  def __call__(self, parser, namespace, file_hnd, option_string=None):
    data = vars(namespace)

    json.dump(data, file_hnd, indent=2)
    file_hnd.close()
    namespace.no_run = True


class LoadConfigAction(argparse.Action):

  def __init__(self, option_strings, dest, nargs=None, **kwargs):
    super(LoadConfigAction, self).__init__(option_strings, dest, **kwargs)

  def __call__(self, parser, namespace, file_hnd, option_string=None):
    loaded = json.load(file_hnd)
    for k, v in loaded.iteritems():
      setattr(namespace, k, v)
    file_hnd.close()


def populate_peregrine_cmd_line_arguments(parser):
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

  parser.add_argument("--file",
                      help="the sample data file to process")

  parser.add_argument('--no-run',
                      action="store_true",
                      default=False,
                      help="Do not generate output.")

  parser.add_argument('--save-config',
                      type=argparse.FileType('wt'),
                      metavar='FILE_NAME',
                      help="Store configuration into file (implies --no-run)",
                      action=SaveConfigAction)

  parser.add_argument('--load-config',
                      type=argparse.FileType('rt'),
                      metavar='FILE_NAME',
                      help="Restore configuration from file",
                      action=LoadConfigAction)

  inputCtrl = parser.add_argument_group('Data Source',
                                        'Data source configuration')

  skipExcl = inputCtrl.add_mutually_exclusive_group(required=False)

  skipExcl.add_argument("--skip-samples",
                        type=int,
                        default=0,
                        metavar='N_SAMPLES',
                        help="How many samples to skip. Optional.")

  skipExcl.add_argument("--skip-ms",
                        type=float,
                        default=None,
                        metavar='N_MS',
                        help="How many milliseconds to skip")

  inputCtrl.add_argument("-f", "--file-format",
                         choices=['piksi', 'int8', '1bit', '1bitrev',
                                  '1bit_x2', '2bits', '2bits_x2', '2bits_x4'],
                         metavar='FORMAT',
                         help="The format of the sample data file "
                         "('piksi', 'int8', '1bit', '1bitrev', "
                         "'1bit_x2', '2bits', '2bits_x2', '2bits_x4')")

  inputCtrl.add_argument("--ms-to-process",
                         metavar='MS',
                         help="the number of milliseconds to process."
                         "(-1: use all available data)",
                         default="-1")

  inputCtrl.add_argument("--profile",
                         choices=['peregrine', 'custom_rate', 'low_rate',
                                  'normal_rate', 'piksi_v3', 'high_rate'],
                         metavar='PROFILE',
                         help="L1C/A & L2C IF + sampling frequency profile"
                         "('peregrine'/'custom_rate', 'low_rate', "
                         "'normal_rate', 'piksi_v3', 'high_rate')",
                         default='peregrine')

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

  signalParam = parser.add_argument_group('Signal tracking',
                                          'Parameters for satellite vehicle'
                                          ' signal')

  signalParam.add_argument('--l1ca-profile',
                           metavar='PROFILE',
                           help='L1 C/A stage profile. Controls coherent'
                                ' integration time and tuning parameters: %s.' %
                                str(defaults.l1ca_stage_profiles.keys()),
                           choices=defaults.l1ca_stage_profiles.keys())

  return signalParam


def main():
  default_logging_config()

  parser = argparse.ArgumentParser()

  parser.add_argument("-a", "--skip-acquisition",
                      help="use previously saved acquisition results",
                      action="store_true")
  parser.add_argument("-t", "--skip-tracking",
                      help="use previously saved tracking results",
                      action="store_true")
  parser.add_argument("-n", "--skip-navigation",
                      help="use previously saved navigation results",
                      action="store_true")

  populate_peregrine_cmd_line_arguments(parser)

  args = parser.parse_args()

  if args.no_run:
    return 0

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

  ms_to_process = int(args.ms_to_process)

  skip_samples = 0
  if args.skip_samples is not None:
    skip_samples = args.skip_samples
  if args.skip_ms is not None:
    skip_samples = int(args.skip_ms * freq_profile['sampling_freq'] / 1e3)

  samples = {gps.L1CA: {'IF': freq_profile['GPS_L1_IF']},
             gps.L2C: {'IF': freq_profile['GPS_L2_IF']},
             'samples_total': -1,
             'sample_index': skip_samples}

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
    for signal in [gps.L1CA]:

      samplesPerCode = int(round(freq_profile['sampling_freq'] /
                                 (gps.l1ca_chip_rate / gps.l1ca_code_length)))

      # Get 11ms of acquisition samples for fine frequency estimation
      load_samples(samples=samples,
                   num_samples=11 * samplesPerCode,
                   filename=args.file,
                   file_format=args.file_format)

      acq = Acquisition(signal,
                        samples[signal]['samples'],
                        freq_profile['sampling_freq'],
                        freq_profile['GPS_L1_IF'],
                        gps.l1ca_code_period * freq_profile['sampling_freq'],
                        gps.l1ca_code_length)
      # only one signal - L1CA is expected to be acquired at the moment
      # TODO: add handling of acquisition results from GLONASS once GLONASS
      # acquisition is supported.
      acq_results = acq.acquisition(progress_bar_output=args.progress_bar)

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
  if not args.skip_tracking:
    # Remove tracking output files from the previous session.
    removeTrackingOutputFiles(args.file)

    load_samples(samples=samples,
                 filename=args.file,
                 file_format=args.file_format)

    if ms_to_process < 0:
      ms_to_process = int(
          1e3 * samples['samples_total'] / freq_profile['sampling_freq'])

    # Create the tracker object, which also create one tracking
    # channel per each acquisition result in 'acq_results' list.
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
    # The tracking channels are designed to support batch processing.
    # In the batch processing mode the data samples are provided in
    # batches (chunks) of 'defaults.processing_block_size' bytes size.
    # The loop below runs all tracking channels for each batch as it
    # reads it from the samples file.
    tracker.start()
    condition = True
    while condition:
      # Each tracking channel remembers its own data samples offset within
      # 'samples' such that when new batch of data is provided, it
      # starts precisely, where it finished at the previous batch
      # processing round.
      # 'sample_index' is set to the smallest offset within 'samples'
      # array across all tracking channels.
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
  if not args.skip_navigation:
    combinedResultObject = TrackingResults(args.file)

    # Dump combined output into a text file
    with open(createTrackingDumpOutputFileName(args.file), "wt") as f:
      logging.debug("Creating combined tracking file %s", f.name)
      combinedResultObject.dump(f)

    samplingFreqHz = freq_profile['sampling_freq']
    nav_solns = navigation(combinedResultObject, samplingFreqHz)
    nav_results = []
    for s, t in nav_solns:
      nav_results += [(t, s.pos_llh, s.vel_ned)]
    if len(nav_results):
      print "First nav solution: t=%s lat=%.5f lon=%.5f h=%.1f vel_ned=(%.2f, %.2f, %.2f)" % (
          nav_results[0][0],
          np.degrees(nav_results[0][1][0]), np.degrees(
              nav_results[0][1][1]), nav_results[0][1][2],
          nav_results[0][2][0], nav_results[0][2][1], nav_results[0][2][2])
      nav_results_file = args.file + ".nav_results"
      with open(nav_results_file, 'wb') as f:
        cPickle.dump(nav_results, f, protocol=cPickle.HIGHEST_PROTOCOL)
      print "and %d more are cPickled in '%s'." % (len(nav_results) - 1, nav_results_file)
    else:
      print "No navigation results."

if __name__ == '__main__':
  main()

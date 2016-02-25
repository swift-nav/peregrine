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
from operator import attrgetter
import numpy as np

from peregrine.samples import load_samples
from peregrine.acquisition import Acquisition, load_acq_results, save_acq_results
from peregrine.navigation import navigation
from peregrine.tracking import track
from peregrine.log import default_logging_config
from peregrine.analysis.tracking_loop import dump_tracking_results_for_analysis
import defaults

from initSettings import initSettings

def main():
  default_logging_config()

  parser = argparse.ArgumentParser()
  parser.add_argument("file",
                      help="the sample data file to process")
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
                      help = "the number of milliseconds to process."
                      "(-1: use all available data",
                      default = "-1")
  parser.add_argument("--profile",
                      help="L1C/A & L2C IF + sampling frequency profile"
                      "('peregrine', 'low_rate', 'piksi_v3')",
                      default = 'peregrine')
  parser.add_argument("-f", "--file-format", default=defaults.file_format,
                      help="the format of the sample data file "
                      "('piksi', 'int8', '1bit', '1bitrev', "
                      "'1bit_x2', '2bits', '2bits_x2', '2bits_x4')")
  args = parser.parse_args()

  if args.profile == 'peregrine':
    freq_profile = defaults.freq_profile_peregrine
  elif args.profile == 'low_rate':
    freq_profile = defaults.freq_profile_low_rate
  elif args.profile == 'piksi_v3':
    freq_profile = defaults.freq_profile_piksi_v3
  else:
    raise NotImplementedError()

  settings = initSettings(freq_profile)
  settings.fileName = args.file

  ms_to_process = int(args.ms_to_process)
  if ms_to_process > 0:
    samples_num = freq_profile['sampling_freq'] * 1e-3 * ms_to_process
  else:
    samples_num = -1 # all available samples

  samplesPerCode = int(round(settings.samplingFreq /
                             (settings.codeFreqBasis / settings.codeLength)))

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
    acq_samples = load_samples(args.file, 11 * samplesPerCode,
                               settings.skipNumberOfBytes,
                               file_format=args.file_format)
    acq = Acquisition(acq_samples[0],
                      freq_profile['sampling_freq'],
                      freq_profile['GPS_L1_IF'],
                      defaults.code_period * freq_profile['sampling_freq'])
    acq_results = acq.acquisition()

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
    signal = load_samples(args.file,
                          int(samples_num),
                          settings.skipNumberOfBytes,
                          file_format=args.file_format)
    if ms_to_process < 0:
      ms_to_process = int(1e3 * len(signal[0]) / freq_profile['sampling_freq'])

    settings.msToProcess = ms_to_process - 22

    if len(signal) > 1:
      samples = [ {'data': signal[0], 'IF': freq_profile['GPS_L1_IF']},
                  {'data': signal[1], 'IF': freq_profile['GPS_L2_IF']} ]
    else:
      samples = [ {data: signal[0], 'IF': freq_profile['GPS_L1_IF']} ]

    track_results = track( samples, acq_results,
                           settings.msToProcess, freq_profile['sampling_freq'])
    try:
      with open(track_results_file, 'wb') as f:
        cPickle.dump(track_results, f, protocol=cPickle.HIGHEST_PROTOCOL)
      logging.debug("Saving tracking results as '%s'" % track_results_file)
      logging.debug("Saving tracking results for analysis")
      dump_tracking_results_for_analysis(track_results_file, track_results)
    except IOError:
      logging.error("Couldn't save tracking results file '%s'.",
                    track_results_file)

  # Do navigation
  nav_results_file = args.file + ".nav_results"
  if not args.skip_navigation:
    nav_solns = navigation(track_results, settings)
    nav_results = []
    for s, t in nav_solns:
      nav_results += [(t, s.pos_llh, s.vel_ned)]
    if len(nav_results):
      print "First nav solution: t=%s lat=%.5f lon=%.5f h=%.1f vel_ned=(%.2f, %.2f, %.2f)" % (
        nav_results[0][0],
        np.degrees(nav_results[0][1][0]), np.degrees(nav_results[0][1][1]), nav_results[0][1][2],
        nav_results[0][2][0], nav_results[0][2][1], nav_results[0][2][2])
      with open(nav_results_file, 'wb') as f:
        cPickle.dump(nav_results, f, protocol=cPickle.HIGHEST_PROTOCOL)
      print "and %d more are cPickled in '%s'." % (len(nav_results) - 1, nav_results_file)
    else:
      print "No navigation results."

if __name__ == '__main__':
  main()

#!/usr/bin/env python
#--------------------------------------------------------------------------
#                           SoftGNSS v3.0
#
# Copyright (C) Darius Plausinaitis and Dennis M. Akos
# Written by Darius Plausinaitis and Dennis M. Akos
# Converted to Python by Colin Beighley
#--------------------------------------------------------------------------
#This program is free software; you can redistribute it and/or
#modify it under the terms of the GNU General Public License
#as published by the Free Software Foundation; either version 2
#of the License, or (at your option) any later version.
#
#This program is distributed in the hope that it will be useful,
#but WITHOUT ANY WARRANTY; without even the implied warranty of
#MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#GNU General Public License for more details.
#
#You should have received a copy of the GNU General Public License
#along with this program; if not, write to the Free Software
#Foundation, Inc., 51 Franklin Street, Fifth Floor, Boston, MA  02110-1301,
#USA.
#--------------------------------------------------------------------------

import sys
import argparse
from initSettings import initSettings
import getSamples
from acquisition import acquisition
from navigation import navigation
import pickle
from include.showChannelStatus import showChannelStatus
from tracking import track
import logging
from operator import attrgetter
logging.basicConfig(level=logging.DEBUG, format="%(asctime)s [%(levelname)s] %(name)s: %(message)s")

#Initialize constants, settings
settings = initSettings()

parser = argparse.ArgumentParser()
parser.add_argument("file", help="the sample data file to process")
parser.add_argument("-a", "--skip-acquisition", help="use previously saved acquisition results", action="store_true")
parser.add_argument("-t", "--skip-tracking", help="use previously saved tracking results", action="store_true")
parser.add_argument("-n", "--skip-navigation", help="use previously saved navigation results", action="store_true")
args = parser.parse_args()
settings.fileName = args.file

samplesPerCode = int(round(settings.samplingFreq / (settings.codeFreqBasis / settings.codeLength)))

# Do acquisition
acq_results_file = args.file + ".acq_results"
if args.skip_acquisition:
  logging.info("Skipping acquisition, loading saved acquisition results.")
  try:
    with open(acq_results_file, 'rb') as f:
      acq_results = pickle.load(f)
  except IOError:
    logging.critical("Couldn't open acquisition results file '%s'.", acq_results_file)
    sys.exit(1)
else:
  # Get 11ms of acquisition samples for fine frequency estimation
  acq_samples = getSamples.int8(args.file, 11*samplesPerCode, settings.skipNumberOfBytes)
  acq_results = acquisition(acq_samples, settings)
  try:
    with open(acq_results_file, 'wb') as f:
      pickle.dump(acq_results, f)
  except IOError:
    logging.error("Couldn't save acquisition results file '%s'.", acq_results_file)

if len(acq_results) == 0:
  logging.critical("No satellites acquired!")
  sys.exit(1)

acq_results.sort(key=attrgetter('SNR'), reverse=True)

showChannelStatus(acq_results, settings)

# Track the acquired satellites
track_results_file = args.file + ".track_results"
if args.skip_tracking:
  logging.info("Skipping tracking, loading saved tracking results.")
  try:
    with open(track_results_file, 'rb') as f:
      (track_results, channel) = pickle.load(f)
  except IOError:
    logging.critical("Couldn't open tracking results file '%s'.", track_results_file)
    sys.exit(1)
else:
  (track_results, channel) = track(acq_results, settings)
  try:
    with open(track_results_file, 'wb') as f:
      pickle.dump((track_results, channel), f)
  except IOError:
    logging.error("Couldn't save tracking results file '%s'.", track_results_file)

# Do navigation
if not args.skip_navigation:
  navSolutions = navigation(track_results, settings)

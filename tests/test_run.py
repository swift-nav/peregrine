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
import cPickle
import os

from peregrine.acquisition import load_acq_results
from mock import patch
from shutil import copyfile

SAMPLES_PATH = 'tests/test_data/'
RES_PATH = SAMPLES_PATH + '/results/'

SAMPLES_FNAME = 'gpsl1ca_ci_samples.piksi_format'

SAMPLES = SAMPLES_PATH + SAMPLES_FNAME

OLD_ACQ_RES = RES_PATH + SAMPLES_FNAME + '.acq_results'
OLD_TRK_RES = RES_PATH + SAMPLES_FNAME + '.track_results'
OLD_NAV_RES = RES_PATH + SAMPLES_FNAME + '.nav_results'

BLAH_TRK_RES = RES_PATH + 'blah' + '.track_results'

# run.py deposits results in same location as samples
NEW_ACQ_RES = SAMPLES_PATH + SAMPLES_FNAME + '.acq_results'
NEW_TRK_RES = SAMPLES_PATH + SAMPLES_FNAME + '.track_results'
NEW_NAV_RES = SAMPLES_PATH + SAMPLES_FNAME + '.nav_results'

def test_acquisition():

  # Replace argv with args to skip tracking and navigation.
  with patch.object(sys, 'argv', ['peregrine', SAMPLES, '-t', '-n']):

    try:
      peregrine.run.main()
    except SystemExit:
      # Thrown if track and nav results files are not present and we
      # supplied command line args to skip tracking and navigation.
      pass
    
    new_acq_results = load_acq_results(NEW_ACQ_RES)
    old_acq_results = load_acq_results(OLD_ACQ_RES)

    assert new_acq_results == old_acq_results

    # Clean-up.
    os.remove(NEW_ACQ_RES)

def test_tracking():

  # Replace argv with args to skip acquisition and navigation.
  with patch.object(sys, 'argv', ['peregrine', SAMPLES, '-a', '-n']):

    # Copy reference acq results to use in order to skip acquisition.
    copyfile(OLD_ACQ_RES, NEW_ACQ_RES)

    try:
      peregrine.run.main()
    except SystemExit:
      # Thrown if nav results file is not present and we supplied
      # command line arg to skip navigation.
      pass

    with open(NEW_TRK_RES, 'rb') as f:
      new_trk_results = cPickle.load(f)
    with open(OLD_TRK_RES, 'rb') as f:
      old_trk_results = cPickle.load(f)

    #assert new_trk_results == old_trk_results

    # Clean-up.
    #os.remove(NEW_ACQ_RES)
    #os.remove(NEW_TRK_RES)

def test_blah():

  with open(BLAH_TRK_RES, 'rb') as f:
    blah_trk_results = cPickle.load(f)
  with open(OLD_TRK_RES, 'rb') as f:
    old_trk_results = cPickle.load(f)

  assert blah_trk_results == old_trk_results



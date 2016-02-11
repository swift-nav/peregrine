# Copyright (C) 2015 Swift Navigation Inc.
#
# This source is subject to the license found in the file 'LICENSE' which must
# be be distributed together with this source. All other rights reserved.
#
# THIS CODE AND INFORMATION IS PROVIDED "AS IS" WITHOUT WARRANTY OF ANY KIND,
# EITHER EXPRESSED OR IMPLIED, INCLUDING BUT NOT LIMITED TO THE IMPLIED
# WARRANTIES OF MERCHANTABILITY AND/OR FITNESS FOR A PARTICULAR PURPOSE.

import peregrine.run
from peregrine.acquisition import load_acq_results
from mock import patch
import sys
import cPickle
import os

SAMPLES_PATH = 'tests/test_data/'
RES_PATH = SAMPLES_PATH + '/results/'

SAMPLES_FNAME = 'gpsl1ca_ci_samples.piksi_format'

SAMPLES = SAMPLES_PATH + SAMPLES_FNAME

OLD_ACQ_RES = RES_PATH + SAMPLES_FNAME + '.acq_results'
OLD_TRK_RES = RES_PATH + SAMPLES_FNAME + '.track_results'
OLD_NAV_RES = RES_PATH + SAMPLES_FNAME + '.nav_results'

# run.py deposits results in same location as samples
NEW_ACQ_RES = SAMPLES_PATH + SAMPLES_FNAME + '.acq_results'
NEW_TRK_RES = SAMPLES_PATH + SAMPLES_FNAME + '.track_results'
NEW_NAV_RES = SAMPLES_PATH + SAMPLES_FNAME + '.nav_results'

def test_acquisition():

  with patch.object(sys, 'argv', ['peregrine', SAMPLES, '-t', '-n']):

    try:
      peregrine.run.main()
    except SystemExit:
      # Will be thrown if track or nav results files are not present
      pass
    
    # Load acquisition results from test run
    new_acq_results = load_acq_results(NEW_ACQ_RES)

    # Load saved acq results to compare against
    old_acq_results = load_acq_results(OLD_ACQ_RES)

    assert new_acq_results == old_acq_results

    os.remove(NEW_ACQ_RES)

#def test_tracking():
#  with patch.object(sys, 'argv', ['peregrine', SAMPLES, '-a', '-n']):
#    peregrine.run.main()
#    os.remove(ACQ_RES)
#    os.remove(TRK_RES)

# TODO
#def test_navigation():
#  with patch.object(sys, 'argv', ['peregrine', SAMPLES, '-a', '-t']):
#    peregrine.run.main()
#    os.remove(ACQ_RES)
#    os.remove(TRK_RES)
#    os.remove(NAV_RES)

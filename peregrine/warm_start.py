#!/usr/bin/env python
# Copyright (C) 2012 - 2016 Swift Navigation Inc.
# Contact: Fergus Noble <fergus@swiftnav.com>
#
# This source is subject to the license found in the file 'LICENSE' which must
# be be distributed together with this source. All other rights reserved.
#
# THIS CODE AND INFORMATION IS PROVIDED "AS IS" WITHOUT WARRANTY OF ANY KIND,
# EITHER EXPRESSED OR IMPLIED, INCLUDING BUT NOT LIMITED TO THE IMPLIED
# WARRANTIES OF MERCHANTABILITY AND/OR FITNESS FOR A PARTICULAR PURPOSE.

from math import degrees, radians, acos
from numpy.linalg import norm
from peregrine.gps_time import datetime_to_tow
import os, os.path, shutil
import peregrine.acquisition as acquisition
import peregrine.almanac as almanac
import peregrine.ephemeris as ephemeris
import peregrine.gps_constants as gps
import swiftnav.coord_system

import logging
logger = logging.getLogger(__name__)

def horizon_dip(r):
    # Approximation to the dip angle of the horizon.
    lat, lon, height = swiftnav.coord_system.wgsecef2llh_(r[0], r[1], r[2])
    r_e = norm(swiftnav.coord_system.wgsllh2ecef_(lat, lon, 0))
    return degrees(-acos(r_e / norm(r_e + height)))

def whatsup(ephem, r, t, mask = None, disp = False):
    hd = horizon_dip(r)
    if mask is None:
        mask = hd
    wk, tow = datetime_to_tow(t)
    satsup = []

    if disp:
        print "Approximate horizon dip angle: %+4.1f deg"%hd
        print "Satellite sky positions from prior (above mask and healthy):"
        print "PRN\tAz\tEl\t"

    for prn in ephem:
        pos, _, _, _ = ephemeris.calc_sat_pos(ephem[prn], tow, wk,
                                              warn_stale = False)
        az, el = swiftnav.coord_system.wgsecef2azel_(pos, r)
        if ephem[prn]['healthy'] and degrees(el) > mask:
            satsup.append(prn)
            if disp:
                print "%2d\t%5.1f\t%+5.1f" % (prn + 1, degrees(az), degrees(el))
    return satsup

def whatsdown(ephem, r, t, mask = -45):
    """
    Return sats *below* a certain mask, for sanity check
    """
    wk, tow = datetime_to_tow(t)
    satsdown = []
    for prn in ephem:
        pos, _, _, _ = ephemeris.calc_sat_pos(ephem[prn], tow, wk,
                                              warn_stale = False)
        az, el = swiftnav.coord_system.wgsecef2azel_(pos, r)
        if degrees(el) < mask:
            satsdown.append(prn)
    return satsdown


def warm_start(signal, t_prior, r_prior, v_prior, ephem, settings,
               n_codes_integrate = 8):
    """
    Perform rapid / more-sensitive acquisition based on a prior estimate of the
    receiver's position, velocity and time.
    """

    pred = whatsup(ephem, r_prior, t_prior,
                   mask = settings.elevMask,
                   disp=True)
    pred_dopp = ephemeris.pred_dopplers(pred, ephem, r_prior, v_prior, t_prior)
    if settings.acqSanityCheck:
        notup = whatsdown(ephem, r_prior, t_prior)
    else:
        notup = []

    # Acquisition
    wiz_file = os.path.join(settings.cacheDir, "fftw_wisdom")
    if not os.path.isfile(wiz_file):
        if not os.path.isdir(settings.cacheDir):
            os.makedirs(settings.cacheDir)
        if os.path.isfile("/etc/fftw/wisdom"):
            shutil.copy("/etc/fftw/wisdom", wiz_file)

    samplingFreq = settings.freq_profile['sampling_freq']

    a = acquisition.Acquisition(signal, samplingFreq,
                                settings.freq_profile['GPS_L1_IF'],
                                samplingFreq * settings.code_period,
                                n_codes_integrate=n_codes_integrate,
                                wisdom_file = wiz_file)
    # Attempt to acquire both the sats we predict are visible
    # and some we predict are not.
    acq_results = a.acquisition(threshold = settings.acqThreshold,
                                prns = pred + notup,
                                doppler_priors = pred_dopp + [0 for p in notup],
                                doppler_search = settings.rxFreqTol * gps.l1,
                                show_progress = True, multi = True)
    nacq_results = acq_results[len(pred):]
    acq_results = acq_results[:len(pred)]

    # Sanity check: We should not be acquiring sats that are out of view
    nacq_acqed = [ar for ar in nacq_results if ar.status == 'A']
    if len(nacq_acqed) > 0:
        print "ALERT! %d of %d PRNs acquired despite being well below the horizon:" % (len(nacq_acqed), len(notup))
        for ar in nacq_acqed:
            print ar
        print "Maybe there's heavy jamming, prior orbit is badly wrong or thresholds need to be adjusted."
        if settings.abortIfInsane:
            print "Aborting this sample set."
            return []

    acquisition.print_scores(acq_results, pred, pred_dopp)

    acqed = [a for a in acq_results if a.status == 'A']
    return acqed

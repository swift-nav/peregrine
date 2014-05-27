import peregrine.almanac as almanac
import peregrine.ephemeris as ephemeris
import peregrine.acquisition as acquisition
import peregrine.gps_constants as gps
from peregrine.time import datetime_to_tow

import swiftnav.coord_system

from numpy.linalg import norm
from math import degrees, radians, acos
import os, os.path, shutil
import logging
logger = logging.getLogger(__name__)

def horizon_dip(r):
    # Approximation to the dip angle of the horizon.
    lat, lon, height = swiftnav.coord_system.wgsecef2llh(r[0], r[1], r[2])
    r_e = norm(swiftnav.coord_system.wgsllh2ecef(lat, lon, 0))
    return degrees(-acos(r_e / norm(r_e + height)))

def whatsup(ephem, r, t, mask = None):
    if mask is None:
        mask = horizon_dip(r)
    wk, tow = datetime_to_tow(t)
    satsup = []
    for prn in ephem:
        pos, _, _, _ = ephemeris.calc_sat_pos(ephem[prn], tow, wk,
                                              warn_stale = False)
        az, el = swiftnav.coord_system.wgsecef2azel(pos, r)
        if ephem[prn]['healthy'] and degrees(el) > mask:
            satsup.append(prn)
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
        az, el = swiftnav.coord_system.wgsecef2azel(pos, r)
        if degrees(el) < mask:
            satsdown.append(prn)
    return satsdown


def warm_start(signal, t_prior, r_prior, v_prior, ephem, settings,
               n_codes_integrate = 8):
    """
    Perform rapid / more-sensitive acquisition based on a prior estimate of the
    receiver's position, velocity and time.
    """

    pred = whatsup(ephem, r_prior, t_prior)
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

    a = acquisition.Acquisition(signal, settings.samplingFreq,
                                settings.IF,
                                settings.samplingFreq * gps.code_period,
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
        if settings.abortOnInsane:
            print "Aborting this sample set."
            return []

    acquisition.print_scores(acq_results, pred, pred_dopp)

    acqed = [a for a in acq_results if a.status == 'A']
    return acqed

## Copyright (C) 2014 Planet Labs Inc.
# Author: Henry Hallam
#
# Tools for performing point solutions from short sample sets
#
# This source is subject to the license found in the file 'LICENSE' which must
# be be distributed together with this source. All other rights reserved.
#
# THIS CODE AND INFORMATION IS PROVIDED "AS IS" WITHOUT WARRANTY OF ANY KIND,
# EITHER EXPRESSED OR IMPLIED, INCLUDING BUT NOT LIMITED TO THE IMPLIED
# WARRANTIES OF MERCHANTABILITY AND/OR FITNESS FOR A PARTICULAR PURPOSE.

from datetime import datetime, timedelta
from numpy import dot
from numpy.linalg import norm
from peregrine.ephemeris import calc_sat_pos, obtain_ephemeris
from peregrine.gps_time import datetime_to_tow
from scipy.optimize import fmin, fmin_powell
from warnings import warn
import cPickle
import hashlib
import math
import numpy as np
import os, os.path
import peregrine.acquisition
import peregrine.gps_constants as gps
import peregrine.samples
import peregrine.warm_start

import logging
logger = logging.getLogger(__name__)

dt = lambda sec: timedelta(seconds=sec)

def pseudoranges_from_ranges(ranges, prn_ref):
    pseudoranges = {}
    for prn, rngs in ranges.iteritems():
        pseudoranges[prn] = rngs - ranges[prn_ref]
    return pseudoranges

def resolve_ms_integers(obs_pr, pred_pr, prn_ref, disp = True):
    # Solve for the pseudorange millisecond ambiguities
    obs_pr = pseudoranges_from_ranges(obs_pr, prn_ref)
    pred_pr = pseudoranges_from_ranges(pred_pr, prn_ref)

    if disp:
        print "Resolving millisecond integers:"

    for prn, pr in obs_pr.iteritems():
        pr_int_est = (pred_pr[prn] - pr) / gps.code_wavelength
        pr_int = round(pr_int_est)
        if abs(pr_int - pr_int_est) > 0.15:
            logger.warn("Pseudorange integer for PRN %2d is %.4f" % (
                prn + 1, pr_int_est) + ", which isn't very close to an integer.")
        pr += pr_int * gps.code_wavelength
        obs_pr[prn] = pr
        if disp:
            print ("PRN %2d: pred pseudorange = %9.3f km, obs = %9.3f, " + \
              "(pred - obs) = %9.3f km") % (
                prn + 1,
                pred_pr[prn] / 1e3,
                pr / 1e3,
                (pred_pr[prn] - pr) / 1e3
        )
    return obs_pr

def nav_bit_hypotheses(n_ms):
    import itertools
    def fill_remainder(n_ms):
        if n_ms <= 20:
            return [ [1]*n_ms, [-1]*n_ms]
        return [b + f for b in [[1]*20, [-1]*20] for f in fill_remainder(n_ms - 20)]
    hs = []
    for nav_edge_phase in range(1,min(n_ms,21)):
        h = [([1]*nav_edge_phase) + f for f in fill_remainder(n_ms - nav_edge_phase)]
        hs += h
    return [k for k,v in itertools.groupby(sorted(hs))]

def long_correlation(signal, ca_code, code_phase, doppler, settings, plot=False, coherent = 0, nav_bit_hypoth = None):
    from swiftnav.correlate import track_correlate_
    code_freq_shift = (doppler / gps.l1) * gps.chip_rate
    samples_per_chip = settings.samplingFreq / (gps.chip_rate + code_freq_shift)
    samples_per_code = samples_per_chip * gps.chips_per_code
    numSamplesToSkip = round(code_phase * samples_per_chip)
    remCodePhase = (1.0 * numSamplesToSkip / samples_per_chip) - code_phase
    remCarrPhase = 0.0
    n_ms = int((len(signal) - numSamplesToSkip) / samples_per_code)
    i_p = []
    q_p = []
    i_c = []
    q_c = []
    costas_i = 0.0
    costas_q = 0.0
    for loopCnt in range(n_ms):
        rawSignal = signal[numSamplesToSkip:]#[:blksize_]
        E, P, L, blksize, remCodePhase, remCarrPhase = track_correlate_(
                            rawSignal,
                            code_freq_shift + gps.chip_rate,
                            remCodePhase,
                            doppler + settings.IF,
                            remCarrPhase, ca_code, settings.samplingFreq)

        I_E = E.real
        Q_E = E.imag
        I_P = P.real
        Q_P = P.imag
        I_L = L.real
        Q_L = L.imag

        numSamplesToSkip += blksize
        #print "@ %d, I_P = %.0f, Q_P = %.0f" % (loopCnt, I_P, Q_P)
        i_p.append(I_P)
        q_p.append(Q_P)
        if coherent == 0:
            Q_C = 0
            I_C = math.sqrt(I_P**2 + Q_P**2)
        elif coherent == 0.5:
            phase = math.atan(Q_P / I_P)
            mag = math.sqrt(I_P**2 + Q_P**2)
            I_C = mag * math.cos(phase)
            Q_C = mag * math.sin(phase)
        elif coherent == 1:
            if nav_bit_hypoth is None:
                I_C = I_P
                Q_C = Q_P
            else:
                I_C = I_P * nav_bit_hypoth[loopCnt]
                Q_C = Q_P * nav_bit_hypoth[loopCnt]
        else:
            raise ValueError("'coherent' should be 0, 0.5 or 1")
        i_c.append(I_C)
        q_c.append(Q_C)
        costas_i += I_C
        costas_q += Q_C
    if plot:
        ax = plt.figure(figsize=(5,5)).gca()
        ax.plot(i_p, q_p, '.')
        ax.plot(i_c, q_c, 'r+')
        ax.plot(costas_i/n_ms, costas_q/n_ms, 'ko')
        ax.axis('equal')
        plt.xlim([-1000, 1000])
        plt.ylim([-1000, 1000])
        plt.title(str(doppler))

    return ((costas_i / n_ms) ** 2 + (costas_q / n_ms) ** 2)

def refine_ob(signal, acq_result, settings, print_results = True, return_sweeps = False):
    # TODO: Fit code phase results for better resolution
    from peregrine.include.generateCAcode import caCodes
    from scipy import optimize as opt
    samples_per_chip = settings.samplingFreq / gps.chip_rate
    samples_per_code = samples_per_chip * gps.chips_per_code
    # Get a vector with the C/A code sampled 1x/chip
    ca_code = caCodes[acq_result.prn]
    # Add wrapping to either end to be able to do early/late
    ca_code = np.concatenate(([ca_code[1022]],ca_code,[ca_code[0]]))

    dopp_offset_search = 100 # Hz away from acquisition
    code_offsets = np.arange(-1,1, 1.0 / 16 / 2)

    pwr_1 = []
    for code_offset in code_offsets:
        pwr_1.append(long_correlation(signal, ca_code, acq_result.code_phase + code_offset, acq_result.doppler + 0.0, settings,
                                    coherent = 0))
    code_offset_best_noncoherent = code_offsets[np.argmax(pwr_1)]

    n_ms = int((len(signal) - samples_per_chip * (acq_result.code_phase + code_offset_best_noncoherent)) / samples_per_code)
    nbhs = nav_bit_hypotheses(n_ms)
    pwr_2 = []
    dopp_offset_best_2 = []
    for nbh in nbhs:
        def score(dopp_offset):
            return -long_correlation(signal, ca_code,
                                        acq_result.code_phase + code_offset_best_noncoherent,
                                        acq_result.doppler + dopp_offset,
                                        settings,
                                        coherent = 1,
                                        nav_bit_hypoth = nbh,
                                        plot=False)
        xopt, fval, _, _ = opt.fminbound(score, -dopp_offset_search, dopp_offset_search, xtol=0.1, maxfun=500, full_output=True, disp=1)
        pwr_2.append(-fval)
        dopp_offset_best_2.append(xopt)

    nbh_best = np.argmax(pwr_2)
    dopp_offset_best = dopp_offset_best_2[nbh_best]
    try:
        nbp_best = nbhs[nbh_best].index(-1) % 20
    except ValueError:
        nbp_best = None

    if return_sweeps:
        dopp_plot_offsets = np.arange(-50,50,2) + dopp_offset_best
        pwr_3 = []
        for dopp_offset in dopp_plot_offsets:
            pwr_3.append(long_correlation(signal, ca_code,
                                                  acq_result.code_phase + code_offset_best_noncoherent,
                                                  acq_result.doppler + dopp_offset, settings,
                                                  coherent = 1, nav_bit_hypoth = nbhs[nbh_best]))

    pwr_4 = []
    for code_offset in code_offsets:
        pwr_4.append(long_correlation(signal, ca_code, acq_result.code_phase + code_offset,
                                    acq_result.doppler + dopp_offset_best,
                                    settings, coherent = 1, nav_bit_hypoth = nbhs[nbh_best]))
    code_offset_best = code_offsets[np.argmax(pwr_4)]

    if print_results:
        print "%2d\t%+6.0f\t%5.1f\t%+6.3f\t\t%d\t" % (
            acq_result.prn + 1, acq_result.doppler, acq_result.snr,
            code_offset_best_noncoherent, nbh_best),
        if nbp_best is None:
            print "-",
        else:
            print nbp_best,
        print "\t%+6.1f\t\t%+6.3f" % (dopp_offset_best, code_offset_best)

    ob_cp = acq_result.code_phase + code_offset_best
    ob_dopp = acq_result.doppler + dopp_offset_best

    if return_sweeps:
        sweeps = (code_offsets, code_offset_best,
                  dopp_plot_offsets, dopp_offset_best,
                  nbh_best,
                  pwr_1, pwr_2, pwr_3, pwr_4)
        return ob_cp, ob_dopp, sweeps
    else:
        return ob_cp, ob_dopp

def plot_refine_results(acq_result, sweeps):
    import matplotlib.pyplot as plt

    (code_offsets, code_offset_best,
     dopp_plot_offsets, dopp_offset_best,
     nbh_best,
     pwr_1, pwr_2, pwr_3, pwr_4) = sweeps

    fig=plt.figure(figsize=(14,10))
    fig.suptitle(str(acq_result))

    ax=fig.add_subplot(221)
    plt.title("Initial code phase search (noncoherent)")
    ax.plot(code_offsets, pwr_1, 'k.')
    plt.xlabel('Code phase offset')
    plt.ylim([0, 500e3])

    ax=fig.add_subplot(222)
    ax.plot(pwr_2, 'r.')
    ax.plot(nbh_best, np.amax(pwr_2), 'k*')
    plt.ylim([0, 500e3])
    plt.title("Nav edge search (coherent)")
    plt.xlabel('Nav bits hypothesis #')

    ax=fig.add_subplot(223)
    ax.plot(dopp_plot_offsets, pwr_3, 'b.')
    ax.plot(dopp_offset_best, np.amax(pwr_2), 'k*')
    plt.ylim([0, 500e3])
    plt.title("Carrier freq search (coherent)")
    plt.xlabel('Carrier freq offset')

    ax=fig.add_subplot(224)
    ax.plot(code_offsets, pwr_4, 'g.')
    ax.plot(code_offset_best, np.amax(pwr_4), 'k*')
    plt.ylim([0, 500e3])
    plt.title("Final code phase search (coherent)")
    plt.xlabel('Code phase offset')

def refine_obs(signal, acq_results, settings,
               print_results = True,
               plot = True,
               multi = True):

    from peregrine.parallel_processing import parmap
    mapper = parmap if multi else map

    obs_cp = {}
    obs_dopp = {}
    sweepss = {}
    if print_results:
        print "PRN\tAcquisition:\tNon-coherent\tNavigation bit:\tCoherent\tCoherent"
        print "\tDopp\tSNR\tcode phase\tHyp #\tPhase\tdoppler\t\tcode phase"

    res = mapper(lambda a: refine_ob(signal, a, settings,
                                   print_results = print_results, return_sweeps = True),
              acq_results)
    for i, a in enumerate(acq_results):
        ob_cp, ob_dopp, sweeps = res[i]
        obs_cp[a.prn] = ob_cp
        obs_dopp[a.prn] = ob_dopp
        sweepss[a.prn] = sweeps
    if plot:
        import matplotlib.pyplot as plt
        for a in acq_results:
            plot_refine_results(a, sweepss[a.prn])
        plt.show()

    return obs_cp, obs_dopp

def predict_observables(prior_traj, prior_datetime, prns, ephem, window):
    from datetime import timedelta
    from numpy.linalg import norm
    from numpy import dot
    """Given a list of PRNs, a set of ephemerides, a nominal capture time (datetime) and a
    and a time window (seconds), compute the ranges and dopplers for
    each satellite at 1ms shifts."""
    timeres = 50 * gps.code_period # Might be important to keep this an integer number of code periods
    t0 = prior_datetime - timedelta(seconds=window / 2.0)
    ranges = {}
    dopplers = {}
    for prn in prns:
        ranges[prn] = []
        dopplers[prn] = []
    times = []
    for tt in np.arange(0, window, timeres):
        t = t0 + timedelta(seconds = tt)
        times.append(t)
        r, v = prior_traj(t)
        for prn in prns:
            wk, tow = datetime_to_tow(t)
            gps_r, gps_v, clock_err, clock_rate_err = calc_sat_pos(ephem[prn], tow, week = wk)

            # TODO: Should we be applying sagnac correction here?

            # Compute doppler
            los_r = gps_r - r
            ratepred = dot(gps_v - v, los_r) / norm(los_r)
            shift = (-ratepred / gps.c - clock_rate_err)* gps.l1
            # Compute range
            rangepred = norm(r - gps_r)
            # Apply GPS satellite clock correction
            rangepred -= clock_err * gps.c

            ranges[prn].append(rangepred)
            dopplers[prn].append(shift)
    for prn in prns:
        ranges[prn] = np.array(ranges[prn])
        dopplers[prn] = np.array(dopplers[prn])
    return ranges, dopplers, times

def minimize_doppler_error(obs_dopp, times, pred_dopp, plot = False):
    norm_dopp_err = np.zeros_like(times)
    prns = obs_dopp.keys()
    for i, t in enumerate(times):
        d_diff = {prn: obs_dopp[prn] - pred_dopp[prn][i] for prn in prns}
        mean = np.mean(d_diff.values())
        sum_dopp_err_sq = sum([(d_diff[prn] - mean) ** 2 for prn in prns])
        norm_dopp_err[i] = math.sqrt(sum_dopp_err_sq)

    if plot:
        import matplotlib.pyplot as plt
        ax = plt.figure(figsize=(8,4)).gca()
        plt.title("Time of capture refinement by pseudodoppler vs prior trajectory\n")
        plt.ylabel('Pseudodoppler error norm / Hz')
        ax.plot(times, norm_dopp_err,  'b+-')
        plt.show()

    i_min = np.argmin(norm_dopp_err)
    return i_min, times[i_min]

def plot_expected_vs_measured(acqed_prns, prn_ref,
                              obs_pr, obs_dopp,
                              prior_traj, t_better,
                              ephem):
    import matplotlib.pyplot as plt

    # Compute predicted observables around this new estimate of capture time
    pred_ranges, pred_dopplers, times = predict_observables(prior_traj, t_better, acqed_prns, ephem, 20)
    pred_pr = pseudoranges_from_ranges(pred_ranges, prn_ref)

    ax = plt.figure(figsize=(12,6)).gca()
    plt.title("Code pseudophase referred to PRN %d.\n" % (prn_ref + 1) +
          "Solid lines are predicted pseudophase for each GPS sat.\n" +
          "Dotted lines are observed pseudophases")
    plt.ylabel('Code phase / m')

    colors = "bgrcmyk"
    for i, prn in enumerate(acqed_prns):
        color = colors[i % len(colors)]
        ax.plot([times[0], times[-1]], [obs_pr[prn], obs_pr[prn]], color + ':')
        ax.plot(times, pred_pr[prn], color + '-')

    ax = plt.figure(figsize=(12,6)).gca()
    plt.title("Code pseudophase error (observed - predicted).\n" +
          "Ideally these should come to a minimum (< 10 km) at the true time of capture.\n"
          "Note, this is still coupled to the prior trajectory.")
    plt.ylabel('Code phase error / m')
    for i, prn in enumerate(acqed_prns):
        color = colors[i % len(colors)]
        if i > 0:
            ax.plot(times, [obs_pr[prn] - pr for pr in pred_pr[prn]], color + '-')
    #plt.ylim([-300,300])
    #plt.xlim([datetime.datetime(2014,5,4,0,44,13),datetime.datetime(2014,5,4,0,44,14)])

    ax = plt.figure(figsize=(12,6)).gca()
    plt.title("norm(code pseudophase error)\n"
          "Note, this is still coupled to the prior trajectory.")
    plt.ylabel('norm(Code phase error) / km')
    norm_err = np.zeros_like(times)
    for i, prn in enumerate(acqed_prns):
        norm_err += [(obs_pr[prn] - pr) ** 2 for pr in pred_pr[prn]]
    norm_err /= len(acqed_prns)
    norm_err = [math.sqrt(e)/1e3 for e in norm_err]
    ax.plot(times, norm_err)
#    i = times.index(t_better)
    plt.show()

def sagnac(gps_r, tof):
    # Apply Sagnac correction (reference frame rotation during signal time of flight)
    wEtau = gps.omegae_dot * tof # Rotation of Earth during time of flight in radians.
    gps_r_sagnac = np.empty_like(gps_r)
    gps_r_sagnac[0] = gps_r[0] + wEtau * gps_r[1];
    gps_r_sagnac[1] = gps_r[1] - wEtau * gps_r[0];
    gps_r_sagnac[2] = gps_r[2];
    return gps_r_sagnac

def pt_step(r_recv, delta_t, ephem, obs_pr, t_recv_ref):
    # t_recv = t_recv_ref + delta_t
    residuals = []
    los = {}
    tot = {}
    wk, tow_ref = datetime_to_tow(t_recv_ref)

    for prn, ob_pr in obs_pr.iteritems():
        range_obs = ob_pr + delta_t * gps.c
        tof = range_obs / gps.c
        tot[prn] = tow_ref - tof

        # Compute predicted range
        gps_r, gps_v, clock_err, clock_rate_err = calc_sat_pos(ephem[prn], tot[prn], week = wk)
        gps_r_sagnac = sagnac(gps_r, tof)
        line_of_sight = gps_r_sagnac - r_recv
        range_pred = norm(line_of_sight)
        # Apply GPS satellite clock correction
        range_pred -= clock_err * gps.c

        range_residual = range_pred - range_obs

        residuals.append(range_residual)
        los[prn] = -line_of_sight / norm(line_of_sight)
    return residuals, los, tot

def p_solve(r_init, t_recv, obs_pr, ephem):
    # TODO: Adapt libswiftnav solver instead.  This is way slow.
    # Solve for position given pseudoranges, time of reception and initial position guess
    def score(params):
        r = params[0:3]
        delta_t = params[3]
        residuals, _, _ = pt_step(r, delta_t, ephem, obs_pr, t_recv)
        return norm(residuals)
    params_init = np.append(r_init, [gps.nominal_range / gps.c])
    params_min = fmin_powell(score, params_init, disp = False)
    r_sol = params_min[0:3]
    residuals, los, tot = pt_step(r_sol, params_min[3], ephem, obs_pr, t_recv)
    return r_sol, residuals, los, tot

def pt_solve(r_init, t_init, obs_pr, ephem):
    # Solve for position and time given pseudoranges and initial guess for position and time of reception
    # Implemented as an outer loop around p_solve
    def score(params):
        delta_t_recv = params[0]
        t_recv = t_init + timedelta(seconds = delta_t_recv)
        r_sol, residuals, los, tot = p_solve(r_init, t_recv, obs_pr, ephem)
        return norm(residuals)
    params_min = fmin(score, [0], disp = True)
    t_sol = t_init + timedelta(seconds = params_min[0])
    r_sol, residuals, los, tot = p_solve(r_init, t_sol, obs_pr, ephem)
    return r_sol, t_sol, los, tot, residuals

def plot_t_recv_sensitivity(r_init, t_ref, obs_pr, ephem, spread = 0.2, step = 0.025):
    import matplotlib.pyplot as plt
    times = [t_ref + dt(offset) for offset in np.arange(-spread, spread, step)]
    scores = []
    t_sols = []
    ax = plt.figure(figsize=(12,6)).gca()
    plt.ylabel('Residual norm / m')
    for t_recv in times:
        r_sol, residuals, _, _ = p_solve(r_init, t_recv, obs_pr, ephem)
        scores.append(np.linalg.norm(residuals))
    ax.plot(times, scores,'+-')
    plt.xlabel('t_recv (step = %.0f ms)' % (step / 1E-3))
    plt.ylim([0, max(scores)])
    plt.title('Sensitivity of solution to reception time')
    plt.show()

def vel_solve(r_sol, t_sol, ephem, obs_pseudodopp, los, tot):
    prns = los.keys()
    pred_prr = {}
    for prn in prns:
        _, gps_v, _, clock_rate_err = calc_sat_pos(ephem[prn], tot[prn])
        pred_prr[prn] = -dot(gps_v, los[prn]) + clock_rate_err * gps.c

    los = np.array(los.values())
    obs_prr = -(np.array(obs_pseudodopp.values()) / gps.l1) * gps.c
    pred_prr = np.array(pred_prr.values())

    prr_err = obs_prr - pred_prr

    G = np.append(los, (np.array([[1] * len(prns)])).transpose(), 1)

    X = prr_err

    sol, v_residsq, _, _ = np.linalg.lstsq(G, X)
    v_sol = sol[0:3]
    f_sol = (sol[3] / gps.c) * gps.l1
    print "Velocity residual norm: %.1f m/s" % math.sqrt(v_residsq)
    print "Receiver clock frequency error: %+6.1f Hz" % f_sol
    return v_sol, f_sol

def postprocess_short_samples(signal, prior_trajectory, t_prior, settings,
                              plot = True):
    """
    Postprocess a short baseband sample record into a navigation solution.

    Parameters
    ----------
    sample_filename : string
      Filename to load baseband samples from
    prior_traj : state vector tuple ([x,y,z], [vx, vy, vz]) or function f(t)
      This specifies the prior estimate of the receiver trajectory.
      It can either be a single position / velocity state vector, or
      a function of time.
      It is given in the ECEF frame in meters and meters / second.
    t_prior : datetime
      Prior estimate of the time the samples were captures (on GPST timescale)
    settings : peregrine settings class
      e.g. from peregrine.initSettings.initSettings()
    plot : bool
      Make pretty graphs.

    Returns
    -------
    acq_results : [:class:`AcquisitionResult`]
      List of :class:`AcquisitionResult` objects loaded from the file.

    """

    if hasattr(prior_trajectory, '__call__'):
        prior_traj_func = True
        prior_traj = prior_trajectory
    else:
        prior_traj_func = False
        prior_traj = lambda t: prior_trajectory

    sig_len_ms = len(signal) / settings.samplingFreq / 1E-3
    print "Signal is %.2f ms long." % sig_len_ms

    r_prior, v_prior = prior_traj(t_prior)

    ephem = peregrine.ephemeris.obtain_ephemeris(t_prior, settings)
    n_codes_integrate = min(15, int(sig_len_ms / 2))

    obs_cache_dir = os.path.join(settings.cacheDir, "obs")
    obs_cache_file = os.path.join(obs_cache_dir, hashlib.md5(signal).hexdigest())
    if settings.useCache and os.path.exists(obs_cache_file):
        with open(obs_cache_file, 'rb') as f:
            (acqed_prns, obs_cp, obs_dopp) = cPickle.load(f)
        print "Loaded cached observations from '%s'." % obs_cache_file
    else:
        print "Performing acquisition with %d ms integration." % n_codes_integrate
        acqed = peregrine.warm_start.warm_start(signal,
                                                t_prior, r_prior, v_prior,
                                                ephem, settings,
                                                n_codes_integrate)

        # If acquisition failed, update the cache accordingly and abort
        if len(acqed)==0:
            logger.error("Acquisition failed, aborting processing of this capture")
            if settings.useCache:
                if not os.path.exists(obs_cache_dir):
                    os.makedirs(obs_cache_dir)
                with open(obs_cache_file, 'wb') as f:
                    cPickle.dump(([], None, None), f,
                                 protocol=cPickle.HIGHEST_PROTOCOL)
                logger.error("Marked failed acquisition in cache")
            return

        # Rearrange to put sat with smallest range-rate first.
        # This makes graphs a bit less hairy.
        acqed.sort(key = lambda a: abs(a.doppler))

        acqed_prns = [a.prn for a in acqed]

        # Improve the observables with fine correlation search
        obs_cp, obs_dopp = refine_obs(signal, acqed[:], settings, plot = plot)

        if settings.useCache:
            if not os.path.exists(obs_cache_dir):
                os.makedirs(obs_cache_dir)
            with open(obs_cache_file, 'wb') as f:
                cPickle.dump((acqed_prns, obs_cp, obs_dopp), f,
                             protocol=cPickle.HIGHEST_PROTOCOL)

    # Check whether we have enough satellites
    if len(acqed_prns) < 5:
        logger.error(("Acquired %d SVs; need at least 5 for a solution" +
                      " in short-capture mode.") % len(acqed_prns))
        return

    # Determine the reference PRN
    prn_ref = acqed_prns[0]
    print "PRNs in use: " + str([p + 1 for p in acqed_prns])


    # Improve the time part of the prior estimate by minimizing doppler residuals
    pred_ranges, pred_dopplers, times = predict_observables(prior_traj, t_prior,
                                                            acqed_prns, ephem,
                                                            30)
    i, t_better = minimize_doppler_error(obs_dopp, times, pred_dopplers,
                                         plot = plot)

    # Revise the prior state vector based on this new estimate of capture time
    r_better, v_better = prior_traj(t_better)
    delta_t = (t_better - t_prior).total_seconds()
    delta_r = np.linalg.norm(np.array(r_better) - r_prior)
    print "By minimizing doppler residuals, adjusted the prior time and position by %.6s seconds, %.3f km" % (
        delta_t, delta_r/ 1e3)
    pred_ranges, pred_dopplers, times = predict_observables(
        prior_traj, t_better, acqed_prns, ephem, 1e-9)

    pred_pr_t_better = {prn: pred_ranges[prn][0] for prn in acqed_prns}

    # Resolve code phase integers to find observed pseudoranges
    obs_pr = {prn: (obs_cp[prn] / gps.chip_rate) * gps.c for prn in acqed_prns}
    obs_pr = resolve_ms_integers(obs_pr, pred_pr_t_better, prn_ref, disp = True)

    if plot:
        plot_expected_vs_measured(acqed_prns, prn_ref, obs_pr, obs_dopp,
                                  prior_traj, t_better, ephem)

    # Perform PVT navigation solution
    r_sol, t_sol, los, tot, residuals = pt_solve(r_better, t_better, obs_pr,
                                                 ephem)
    resid_norm_norm = norm(residuals) / len(acqed_prns)
    print "PVT solution residuals:",residuals
    print "PVT solution residual norm (meters per SV):",resid_norm_norm

    if resid_norm_norm > settings.navSanityMaxResid:
        logger.error("PVT solution not satisfactorily converged: %.0f > %.0f" % (
            resid_norm_norm, settings.navSanityMaxResid))
        return

    print "Position: " + str(r_sol)
    print "t_sol:  " + str(t_sol)
    print "t_prior: " + str(t_prior)
    v_sol, rx_freq_err = vel_solve(r_sol, t_sol, ephem, obs_dopp, los, tot)
    print "Velocity: %s (%.1f m/s)" % (v_sol, norm(v_sol))

    # How accurate is the time component of the solution?
    if plot:
        plot_t_recv_sensitivity(r_sol, t_sol, obs_pr, ephem,
                                spread = 0.1, step = 0.01)

    return r_sol, v_sol, t_sol

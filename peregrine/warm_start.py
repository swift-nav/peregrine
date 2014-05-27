import peregrine.almanac as almanac
import peregrine.ephemeris as ephemeris
import peregrine.acquisition as acquisition
import peregrine.gps_constants as gps
import logging
logger = logging.getLogger(__name__)

def warm_start(signal, t_prior, r_prior, v_prior, alm, ephem, settings,
               n_codes_integrate = 8):
    """
    Perform rapid / more-sensitive acquisition based on a prior estimate of the
    receiver's position, velocity and time.
    """

    pred = almanac.whatsup(alm, r_prior, t_prior)
    pred_dopp = ephemeris.pred_dopplers(pred, ephem, r_prior, v_prior, t_prior)
    if settings.acqSanityCheck:
        notup = almanac.whatsdown(alm, r_prior, t_prior)
    else:
        notup = []

    # Acquisition
    a = acquisition.Acquisition(signal, settings.samplingFreq,
                                          settings.IF,
                                          settings.samplingFreq * gps.code_period,
                                          n_codes_integrate=n_codes_integrate)
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

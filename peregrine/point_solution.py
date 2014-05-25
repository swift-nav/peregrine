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

import gps_constants as gps

def pseudoranges_from_ranges(ranges, prn_ref):
    pseudoranges = {}
    for prn, rngs in ranges.iteritems():
        pseudoranges[prn] = rngs - ranges[prn_ref]
    return pseudoranges

def resolve_ms_integers(obs_pr, pred_pr, prn_ref, disp = True):
    # Solve for the pseudorange millisecond ambiguities
    obs_pr = pseudoranges_from_ranges(obs_pr, prn_ref)

    if disp:
        print "Resolving millisecond integers:"

    for prn, pr in obs_pr.iteritems():
        pr_int_est = (pred_pr[prn] - pr) / gps.code_wavelength
        pr_int = round(pr_int_est)
        if abs(pr_int - pr_int_est) > 0.1:
            print "WARNING: Pseudorange integer for PRN %2d is %.4f" % prn + \
                  ", which isn't very close to an integer."
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

from peregrine.time import datetime_to_tow
import peregrine.gps_constants as gps
from datetime import datetime, timedelta
import numpy as np
from numpy import dot
from numpy.linalg import norm
from math import radians, degrees, sin, cos, asin, acos, sqrt, fabs, atan2
import os, os.path, subprocess
import urllib

def load_rinex_nav_msg(filename, t, settings):
    """
    Import a set of GPS ephemerides from a RINEX 2 or 3 GNSS Navigation Message file

    Parameters
    ----------
    filename : string
      Path to a RINEX 2 or 3 GNSS Navigation Message File
      e.g. from http://igs.bkg.bund.de/root_ftp/NTRIP/BRDC_v3/ or http://qz-vision.jaxa.jp/USE/archives/ephemeris/
    t : datetime
      The time of your observations.  The navigation message files usually
      contain multiple ephemerides over a range of epochs; load_rinex3_nav_msg
      will return the ephemeris set with epoch closest to t.

    Returns
    -------
    ephem : dict of dicts
      dict by 0-indexed PRN of the ephemeris parameters.
      e.g. ephem[21]['af0'] contains the first-order clock correction for PRN 22.

    """
    f = open(filename,'r')
    ephem = {}

    got_header = False
    best_depoch = {}
    rinex_ver = None
    while True:
        line = f.readline()[:-1]
        if not line:
            break
        if got_header == False:
            if rinex_ver is None:
                if line[60:80] != "RINEX VERSION / TYPE":
                    print line
                    raise FormatException("Doesn't appear to be a RINEX file")
                rinex_ver = int(float(line[0:9]))
                print "Rinex version", rinex_ver
                if line[20] != "N":
                    raise FormatException("Doesn't appear to be a Navigation Message file")
            if line[60:73] == "END OF HEADER":
                got_header = True
            continue
        if rinex_ver == 3:
            if line[0] != 'G':
                continue

        if rinex_ver == 3:
            prn = int(line[1:3]) - 1
            epoch = datetime.strptime(line[4:23], "%Y %m %d %H %M %S")
        elif rinex_ver == 2:
            prn = int(line[0:2]) - 1
            epoch = datetime.strptime(line[3:20], "%y %m %d %H %M %S")
            line = ' ' + line # Shift 1 char to the right

        depoch = abs(epoch - t)
        if prn not in best_depoch or depoch < best_depoch[prn]:
            line = line.replace('D','E') # Handle bizarro float format
            best_depoch[prn] = depoch
            e = {'epoch': epoch, 'prn': prn}
            e['toc'] = datetime_to_tow(epoch)
            e['af0'] = float(line[23:42])
            e['af1'] = float(line[42:61])
            e['af2'] = float(line[61:80])
            def read4(f):
                line = f.readline()[:-1]
                if rinex_ver == 2: line = ' ' + line # Shift 1 char to the right
                line = line.replace('D','E') # Handle bizarro float format
                return  float(line[4:23]), float(line[23:42]),\
                        float(line[42:61]), float(line[61:80])
            e['iode'], e['crs'], e['dn'], e['m0'] = read4(f)
            e['cuc'], e['ecc'], e['cus'], e['sqrta'] = read4(f)
            toe, e['cic'], e['omega0'], e['cis'] = read4(f)
            e['inc'], e['crc'], e['w'], e['omegadot'] = read4(f)
            e['inc_dot'], e['l2_codes'], week, e['l2_pflag'] = read4(f)
            e['sv_accuracy'], e['health'], e['tgd'], e['iodc'] = read4(f)
            f.readline() # Discard last row

            e['toe'] = week % 1024, toe # TODO: check mod-1024 situation
            e['healthy'] = (e['health'] == 0.0) and depoch < timedelta(
                seconds = settings.ephemMaxAge)
            ephem[prn] = e
        else: # Don't bother with this entry, time is too far off
            for l in range(7): f.readline() # Discard 7 lines
    f.close()
    count_healthy = sum([1 for e in ephem.values() if e['healthy']])
    print "Ephemeris '%s' loaded with %d healthy satellites." % (
        filename, count_healthy)
    return ephem

def obtain_ephemeris(t, settings):
    """
    Finds an appropriate GNSS ephemeris file for a certain time,
    downloading from BKG's Internet server if not already cached.

    Parameters
    ----------
    cache_dir : string, optional
      Absolute or relative path to search for cached ephemerides, and store
      downloaded ones in.

    t : datetime
      The time of your observations.  obtain_ephemeris will attempt to find the
      appropriate file.

    Returns
    -------
    ephem : dict of dicts
      dict by 0-indexed PRN of the ephemeris parameters.
      e.g. ephem[21]['af0'] contains the first-order clock correction for PRN 22.
    """
    print "Obtaining ephemeris file for ", t

    #TODO: If it's today and more than 1 hr old, check for an update

    filename = t.strftime("brdc%j0.%yn")
    filedir = os.path.join(settings.cacheDir, "ephem")
    filepath = os.path.join(filedir, filename)
    url = t.strftime(
        'http://qz-vision.jaxa.jp/USE/archives/ephemeris/%Y/') + filename
    if not os.path.isfile(filepath):
        if not os.path.exists(filedir):
            os.makedirs(filedir)
        _, hdrs = urllib.urlretrieve(url, filepath)
    ephem = load_rinex_nav_msg(filepath, t, settings)
    if len(ephem) < 22:
        raise ValueError(
            "Unable to parse ephemeris file '%s' " % filename +
            "(or surprisingly few sats in it)")
    return ephem

def calc_sat_pos(eph, tow, week = None, warn_stale = True):

    # Clock correction (except for general relativity which is applied later)
    tdiff = tow - eph['toc'][1] # Time of clock
    if week is not None:
        tdiff += (week - eph['toc'][0]) * 7 * 86400
    clock_err = eph['af0'] + tdiff * (eph['af1'] + tdiff * eph['af2']) - eph['tgd']
    clock_rate_err = eph['af1'] + 2 * tdiff * eph['af2']

    # Orbit propagation
    tdiff = tow - eph['toe'][1] # Time of ephemeris (might be different from time of clock)
    if week is not None:
        tdiff += (week - eph['toe'][0]) * 7 * 86400
    if warn_stale and abs(tdiff) > 12 * 3600:
        print "WARNING: PRN %2d using ephemeris %.1f hours old!" % (
            eph['prn'] + 1, tdiff / 3600.0)
        print tdiff, tow, eph['toe']

    # Calculate position per IS-GPS-200D p 97 Table 20-IV
    a = eph['sqrta'] * eph['sqrta']  # [m] Semi-major axis
    ma_dot = sqrt (gps.earth_gm / (a * a * a)) + eph['dn'] # [rad/sec] Corrected mean motion
    ma = eph['m0'] + ma_dot * tdiff  # [rad] Corrected mean anomaly

    # Iteratively solve for the Eccentric Anomaly (from Keith Alter and David Johnston)
    ea = ma      # Starting value for E

    ea_old = 2222
    while fabs (ea - ea_old) > 1.0E-14:
      ea_old = ea
      tempd1 = 1.0 - eph['ecc'] * cos (ea_old)
      ea = ea + (ma - ea_old + eph['ecc'] * sin (ea_old)) / tempd1
    ea_dot = ma_dot / tempd1

    # Relativistic correction term
    einstein = -4.442807633E-10 * eph['ecc'] * eph['sqrta'] * sin (ea)

    # Begin calc for True Anomaly and Argument of Latitude
    tempd2 = sqrt (1.0 - eph['ecc'] * eph['ecc'])
    # [rad] Argument of Latitude = True Anomaly + Argument of Perigee
    al = atan2 (tempd2 * sin (ea), cos (ea) - eph['ecc']) + eph['w']
    al_dot = tempd2 * ea_dot / tempd1

    # Calculate corrected argument of latitude based on position
    cal = al + eph['cus'] * sin (2.0 * al) + eph['cuc'] * cos (2.0 * al)
    cal_dot = al_dot * (1.0 + 2.0 * (eph['cus'] * cos (2.0 * al) - \
           eph['cuc'] * sin (2.0 * al)))

    # Calculate corrected radius based on argument of latitude
    r = a * tempd1 + eph['crc'] * cos (2.0 * al) + \
      eph['crs'] * sin (2.0 * al)
    r_dot = a * eph['ecc'] * sin (ea) * ea_dot + \
      2.0 * al_dot * (eph['crs'] * cos (2.0 * al) - \
                      eph['crc'] * sin (2.0 * al))

    # Calculate inclination based on argument of latitude
    inc = eph['inc'] + eph['inc_dot'] * tdiff + \
      eph['cic'] * cos (2.0 * al) + eph['cis'] * sin (2.0 * al)
    inc_dot = eph['inc_dot'] + 2.0 * al_dot * (eph['cis'] * cos (2.0 * al) - \
             eph['cic'] * sin (2.0 * al))

    # Calculate position and velocity in orbital plane
    x = r * cos (cal)
    y = r * sin (cal)
    x_dot = r_dot * cos (cal) - y * cal_dot
    y_dot = r_dot * sin (cal) + x * cal_dot

    # Corrected longitude of ascending node
    om_dot = eph['omegadot'] - gps.omegae_dot
    om = eph['omega0'] + tdiff * om_dot - gps.omegae_dot * eph['toe'][1]

    # Compute the satellite's position in Earth-Centered Earth-Fixed coordiates
    pos = np.empty(3)
    pos[0] = x * cos (om) - y * cos (inc) * sin (om)
    pos[1] = x * sin (om) + y * cos (inc) * cos (om)
    pos[2] = y * sin (inc)

    tempd3 = y_dot * cos (inc) - y * sin (inc) * inc_dot

    # Compute the satellite's velocity in Earth-Centered Earth-Fixed coordiates
    vel = np.empty(3)
    vel[0] = -om_dot * pos[1] + x_dot * cos (om) - tempd3 * sin (om)
    vel[1] = om_dot * pos[0] + x_dot * sin (om) + tempd3 * cos (om)
    vel[2] = y * cos (inc) * inc_dot + y_dot * sin (inc)

    clock_err += einstein

    return pos, vel, clock_err, clock_rate_err


def pred_dopplers(prns, ephem, r, v, t):
    wk, tow = datetime_to_tow(t)

    dopplers = []
    for prn in prns:
        gps_r, gps_v, clock_err, clock_rate_err = calc_sat_pos(ephem[prn],
                                        tow, week = wk, warn_stale = False)
        los_r = gps_r - r
        ratepred = dot(gps_v - v, los_r) / norm(los_r)
        dopplers.append((-ratepred / gps.c - clock_rate_err) * gps.l1)
    return dopplers

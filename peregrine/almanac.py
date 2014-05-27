from math import radians, degrees, sin, cos, asin, acos, sqrt
from numpy.linalg import norm
import swiftnav
import swiftnav.almanac
from peregrine.time import *

def horizon_dip(r):
    # Approximation to the dip angle of the horizon.
    lat, lon, height = swiftnav.coord_system.wgsecef2llh(r[0], r[1], r[2])
    r_e = norm(swiftnav.coord_system.wgsllh2ecef(lat, lon, 0))
    return degrees(-acos(r_e / norm(r_e + height)))

def grok_almanac(filename):
    f = open(filename,'r')
    alm = {}
    while True:
        rows=[]
        for n in range(0,14):
            rows.append(f.readline().rstrip())
        if len(rows[0]) == 0:
            break
        for c in range(0, len(rows[0]), 10):
            fields = [r[c:c+10] for r in rows]
            prn = int(fields[0]) - 1 # Convert to Swift convention (0-indexed PRNs everywhere execpt printed output)
            if prn >= 32:  # Discard GLONASS, WAAS etc
                break
            # Parse all the fields, converting units to swiftnav's preferred
            health = fields[1].strip() == '0'
            ecc = float(fields[2])
            a = float(fields[3])**2
            raan = radians(float(fields[4]))
            argp = radians(float(fields[5]))
            M = radians(float(fields[6]))
            toa = float(fields[7])
            i = radians(-float(fields[8]) + 54.0) # given as offset to 54 degrees
            rora = radians(float(fields[9])/1000.0)
            af0 = float(fields[10]) * 1E-9
            af1 = float(fields[11]) * 1E-9
            week = int(fields[12]) % 1024
            raaw = raan - rora * toa
            alm[prn] = swiftnav.almanac.Almanac(ecc, toa, i, rora, a, raaw, argp, M, af0, af1, week, prn, health)
    return alm



def whatsup(alm, r, t, mask = None):
    if mask is None: # If elevation mask not specified, calculate it from the horizon dip angle
        mask = horizon_dip(r)
    wk, tow = datetime_to_tow(t)
    satsup = []
    for a in alm:
        az, el = alm[a].calc_az_el(tow, r, wk)
        if alm[a].healthy and degrees(el) > mask:
            satsup.append(alm[a].prn)
    return satsup

def whatsdown(alm, r, t, mask = -45): # Return sats *below* a certain mask, for sanity check
    wk, tow = datetime_to_tow(t)
    satsdown = []
    for a in alm:
        az, el = alm[a].calc_az_el(tow, r, wk)
        if degrees(el) < mask:
            satsdown.append(alm[a].prn)
    return satsdown

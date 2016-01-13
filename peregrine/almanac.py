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

from math import radians, degrees, sin, cos, asin, acos, sqrt
from numpy.linalg import norm
from peregrine.gps_time import *
from swiftnav.almanac import Almanac

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
            # Convert to Swift convention (0-indexed PRNs everywhere execpt printed output)
            prn = int(fields[0]) - 1
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
            alm[prn] = swiftnav.almanac.Almanac(ecc, toa, i, rora, a, raaw,
                                                argp, M, af0, af1, week,
                                                prn, health)
    return alm

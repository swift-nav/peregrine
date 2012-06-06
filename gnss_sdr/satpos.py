#!/usr/bin/python
#--------------------------------------------------------------------------
#                           SoftGNSS v3.0
# 
# Copyright (C) Darius Plausinaitis and Dennis M. Akos
# Written by Darius Plausinaitis and Dennis M. Akos
# Converted to Python by Colin Beighley
#--------------------------------------------------------------------------
#This program is free software; you can redistribute it and/or
#modify it under the terms of the GNU General Public License
#as published by the Free Software Foundation; either version 2
#of the License, or (at your option) any later version.
#
#This program is distributed in the hope that it will be useful,
#but WITHOUT ANY WARRANTY; without even the implied warranty of
#MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#GNU General Public License for more details.
#
#You should have received a copy of the GNU General Public License
#along with this program; if not, write to the Free Software
#Foundation, Inc., 51 Franklin Street, Fifth Floor, Boston, MA  02110-1301,
#USA.
#--------------------------------------------------------------------------

def satpos(transmitTime, prnList, eph, settings):
  numOfSatellites = len(prnList)
  gpsPi       = 3.1415926535898   # Pi used in the GPS coordinate system
  Omegae_dot  = 7.2921151467e-5;  # Earth rotation rate, [rad/s]
  GM          = 3.986005e14;      # Universal gravitational constant times
                                  # the mass of the Earth, [m^3/s^2]
  F           = -4.442807633e-10; # Constant, [sec/(meter)^(1/2)]

  satClkCorr   = [[] for i in range(numOfSatellites)]
  satPositions = [[] for i in range(numOfSatellites)]

  for satNr = range(numOfSatellites):
    prn = prnList[satNr]
    #Find initial satellite clock correction
    #Find time difference
    dt = check_t(transmitTime - eph[prn].t_oc)

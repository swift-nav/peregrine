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
import math

def satpos(transmitTime, prnList, eph, settings):
  numOfSatellites = len(prnList)
  gpsPi       = 3.1415926535898   # Pi used in the GPS coordinate system
  Omegae_dot  = 7.2921151467e-5;  # Earth rotation rate, [rad/s]
  GM          = 3.986005e14;      # Universal gravitational constant times
                                  # the mass of the Earth, [m^3/s^2]
  F           = -4.442807633e-10; # Constant, [sec/(meter)^(1/2)]

  satClkCorr   = [[] for i in range(numOfSatellites)]
  satPositions = [[] for i in range(numOfSatellites)]

  for satNr in range(numOfSatellites):
    prn = prnList[satNr]
    #Find initial satellite clock correction
    #Find time difference
    dt = check_t(transmitTime - eph[prn].t_oc)
    satClkCorr[satNr] = [eph[prn].a_f2*dt + eph[prn].a_f1*dt + \
                         eph[prn].a_f0 + eph[prn].T_GD]
   
    time = transmitTime - satClkCorr[satNr]

    #Find satellite's position
    #Restore semi-major axis
    a = (eph[prn].sqrtA)**2
    #Time correction
    tk = check_t(time - eph[prn].t_oe)
    #Initial mean motion
    n0 = math.sqrt(GM / a**3)
    #Mean motion
    n = n0 + eph[prn].deltan
    #Mean anomaly
    M = eph[prn].M_0 + n*tk
    #Reduce mean anomaly to between 0 and 2*pi
    M = (M + 2*gpsPi) % 2*gpsPi
    #Initial guess of eccentric anomaly
    E = M
    #Iteratively compute eccentric anomaly
    for i in range(10):
      E_old = E
      E = M + eph[prn].e * sin[E]
      dE = (E - E_old) % 2*gpsPi
      if abs(dE) > (10**(-12)):
        break
    #Constrain eccentric anomaly to between 0 and 2pi
    E = (E + 2*gpsPi) % (2*gpsPi)
    #Compute relativistic correction term
    dtr = F * eph[prn].e * eph[prn].sqrtA * sin(E)
    #Calculate the true anomaly
    nu = math.atan2(sqrt(1-(eph[prn].e))**2*sin(E), cos(E) - eph[prn].e)
    #Compute angle phi
    phi = nu + eph[prn].omega
    #Constrain phi to between 0 and 2pi
    phi = phi % 2*gpsPi
    #Correct argument of latitude
    u = phi + eph[prn].C_uc * cos(2*phi) + eph[prn].C_us * sin(2*phi)
    #Correct radius
    r = a * (1 - eph[prn].e*cos(E)) + eph[prn].C_rc*cos(2*phi) + eph[prn].C_rs*sin(2*phi)
    #Correct inclination
    i = eph[prn]._0 + eph[prn].iDot*tk + eph[prn].C_ic*cos[2*phi] + eph[prn].C_is*sin(2*phi)
    #Compute the angle between the ascending node and the Greenwich meridian
    Omega = eph[prn].omega_0 + (eph[prn].omedaDot - Omegae_dot)*tk - Omegae_dot * eph[prn].t_oe
    #Constrain omega to between 0 and 2pi
    Omega = (Omega + 2*gpsPi) % 2*gpsPi
    #Compute satellite coordinates
    satPositions[satNr].append(cos(u)*r * cos(Omega) - sin(u)*r*cos(i)*sin(Omega))
    satPositions[satNr].append(cos(u)*r * sin(Omega) - sin(u)*r*cos(i)*cos(Omega))
    satPositions[satNr].append(sin(u)*r * sin(i))
    #Include relativistic correciton in clock correction
    satClkCorr[satNr] = (eph[prn].a_f2 * dt + eph[prn].a_f1)*dt + eph[prn].a_f0 - eph[prn].T_GD + dtr

  return (satPositions, satClkCorr)

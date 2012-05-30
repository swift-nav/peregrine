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
import numpy as np
import bin2dec

def ephemeris(bits,D30star):
  
  if not(type(bits)==np.ndarray):
    raise Exception('bits must be a numpy.ndarray')
  if len(bits) < 1500:
    raise Exception('length of bits must be >= 1500')
  #check that bits are all either 0's or 1's
  if not((np.unique(bits) == np.array([0])).all() or \
           (np.unique(bits) == np.array([0,1])).all() or \
             (np.unique(bits) == np.array([1])).all()):
    raise Exception('bits must be all of 0s and 1s')
  if not(D30star==0 or D30star==1):
    raise Exception('D30star must be a 0 or 1')

  gpsPi = 3.1415926535898

  eph = eph_class
  
  #Decode 5 subframes and get ephemeris from subframes 1-3 
  #We have to use 5 as we don't know which subframe the first in the array is
  for i in range(5):
    #Get the i'th subframe from the bits
    subframe = bits[300*i:300*(i+1)]
    #Correct the polarity of the bits in each of the 10 words of the subframe
    for word in range(10):
      if (D30star == 1):
        subframe[np.r_[word*30:(word+1)*30]] = np.invert(subframe[np.r_[word*30:(word+1)*30]]) + 2
      D30star = subframe[(word+1)*30-1]

    #Get the subframe ID to tell which ephemeris parameters are contained within
    subframeID = bin2dec.unsigned(subframe[49:52])

    if (subframeID==1):   #WN, SV clock corrections, health and accuracy
      eph.weekNumber  = bin2dec.unsigned(subframe[60:70]) + 1024
      eph.accuracy    = bin2dec.unsigned(subframe[72:76])
      eph.health      = bin2dec.unsigned(subframe[76:82])
      eph.T_GD        = bin2dec.twoscomp(subframe[196:204]) *2**(-31)
      eph.IODC        = bin2dec.unsigned(np.concatenate((subframe[82:84],subframe[196:204])))
      eph.t_oc        = bin2dec.unsigned(subframe[218:234]) *2**4
      eph.a_f2        = bin2dec.twoscomp(subframe[240:248]) *2**(-55)
      eph.a_f1        = bin2dec.twoscomp(subframe[248:264]) *2**(-43)
      eph.a_f0        = bin2dec.twoscomp(subframe[270:292]) *2**(-31)
    elif (subframeID==2): #First section of ephemeris parameters
      eph.IODE_sf2 = bin2dec.unsigned(subframe[60:68])
      eph.C_rs     = bin2dec.twoscomp(subframe[68:84]) *2**(-5)
      eph.deltan   = bin2dec.twoscomp(subframe[90:106]) *2**(-43) * gpsPi
      eph.M_0      = bin2dec.twoscomp(np.concatenate((subframe[106:114],subframe[120:144]))) *2**(-31)*gpsPi
      eph.C_uc     = bin2dec.twoscomp(subframe[150:166]) *2**(-29)
      eph.e        = bin2dec.unsigned(np.concatenate((subframe[166:174],subframe[180:204]))) *2**(-33)
      eph.C_us     = bin2dec.twoscomp(subframe[210:226]) *2**(-29)
      eph.sqrtA    = bin2dec.unsigned(np.concatenate((subframe[226:234],subframe[240:264]))) *2**(-19)
      eph.t_oe     = bin2dec.unsigned(subframe[270:286]) *2**4
    elif (subframeID==3): #Second section of ephemeris parameters
      eph.C_ic     = bin2dec.twoscomp(subframe[60:76]) *2**(-29)
      eph.omega_0  = bin2dec.twoscomp(np.concatenate((subframe[76:84],subframe[90:114]))) *2**(-31)*gpsPi
      eph.C_is     = bin2dec.twoscomp(subframe[120:136]) *2**(-29)
      eph.i_0      = bin2dec.twoscomp(np.concatenate((subframe[136:144],subframe[150:174]))) *2**(-31)*gpsPi
      eph.C_rc     = bin2dec.twoscomp(subframe[180:196]) *2**(-5)
      eph.omega    = bin2dec.twoscomp(np.concatenate((subframe[196:204],subframe[210:234]))) *2**(-31)*gpsPi
      eph.omegaDot = bin2dec.twoscomp(subframe[240:264]) *2**(-43) * gpsPi
      eph.IODE_sf3 = bin2dec.unsigned(subframe[270:278])
      eph.iDot     = bin2dec.twoscomp(subframe[278:292]) *2**(-43) * gpsPi

    if (i==0):
      TOW = bin2dec.unsigned(subframe[30:47])*6 - 6
  
  return (eph, TOW)

class eph_class:
  def __init__():
    eph.weekNumber  = 0.0
    eph.accuracy    = 0.0
    eph.health      = 0.0
    eph.T_GD        = 0.0
    eph.IODC        = 0.0
    eph.t_oc        = 0.0
    eph.a_f2        = 0.0
    eph.a_f1        = 0.0
    eph.a_f0        = 0.0
    eph.IODE_sf2    = 0.0
    eph.C_rs        = 0.0
    eph.deltan      = 0.0
    eph.M_0         = 0.0
    eph.C_uc        = 0.0
    eph.e           = 0.0
    eph.C_us        = 0.0
    eph.sqrtA       = 0.0
    eph.t_oe        = 0.0
    eph.C_ic        = 0.0
    eph.omega_0     = 0.0
    eph.C_is        = 0.0
    eph.i_0         = 0.0
    eph.C_rc        = 0.0
    eph.omega       = 0.0
    eph.omegaDot    = 0.0
    eph.IODE_sf3    = 0.0
    eph.iDot        = 0.0

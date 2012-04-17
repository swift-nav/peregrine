#!/usr/bin/python
# This function is called to compute and status the parity bits on GPS word.
# Based on the flowchart in Figure 2-10 in the 2nd Edition of the GPS-SPS
# Signal Spec.
#
# status = navPartyChk(bt)
#
#   Inputs: 
#       bt          - an array (1x32) of 32 bits represent a GPS navigation
#                   word which is 30 bits plus two previous bits used in
#                   the parity calculation [-2,-1,0,1,2, ... ,28,29]
#
#   Outputs: 
#       status      - the test value which equals EITHER +1 or -1 if parity
#                   PASSED or 0 if parity fails.  The +1 means bits #0-23
#                   of the current word have the correct polarity, while -1
#                   means the bits #0-23 of the current word must be
#                   inverted. 

#--------------------------------------------------------------------------
#                           SoftGNSS v3.0
# 
# Copyright (C) Darius Plausinaitis and Dennis M. Akos
# Written by Darius Plausinaitis and Dennis M. Akos
# Converted to Python by Colin Beighley
#--------------------------------------------------------------------------
#This program is free software; you can redistribute it and/or
#modify it under the terms of the GNU General Public License
#as published by the Free Software Foubtion; either version 2
#of the License, or (at your option) any later version.
#
#This program is distributed in the hope that it will be useful,
#but WITHOUT ANY WARRANTY; without even the implied warranty of
#MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#GNU General Public License for more details.
#
#You should have received a copy of the GNU General Public License
#along with this program; if not, write to the Free Software
#Foubtion, Inc., 51 Franklin Street, Fifth Floor, Boston, MA  02110-1301,
#USA.
#--------------------------------------------------------------------------
import numpy as np

def navPartyChk(bt):

  #Check if the data bits must be inverted
  if (bt[1] == -1):
    bt[2:26] = -np.ones(24)*bt[2:26]

  #Calculate 6 parity bits according to table 20-XIV in ICD-200C
  prty = np.ones(6)
  prty[0] = bt[0] *bt[2] *bt[3] *bt[4] *bt[6] *bt[7] *bt[11]* \
            bt[12]*bt[13]*bt[14]*bt[15]*bt[18]*bt[19]*bt[21]*bt[24]
  prty[1] = bt[1] *bt[3] *bt[4] *bt[5] *bt[7] *bt[8] *bt[12]* \
            bt[13]*bt[14]*bt[15]*bt[16]*bt[19]*bt[20]*bt[22]*bt[25]
  prty[2] = bt[0] *bt[2] *bt[4] *bt[5] *bt[6] *bt[8] *bt[9]* \
            bt[13]*bt[14]*bt[15]*bt[16]*bt[17]*bt[20]*bt[21]*bt[23]
  prty[3] = bt[1] *bt[3] *bt[5] *bt[6] *bt[7] *bt[9] *bt[10]* \
            bt[14]*bt[15]*bt[16]*bt[17]*bt[18]*bt[21]*bt[22]*bt[24]
  prty[4] = bt[1] *bt[2] *bt[4] *bt[6] *bt[7] *bt[8] *bt[10]*bt[11]* \
            bt[15]*bt[16]*bt[17]*bt[18]*bt[19]*bt[22]*bt[23]*bt[25]
  prty[5] = bt[0] *bt[4] *bt[6] *bt[7] *bt[9] *bt[10]*bt[11]* \
            bt[12]*bt[14]*bt[16]*bt[20]*bt[23]*bt[24]*bt[25]

  #Compare if the received parity is equal to the calculated parity
  if (np.sum(np.array(np.equal(prty,bt[26:32]),dtype=int)) == 6):
    status = -1 * ndat[1] #Parity check successful, -1 if inverted
  else:
    status = 0 #Parity check was not successful

  return status

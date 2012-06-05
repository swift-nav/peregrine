#!/usr/bin/python
# This function is called to compute and status the parity bits on GPS word.
# Based on the flowchart in Figure 2-10 in the 2nd Edition of the GPS-SPS
# Signal Spec.
#
# status = navPartyChk(word)
#
#   Inputs: 
#       word          - an array (1x32) of 32 bits represent a GPS navigation
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

def navPartyChk(wordstar,word):

  #Check if the data bits must be inverted
  if (wordstar[1] == -1):
    word[0:24] = -np.ones(24)*word[0:24]

  #Calculate 6 parity bits according to table 20-XIV in ICD-200C
  prty = np.ones(6)
  prty[0] = wordstar[0] *word[0] *word[1] *word[2] *word[4] *word[5] *word[9]* \
            word[10]*word[11]*word[12]*word[13]*word[16]*word[17]*word[19]*word[22]
  prty[1] = wordstar[1] *word[1] *word[2] *word[3] *word[5] *word[6] *word[10]* \
            word[11]*word[12]*word[13]*word[14]*word[17]*word[18]*word[20]*word[23]
  prty[2] = wordstar[0] *word[0] *word[2] *word[3] *word[4] *word[6] *word[7]* \
            word[11]*word[12]*word[13]*word[14]*word[15]*word[18]*word[19]*word[21]
  prty[3] = wordstar[1] *word[1] *word[3] *word[4] *word[5] *word[7] *word[8]* \
            word[12]*word[13]*word[14]*word[15]*word[16]*word[19]*word[20]*word[22]
  prty[4] = wordstar[1] *word[0] *word[2] *word[4] *word[5] *word[6] *word[8]*word[9]* \
            word[13]*word[14]*word[15]*word[16]*word[17]*word[20]*word[21]*word[23]
  prty[5] = wordstar[0] *word[2] *word[4] *word[5] *word[7] *word[8] *word[9]* \
            word[10]*word[12]*word[14]*word[18]*word[21]*word[22]*word[23]

  #Compare if the received parity is equal to the calculated parity
  if (np.sum(np.array(np.equal(prty,word[24:30]),dtype=int)) == 6):
    status = -1 * wordstar[1] #Parity check successful, -1 if inverted
  else:
    status = 0 #Parity check was not successful

  return status

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

def showChannelStatus(channel,settings):
  print ""
  print "*=========*=====*===============*===========*=============*========*"
  print "| Channel | PRN |   Frequency   |  Doppler  | Code Offset | Status |"
  print "*=========*=====*===============*===========*=============*========*"
  for channelNr in range(len(channel)):
    if not(channel[channelNr].status == '-'):
      print("|      %2d | %3d |  %2.5e  |   % 5d   |  %9s  |    %1s   |" % \
            (channelNr+1, \
            channel[channelNr].PRN + 1, \
            channel[channelNr].acquiredFreq, \
            round(channel[channelNr].acquiredFreq - settings.IF), \
            #+1 to match octave
            ("%4.4f" % (1023-(channel[channelNr].codePhase+1)/(settings.samplingFreq/1.023e6))), \
            channel[channelNr].status))
    else:
      print("|      %2d | --- |  ------------ |   -----   |    ------   |   Off  |" % channelNr)


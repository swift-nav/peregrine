# Copyright (C) 2012 Swift Navigation Inc.
#
# This source is subject to the license found in the file 'LICENSE' which must
# be be distributed together with this source. All other rights reserved.
#
# THIS CODE AND INFORMATION IS PROVIDED "AS IS" WITHOUT WARRANTY OF ANY KIND,
# EITHER EXPRESSED OR IMPLIED, INCLUDING BUT NOT LIMITED TO THE IMPLIED
# WARRANTIES OF MERCHANTABILITY AND/OR FITNESS FOR A PARTICULAR PURPOSE.

def showChannelStatus(channel,settings):
  print ""
  print "*======================ACQUISITION RESULTS=========================*"
  print "*=========*=====*===============*===========*=============*========*"
  print "| Channel | PRN |   Frequency   |  Doppler  | Code Offset | Status |"
  print "*=========*=====*===============*===========*=============*========*"
  for channelNr in range(len(channel)):
    if not(channel[channelNr].status == '-'):
      print("|      %2d | %3d |  %2.5e  |   % 5d   |  %9s  |    %1s   |" % \
            (channelNr+1, \
            channel[channelNr].PRN + 1, \
            channel[channelNr].carrFreq, \
            round(channel[channelNr].carrFreq - settings.IF), \
            #+1 to match octave
            ("%4.4f" % (1023-(channel[channelNr].codePhase+1)/(settings.samplingFreq/1.023e6))), \
            channel[channelNr].status))
    else:
      print("|      %2d | --- |  ------------ |   -----   |    ------   |   Off  |" % channelNr)

  print "*=========*=====*===============*===========*=============*========*"
  print "*==================================================================*"

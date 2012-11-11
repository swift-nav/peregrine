# Copyright (C) 2012 Swift Navigation Inc.
#
# This source is subject to the license found in the file 'LICENSE' which must
# be be distributed together with this source. All other rights reserved.
#
# THIS CODE AND INFORMATION IS PROVIDED "AS IS" WITHOUT WARRANTY OF ANY KIND,
# EITHER EXPRESSED OR IMPLIED, INCLUDING BUT NOT LIMITED TO THE IMPLIED
# WARRANTIES OF MERCHANTABILITY AND/OR FITNESS FOR A PARTICULAR PURPOSE.

def calcLoopCoef(LBW, zeta, k):
  Wn = LBW*8*zeta / (4*zeta**2 + 1)
  tau1 = k / (Wn**2)
  tau2 = 2.0* zeta / Wn
  return (tau1, tau2)

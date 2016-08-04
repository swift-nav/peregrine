# Copyright (C) 2016 Swift Navigation Inc.
# Contact: Adel Mamin <adel.mamin@exafore.com>
#
# This source is subject to the license found in the file 'LICENSE' which must
# be be distributed together with this source. All other rights reserved.
#
# THIS CODE AND INFORMATION IS PROVIDED "AS IS" WITHOUT WARRANTY OF ANY KIND,
# EITHER EXPRESSED OR IMPLIED, INCLUDING BUT NOT LIMITED TO THE IMPLIED
# WARRANTIES OF MERCHANTABILITY AND/OR FITNESS FOR A PARTICULAR PURPOSE.

import numpy as np
from peregrine import defaults
from peregrine import gps_constants


class LockDetector(object):
  """
  Wraps the `libswiftnav` PLL lock detector implementation.

  The detector state, :libswiftnav:`lock_detect_t` is maintained by
  the class instance.

  """

  def __init__(self, **kwargs):
    self.lpfi = 0
    self.lpfq = 0
    self.outo = False
    self.outp = False
    self.pcount1 = 0
    self.pcount2 = 0
    self.reinit( kwargs['k1'],
                 kwargs['k2'],
                 kwargs['lp'],
                 kwargs['lo'])

  def reinit(self, k1, k2, lp, lo):
    # Adjust LPF coefficient
    self.k1 = k1
    self.k2 = k2
    self.lp = lp
    self.lo = lo

  def lpf_update(self, y, x):
    y += self.k1 * (x - y)
    return y

  def update(self, I, Q, DT):
    # Calculated low-pass filtered prompt correlations
    self.lpfi = self.lpf_update(self.lpfi, np.absolute(I) / DT)
    self.lpfq = self.lpf_update(self.lpfq, np.absolute(Q) / DT)

    a = self.lpfi / self.k2
    b = self.lpfq
    if a > b:
      # In-phase > quadrature, looks like we're locked
      self.outo = True
      self.pcount2 = 0
      # Wait before raising the pessimistic indicator
      if self.pcount1 > self.lp:
        self.outp = True
      else:
        self.pcount1 += 1
    else:
      # In-phase < quadrature, looks like we're not locked
      self.outp = False
      self.pcount1 = 0
      # Wait before lowering the optimistic indicator
      if self.pcount2 > self.lo:
        self.outo = False
      else:
        self.pcount2 += 1

    return (self.outo, self.outp, \
            self.pcount1, self.pcount2,\
            self.lpfi, self.lpfq)

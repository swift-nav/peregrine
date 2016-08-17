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
  PLL lock detector implementation.

  """

  def __init__(self, **kwargs):
    """
    Initialize the lock detector parameters

    Parameters
    ----------
    params : dictionary
        k1 - 1st order IIR I & Q filter parameter
        k2 - filtered in-phase divider
        lp - pessimistic lock threshold
        lo - optimistic lock threshold

    """

    self.lpfi = 0
    self.lpfq = 0
    self.outo = False
    self.outp = False
    self.pcount1 = 0
    self.pcount2 = 0
    self.reinit(kwargs['k1'],
                kwargs['k2'],
                kwargs['lp'],
                kwargs['lo'])

  def reinit(self, k1, k2, lp, lo):
    """
    Adjust low-pass filter (LPF) coefficients

    Parameters
    ----------
    params : dictionary
        k1 - 1st order IIR I & Q filter parameter
        k2 - filtered in-phase divider
        lp - pessimistic lock threshold
        lo - optimistic lock threshold

    """

    self.k1 = k1
    self.k2 = k2
    self.lp = lp
    self.lo = lo

  def _lpf_update(self, y, x):
    """
    Low-pass filter (LPF) state update.

    Parameters
    ----------
    y : float
      old state
    x : float
      new input
        lo - optimistic lock threshold

    Returns
    -------
    out : float
      Filtered output

    """

    y += self.k1 * (x - y)
    return y

  def update(self, I, Q, DT):
    """
    Lock detector update.

    Parameters
    ----------
    I : int
      Prompt in-phase correlator output
    Q : int
      Prompt quadrature correlator output
    DT : float
      Time difference since the last update [ms]

    Returns
    -------
    out : tuple
      outo - optimistic lock detector output
      outp - pessimistic lock detector output
      pcount1 - the counter compared against the pessimistic lock threshold
      pcount2 - the counter compared against the optimistic lock threshold
      lpfi - filtered in-phase prompt correlator output
      lpfq - filtered quadrature prompt correlator output

    """

    # Calculated low-pass filtered prompt correlations
    self.lpfi = self._lpf_update(self.lpfi, np.absolute(I) / DT)
    self.lpfq = self._lpf_update(self.lpfq, np.absolute(Q) / DT)

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

    return (self.outo, self.outp,
            self.pcount1, self.pcount2,
            self.lpfi, self.lpfq)

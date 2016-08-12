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
from peregrine import glo_constants


class AliasDetector(object):

  def __init__(self):
    """
    Initialize the parameters, which are common across different
    types of tracking channels.

    Parameters
    ----------
    None

    """
    self.reinit()

  def reinit(self):
    """
    Customize the alias detect reinitialization in a subclass.
    The method can be optionally redefined in a subclass to perform
    a subclass specific actions to happen when alias detect
    reinitialization procedure happens.

    Parameters
    ----------
    None

    """

    self.err_hz = 0.
    self.first_P = 0 + 0j
    self.acc_len = defaults.alias_detect_interval_ms / \
                   defaults.alias_detect_slice_ms
    self.dot = 0.
    self.cross = 0.
    self.fl_count = 0
    self.dt = defaults.alias_detect_slice_ms * 1e-3
    self.first_set = False

  def first(self, P):
    """
    Customize the alias detect procedure in a subclass.
    The method can be optionally redefined in a subclass to perform
    a subclass specific actions to happen before correlator runs
    next integration round.

    Parameters
    ----------
    P : prompt I/Q
      The prompt I/Q samples from correlator.

    """
    self.first_P = P
    self.first_set = True

  def second(self, P):
    """
    Customize the alias detect procedure in a subclass.
    The method can be optionally redefined in a subclass to perform
    a subclass specific actions to happen before correlator runs
    next integration round.

    Parameters
    ----------
    P : prompt I/Q
      The prompt I/Q samples from correlator.

    """
    if not self.first_set:
      return

    self.dot += (np.absolute(P.real * self.first_P.real) + \
                 np.absolute(P.imag * self.first_P.imag)) / self.acc_len
    self.cross += (self.first_P.real * P.imag - P.real * self.first_P.imag) / self.acc_len
    self.fl_count += 1
    if self.fl_count == self.acc_len:
      self.err_hz = np.arctan2(self.cross, self.dot) / (2 * np.pi * self.dt)
      self.fl_count = 0
      self.cross = 0
      self.dot = 0
    else:
      self.err_hz = 0

    abs_err_hz = abs(self.err_hz)
    err_sign = np.sign(self.err_hz)
    # The expected frequency errors are +-(25 + N * 50) Hz
    # For the reference, see:
    # https://swiftnav.hackpad.com/Alias-PLL-lock-detector-in-L2C-4fWUJWUNnOE
    if abs_err_hz > 25.:
      self.err_hz = 25
      self.err_hz += 50 * int((abs_err_hz - 25) / 50)
      abs_err_hz -= self.err_hz
      if abs_err_hz + 25. > 50.:
        self.err_hz += 50
    elif abs_err_hz > 25 / 2.:
      self.err_hz = 25
    else:
      self.err_hz = 0
    self.err_hz *= err_sign

  def get_err_hz(self):
    """
    Customize the alias detect get error procedure in a subclass.

    """
    return self.err_hz

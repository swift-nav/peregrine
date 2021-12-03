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
from swiftnav.track import AliasDetector as AD
from peregrine import defaults
from peregrine import gps_constants
from peregrine import glo_constants


class AliasDetector(object):

  def __init__(self, coherent_ms):
    """
    Initialize the parameters, which are common across different
    types of tracking channels.

    Parameters
    ----------
    coherent_ms : int
      Coherent integration time [ms].


    """
    self.first_step = True
    self.err_hz = 0.
    self.coherent_ms = coherent_ms
    self.iterations_num = coherent_ms / defaults.alias_detect_slice_ms

  def reinit(self, coherent_ms):
    """
    Customize the alias detect reinitialization in a subclass.
    The method can be optionally redefined in a subclass to perform
    a subclass specific actions to happen when alias detect
    reinitialization procedure happens.

    Parameters
    ----------
    coherent_ms : int
      Coherent integration time [ms].

    """
    self.err_hz = 0
    self.coherent_ms = coherent_ms
    self.alias_detect.reinit(self.integration_rounds, time_diff=2e-3)

  def preprocess(self):
    """
    Customize the alias detect procedure in a subclass.
    The method can be optionally redefined in a subclass to perform
    a subclass specific actions to happen before correlator runs
    next integration round.

    """
    self.first_step = True
    return self.iterations_num, self.chips_num

  def postprocess(self, P):
    """
    Customize the alias detect run procedure in a subclass.
    The method can be optionally redefined in a subclass to perform
    a subclass specific actions to happen after correlator runs
    next integration round.

    Parameters
    ----------
    P : prompt I/Q
      The prompt I/Q samples from correlator.
    code_phase : current code phase [chips]

    """

  def postprocess(self, P):
    if self.first_step:
      self.alias_detect.first(P.real, P.imag)
    else:
      self.err_hz = self.alias_detect.second(P.real, P.imag)
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

    self.first_step = not self.first_step

    return self.chips_num

  def get_err_hz(self):
    """
    Customize the alias detect get error procedure in a subclass.

    """
    return self.err_hz


class AliasDetectorL1CA(AliasDetector):

  def __init__(self, coherent_ms):

    AliasDetector.__init__(self, coherent_ms)

    self.chips_num = gps_constants.chips_per_code
    self.integration_rounds = defaults.alias_detect_interval_ms / \
        (defaults.alias_detect_slice_ms * 2)

    self.alias_detect = AD(acc_len=self.integration_rounds, time_diff=2e-3)


class AliasDetectorL2C(AliasDetector):

  def __init__(self, coherent_ms):

    AliasDetector.__init__(self, coherent_ms)

    self.chips_num = 2 * gps_constants.l2_cm_chips_per_code / coherent_ms
    self.integration_rounds = defaults.alias_detect_interval_ms / \
        (defaults.alias_detect_slice_ms * 2)

    self.alias_detect = AD(acc_len=self.integration_rounds, time_diff=2e-3)


class AliasDetectorGLO(AliasDetector):

  def __init__(self, coherent_ms):

    super(AliasDetectorGLO, self).__init__(coherent_ms)

    self.chips_num = glo_constants.glo_code_len
    self.integration_rounds = defaults.alias_detect_interval_ms / \
        (defaults.alias_detect_slice_ms * 2)

    self.alias_detect = AD(acc_len=self.integration_rounds, time_diff=2e-3)

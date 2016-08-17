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

# Multiplier for checking out-of bounds NSR
CN0_MM_NSR_MIN_MULTIPLIER = 1e-6

# Maximum supported NSR value (1/CN0_MM_NSR_MIN_MULTIPLIER)
CN0_MM_NSR_MIN = 1e6

# Moving average filter window size
CN0_MOVING_AVG_WINDOW_SIZE = 500


class CN0_Est_MM(object):

  def __init__(self, bw, cn0_0, cutoff_freq, loop_freq):
    """
    Initialize the C/N0 estimator state.

    Initializes Moment method C/N0 estimator.

    The method uses the following function for SNR computation:

    C/N0(n) = P_d / P_n,
    where P_n(n) = M2(n) - P_d(n),
    where P_d(n) = sqrt(2 * M2(n)^2 - M4(n)),
    where
    M2(n) = sum(1,N)(I(n)^2 + I(n-1)^2 + Q(n)^2 + Q(n-1)^2) / N
    M4(n) = sum(1,N)(I(n)^4 + I(n-1)^4 + Q(n)^4 + Q(n-1)^4) / N

    Parameters
    ----------
    bw : float
      Unused
    cn0_0 : float
      The initial value of C/N_0 in dB-Hz.
    cutoff_freq : float
      Unused
    loop_freq : float
      The estimator update rate [Hz].


    """
    self.cn0_db = cn0_0
    self.M2_arr = np.ndarray(CN0_MOVING_AVG_WINDOW_SIZE, dtype=np.double)
    self.M4_arr = np.ndarray(CN0_MOVING_AVG_WINDOW_SIZE, dtype=np.double)
    self.index = 0
    self.log_bw = 10 * np.log10(loop_freq)
    self.snr_db = 0
    self.snr = 0

  def _compute_cn0(self, M_2, M_4):
    """
    Compute C/N0 value

    Parameters
    ----------
    M_2 : float
      M2 value
    M_4 : float
      M4 value

    Return
    ------
      out : float
        Computed C/N0 value

    """

    tmp = 2 * M_2 * M_2 - M_4

    if tmp < 0:
      self.snr = 1 / CN0_MM_NSR_MIN
    else:
      P_d = np.sqrt(tmp)
      P_n = M_2 - P_d

      # Ensure the SNR is within the limit
      if P_d < P_n * CN0_MM_NSR_MIN_MULTIPLIER:
        return 60
      elif P_n == 0:
        return 10
      else:
        self.snr = P_d / P_n

    self.snr_db = 10 * np.log10(self.snr)

    # Compute CN0
    x = self.log_bw + self.snr_db
    if x < 10:
      return 10
    if x > 60:
      return 60

    return x

  def _moving_average(self, arr, x):
    """
    Moving average filter.

    Parameters
    ----------
    arr : list
      The list of past values
    x : float
      New value

    Return
    ------
      out : float
        Filtered value

    """
    if self.index < CN0_MOVING_AVG_WINDOW_SIZE:
      arr[self.index] = x
      return np.average(arr[:self.index + 1])
    else:
      arr[:-1] = arr[1:]
      arr[-1] = x
      return np.average(arr)

  def update(self, I, Q):
    """
    Compute C/N0 with Moment method.

    Parameters
    ----------
    I : int
      In-phase signal component.
    Q : int
      Quadrature signal component.

    Return
    ------
      out : tuple
        cn0_db - CN0 value in dB-Hz
        snr - SNR
        snr_db - SNR [dB]

    """
    m_2 = I * I + Q * Q
    m_4 = m_2 * m_2

    M_2 = self._moving_average(self.M2_arr, m_2)
    M_4 = self._moving_average(self.M4_arr, m_4)

    if self.index < CN0_MOVING_AVG_WINDOW_SIZE:
      self.index += 1

    # Compute and store updated CN0
    self.cn0_db = self._compute_cn0(M_2, M_4)

    return (self.cn0_db, self.snr, self.snr_db)


class CN0_Est_BL(object):

  def __init__(self, bw, cn0_0, cutoff_freq, loop_freq):
    """
    Initialize the C/N0 estimator state.

    Parameters
    ----------
    bw : float
      Unused
    cn0_0 : float
      The initial value of C/N_0 in dB-Hz.
    cutoff_freq : float
      Unused
    loop_freq : float
      The estimator update rate [Hz].

    """
    self.nsr_arr = np.ndarray(CN0_MOVING_AVG_WINDOW_SIZE, dtype=np.double)
    self.snr_arr = np.ndarray(CN0_MOVING_AVG_WINDOW_SIZE, dtype=np.double)
    self.index = 0
    self.log_bw = 10. * np.log10(loop_freq)
    self.I_prev_abs = -1.
    self.Q_prev_abs = -1.
    self.nsr = 10. ** (0.1 * (self.log_bw - cn0_0))
    self.snr = 0

  def _moving_average(self, arr, x):
    """
    Moving average filter.

    Parameters
    ----------
    arr : list
      The list of past values
    x : float
      New value

    Return
    ------
      out : float
        Filtered value

    """

    if self.index < CN0_MOVING_AVG_WINDOW_SIZE:
      arr[self.index] = x
      return np.average(arr[:self.index + 1])
    else:
      arr[:-1] = arr[1:]
      arr[-1] = x
      return np.average(arr)

  def update(self, I, Q):
    """
    Compute C/N0 with BL method.

    Parameters
    ----------
    I : int
      In-phase signal component.
    Q : int
      Quadrature signal component.

    Return
    ------
      out : tuple
        cn0_db - CN0 value in dB-Hz
        snr - SNR
        snr_db - SNR [dB]

    """

    if self.I_prev_abs < 0.:
      # This is the first iteration, just update the prev state.
      self.I_prev_abs = np.absolute(I)
      self.Q_prev_abs = np.absolute(Q)
    else:
      P_n = np.absolute(I) - self.I_prev_abs
      P_n = P_n * P_n

      P_s = 0.5 * (I * I + self.I_prev_abs * self.I_prev_abs)

      self.I_prev_abs = np.absolute(I)
      self.Q_prev_abs = np.absolute(Q)

      self.nsr = self._moving_average(self.nsr_arr, P_n / P_s)
      self.snr = self._moving_average(self.snr_arr, I ** 2 / (2 * Q ** 2))
      if self.index < CN0_MOVING_AVG_WINDOW_SIZE:
        self.index += 1

    cn0 = self.log_bw - 10. * np.log10(self.nsr)

    return (cn0, self.snr, 10 * np.log10(self.snr))

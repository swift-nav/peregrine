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

CN0_MOVING_AVG_WINDOW_SIZE = 200

class CN0_Est_MM(object):

  def __init__(self, bw, cn0_0, cutoff_freq, loop_freq):
    """
    Initialize the C/N0 estimator state.

    Initializes Moment method C/N0 estimator.

    The method uses the function for SNR computation:

    \frac{C}{N_0}(n) = \frac{P_d}{P_n},
    where P_n(n) = M2(n) - P_d(n),
    where P_d(n) = \sqrt{2# M2(n)^2 - M4(n)},
    where
    M2(n) = \frac{1}{2}(I(n)^2 + I(n-1)^2 + Q(n)^2 + Q(n-1)^2)
    M4(n) = \frac{1}{2}(I(n)^4 + I(n-1)^4 + Q(n)^4 + Q(n-1)^4)

    Parameters
    ----------
\param s     The estimator state struct to initialize.
\param p     Common C/N0 estimator parameters.
\param cn0_0 The initial value of \f$ C / N_0 \f$ in dBHz.

\return None

    Parameters
    ----------
    coherent_ms : int
      Coherent integration time [ms].


    """
    self.cn0_db = cn0_0
    self.M2_arr = np.ndarray(CN0_MOVING_AVG_WINDOW_SIZE, dtype=np.double)
    self.M4_arr = np.ndarray(CN0_MOVING_AVG_WINDOW_SIZE, dtype=np.double)
    self.index = 0
    self.log_bw = 10 * np.log10(loop_freq)


  def _compute_cn0(self, M_2, M_4):
    tmp = 2 * M_2 * M_2 - M_4

    if tmp < 0:
      snr = 1 / CN0_MM_NSR_MIN
    else:
      P_d = np.sqrt(tmp)
      P_n = M_2 - P_d

      # Ensure the NSR is within the limit
      if P_d < P_n * CN0_MM_NSR_MIN_MULTIPLIER:
        return 60
      elif P_n == 0:
        return 10
      else:
        snr = P_d / P_n

    snr_db = 10 * np.log10(snr)

    # Compute CN0
    x= self.log_bw + snr_db
    if x < 10:
      return 10
    if x > 60:
      return 60

    return x


  def _moving_average(self, arr, x):
    if self.index < CN0_MOVING_AVG_WINDOW_SIZE:
      arr[self.index] = x
      return np.average(arr[:self.index + 1])
    else:
      arr[:-1] = arr[1:]
      arr[-1] = x
      return np.average(arr)

  # Computes \f$ C / N_0 \f$ with Moment method.
  #
  # s Initialized estimator object.
  # I In-phase signal component
  # Q Quadrature phase signal component.
  #
  # Computed \f$ C / N_0 \f$ value
  def update(self, I, Q):
    m_2 = I * I + Q * Q
    m_4 = m_2 * m_2

    M_2 = self._moving_average(self.M2_arr, m_2)
    M_4 = self._moving_average(self.M4_arr, m_4)

    if self.index < CN0_MOVING_AVG_WINDOW_SIZE:
      self.index += 1

    # Compute and store updated CN0
    self.cn0_db = self._compute_cn0(M_2, M_4)

    return self.cn0_db

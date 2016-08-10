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
from peregrine.include.controlled_root import controlled_root

def costas_discriminator(I, Q):
  if I == 0:
    # Technically, it should be +/- 0.25, but then we'd have to keep track
    # of the previous sign do it right, so it's simple enough to just return
    # the average of 0.25 and -0.25 in the face of that ambiguity, so zero.
    return 0

  return np.arctan(Q / I)# / (2 * np.pi)

def frequency_discriminator(I, Q, prev_I, prev_Q):
  dot = np.absolute(I * prev_I) + np.absolute(Q * prev_Q)
  cross = prev_I * Q - I * prev_Q
  return np.arctan2(cross, dot)# / (2 * np.pi)

def dll_discriminator(E, P, L):
  E_mag = np.absolute(E)
  L_mag = np.absolute(L)
  if E_mag + L_mag == 0:
    return 0

  return 0.5 * (E_mag - L_mag) / (E_mag + L_mag)

class TrackingLoop3:
  """
  Third order tracking loop initialization.

  For a full description of the loop filter parameters, see
  :libswiftnav:`calc_loop_gains`.

  """

  def __init__(self, **kwargs):
    # Initial state
    self.carr_freq = kwargs['carr_freq']
    self.code_freq = kwargs['code_freq']

    self.code_vel = kwargs['code_freq']
    self.phase_acc = 0
    self.phase_vel = kwargs['carr_freq']
    self.phase_err = 0
    self.code_err = 0
    self.fll_bw = kwargs['carr_freq_b1']
    self.pll_bw = kwargs['carr_bw']
    self.dll_bw = kwargs['code_bw']

    self.P_prev = 1+0j

    self.retune( (kwargs['code_bw'], kwargs['code_zeta'], kwargs['code_k']),
                 (kwargs['carr_bw'], kwargs['carr_zeta'], kwargs['carr_k']),
                 kwargs['loop_freq'],
                 kwargs['carr_freq_b1'],
                 kwargs['carr_to_code'] )

  def retune(self, code_params, carr_params, loop_freq, carr_freq_b1, carr_to_code):
    """
    Retune the tracking loop.

    Parameters
    ----------
    code_params : (float, float, float)
      Code tracking loop parameter tuple, `(bw, zeta, k)`.
    carr_params : (float, float, float)
      Carrier tracking loop parameter tuple, `(bw, zeta, k)`.
    loop_freq : float
      The frequency with which loop updates are performed.
    carr_freq_b1 : float
      FLL aiding gain
    carr_to_code : float
      PLL to DLL aiding gain

    """
    code_bw, code_zeta, code_k = code_params
    carr_bw, carr_zeta, carr_k = carr_params

    # Common parameters
    self.T = 1. / loop_freq

    self.fll_bw = carr_freq_b1
    self.pll_bw = carr_bw
    self.dll_bw = code_bw

    # FLL constants
    freq_omega_0 = carr_freq_b1 / 0.53
    freq_a2 = 1.414

    # a_2 * omega_0f
    self.freq_c1 = freq_a2 * freq_omega_0
    self.freq_c2 = freq_omega_0 * freq_omega_0

    # PLL constants
    phase_omega_0 = carr_bw / 0.7845
    phase_a3 = 1.1
    phase_b3 = 2.4

    self.phase_c1 = phase_b3 * phase_omega_0
    self.phase_c2 = phase_a3 * phase_omega_0 * phase_omega_0
    self.phase_c3 = phase_omega_0 * phase_omega_0 * phase_omega_0

    # DLL constants
    code_omega_0 = code_bw / 0.53
    code_a2 = 1.414

    self.code_c1 = code_a2 * code_omega_0
    self.code_c2 = code_omega_0 * code_omega_0

    self.carr_to_code = carr_to_code

  def update(self, E, P, L):
    """
    Tracking loop update

    Parameters
    ----------
    E : [complex], :math:`I_E + Q_E j`
      Complex Early Correlation
    P : [complex], :math:`I_P + Q_P j`
      Complex Prompt Correlation
    L : [complex], :math:`I_L + Q_L j`
      Complex Late Correlation

    Returns
    -------
    out : (float, float)
      The tuple (code_freq, carrier_freq).

    """

    # Carrier loop
    self.phase_err = costas_discriminator(P.real, P.imag)
    freq_error = 0
    if self.freq_c1 != 0 and self.T != 0:
      freq_error = frequency_discriminator(P.real, P.imag, self.P_prev.real, self.P_prev.imag) / self.T
      self.P_prev = P

    prev = self.phase_acc
    self.phase_acc += freq_error * self.freq_c2 * self.T + self.phase_err * self.phase_c3 * self.T

    sum = (self.phase_acc + prev) * 0.5
    sum += freq_error * self.freq_c1 + self.phase_err * self.phase_c2
    prev = self.phase_vel
    self.phase_vel += sum * self.T
    sum = (self.phase_vel + prev) * 0.5 + self.phase_err * self.phase_c1
    self.carr_freq = sum

    # Code loop
    self.code_err = -dll_discriminator(E, P, L)

    prev = self.code_vel
    self.code_vel += self.code_c2 * self.code_err * self.T
    sum = (prev + self.code_vel) * 0.5 + self.code_c1 * self.code_err

    self.code_freq = sum
    if self.carr_to_code > 0:
      self.code_freq += self.carr_freq / self.carr_to_code

    return (self.code_freq, self.carr_freq)

  def adjust_freq(self, corr):
    self.carr_freq += corr

  def to_dict(self):
    return { k:v for k, v in self.__dict__.items() \
             if not (k.startswith('__') and k.endswith('__')) }


class TrackingLoop3b:
  """
  Third order tracking loop initialization.

  For a full description of the loop filter parameters, see
  :libswiftnav:`calc_loop_gains`.

  """

  def __init__(self, **kwargs):
    # Initial state
    self.carr_freq = kwargs['carr_freq']
    self.code_freq = kwargs['code_freq']

    self.code_vel = kwargs['code_freq']
    self.phase_acc = 0
    self.phase_vel = kwargs['carr_freq']
    self.phase_err = 0
    self.code_err = 0
    self.fll_bw = kwargs['carr_freq_b1']
    self.pll_bw = kwargs['carr_bw']
    self.dll_bw = kwargs['code_bw']

    self.P_prev = 1+0j

    self.retune( (kwargs['code_bw'], kwargs['code_zeta'], kwargs['code_k']),
                 (kwargs['carr_bw'], kwargs['carr_zeta'], kwargs['carr_k']),
                 kwargs['loop_freq'],
                 kwargs['carr_freq_b1'],
                 kwargs['carr_to_code'] )


  def retune(self, code_params, carr_params, loop_freq, carr_freq_b1, carr_to_code):
    """
    Retune the tracking loop.

    Parameters
    ----------
    code_params : (float, float, float)
      Code tracking loop parameter tuple, `(bw, zeta, k)`.
    carr_params : (float, float, float)
      Carrier tracking loop parameter tuple, `(bw, zeta, k)`.
    loop_freq : float
      The frequency with which loop updates are performed.
    carr_freq_b1 : float
      FLL aiding gain
    carr_to_code : float
      PLL to DLL aiding gain

    """
    code_bw, code_zeta, code_k = code_params
    carr_bw, carr_zeta, carr_k = carr_params

    # Common parameters
    self.T = 1. / loop_freq

    self.fll_bw = carr_freq_b1
    self.pll_bw = carr_bw
    self.dll_bw = code_bw

    # FLL constants
    freq_omega_0 = carr_freq_b1 / 0.53
    freq_a2 = 1.414

    # a_2 * omega_0f
    self.freq_c1 = freq_a2 * freq_omega_0
    self.freq_c2 = freq_omega_0 * freq_omega_0

    # PLL constants
    self.phase_c1, self.phase_c2, self.phase_c3 = controlled_root(3, 1 / loop_freq, carr_bw)

    # DLL constants
    code_omega_0 = code_bw / 0.53
    code_a2 = 1.414

    self.code_c1 = code_a2 * code_omega_0
    self.code_c2 = code_omega_0 * code_omega_0

    self.carr_to_code = carr_to_code

  def update(self, E, P, L):
    """
    Tracking loop update

    Parameters
    ----------
    E : [complex], :math:`I_E + Q_E j`
      Complex Early Correlation
    P : [complex], :math:`I_P + Q_P j`
      Complex Prompt Correlation
    L : [complex], :math:`I_L + Q_L j`
      Complex Late Correlation

    Returns
    -------
    out : (float, float)
      The tuple (code_freq, carrier_freq).

    """

    # Carrier loop
    self.phase_err = costas_discriminator(P.real, P.imag)
    freq_error = 0
    if self.freq_c1 != 0 and self.T != 0:
      freq_error = frequency_discriminator(P.real, P.imag, self.P_prev.real, self.P_prev.imag) / self.T
      self.P_prev = P

    self.phase_acc += self.phase_err * self.phase_c3 / self.T

    sum = self.phase_acc + self.phase_err * self.phase_c2 / self.T
    self.phase_vel += sum
    sum = self.phase_vel + self.phase_err * self.phase_c1 / self.T
    self.carr_freq = sum

    # Code loop
    self.code_err = -dll_discriminator(E, P, L)

    prev = self.code_vel
    self.code_vel += self.code_c2 * self.code_err * self.T
    sum = (prev + self.code_vel) * 0.5 + self.code_c1 * self.code_err

    self.code_freq = sum
    if self.carr_to_code > 0:
      self.code_freq += self.carr_freq / self.carr_to_code

    return (self.code_freq, self.carr_freq)

  def adjust_freq(self, corr):
    self.carr_freq += corr

  def to_dict(self):
    return { k:v for k, v in self.__dict__.items() \
             if not (k.startswith('__') and k.endswith('__')) }


class TrackingLoop2b:
  """
  Second order tracking loop initialization.

  For a full description of the loop filter parameters, see
  :libswiftnav:`calc_loop_gains`.

  """

  def __init__(self, **kwargs):
    # Initial state
    self.carr_freq = kwargs['carr_freq']
    self.code_freq = kwargs['code_freq']

    self.code_vel = kwargs['code_freq']
    self.phase_vel = kwargs['carr_freq']

    self.P_prev = 1+0j

    self.retune( (kwargs['code_bw'], kwargs['code_zeta'], kwargs['code_k']),
                 (kwargs['carr_bw'], kwargs['carr_zeta'], kwargs['carr_k']),
                 kwargs['loop_freq'],
                 kwargs['carr_freq_b1'],
                 kwargs['carr_to_code'] )

  def retune(self, code_params, carr_params, loop_freq, carr_freq_b1, carr_to_code):
    """
    Retune the tracking loop.

    Parameters
    ----------
    code_params : (float, float, float)
      Code tracking loop parameter tuple, `(bw, zeta, k)`.
    carr_params : (float, float, float)
      Carrier tracking loop parameter tuple, `(bw, zeta, k)`.
    loop_freq : float
      The frequency with which loop updates are performed.
    carr_freq_b1 : float
      FLL aiding gain
    carr_to_code : float
      PLL to DLL aiding gain

    """
    code_bw, code_zeta, code_k = code_params
    carr_bw, carr_zeta, carr_k = carr_params

    # Common parameters
    self.T = 1 / loop_freq

    # FLL constants
    freq_omega_0 = carr_freq_b1 / 0.53
    freq_a2 = 1.414

    # a_2 * omega_0f
    self.freq_c1 = freq_a2 * freq_omega_0
    self.freq_c2 = freq_omega_0 * freq_omega_0

    # PLL constants
    phase_omega_0 = carr_bw / 0.53
    phase_a2 = 1.414

    self.phase_c1 = phase_a2 * phase_omega_0
    self.phase_c2 = phase_omega_0 * phase_omega_0
    # self.phase_c1, self.phase_c2 = controlled_root(2, 1 / loop_freq, carr_bw)
    # print "T = ", 1 / loop_freq, " BW = ", carr_bw

    # DLL constants
    code_omega_0 = code_bw / 0.53
    code_a2 = 1.414

    self.code_c1 = code_a2 * code_omega_0
    self.code_c2 = code_omega_0 * code_omega_0

    self.carr_to_code = carr_to_code

    # self.code_vel = 0
    # self.phase_vel = 0

  def update(self, E, P, L):
    """
    Tracking loop update

    Parameters
    ----------
    E : [complex], :math:`I_E + Q_E j`
      Complex Early Correlation
    P : [complex], :math:`I_P + Q_P j`
      Complex Prompt Correlation
    L : [complex], :math:`I_L + Q_L j`
      Complex Late Correlation

    Returns
    -------
    out : (float, float)
      The tuple (code_freq, carrier_freq).

    """

    # Carrier loop
    self.phase_err = costas_discriminator(P.real, P.imag)
    freq_error = 0
    if self.freq_c1 != 0:
      freq_error = frequency_discriminator(P.real, P.imag, self.P_prev.real, self.P_prev.imag) / self.T

    self.P_prev = P

    self.phase_vel += freq_error * self.freq_c2 * self.T + self.phase_err * self.phase_c2 * self.T

    self.carr_freq = self.phase_vel + freq_error * self.freq_c1 + self.phase_err * self.phase_c1

    # Code loop
    code_error = -dll_discriminator(E, P, L)

    prev = self.code_vel
    self.code_vel += self.code_c2 * code_error * self.T
    sum = (prev + self.code_vel) * 0.5 + self.code_c1 * code_error

    self.code_freq = sum
    if self.carr_to_code > 0:
      self.code_freq += self.carr_freq / self.carr_to_code

    return (self.code_freq, self.carr_freq)

  def adjust_freq(self, corr):
    self.carr_freq += corr

  def to_dict(self):
    return { k:v for k, v in self.__dict__.items() \
             if not (k.startswith('__') and k.endswith('__')) }


class TrackingLoop3Optimal:
  """
  Third order optimal tracking loop initialization.

  For a full description of the loop filter parameters, see
  :libswiftnav:`calc_loop_gains`.

  """

  def __init__(self, **kwargs):
    # Initial state
    self.carr_freq = kwargs['carr_freq']
    self.code_freq = kwargs['code_freq']

    self.code_vel = kwargs['code_freq']
    self.phase_vel = kwargs['carr_freq']

    self.P_prev = 1+0j

    self.retune( (kwargs['code_bw'], kwargs['code_zeta'], kwargs['code_k']),
                 (kwargs['carr_bw'], kwargs['carr_zeta'], kwargs['carr_k']),
                 kwargs['loop_freq'],
                 kwargs['carr_freq_b1'],
                 kwargs['carr_to_code'] )

  def retune(self, code_params, carr_params, loop_freq, carr_freq_b1, carr_to_code):
    """
    Retune the tracking loop.

    Parameters
    ----------
    code_params : (float, float, float)
      Code tracking loop parameter tuple, `(bw, zeta, k)`.
    carr_params : (float, float, float)
      Carrier tracking loop parameter tuple, `(bw, zeta, k)`.
    loop_freq : float
      The frequency with which loop updates are performed.
    carr_freq_b1 : float
      FLL aiding gain
    carr_to_code : float
      PLL to DLL aiding gain

    """
    code_bw, code_zeta, code_k = code_params
    carr_bw, carr_zeta, carr_k = carr_params

    # Common parameters
    self.T = 1 / loop_freq

    # FLL constants
    freq_omega_0 = carr_freq_b1 / 0.53
    freq_a2 = 1.414

    # a_2 * omega_0f
    self.freq_c1 = freq_a2 * freq_omega_0
    self.freq_c2 = freq_omega_0 * freq_omega_0

    # PLL constants
    phase_omega_0 = carr_bw / 0.53
    phase_a2 = 1.414

    self.phase_c1 = phase_a2 * phase_omega_0
    self.phase_c2 = phase_omega_0 * phase_omega_0
    # self.phase_c1, self.phase_c2 = controlled_root(2, 1 / loop_freq, carr_bw)
    # print "T = ", 1 / loop_freq, " BW = ", carr_bw

    # DLL constants
    code_omega_0 = code_bw / 0.53
    code_a2 = 1.414

    self.code_c1 = code_a2 * code_omega_0
    self.code_c2 = code_omega_0 * code_omega_0

    self.carr_to_code = carr_to_code

    # self.code_vel = 0
    # self.phase_vel = 0

  def update(self, E, P, L):
    """
    Tracking loop update

    Parameters
    ----------
    E : [complex], :math:`I_E + Q_E j`
      Complex Early Correlation
    P : [complex], :math:`I_P + Q_P j`
      Complex Prompt Correlation
    L : [complex], :math:`I_L + Q_L j`
      Complex Late Correlation

    Returns
    -------
    out : (float, float)
      The tuple (code_freq, carrier_freq).

    """

    # Carrier loop
    self.phase_err = costas_discriminator(P.real, P.imag)
    freq_error = 0
    if self.freq_c1 != 0:
      freq_error = frequency_discriminator(P.real, P.imag, self.P_prev.real, self.P_prev.imag) / self.T

    self.P_prev = P

    self.phase_vel += freq_error * self.freq_c2 * self.T + self.phase_err * self.phase_c2 * self.T

    self.carr_freq = self.phase_vel + freq_error * self.freq_c1 + self.phase_err * self.phase_c1

    # Code loop
    code_error = -dll_discriminator(E, P, L)

    prev = self.code_vel
    self.code_vel += self.code_c2 * code_error * self.T
    sum = (prev + self.code_vel) * 0.5 + self.code_c1 * code_error

    self.code_freq = sum
    if self.carr_to_code > 0:
      self.code_freq += self.carr_freq / self.carr_to_code

    return (self.code_freq, self.carr_freq)

  def adjust_freq(self, corr):
    self.carr_freq += corr

  def to_dict(self):
    return { k:v for k, v in self.__dict__.items() \
             if not (k.startswith('__') and k.endswith('__')) }

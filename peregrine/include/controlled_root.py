# -*- coding: utf-8 -*-
"""
Created on Thu Jul 14 14:29:34 2016

@author: tpaakki

This script generates controlled-root loop parameters, based on 
"Stephens, S. A., and J. C. Thomas, "Controlled-Root Formulation for 
Digital Phase-Locked Loops," IEEE Trans. on Aerospace and Electronics
 Systems, January 1995"

"""
from math import factorial, exp
import cmath

def controlled_root(N, T, BW):
  # Input Parameters
  # N [-]  Loop Order
  # T [s]  Integration Time
  # BW [Hz] Loop Bandwidth
  # Output Parameters
  # K [-] Loop constants

  K = []
  tol = 1.e-6     # Error tolerance
  goal = BW*T     # This is the BLT we want to solve

  # Few precomputed factorial parameters
  if N > 1:
    fac1 = factorial(N)/(factorial(1)*factorial(N-1))     # eq.(45)
  if N > 2:
    fac2 = factorial(N)/(factorial(2)*factorial(N-2))     # eq.(46)
    fac3 = factorial(N-1)/(factorial(1)*factorial(N-1-1)) # eq.(46)
    fac4 = factorial(N-2)/(factorial(1)*factorial(N-2-1)) # eq.(46)

  beta = 0.5
  step = 0.25
  done = True
  ii = 1
  if N == 1:
    while done:
      z1 = exp(-beta)        # eq.(50)
      K1 = 1.-z1             # eq.(49)
      blt = K1/(2.*(2.-K1))  # Table IV
      err = goal-blt
      if abs(err) <= tol:
        K = [K1]
        done = False
      if err > 0.:
        beta = beta + step
        step = step / 2.
      if err < 0.:
        beta = beta - step
        step = step / 2.
      if ii > 30:
        'Error - did not converge'
        done = False
      ii = ii + 1;
  if N == 2:
    while done:
      z1 = cmath.exp(-beta*(1.+1.j)) # eq.(50)
      z2 = cmath.exp(-beta*(1.-1.j)) # eq.(50)
      K1 = 1.-z1*z2                  # eq.(49)
      K1 = K1.real
      K2 = fac1-K1-z1-z2             # eq.(45)
      K2 = K2.real
      blt = (2.*K1*K1+2.*K2+K1*K2)/(2.*K1*(4.-2*K1-K2)) # Table IV
      err = goal-blt
      if abs(err) <= tol:
        K = K1, K2
        done = False
      if err > 0.:
        beta = beta + step
        step = step / 2.
      if err < 0.:
        beta = beta - step
        step = step / 2.
      if ii > 30:
        'Error - did not converge'
        done = False
        ii = ii + 1;
  if N == 3:
    while done:
      z1 = exp(-beta)                # eq.(50)
      z2 = cmath.exp(-beta*(1.+1.j)) # eq.(50)
      z3 = cmath.exp(-beta*(1.-1.j)) # eq.(50)
      K1 = 1-z1*z2*z3                # eq.(49)
      K1 = K1.real
      summ = z1*z2+z1*z3+z2*z3;
      K2 = (fac2-fac3*K1-summ)/fac4  # eq.(46)
      K2 = K2.real
      K3 = fac1-K1-K2-z1-z2-z3       # eq.(45)
      K3 = K3.real
      blt = (4.*K1*K1*K2-4.*K1*K3+4.*K2*K2+2.*K1*K2*K2+4.*K1*K1*K3+4.*K2*K3
           +3*K1*K2*K3+K3*K3+K1*K3*K3)/(2.*(K1*K2-K3+K1*K3)*(8.
           -4.*K1-2.*K2-K3))         # Table IV
      err = goal-blt
      if abs(err) <= tol:
        K = K1, K2, K3
        done = False
      if err > 0.:
        beta = beta + step
        step = step / 2.
      if err < 0.:
        beta = beta - step
        step = step / 2.
      if ii > 30:
        'Error - did not converge'
        done = False
      ii = ii + 1;

  return K

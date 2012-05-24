#!/usr/bin/python
#
# Copyright (C) 2012 Colin Beighley <colinbeighley@gmail.com>
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.
#

import numpy as np

def unsigned(inbin):
  #Check that inbin is a numpy.ndarray
  if not(type(inbin)==np.ndarray):
    raise Exception('input must be a numpy.ndarray')
  #Check that inbin is a list of 0's and 1's
  if not((np.unique(inbin) == np.array([0])).all() or \
           (np.unique(inbin) == np.array([0,1])).all() or \
             (np.unique(inbin) == np.array([1])).all()):
    raise Exception('input must be a list of 0s and 1s')
  #Convert list of 1's and 0's to string of 1's and 0's
  tmp = ''
  for i in inbin:
    tmp += str(i)
  #Convert string of 1's and 0's to decimal
  tmp = int(tmp,2)
  return tmp 

def twoscomp(inbin):
  #Check that inbin is a numpy.ndarray
  if not(type(inbin)==np.ndarray):
    raise Exception('input must be a numpy.ndarray')
  #Check that inbin is a list of 0's and 1's
  if not((np.unique(inbin) == np.array([0])).all() or \
           (np.unique(inbin) == np.array([0,1])).all() or \
             (np.unique(inbin) == np.array([1])).all()):
    raise Exception('input must be a list of 0s and 1s')
  #Compute magnitude of unsigned portion
  tmp = unsigned(inbin[1::])
  #Convert to negative if signed
  if inbin[0] == 1:
    tmp = tmp - 2**(len(inbin)-1)
  return tmp

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
#Takes tracking loop correlations of length a and returns 
#bits (sign of average of 20 correltions) of length a/20
def signed(incorrs):
  #Check that input is a numpy.ndarray
  if not(type(incorrs)==np.ndarray):
    raise Exception('input must be a numpy.ndarray')
  #Check that length of input is a multiple of 20
  if not((len(incorrs) % 20) == 0):
    raise Exception('length of input must be a multiple of 20')
  tmp = np.reshape(incorrs,(len(incorrs)/20,20))
  tmp = np.sum(tmp,1)
  tmp = np.sign(tmp)
  return tmp

#Same as signed, except instead of (-1,1), bits are (0,1)
def unsigned(incorrs):
  #Check that input is a numpy.ndarray
  if not(type(incorrs)==np.ndarray):
    raise Exception('input must be a numpy.ndarray')
  #Check that length of input is a multiple of 20
  if not((len(incorrs) % 20) == 0):
    raise Exception('length of input must be a multiple of 20')
  tmp = np.reshape(incorrs,(len(incorrs)/20,20))
  tmp = np.sum(tmp,1)
  tmp = np.sign(tmp)
  tmp = (tmp+1)/2
  tmp = np.array(map(int,tmp))
  return tmp

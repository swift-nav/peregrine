# Copyright (C) 2012 Swift Navigation Inc.
#
# This source is subject to the license found in the file 'LICENSE' which must
# be be distributed together with this source. All other rights reserved.
#
# THIS CODE AND INFORMATION IS PROVIDED "AS IS" WITHOUT WARRANTY OF ANY KIND,
# EITHER EXPRESSED OR IMPLIED, INCLUDING BUT NOT LIMITED TO THE IMPLIED
# WARRANTIES OF MERCHANTABILITY AND/OR FITNESS FOR A PARTICULAR PURPOSE.

import numpy

signmag_dict = {0:  1, 1:  3, 2:  5, 3:  7,
                4: -1, 5: -3, 6: -5, 7: -7}

def ascii_int8(filename, num_samples, num_skip=0):
  with open(filename, 'r') as f:
    try:
      samples = map(int, f.readlines())
    except ValueError:
      raise Exception("Reading sample file failed")

  return samples[num_skip:num_skip+num_samples]

def uint8(filename, num_samples, num_skip=0):
  with open(filename, 'r') as f:
    f.seek(num_skip)
    samples_u8 = f.read(num_samples)

  try:
    samples = [signmag_dict[ord(i)] for i in samples_u8]
  except KeyError:
    raise Exception("Sign-magnitude to integer conversion failed")

  return samples

def int8(filename, num_samples, num_skip=0):
  with open(filename, 'r') as f:
    f.seek(num_skip)
    samples = numpy.fromfile(f, dtype=numpy.int8, count=num_samples)

  if (len(samples) < num_samples):
    raise Exception("Failed to read %d samples from file '%s'" %
                    (num_samples, filename))

  return samples

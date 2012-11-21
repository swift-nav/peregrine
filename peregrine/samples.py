# Copyright (C) 2012 Swift Navigation Inc.
#
# This source is subject to the license found in the file 'LICENSE' which must
# be be distributed together with this source. All other rights reserved.
#
# THIS CODE AND INFORMATION IS PROVIDED "AS IS" WITHOUT WARRANTY OF ANY KIND,
# EITHER EXPRESSED OR IMPLIED, INCLUDING BUT NOT LIMITED TO THE IMPLIED
# WARRANTIES OF MERCHANTABILITY AND/OR FITNESS FOR A PARTICULAR PURPOSE.

"""Functions for handling sample data and sample data files."""

import numpy as np

__all__ = ['load_samples', 'save_samples']

def load_samples(filename, num_samples=-1, num_skip=0, file_format='int8'):
  """
  Load sample data from a file.

  Parameters
  ----------
  filename : string
    Filename of sample data file.
  num_samples : int, optional
    Number of samples to read, ``-1`` means the whole file.
  num_skip : int, optional
    Number of samples to discard from the beginning of the file.
  file_format : {'int8'}, optional
    Format of the sample data file. Takes one of the following values:
      * `'int8'` : Binary file consisting of a packed array of 8-bit signed
        integers.

  Returns
  -------
  out : :class:`numpy.ndarray`, shape(`num_samples`,)
    The sample data as a numpy array.

  Raises
  ------
  EOFError
    Unless `num_samples` is ``-1``, `load_samples` will always return exactly
    `num_samples` samples. If the end of the file is encountered before
    `num_samples` samples have been read, an `EOFError` will be raised.
  ValueError
    If `file_format` is unrecognised.

  """
  if file_format != 'int8':
    raise ValueError("Unknown file type '%s'" % file_format)

  with open(filename, 'rb') as f:
    f.seek(num_skip)
    samples = np.fromfile(f, dtype=np.int8, count=num_samples)

  if len(samples) < num_samples:
    raise EOFError("Failed to read %d samples from file '%s'" %
                   (num_samples, filename))

  return samples

def save_samples(filename, samples, file_format='int8'):
  """
  Save sample data to a file.

  Parameters
  ----------
  filename : string
    Filename of sample data file.
  samples : :class:`numpy.ndarray`, shape(`num_samples`,)
    Array containing the samples to save.
  file_format : {'int8'}, optional
    Format of the sample data file. Takes one of the following values:
      * `'int8'` : Binary file consisting of a packed array of 8-bit signed
        integers.

  Raises
  ------
  ValueError
    If `file_format` is unrecognised.

  """
  if file_format != 'int8':
    raise ValueError("Unknown file type '%s'" % file_format)

  with open(filename, 'wb') as f:
    samples.astype(np.int8).tofile(f)


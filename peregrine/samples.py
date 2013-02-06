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
      * `'1bit'` : Binary file consisting of a packed array of 1-bit samples,
        8 samples per byte. A high bit is considered positive.
      * `'piksi'` : Binary file consisting of 3-bit sign-magnitude samples, 2
        samples per byte. First samples is in bits [7..5], second sample is in
        bits [4..2].

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
  if file_format == 'int8':
    with open(filename, 'rb') as f:
      f.seek(num_skip)
      samples = np.fromfile(f, dtype=np.int8, count=num_samples)

  elif file_format == 'piksi':
    """
    Piksi format is packed 3-bit sign-magnitude samples, 2 samples per byte.

    Bits:
    [1..0] Flags (reserved for future use)
    [3..2] Sample 2 magnitude
    [4]    Sample 2 sign (1 is -ve)
    [6..5] Sample 1 magnitude
    [7]    Sample 1 sign (1 is -ve)

    """
    if num_samples > 0:
      num_skip_bytes = num_skip / 2
      num_skip_samples = num_skip % 2
      num_bytes = num_samples/2 + 1
    else:
      # Read whole file
      num_skip_bytes = 0
      num_skip_samples = 0
      num_bytes = -1
    with open(filename, 'rb') as f:
      f.seek(num_skip_bytes)
      packed = np.fromfile(f, dtype=np.uint8, count=num_bytes)
    sign_mag_mapping = np.array([1, 3, 5, 7, -1, -3, -5, -7], dtype=np.int8)
    samples = np.empty(len(packed) * 2, dtype=np.int8)
    samples[::2] = (packed >> 5) & 7
    samples[1::2] = (packed >> 2) & 7
    samples = sign_mag_mapping[samples]
    samples = samples[num_skip_samples:]
    if num_samples > 0:
      samples = samples[:num_samples]

  elif file_format == '1bit':
    if num_samples > 0:
      num_skip_bytes = num_skip / 8
      num_skip_samples = num_skip % 8
      num_bytes = num_samples/8 + 1
    else:
      # Read whole file
      num_skip_bytes = 0
      num_skip_samples = 0
      num_bytes = -1
    with open(filename, 'rb') as f:
      f.seek(num_skip_bytes)
      sample_bytes = np.fromfile(f, dtype=np.uint8, count=num_bytes)
    samples = 2*np.unpackbits(sample_bytes).astype(np.int8) - 1
    samples = samples[num_skip_samples:]
    if num_samples > 0:
      samples = samples[:num_samples]

  else:
    raise ValueError("Unknown file type '%s'" % file_format)

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
      * `'1bit'` : Binary file consisting of a packed array of 1-bit samples,
        8 samples per byte. A high bit is considered positive.
      * `'piksi'` : Binary file consisting of 3-bit sign-magnitude samples, 2
        samples per byte. First samples is in bits [7..5], second sample is in
        bits [4..2].

  Raises
  ------
  ValueError
    If `file_format` is unrecognised.

  """
  if file_format == 'int8':
    with open(filename, 'wb') as f:
      samples.astype(np.int8).tofile(f)

  elif file_format == 'piksi':
    signs = (samples < 0).astype(np.uint8)
    mags = ((np.abs(samples) / 2) & 3).astype(np.uint8)
    sign_mag_samples = mags | (signs << 2)
    packed = np.zeros((len(samples) + 1) / 2, dtype=np.uint8)
    packed = (sign_mag_samples[::2] & 7) << 5
    packed |= (sign_mag_samples[1::2] & 7) << 2
    with open(filename, 'wb') as f:
      packed.tofile(f)

  elif file_format == '1bit':
    sample_bytes = np.packbits((samples > 0).astype(np.uint8))
    with open(filename, 'wb') as f:
      sample_bytes.tofile(f)

  else:
    raise ValueError("Unknown file type '%s'" % file_format)


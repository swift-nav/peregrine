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

def load_samples(filename, num_samples=-1, num_skip=0, file_format='piksi'):
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
  file_format : string, optional
    Format of the sample data file. Takes one of the following values:
      * `'int8'` : Binary file consisting of a packed array of 8-bit signed
        integers.
      * `'1bit'` : Binary file consisting of a packed array of 1-bit samples,
        8 samples per byte. A high bit is considered positive.  The most
        significant bit of each byte is considered to be the first sample;
        thus [0x80, 0x55] decodes to [1, -1, -1, -1, -1, -1, -1, -1,
          -1, 1, -1, 1, -1, 1, -1, 1]
      * `'1bitrev'`: As '1bit' but with the opposite bit order, that is
        least significant bit first.
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
  elif file_format == 'c8c8':
    # Interleaved complex samples from two receivers, i.e. first four bytes are
    # I0 Q0 I1 Q1
    s_file = np.memmap(filename, offset=num_skip, dtype=np.int8, mode='r')
    n_rx = 2
    if num_samples > 0:
      s_file = s_file[:num_samples*2*n_rx]
    samples = np.empty([n_rx, len(s_file)/(2 * n_rx)], dtype=np.complex64)
    for rx in range(n_rx):
      samples[rx] = s_file[2 * rx : : 2 * n_rx] + s_file[2*rx + 1 :: 2 * n_rx]*1j
  elif file_format == 'c8c8_tayloe':
    # Interleaved complex samples from two receivers, i.e. first four bytes are
    # I0 Q0 I1 Q1.  Tayloe-upconverted to become purely real with fs=4fs0, fi=fs0
    s_file = np.memmap(filename, offset=num_skip, dtype=np.int8, mode='r')
    n_rx = 2
    if num_samples > 0:
      s_file = s_file[:num_samples*2*n_rx]
    samples = np.empty([n_rx, 4*len(s_file)/(2 * n_rx)], dtype=np.int8)
    for rx in range(n_rx):
      samples[rx][0::4] =  s_file[2 * rx     : : 2 * n_rx]
      samples[rx][1::4] = -s_file[2 * rx + 1 : : 2 * n_rx]
      samples[rx][2::4] = -s_file[2 * rx     : : 2 * n_rx]
      samples[rx][3::4] =  s_file[2 * rx + 1 : : 2 * n_rx]

  elif file_format == 'piksinew':
    packed = np.memmap(filename, offset=num_skip, dtype=np.uint8, mode='r')
    if num_samples > 0:
      packed = packed[:num_samples]
    samples = np.empty(len(packed), dtype=np.int8)
    samples[:] = (packed >> 6) - 1

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

    packed = np.memmap(filename, offset=num_skip_bytes, dtype=np.uint8, mode='r')
    if num_bytes > 0:
      packed = packed[:num_bytes]

    samples = np.empty(len(packed) * 2, dtype=np.int8)

    # Unpack 2 samples from each byte
    samples[::2] = (packed >> 5)
    samples[1::2] = (packed >> 2) & 7
    # Sign-magnitude to two's complement mapping
    samples = (1-2*(samples>>2)) * (2*(samples&3)+1)

    samples = samples[num_skip_samples:]
    if num_samples > 0:
      samples = samples[:num_samples]

  elif file_format == '1bit' or file_format == '1bitrev':
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
#    samples = 2*np.unpackbits(sample_bytes).astype(np.int8) - 1
    samples = np.unpackbits(sample_bytes).view('int8')
    samples *= 2
    samples -= 1
    if file_format == '1bitrev':
        samples = np.reshape(samples,(-1,8))[:,::-1].flatten();
    samples = samples[num_skip_samples:]
    if num_samples > 0:
      samples = samples[:num_samples]

  else:
    raise ValueError("Unknown file type '%s'" % file_format)

  if len(samples.T) < num_samples:
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

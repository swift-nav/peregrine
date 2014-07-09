# Copyright (C) 2012 Swift Navigation Inc.
#
# This source is subject to the license found in the file 'LICENSE' which must
# be be distributed together with this source. All other rights reserved.
#
# THIS CODE AND INFORMATION IS PROVIDED "AS IS" WITHOUT WARRANTY OF ANY KIND,
# EITHER EXPRESSED OR IMPLIED, INCLUDING BUT NOT LIMITED TO THE IMPLIED
# WARRANTIES OF MERCHANTABILITY AND/OR FITNESS FOR A PARTICULAR PURPOSE.

import numpy as np
from include.generateCAcode import caCodes
import gps_constants
import progressbar
import math
import parallel_processing as pp

import swiftnav.track
import swiftnav.correlate
import defaults

import logging
logger = logging.getLogger(__name__)

# Import progressbar if it is available.
_progressbar_available = True
try:
  import progressbar
except ImportError:
  _progressbar_available = False


class TrackingLoop(object):
  """
  Abstract base class for a tracking loop.

  Sub-classes should implement :meth:`update` and :meth:`start` and provide
  access to `code_freq` and `carr_freq` attributes or properties.

  The tracking loop should initialise its constant parameters in its `__init__`
  method. :meth:`start` will be called to (re)initialise the tracking loop,
  passing in the initial carrier and code frequencies.

  """
  __slots__ = ('code_freq', 'carr_freq')

  def start(self, code_freq, carr_freq):
    """
    (Re-)initialise the tracking loop.

    Parameters
    ----------
    code_freq : float
      The code phase rate (i.e. frequency).
    carr_freq : float
      The carrier frequency.

    """
    raise NotImplementedError()

  def update(self, e, p, l):
    """
    Tracking loop update step.

    Parameters
    ----------
    e : complex, :math:`I_E + Q_E j`
      The early correlation. The real component contains the in-phase
      correlation and the imaginary component contains the quadrature
      correlation.
    p : complex, :math:`I_P + Q_P j`
      The prompt correlation.
    l : complex, :math:`I_L + Q_L j`
      The late correlation.

    Returns
    -------
    out : (float, float)
      The tuple (code_freq, carrier_freq).

    """
    raise NotImplementedError()

default_loop_filter = swiftnav.track.SimpleTrackingLoop(
  (2, 0.7, 1),     # Code loop parameters
  (25, 0.7, 0.25), # Carrier loop parameters
  1e3              # Loop frequency
)

def track(samples, channels,
          ms_to_track=None,
          sampling_freq=defaults.sampling_freq,
          chipping_rate=defaults.chipping_rate,
          IF=defaults.IF,
          show_progress=True,
          loop_filter=default_loop_filter,
          stage2_delay = 100,
          correlator=swiftnav.correlate.track_correlate,
          num_ms=4,
          multi=True):

  n_channels = len(channels)

  # Add 22ms for safety, the corellator might try to access data a bit past
  # just the number of milliseconds specified.
  # TODO: Fix the correlator so this isn't an issue.
  samples_length_ms = 1e3 * len(samples) / sampling_freq - 22

  if ms_to_track is None:
    ms_to_track = samples_length_ms

  if samples_length_ms < ms_to_track:
    logger.warning("Samples set too short for requested tracking length (%.4fs)"
        % (ms_to_track * 1e-3))
    ms_to_track = samples_length_ms

  logger.info("Tracking %.4fs of data (%d samples)" %
      (ms_to_track * 1e-3, ms_to_track * 1e-3 * sampling_freq))

  if ms_to_track <= stage2_delay:
    num_points = int(math.floor(ms_to_track))
  else:
    num_points = stage2_delay + (ms_to_track - stage2_delay) / num_ms

  # Make sure we have an integer number of points
  num_points = int(math.floor(num_points))

  logger.info("Tracking starting")
  logger.debug("Tracking %d channels, PRNs %s" %
      (n_channels, [chan.prn+1 for chan in channels]))

  # If progressbar is not available, disable show_progress.
  if show_progress and not _progressbar_available:
    show_progress = False
    logger.warning("show_progress = True but progressbar module not found.")

  # Setup our progress bar if we need it
  if show_progress and not multi:
    widgets = ['  Tracking ',
               progressbar.Attribute(['chan', 'nchan'],
                                     '(CH: %d/%d)',
                                     '(CH: -/-)'), ' ',
               progressbar.Percentage(), ' ',
               progressbar.ETA(), ' ',
               progressbar.Bar()]
    pbar = progressbar.ProgressBar(widgets=widgets,
                                   maxval=n_channels*num_points,
                                   attr={'nchan': n_channels})
    pbar.start()
  else:
    pbar = None

  # Run tracking for each channel
  def do_channel(chan):
    track_result = TrackResults(num_points)
    track_result.prn = chan.prn

    # Convert acquisition SNR to C/N0
    cn0_0 = 10 * np.log10(chan.snr)
    cn0_0 += 10 * np.log10(1000) # Channel bandwidth
    cn0_est = swiftnav.track.CN0Estimator(1e3, cn0_0, 10, 1e3)

    # Estimate initial code freq via aiding from acq carrier freq
    code_freq_init = (chan.carr_freq - IF) * \
                     gps_constants.chip_rate / gps_constants.l1
    loop_filter.start(code_freq_init, chan.carr_freq - IF)
    code_phase = 0.0
    carr_phase = 0.0
    
    # Get a vector with the C/A code sampled 1x/chip
    ca_code = caCodes[chan.prn]

    # Add wrapping to either end to be able to do early/late
    ca_code = np.concatenate(([ca_code[1022]], ca_code, [ca_code[0]]))

    # Number of samples to seek ahead in file
    samples_per_chip = int(round(sampling_freq / chipping_rate))

    # Set sample_index to start on a code rollover
    sample_index = chan.code_phase * samples_per_chip

    # Process the specified number of ms
    for i in range(num_points):
      if pbar:
        pbar.update(i + n * num_points, attr={'chan': n+1})

      stage2 = i < stage2_delay

      E = 0+0.j; P = 0+0.j; L = 0+0.j

      num_inner_loops = 1 if stage2 else num_ms
      for j in range(num_inner_loops):
        samples_ = samples[sample_index:]

        E_, P_, L_, blksize, code_phase, carr_phase = correlator(
          samples_,
          loop_filter.code_freq + chipping_rate, code_phase,
          loop_filter.carr_freq + IF, carr_phase,
          ca_code,
          sampling_freq
        )
        sample_index += blksize

        E += E_; P += P_; L += L_

      loop_filter.update(E, P, L)

      track_result.carr_phase[i] = carr_phase
      track_result.carr_freq[i] = loop_filter.carr_freq + IF

      track_result.code_phase[i] = code_phase
      track_result.code_freq[i] = loop_filter.code_freq + chipping_rate

      # Record stuff for postprocessing
      track_result.absolute_sample[i] = sample_index

      track_result.E[i] = E
      track_result.P[i] = P
      track_result.L[i] = L

      track_result.cn0[i] = cn0_est.update(P.real)

    # Possibility for lock-detection later
    track_result.status = 'T'
    return track_result

  if multi:
    track_results=pp.parmap(do_channel, channels, show_progress=show_progress)
  else:
    track_results=map(do_channel, channels)

  if pbar:
    pbar.finish()

  logger.info("Tracking finished")

  return track_results


class TrackResults:
  def __init__(self, n_points):
    self.status = '-'
    self.prn = None
    self.absolute_sample = np.zeros(n_points)
    self.code_phase = np.zeros(n_points)
    self.code_freq = np.zeros(n_points)
    self.carr_phase = np.zeros(n_points)
    self.carr_freq = np.zeros(n_points)
    self.E = np.zeros(n_points, dtype=np.complex128)
    self.P = np.zeros(n_points, dtype=np.complex128)
    self.L = np.zeros(n_points, dtype=np.complex128)
    self.cn0 = np.zeros(n_points)


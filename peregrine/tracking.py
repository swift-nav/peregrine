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
import swiftnav.nav_msg
import defaults

import logging
logger = logging.getLogger(__name__)

# Import progressbar if it is available.
_progressbar_available = True
try:
  import progressbar
except ImportError:
  _progressbar_available = False

default_stage1_loop_filter_params = {
  'code_loop': {
    'bw': 1,
    'zeta': 0.7,
    'k': 1,
  },
  'carr_loop': {
    'bw': 25,
    'zeta': 0.7,
    'k': 1,
  },
  'loop_freq': 1e3,
  'carr_freq_b1': 5,
  'carr_to_code': 1540,
}


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


def track(samples, channels,
          ms_to_track=None,
          sampling_freq=defaults.sampling_freq,
          chipping_rate=defaults.chipping_rate,
          IF=defaults.IF,
          show_progress=True,
          loop_filter_class=swiftnav.track.AidedTrackingLoop,
          stage1_loop_filter_params=\
            default_stage1_loop_filter_params,
          correlator=swiftnav.correlate.track_correlate_,
          stage2_coherent_ms=None,
          stage2_loop_filter_params=None,
          multi=True):

  n_channels = len(channels)

  # Add 22ms for safety, the corellator might try to access data a bit past
  # just the number of milliseconds specified.
  # TODO: Fix the correlator so this isn't an issue.
  samples_length_ms = int(1e3 * len(samples) / sampling_freq - 22)

  if ms_to_track is None:
    ms_to_track = samples_length_ms

  if samples_length_ms < ms_to_track:
    logger.warning("Samples set too short for requested tracking length (%.4fs)"
        % (ms_to_track * 1e-3))
    ms_to_track = samples_length_ms

  logger.info("Tracking %.4fs of data (%d samples)" %
      (ms_to_track * 1e-3, ms_to_track * 1e-3 * sampling_freq))

  # Make sure we have an integer number of points
  num_points = int(math.floor(ms_to_track))

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
  def do_channel(chan, n=None, q_progress=None):
    track_result = TrackResults(num_points, chan.prn)

    # Convert acquisition SNR to C/N0
    cn0_0 = 10 * np.log10(chan.snr)
    cn0_0 += 10 * np.log10(1000) # Channel bandwidth
    cn0_est = swiftnav.track.CN0Estimator(
                                          bw=1e3,
                                          cn0_0=cn0_0,
                                          cutoff_freq=10,
                                          loop_freq=1e3
                                          )

    # Estimate initial code freq via aiding from acq carrier freq
    code_freq_init = (chan.carr_freq - IF) * \
                     gps_constants.chip_rate / gps_constants.l1
    carr_freq_init = chan.carr_freq - IF
    loop_filter = loop_filter_class(
      loop_freq    = stage1_loop_filter_params['loop_freq'],
      code_freq    = code_freq_init,
      code_bw      = stage1_loop_filter_params['code_loop_bw'],
      code_zeta    = stage1_loop_filter_params['code_loop_zeta'],
      code_k       = stage1_loop_filter_params['code_loop_k'],
      carr_to_code = stage1_loop_filter_params['carr_to_code'],
      carr_freq    = carr_freq_init, \
      carr_bw      = stage1_loop_filter_params['carr_loop_bw'],
      carr_zeta    = stage1_loop_filter_params['carr_loop_zeta'],
      carr_k       = stage1_loop_filter_params['carr_loop_k'],
      carr_freq_b1 = stage1_loop_filter_params['carr_freq_b1'],
    )
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

    # Start in 1ms integration until we know the nav bit phase
    stage1 = True

    carr_phase_acc = 0.0
    code_phase_acc = 0.0

    progress = 0
    ms_tracked = 0
    i = 0
    # Process the specified number of ms
    while ms_tracked < ms_to_track:
      if pbar:
        pbar.update(ms_tracked + n * num_points, attr={'chan': n+1})

      E = 0+0.j; P = 0+0.j; L = 0+0.j

      if stage1 and stage2_coherent_ms and track_result.nav_msg.bit_phase == track_result.nav_msg.bit_phase_ref:
        #print "PRN %02d transition to stage 2 at %d ms" % (chan.prn+1, ms_tracked)
        stage1 = False
        loop_filter.retune(*stage2_loop_filter_params)
        cn0_est = swiftnav.track.CN0Estimator(bw=1e3/stage2_coherent_ms,
                                              cn0_0=track_result.cn0[i-1],
                                              cutoff_freq=10,
                                              loop_freq=1e3/stage2_coherent_ms)

      coherent_ms = 1 if stage1 else stage2_coherent_ms

      for j in range(coherent_ms):
        samples_ = samples[sample_index:]

        E_, P_, L_, blksize, code_phase, carr_phase = correlator(
          samples_,
          loop_filter.to_dict()['code_freq'] + chipping_rate, code_phase,
          loop_filter.to_dict()['carr_freq'] + IF, carr_phase,
          ca_code,
          sampling_freq
        )
        sample_index += blksize
        carr_phase_acc += loop_filter.to_dict()['carr_freq'] * blksize / sampling_freq
        code_phase_acc += loop_filter.to_dict()['code_freq'] * blksize / sampling_freq

        E += E_; P += P_; L += L_

      loop_filter.update(E, P, L)
      track_result.coherent_ms[i] = coherent_ms

      track_result.nav_bit_sync.update(np.real(P), coherent_ms)

      # TODO - Is this the correct way to call nav_msg.update?
      tow = track_result.nav_msg.update(np.real(P) >= 0)
      track_result.nav_msg_bit_phase_ref[i] = track_result.nav_msg.bit_phase_ref
      track_result.tow[i] = tow or (track_result.tow[i-1] + coherent_ms)

      track_result.carr_phase[i] = carr_phase
      track_result.carr_phase_acc[i] = carr_phase_acc
      track_result.carr_freq[i] = loop_filter.to_dict()['carr_freq'] + IF

      track_result.code_phase[i] = code_phase
      track_result.code_phase_acc[i] = code_phase_acc
      track_result.code_freq[i] = loop_filter.to_dict()['code_freq'] + chipping_rate

      # Record stuff for postprocessing
      track_result.absolute_sample[i] = sample_index

      track_result.E[i] = E
      track_result.P[i] = P
      track_result.L[i] = L

      track_result.cn0[i] = cn0_est.update(P.real, P.imag)

      i += 1
      ms_tracked += coherent_ms

      if q_progress and (i % 200 == 0):
        p = 1.0 * ms_tracked / ms_to_track
        q_progress.put(p - progress)
        progress = p

    # Possibility for lock-detection later
    track_result.status = 'T'

    track_result.resize(i)
    if q_progress:
      q_progress.put(1.0 - progress)

    return track_result

  if multi:
    track_results=pp.parmap(do_channel, channels,
                            show_progress=show_progress, func_progress=show_progress)
  else:
    track_results=map(lambda (n, chan): do_channel(chan, n=n), enumerate(channels))

  if pbar:
    pbar.finish()

  logger.info("Tracking finished")

  return track_results


class TrackResults:
  def __init__(self, n_points, prn):
    self.status = '-'
    self.prn = prn
    self.absolute_sample = np.zeros(n_points)
    self.code_phase = np.zeros(n_points)
    self.code_phase_acc = np.zeros(n_points)
    self.code_freq = np.zeros(n_points)
    self.carr_phase = np.zeros(n_points)
    self.carr_phase_acc = np.zeros(n_points)
    self.carr_freq = np.zeros(n_points)
    self.E = np.zeros(n_points, dtype=np.complex128)
    self.P = np.zeros(n_points, dtype=np.complex128)
    self.L = np.zeros(n_points, dtype=np.complex128)
    self.cn0 = np.zeros(n_points)
    self.nav_msg = swiftnav.nav_msg.NavMsg()
    self.nav_msg_bit_phase_ref = np.zeros(n_points)
    self.nav_bit_sync = NBSMatchBit() if prn < 32 else NBSSBAS()
    self.tow = np.empty(n_points)
    self.tow[:] = np.NAN
    self.coherent_ms = np.zeros(n_points)

  def resize(self, n_points):
    for k in dir(self):
      v = getattr(self, k)
      if isinstance(v, np.ndarray):
        v.resize(n_points, refcheck=False)

  def __eq__(self, other):
    return self._equal(other)

  def _equal(self, other):
    """
    Compare equality between self and another :class:`TrackResults` object.

    Parameters
    ----------
    other : :class:`TrackResults` object
      The :class:`TrackResults` to test equality against.

    Return
    ------
    out : bool
      True if the passed :class:`TrackResults` object is identical.

    """
    if self.__dict__.keys() != other.__dict__.keys():
      return False
    
    for k in self.__dict__.keys():
      if isinstance(self.__dict__[k], np.ndarray):
        # If np.ndarray, elements might be floats, so compare accordingly.
        if any(np.greater((self.__dict__[k]-other.__dict__[k]), np.ones(len(self.__dict__[k]))*10e-6)):
          return False
      elif self.__dict__[k] != other.__dict__[k]:
        return False

    return True


class NavBitSync:
  def __init__(self):
    self.bit_phase = 0
    self.bit_integrate = 0
    self.synced=False
    self.bits=[]
    self.bit_phase_ref=-1 # A new bit begins when bit_phase == bit_phase_ref
    self.count = 0
    
  def update(self, corr, ms):
    self.bit_phase += ms
    self.bit_phase %= 20
    self.count += 1
    self.bit_integrate += corr
    if not self.synced:
      self.update_bit_sync(corr, ms)
    if self.bit_phase == self.bit_phase_ref:
      self.bits.append(1 if self.bit_integrate > 0 else 0)
      self.bit_integrate = 0

  def update_bit_sync(self, corr, ms):
    raise NotImplementedError

  def bitstring(self):
    return ''.join(map(str, self.bits))

  def __eq__(self, other):
    return self._equal(other)

  def __ne__(self, other):
    return not self._equal(other)

  def _equal(self, other):
    """
    Compare equality between self and another :class:`NavBitSync` object.

    Parameters
    ----------
    other : :class:`NavBitSync` object
      The :class:`NavBitSync` to test equality against.

    Return
    ------
    out : bool
      True if the passed :class:`NavBitSync` object is identical.

    """
    if self.__dict__.keys() != other.__dict__.keys():
      return False
    
    for k in self.__dict__.keys():
      if isinstance(self.__dict__[k], np.ndarray):
        # If np.ndarray, elements might be floats, so compare accordingly.
        if any((self.__dict__[k]-other.__dict__[k]) > 10e-6):
          return False
      elif self.__dict__[k] != other.__dict__[k]:
        return False

    return True

class NavBitSyncSBAS:
  def __init__(self):
    self.bit_phase = 0
    self.bit_integrate = 0
    self.synced=False
    self.bits=[]
    self.bit_phase_ref=-1 # A new bit begins when bit_phase == bit_phase_ref
    self.count = 0

  def update(self, corr, ms):
    self.bit_phase += ms
    self.bit_phase %= 2
    self.count += 1
    self.bit_integrate += corr
    if not self.synced:
      self.update_bit_sync(corr, ms)
    if self.bit_phase == self.bit_phase_ref:
      self.bits.append(1 if self.bit_integrate > 0 else 0)
      self.bit_integrate = 0

  def update_bit_sync(self, corr, ms):
    raise NotImplementedError

  def bitstring(self):
    return ''.join(map(str, self.bits))


class NBSSBAS(NavBitSyncSBAS):
  def __init__(self, thres=200):
    NavBitSyncSBAS.__init__(self)
    self.hist = np.zeros(2)
    self.acc = 0
    self.prev = np.zeros(2)
    self.thres = thres
    self.score = 0

  def update_bit_sync(self, corr, ms):
    self.bit_integrate -= self.prev[self.bit_phase]
    self.prev[self.bit_phase] = corr
    if self.count >= 2:
      # Accumulator valid
      self.hist[self.bit_phase % 2] += abs(self.bit_integrate)
      if self.bit_phase == 1:
        # Histogram valid
        sh = sorted(self.hist)
        self.score = sh[-1] - sh[-2]
        max_prev_corr = max(np.abs(self.prev))
        if self.score > self.thres * 2 * max_prev_corr:
          self.synced = True
          self.bit_phase_ref = np.argmax(self.hist)

class NBSLibSwiftNav(NavBitSync):
  def __init__(self):
    NavBitSync.__init__(self)
    self.nav_msg = swiftnav.nav_msg.NavMsg()

  def update_bit_sync(self, corr, ms):
    self.nav_msg.update(corr, ms)
    self.bit_phase_ref = self.nav_msg.bit_phase_ref
    self.synced = self.bit_phase_ref >= 0

class NBSMatchBit(NavBitSync):
  def __init__(self, thres=22):
    NavBitSync.__init__(self)
    self.hist = np.zeros(20)
    self.acc = 0
    self.prev = np.zeros(20)
    self.thres = thres
    self.score = 0

  def update_bit_sync(self, corr, ms):
    self.bit_integrate -= self.prev[self.bit_phase]
    self.prev[self.bit_phase] = corr
    if self.count >= 20:
      # Accumulator valid
      self.hist[(self.bit_phase) % 20] += abs(self.bit_integrate)
      if self.bit_phase == 19:
        # Histogram valid
        sh = sorted(self.hist)
        self.score = sh[-1] - sh[-2]
        max_prev_corr = max(np.abs(self.prev))
        if self.score > self.thres * 2 * max_prev_corr:
          self.synced = True
          self.bit_phase_ref = np.argmax(self.hist)

class NBSHistogram(NavBitSync):
  def __init__(self, thres=10):
    NavBitSync.__init__(self)
    self.bit_phase_count = 0
    self.prev_corr = 0
    self.hist = np.zeros(20)
    self.thres = thres

  def update_bit_sync(self, corr, ms):
    dot = corr * self.prev_corr
    self.prev_corr = corr
    if dot < 0:
      self.hist[self.bit_phase % 20] += -dot
      self.bit_phase_count += 1
      if self.bit_phase_count == self.thres:
        self.synced = True
        self.bit_phase_ref = np.argmax(self.hist)
        self.hist = np.zeros(20)
        self.bit_phase_count = 0

class NBSMatchEdge(NavBitSync):
  # TODO: This isn't quite right - might get wrong answer with long leading run of same bits, depending on initial phase
  def __init__(self, thres=100000):
    NavBitSync.__init__(self)
    self.hist = np.zeros(20)
    self.acc = 0
    self.prev = np.zeros(40)
    self.thres = thres

  def update_bit_sync(self, corr, ms):
    bp40 = self.bit_phase % 40
    self.acc += corr - 2*self.prev[(bp40 - 20) % 40] + self.prev[bp40]
    self.prev[bp40] = corr
    if self.bit_phase >= 40:
      # Accumulator valid
      self.hist[(bp40 + 1) % 20] += abs(self.acc)
      if bp40 % 20 == 19:
        # Histogram valid
        sh = sorted(self.hist)
        if sh[-1] - sh[-2] > self.thres:
          self.synced = True
          self.bit_phase_ref = np.argmax(self.hist)

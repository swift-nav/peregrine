# Copyright (C) 2012,2016 Swift Navigation Inc.
# Contact: Adel Mamin <adelm@exafore.com>
#
# This source is subject to the license found in the file 'LICENSE' which must
# be be distributed together with this source. All other rights reserved.
#
# THIS CODE AND INFORMATION IS PROVIDED "AS IS" WITHOUT WARRANTY OF ANY KIND,
# EITHER EXPRESSED OR IMPLIED, INCLUDING BUT NOT LIMITED TO THE IMPLIED
# WARRANTIES OF MERCHANTABILITY AND/OR FITNESS FOR A PARTICULAR PURPOSE.

import numpy as np
from include.generateCAcode import caCodes
from include.generateL2CMcode import L2CMCodes
import gps_constants
import progressbar
import math
import parallel_processing as pp

import swiftnav.track
import swiftnav.correlate
import swiftnav.nav_msg
import swiftnav.cnav_msg
import swiftnav.ephemeris
import defaults
from peregrine.acquisition import AcquisitionResult

import logging
logger = logging.getLogger(__name__)

# Import progressbar if it is available.
_progressbar_available = True
try:
  import progressbar
except ImportError:
  _progressbar_available = False

default_stage1_loop_filter_params = {
  'code_loop_bw': 1,
  'code_loop_zeta': 0.7,
  'code_loop_k': 1,
  'carr_loop_bw': 25,
  'carr_loop_zeta': 0.7,
  'carr_loop_k': 1,
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
          ms_to_track,
          sampling_freq,
          chipping_rate=defaults.chipping_rate,
          show_progress=True,
          loop_filter_class=swiftnav.track.AidedTrackingLoop,
          correlator=swiftnav.correlate.track_correlate,
          stage2_coherent_ms=None,
          stage2_loop_filter_params=None,
          multi=True):

  n_channels = len(channels)

  samples_length_ms = int(1e3 * len(samples[0]['data']) / sampling_freq)

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
               (n_channels, [chan.prn + 1 for chan in channels]))

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
                                   maxval=n_channels * num_points,
                                   attr={'nchan': n_channels})
    pbar.start()
  else:
    pbar = None

  # Run tracking for each channel
  def do_channel(chan, n=None, q_progress=None):
    isL1CA = (chan.signal == gps_constants.L1CA)
    isL2C = (chan.signal == gps_constants.L2C)

    if not isL1CA and not isL2C:
      NotImplementedError("Signal type '%s' is not supported" % chan.signal)

    track_result = TrackResults(num_points, chan.prn, chan.signal)
    l2c_handover_chan = AcquisitionResult(chan.prn, 0, 0, 0, 0, '-', 'l2c')

    # Do not track if acquisition or handover failed
    if chan.status == '-':
      return track_result, l2c_handover_chan

    IF = samples[chan.sample_channel]['IF']

    logger.info("[PRN: %d (%s)] Tracking is started."
                "IF: %f, Doppler: %f, code phase: %f, "
                "sample channel: %d sample index: %d" %
                (chan.prn + 1, chan.signal,
                 IF, chan.doppler, chan.code_phase,
                 chan.sample_channel,
                 chan.sample_index if chan.sample_index else 0))

    if isL1CA:
      loop_filter_params = defaults.l1ca_stage1_loop_filter_params
      lock_detect_params = defaults.l1ca_lock_detect_params_opt
      lock_detect = swiftnav.track.LockDetector(
                       k1 = lock_detect_params["k1"],
                       k2 = lock_detect_params["k2"],
                       lp = lock_detect_params["lp"],
                       lo = lock_detect_params["lo"])
      prn_code = caCodes[chan.prn]
      coherent_ms = 1
      nav_msg = swiftnav.nav_msg.NavMsg()
      nav_msg_bit_phase_ref = np.zeros(num_points)
      nav_bit_sync = NBSMatchBit() if chan.prn < 32 else NBSSBAS()
      # Convert acquisition SNR to C/N0
      cn0_0 = 10 * np.log10(chan.snr)
      cn0_0 += 10 * np.log10(defaults.L1CA_CHANNEL_BANDWIDTH_HZ)
    elif isL2C:
      loop_filter_params = defaults.l2c_loop_filter_params
      lock_detect_params = defaults.l2c_lock_detect_params_20ms
      lock_detect = swiftnav.track.LockDetector(
                       k1 = lock_detect_params["k1"],
                       k2 = lock_detect_params["k2"],
                       lp = lock_detect_params["lp"],
                       lo = lock_detect_params["lo"])
      prn_code = L2CMCodes[chan.prn]
      coherent_ms = 20
      cnav_msg = swiftnav.cnav_msg.CNavMsg()
      cnav_msg_decoder = swiftnav.cnav_msg.CNavMsgDecoder()
      # Convert acquisition SNR to C/N0
      cn0_0 = 10 * np.log10(chan.snr)
      cn0_0 += 10 * np.log10(defaults.L2C_CHANNEL_BANDWIDTH_HZ)
    else:
      raise NotImplementedError()

    alias_detect_init = 1 # require alias_detect_first() call
                          # or alias_detect.reinit() call or both
    alias_detect = swiftnav.track.AliasDetector(
                     acc_len = defaults.alias_detect_interval_ms / coherent_ms,
                     time_diff = 1)

    cn0_est = swiftnav.track.CN0Estimator(
        bw=1e3,
        cn0_0=cn0_0,
        cutoff_freq=10,
        loop_freq=loop_filter_params["loop_freq"]
    )

    # Estimate initial code freq via aiding from acq carrier freq
    if isL1CA:
      code_freq_init = (chan.carr_freq - IF) * \
          gps_constants.chip_rate / gps_constants.l1
    elif isL2C:
      code_freq_init = (chan.carr_freq - IF) * \
          gps_constants.chip_rate / gps_constants.l2
    else:
      raise NotImplementedError()

    carr_freq_init = chan.carr_freq - IF
    loop_filter = loop_filter_class(
        loop_freq=loop_filter_params['loop_freq'],
        code_freq=code_freq_init,
        code_bw=loop_filter_params['code_bw'],
        code_zeta=loop_filter_params['code_zeta'],
        code_k=loop_filter_params['code_k'],
        carr_to_code=0, # the provided code frequency accounts for Doppler
        carr_freq=carr_freq_init,
        carr_bw=loop_filter_params['carr_bw'],
        carr_zeta=loop_filter_params['carr_zeta'],
        carr_k=loop_filter_params['carr_k'],
        carr_freq_b1=loop_filter_params['carr_freq_b1'],
    )
    code_phase = 0.0
    carr_phase = 0.0

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
    # For L2C, proceed in steps of full milliseconds up to the ms when
    # handover succeeded. Do not set sample_index := chan.sample_index
    # since the sub ms part of sample_index presents code phase.
    # Therefore, skip just full ms steps to preserve code phase.
    if isL2C:
      samples_per_ms = sampling_freq * defaults.code_period
      skip_ms = int((chan.sample_index - sample_index) / samples_per_ms)
      skip_samples = skip_ms * samples_per_ms
      sample_index += skip_samples
      ms_tracked += skip_ms

    # Process the specified number of ms
    while ms_tracked < ms_to_track:
      if pbar:
        pbar.update(ms_tracked + n * num_points, attr={'chan': n + 1})

      if isL1CA:
        # For L1 C/A there are coherent and non-coherent tracking options.
        if stage1 and \
           stage2_coherent_ms and \
           nav_bit_sync.bit_phase == nav_bit_sync.bit_phase_ref:

          stage1 = False
          coherent_ms = stage2_coherent_ms
          loop_filter.retune(*stage2_loop_filter_params)
          lock_detect.reinit(
                       k1 = lock_detect_params["k1"] * coherent_ms,
                       k2 = lock_detect_params["k2"],
                       lp = lock_detect_params["lp"],
                       lo = lock_detect_params["lo"]);
          cn0_est = swiftnav.track.CN0Estimator(bw=1e3 / stage2_coherent_ms,
                                                cn0_0=track_result.cn0[i - 1],
                                                cutoff_freq=10,
                                                loop_freq=1e3 / stage2_coherent_ms)

        coherent_iter = coherent_ms
      elif isL2C:
        # L2 C is always tracked coherently
        coherent_ms = 20
        coherent_iter = 1
      else:
        raise NotImplementedError()

      E = 0 + 0.j
      P = 0 + 0.j
      L = 0 + 0.j

      for _ in range(coherent_iter):

        if sample_index >= len(samples[chan.sample_channel]['data']):
          break

        samples_ = samples[chan.sample_channel]['data'][sample_index:]

        E_, P_, L_, blksize, code_phase, carr_phase = correlator(
            samples_,
            loop_filter.to_dict()['code_freq'] + chipping_rate, code_phase,
            loop_filter.to_dict()['carr_freq'] + IF, carr_phase,
            prn_code,
            sampling_freq,
            chan.signal
        )
        sample_index += blksize
        carr_phase_acc += loop_filter.to_dict()['carr_freq'] * \
            blksize / sampling_freq
        code_phase_acc += loop_filter.to_dict()['code_freq'] * \
            blksize / sampling_freq

        E += E_
        P += P_
        L += L_

      # Update PLL lock detector
      lock_detect_outo, lock_detect_outp, \
      lock_detect_pcount1, lock_detect_pcount2, \
      lock_detect_lpfi, lock_detect_lpfq = lock_detect.update(P.real, P.imag,
                                                              coherent_ms)

      if lock_detect_outo:
        if alias_detect_init:
          alias_detect_init = 0
          alias_detect.reinit(defaults.alias_detect_interval_ms / coherent_ms,
                              time_diff = 1)
          alias_detect.first(P.real, P.imag)
        alias_detect_err_hz = alias_detect.second(P.real, P.imag) * np.pi * \
                              (1e3 / defaults.alias_detect_interval_ms)
        alias_detect.first(P.real, P.imag)
      else:
        alias_detect_init = 1
        alias_detect_err_hz = 0

      loop_filter.update(E, P, L)
      track_result.coherent_ms[i] = coherent_ms

      if isL1CA:
        sync, bit = nav_bit_sync.update(np.real(P), coherent_ms)
        if sync:
          tow = nav_msg.update(bit)
          if tow >= 0:
            logger.info("[PRN: %d (%s)] ToW %d" %
                        (chan.prn + 1, chan.signal, tow))
          if nav_msg.subframe_ready():
            eph = swiftnav.ephemeris.Ephemeris()
            res = nav_msg.process_subframe(eph)
            if res < 0:
              logger.error("[PRN: %d (%s)] Subframe decoding error %d" %
                           (chan.prn + 1, chan.signal, res))
            elif res > 0:
              logger.info("[PRN: %d (%s)] Subframe decoded" %
                          (chan.prn + 1, chan.signal) )
            else:
              # Subframe decoding is in progress
              pass
        else:
          tow = -1
        nav_msg_bit_phase_ref[i] = nav_msg.bit_phase_ref
        track_result.tow[i] = tow if tow >= 0 else (
            track_result.tow[i - 1] + coherent_ms)
      elif isL2C:
        symbol = 0xFF if np.real(P) >= 0 else 0x00
        res, delay = cnav_msg_decoder.decode(symbol, cnav_msg)
        if res:
          logger.debug("[PRN: %d (%s)] CNAV message decoded: "
                       "prn=%d msg_id=%d tow=%d alert=%d delay=%d" %
                       (chan.prn + 1,
                        chan.signal,
                        cnav_msg.getPrn(),
                        cnav_msg.getMsgId(),
                        cnav_msg.getTow(),
                        cnav_msg.getAlert(),
                        delay))
          tow = cnav_msg.getTow() * 6000 + delay * 20
          logger.debug("[PRN: %d (%s)] ToW %d" % (chan.prn + 1, chan.signal, tow))
          track_result.tow[i] = tow
        else:
          track_result.tow[i] = track_result.tow[i - 1] + coherent_ms
      else:
        raise NotImplementedError()

      track_result.IF = IF
      track_result.carr_phase[i] = carr_phase
      track_result.carr_phase_acc[i] = carr_phase_acc
      track_result.carr_freq[i] = loop_filter.to_dict()['carr_freq'] + IF

      track_result.code_phase[i] = code_phase
      track_result.code_phase_acc[i] = code_phase_acc
      track_result.code_freq[
          i] = loop_filter.to_dict()['code_freq'] + chipping_rate

      # Record stuff for postprocessing
      track_result.absolute_sample[i] = sample_index

      track_result.E[i] = E
      track_result.P[i] = P
      track_result.L[i] = L

      track_result.cn0[i] = cn0_est.update(P.real, P.imag)

      track_result.lock_detect_outo[i] = lock_detect_outo
      track_result.lock_detect_outp[i] = lock_detect_outp
      track_result.lock_detect_pcount1[i] = lock_detect_pcount1
      track_result.lock_detect_pcount2[i] = lock_detect_pcount2
      track_result.lock_detect_lpfi[i] = lock_detect_lpfi
      track_result.lock_detect_lpfq[i] = lock_detect_lpfq

      track_result.alias_detect_err_hz[i] = alias_detect_err_hz

      # Handover to L2C if possible
      if isL1CA and l2c_handover_chan.status == '-' and sync:
        chan_snr = track_result.cn0[i]
        chan_snr -= 10 * np.log10(defaults.L1CA_CHANNEL_BANDWIDTH_HZ)
        chan_snr = np.power(10, chan_snr / 10)
        l2c_doppler = loop_filter.to_dict()['carr_freq'] * gps_constants.l2 / gps_constants.l1
        l2c_handover_chan = AcquisitionResult(track_result.prn,
                                              samples[chan.sample_channel]['IF'] + l2c_doppler,
                                              l2c_doppler, # carrier doppler
                                              track_result.code_phase[i],
                                              chan_snr,
                                              'A',
                                              'l2c',
                                              1, # samples' channel index
                                              track_result.absolute_sample[i])
      i += 1
      if isL1CA or isL2C:
        ms_tracked += coherent_ms
      else:
        raise NotImplementedError()

      if q_progress and (i % 200 == 0):
        p = 1.0 * ms_tracked / ms_to_track
        q_progress.put(p - progress)
        progress = p

    # Possibility for lock-detection later
    track_result.status = 'T'

    track_result.resize(i)
    if q_progress:
      q_progress.put(1.0 - progress)

    return track_result, l2c_handover_chan

  # Run L1CA
  if multi:
    track_handover_results = pp.parmap(do_channel, channels,
                                       show_progress=show_progress, func_progress=show_progress)
  else:
    track_handover_results = map(
        lambda (n, chan): do_channel(chan, n=n), enumerate(channels))
  # Extract track and handover results
  l1ca_track_results = map(lambda x: x[0], track_handover_results)
  l2c_handover_channels = map(lambda x: x[1], track_handover_results)

  # Run L2C
  logger.info("Start L2C tracking")
  if multi:
    track_handover_results = pp.parmap(do_channel, l2c_handover_channels,
                                       show_progress=show_progress, func_progress=show_progress)
  else:
    track_handover_results = map(lambda (n, chan): do_channel(
        chan, n=n), enumerate(l2c_handover_channels))
  # Extract track results, handover results are unused
  l2c_track_results = map(lambda x: x[0], track_handover_results)

  if pbar:
    pbar.finish()

  logger.info("Tracking finished")

  return l1ca_track_results + l2c_track_results


class TrackResults:

  def __init__(self, n_points, prn, signal):
    self.status = '-'
    self.prn = prn
    self.IF = 0
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
    self.lock_detect_outp = np.zeros(n_points)
    self.lock_detect_outo = np.zeros(n_points)
    self.lock_detect_pcount1 = np.zeros(n_points)
    self.lock_detect_pcount2 = np.zeros(n_points)
    self.lock_detect_lpfi = np.zeros(n_points)
    self.lock_detect_lpfq = np.zeros(n_points)
    self.alias_detect_err_hz = np.zeros(n_points)
    self.nav_msg = swiftnav.nav_msg.NavMsg()
    self.nav_msg_bit_phase_ref = np.zeros(n_points)
    self.nav_bit_sync = NBSMatchBit() if prn < 32 else NBSSBAS()
    self.tow = np.empty(n_points)
    self.tow[:] = np.NAN
    self.coherent_ms = np.zeros(n_points)
    # self.cnav_msg = swiftnav.cnav_msg.CNavMsg()
    # self.cnav_msg_decoder = swiftnav.cnav_msg.CNavMsgDecoder()
    self.signal = signal

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
    self.synced = False
    self.bits = []
    self.bit_phase_ref = -1  # A new bit begins when bit_phase == bit_phase_ref
    self.count = 0

  def update(self, corr, ms):
    self.bit_phase += ms
    self.bit_phase %= 20
    self.count += 1
    self.bit_integrate += corr
    if not self.synced:
      self.update_bit_sync(corr, ms)
    if self.bit_phase == self.bit_phase_ref:
      bit = 1 if self.bit_integrate > 0 else 0
      self.bits.append(bit)
      self.bit_integrate = 0
      return True, bit
    else:
      return False, None

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
    self.synced = False
    self.bits = []
    self.bit_phase_ref = -1  # A new bit begins when bit_phase == bit_phase_ref
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
  # TODO: This isn't quite right - might get wrong answer with long leading
  # run of same bits, depending on initial phase

  def __init__(self, thres=100000):
    NavBitSync.__init__(self)
    self.hist = np.zeros(20)
    self.acc = 0
    self.prev = np.zeros(40)
    self.thres = thres

  def update_bit_sync(self, corr, ms):
    bp40 = self.bit_phase % 40
    self.acc += corr - 2 * self.prev[(bp40 - 20) % 40] + self.prev[bp40]
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

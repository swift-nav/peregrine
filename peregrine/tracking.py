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
import os
import math
import parallel_processing as pp
import multiprocessing as mp

from swiftnav.track import LockDetector
from swiftnav.track import CN0Estimator
from swiftnav.track import AliasDetector
from swiftnav.track import AidedTrackingLoop
from swiftnav.correlate import track_correlate
from swiftnav.nav_msg import NavMsg
from swiftnav.cnav_msg import CNavMsg
from swiftnav.cnav_msg import CNavMsgDecoder
from swiftnav.ephemeris import Ephemeris
from peregrine import defaults
from peregrine import gps_constants
from peregrine.acquisition import AcquisitionResult
from peregrine.include.generateCAcode import caCodes
from peregrine.include.generateL2CMcode import L2CMCodes

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


def _tracking_channel_factory(parameters):
  if parameters['acq'].signal == gps_constants.L1CA:
    return TrackingChannelL1CA(parameters)
  if parameters['acq'].signal == gps_constants.L2C:
    return TrackingChannelL2C(parameters)


class TrackingChannel(object):

  def __init__(self, params):
    for (key, value) in params.iteritems():
      setattr(self, key, value)

    self.prn = params['acq'].prn
    self.signal = params['acq'].signal

    self.results_num = 1000
    self.stage1 = True

    self.lock_detect = LockDetector(
        k1=self.lock_detect_params["k1"],
        k2=self.lock_detect_params["k2"],
        lp=self.lock_detect_params["lp"],
        lo=self.lock_detect_params["lo"])

    self.alias_detect = AliasDetector(
        acc_len=defaults.alias_detect_interval_ms / self.coherent_ms,
        time_diff=1)

    self.cn0_est = CN0Estimator(
        bw=1e3 / self.coherent_ms,
        cn0_0=self.cn0_0,
        cutoff_freq=10,
        loop_freq=self.loop_filter_params["loop_freq"]
    )

    self.loop_filter = self.loop_filter_class(
        loop_freq=self.loop_filter_params['loop_freq'],
        code_freq=self.code_freq_init,
        code_bw=self.loop_filter_params['code_bw'],
        code_zeta=self.loop_filter_params['code_zeta'],
        code_k=self.loop_filter_params['code_k'],
        carr_to_code=0,  # the provided code frequency accounts for Doppler
        carr_freq=self.acq.doppler,
        carr_bw=self.loop_filter_params['carr_bw'],
        carr_zeta=self.loop_filter_params['carr_zeta'],
        carr_k=self.loop_filter_params['carr_k'],
        carr_freq_b1=self.loop_filter_params['carr_freq_b1'],
    )

    self.next_code_freq = self.loop_filter.to_dict()['code_freq']
    self.next_carr_freq = self.loop_filter.to_dict()['carr_freq']

    self.track_result = TrackResults(
        self.results_num, self.acq.prn, self.acq.signal)
    self.alias_detect_init = 1
    self.code_phase = 0.0
    self.carr_phase = 0.0
    self.samples_per_chip = int(round(self.sampling_freq / self.chipping_rate))
    self.sample_index = self.acq.sample_index
    self.sample_index += self.acq.code_phase * self.samples_per_chip
    self.sample_index = int(math.floor(self.sample_index))
    self.carr_phase_acc = 0.0
    self.code_phase_acc = 0.0
    self.samples_tracked = 0
    self.i = 0
    #self.samples_offset = self.samples['samples_offset']

    self.pipelining = False
    self.pipelining_k = 0.
    if self.tracker_options:
      self.mode = self.tracker_options['mode']
      if self.mode == 'pipelining':
        self.pipelining = True
        self.pipelining_k = self.tracker_options['k']
      else:
        raise ValueError("Invalid tracker mode %s" % str(self.mode))

  def dump(self):
    filename = self.track_result.dump(self.output_file, self.i)
    self.i = 0
    return filename

  def start(self):
    logger.info("[PRN: %d (%s)] Tracking is started. "
                "IF: %.1f, Doppler: %.1f, code phase: %.1f, "
                "sample channel: %d sample index: %d" %
                (self.prn + 1,
                 self.signal,
                 self.IF,
                 self.acq.doppler,
                 self.acq.code_phase,
                 self.acq.sample_channel,
                 self.acq.sample_index))

  def get_index(self):
    return self.sample_index

  def _run_preprocess(self):  # optionally redefined in subclasses
    pass

  def _run_postprocess(self):  # optionally redefine in subclasses
    pass

  def _get_result(self):  # optionally redefine in subclasses
    return None

  def run_parallel(self, samples):
    handover = self.run(samples)
    return (handover, self)

  def run(self, samples):

    self.samples = samples

    if self.sample_index < samples['sample_index']:
      raise ValueError("Incorrent samples offset")

    sample_index = self.sample_index - samples['sample_index']
    samples_processed = 0
    samples_total = len(samples[self.signal]['samples'])

    estimated_blksize = self.coherent_ms * self.sampling_freq / 1e3

    while self.samples_tracked < self.samples_to_track and \
            (sample_index + 2 * estimated_blksize) < samples_total:

      self._run_preprocess()

      if self.pipelining:
        # Pipelining and prediction
        corr_code_freq, corr_carr_freq = self.next_code_freq, self.next_carr_freq

        self.next_code_freq = self.loop_filter.to_dict()['code_freq']
        self.next_carr_freq = self.loop_filter.to_dict()['carr_freq']

        # There is an error between target frequency and actual one. Affect
        # the target frequency according to the computed error
        carr_freq_error = self.next_carr_freq - corr_carr_freq
        self.next_carr_freq += carr_freq_error * self.pipelining_k

        code_freq_error = self.next_code_freq - corr_code_freq
        self.next_code_freq += code_freq_error * self.pipelining_k

      else:
        # Immediate correction simulation
        self.next_code_freq = self.loop_filter.to_dict()['code_freq']
        self.next_carr_freq = self.loop_filter.to_dict()['carr_freq']

        corr_code_freq, corr_carr_freq = self.next_code_freq, self.next_carr_freq

      self.E = self.P = self.L = 0.j

      for _ in range(self.coherent_iter):

        if (sample_index + 2 * estimated_blksize) >= samples_total:
          break

        samples_ = samples[self.signal]['samples'][sample_index:]

        E_, P_, L_, blksize, self.code_phase, self.carr_phase = self.correlator(
            samples_,
            corr_code_freq + self.chipping_rate, self.code_phase,
            corr_carr_freq + self.IF, self.carr_phase,
            self.prn_code,
            self.sampling_freq,
            self.signal
        )

        if blksize > estimated_blksize:
          estimated_blksize = blksize

        sample_index += blksize
        samples_processed += blksize
        self.carr_phase_acc += corr_carr_freq * blksize / self.sampling_freq
        self.code_phase_acc += corr_code_freq * blksize / self.sampling_freq

        self.E += E_
        self.P += P_
        self.L += L_

      # Update PLL lock detector
      lock_detect_outo, \
          lock_detect_outp, \
          lock_detect_pcount1, \
          lock_detect_pcount2, \
          lock_detect_lpfi, \
          lock_detect_lpfq = self.lock_detect.update(self.P.real,
                                                     self.P.imag,
                                                     self.coherent_ms)

      if lock_detect_outo:
        if self.alias_detect_init:
          self.alias_detect_init = 0
          self.alias_detect.reinit(defaults.alias_detect_interval_ms /
                                   self.coherent_ms,
                                   time_diff=1)
          self.alias_detect.first(self.P.real, self.P.imag)
        alias_detect_err_hz = \
            self.alias_detect.second(self.P.real, self.P.imag) * np.pi * \
            (1e3 / defaults.alias_detect_interval_ms)
        self.alias_detect.first(self.P.real, self.P.imag)
      else:
        self.alias_detect_init = 1
        alias_detect_err_hz = 0

      self.loop_filter.update(self.E, self.P, self.L)
      self.track_result.coherent_ms[self.i] = self.coherent_ms

      self.track_result.IF = self.IF
      self.track_result.carr_phase[self.i] = self.carr_phase
      self.track_result.carr_phase_acc[self.i] = self.carr_phase_acc
      self.track_result.carr_freq[self.i] = \
          self.loop_filter.to_dict()['carr_freq'] + self.IF

      self.track_result.code_phase[self.i] = self.code_phase
      self.track_result.code_phase_acc[self.i] = self.code_phase_acc
      self.track_result.code_freq[self.i] = \
          self.loop_filter.to_dict()['code_freq'] + self.chipping_rate

      # Record stuff for postprocessing
      self.track_result.absolute_sample[self.i] = self.sample_index + \
          samples_processed

      self.track_result.E[self.i] = self.E
      self.track_result.P[self.i] = self.P
      self.track_result.L[self.i] = self.L

      self.track_result.cn0[self.i] = self.cn0_est.update(
          self.P.real, self.P.imag)

      self.track_result.lock_detect_outo[self.i] = lock_detect_outo
      self.track_result.lock_detect_outp[self.i] = lock_detect_outp
      self.track_result.lock_detect_pcount1[self.i] = lock_detect_pcount1
      self.track_result.lock_detect_pcount2[self.i] = lock_detect_pcount2
      self.track_result.lock_detect_lpfi[self.i] = lock_detect_lpfi
      self.track_result.lock_detect_lpfq[self.i] = lock_detect_lpfq

      self.track_result.alias_detect_err_hz[self.i] = alias_detect_err_hz

      self._run_postprocess()

      self.samples_tracked = self.sample_index + samples_processed
      self.track_result.ms_tracked[self.i] = self.samples_tracked * 1e3 / \
          self.sampling_freq

      self.i += 1
      if self.i >= self.results_num:
        self.dump()

    self.sample_index += samples_processed
    self.track_result.status = 'T'

    return self._get_result()


class TrackingChannelL1CA(TrackingChannel):

  def __init__(self, params):
    # Convert acquisition SNR to C/N0
    cn0_0 = 10 * np.log10(params['acq'].snr)
    cn0_0 += 10 * np.log10(defaults.L1CA_CHANNEL_BANDWIDTH_HZ)

    params['cn0_0'] = cn0_0
    params['coherent_ms'] = 1
    params['IF'] = params['samples'][gps_constants.L1CA]['IF']
    params['prn_code'] = caCodes[params['acq'].prn]
    params['code_freq_init'] = params['acq'].doppler * \
        gps_constants.chip_rate / gps_constants.l1
    params['loop_filter_params'] = defaults.l1ca_stage1_loop_filter_params
    params['lock_detect_params'] = defaults.l1ca_lock_detect_params_opt

    TrackingChannel.__init__(self, params)

    self.nav_msg = NavMsg()
    self.nav_bit_sync = NBSMatchBit() if self.prn < 32 else NBSSBAS()
    self.l2c_handover_acq = None
    self.l2c_handover_done = False

  def _run_preprocess(self):
    # For L1 C/A there are coherent and non-coherent tracking options.
    if self.stage1 and \
       self.stage2_coherent_ms and \
       self.nav_bit_sync.bit_phase == self.nav_bit_sync.bit_phase_ref:

      logger.info("[PRN: %d (%s)] switching to stage2, coherent_ms=%d" %
                  (self.prn + 1, self.signal, self.stage2_coherent_ms))

      self.stage1 = False
      self.coherent_ms = self.stage2_coherent_ms

      self.loop_filter.retune(**self.stage2_loop_filter_params)
      self.lock_detect.reinit(
          k1=self.lock_detect_params["k1"] * self.coherent_ms,
          k2=self.lock_detect_params["k2"],
          lp=self.lock_detect_params["lp"],
          lo=self.lock_detect_params["lo"])
      self.cn0_est = CN0Estimator(bw=1e3 / self.stage2_coherent_ms,
                                  cn0_0=self.track_result.cn0[self.i - 1],
                                  cutoff_freq=10,
                                  loop_freq=1e3 / self.stage2_coherent_ms)

    self.coherent_iter = self.coherent_ms

  def _get_result(self):
    if self.l2c_handover_acq and not self.l2c_handover_done:
      self.l2c_handover_done = True
      return self.l2c_handover_acq
    return None

  def _run_postprocess(self):
    sync, bit = self.nav_bit_sync.update(np.real(self.P), self.coherent_ms)
    if sync:
      tow = self.nav_msg.update(bit)
      if tow >= 0:
        logger.info("[PRN: %d (%s)] ToW %d" %
                    (self.prn + 1, self.signal, tow))
      if self.nav_msg.subframe_ready():
        eph = Ephemeris()
        res = self.nav_msg.process_subframe(eph)
        if res < 0:
          logger.error("[PRN: %d (%s)] Subframe decoding error %d" %
                       (self.prn + 1, self.signal, res))
        elif res > 0:
          logger.info("[PRN: %d (%s)] Subframe decoded" %
                      (self.prn + 1, self.signal))
        else:
          # Subframe decoding is in progress
          pass
    else:
      tow = -1
    self.track_result.tow[self.i] = tow if tow >= 0 else (
        self.track_result.tow[self.i - 1] + self.coherent_ms)

    # Handover to L2C if possible
    if self.l2c_handover and not self.l2c_handover_acq and \
       'samples' in self.samples[gps_constants.L2C] and sync:
      chan_snr = self.track_result.cn0[self.i]
      chan_snr -= 10 * np.log10(defaults.L1CA_CHANNEL_BANDWIDTH_HZ)
      chan_snr = np.power(10, chan_snr / 10)
      l2c_doppler = self.loop_filter.to_dict(
      )['carr_freq'] * gps_constants.l2 / gps_constants.l1
      self.l2c_handover_acq = AcquisitionResult(self.prn,
                                                self.samples[gps_constants.L2C][
                                                    'IF'] + l2c_doppler,
                                                l2c_doppler,  # carrier doppler
                                                self.track_result.code_phase[
                                                    self.i],
                                                chan_snr,
                                                'A',
                                                gps_constants.L2C,
                                                self.track_result.absolute_sample[self.i])


class TrackingChannelL2C(TrackingChannel):

  def __init__(self, params):
    # Convert acquisition SNR to C/N0
    cn0_0 = 10 * np.log10(params['acq'].snr)
    cn0_0 += 10 * np.log10(defaults.L2C_CHANNEL_BANDWIDTH_HZ)
    params['cn0_0'] = cn0_0
    params['coherent_ms'] = 20
    params['coherent_iter'] = 1
    params['loop_filter_params'] = defaults.l2c_loop_filter_params
    params['lock_detect_params'] = defaults.l2c_lock_detect_params_20ms
    params['IF'] = params['samples'][gps_constants.L2C]['IF']
    params['prn_code'] = L2CMCodes[params['acq'].prn]
    params['code_freq_init'] = params['acq'].doppler * \
        gps_constants.chip_rate / gps_constants.l2

    TrackingChannel.__init__(self, params)

    self.cnav_msg = CNavMsg()
    self.cnav_msg_decoder = CNavMsgDecoder()

  def _run_postprocess(self):
    symbol = 0xFF if np.real(self.P) >= 0 else 0x00
    res, delay = self.cnav_msg_decoder.decode(symbol, self.cnav_msg)
    if res:
      logger.debug("[PRN: %d (%s)] CNAV message decoded: "
                   "prn=%d msg_id=%d tow=%d alert=%d delay=%d" %
                   (self.prn + 1,
                    self.signal,
                    self.cnav_msg.getPrn(),
                    self.cnav_msg.getMsgId(),
                    self.cnav_msg.getTow(),
                    self.cnav_msg.getAlert(),
                    delay))
      tow = self.cnav_msg.getTow() * 6000 + delay * 20
      logger.debug("[PRN: %d (%s)] ToW %d" %
                   (self.prn + 1, self.signal, tow))
      self.track_result.tow[self.i] = tow
    else:
      self.track_result.tow[self.i] = self.track_result.tow[self.i - 1] + \
          self.coherent_ms


class Tracker(object):

  def __init__(self,
               samples,
               channels,
               ms_to_track,
               sampling_freq,
               chipping_rate=defaults.chipping_rate,
               l2c_handover=True,
               show_progress=True,
               loop_filter_class=AidedTrackingLoop,
               correlator=track_correlate,
               stage2_coherent_ms=None,
               stage2_loop_filter_params=None,
               multi=True,
               tracker_options=None,
               output_file=None):

    self.samples = samples
    self.sampling_freq = sampling_freq
    self.ms_to_track = ms_to_track
    self.tracker_options = tracker_options
    self.output_file = output_file
    self.chipping_rate = chipping_rate
    self.l2c_handover = l2c_handover
    self.show_progress = show_progress
    self.correlator = correlator
    self.stage2_coherent_ms = stage2_coherent_ms
    self.stage2_loop_filter_params = stage2_loop_filter_params
    self.multi = multi
    self.loop_filter_class = loop_filter_class

    if self.ms_to_track:
      self.samples_to_track = self.ms_to_track * sampling_freq / 1e3
      if samples['samples_total'] < self.samples_to_track:
        logger.warning("Samples set too short for requested tracking length (%.4fs)"
                       % (self.ms_to_track * 1e-3))
        self.samples_to_track = samples['samples_total']
    else:
      self.samples_to_track = samples['samples_total']

    # If progressbar is not available, disable show_progress.
    if show_progress and not _progressbar_available:
      show_progress = False
      logger.warning("show_progress = True but progressbar module not found.")

    # Setup our progress bar if we need it
    if show_progress:
      widgets = ['  Tracking ',
                 progressbar.Attribute(['sample', 'samples'],
                                       '(sample: %d/%d)',
                                       '(sample: -/-)'), ' ',
                 progressbar.Percentage(), ' ',
                 progressbar.ETA(), ' ',
                 progressbar.Bar()]
      self.pbar = progressbar.ProgressBar(widgets=widgets,
                                          maxval=samples['samples_total'],
                                          attr={'samples': self.samples['samples_total'],
                                                'sample': 0l})
    else:
      self.pbar = None

    self.tracking_channels = map(self._create_channel, channels)

  def start(self):
    logger.info("Number of CPUs: %d" % (mp.cpu_count()))

    logger.info("Tracking %.4fs of data (%d samples)" %
                (self.samples_to_track / self.sampling_freq,
                 self.samples_to_track))

    logger.info("Tracking starting")
    logger.debug("Tracking PRNs %s" %
                 ([chan.prn + 1 for chan in self.tracking_channels]))

    self.pbar.start()

  def _print_name(self, name):
    print name

  def stop(self):
    if self.pbar:
      self.pbar.finish()

    filenames = map(lambda chan: chan.dump(), self.tracking_channels)

    print "The tracking results were stored into:"
    map(self._print_name, filenames)

    logger.info("Tracking finished")

  def _create_channel(self, acq):
    if not acq:
      return
    parameters = {'acq': acq,
                  'samples': self.samples,
                  'loop_filter_class': self.loop_filter_class,
                  'tracker_options': self.tracker_options,
                  'output_file': self.output_file,
                  'samples_to_track': self.samples_to_track,
                  'sampling_freq': self.sampling_freq,
                  'chipping_rate': self.chipping_rate,
                  'l2c_handover': self.l2c_handover,
                  'show_progress': self.show_progress,
                  'correlator': self.correlator,
                  'stage2_coherent_ms': self.stage2_coherent_ms,
                  'stage2_loop_filter_params': self.stage2_loop_filter_params,
                  'multi': self.multi}
    return _tracking_channel_factory(parameters)

  def run_channels(self, samples):
    self.samples = samples
    tracking_channels = self.tracking_channels

    while tracking_channels and not all(v is None for v in tracking_channels):
      if self.multi and mp.cpu_count() > 1:
        res = pp.parmap(lambda x: self.run(samples),
                        tracking_channels,
                        show_progress=False,
                        func_progress=False)

        handover = map(lambda x: x[0], res)
        tracking_channels = map(lambda x: x[1], res)
      else:
        handover = map(lambda x: x.run(samples), tracking_channels)

      handover = [h for h in handover if h is not None]
      if handover:
        tracking_channels = map(self._create_channel, handover)
        self.tracking_channels += tracking_channels
      else:
        tracking_channels = None

    indexes = map(lambda x: x.get_index(), self.tracking_channels)
    min_index = min(indexes)

    if self.pbar:
      self.pbar.update(min_index, attr={'sample': min_index})

    return min_index


class TrackResults:

  def __init__(self, n_points, prn, signal):
    self.print_start = 1
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
    self.nav_msg = NavMsg()
    self.nav_msg_bit_phase_ref = np.zeros(n_points)
    self.nav_bit_sync = NBSMatchBit() if prn < 32 else NBSSBAS()
    self.tow = np.empty(n_points)
    self.tow[:] = np.NAN
    self.coherent_ms = np.zeros(n_points)
    # self.cnav_msg = swiftnav.cnav_msg.CNavMsg()
    # self.cnav_msg_decoder = swiftnav.cnav_msg.CNavMsgDecoder()
    self.signal = signal
    self.ms_tracked = np.zeros(n_points)

  def dump(self, output_file, size):
    output_filename, output_file_extension = os.path.splitext(output_file)

    # mangle the result file name with the tracked signal name
    filename = output_filename + \
        (".PRN-%d.%s" % (self.prn + 1, self.signal)) +\
        output_file_extension

    if self.print_start:
      mode = 'w'
    else:
      mode = 'a'

    # print "Storing tracking results into file: ", filename

    with open(filename, mode) as f1:
      if self.print_start:
        f1.write("sample_index,ms_tracked,IF,doppler_phase,carr_doppler,"
                 "code_phase, code_freq,"
                 "CN0,E_I,E_Q,P_I,P_Q,L_I,L_Q,"
                 "lock_detect_outp,lock_detect_outo,"
                 "lock_detect_pcount1,lock_detect_pcount2,"
                 "lock_detect_lpfi,lock_detect_lpfq,alias_detect_err_hz,"
                 "code_phase_acc\n")
      for i in range(size):
        f1.write("%s," % int(self.absolute_sample[i]))
        f1.write("%s," % self.ms_tracked[i])
        f1.write("%s," % self.IF)
        f1.write("%s," % self.carr_phase[i])
        f1.write("%s," % (self.carr_freq[i] -
                          self.IF))
        f1.write("%s," % self.code_phase[i])
        f1.write("%s," % self.code_freq[i])
        f1.write("%s," % self.cn0[i])
        f1.write("%s," % self.E[i].real)
        f1.write("%s," % self.E[i].imag)
        f1.write("%s," % self.P[i].real)
        f1.write("%s," % self.P[i].imag)
        f1.write("%s," % self.L[i].real)
        f1.write("%s," % self.L[i].imag)
        f1.write("%s," % int(self.lock_detect_outp[i]))
        f1.write("%s," % int(self.lock_detect_outo[i]))
        f1.write("%s," % int(self.lock_detect_pcount1[i]))
        f1.write("%s," % int(self.lock_detect_pcount2[i]))
        f1.write("%s," % self.lock_detect_lpfi[i])
        f1.write("%s," % self.lock_detect_lpfq[i])
        f1.write("%s," % self.alias_detect_err_hz[i])
        f1.write("%s\n" % self.code_phase_acc[i])

    self.print_start = 0

    return filename

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
        if any(np.greater((self.__dict__[k] - other.__dict__[k]), np.ones(len(self.__dict__[k])) * 10e-6)):
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
        if any((self.__dict__[k] - other.__dict__[k]) > 10e-6):
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
    self.nav_msg = NavMsg()

  def update_bit_sync(self, corr, ms):
    self.nav_msg.update(corr, ms)
    self.bit_phase_ref = self.nav_msg.bit_phase_ref
    self.synced = self.bit_phase_ref >= 0


class NBSMatchBit(NavBitSync):

  def __init__(self, thres=25):
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

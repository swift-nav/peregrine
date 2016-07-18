# Copyright (C) 2012,2016 Swift Navigation Inc.
# Contact: Adel Mamin <adel.mamin@exafore.com>
#
# This source is subject to the license found in the file 'LICENSE' which must
# be be distributed together with this source. All other rights reserved.
#
# THIS CODE AND INFORMATION IS PROVIDED "AS IS" WITHOUT WARRANTY OF ANY KIND,
# EITHER EXPRESSED OR IMPLIED, INCLUDING BUT NOT LIMITED TO THE IMPLIED
# WARRANTIES OF MERCHANTABILITY AND/OR FITNESS FOR A PARTICULAR PURPOSE.

import numpy as np
import math
import parallel_processing as pp
import multiprocessing as mp
import cPickle

from swiftnav.track import LockDetector
from swiftnav.track import CN0Estimator
from swiftnav.track import AidedTrackingLoop
from swiftnav.correlate import track_correlate
from swiftnav.nav_msg import NavMsg
from swiftnav.nav_msg import GpsL1CADecodedData
from swiftnav.cnav_msg import CNavMsg
from swiftnav.cnav_msg import CNavMsgDecoder
from swiftnav.signal import signal_from_code_index
from peregrine import defaults
from peregrine import gps_constants
from peregrine import glo_constants
from peregrine import alias_detector
from peregrine.acquisition import AcquisitionResult
from peregrine.acquisition import GloAcquisitionResult
from peregrine.include.generateCAcode import caCodes
from peregrine.include.generateL2CMcode import L2CMCodes
from peregrine.include.generateGLOcode import GLOCode
from peregrine.tracking_file_utils import createTrackingOutputFileNames
from peregrine.cn0 import CN0_Est_MM

import logging
import sys

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
  """
  Tracking channel factory.
  The right tracking channel is created depending
  on the type of signal provided in acquisition
  results.

  Parameters
  ----------
  parameters : dictionary
    Combines all relevant tracking channel parameters
    needed to create a tracking channel instance.

  Returns
  -------
  out : TrackingChannel
    Tracking channel instance

  """

  if parameters['acq'].signal == gps_constants.L1CA:
    return TrackingChannelL1CA(parameters)
  if parameters['acq'].signal == gps_constants.L2C:
    return TrackingChannelL2C(parameters)
  if parameters['acq'].signal == glo_constants.GLO_L1:
    return TrackingChannelGLOL1(parameters)


class TrackingChannel(object):
  """
  Tracking channel base class.
  Specialized signal tracking channel classes are subclassed from
  this class. See TrackingChannelL1CA or TrackingChannelL2C as
  examples.

  Sub-classes can optionally implement :meth:'_run_preprocess',
  :meth:'_run_postprocess' and :meth:'_get_result' methods.

  The class is designed to support batch processing of sample data.
  This is to help processing of large data sample files without the need
  of loading the whole file into a memory.
  The class instance keeps track of the next sample to be processed
  in the form of an index within the original data file.
  Each sample data batch comes with its starting index within the original
  data file. Given the starting index of the batch and its own index
  of the next sample to be processed, the code computes the offset
  within the batch and starts/continues the tracking procedure from there.

  """

  def __init__(self, params):
    """
    Initialize the parameters, which are common across different
    types of tracking channels.

    Parameters
    ----------
    params : dictionary
      The subset of tracking channel parameters that are deemed
      to be common across different types of tracking channels.


    """
    for (key, value) in params.iteritems():
      setattr(self, key, value)

    self.prn = params['acq'].prn
    self.signal = params['acq'].signal

    self.results_num = 500
    self.stage1 = True

    self.lock_detect = LockDetector(
        k1=self.lock_detect_params["k1"],
        k2=self.lock_detect_params["k2"],
        lp=self.lock_detect_params["lp"],
        lo=self.lock_detect_params["lo"])

    self.cn0_est = CN0_Est_MM(
        bw=1e3 / self.coherent_ms,
        cn0_0=self.cn0_0,
        cutoff_freq=0.1,
        loop_freq=self.loop_filter_params["loop_freq"]
    )

    self.loop_filter = self.loop_filter_class(
        loop_freq=self.loop_filter_params['loop_freq'],
        code_freq=self.code_freq_init,
        code_bw=self.loop_filter_params['code_bw'],
        code_zeta=self.loop_filter_params['code_zeta'],
        code_k=self.loop_filter_params['code_k'],
        carr_to_code=self.loop_filter_params['carr_to_code'],
        carr_freq=self.acq.doppler,
        carr_bw=self.loop_filter_params['carr_bw'],
        carr_zeta=self.loop_filter_params['carr_zeta'],
        carr_k=self.loop_filter_params['carr_k'],
        carr_freq_b1=self.loop_filter_params['carr_freq_b1'],
    )

    self.next_code_freq = self.loop_filter.to_dict()['code_freq']
    self.next_carr_freq = self.loop_filter.to_dict()['carr_freq']

    self.track_result = TrackResults(self.results_num,
                                     self.acq.prn,
                                     self.acq.signal)
    self.code_phase = 0.0
    self.carr_phase = 0.0
    self.samples_per_chip = int(round(self.sampling_freq / self.chipping_rate))
    self.sample_index = params['sample_index']
    self.sample_index += self.acq.sample_index
    self.sample_index += self.acq.code_phase * self.samples_per_chip
    self.sample_index = int(math.floor(self.sample_index))
    self.carr_phase_acc = 0.0
    self.code_phase_acc = 0.0
    self.samples_tracked = 0
    self.i = 0
    self.started = False
    self.lock_detect_outo = 0
    self.lock_detect_outp = 0

    self.pipelining = False    # Flag if pipelining is used
    self.pipelining_k = 0.     # Error prediction coefficient for pipelining
    self.short_n_long = False  # Short/Long cycle simulation
    self.short_step = True    # Short cycle
    if self.tracker_options:
      mode = self.tracker_options['mode']
      if mode == 'pipelining':
        self.pipelining = True
        self.pipelining_k = self.tracker_options['k']
      elif mode == 'short-long-cycles':
        self.short_n_long = True
        self.pipelining = True
        self.pipelining_k = self.tracker_options['k']
      else:
        raise ValueError("Invalid tracker mode %s" % str(mode))

  def dump(self):
    """
    Append intermediate tracking results to a file.

    """
    fn_analysis, fn_results = self.track_result.dump(self.output_file, self.i)
    self.i = 0
    return fn_analysis, fn_results

  def start(self):
    """
    Start tracking channel.
    For the time being only prints an informative log message about
    the initial parameters of the tracking channel.

    """

    if self.started:
      return

    self.started = True

    logger.info("[PRN: %d (%s)] Tracking is started. "
                "IF: %.1f, Doppler: %.1f, code phase: %.1f, "
                "sample index: %d" %
                (self.prn + 1,
                 self.signal,
                 self.IF,
                 self.acq.doppler,
                 self.acq.code_phase,
                 self.acq.sample_index))

  def get_index(self):
    """
    Return index of next sample to be processed by the tracking channel.
    The tracking channel is designed to process the input data samples
    in batches. A single batch is fed to multiple tracking channels.
    To keep track of the order of samples within one tracking channel,
    each channel maintains an index of the next sample to be processed.
    This method is a getter method for the index.

    Returns
    -------
    sample_index: integer
      The next data sample to be processed.

    """
    return self.sample_index

  def _run_preprocess(self):
    """
    Customize the tracking run procedure in a subclass.
    The method can be optionally redefined in a subclass to perform
    a subclass specific actions to happen before correlator runs
    next integration round.

    """
    pass

  def _run_postprocess(self):
    """
    Customize the tracking run procedure in a subclass.
    The method can be optionally redefined in a subclass to perform
    a subclass specific actions to happen after correlator runs
    next integration round.

    """
    pass

  def _get_result(self):
    """
    Customize the tracking run procedure outcome in a subclass.
    The method can be optionally redefined in a subclass to return
    a subclass specific data as a result of the tracking procedure.

    Returns
    -------
    out :
      None is returned by default.

    """
    return None

  def _short_n_long_preprocess(self):
    pass

  def _short_n_long_postprocess(self):
    pass

  def is_pickleable(self):
    """
    Check if object is pickleable.
    The base class instance is always pickleable.
    If a subclass is not pickleable, then it should redefine the method
    and return False.
    The need to know if an object is pickleable or not arises from the fact
    that we try to run the tracking procedure for multiple tracking channels
    on multiple CPU cores, if more than one core is available.
    This is done to speed up the overall processing time. When a tracking
    channel runs on a separate CPU core, it also runs on a separate
    process. When the tracking of the given batch of data is over, the process
    exits and the tracking channel state is returned to the parent process.
    This requires serialization (pickling) of the tracking object state,
    which might not be always trivial. This method essentially defines
    if the tracking channels can be run in a separate processs.
    If the object is not pickleable, then the tracking for the channel is
    done on the same CPU, which runs the parent process. Therefore all
    non-pickleable tracking channels are processed sequentially.

    Returns
    -------
    out : bool
      True if the object is pickleable, False - if not.

    """
    return True

  def run(self, samples):
    """
    Run tracking channel for the given batch of data.
    This method is an entry point for the tracking procedure.
    Subclasses normally will not redefine the method, but instead
    redefine the customization methods '_run_preprocess', '_run_postprocess'
    and '_get_result' to run signal specific tracking operations.

    Parameters
    ----------
    sample : dictionary
      Sample data. Sample data are provided in batches

    Return
    ------
      The return value is determined by '_get_result' customization method,
      which can be redefined in subclasses

    """
    self.samples = samples

    if self.sample_index < samples['sample_index']:
      raise ValueError("Incorrect samples offset")

    sample_index = self.sample_index - samples['sample_index']
    samples_processed = 0
    samples_total = len(samples[self.signal]['samples'])

    estimated_blksize = self.coherent_ms * self.sampling_freq / 1e3

    self.track_result.status = 'T'

    while self.samples_tracked < self.samples_to_track and \
            (sample_index + 2 * estimated_blksize) < samples_total:

      self._run_preprocess()

      if self.pipelining:
        # Pipelining and prediction
        corr_code_freq = self.next_code_freq
        corr_carr_freq = self.next_carr_freq

        self.next_code_freq = self.loop_filter.to_dict()['code_freq']
        self.next_carr_freq = self.loop_filter.to_dict()['carr_freq']

        if self.short_n_long and not self.stage1 and not self.short_step:
          # In case of short/long cycles, the correction applicable for the
          # long cycle is smaller proportionally to the actual cycle size
          pipelining_k = self.pipelining_k / (self.coherent_ms - 1)
        else:
          pipelining_k = self.pipelining_k

        # There is an error between target frequency and actual one. Affect
        # the target frequency according to the computed error
        carr_freq_error = self.next_carr_freq - corr_carr_freq
        self.next_carr_freq += carr_freq_error * pipelining_k

        code_freq_error = self.next_code_freq - corr_code_freq
        self.next_code_freq += code_freq_error * pipelining_k

      else:
        # Immediate correction simulation
        self.next_code_freq = self.loop_filter.to_dict()['code_freq']
        self.next_carr_freq = self.loop_filter.to_dict()['carr_freq']

        corr_code_freq = self.next_code_freq
        corr_carr_freq = self.next_carr_freq

      if self.short_n_long:
        coherent_iter, code_chips_to_integrate = self._short_n_long_preprocess()
      else:
        coherent_iter, code_chips_to_integrate = \
            self.alias_detector.preprocess()
        self.E = self.P = self.L = 0.j

      # Estimated blksize might change as a result of a change of
      # the coherent integration time.
      estimated_blksize = self.coherent_ms * self.sampling_freq / 1e3
      if (sample_index + 2 * estimated_blksize) > samples_total:
        continue

      for _ in range(coherent_iter):

        samples_ = samples[self.signal]['samples'][sample_index:]

        E_, P_, L_, blksize, self.code_phase, self.carr_phase = self.correlator(
            samples_,
            self.code_phase + code_chips_to_integrate,
            corr_code_freq + self.chipping_rate, self.code_phase,
            corr_carr_freq + self.IF, self.carr_phase,
            self.prn_code,
            self.sampling_freq,
            self.signal
        )

        sample_index += blksize
        samples_processed += blksize
        self.carr_phase_acc += corr_carr_freq * blksize / self.sampling_freq
        self.code_phase_acc += corr_code_freq * blksize / self.sampling_freq

        self.E += E_
        self.P += P_
        self.L += L_

        if self.short_n_long:
          continue

        if self.lock_detect_outo:
          code_chips_to_integrate = self.alias_detector.postprocess(P_)
        else:
          self.alias_detector.reinit(self.coherent_ms)

      if self.short_n_long:
        more_integration_needed = self._short_n_long_postprocess()
        if more_integration_needed:
          continue

      err_hz = self.alias_detector.get_err_hz()
      if abs(err_hz) > 0:
        logger.info("[PRN: %d (%s)] False lock detected. "
                    "Error: %.1f Hz. Correcting..." %
                    (self.prn + 1, self.signal, -err_hz))
        self.loop_filter.adjust_freq(err_hz)

      # Update PLL lock detector
      self.lock_detect_outo, \
          self.lock_detect_outp, \
          lock_detect_pcount1, \
          lock_detect_pcount2, \
          lock_detect_lpfi, \
          lock_detect_lpfq = self.lock_detect.update(self.P.real,
                                                     self.P.imag,
                                                     coherent_iter)

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

      self.track_result.lock_detect_outo[self.i] = self.lock_detect_outo
      self.track_result.lock_detect_outp[self.i] = self.lock_detect_outp
      self.track_result.lock_detect_pcount1[self.i] = lock_detect_pcount1
      self.track_result.lock_detect_pcount2[self.i] = lock_detect_pcount2
      self.track_result.lock_detect_lpfi[self.i] = lock_detect_lpfi
      self.track_result.lock_detect_lpfq[self.i] = lock_detect_lpfq

      self.track_result.alias_detect_err_hz[self.i] = err_hz

      self._run_postprocess()

      self.samples_tracked = self.sample_index + samples_processed
      self.track_result.ms_tracked[self.i] = self.samples_tracked * 1e3 / \
          self.sampling_freq

      self.i += 1
      if self.i >= self.results_num:
        self.dump()

    if self.i > 0:
      self.dump()

    self.sample_index += samples_processed

    return self._get_result()


class TrackingChannelL1CA(TrackingChannel):

  """
  L1CA tracking channel.
  """

  def __init__(self, params):
    """
    Initialize L1C/A tracking channel with L1C/A specific data.

    Parameters
    ----------
    params : dictionary
    L1C/A tracking initialization parameters

    """

    # Convert acquisition SNR to C/N0
    cn0_0 = 10 * np.log10(params['acq'].snr)
    cn0_0 += 10 * np.log10(defaults.L1CA_CHANNEL_BANDWIDTH_HZ)

    params['cn0_0'] = cn0_0
    params['coherent_ms'] = 1
    params['IF'] = params['samples'][gps_constants.L1CA]['IF']
    params['prn_code'] = caCodes[params['acq'].prn]
    params['code_freq_init'] = params['acq'].doppler * \
        gps_constants.l1ca_chip_rate / gps_constants.l1
    params['loop_filter_params'] = defaults.l1ca_stage1_loop_filter_params
    params['lock_detect_params'] = defaults.l1ca_lock_detect_params_opt
    params['chipping_rate'] = gps_constants.l1ca_chip_rate
    params['sample_index'] = params['samples']['sample_index']
    params['alias_detector'] = \
        alias_detector.AliasDetectorL1CA(params['coherent_ms'])

    TrackingChannel.__init__(self, params)

    self.nav_msg = NavMsg()
    self.nav_bit_sync = NBSMatchBit() if self.prn < 32 else NBSSBAS()
    self.l2c_handover_acq = None
    self.l2c_handover_done = False

  def _run_preprocess(self):
    """
    Run L1C/A tracking loop preprocessor operation.
    It runs before every coherent integration round.

    """

    # For L1 C/A there are coherent and non-coherent tracking options.
    if self.stage1 and \
       self.stage2_coherent_ms and \
       self.nav_bit_sync.bit_phase == self.nav_bit_sync.bit_phase_ref:

      logger.info("[PRN: %d (%s)] switching to stage2, coherent_ms=%d" %
                  (self.prn + 1, self.signal, self.stage2_coherent_ms))

      self.stage1 = False
      self.coherent_ms = self.stage2_coherent_ms

      self.alias_detector.reinit(self.coherent_ms)

      self.loop_filter.retune(**self.stage2_loop_filter_params)
      self.lock_detect.reinit(
          k1=self.lock_detect_params["k1"] * self.coherent_ms,
          k2=self.lock_detect_params["k2"],
          lp=self.lock_detect_params["lp"],
          lo=self.lock_detect_params["lo"])
      self.cn0_est = CN0_Est_MM(bw=1e3 / self.stage2_coherent_ms,
                                  cn0_0=self.track_result.cn0[self.i - 1],
                                  cutoff_freq=10,
                                  loop_freq=1e3 / self.stage2_coherent_ms)

    self.coherent_iter = self.coherent_ms

  def _get_result(self):
    """
    Get L1C/A tracking results.
    The possible outcome of L1C/A tracking operation is
    the L1C/A handover to L2C in the form of an AcquisitionResult object.

    Returns
    -------
    out : AcquisitionResult
      L2C acquisition result or None

    """

    if self.l2c_handover_acq and not self.l2c_handover_done:
      self.l2c_handover_done = True
      return self.l2c_handover_acq
    return None

  def _short_n_long_preprocess(self):
    if self.stage1:
      self.E = self.P = self.L = 0.j
    else:
      # When simulating short and long cycles, short step resets EPL
      # registers, and long one adds up to them
      if self.short_step:
        self.E = self.P = self.L = 0.j
        self.coherent_iter = 1
      else:
        self.coherent_iter = self.coherent_ms - 1

    self.code_chips_to_integrate = gps_constants.chips_per_code

    return self.coherent_iter, self.code_chips_to_integrate

  def _short_n_long_postprocess(self):
    more_integration_needed = False
    if not self.stage1:
      if self.short_step:
        # In case of short step - go to next integration period
        self.short_step = False
        more_integration_needed = True
      else:
        # Next step is short cycle
        self.short_step = True
    return more_integration_needed

  def _run_postprocess(self):
    """
    Run L1C/A coherent integration postprocessing.
    Runs navigation bit sync decoding operation and
    L1C/A to L2C handover.
    """

    sync, bit = self.nav_bit_sync.update(np.real(self.P), self.coherent_ms)
    if sync:
      tow = self.nav_msg.update(bit)
      if tow >= 0:
        logger.info("[PRN: %d (%s)] ToW %d" %
                    (self.prn + 1, self.signal, tow))
      if self.nav_msg.subframe_ready():
        data = GpsL1CADecodedData()
        sid = signal_from_code_index(0, self.prn)
        res = self.nav_msg.process_subframe(sid, data)
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
        gps_constants.L2C in self.samples and \
       'samples' in self.samples[gps_constants.L2C] and sync:
      chan_snr = self.track_result.cn0[self.i]
      chan_snr -= 10 * np.log10(defaults.L1CA_CHANNEL_BANDWIDTH_HZ)
      chan_snr = np.power(10, chan_snr / 10)
      l2c_doppler = self.loop_filter.to_dict(
      )['carr_freq'] * gps_constants.l2 / gps_constants.l1
      self.l2c_handover_acq = \
          AcquisitionResult(self.prn,
                            self.samples[gps_constants.L2C][
                                'IF'] + l2c_doppler,
                            l2c_doppler,  # carrier doppler
                            self.track_result.code_phase[self.i],
                            chan_snr,
                            'A',
                            gps_constants.L2C,
                            self.track_result.absolute_sample[self.i])


class TrackingChannelL2C(TrackingChannel):
  """
  L2C tracking channel.
  """

  def __init__(self, params):
    """
    Initialize L2C tracking channel with L2C specific data.

    Parameters
    ----------
    params : dictionary
    L2C tracking initialization parameters

    """
    # Convert acquisition SNR to C/N0
    cn0_0 = 10 * np.log10(params['acq'].snr)
    cn0_0 += 10 * np.log10(defaults.L2C_CHANNEL_BANDWIDTH_HZ)
    params['cn0_0'] = cn0_0
    params['coherent_ms'] = defaults.l2c_coherent_integration_time_ms
    params['coherent_iter'] = 1
    params['loop_filter_params'] = defaults.l2c_loop_filter_params
    params['lock_detect_params'] = defaults.l2c_lock_detect_params_20ms
    params['IF'] = params['samples'][gps_constants.L2C]['IF']
    params['prn_code'] = L2CMCodes[params['acq'].prn]
    params['code_freq_init'] = params['acq'].doppler * \
        gps_constants.l2c_chip_rate / gps_constants.l2
    params['chipping_rate'] = gps_constants.l2c_chip_rate
    params['sample_index'] = 0
    params['alias_detector'] = \
        alias_detector.AliasDetectorL2C(params['coherent_ms'])

    TrackingChannel.__init__(self, params)

    self.cnav_msg = CNavMsg()
    self.cnav_msg_decoder = CNavMsgDecoder()

  def is_pickleable(self):
    """
    L2C tracking channel object is not pickleable due to complexity
    of serializing cnav_msg_decoder Cython object.

    out : bool
       False - the L2C tracking object is not pickleable
    """
    return False

  def _short_n_long_preprocess(self):
    # When simulating short and long cycles, short step resets EPL
    # registers, and long one adds up to them
    if self.short_step:
      self.E = self.P = self.L = 0.j
      # L2C CM code is only half of the PRN code length.
      # The other half is CL code. Thus multiply by 2.
      self.code_chips_to_integrate = \
          int(2 * defaults.l2c_short_step_chips)
    else:
      # L2C CM code is only half of the PRN code length.
      # The other half is CL code. Thus multiply by 2.
      self.code_chips_to_integrate = \
          2 * gps_constants.l2_cm_chips_per_code - \
          self.code_chips_to_integrate
    code_chips_to_integrate = self.code_chips_to_integrate

    return self.coherent_iter, code_chips_to_integrate

  def _short_n_long_postprocess(self):
    more_integration_needed = False
    if self.short_step:
      self.short_step = False
      more_integration_needed = True
    else:
      self.short_step = True

    return more_integration_needed

  def _run_postprocess(self):
    """
    Run L2C coherent integration postprocessing.
    Runs navigation bit sync decoding operation.

    """

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


class TrackingChannelGLOL1(TrackingChannel):
  """
  GLO L1 tracking channel.
  """

  def __init__(self, params):
    """
    Initialize GLO L1 tracking channel with GLO L1 specific data.

    Parameters
    ----------
    params : dictionary
    GLO L1 tracking initialization parameters

    """
    # Convert acquisition SNR to C/N0
    cn0_0 = 10 * np.log10(params['acq'].snr)
    cn0_0 += 10 * np.log10(defaults.GLOL1_CHANNEL_BANDWIDTH_HZ)
    params['cn0_0'] = cn0_0
    params['coherent_ms'] = 1
    params['coherent_iter'] = 1
    params['loop_filter_params'] = defaults.l1ca_stage1_loop_filter_params
    params['lock_detect_params'] = defaults.l1ca_lock_detect_params_opt
    params['IF'] = params['samples'][glo_constants.GLO_L1]['IF']
    params['prn_code'] = GLOCode
    params['code_freq_init'] = params['acq'].doppler * \
        glo_constants.glo_chip_rate / glo_constants.glo_l1
    params['chipping_rate'] = glo_constants.glo_chip_rate
    params['sample_index'] = 0
    params['alias_detector'] = \
        alias_detector.AliasDetectorGLO(params['coherent_ms'])

    TrackingChannel.__init__(self, params)

    self.glol2_handover_acq = None
    self.glol2_handover_done = False

    # TODO add nav msg decoder (GLO L1)

  def is_pickleable(self):
    """
    GLO L1 tracking channel object is not pickleable due to complexity
    of serializing cnav_msg_decoder Cython object.

    out : bool
       False - the GLO L1 tracking object is not pickleable
    """
    return False

  def _get_result(self):
    """
    Get GLO L1 tracking results.
    The possible outcome of GLO L1 tracking operation is
    the GLO L1 handover to GLO L2 in the form of an GloAcquisitionResult object.

    Returns
    -------
    out : AcquisitionResult
      GLO L2 acquisition result or None

    """

    if self.glol2_handover_acq and not self.glol2_handover_done:
      self.glol2_handover_done = True
      return self.glol2_handover_acq
    return None

  def _run_preprocess(self):
    """
    Run GLONASS tracking loop preprocessor operation.
    It runs before every coherent integration round.

    """

    self.coherent_iter = self.coherent_ms

  def _short_n_long_preprocess(self):
    if self.stage1:
      self.E = self.P = self.L = 0.j
    else:
      # When simulating short and long cycles, short step resets EPL
      # registers, and long one adds up to them
      if self.short_step:
        self.E = self.P = self.L = 0.j
        self.coherent_iter = 1
      else:
        self.coherent_iter = self.coherent_ms - 1

    self.code_chips_to_integrate = glo_constants.glo_code_len

    return self.coherent_iter, self.code_chips_to_integrate

  def _short_n_long_postprocess(self):
    more_integration_needed = False
    if not self.stage1:
      if self.short_step:
        # In case of short step - go to next integration period
        self.short_step = False
        more_integration_needed = True
      else:
        # Next step is short cycle
        self.short_step = True
    return more_integration_needed

  def _run_postprocess(self):
    """
    Run GLO L1 coherent integration postprocessing.
    Runs navigation bit sync decoding operation and
    GLO L1 to GLO L2 handover.
    """

    # Handover to L2C if possible
    if self.glol2_handover and not self.glol2_handover_acq and \
        glo_constants.GLO_L2 in  self.samples and \
       'samples' in self.samples[glo_constants.GLO_L2]:  # and sync:
      chan_snr = self.track_result.cn0[self.i]
      # chan_snr -= 10 * np.log10(defaults.GLOL1_CHANNEL_BANDWIDTH_HZ)
      chan_snr = np.power(10, chan_snr / 10)
      glol2_doppler = self.loop_filter.to_dict()['carr_freq'] * \
          glo_constants.glo_l2 / glo_constants.glo_l1
      self.glol2_handover_acq = \
          GloAcquisitionResult(self.prn,
                               self.samples[glo_constants.GLO_L2]['IF'] +
                               glol2_doppler,
                               glol2_doppler,  # carrier doppler
                               self.track_result.code_phase[
                                   self.i],
                               chan_snr,
                               'A',
                               glo_constants.GLO_L2,
                               self.track_result.absolute_sample[self.i])


class Tracker(object):
  """
  Tracker class.
  Encapsulates and manages the processing of tracking channels.

  """

  def __init__(self,
               samples,
               channels,
               ms_to_track,
               sampling_freq,
               check_l2c_mask=False,
               l2c_handover=True,
               glol2_handover=True,
               progress_bar_output='none',
               loop_filter_class=AidedTrackingLoop,
               correlator=track_correlate,
               stage2_coherent_ms=None,
               stage2_loop_filter_params=None,
               multi=False,
               tracker_options=None,
               output_file=None):
    """
    Set up tracking environment.
    1. Check if multy CPU tracking is possible
    2. Set up progress bar
    3. Create tracking channels based on the provided acquistion results

    Parameters
    ----------
    samples : dictionary
      Samples data for all one or more data channels
    channels : list
      A list of acquisition results
    ms_to_track : float
      How many milliseconds to track [ms].
      If set to '-1', then use all samples.
    sampling_freq : float
      Data sampling frequency [Hz]
    l2c_handover : bool
      Instructs if L1C/A to L2C handover is to be done
    progress_bar_output : string
      Where the progress bar updates are forwarded.
    loop_filter_class : class
      The type of the loop filter class to be used by tracker channels
    correlator : class
      The correlator class to be used by tracker channels
    stage2_coherent_ms : dictionary
      Stage 2 coherent integration parameters set.
    stage2_loop_filter_params : dictionary
      Stage 2 loop filter parameters set.
    multi : bool
      Enable multi core CPU utilization
    tracker_options : dictionary
      Enable piplining or short/long cycles tracking to simulate HW
    output_file : string
      The name of the output file, where the tracking results are stored.
      The actual file name is a mangled version of this file name and
      reflects the signal name and PRN number for which the tracking results
      are generated.

    """

    print "loop_filter_class = ", loop_filter_class
    self.samples = samples
    self.sampling_freq = sampling_freq
    self.ms_to_track = ms_to_track
    self.tracker_options = tracker_options
    self.output_file = output_file
    self.l2c_handover = l2c_handover
    self.glol2_handover = glol2_handover
    self.check_l2c_mask = check_l2c_mask
    self.correlator = correlator
    self.stage2_coherent_ms = stage2_coherent_ms
    self.stage2_loop_filter_params = stage2_loop_filter_params

    if mp.cpu_count() > 1:
      self.multi = multi
    else:
      self.multi = False

    self.loop_filter_class = loop_filter_class

    if self.ms_to_track >= 0:
      self.samples_to_track = self.ms_to_track * sampling_freq / 1e3
      if samples['samples_total'] < self.samples_to_track:
        logger.warning(
            "Samples set too short for requested tracking length (%.4fs)"
            % (self.ms_to_track * 1e-3))
        self.samples_to_track = samples['samples_total']
    else:
      self.samples_to_track = samples['samples_total']

    if progress_bar_output == 'stdout':
      self.show_progress = True
      progress_fd = sys.stdout
    elif progress_bar_output == 'stderr':
      self.show_progress = True
      progress_fd = sys.stderr
    else:
      self.show_progress = False
      progress_fd = -1

    # If progressbar is not available, disable show_progress.
    if self.show_progress and not _progressbar_available:
      self.show_progress = False
      logger.warning("show_progress = True but progressbar module not found.")

    self.init_sample_index = samples['sample_index']
    # Setup our progress bar if we need it
    if self.show_progress:
      widgets = ['  Tracking ',
                 progressbar.Attribute(['sample', 'samples'],
                                       '(sample: %d/%d)',
                                       '(sample: -/-)'), ' ',
                 progressbar.Percentage(), ' ',
                 progressbar.ETA(), ' ',
                 progressbar.Bar()]
      self.pbar = progressbar.ProgressBar(
          widgets=widgets,
          maxval=samples['samples_total'],
          attr={'samples': self.samples['samples_total'],
                'sample': 0l},
          fd=progress_fd)
    else:
      self.pbar = None

    self.tracking_channels = map(self._create_channel, channels)

  def start(self):
    """
    Start tracking operation for all created tracking channels.
    Print relevant log messages, start progress bar.

    """
    logger.info("Number of CPUs: %d" % (mp.cpu_count()))

    logger.info("Tracking %.4fs of data (%d samples). "
                "Skipped %0.4fms (%d samples)" %
                (self.samples_to_track / self.sampling_freq,
                 self.samples_to_track,
                 1e3 * self.init_sample_index / self.sampling_freq,
                 self.init_sample_index))

    logger.info("Tracking starting")
    logger.debug("Tracking PRNs %s" %
                 ([chan.prn + 1 for chan in self.tracking_channels]))

    if self.pbar:
      self.pbar.start()

  def stop(self):
    """
    Stop tracking operation of all tracking channels.
    1. Stop progress bar.
    2. Complete logging tracking results for all tracking channels.

    Return
    ------
    out : list
      A list of file names - one file name for one tracking channel.
      Each file contains pickled TrackingResults object

    """

    if self.pbar:
      self.pbar.finish()
    res = map(lambda chan: chan.track_result.makeOutputFileNames(
        chan.output_file),
        self.tracking_channels)

    fn_analysis = map(lambda x: x[0], res)
    fn_results = map(lambda x: x[1], res)

    def _print_name(name):
      print name

    print "The tracking results were stored into:"
    map(_print_name, fn_analysis)

    logger.info("Tracking finished")

    return fn_results

  def _create_channel(self, acq):
    """
    Create a new channel for the given acquisition result.

    Parameters
    ----------
    acq : AcquisitionResults
      Acquisition results class object

    Return
    ------
    out : TrackingChannel
      The new tracking channel class object

    """
    if not acq:
      return

    l2c_handover = self.l2c_handover

    if self.check_l2c_mask and (gps_constants.L2C_CAPB & (0x1 << acq.prn) == 0):
      l2c_handover = False

    parameters = {'acq': acq,
                  'samples': self.samples,
                  'loop_filter_class': self.loop_filter_class,
                  'tracker_options': self.tracker_options,
                  'output_file': self.output_file,
                  'samples_to_track': self.samples_to_track,
                  'sampling_freq': self.sampling_freq,
                  'l2c_handover': l2c_handover,
                  'glol2_handover': self.glol2_handover,
                  'show_progress': self.show_progress,
                  'correlator': self.correlator,
                  'stage2_coherent_ms': self.stage2_coherent_ms,
                  'stage2_loop_filter_params': self.stage2_loop_filter_params,
                  'multi': self.multi}
    return _tracking_channel_factory(parameters)

  def run_channels(self, samples):
    """
    Run tracking channels.

    Parameters
    ----------
    samples : dictionary
      Sample data together with description data

    Return
    ------
    out : int
      The smallest data sample index across all tracking channels.
      The index tells the offset, from which the next sample data batch
      is to be read from the input data file.

    """
    channels = self.tracking_channels
    self.tracking_channels = []

    def _run_parallel(i, samples):
      """
      Run a tracking channel.
      Expected to be run in a child process.

      Parameters
      ----------
      i : int
        Channel index within self.parallel_channels list

      Return
      out : TrackingChannel, AcquisitionResult
        Tracking channel state and handover result

      """
      handover = self.parallel_channels[i].run(samples)
      return self.parallel_channels[i], handover

    while channels and not all(v is None for v in channels):

      if self.multi:
        self.parallel_channels = filter(lambda x: x.is_pickleable(), channels)
      else:
        self.parallel_channels = []

      serial_channels = list(set(channels) - set(self.parallel_channels))
      channels = []
      handover = []

      if self.parallel_channels:
        res = pp.parmap(lambda i: _run_parallel(i, samples),
                        range(len(self.parallel_channels)),
                        nprocs=len(self.parallel_channels),
                        show_progress=False,
                        func_progress=False)

        channels = map(lambda x: x[0], res)
        handover += map(lambda x: x[1], res)

      if serial_channels:
        handover += map(lambda x: x.run(samples), serial_channels)

      self.tracking_channels += channels + serial_channels
      handover = [h for h in handover if h is not None]
      if handover:
        channels = map(self._create_channel, handover)
      else:
        channels = None

    indicies = map(lambda x: x.get_index(), self.tracking_channels)
    min_index = min(indicies)

    if self.pbar:
      self.pbar.update(min_index - self.init_sample_index,
                       attr={'sample': min_index})

    return min_index


class TrackResults:
  """
  Tracking results.
  The class is designed to support accumulation of tracking
  result up to a certain limit. Once the limit is reached
  'dump' method is expected to be called to store the accumulated
  tracking results to the file system.

  """

  def __init__(self, n_points, prn, signal):
    """
    Init tracking results.
    Paremeters
    ----------
    n_points : int
      How many tracking results can be accumulated until they are
      stored into the file system
    prn : int
      PRN number, for which the tracking results object is created
    signal : string
      Signal for which the tracking results object is created.

    """
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
    self.signal = signal
    self.ms_tracked = np.zeros(n_points)

  def dump(self, output_file, size):
    """
    Store tracking result to file system.
    The tracking results are stored in two different formats:
    CSV (test) and Python pickle (binary) format.

    Parameters
    ----------
    output_file : string
      The name of the output file. The actual file name is a mangled
      version of this name and includes the PRN and signal type.
    size : int
      How many entries of the tracking results are to be stored into the file.

    """
    # mangle the output file names with the tracked signal name
    fn_analysis, fn_results = self.makeOutputFileNames(output_file)

    if self.print_start:
      mode = 'w'
    else:
      mode = 'a'

    # saving tracking results for navigation stage
    with open(fn_results, mode) as f1:
      if size != 500:
        self.resize(size)
      cPickle.dump(self, f1, protocol=cPickle.HIGHEST_PROTOCOL)
      if size != 500:
        self.resize(500)

    with open(fn_analysis, mode) as f1:
      if self.print_start:
        f1.write(
            "sample_index,ms_tracked,coherent_ms,IF,doppler_phase,carr_doppler,"
            "code_phase,code_freq,"
            "CN0,E_I,E_Q,P_I,P_Q,L_I,L_Q,"
            "lock_detect_outp,lock_detect_outo,"
            "lock_detect_pcount1,lock_detect_pcount2,"
            "lock_detect_lpfi,lock_detect_lpfq,alias_detect_err_hz,"
            "code_phase_acc\n")
      for i in range(size):
        f1.write("%s," % int(self.absolute_sample[i]))
        f1.write("%s," % self.ms_tracked[i])
        f1.write("%s," % self.coherent_ms[i])
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
    return fn_analysis, fn_results

  def makeOutputFileNames(self, outputFileName):
    # mangle the output file names with the tracked signal name
    prn = self.prn
    if self.signal == gps_constants.L1CA or self.signal == gps_constants.L2C:
      prn += 1
    fn_analysis, fn_results = createTrackingOutputFileNames(outputFileName,
                                                            prn,
                                                            self.signal)
    return fn_analysis, fn_results

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
        if any(np.greater((self.__dict__[k] - other.__dict__[k]),
                          np.ones(len(self.__dict__[k])) * 10e-6)):
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

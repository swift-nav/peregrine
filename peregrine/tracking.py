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
import scipy.constants as constants
import math
import parallel_processing as pp
import multiprocessing as mp
import cPickle

from peregrine import lock_detect
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
from peregrine.cn0 import CN0_Est_MM, CN0_Est_BL

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


def get_fsm_states(fsm_states, ms, short_n_long, bit_sync):
  """
  Tracking loop FSM operation table getter.
  The right FSM operation table is chosen based on the
  set of input parameters.

  Parameters
  ----------
  fsm_states : dictionary
    Contains FSM operation tables for different modes
  ms : integer
    The integration time [ms]
  short_n_long : Boolean
    FPGA operation simulation flag. True - the simulation
    is requested.
  bit_sync : Boolean
    Tells if bit sync is acquired.

  Returns
  -------
  out : dictionary
    The relevant tracking loop FSM operation table

  """

  if ms == 1:
    ms = '1ms'
  elif ms == 2:
    ms = '2ms'
  elif ms == 4:
    ms = '4ms'
  elif ms == 5:
    ms = '5ms'
  elif ms == 10:
    ms = '10ms'
  elif ms == 20:
    ms = '20ms'
  elif ms == 40:
    ms = '40ms'
  elif ms == 80:
    ms = '80ms'
  else:
    raise ValueError("Not implemented!")

  if short_n_long:
    mode = 'short_n_long'
  else:
    mode = 'ideal'

  if bit_sync:
    bit_sync_status = 'bit_sync'
  else:
    bit_sync_status = 'no_bit_sync'

  return fsm_states[ms][bit_sync_status][mode]


def get_lock_detector(cur_bw, lock_detect_set):
  """
  Selects the relevant lock detector parameter set.
  The selection is done based on the current PLL bandwidth.

  Parameters
  ----------
  cur_bw : float
    The current PLL bandwidth
  lock_detect_set : tuple
    The combination of PLL bandwidth and its lock detector
    parameters set

  Returns
  -------
  out : dictionary
    The relevant lock detector parameters set

  """

  for bw, params in lock_detect_set:
    if cur_bw < bw:
      continue
    return params


class TrackingChannel(object):
  """
  Tracking channel base class.
  Specialized signal tracking channel classes are subclassed from
  this class. See TrackingChannelL1CA or TrackingChannelL2C as
  examples.

  Sub-classes can optionally implement :meth:'_run_track_profile_selection',
  :meth:'_run_nav_data_decoding' and :meth:'_get_result' methods.

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

    self.coherent_ms_index = 0
    self.fll_bw_index = 0
    self.pll_bw_index = 0
    coherent_ms = self.track_params['coherent_ms'][self.coherent_ms_index]
    fll_bw = self.track_params['fll_bw'][self.fll_bw_index]
    pll_bw = self.track_params['pll_bw'][self.pll_bw_index]

    loop_filter_params = self.loop_filter_params_template
    carr_params = loop_filter_params['carr_params']
    loop_filter_params['carr_params'] = (pll_bw,
                                         carr_params[1],
                                         carr_params[2])
    loop_filter_params['loop_freq'] = 1000 / coherent_ms
    loop_filter_params['carr_freq_b1'] = fll_bw

    self.track_profile = {'loop_filter_params': loop_filter_params,
                          'coherent_ms': coherent_ms,
                          'iq_ratio': 0}

    self.track_candidates = []
    self.stabilization_time = defaults.tracking_loop_stabilization_time_ms
    self.coherent_ms = coherent_ms
    self.alias_detector = alias_detector.AliasDetector()

    self.short_n_long = False
    if params['tracker_options']:
      mode = params['tracker_options']['mode']
      if mode == 'short-long-cycles':
        self.short_n_long = True

    self.bit_sync_prev = self.bit_sync

    self.fsm_index = 0
    self.fsm_states = get_fsm_states(self.fsm_states_all,
                                     ms=self.coherent_ms,
                                     short_n_long=self.short_n_long,
                                     bit_sync=self.bit_sync)

    self.lock_detect = lock_detect.LockDetector(
        k1=self.lock_detect_params["k1"],
        k2=self.lock_detect_params["k2"],
        lp=self.lock_detect_params["lp"],
        lo=self.lock_detect_params["lo"])

    code_params = loop_filter_params['code_params']
    carr_params = loop_filter_params['carr_params']
    pll_bw = carr_params[0]

    lock_detect_params_fast = get_lock_detector(pll_bw,
                                                defaults.lock_detect_params_fast)

    self.lock_detect_fast = lock_detect.LockDetector(
        k1=lock_detect_params_fast["k1"],
        k2=lock_detect_params_fast["k2"],
        lp=lock_detect_params_fast["lp"],
        lo=lock_detect_params_fast["lo"])

    self.lock_detect_slow = lock_detect.LockDetector(
        k1=defaults.lock_detect_params_slow["k1"],
        k2=defaults.lock_detect_params_slow["k2"],
        lp=defaults.lock_detect_params_slow["lp"],
        lo=defaults.lock_detect_params_slow["lo"])

    self.cn0_est = CN0_Est_MM(
        bw=1e3 / self.coherent_ms,
        cn0_0=self.cn0_0,
        cutoff_freq=0.1,
        loop_freq=loop_filter_params["loop_freq"]
    )

    self.loop_filter = self.loop_filter_class(
        loop_freq=loop_filter_params['loop_freq'],
        code_freq=0,
        code_bw=code_params[0],  # code_bw'
        code_zeta=code_params[1],  # code_zeta
        code_k=code_params[2],  # code_k
        carr_to_code=loop_filter_params['carr_to_code'],
        carr_freq=self.acq.doppler * 2 * np.pi,
        carr_bw=carr_params[0],  # carr_bw,
        carr_zeta=carr_params[1],  # carr_zeta
        carr_k=carr_params[2],  # carr_k
        carr_freq_b1=loop_filter_params['carr_freq_b1'],
    )

    self.code_freq_1 = self.code_freq_2 = self.corr_code_freq = \
        params['code_freq_init']

    self.carr_freq_1 = self.carr_freq_2 = self.corr_carr_freq = \
        self.acq.doppler

    self.track_result = TrackResults(self.results_num,
                                     self.acq.prn,
                                     self.acq.signal)
    self.track_profile_timer_ms = 0
    self.acc_timer_ms = 0
    self.bit_sync_timer_ms = 0
    self.acc_detected = False
    self.code_phase = 0.0
    self.carr_phase = 0.0
    self.lock_detect_outp_prev = False
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
    self.E = self.P = self.L = 0.j
    self.acc_g = 0

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

  def _set_track_profile(self):
    """
    Set the current track profile.
    The current track profile determines the PLL BW, FLL BW and
    the coherent integration time.

    """

    coherent_ms = self.track_params['coherent_ms'][self.coherent_ms_index]
    fll_bw = self.track_params['fll_bw'][self.fll_bw_index]
    pll_bw = self.track_params['pll_bw'][self.pll_bw_index]

    loop_filter_params = self.loop_filter_params_template
    carr_params = loop_filter_params['carr_params']
    loop_filter_params['carr_params'] = (pll_bw,
                                         carr_params[1],
                                         carr_params[2])
    loop_filter_params['loop_freq'] = 1000 / coherent_ms
    loop_filter_params['carr_freq_b1'] = fll_bw

    self.track_profile = {'loop_filter_params': loop_filter_params,
                          'coherent_ms': coherent_ms,
                          'iq_ratio': 0}

    self.coherent_ms = coherent_ms

    # logger.info("[PRN: %d (%s)] coherent_ms=%d and PLL bw=%f FLL bw=%f" %
    #             (self.prn + 1, self.signal, self.coherent_ms, pll_bw, fll_bw))

    lock_detect_params_fast = get_lock_detector(pll_bw,
                                                defaults.lock_detect_params_fast)

    self.lock_detect_fast.reinit(k1=lock_detect_params_fast["k1"],
                                 k2=lock_detect_params_fast["k2"],
                                 lp=lock_detect_params_fast["lp"],
                                 lo=lock_detect_params_fast["lo"])

    self.loop_filter.retune(**loop_filter_params)

    self.cn0_est = CN0_Est_MM(bw=1e3 / self.coherent_ms,
                              cn0_0=self.track_result.cn0[self.i - 1],
                              cutoff_freq=10,
                              loop_freq=1e3 / self.coherent_ms)

    self.fsm_states = get_fsm_states(self.fsm_states_all,
                                     ms=self.coherent_ms,
                                     short_n_long=self.short_n_long,
                                     bit_sync=self.bit_sync)
    self.fsm_index = 0
    self.track_profile_timer_ms = 0

  def _make_track_candidates(self):
    """
    Create a list of track profile candidates.
    The list content depends on the current track profile.
    We are in the recovery stage, when this function is called.
    See more details at
    https://swiftnav.hackpad.com/High-sensitivity-tracking-FLL-PLL-profile-switching-design-HDpuFC1BygA

    """

    fll_bw_index = self.fll_bw_index
    # we try to minimize FLL BW first
    if fll_bw_index == len(self.track_params['fll_bw']) - 1:
      # FLL is already mith minimum BW
      coherent_ms_index = self.coherent_ms_index
      if coherent_ms_index < len(self.track_params['coherent_ms']) - 1:
        coherent_ms_index += 1
        candidate = {'fll_bw_index': self.fll_bw_index,
                     'pll_bw_index': self.pll_bw_index,
                     'coherent_ms_index': coherent_ms_index}
        self.track_candidates.append(candidate)

      pll_bw_index = self.pll_bw_index
      if pll_bw_index < len(self.track_params['pll_bw']) - 1:
        pll_bw_index += 1
        candidate = {'fll_bw_index': self.fll_bw_index,
                     'pll_bw_index': pll_bw_index,
                     'coherent_ms_index': self.coherent_ms_index}
        self.track_candidates.append(candidate)
    else:
      fll_bw_index += 1
      candidate = {'fll_bw_index': fll_bw_index,
                   'pll_bw_index': self.pll_bw_index,
                   'coherent_ms_index': self.coherent_ms_index}
      self.track_candidates.append(candidate)

  def _filter_track_candidates(self):
    """
    Filter the track candidate list.
    The track candidate list is created by _make_track_candidate()
    function.

    Returns
    -------
    res: list
      The filtered track profiles candidates list
    """

    res = []
    for candidate in self.track_candidates:
      pll_bw_index = candidate['pll_bw_index']
      pll_bw = self.track_params['pll_bw'][pll_bw_index]

      coherent_ms_index = candidate['coherent_ms_index']
      coherent_ms = self.track_params['coherent_ms'][coherent_ms_index]

      bw_time = pll_bw * coherent_ms * 1e-3

      if pll_bw < 5:
        continue

      if coherent_ms == 1:
        if 30 <= pll_bw:
          pass
        else:
          continue

      elif coherent_ms == 2:
        if 12 <= pll_bw and pll_bw <= 30:
          pass
        else:
          continue

      elif coherent_ms == 4:
        if 10 <= pll_bw and pll_bw <= 12:
          pass
        else:
          continue

      elif coherent_ms == 5:
        if 5 <= pll_bw and pll_bw <= 10:
          pass
        else:
          continue

      elif bw_time > 0.04:
        if self.acc_detected:
          if coherent_ms <= 10 and pll_bw <= 5:
            pass
          else:
            continue
        elif pll_bw == 5:
          pass
        else:
          continue

      res.append(candidate)

    return res

  def _run_track_profile_selection(self):
    """
    Runs tracking profile selection based on the
    availability of bit sync, fast and normal locks.

    """

    if self.bit_sync and not self.bit_sync_prev:
      # we just got bit sync
      self.bit_sync_timer_ms = 0
      self.bit_sync_prev = self.bit_sync

    if self.lock_detect_outp:

      if not self.lock_detect_fast_outp:
        # we lost fast lock detector
        if self.acc_detected:
          # and we are facing dynamics
          if self.fll_bw_index == 0 and \
             self.pll_bw_index == 0 and \
             self.coherent_ms_index == 0:
            return
          self.fll_bw_index = 0
          self.pll_bw_index = 0
          self.coherent_ms_index = 0
        else:
          # we are in static scenario - just add FLL
          if self.fll_bw_index == 0:
            return
          self.fll_bw_index = 0

        self._set_track_profile()
        return

      track_settled = self.track_profile_timer_ms >= self.stabilization_time
      if not track_settled:
        return

      # Detect dynamics
      # do not assess dynamics in FLL mode as
      # the PLL phase acceleration indicator looks to be scrued
      fll_bw = self.track_params['fll_bw'][self.fll_bw_index]
      if fll_bw == 0:
        acc = self.loop_filter.to_dict()['phase_acc'] / (2 * np.pi)
        self.acc_g = acc * constants.c / (self.carrier_freq * constants.g)

        if acc > 30:  # [hz/sec]
          self.acc_timer_ms = 0
          self.acc_detected = True

      if self.acc_timer_ms > 2000:
        # clear acceleration flag as it is too old
        self.acc_detected = False

      final_profile = \
          self.fll_bw_index == len(self.track_params['fll_bw']) - 1 and \
          self.pll_bw_index == len(self.track_params['pll_bw']) - 1 and \
          self.coherent_ms_index == len(self.track_params['coherent_ms']) - 1
      if final_profile:
        return

      if len(self.track_candidates) == 0:
        self._make_track_candidates()
        self.track_candidates = self._filter_track_candidates()
        if len(self.track_candidates) == 0:
          return

      for i, track_profile in list(enumerate(self.track_candidates)):
        coherent_ms_index = track_profile['coherent_ms_index']
        coherent_ms = self.track_params['coherent_ms'][coherent_ms_index]
        bit_sync_required = (coherent_ms != 1)

        if bit_sync_required:
          if not self.bit_sync:
            continue
          if int(self.bit_sync_timer_ms + 0.5) % 20 != 0:
            # wait for bit edge
            continue

        track_profile = self.track_candidates.pop(i)

        # switch to next track profile

        self.fll_bw_index = track_profile['fll_bw_index']
        self.pll_bw_index = track_profile['pll_bw_index']
        self.coherent_ms_index = track_profile['coherent_ms_index']

        self.track_candidates = []
        self._set_track_profile()
        break

    else:
      if self.lock_detect_outp_prev:
        # we just lost the lock
        self.track_profile_timer_ms = 0

      if self.acc_detected:
        threshold = 50
      else:
        threshold = 10000

      if self.track_profile_timer_ms > threshold:
        if self.fll_bw_index == 0 and \
           self.pll_bw_index == 0 and \
           self.coherent_ms_index == 0:
          return
        self.fll_bw_index = 0
        self.pll_bw_index = 0
        self.coherent_ms_index = 0
      else:
        if self.fll_bw_index == 0:
          return
        self.fll_bw_index = 0

      self._set_track_profile()

    self.lock_detect_outp_prev = self.lock_detect_outp

  def _run_nav_data_decoding(self):
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
    redefine the customization methods
    '_run_track_profile_selection', '_run_nav_data_decoding'
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

      cur_fsm_state = self.fsm_states[self.fsm_index]
      flags_pre = cur_fsm_state[2]['pre']

      if defaults.APPLY_CORR_1 in flags_pre:
        self.corr_code_freq = self.code_freq_1
        self.corr_carr_freq = self.carr_freq_1
      elif defaults.APPLY_CORR_2 in flags_pre:
        self.corr_code_freq = self.code_freq_2
        self.corr_carr_freq = self.carr_freq_2

      if defaults.PREPARE_BIT_COMPENSATION in flags_pre:
        comp_bit_E = 0
        comp_bit_P = 0
        comp_bit_L = 0

      samples_ = samples[self.signal]['samples'][sample_index:]

      E_, P_, L_, blksize, self.code_phase, self.carr_phase = self.correlator(
          samples_,
          self.code_phase + cur_fsm_state[0],
          self.corr_code_freq + self.chipping_rate, self.code_phase,
          self.corr_carr_freq + self.IF, self.carr_phase,
          self.prn_code,
          self.sampling_freq,
          self.signal
      )

      self.track_profile_timer_ms += 1e3 * blksize / self.sampling_freq
      self.bit_sync_timer_ms += 1e3 * blksize / self.sampling_freq
      self.acc_timer_ms += 1e3 * blksize / self.sampling_freq

      sample_index += blksize
      samples_processed += blksize
      self.carr_phase_acc += self.corr_carr_freq * blksize / self.sampling_freq
      self.code_phase_acc += self.corr_code_freq * blksize / self.sampling_freq
      estimated_blksize -= blksize

      self.E += E_
      self.P += P_
      self.L += L_

      flags_post = cur_fsm_state[2]['post']
      self.fsm_index = cur_fsm_state[1]

      if defaults.COMPENSATE_BIT_POLARITY in flags_post:
        if self.P.real < 0:
          comp_bit_E += -self.E
          comp_bit_P += -self.P
          comp_bit_L += -self.L
        else:
          comp_bit_E += self.E
          comp_bit_P += self.P
          comp_bit_L += self.L
        self.E = 0
        self.P = 0
        self.L = 0

      if defaults.USE_COMPENSATED_BIT in flags_post:
        self.E = comp_bit_E
        self.P = comp_bit_P
        self.L = comp_bit_L

      if defaults.RUN_LD in flags_post:
        # Update PLL lock detector
        self.lock_detect_outo, \
            self.lock_detect_outp, \
            lock_detect_pcount1, \
            lock_detect_pcount2, \
            self.lock_detect_lpfi, \
            self.lock_detect_lpfq = self.lock_detect.update(self.P.real,
                                                            self.P.imag,
                                                            1)
        # Update PLL fast lock detector
        self.lock_detect_fast_outo, \
            self.lock_detect_fast_outp, \
            lock_detect_fast_pcount1, \
            lock_detect_fast_pcount2, \
            self.lock_detect_fast_lpfi, \
            self.lock_detect_fast_lpfq = self.lock_detect_fast.update(self.P.real,
                                                                      self.P.imag,
                                                                      1)

        # Update PLL fast lock detector
        self.lock_detect_slow_outo, \
            self.lock_detect_slow_outp, \
            lock_detect_slow_pcount1, \
            lock_detect_slow_pcount2, \
            self.lock_detect_slow_lpfi, \
            self.lock_detect_slow_lpfq = self.lock_detect_slow.update(self.P.real,
                                                                      self.P.imag,
                                                                      1)

      if defaults.ALIAS_DETECT_1ST in flags_post or \
         defaults.ALIAS_DETECT_BOTH in flags_post:
        self.alias_detector.first(P_)

      if defaults.ALIAS_DETECT_2ND in flags_post or \
         defaults.ALIAS_DETECT_BOTH in flags_post:
        self.alias_detector.second(P_)

      err_hz = self.alias_detector.get_err_hz()
      if abs(err_hz) > 0:
        logger.info("[PRN: %d (%s)] False lock detected. "
                    "Error: %.1f Hz. Correcting..." %
                    (self.prn + 1, self.signal, -err_hz))
        self.loop_filter.adjust_freq(err_hz * 2 * np.pi)

      if not (defaults.GET_CORR_1 in flags_post) and \
         not (defaults.GET_CORR_2 in flags_post):
        continue

      phase_acc = self.loop_filter.to_dict()['phase_acc'] / (2 * np.pi)
      self.track_result.acc_g[self.i] = self.acc_g

      # run tracking loop
      self.loop_filter.update(self.E, self.P, self.L)

      if defaults.GET_CORR_1 in flags_post:
        self.code_freq_1 = \
            self.loop_filter.to_dict()['code_freq'] / (2 * np.pi)
        self.carr_freq_1 = \
            self.loop_filter.to_dict()['carr_freq'] / (2 * np.pi)
      elif defaults.GET_CORR_2 in flags_post:
        self.code_freq_2 = \
            self.loop_filter.to_dict()['code_freq'] / (2 * np.pi)
        self.carr_freq_2 = \
            self.loop_filter.to_dict()['carr_freq'] / (2 * np.pi)

      self.track_result.coherent_ms[self.i] = self.coherent_ms

      self.track_result.IF = self.IF
      self.track_result.carr_phase[self.i] = self.carr_phase
      self.track_result.carr_phase_acc[self.i] = self.carr_phase_acc
      self.track_result.carr_freq[self.i] = \
          self.loop_filter.to_dict()['carr_freq'] / (2 * np.pi)

      self.track_result.code_phase[self.i] = self.code_phase
      self.track_result.code_phase_acc[self.i] = self.code_phase_acc
      self.track_result.code_freq[self.i] = \
          self.loop_filter.to_dict()['code_freq']

      self.track_result.phase_err[self.i] = \
          self.loop_filter.to_dict()['phase_err']
      self.track_result.iq_ratio_min[self.i] = self.track_profile['iq_ratio']

      self.track_result.code_err[self.i] = \
          self.loop_filter.to_dict()['code_err']

      self.track_result.acceleration[self.i] = \
          self.loop_filter.to_dict()['phase_acc']

      self.track_result.fll_bw[self.i] = self.loop_filter.to_dict()['fll_bw']
      self.track_result.pll_bw[self.i] = self.loop_filter.to_dict()['pll_bw']
      self.track_result.dll_bw[self.i] = self.loop_filter.to_dict()['dll_bw']

      self.track_result.track_timer_ms[self.i] = self.track_profile_timer_ms
      self.track_result.acc_timer_ms[self.i] = self.acc_timer_ms
      self.track_result.acc_detected[self.i] = self.acc_detected

      # Record stuff for postprocessing
      self.track_result.absolute_sample[self.i] = self.sample_index + \
          samples_processed

      self.track_result.E[self.i] = self.E
      self.track_result.P[self.i] = self.P
      self.track_result.L[self.i] = self.L

      self.track_result.cn0[self.i], \
          self.track_result.snr[self.i], \
          self.track_result.snr_db[self.i] = \
          self.cn0_est.update(self.P.real, self.P.imag)

      self.track_result.lock_detect_outo[self.i] = self.lock_detect_outo
      self.track_result.lock_detect_outp[self.i] = self.lock_detect_outp
      self.track_result.lock_detect_fast_outo[self.i] = \
          self.lock_detect_fast_outo
      self.track_result.lock_detect_fast_outp[self.i] = \
          self.lock_detect_fast_outp
      self.track_result.lock_detect_pcount1[self.i] = lock_detect_pcount1
      self.track_result.lock_detect_pcount2[self.i] = lock_detect_pcount2

      self.track_result.lock_detect_lpfi[self.i] = self.lock_detect_lpfi
      self.track_result.lock_detect_lpfq[self.i] = self.lock_detect_lpfq

      self.track_result.lock_detect_fast_lpfi[self.i] = \
          self.lock_detect_fast_lpfi
      self.track_result.lock_detect_fast_lpfq[self.i] = \
          self.lock_detect_fast_lpfq

      self.track_result.lock_detect_slow_lpfi[self.i] = \
          self.lock_detect_slow_lpfi
      self.track_result.lock_detect_slow_lpfq[self.i] = \
          self.lock_detect_slow_lpfq

      self.track_result.alias_detect_err_hz[self.i] = err_hz

      self._run_nav_data_decoding()
      self._run_track_profile_selection()

      self.track_result.bit_sync[self.i] = self.bit_sync

      # Estimated blksize might change as a result of a change of
      # the coherent integration time.
      estimated_blksize = self.coherent_ms * self.sampling_freq / 1e3

      if (sample_index + 2 * estimated_blksize) < samples_total:
        self.track_result.more_samples[self.i] = 0
      else:
        self.track_result.more_samples[self.i] = 1

      self.samples_tracked = self.sample_index + samples_processed
      self.track_result.ms_tracked[self.i] = self.samples_tracked * 1e3 / \
          self.sampling_freq

      self.i += 1
      if self.i >= self.results_num:
        self.dump()

      self.E = self.P = self.L = 0.j

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
    params['IF'] = params['samples'][gps_constants.L1CA]['IF']
    params['prn_code'] = caCodes[params['acq'].prn]
    params['code_freq_init'] = params['acq'].doppler * \
        gps_constants.l1ca_chip_rate / gps_constants.l1

    params['track_params'] = defaults.l1ca_track_params
    params['loop_filter_params_template'] = \
        defaults.l1ca_loop_filter_params_template

    params['lock_detect_params'] = defaults.l1ca_lock_detect_params_opt
    params['chipping_rate'] = gps_constants.l1ca_chip_rate
    params['sample_index'] = params['samples']['sample_index']
    params['carrier_freq'] = gps_constants.l1
    params['fsm_states_all'] = defaults.gps_fsm_states

    self.bit_sync = False

    TrackingChannel.__init__(self, params)

    self.nav_msg = NavMsg()
    self.nav_bit_sync = NBSMatchBit() if self.prn < 32 else NBSSBAS()
    self.l2c_handover_acq = None
    self.l2c_handover_done = False

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

  def _run_nav_data_decoding(self):
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

    self.bit_sync = self.nav_bit_sync.bit_sync_acquired()

    # Handover to L2C if possible
    if self.l2c_handover and not self.l2c_handover_acq and \
        gps_constants.L2C in self.samples and \
       'samples' in self.samples[gps_constants.L2C] and sync:
      chan_snr = self.track_result.cn0[self.i]
      chan_snr -= 10 * np.log10(defaults.L1CA_CHANNEL_BANDWIDTH_HZ)
      chan_snr = np.power(10, chan_snr / 10)
      l2c_doppler = self.loop_filter.to_dict(
      )['carr_freq'] * gps_constants.l2 / gps_constants.l1 / (2 * np.pi)
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

    params['lock_detect_params'] = defaults.l2c_lock_detect_params_20ms
    params['IF'] = params['samples'][gps_constants.L2C]['IF']
    params['prn_code'] = L2CMCodes[params['acq'].prn]
    params['code_freq_init'] = params['acq'].doppler * \
        gps_constants.l2c_chip_rate / gps_constants.l2

    params['track_params'] = defaults.l2c_track_params
    params['loop_filter_params_template'] = \
        defaults.l2c_loop_filter_params_template

    params['chipping_rate'] = gps_constants.l2c_chip_rate
    params['sample_index'] = 0
    params['carrier_freq'] = gps_constants.l2
    params['fsm_states_all'] = defaults.gps_fsm_states

    self.bit_sync = True

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

  def _run_nav_data_decoding(self):
    """
    Runs L2C navigation bit sync decoding operation.

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
    params['IF'] = params['samples'][glo_constants.GLO_L1]['IF']
    params['prn_code'] = GLOCode
    params['code_freq_init'] = params['acq'].doppler * \
        glo_constants.glo_chip_rate / glo_constants.glo_l1

    params['track_params'] = defaults.glol1_track_params
    params['loop_filter_params_template'] = \
        defaults.glol1_loop_filter_params_template

    params['lock_detect_params'] = defaults.glol1_lock_detect_params
    params['chipping_rate'] = glo_constants.glo_chip_rate
    params['sample_index'] = params['samples']['sample_index']
    params['carrier_freq'] = glo_constants.glo_l1

    params['fsm_states_all'] = defaults.glo_fsm_states

    self.bit_sync = False

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

  def _run_nav_data_decoding(self):
    """
    Run GLO L1 coherent integration postprocessing.
    Runs navigation bit sync decoding operation and
    GLO L1 to GLO L2 handover.
    """

    # Handover to L2 if possible
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
    self.snr = np.zeros(n_points)
    self.snr_db = np.zeros(n_points)
    self.lock_detect_outp = np.zeros(n_points)
    self.lock_detect_outo = np.zeros(n_points)
    self.lock_detect_fast_outp = np.zeros(n_points)
    self.lock_detect_fast_outo = np.zeros(n_points)
    self.lock_detect_pcount1 = np.zeros(n_points)
    self.lock_detect_pcount2 = np.zeros(n_points)

    self.lock_detect_lpfi = np.zeros(n_points)
    self.lock_detect_lpfq = np.zeros(n_points)

    self.lock_detect_fast_lpfi = np.zeros(n_points)
    self.lock_detect_fast_lpfq = np.zeros(n_points)

    self.lock_detect_slow_lpfi = np.zeros(n_points)
    self.lock_detect_slow_lpfq = np.zeros(n_points)

    self.alias_detect_err_hz = np.zeros(n_points)
    self.phase_err = np.zeros(n_points)
    self.iq_ratio_min = np.zeros(n_points)
    self.code_err = np.zeros(n_points)
    self.acceleration = np.zeros(n_points)
    self.acc_g = np.zeros(n_points)
    self.acc_detected = np.zeros(n_points)
    self.nav_msg = NavMsg()
    self.nav_msg_bit_phase_ref = np.zeros(n_points)
    self.nav_bit_sync = NBSMatchBit() if prn < 32 else NBSSBAS()
    self.tow = np.empty(n_points)
    self.tow[:] = np.NAN
    self.coherent_ms = np.zeros(n_points)
    self.more_samples = np.zeros(n_points)

    self.bit_sync = np.zeros(n_points)

    self.fll_bw = np.zeros(n_points)
    self.pll_bw = np.zeros(n_points)
    self.dll_bw = np.zeros(n_points)

    self.track_timer_ms = np.zeros(n_points)
    self.acc_timer_ms = np.zeros(n_points)

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
            "sample,ms,coherent_ms,bs,fll_bw,pll_bw,dll_bw,"
            "track_ms,acc_ms,"
            "plock,plock_fast,"
            "i/q,i/q_fast,i/q_slow,i/q_raw,i/q_min,"
            "acc_g,acc_flag,"
            "phase_err,code_err,CN0,IF,doppler_phase,"
            "carr_doppler,code_phase,code_freq,"
            "SNR,SNR_DB,P_Mag,E_I,E_Q,P_I,P_Q,L_I,L_Q,"
            "lock_detect_pcount1,lock_detect_pcount2,"
            "lock_detect_lpfi,lock_detect_lpfq,"
            "alias_detect_err_hz,"
            "acceleration,code_phase_acc,more_samples\n")
      for i in range(size):
        f1.write("%s," % int(self.absolute_sample[i]))
        f1.write("%.1f," % self.ms_tracked[i])
        f1.write("%s," % self.coherent_ms[i])

        f1.write("%d," % self.bit_sync[i])

        f1.write("%s," % self.fll_bw[i])
        f1.write("%s," % self.pll_bw[i])
        f1.write("%s," % self.dll_bw[i])

        f1.write("%d," % self.track_timer_ms[i])
        f1.write("%d," % self.acc_timer_ms[i])

        f1.write("%s," % int(self.lock_detect_outp[i]))
        f1.write("%s," % int(self.lock_detect_fast_outp[i]))

        f1.write("%.1f," % (self.lock_detect_lpfi[i] / self.lock_detect_lpfq[i]))
        f1.write("%.1f," % (self.lock_detect_fast_lpfi[i] /
                          self.lock_detect_fast_lpfq[i]))
        f1.write("%.1f," % (self.lock_detect_slow_lpfi[i] /
                          self.lock_detect_slow_lpfq[i]))
        f1.write("%.1f," % np.absolute(self.P[i].real / self.P[i].imag))
        f1.write("%.1f," % self.iq_ratio_min[i])

        f1.write("%.1f," % self.acc_g[i])
        f1.write("%d," % self.acc_detected[i])

        f1.write("%.1f," % self.phase_err[i])
        f1.write("%.1f," % self.code_err[i])
        f1.write("%.1f," % self.cn0[i])

        f1.write("%s," % self.IF)
        f1.write("%.1f," % self.carr_phase[i])
        f1.write("%.1f," % self.carr_freq[i])
        f1.write("%.1f," % self.code_phase[i])
        f1.write("%.1f," % self.code_freq[i])
        f1.write("%.1f," % self.snr[i])
        f1.write("%.1f," % self.snr_db[i])
        f1.write("%.1f," % (np.absolute(self.P[i]) ** 2))
        f1.write("%.1f," % self.E[i].real)
        f1.write("%.1f," % self.E[i].imag)
        f1.write("%.1f," % self.P[i].real)
        f1.write("%.1f," % self.P[i].imag)
        f1.write("%.1f," % self.L[i].real)
        f1.write("%.1f," % self.L[i].imag)
        f1.write("%s," % int(self.lock_detect_pcount1[i]))
        f1.write("%s," % int(self.lock_detect_pcount2[i]))
        f1.write("%s," % self.lock_detect_lpfi[i])
        f1.write("%s," % self.lock_detect_lpfq[i])
        f1.write("%s," % self.alias_detect_err_hz[i])
        f1.write("%s," % self.acceleration[i])
        f1.write("%s," % self.code_phase_acc[i])
        f1.write("%s\n" % self.more_samples[i])

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
    self.sync_acquired = False
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
      self.sync_acquired = True
      return True, bit
    else:
      return False, None

  def bit_sync_acquired(self):
    return self.sync_acquired

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

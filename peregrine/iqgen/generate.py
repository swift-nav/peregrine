# Copyright (C) 2016 Swift Navigation Inc.
# Contact: Valeri Atamaniouk <valeri@swiftnav.com>
#
# This source is subject to the license found in the file 'LICENSE' which must
# be be distributed together with this source. All other rights reserved.
#
# THIS CODE AND INFORMATION IS PROVIDED "AS IS" WITHOUT WARRANTY OF ANY KIND,
# EITHER EXPRESSED OR IMPLIED, INCLUDING BUT NOT LIMITED TO THE IMPLIED
# WARRANTIES OF MERCHANTABILITY AND/OR FITNESS FOR A PARTICULAR PURPOSE.


"""
The :mod:`peregrine.iqgen.generate` module contains classes and functions
related to main loop of samples generation.

"""

from peregrine.iqgen.bits.satellite_gps import GPSSatellite
from peregrine.iqgen.bits.filter_lowpass import LowPassFilter
from peregrine.iqgen.bits.filter_bandpass import BandPassFilter

from peregrine.iqgen.bits.amplitude_base import NoiseParameters

from peregrine.iqgen.bits import signals

import sys
import traceback
import logging
import scipy
import numpy
import time

import multiprocessing

logger = logging.getLogger(__name__)


class Task(object):
  '''
  Period computation task. This object performs a batch computation of signal
  in the specified range.
  '''

  def __init__(self,
               outputConfig,
               signalSources,
               noiseParams,
               tcxo,
               signalFilters,
               groupDelays,
               bands,
               generateDebug):
    '''
    Parameters
    ----------
    outputConfig : object
      Output profile
    signalSources : array-like
      List of satellites
    noiseParams : NoiseParameters
      Noise parameters container
    tcxo : object
      TCXO control object
    signalFilters : array-like
      Output signal filter objects
    groupDelays : bool
      Flag if group delays are enabled
    bands : list
      List of bands to generate
    generateDebug : bool
      Flag if additional debug output is required
    '''

    self.outputConfig = outputConfig
    self.signalSources = signalSources
    self.signalFilters = signalFilters
    self.generateDebug = generateDebug
    self.noiseParams = noiseParams
    self.tcxo = tcxo
    self.signals = scipy.ndarray(shape=(outputConfig.N_GROUPS,
                                        outputConfig.SAMPLE_BATCH_SIZE),
                                 dtype=numpy.float)
    self.noise = self.createNoise(outputConfig.SAMPLE_BATCH_SIZE)
    self.nSamples = outputConfig.SAMPLE_BATCH_SIZE
    self.groupDelays = groupDelays
    self.bands = bands

  def update(self, userTime0_s, nSamples, firstSampleIndex):
    '''
    Configure object for the next batch generation

    The method stores parameters for the generation step and updates internal
    arrays to match output shape.

    Parameters
    ----------
    userTime0_s : float
      Time of the interval start in seconds
    nSamples : long
      Number of samples in the interval
    firstSampleIndex : long
      Index of the first sample
    '''
    self.userTime0_s = userTime0_s
    self.firstSampleIndex = firstSampleIndex

    if (self.nSamples != nSamples):
      newSignals = numpy.ndarray((self.outputConfig.N_GROUPS,
                                  nSamples), dtype=float)
      newNoise = self.createNoise(nSamples)
      self.nSamples = nSamples
      self.signals = newSignals
      self.noise = newNoise

  def createNoise(self, nSamples):
    '''
    Generate noise array for a given noise sigma.

    Parameters
    ----------
    nSamples : int
      Length of the samples vectors

    Returns
    -------
    numpy.ndarray(shape=(outputConfig.N_GROUPS, nSamples), dtype=numpy.float)
      Noise values
    '''
    noiseParams = self.noiseParams
    noise = None
    if noiseParams is not None:
      # Initialize signal array with noise
      noiseSigma = noiseParams.getNoiseSigma()
      noise = noiseSigma * scipy.randn(self.outputConfig.N_GROUPS,
                                       nSamples) if noiseSigma else None
    return noise

  def computeTcxoVector(self):
    '''
    Computes TCXO time drift vector if enabled.

    Returns
    -------
    numpy.array or None
      Computed TCXO time drift as a vector or None if TCXO is not enabled
    '''
    tcxo = self.tcxo
    if tcxo:
      firstSampleIndex = self.firstSampleIndex
      finalSampleIndex = firstSampleIndex + self.nSamples
      outputConfig = self.outputConfig
      tcxoTimeDrift_s = tcxo.computeTcxoTime(firstSampleIndex,
                                             finalSampleIndex,
                                             outputConfig)
    else:
      tcxoTimeDrift_s = None
    return tcxoTimeDrift_s

  def computeTimeVector(self):
    '''
    Computes time vector for the batch.

    Returns
    -------
    numpy.array
      Computed time vector for computing sampling time
    '''
    outputConfig = self.outputConfig

    # Group delay shifts all time stamps backwards, this shift is performed
    # before TCXO drift is applied, as group delays are not controlled by TCXO
    userTime0_s = self.userTime0_s
    userTimeX_s = userTime0_s + float(self.nSamples) / \
        float(outputConfig.SAMPLE_RATE_HZ)
    userTimeAll_s = scipy.linspace(userTime0_s,
                                   userTimeX_s,
                                   self.nSamples,
                                   endpoint=False)
    return userTimeAll_s

  def computeGroupTimeVectors(self, userTimeAll_s, outputConfig):
    '''
    Computes group time vector from a single source and output configuration.

    Parameters
    ----------
    userTimeAll_s : numpy.array
      Time vector
    outputConfig : object
      Output configuration with group delay parameters

    Returns
    -------
    list[numpy.array] * outputConfig.N_GROUPS
      If the group delays are enabled, each element offsets initial time vector
      by an appropriate group delay, otherwise all entries point to original
      time vector without modifications. 
    '''
    if self.groupDelays:
      # In case of group delays the time vector shall be adjusted for each
      # signal group. This makes impossible parallel processing of multiple
      # signals with the same time vector.
      bandTimeAll_s = [userTimeAll_s + outputConfig.GROUP_DELAYS[x]
                       for x in range(outputConfig.N_GROUPS)]
    else:
      bandTimeAll_s = [userTimeAll_s] * outputConfig.N_GROUPS

    return bandTimeAll_s

  def perform(self):
    outputConfig = self.outputConfig
    signalSources = self.signalSources
    signalFilters = self.signalFilters
    noiseParams = self.noiseParams
    generateDebug = self.generateDebug
    noise = self.noise  # Noise matrix if present
    sigs = self.signals  # Signal matrix

    # Compute time stamps in linear time space
    userTimeAll_s = self.computeTimeVector()

    # Compute TCXO time drift and apply if appropriate
    tcxoTimeDrift_s = self.computeTcxoVector()
    if tcxoTimeDrift_s:
      userTimeAll_s += tcxoTimeDrift_s

    # Compute band time vectors with group delays
    bandTimeAll_s = self.computeGroupTimeVectors(userTimeAll_s, outputConfig)

    # Prepare signal matrix
    sigs.fill(0.)
    if noise is not None:
      # Initialize signal array with noise
      sigs += noise

    # Debug data
    if generateDebug:
      signalData = []
      debugData = {'time': userTimeAll_s, 'signalData': signalData}
    else:
      debugData = None

    # Sum up signals for all SVs
    for signalSource in signalSources:
      for band in self.bands:
        if signalSource.isBandEnabled(band, outputConfig):
          # Add signal from source (satellite) to signal accumulator
          t = signalSource.getBatchSignals(bandTimeAll_s[band.INDEX],
                                           sigs,
                                           outputConfig,
                                           noiseParams,
                                           band,
                                           generateDebug)
          # Debugging output
          if generateDebug:
            svDebug = {'name': signalSource.getSvName(), 'data': t}
            signalData.append(svDebug)

          t = None

    if signalFilters is list:
      # Filter signal values through LPF, BPF or another
      for i in range(outputConfig.N_GROUPS):
        filterObject = signalFilters[i]
        if filterObject is not None:
          sigs[i][:] = filterObject.filter(sigs[i])

    inputParams = (self.userTime0_s, self.nSamples, self.firstSampleIndex)
    return (inputParams, sigs, debugData)


class Worker(multiprocessing.Process):
  '''
  Remote process worker. The object encapsulates Task logic for running in a
  separate address space.
  '''

  def __init__(self,
               outputConfig,
               signalSources,
               noiseParams,
               tcxo,
               signalFilters,
               groupDelays,
               bands,
               generateDebug):
    super(Worker, self).__init__()
    self.queueIn = multiprocessing.Queue()
    self.queueOut = multiprocessing.Queue()
    self.totalWaitTime_s = 0.
    self.totalExecTime_s = 0.
    self.outputConfig = outputConfig
    self.signalSources = signalSources
    self.noiseParams = noiseParams
    self.tcxo = tcxo
    self.signalFilters = signalFilters
    self.groupDelays = groupDelays
    self.bands = bands
    self.generateDebug = generateDebug

  def run(self):
    task = Task(self.outputConfig,
                self.signalSources,
                noiseParams=self.noiseParams,
                tcxo=self.tcxo,
                signalFilters=self.signalFilters,
                groupDelays=self.groupDelays,
                bands=self.bands,
                generateDebug=self.generateDebug)

    while True:
      opStartTime_s = time.clock()
      inputRequest = self.queueIn.get()
      if inputRequest is None:
        # EOF reached
        break
      (userTime0_s, nSamples, firstSampleIndex) = inputRequest

      opDuration_s = time.clock() - opStartTime_s
      self.totalWaitTime_s += opDuration_s
      startTime_s = time.clock()
      try:
        task.update(userTime0_s, nSamples, firstSampleIndex)
        result = task.perform()
        import copy
        result = copy.deepcopy(result)
        self.queueOut.put(result)
      except:
        exType, exValue, exTraceback = sys.exc_info()
        traceback.print_exception(
            exType, exValue, exTraceback, file=sys.stderr)
        self.queueOut.put(None)
        self.queueIn.close()
        self.queueOut.close()
        sys.exit(1)
      duration_s = time.clock() - startTime_s
      self.totalExecTime_s += duration_s

    statistics = (self.totalWaitTime_s, self.totalExecTime_s)
    self.queueOut.put(statistics)
    self.queueIn.close()
    self.queueOut.close()
    sys.exit(0)


def printSvInfo(sv_list, outputConfig, lpfFA_db, noiseParams, encoder):
  '''
  Print some relevant information to console.

  Parameters
  ----------
  sv_list : list
    List of signal sources
  outputConfig : object
    Output configuration object
  lpfFA_db : list
    Filter attenuation levels for each band
  encoder : Encoder
    Encoder object
  '''
  for _sv in sv_list:
    _svNo = _sv.getName()
    _amp = _sv.amplitude
    _svTime0_s = 0
    _dist0_m = _sv.doppler.computeDistanceM(_svTime0_s)
    _speed_mps = _sv.doppler.computeSpeedMps(_svTime0_s)
    # svMeanPower = _sv.getAmplitude().computeMeanPower()
    if isinstance(_sv, GPSSatellite):
      band1 = outputConfig.GPS.L1
      band2 = outputConfig.GPS.L2
      band1IncreaseDb = 60. - lpfFA_db[band1.INDEX]  # GPS L1 C/A
      # GPS L2C CM - only half of power is used: -3dB
      band2IncreaseDb = 60. - 3. - lpfFA_db[band2.INDEX]
      signal1 = signals.GPS.L1CA
      signal2 = signals.GPS.L2C
      _msg1 = _sv.getL1CAMessage()
      _msg2 = _sv.getL2CMessage()
      _l2ct = _sv.getL2CLCodeType()
    else:
      pass
    # SNR for a satellite. Depends on sampling rate.
    if noiseParams.getNoiseSigma():
      svSNR_db = _sv.getAmplitude().computeSNR(noiseParams)
      svCNoL1 = svSNR_db + band1IncreaseDb - encoder.getAttenuationLevel()
      svCNoL2 = svSNR_db + band2IncreaseDb - encoder.getAttenuationLevel()
    else:
      svSNR_db = 60.
      svCNoL1 = svCNoL2 = 120

    _d1 = signal1.calcDopplerShiftHz(_dist0_m, _speed_mps)
    _d2 = signal2.calcDopplerShiftHz(_dist0_m, _speed_mps)
    _f1 = signal1.CENTER_FREQUENCY_HZ
    _f2 = signal2.CENTER_FREQUENCY_HZ
    _bit = signal1.getSymbolIndex(_svTime0_s)
    _c1 = signal1.getCodeChipIndex(_svTime0_s)
    _c2 = signal2.getCodeChipIndex(_svTime0_s)

    print "{} = {{".format(_svNo)
    print "  .amplitude:  {}".format(_amp)
    print "  .doppler:    {}".format(_sv.doppler)
    if _sv.isBandEnabled(band1, outputConfig):
      print "  .l1_message: {}".format(_msg1)
    if _sv.isBandEnabled(band2, outputConfig):
      print "  .l2_message: {}".format(_msg2)
    if _l2ct:
      print "  .l2_cl_type: {}".format(_l2ct)
    print "  .epoc:"
    print "    .SNR (dB):   {}".format(svSNR_db)
    if _sv.isBandEnabled(band1, outputConfig):
      print "    .L1 CNo:     {}".format(svCNoL1)
    if _sv.isBandEnabled(band2, outputConfig):
      print "    .L2 CNo:     {}".format(svCNoL2)
    print "    .distance:   {} m".format(_dist0_m)
    print "    .speed:      {} m/s".format(_speed_mps)
    if _sv.isBandEnabled(band1, outputConfig):
      print "    .l1_doppler: {} hz @ {}".format(_d1, _f1)
    if _sv.isBandEnabled(band2, outputConfig):
      print "    .l2_doppler: {} hz @ {}".format(_d2, _f2)
    print "    .symbol:     {}".format(_bit)
    if _sv.isBandEnabled(band1, outputConfig):
      print "    .l1_chip:    {}".format(_c1)
    if _sv.isBandEnabled(band2, outputConfig):
      print "    .l2_chip:    {}".format(_c2)
    print "}"


def generateSamples(outputFile,
                    sv_list,
                    encoder,
                    time0S,
                    nSamples,
                    outputConfig,
                    noiseSigma=None,
                    tcxo=None,
                    filterType="none",
                    groupDelays=None,
                    logFile=None,
                    threadCount=0,
                    pbar=None):
  '''
  Generates samples.

  Parameters
  ----------
  fileName : string
    Output file name.
  sv_list : list
    List of configured satellite objects.
  encoder : Encoder
    Output encoder object.
  time0S : float
    Time epoch for the first sample.
  nSamples : long
    Total number of samples to generate.
  outputConfig : object
    Output parameters
  noiseSigma : float, optional
    When specified, adds random noise to the output.
  tcxo : object, optional
    When specified, controls TCXO drift
  filterType : string, optional
    Controls IIR/FIR signal post-processing. Disabled by default.
  groupDelays : bool
    Flag if group delays are enabled.
  logFile : object
    Debug information destination file.
  threadCount : int
    Number of parallel threads for multi-process computation.
  pbar : object
    Progress bar object
  '''

  _t0 = time.clock()
  _count = 0l

  # Check which bands are enabled, configure band-specific parameters
  bands = [outputConfig.GPS.L1,
           outputConfig.GPS.L2,
           outputConfig.GLONASS.L1,
           outputConfig.GLONASS.L2]  # Supported bands
  lpf = [None] * outputConfig.N_GROUPS
  lpfFA_db = [0.] * outputConfig.N_GROUPS  # Filter attenuation levels
  bandsEnabled = [False] * outputConfig.N_GROUPS

  bandPass = filterType == 'bandpass'
  lowPass = filterType == 'lowpass'

  for band in bands:
    for sv in sv_list:
      bandsEnabled[band.INDEX] |= sv.isBandEnabled(band, outputConfig)
    sv = None

    filterObject = None
    ifHz = 0.
    if hasattr(band, "INTERMEDIATE_FREQUENCY_HZ"):
      ifHz = band.INTERMEDIATE_FREQUENCY_HZ
    elif hasattr(band, "INTERMEDIATE_FREQUENCIES_HZ"):
      ifHz = band.INTERMEDIATE_FREQUENCIES_HZ[0]
    else:
      raise ValueError("Unknown band type")

    if lowPass:
      filterObject = LowPassFilter(outputConfig, ifHz)
    elif bandPass:
      filterObject = BandPassFilter(outputConfig, ifHz)
    if filterObject:
      lpf[band.INDEX] = filterObject
      lpfFA_db[band.INDEX] = filterObject.getPassBandAtt()
      logger.debug("Band %d filter NBW is %s" %
                   (band.INDEX, str(filterObject)))

  if noiseSigma is not None:
    noiseVariance = noiseSigma * noiseSigma
    noiseParams = NoiseParameters(outputConfig.SAMPLE_RATE_HZ, noiseSigma)
    logger.info("Selected noise sigma %f (variance %f)" %
                (noiseSigma, noiseVariance))

  else:
    noiseVariance = 0.
    noiseSigma = 0.
    noiseParams = NoiseParameters(outputConfig.SAMPLE_RATE_HZ, 0.)
    logger.info("SNR is not provided, noise is not generated.")

  # Print out parameters
  logger.info("Generating samples, sample rate={} Hz, interval={} seconds".format(
      outputConfig.SAMPLE_RATE_HZ, nSamples / outputConfig.SAMPLE_RATE_HZ))
  logger.debug("Jobs: %d" % threadCount)
  # Print out SV parameters
  printSvInfo(sv_list, outputConfig, lpfFA_db, noiseParams, encoder)

  userTime_s = float(time0S)

  deltaUserTime_s = (float(outputConfig.SAMPLE_BATCH_SIZE) /
                     float(outputConfig.SAMPLE_RATE_HZ))
  debugFlag = logFile is not None

  if debugFlag:
    logFile.write("Index,Time")
    for sv in sv_list:
      svName = sv.getSvName()
      if sv.isL1CAEnabled():
        logFile.write(",%s/L1/doppler" % svName)
      if sv.isL2CEnabled():
        logFile.write(",%s/L2/doppler" % svName)
    # End of line
    logFile.write("\n")

  if threadCount > 0:
    # Parallel execution: create worker pool
    workerPool = [Worker(outputConfig,
                         sv_list,
                         noiseParams,
                         tcxo,
                         lpf,
                         groupDelays,
                         bands,
                         debugFlag) for _ in range(threadCount)]

    for worker in workerPool:
      worker.start()
    # Each worker in the pool permits 2 tasks in the queue.
    maxTaskListSize = threadCount * 2
  else:
    # Synchronous execution: single worker
    workerPool = None
    task = Task(outputConfig,
                sv_list,
                noiseParams=noiseParams,
                tcxo=tcxo,
                signalFilters=lpf,
                groupDelays=groupDelays,
                bands=bands,
                generateDebug=debugFlag)
    maxTaskListSize = 1

  workerPutIndex = 0  # Worker index for adding task parameters with RR policy
  workerGetIndex = 0  # Worker index for getting task results with RR policy
  activeTasks = 0     # Number of active generation tasks

  totalSampleCounter = 0l
  taskQueuedCounter = 0
  taskReceivedCounter = 0

  totalEncodeTime_s = 0.
  totalWaitTime_s = 0.

  while True:
    while activeTasks < maxTaskListSize and totalSampleCounter < nSamples:
      # We have space in the task backlog and not all batchIntervals are issued

      userTime0_s = userTime_s

      if totalSampleCounter + outputConfig.SAMPLE_BATCH_SIZE > nSamples:
        # Last interval may contain less than full batch size of samples
        sampleCount = nSamples - totalSampleCounter
        userTimeX_s = userTime0_s + (float(sampleCount) /
                                     float(outputConfig.SAMPLE_RATE_HZ))
      else:
        # Normal internal: full batch size
        userTimeX_s = userTime_s + deltaUserTime_s
        sampleCount = outputConfig.SAMPLE_BATCH_SIZE

      # Parameters: time interval start, number of samples, sample index
      # counter for debug output
      params = (userTime0_s, sampleCount, totalSampleCounter)
      if workerPool is not None:
        # Parallel execution: add the next task parameters into the worker's
        # pool queue. Worker pool uses RR policy.
        workerPool[workerPutIndex].queueIn.put(params)
        workerPutIndex = (workerPutIndex + 1) % threadCount
      else:
        # Synchronous execution: update task parameters for the next interval
        task.update(userTime0_s, sampleCount, totalSampleCounter)
      activeTasks += 1

      # Update parameters for the next batch interval
      userTime_s = userTimeX_s
      totalSampleCounter += sampleCount
      taskQueuedCounter += 1

    # What for the data only if we have something to wait
    if taskReceivedCounter == taskQueuedCounter and \
       totalSampleCounter == nSamples:
      # No more tasks to issue to generator
      # No more tasks to wait
      break

    try:
      if workerPool is not None:
        # Parallel execution: wait for the next task result
        worker = workerPool[workerGetIndex]
        waitStartTime_s = time.time()
        result = worker.queueOut.get()
        workerGetIndex = (workerGetIndex + 1) % threadCount
        waitDuration_s = time.time() - waitStartTime_s
        totalWaitTime_s += waitDuration_s
      else:
        # Synchronous execution: execute task and get result
        result = task.perform()
    except:
      exType, exValue, exTraceback = sys.exc_info()
      traceback.print_exception(exType, exValue, exTraceback, file=sys.stderr)
      result = None
    taskReceivedCounter += 1
    activeTasks -= 1

    if result is None:
      print "Error in processor; aborting."
      break

    # Unpack result values.
    (inputParams, signalSamples, debugData) = result
    (_userTime0_s, _sampleCount, _firstSampleIndex) = inputParams

    if logFile is not None:
      # Data from all satellites is collected. Now we can dump the debug matrix

      userTimeAll_s = debugData['time']
      signalData = debugData['signalData']
      for smpl_idx in range(_sampleCount):
        logFile.write("{},{}".format(_firstSampleIndex + smpl_idx,
                                     userTimeAll_s[smpl_idx]))
        for svIdx in range(len(signalData)):
          signalSourceData = signalData[svIdx]['data']
          for band in signalSourceData:
            doppler = band['doppler']
            logFile.write(",{}".format(doppler[smpl_idx]))
        # End of line
        logFile.write("\n")

    encodeStartTime_s = time.time()
    # Feed data into encoder
    encodedSamples = encoder.addSamples(signalSamples)
    signalSamples = None

    if len(encodedSamples) > 0:
      _count += len(encodedSamples)
      encodedSamples.tofile(outputFile)
      encodedSamples = None

    totalEncodeTime_s += time.time() - encodeStartTime_s

    if pbar:
      pbar.update(_firstSampleIndex + _sampleCount)

  # Generation completed.

  # Flush any pending data in encoder
  encodedSamples = encoder.flush()
  if len(encodedSamples) > 0:
    encodedSamples.tofile(outputFile)

  # Close debug log file
  if debugFlag:
    logFile.close()

  # Terminate all worker processes
  if workerPool is not None:
    for worker in workerPool:
      worker.queueIn.put(None)
    for worker in workerPool:
      try:
        statistics = worker.queueOut.get(timeout=2)
        print "Statistics:", statistics
      except:
        exType, exValue, exTraceback = sys.exc_info()
        traceback.print_exception(
            exType, exValue, exTraceback, file=sys.stderr)
      worker.queueIn.close()
      worker.queueOut.close()
      worker.terminate()
      worker.join()

  # Print some statistical debug information
  logger.debug("MAIN: Encode duration: %f" % totalEncodeTime_s)
  logger.debug("MAIN: wait duration: %f" % totalWaitTime_s)

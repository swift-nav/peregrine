# Copyright (C) 2016 Swift Navigation Inc.
# Contact: Valeri Atamaniouk <valeri@swiftnav.com>
#
# This source is subject to the license found in the file 'LICENSE' which must
# be be distributed together with this source. All other rights reserved.
#
# THIS CODE AND INFORMATION IS PROVIDED "AS IS" WITHOUT WARRANTY OF ANY KIND,
# EITHER EXPRESSED OR IMPLIED, INCLUDING BUT NOT LIMITED TO THE IMPLIED
# WARRANTIES OF MERCHANTABILITY AND/OR FITNESS FOR A PARTICULAR PURPOSE.

import sys
import traceback

"""
The :mod:`peregrine.iqgen.generate` module contains classes and functions
related to main loop of samples generation.

"""
from peregrine.iqgen.bits.filter_lowpass import LowPassFilter
from peregrine.iqgen.bits.filter_bandpass import BandPassFilter

from peregrine.iqgen.bits import signals

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
               noiseSigma,
               tcxo,
               signalFilters,
               generateDebug):
    '''
    Parameters
    ----------
    outputConfig : object
      Output profile
    signalSources : array-like
      List of satellites
    noiseSigma : float
      Noise sigma value
    tcxo : object
      TCXO control object
    signalFilters : array-like
      Output signal filter objects
    generateDebug : bool
      Flag if additional debug output is required
    '''

    self.outputConfig = outputConfig
    self.signalSources = signalSources
    self.signalFilters = signalFilters
    self.generateDebug = generateDebug
    self.noiseSigma = noiseSigma
    self.tcxo = tcxo
    self.signals = scipy.ndarray(shape=(4, outputConfig.SAMPLE_BATCH_SIZE),
                                 dtype=numpy.float)
    self.noise = self.createNoise(outputConfig.SAMPLE_BATCH_SIZE)
    self.nSamples = outputConfig.SAMPLE_BATCH_SIZE

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
      newSignals = numpy.ndarray((4, nSamples), dtype=float)
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
    numpy.ndarray(shape=(4, nSamples), dtype=numpy.float)
      Noise values
    '''
    noiseSigma = self.noiseSigma
    if noiseSigma is not None:
      # Initialize signal array with noise
      noiseType = 1
      if noiseType == 1:
        noise = noiseSigma * scipy.randn(4, nSamples)
      else:
        noise = numpy.random.normal(loc=0.,
                                    scale=noiseSigma,
                                    size=(4, nSamples))
      # print self.noise
    else:
      noise = None
    return noise

  def perform(self):
    outputConfig = self.outputConfig
    signalSources = self.signalSources
    signalFilters = self.signalFilters
    tcxo = self.tcxo
    firstSampleIndex = self.firstSampleIndex
    finalSampleIndex = firstSampleIndex + self.nSamples

    generateDebug = self.generateDebug

    userTime0_s = self.userTime0_s
    userTimeX_s = userTime0_s + float(self.nSamples) / \
        float(outputConfig.SAMPLE_RATE_HZ)
    userTimeAll_s = scipy.linspace(userTime0_s,
                                   userTimeX_s,
                                   self.nSamples,
                                   endpoint=False)

    if tcxo:
      tcxoTimeDrift_s = tcxo.computeTcxoTime(firstSampleIndex,
                                             finalSampleIndex,
                                             outputConfig)
      if tcxoTimeDrift_s:
        userTimeAll_s += tcxoTimeDrift_s

    noise = self.noise
    sigs = self.signals
    sigs.fill(0.)
    if noise is not None:
      # Initialize signal array with noise
      sigs += noise

    if generateDebug:
      signalData = []
      debugData = {'time': userTimeAll_s, 'signalData': signalData}
    else:
      debugData = None

    # Sum up signals for all SVs
    for signalSource in signalSources:
      # Add signal from source (satellite) to signal accumulator
      t = signalSource.getBatchSignals(userTimeAll_s,
                                       sigs,
                                       outputConfig,
                                       generateDebug)
      # Debugging output
      if generateDebug:
        svDebug = {'name': signalSource.getSvName(), 'data': t}
        signalData.append(svDebug)
      t = None

    if signalFilters is list:
      # Filter signal values through LPF, BPF or another
      for i in range(len(self.filters)):
        filterObject = signalFilters[i]
        if filterObject is not None:
          sigs[i][:] = filterObject.filter(sigs[i])

    inputParams = (self.userTime0_s, self.nSamples, self.firstSampleIndex)
    return (inputParams, sigs, debugData)


class Worker(multiprocessing.Process):

  def __init__(self,
               outputConfig,
               signalSources,
               noiseSigma,
               tcxo,
               signalFilters,
               generateDebug):
    super(Worker, self).__init__()
    self.queueIn = multiprocessing.Queue()
    self.queueOut = multiprocessing.Queue()
    self.totalWaitTime_s = 0.
    self.totalExecTime_s = 0.
    self.outputConfig = outputConfig
    self.signalSources = signalSources
    self.noiseSigma = noiseSigma
    self.tcxo = tcxo
    self.signalFilters = signalFilters
    self.generateDebug = generateDebug

  def run(self):
    task = Task(self.outputConfig,
                self.signalSources,
                noiseSigma=self.noiseSigma,
                tcxo=self.tcxo,
                signalFilters=self.signalFilters,
                generateDebug=self.generateDebug)

    while True:
      opStartTime_s = time.clock()
      inputRequest = self.queueIn.get()
      if inputRequest is None:
        # EOF reached
        break
      (userTime0_s, nSamples, firstSampleIndex) = inputRequest
      # print "Received params", userTime0_s, nSamples, firstSampleIndex
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


def computeTimeIntervalS(outputConfig):
  '''
  Helper for computing generation interval duration in seconds.

  Parameters
  ----------
  outputConfig : object
    Output configuration.

  Returns
  -------
  float
    Generation interval duration in seconds
  '''
  deltaTime_s = float(outputConfig.SAMPLE_BATCH_SIZE) / \
      outputConfig.SAMPLE_RATE_HZ
  return deltaTime_s


def generateSamples(outputFile,
                    sv_list,
                    encoder,
                    time0S,
                    nSamples,
                    outputConfig,
                    SNR=None,
                    tcxo=None,
                    filterType="none",
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
  SNR : float, optional
    When specified, adds random noise to the output.
  tcxo : object, optional
    When specified, controls TCXO drift
  filterType : string, optional
    Controls IIR/FIR signal post-processing. Disabled by default.
  debugLog : bool, optional
    Control generation of additional debug output. Disabled by default.
  '''

  #
  # Print out parameters
  #
  print "Generating samples, sample rate={} Hz, interval={} seconds, SNR={}".format(
        outputConfig.SAMPLE_RATE_HZ, nSamples / outputConfig.SAMPLE_RATE_HZ, SNR)
  print "Jobs: ", threadCount

  _t0 = time.clock()
  _count = 0l

  # Check which bands are enabled, configure band-specific parameters
  bands = [outputConfig.GPS.L1, outputConfig.GPS.L2]  # Supported bands
  lpf = [None] * len(bands)
  bandsEnabled = [False] * len(bands)

  bandPass = False
  lowPass = False
  if filterType == 'lowpass':
    lowPass = True
  elif filterType == 'bandpass':
    bandPass = True
  elif filterType == 'none':
    pass
  else:
    raise ValueError("Invalid filter type %s" % repr(filter))

  for band in bands:
    for sv in sv_list:
      bandsEnabled[band.INDEX] |= sv.isBandEnabled(band.INDEX, outputConfig)

    filterObject = None
    if lowPass:
      filterObject = LowPassFilter(outputConfig,
                                   band.INTERMEDIATE_FREQUENCY_HZ)
    elif bandPass:
      filterObject = BandPassFilter(outputConfig,
                                    band.INTERMEDIATE_FREQUENCY_HZ)
    if filterObject:
      lpf[band.INDEX] = filterObject
      logger.debug("Band %d filter NBW is %s" %
                   (band.INDEX, str(filterObject)))

  if SNR is not None:
    sourcePower = 0.
    for sv in sv_list:
      svMeanPower = sv.getAmplitude().computeMeanPower()
      sourcePower += svMeanPower
      logger.debug("[%s] Estimated mean power is %f" %
                   (sv.getSvName(), svMeanPower))
    meanPower = sourcePower / len(sv_list)
    meanAmplitude = scipy.sqrt(meanPower)
    logger.debug("Estimated total signal power is %f, mean %f, mean amplitude %f" %
                 (sourcePower, meanPower, meanAmplitude))

    # Nsigma and while noise amplitude computation: check if the Nsigma is
    # actually a correct value for white noise with normal distribution.

    # Number of samples for 1023 MHz
    freqTimesTau = outputConfig.SAMPLE_RATE_HZ / 1.023e6
    noiseVariance = freqTimesTau * meanPower / (4. * 10. ** (float(SNR) / 10.))
    noiseSigma = numpy.sqrt(noiseVariance)
    logger.info("Selected noise sigma %f (variance %f) for SNR %f" %
                (noiseSigma, noiseVariance, float(SNR)))

  else:
    noiseVariance = None
    noiseSigma = None
    logger.info("SNR is not provided, noise is not generated.")

  #
  # Print out SV parameters
  #
  for _sv in sv_list:
    _svNo = _sv.getSvName()
    _amp = _sv.amplitude
    _svTime0_s = 0
    _dist0_m = _sv.doppler.computeDistanceM(_svTime0_s)
    _speed_mps = _sv.doppler.computeSpeedMps(_svTime0_s)
    _bit = signals.GPS.L1CA.getSymbolIndex(_svTime0_s)
    _c1 = signals.GPS.L1CA.getCodeChipIndex(_svTime0_s)
    _c2 = signals.GPS.L2C.getCodeChipIndex(_svTime0_s)
    _d1 = signals.GPS.L1CA.calcDopplerShiftHz(_dist0_m, _speed_mps)
    _d2 = signals.GPS.L2C.calcDopplerShiftHz(_dist0_m, _speed_mps)
    svMeanPower = _sv.getAmplitude().computeMeanPower()
    # SNR for a satellite. Depends on sampling rate.
    if noiseVariance:
      svSNR = svMeanPower / (4. * noiseVariance) * freqTimesTau
    else:
      svSNR = 1e6
    svSNR_db = 10. * numpy.log10(svSNR)
    # Filters lower the power according to their attenuation levels
    l1FA_db = lpf[0].getPassBandAtt() if lpf[0] else 0.
    l2FA_db = lpf[1].getPassBandAtt() if lpf[1] else 0.
    # CNo for L1
    svCNoL1 = svSNR_db + 10. * numpy.log10(1.023e6) - l1FA_db
    # CNo for L2, half power used (-3dB)
    svCNoL2 = svSNR_db + 10. * numpy.log10(1.023e6) - 3. - l2FA_db

    print "{} = {{".format(_svNo)
    print "  .amplitude:  {}".format(_amp)
    print "  .doppler:    {}".format(_sv.doppler)
    print "  .l1_message: {}".format(_sv.getL1CAMessage())
    print "  .l2_message: {}".format(_sv.getL2CMessage())
    print "  .l2_cl_type: {}".format(_sv.getL2CLCodeType())
    print "  .SNR (dBHz): {}".format(svSNR_db)
    print "  .L1 CNo:     {}".format(svCNoL1)
    print "  .L2 CNo:     {}".format(svCNoL2)
    print "  .epoc:"
    print "    .distance:   {} m".format(_dist0_m)
    print "    .speed:      {} m/s".format(_speed_mps)
    print "    .symbol:     {}".format(_bit)
    print "    .l1_doppler: {} hz".format(_d1)
    print "    .l2_doppler: {} hz".format(_d2)
    print "    .l1_chip:    {}".format(_c1)
    print "    .l2_chip:    {}".format(_c2)
    print "}"

  userTime_s = float(time0S)

  deltaUserTime_s = computeTimeIntervalS(outputConfig)
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
    workerPool = [Worker(outputConfig,
                         sv_list,
                         noiseSigma,
                         tcxo,
                         lpf,
                         debugFlag) for _ in range(threadCount)]

    for worker in workerPool:
      worker.start()
    maxTaskListSize = threadCount * 2
  else:
    workerPool = None
    task = Task(outputConfig,
                sv_list,
                noiseSigma=noiseSigma,
                tcxo=tcxo,
                signalFilters=lpf,
                generateDebug=debugFlag)
    maxTaskListSize = 1

  workerPutIndex = 0
  workerGetIndex = 0
  activeTasks = 0

  totalSampleCounter = 0
  taskQueuedCounter = 0
  taskReceivedCounter = 0

  totalEncodeTime_s = 0.
  totalWaitTime_s = 0.

  while True:
    while activeTasks < maxTaskListSize and totalSampleCounter < nSamples:
      # We have space in the task backlog and not all batchIntervals are issued
      userTime0_s = userTime_s
      userTimeX_s = userTime_s + deltaUserTime_s
      sampleCount = outputConfig.SAMPLE_BATCH_SIZE

      if totalSampleCounter + sampleCount > nSamples:
        # Last interval may contain less than full batch size of samples
        sampleCount = nSamples - totalSampleCounter
        userTimeX_s = userTime0_s + float(sampleCount) / \
            outputConfig.SAMPLE_RATE_HZ

      params = (userTime0_s, sampleCount, totalSampleCounter)
      # print ">>> ", userTime0_s, sampleCount, totalSampleCounter,
      # workerPutIndex
      if workerPool is not None:
        workerPool[workerPutIndex].queueIn.put(params)
        workerPutIndex = (workerPutIndex + 1) % threadCount
      else:
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
        # Wait for the first task
        worker = workerPool[workerGetIndex]
        waitStartTime_s = time.time()
        # print "waiting data from worker", workerGetIndex
        result = worker.queueOut.get()
        # print "Data received from worker", workerGetIndex
        workerGetIndex = (workerGetIndex + 1) % threadCount
        waitDuration_s = time.time() - waitStartTime_s
        totalWaitTime_s += waitDuration_s
      else:
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

    (inputParams, signalSamples, debugData) = result
    (_userTime0_s, _sampleCount, _firstSampleIndex) = inputParams
    # print "<<< ", _userTime0_s, _sampleCount, _firstSampleIndex

    if logFile is not None:
      # Data from all satellites is collected. Now we can dump the debug matrix

      userTimeAll_s = debugData['time']
      signalData = debugData['signalData']
      for smpl_idx in range(_sampleCount):
        logFile.write("{},{}".format(_firstSampleIndex + smpl_idx,
                                     userTimeAll_s[smpl_idx]))
        for svIdx in range(len(signalData)):
          # signalSourceName = signalData[svIdx]['name']
          signalSourceData = signalData[svIdx]['data']
          for band in signalSourceData:
            # bandType = band['type']
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
    encodeDuration_s = time.time() - encodeStartTime_s
    totalEncodeTime_s += encodeDuration_s

    if pbar:
      pbar.update(_firstSampleIndex + _sampleCount)

  logger.debug("MAIN: Encode duration: %f" % totalEncodeTime_s)
  logger.debug("MAIN: wait duration: %f" % totalWaitTime_s)

  encodedSamples = encoder.flush()
  if len(encodedSamples) > 0:
    encodedSamples.tofile(outputFile)

  if debugFlag:
    logFile.close()

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

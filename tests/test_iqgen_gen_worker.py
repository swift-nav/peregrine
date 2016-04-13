# Copyright (C) 2016 Swift Navigation Inc.
#
# Contact: Valeri Atamaniouk <valeri@swiftnav.com>
# This source is subject to the license found in the file 'LICENSE' which must
# be be distributed together with this source. All other rights reserved.
#
# THIS CODE AND INFORMATION IS PROVIDED "AS IS" WITHOUT WARRANTY OF ANY KIND,
# EITHER EXPRESSED OR IMPLIED, INCLUDING BUT NOT LIMITED TO THE IMPLIED
# WARRANTIES OF MERCHANTABILITY AND/OR FITNESS FOR A PARTICULAR PURPOSE.

'''
Unit tests for IQgen generator worker
'''

from peregrine.iqgen.generate import Worker
from peregrine.iqgen.if_iface import NormalRateConfig
from peregrine.iqgen.bits.satellite_base import Satellite
from peregrine.iqgen.bits.satellite_gps import GPSSatellite
from peregrine.iqgen.bits.amplitude_base import NoiseParameters


def test_Worker_init():
  '''
  Worker object initialization
  '''
  outputConfig = NormalRateConfig
  sv0 = GPSSatellite(1)
  sv0.setL1CAEnabled(True)
  signalSources = [sv0]
  noiseParams = NoiseParameters(outputConfig.SAMPLE_RATE_HZ, 1.)
  tcxo = None
  signalFilters = [None] * 4
  groupDelays = False
  bands = [outputConfig.GPS.L1]
  generateDebug = False

  worker = Worker(outputConfig,
                  signalSources,
                  noiseParams,
                  tcxo,
                  signalFilters,
                  groupDelays,
                  bands,
                  generateDebug)
  assert worker.totalWaitTime_s == 0.
  assert worker.totalExecTime_s == 0.
  assert worker.outputConfig == outputConfig
  assert worker.signalSources == signalSources
  assert worker.noiseParams == noiseParams
  assert worker.tcxo == tcxo
  assert worker.signalFilters == signalFilters
  assert worker.groupDelays == groupDelays
  assert worker.bands == bands
  assert worker.generateDebug == generateDebug


def test_Task_runOnce0():
  '''
  Worker object loop cycle test
  '''
  class MyQueue(object):

    def __init__(self):
      self.queue = []

    def get(self):
      return self.queue.pop(0)

    def put(self, obj):
      return self.queue.append(obj)

  outputConfig = NormalRateConfig
  sv0 = GPSSatellite(1)
  sv0.setL1CAEnabled(True)
  signalSources = [sv0]
  noiseParams = NoiseParameters(outputConfig.SAMPLE_RATE_HZ, 1.)
  tcxo = None
  signalFilters = [None] * 4
  groupDelays = False
  bands = [outputConfig.GPS.L1]
  generateDebug = False

  worker = Worker(outputConfig,
                  signalSources,
                  noiseParams,
                  tcxo,
                  signalFilters,
                  groupDelays,
                  bands,
                  generateDebug)
  # worker.start()
  worker.queueIn = MyQueue()
  worker.queueOut = MyQueue()
  nSamples = 1024
  userTime0_s = 0.
  firstSampleIndex = 1l
  params = (userTime0_s, nSamples, firstSampleIndex)
  worker.queueIn.put(params)
  task = worker.createTask()
  worker.run_once(task)
  result = worker.queueOut.get()
  (inputParams, signalSamples, debugData) = result
  assert inputParams[0] == userTime0_s
  assert inputParams[1] == nSamples
  assert inputParams[2] == firstSampleIndex
  assert debugData is None
  assert signalSamples.shape == (outputConfig.N_GROUPS, nSamples)
  worker.queueIn.put(None)
  worker.run_once(task)
  worker.queueOut.get()
  # worker.terminate()


def test_Task_runOnce1():
  '''
  Worker object loop cycle test
  '''
  class MyQueue(object):

    def __init__(self):
      self.queue = []

    def get(self):
      return self.queue.pop(0)

    def put(self, obj):
      return self.queue.append(obj)

  outputConfig = NormalRateConfig
  sv0 = Satellite('1')
  signalSources = [sv0]
  noiseParams = NoiseParameters(outputConfig.SAMPLE_RATE_HZ, 1.)
  tcxo = None
  signalFilters = [None] * 4
  groupDelays = False
  bands = [outputConfig.GPS.L1]
  generateDebug = False

  worker = Worker(outputConfig,
                  signalSources,
                  noiseParams,
                  tcxo,
                  signalFilters,
                  groupDelays,
                  bands,
                  generateDebug)
  # worker.start()
  worker.queueIn = MyQueue()
  worker.queueOut = MyQueue()
  nSamples = 1024
  userTime0_s = 0.
  firstSampleIndex = 1l
  params = (userTime0_s, nSamples, firstSampleIndex)
  worker.queueIn.put(params)
  task = worker.createTask()
  worker.run_once(task)
  result = worker.queueOut.get()
  assert result is None

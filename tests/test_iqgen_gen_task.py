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
Unit tests for IQgen generator task
'''

from peregrine.iqgen.generate import Task
from peregrine.iqgen.if_iface import NormalRateConfig, HighRateConfig
from peregrine.iqgen.bits.satellite_gps import GPSSatellite
from peregrine.iqgen.bits.amplitude_base import NoiseParameters
from peregrine.iqgen.bits.tcxo_poly import TCXOPoly
from peregrine.iqgen.bits.filter_lowpass import LowPassFilter
import numpy


def test_Task_init():
  '''
  Task object initialization test
  '''
  outputConfig = NormalRateConfig
  sv0 = GPSSatellite(1)
  sv0.setL1CAEnabled(True)
  signalSources = [sv0]
  noiseParams = NoiseParameters(outputConfig.SAMPLE_RATE_HZ, 1.)
  tcxo = TCXOPoly(())
  signalFilters = [None] * 4
  groupDelays = False
  bands = [outputConfig.GPS.L1]
  generateDebug = False

  task = Task(outputConfig,
              signalSources,
              noiseParams,
              tcxo,
              signalFilters,
              groupDelays,
              bands,
              generateDebug)

  assert task.outputConfig == outputConfig
  assert task.bands == bands
  assert task.generateDebug == generateDebug
  assert task.groupDelays == groupDelays
  assert task.noiseParams == noiseParams
  assert task.signalFilters == signalFilters
  assert task.signalSources == signalSources
  assert task.tcxo == tcxo
  assert isinstance(task.noise, numpy.ndarray)
  assert task.noise.shape == (outputConfig.N_GROUPS,
                              outputConfig.SAMPLE_BATCH_SIZE)
  assert isinstance(task.signals, numpy.ndarray)
  assert task.signals.shape == (outputConfig.N_GROUPS,
                                outputConfig.SAMPLE_BATCH_SIZE)


def test_Task_update0():
  '''
  Task object parameter update test
  '''
  outputConfig = NormalRateConfig
  sv0 = GPSSatellite(1)
  sv0.setL1CAEnabled(True)
  signalSources = [sv0]
  noiseParams = NoiseParameters(outputConfig.SAMPLE_RATE_HZ, 1.)
  tcxo = TCXOPoly(())
  signalFilters = [None] * 4
  groupDelays = False
  bands = [outputConfig.GPS.L1]
  generateDebug = False

  task = Task(outputConfig,
              signalSources,
              noiseParams,
              tcxo,
              signalFilters,
              groupDelays,
              bands,
              generateDebug)

  userTime0_s = 123.
  nSamples = outputConfig.SAMPLE_BATCH_SIZE
  firstSampleIndex = 1
  task.update(userTime0_s, nSamples, firstSampleIndex)
  assert task.nSamples == nSamples
  assert task.firstSampleIndex == firstSampleIndex
  assert task.userTime0_s == userTime0_s
  assert task.noise.shape == (outputConfig.N_GROUPS, nSamples)
  assert isinstance(task.signals, numpy.ndarray)
  assert task.signals.shape == (outputConfig.N_GROUPS,  nSamples)


def test_Task_update1():
  '''
  Task object parameter update test
  '''
  outputConfig = NormalRateConfig
  sv0 = GPSSatellite(1)
  sv0.setL1CAEnabled(True)
  signalSources = [sv0]
  noiseParams = NoiseParameters(outputConfig.SAMPLE_RATE_HZ, 1.)
  tcxo = TCXOPoly(())
  signalFilters = [None] * 4
  groupDelays = False
  bands = [outputConfig.GPS.L1]
  generateDebug = False

  task = Task(outputConfig,
              signalSources,
              noiseParams,
              tcxo,
              signalFilters,
              groupDelays,
              bands,
              generateDebug)

  userTime0_s = 123.
  nSamples = 1024
  firstSampleIndex = 1
  task.update(userTime0_s, nSamples, firstSampleIndex)
  assert task.nSamples == nSamples
  assert task.firstSampleIndex == firstSampleIndex
  assert task.userTime0_s == userTime0_s
  assert task.noise.shape == (outputConfig.N_GROUPS, nSamples)
  assert isinstance(task.signals, numpy.ndarray)
  assert task.signals.shape == (outputConfig.N_GROUPS,  nSamples)


def test_Task_computeTcxoVector0():
  '''
  Task object TCXO helper test
  '''
  outputConfig = NormalRateConfig
  sv0 = GPSSatellite(1)
  sv0.setL1CAEnabled(True)
  signalSources = [sv0]
  noiseParams = NoiseParameters(outputConfig.SAMPLE_RATE_HZ, 1.)
  tcxo = TCXOPoly(())
  signalFilters = [None] * 4
  groupDelays = False
  bands = [outputConfig.GPS.L1]
  generateDebug = False

  task = Task(outputConfig,
              signalSources,
              noiseParams,
              tcxo,
              signalFilters,
              groupDelays,
              bands,
              generateDebug)

  tcxo = task.computeTcxoVector()
  assert tcxo is None


def test_Task_computeTcxoVector1():
  '''
  Task object TCXO helper test
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

  task = Task(outputConfig,
              signalSources,
              noiseParams,
              tcxo,
              signalFilters,
              groupDelays,
              bands,
              generateDebug)
  userTime0_s = 123.
  nSamples = 1024
  firstSampleIndex = 1
  task.update(userTime0_s, nSamples, firstSampleIndex)

  tcxo = task.computeTcxoVector()
  assert tcxo is None


def test_Task_computeTcxoVector2():
  '''
  Task object TCXO helper test
  '''
  outputConfig = NormalRateConfig
  sv0 = GPSSatellite(1)
  sv0.setL1CAEnabled(True)
  signalSources = [sv0]
  noiseParams = NoiseParameters(outputConfig.SAMPLE_RATE_HZ, 1.)
  tcxo = TCXOPoly((1.,))
  signalFilters = [None] * 4
  groupDelays = False
  bands = [outputConfig.GPS.L1]
  generateDebug = False

  task = Task(outputConfig,
              signalSources,
              noiseParams,
              tcxo,
              signalFilters,
              groupDelays,
              bands,
              generateDebug)
  userTime0_s = 123.
  nSamples = 1024
  firstSampleIndex = 1
  task.update(userTime0_s, nSamples, firstSampleIndex)

  tcxoVector = task.computeTcxoVector()
  assert isinstance(tcxoVector, numpy.ndarray)
  assert tcxoVector.shape == (1024,)
  assert (tcxoVector != 0.).all()


def test_Task_createNoise():
  '''
  Task object noise helper test
  '''
  outputConfig = NormalRateConfig
  sv0 = GPSSatellite(1)
  sv0.setL1CAEnabled(True)
  signalSources = [sv0]
  noiseParams = NoiseParameters(outputConfig.SAMPLE_RATE_HZ, 1.)
  tcxo = TCXOPoly((1.,))
  signalFilters = [None] * 4
  groupDelays = False
  bands = [outputConfig.GPS.L1]
  generateDebug = False

  task = Task(outputConfig,
              signalSources,
              noiseParams,
              tcxo,
              signalFilters,
              groupDelays,
              bands,
              generateDebug)
  userTime0_s = 123.
  nSamples = outputConfig.SAMPLE_BATCH_SIZE
  firstSampleIndex = 1
  task.update(userTime0_s, nSamples, firstSampleIndex)

  noiseMatrix = task.createNoise()
  assert isinstance(noiseMatrix, numpy.ndarray)
  assert noiseMatrix.shape == (outputConfig.N_GROUPS, nSamples)
  assert numpy.mean(noiseMatrix) < 0.1
  assert (noiseMatrix != 0.).sum() > 1000


def test_Task_computeGroupTimeVectors0():
  '''
  Task object group time vector test
  '''
  outputConfig = NormalRateConfig
  sv0 = GPSSatellite(1)
  sv0.setL1CAEnabled(True)
  signalSources = [sv0]
  noiseParams = NoiseParameters(outputConfig.SAMPLE_RATE_HZ, 1.)
  tcxo = TCXOPoly((1.,))
  signalFilters = [None] * 4
  groupDelays = False
  bands = [outputConfig.GPS.L1]
  generateDebug = False

  task = Task(outputConfig,
              signalSources,
              noiseParams,
              tcxo,
              signalFilters,
              groupDelays,
              bands,
              generateDebug)
  nSamples = 1024
  userTime0_s = 0.
  firstSampleIndex = 1
  task.update(userTime0_s, nSamples, firstSampleIndex)
  userTimeAll_s = task.computeTimeVector()
  result = task.computeGroupTimeVectors(userTimeAll_s)
  assert isinstance(result, list)
  for i in range(outputConfig.N_GROUPS):
    assert (result[i] == userTimeAll_s).all()


def test_Task_computeGroupTimeVectors1():
  '''
  Task object group time vector test
  '''
  outputConfig = NormalRateConfig
  sv0 = GPSSatellite(1)
  sv0.setL1CAEnabled(True)
  signalSources = [sv0]
  noiseParams = NoiseParameters(outputConfig.SAMPLE_RATE_HZ, 1.)
  tcxo = TCXOPoly((1.,))
  signalFilters = [None] * 4
  groupDelays = True
  bands = [outputConfig.GPS.L1]
  generateDebug = False

  task = Task(outputConfig,
              signalSources,
              noiseParams,
              tcxo,
              signalFilters,
              groupDelays,
              bands,
              generateDebug)
  nSamples = 1024
  userTime0_s = 0.
  firstSampleIndex = 1
  task.update(userTime0_s, nSamples, firstSampleIndex)
  userTimeAll_s = task.computeTimeVector()
  result = task.computeGroupTimeVectors(userTimeAll_s)
  assert isinstance(result, list)
  for i in range(outputConfig.N_GROUPS):
    assert (result[i] == userTimeAll_s + outputConfig.GROUP_DELAYS[i]).all()


def test_Task_generate0():
  '''
  Task object generation test
  '''
  outputConfig = HighRateConfig
  sv0 = GPSSatellite(1)
  sv0.setL1CAEnabled(True)
  signalSources = [sv0]
  noiseParams = NoiseParameters(outputConfig.SAMPLE_RATE_HZ, 1.)
  tcxo = TCXOPoly((1.,))
  signalFilters = [LowPassFilter(outputConfig,
                                 outputConfig.GPS.L1.INTERMEDIATE_FREQUENCY_HZ),
                   None, None, None]
  groupDelays = True
  bands = [outputConfig.GPS.L1]
  generateDebug = False

  task = Task(outputConfig,
              signalSources,
              noiseParams,
              tcxo,
              signalFilters,
              groupDelays,
              bands,
              generateDebug)
  nSamples = 1024
  userTime0_s = 0.
  firstSampleIndex = 1
  task.update(userTime0_s, nSamples, firstSampleIndex)
  inputParams, sigs, debugData = task.perform()
  assert inputParams[0] == userTime0_s
  assert inputParams[1] == nSamples
  assert inputParams[2] == firstSampleIndex
  assert debugData is None
  assert sigs.shape == (outputConfig.N_GROUPS, nSamples)


def test_Task_generate1():
  '''
  Task object generation test
  '''
  outputConfig = HighRateConfig
  sv0 = GPSSatellite(1)
  sv0.setL1CAEnabled(True)
  signalSources = [sv0]
  noiseParams = NoiseParameters(outputConfig.SAMPLE_RATE_HZ, 1.)
  tcxo = None
  signalFilters = [None] * 4
  groupDelays = True
  bands = [outputConfig.GPS.L1]
  generateDebug = True

  task = Task(outputConfig,
              signalSources,
              noiseParams,
              tcxo,
              signalFilters,
              groupDelays,
              bands,
              generateDebug)
  nSamples = 1024
  userTime0_s = 0.
  firstSampleIndex = 1
  task.update(userTime0_s, nSamples, firstSampleIndex)
  inputParams, sigs, debugData = task.perform()
  assert inputParams[0] == userTime0_s
  assert inputParams[1] == nSamples
  assert inputParams[2] == firstSampleIndex
  assert isinstance(debugData, dict)
  assert sigs.shape == (outputConfig.N_GROUPS, nSamples)

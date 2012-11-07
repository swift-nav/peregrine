#!/usr/bin/python
#--------------------------------------------------------------------------
#                           SoftGNSS v3.0
#
# Copyright (C) Darius Plausinaitis and Dennis M. Akos
# Written by Darius Plausinaitis and Dennis M. Akos
# Converted to Python by Colin Beighley
#--------------------------------------------------------------------------
#This program is free software; you can redistribute it and/or
#modify it under the terms of the GNU General Public License
#as published by the Free Software Foundation; either version 2
#of the License, or (at your option) any later version.
#
#This program is distributed in the hope that it will be useful,
#but WITHOUT ANY WARRANTY; without even the implied warranty of
#MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#GNU General Public License for more details.
#
#You should have received a copy of the GNU General Public License
#along with this program; if not, write to the Free Software
#Foundation, Inc., 51 Franklin Street, Fifth Floor, Boston, MA  02110-1301,
#USA.
#--------------------------------------------------------------------------

import numpy as np
import pylab
import math
import pyfftw
import pickle
from include.makeCaTable import makeCaTable
from include.generateCAcode import generateCAcode

import logging
logger = logging.getLogger(__name__)

@profile
def acquisition(longSignal, settings, wisdom_file="fftw_wisdom"):
  logger.info("Acquisition starting")

  # Try to load saved FFTW wisdom
  try:
    with open(wisdom_file, 'rb') as f:
      wisdom = pickle.load(f)
      pyfftw.import_wisdom(wisdom)
  except IOError:
    logger.warning("Couldn't open FFTW wisdom file, this run might take longer than usual.")

  # Number of samples per code period
  samplesPerCode = int(round(settings.samplingFreq / (settings.codeFreqBasis / settings.codeLength)))
  #samplesPerCode = 16384
  # Create two 1msec vectors of data to correlate with and one with zero DC
  signal1 = np.array(longSignal[0:samplesPerCode])
  signal2 = np.array(longSignal[samplesPerCode:2*samplesPerCode])
  signal0DC = np.array(longSignal - np.mean(longSignal))
  # Find sampling period
  ts = 1.0/settings.samplingFreq
  # Find phases for the local carrier
  #phasePoints = np.array([2*math.pi*i*ts for i in range(0,samplesPerCode)])
  phasePoints = 2*math.pi*ts * np.arange(samplesPerCode)
  # Number of frequency bins for the given acquisition band (500 Hz steps)
  numberOfFrqBins = int(math.floor(settings.acqSearchBand*1e3/500 + 1))
  # Generate all C/A codes and sample them according to the sampling freq
  caCodesTable = np.array(makeCaTable(settings))
  # Initialize arrays
  results = np.zeros((numberOfFrqBins, samplesPerCode))
  # Carrier frequencies of the frequency bins
  frqBins = np.zeros((numberOfFrqBins))
  # Initialize acqResults
  acqResults = []

  # Make aligned arrays for FFTW
  ca_code = pyfftw.n_byte_align_empty((samplesPerCode), 16, dtype=np.complex128)
  ca_code_ft = pyfftw.n_byte_align_empty(ca_code.shape, 16, dtype=ca_code.dtype)

  corr_ft1 = pyfftw.n_byte_align_empty((samplesPerCode), 16, dtype=np.complex128)
  corr1 = pyfftw.n_byte_align_empty((samplesPerCode), 16, dtype=np.complex128)
  corr_ft2 = pyfftw.n_byte_align_empty((samplesPerCode), 16, dtype=np.complex128)
  corr2 = pyfftw.n_byte_align_empty((samplesPerCode), 16, dtype=np.complex128)

  # Setup FFTW transforms
  ca_code_fft = pyfftw.FFTW(ca_code, ca_code_ft)
  corr_ifft1 = pyfftw.FFTW(corr_ft1, corr1, direction='FFTW_BACKWARD')
  corr_ifft2 = pyfftw.FFTW(corr_ft2, corr2, direction='FFTW_BACKWARD')

  # Find Fourier transforms of the two signals
  signal1_ft = np.fft.fft(signal1)
  signal2_ft = np.fft.fft(signal2)

  for PRN in settings.acqSatelliteList:

    # Find the conjugate Fourier transform of the CA code which will be used to
    # perform the correlation
    ca_code[:] = caCodesTable[PRN]
    ca_code_fft.execute()
    ca_code_ft_conj = np.conj(ca_code_ft)

    for frqBinIndex in range(numberOfFrqBins):
      #--- Generate carrier wave frequency grid (0.5kHz step) -----------
      frqBins[frqBinIndex] = settings.IF \
                             - settings.acqSearchBand/2*1000 \
                             + 0.5e3*frqBinIndex

      # Shift the signal in the frequency domain to remove the carrier
      # i.e. mix down to baseband
      shift = int((len(signal1_ft) / settings.samplingFreq) * frqBins[frqBinIndex])
      signal1_ft_bb = np.append(signal1_ft[shift:], signal1_ft[:shift])
      signal2_ft_bb = np.append(signal2_ft[shift:], signal2_ft[:shift])

      # Multiplication in frequency <-> correlation in time
      corr_ft1[:] = signal1_ft_bb * ca_code_ft_conj
      corr_ft2[:] = signal2_ft_bb * ca_code_ft_conj

      # Perform inverse Fourier transform to obtain correlation results
      corr_ifft1.execute()
      corr_ifft2.execute()
      # Find the correlation amplitude
      acq_result1 = np.abs(corr1)
      acq_result2 = np.abs(corr2)

      # Use the signal with the largest correlation peak as the result as one of
      # the signals may contain a nav bit edge. Square the result to find the
      # correlation power.
      if (np.max(acq_result1) > np.max(acq_result1)):
        results[frqBinIndex] = np.square(acq_result1)
      else:
        results[frqBinIndex] = np.square(acq_result2)

    # Find the correlation peak power, frequency and code phase
    peakSize = np.max(results)
    frequencyBinIndex, codePhase = np.unravel_index(results.argmax(), results.shape)

    #--- Find 1 chip wide C/A code phase exclude range around the peak
    samplesPerCodeChip = int(round(settings.samplingFreq \
                                   / settings.codeFreqBasis))
    excludeRangeIndex1 = codePhase - samplesPerCodeChip
    excludeRangeIndex2 = codePhase + samplesPerCodeChip
    #print codePhase, excludeRangeIndex1, excludeRangeIndex2, len(results)
    #--- Correct C/A code phase exclude range if the range includes
    #--- array boundaries
    if (excludeRangeIndex1 < 1):
      #codePhaseRange = range(excludeRangeIndex2,samplesPerCode+excludeRangeIndex1+1)
      secondPeakSize = np.max(results[frequencyBinIndex][excludeRangeIndex2:samplesPerCode+excludeRangeIndex1+1])
    elif (excludeRangeIndex2 >= (samplesPerCode-1)):
      #codePhaseRange = range(excludeRangeIndex2-samplesPerCode,excludeRangeIndex1+1)
      secondPeakSize = np.max(results[frequencyBinIndex][excludeRangeIndex2-samplesPerCode:excludeRangeIndex1+1])
    else:
      #codePhaseRange = np.concatenate((range(0,excludeRangeIndex1+1),\
                                       #range(excludeRangeIndex2,samplesPerCode)))
      secondPeakSize = max(
          np.max(results[frequencyBinIndex][:excludeRangeIndex1+1]),
          np.max(results[frequencyBinIndex][excludeRangeIndex2:])
      )
    #Find the second highest correlation peak in the same freq bin
    #secondPeakSize = 0
    #for i in codePhaseRange:
      #if (secondPeakSize < results[frequencyBinIndex][i]):
        #secondPeakSize = results[frequencyBinIndex][i]
    #secondPeakSize = np.max(results[frequencyBinIndex])

    SNR = peakSize/secondPeakSize

    #If the result is above the threshold, then we have acquired the satellite
    if (SNR > settings.acqThreshold):
      #Fine resolution frequency search
      #Generate 8msc long C/A codes sequence for given PRN
      caCode = np.array(generateCAcode(PRN))
      #codeValueIndex = np.array([int(math.floor(ts*i*settings.codeFreqBasis)) for i in \
                                   #range(1,8*samplesPerCode+1)])

      codeValueIndex = np.arange(1.0, 8.0*samplesPerCode+1.0) * ts * settings.codeFreqBasis
      codeValueIndex = np.asarray(codeValueIndex, np.int)
      #longCaCode = np.array([caCode[i] for i in np.remainder(codeValueIndex,1023)])
      longCaCode = caCode[np.remainder(codeValueIndex,1023)]
      #Remove CA code modulation from the original signal
      #xCarrier = np.array([signal0DC[codePhase+i]*longCaCode[i] for i in range(0,8*samplesPerCode)])
      xCarrier = signal0DC[codePhase:][:8*samplesPerCode]*longCaCode[:8*samplesPerCode]
      #Find next highest power of 2 and increase by 8x
      fftNumPts = 8*(2**int(math.ceil(math.log(len(xCarrier),2))))
      #Compute the magnitude of the FFT, find the maximum, and the associated carrrier frequency
      #for some reason the output of this fft is different than Octave's, but they seem to
      #preeeeetty much reach the same conclusion for the best carrier frequency
      fftxc = np.abs(np.fft.fft(xCarrier,n=fftNumPts))
      uniqFftPts = int(math.ceil((fftNumPts+1)/2))
      #fftMax = 0
      #for i in range(4,uniqFftPts-5):
        #if (fftMax < fftxc[i]):
          #fftMax = fftxc[i]
          #fftMaxIndex = i
      #print fftMax, fftMaxIndex, len(fftxc)
      foo = fftxc[4:uniqFftPts-5]
      fftMax = np.max(foo)
      fftMaxIndex = np.argmax(foo) + 4
      #print fftMax, fftMaxIndex, len(foo)
      #fftFreqBins = np.array([i*settings.samplingFreq/fftNumPts for i in range(uniqFftPts)])
      fftFreqBins = np.arange(uniqFftPts) * settings.samplingFreq/fftNumPts
      #Save properties of the detected satellite signal
      acqResults += [AcquisitionResult(PRN,
                                       fftFreqBins[fftMaxIndex],
                                       codePhase,
                                       SNR)]
      #acqResults[PRN].carrFreq = fftFreqBins[fftMaxIndex]
      #acqResults[PRN].codePhase = codePhase
      #acqResults[PRN][1] = fftFreqBins[fftMaxIndex]
      #acqResults[PRN][2] = codePhase
      logger.debug("PRN %2d acquired: SNR %5.2f @ %6.1f, % 8.2f Hz" % \
          (PRN+1, SNR,
           float(codePhase)/samplesPerCodeChip,
           fftFreqBins[fftMaxIndex] - settings.IF))
    #If the result is NOT above the threshold, we haven't acquired the satellite
    else:
      #logger.debug("PRN %d not found." % PRN)
      pass
  #Acquisition is over

  # Save FFTW wisdom for later
  with open(wisdom_file, 'wb') as f:
    pickle.dump(pyfftw.export_wisdom(), f)

  logger.info("Acquisition finished")
  logger.info("Acquired %d satellites, PRNs: %s.", len(acqResults), [ar.PRN for ar in acqResults])

  return acqResults

class AcquisitionResult:
  def __init__(self, PRN, carrFreq, codePhase, SNR, status='T'):
    self.PRN          = PRN
    self.SNR          = SNR
    self.carrFreq     = carrFreq
    self.codePhase    = codePhase
    self.status       = status

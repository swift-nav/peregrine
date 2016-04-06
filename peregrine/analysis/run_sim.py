#!/usr/bin/env python

# Copyright (C) 2016 Swift Navigation Inc.
# Contact: Perttu Salmela <psalmela@exafore.com>
#
# This source is subject to the license found in the file 'LICENSE' which must
# be be distributed together with this source. All other rights reserved.
#
# THIS CODE AND INFORMATION IS PROVIDED "AS IS" WITHOUT WARRANTY OF ANY KIND,
# EITHER EXPRESSED OR IMPLIED, INCLUDING BUT NOT LIMITED TO THE IMPLIED
# WARRANTIES OF MERCHANTABILITY AND/OR FITNESS FOR A PARTICULAR PURPOSE.

import os
import sys
import argparse
import subprocess
import json
import datetime
import numpy
import peregrine.iqgen.bits.signals as signals
import numpy as np

IQ_DATA = "iqdata.bin"
TRACK_DATA = "track_res"
TRACK_RES_DATA = "track_res.json"


def runCmd(cmd):
  print cmd
  # Do not use shell=True for untrusted input!
  out = subprocess.check_output(cmd, shell=True)
  print out
  return out


def runIqGen(lens, snr, dop, acc):
  cmd = "python " + peregrinePath() + "/peregrine/iqgen/iqgen_main.py"
  cmd = cmd + " --gps-sv 1 --encoder 1bit --bands l1ca+l2c --message-type crc --profile low_rate"
  if float(acc) != 0.0:
    cmd = cmd + " --doppler-type linear --doppler-speed " + acc + " "
  elif float(dop) != 0.0:
    cmd = cmd + " --doppler-type const " + dop + " "
  else:
    cmd = cmd + " --doppler-type zero "
  cmd = cmd + " --snr " + snr + " --generate " + lens + " "
  cmd = cmd + " --output " + IQ_DATA + " "
  out = runCmd(cmd)
  lines = out.split('\n')
  cn0 = None
  l2dop = None
  l2chip = None
  for ln in lines:
    words = ln.split()
    if len(words) == 0:
      continue
    if words[0] == ".L2":
      cn0 = words[2]
    if words[0] == ".l2_doppler:":
      l2dop = words[1]
    if words[0] == ".l2_chip:":
      l2chip = words[1]
    if words[0] == ".SNR":
      if float(words[2]) != float(snr):
        print "snr unexpected"
        sys.exit(1)
  if cn0 == None or l2dop == None or l2chip == None:
    print "iqgen output parse error"
    sys.exit(1)
  return lens, snr, l2dop, acc, l2chip, cn0, cmd


def runTracker(dopp, cp, lens):
  cmd = "python " + peregrinePath() + \
      "/peregrine/analysis/tracking_loop.py -f 1bit_x2 -P 1 --profile low_rate "
  cmd = cmd + "-p " + cp + " -d " + dopp
  cmd = cmd + " -o " + TRACK_DATA + " "
  cmd = cmd + " -S l2c "
  cmd = cmd + IQ_DATA + " "
  out = runCmd(cmd)
  lines = out.split('\n')
  durationOk = False
  for ln in lines:
    words = ln.split()
    if len(words) == 0:
      continue
    if words[0] == "Time" and words[1] == "to" and words[2] == "process":
      if int(words[4]) / 1000 == int(lens):
        durationOk = True
  if not durationOk:
    print "Data duration mismatch"
    sys.exit(1)
  return cmd


def processTrackResults(acc):
  data = np.genfromtxt(TRACK_DATA + ".PRN-1.l2c",
                       dtype=float, delimiter=',', names=True)
  CN0 = data['CN0']
  dopp = data['carr_doppler']
  lock = data['lock_detect_outp']
  nsamples = len(CN0)
  acc = float(acc)

  avgCN0 = np.mean(CN0)
  lockRate = np.sum(lock) / nsamples

  dopErr = np.ndarray(shape=(1, len(dopp)), dtype=float)
  i = np.linspace(1, len(dopp), len(dopp), dtype=float)
  # Doppler - (i * 20 ms * acc Hz/s * L2/L1 Hz relation)
  dopErr = np.abs(dopp - i * 0.02 * acc *
                  (signals.GPS.L2C.CENTER_FREQUENCY_HZ / signals.GPS.L1CA.CENTER_FREQUENCY_HZ))
  maxDopErr = np.max(dopErr)
  sortedDopErr = np.sort(dopErr)
  ix1 = int(0.5 + 0.6827 * (len(sortedDopErr) - 1))
  ix2 = int(0.5 + 0.9545 * (len(sortedDopErr) - 1))
  ix3 = int(0.5 + 0.9973 * (len(sortedDopErr) - 1))
  dopSigma1 = sortedDopErr[ix1]
  dopSigma2 = sortedDopErr[ix2]
  dopSigma3 = sortedDopErr[ix3]

  return avgCN0, lockRate, dopSigma1, dopSigma2, dopSigma3, maxDopErr


def produce(lens, snr, dop, acc):
  lens = str(int(lens))
  snr = str(float(snr))
  dop = str(float(dop))
  acc = str(float(acc))
  lens, snr, l2dop, acc, l2chip, cn0, iqgenCmd = runIqGen(lens, snr, dop, acc)
  trackerCmd = runTracker(l2dop, l2chip, lens)
  avgCN0, lockRate, dopSigma1, dopSigma2, dopSigma3, maxDopErr = processTrackResults(
      acc)
  fpout = open(TRACK_RES_DATA, "a")
  d = datetime.datetime(2000, 1, 1)
  js = json.dumps({"stamp": d.utcnow().isoformat(),
                   "snr": snr,
                   "duration": float(lens),
                   "iqgencn0": float(cn0),
                   "l2dop": float(l2dop),
                   "l2chip": float(l2chip),
                   "acc": float(acc),
                   "avgcn0": avgCN0,
                   "lockrate": lockRate,
                   "dopSigma1": dopSigma1,
                   "dopSigma2": dopSigma2,
                   "dopSigma3": dopSigma3,
                   "dopMaxErr": maxDopErr,
                   "iqgencmd": iqgenCmd,
                   "trackcmd": trackerCmd},
                  sort_keys=True, indent=4, separators=(',', ': '))
  print js
  fpout.write(js + ',')
  fpout.close()

  return lockRate, dopSigma1, dopSigma2


def runCn0Range():
  length = 6                    # Duration (s)
  snrRng = range(-270, -350, -10)  # SNR for iqgen command. Unit 0.1 dBHz
  doppler = 0                   # Hz
  acceleration = 0.0            # Hz / s
  for snr in snrRng:
    lockRate, dopSigma1, dopSigma2 = produce(
        length, snr / 10.0, doppler, acceleration)


def runDynamicLockRate():
  # Run different accelerations for each CN0 bin
  length = 30                   # Duration (s)
  snrRng = range(-300, -200, 10)  # Unit 0.1 dBHz.
  # snrRng = range(-210,-200,10)  # Unit 0.1 dBHz.
  # Must run from low CN0 to high CN0
  doppler = 0                   # Hz
  accStep = 10                  # Size of single acceleration step (L1CA Hz/s)
  # Failure threshold. When it is reached, the next CN0 bin is tried
  lockRateThreshold = 0.68

  lockRate = 0.0
  bestAcc = 0.0 + 2 * accStep
  for snr in snrRng:
    # It should be at least as good as prev round
    # so start iterating acceleration from prev round
    # highest acceleration minus x.
    acc = max(0, bestAcc - 2 * accStep)
    lockRate = 0
    while True:
      bestLockRate = lockRate
      bestAcc = acc

      lockRate, dopSigma1, dopSigma2 = produce(
          length, snr / 10.0, doppler, acc)
      print "SNR", snr / 10.0, "ACC", acc, "LOCKRATE", lockRate
      if lockRate >= lockRateThreshold:
        acc = acc + accStep
      else:
        print "BEST ACC", bestAcc, "LOCKRATE", bestLockRate
        break


def runDynamicFreq():
  # Run different accelerations for each CN0 bin
  length = 30                   # Duration (s)
  snrRng = range(-300, -200, 10)  # Unit 0.1 dBHz.
  # Must run from low CN0 to high CN0
  doppler = 0                   # Hz
  accStep = 10                  # Size of single acceleration step (L1CA Hz/s)
  freqErrThreshold = 1.0 / (12 * 0.02)  # 1/12T, Tcoh=20 ms. Failure threshold.
  # When it is reached, the next CN0 bin is tried

  freqErr = 0.0  # 1-sigma
  bestAcc = 0.0 + 2 * accStep
  for snr in snrRng:
    # It should be at least as good as prev round
    # so start iterating acceleration from prev round
    # highest acceleration.
    acc = max(0, bestAcc - 2 * accStep)
    freqErr = 0
    while True:
      bestFreqErr = freqErr
      bestAcc = acc

      lockRate, dopSigma1, dopSigma2 = produce(
          length, snr / 10.0, doppler, acc)
      freqErr = dopSigma1
      print "SNR", snr / 10.0, "ACC", acc, "1-SIGMA", freqErr
      if freqErr <= freqErrThreshold:
        acc = acc + accStep
      else:
        print "BEST ACC", bestAcc, "1-SIGMA", bestFreqErr
        break


def peregrinePath():
  p = os.path.realpath(__file__)
  return os.path.split(os.path.split(os.path.split(p)[0])[0])[0]


def main():
  global TRACK_RES_DATA
  parser = argparse.ArgumentParser()
  parser.add_argument("-l", "--lockrate",
                      help="Simple lockrate vs. CN0",
                      action="store_true")
  parser.add_argument("-f", "--filename",
                      help="Output file which is appended. Default " + TRACK_RES_DATA)
  parser.add_argument("-d", "--dyn-lockrate",
                      help="Lockrate, acceleration, CN0",
                      action="store_true")
  parser.add_argument("-e", "--dyn-freq",
                      help="Fequency error, acceleration, CN0",
                      action="store_true")

  args = parser.parse_args()
  if args.filename:
    TRACK_RES_DATA = args.filename
  if args.lockrate:
    runCn0Range()
  elif args.dyn_lockrate:
    runDynamicLockRate()
  elif args.dyn_freq:
    runDynamicFreq()


if __name__ == '__main__':
  main()

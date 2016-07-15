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


class CfgClass:

  def __init__(self):
    self.IQ_DATA = "iqdata.bin"
    self.TRACK_DATA = "track_res"
    self.TRACK_RES_DATA = "track_res.json"
    self.BAND = 'l1ca' # "l2c"
    #self.fpgaSim = " "  # "--short-long-cycles "
    self.fpgaSim = "--short-long-cycles "

  def isL1CA(self):
    if "l1ca" == self.BAND:
      return True
    return False

  def __str__(self):
    s = "band:" + self.BAND + "\n"
    s = s + "fpga delay control simulation: " + self.fpgaSim
    return s


cfg = CfgClass()


def runCmd(cmd):
  print cmd
  # Do not use shell=True for untrusted input!
  try:
    out = subprocess.check_output(cmd, shell=True)
  except subprocess.CalledProcessError as e:
    # Peregrine exits with failure if acquisition fails.
    # Therefore handle error case
    print e.output
    return e.output, False

  print out
  return out, True


def runIqGen(lens, snr, dop, acc):
  cmd = "python " + peregrinePath() + "/peregrine/iqgen/iqgen_main.py"
  if cfg.isL1CA():
    cmd = cmd + " --gps-sv 1 --encoder 1bit --bands l1ca --message-type zero+one --profile low_rate"
  else:
    cmd = cmd + " --gps-sv 1 --encoder 1bit --bands l1ca+l2c --message-type zero+one --profile low_rate"

  if float(acc) != 0.0:
    cmd = cmd + " --doppler-type linear --doppler-speed " + acc + " "
  elif float(dop) != 0.0:
    cmd = cmd + " --doppler-type const " + dop + " "
  else:
    cmd = cmd + " --doppler-type zero "
  cmd = cmd + "--amplitude-type poly --amplitude-units snr-db --amplitude-a0 " + snr
  cmd = cmd + " --generate " + lens + " "

  cmd = cmd + " --output " + cfg.IQ_DATA + " "
  out, success = runCmd(cmd)
  if not success:
    print "iqgen failed"
    sys.exit(1)

  lines = out.split('\n')
  cn0 = None
  l_dop = None
  l_chip = None
  for ln in lines:
    words = ln.split()
    if len(words) == 0:
      continue
    if cfg.isL1CA():
      if words[0] == ".l1":
        cn0 = words[2]
      if words[0] == ".l1_doppler:":
        l_dop = words[1]
      if words[0] == ".l1_chip:":
        l_chip = words[1]
    else:
      if words[0] == ".l2":
        cn0 = words[2]
      if words[0] == ".l2_doppler:":
        l_dop = words[1]
      if words[0] == ".l2_chip:":
        l_chip = words[1]

    if words[0] == ".SNR":
      if float(words[2]) != float(snr):
        print "snr unexpected"
        sys.exit(1)
  if cn0 is None or l_dop is None or l_chip is None:
    print "iqgen output parse error"
    sys.exit(1)
  return lens, snr, l_dop, acc, l_chip, cn0, cmd


def runTracker(dopp, cp, lens):
  if cfg.isL1CA():
    cmd = "python " + peregrinePath() + \
          "/peregrine/analysis/tracking_loop.py -f 1bit -P 1 --profile low_rate --l1ca-profile med "
    # "--short-long-cycles " tracking loop corrections are taken in use in FPGA with a delay of 1 ms
    cmd = cmd + cfg.fpgaSim
    cmd = cmd + "-p " + cp + " -d " + dopp
    cmd = cmd + " -o " + cfg.TRACK_DATA + " "
    cmd = cmd + " -S l1ca "
    cmd = cmd + " --file " + cfg.IQ_DATA + " "

  else:
    cmd = "python " + peregrinePath() + \
          "/peregrine/analysis/tracking_loop.py -f 1bit_x2 -P 1 --profile low_rate --ms-to-process -1 "
    cmd = cmd + "-p " + cp + " -d " + dopp
    cmd = cmd + " -o " + cfg.TRACK_DATA + " "
    cmd = cmd + " -S l2c "
    cmd = cmd + " --file " + cfg.IQ_DATA + " "

  out, success = runCmd(cmd)
  lines = out.split('\n')
  # This is usefull if acquisition is run instead of
  # running tracking_loop.py directly
  if not success:
    for ln in lines:
      if ln.find("No satellites acquired"):
        # Acceptable failure
        return cmd, False
    # Unacceptable failure
    print "Acquisition/tracking failed unexpectedly"
    sys.exit(1)

  durationOk = False
  for ln in lines:
    words = ln.split()
    if len(words) == 0:
      continue
    if words[0] == "Time" and words[1] == "to" and words[2] == "process":
      if round(float(words[4])) == int(lens):
        durationOk = True
  if not durationOk:
    print "Data duration mismatch"
    sys.exit(1)
  return cmd, True


def processTrackResults(acc):
  if cfg.isL1CA():
    data = np.genfromtxt(cfg.TRACK_DATA + ".PRN-1.l1ca",
                         dtype=float, delimiter=',', names=True)
  else:
    data = np.genfromtxt(cfg.TRACK_DATA + ".PRN-1.l2c",
                         dtype=float, delimiter=',', names=True)
  CN0 = data['CN0']
  dopp = data['carr_doppler']
  lock = data['lock_detect_outp']
  coherent_ms = data['coherent_ms']
  acc = float(acc)

  avgCN0 = np.mean(CN0)
  lockRate = np.sum([a * b for a, b in zip(lock, coherent_ms)]) / np.sum(coherent_ms)

  dopErr = np.ndarray(shape=(1, len(dopp)), dtype=float)

  if cfg.isL1CA():
    ms_tracked = data['ms_tracked']
    dopErr = np.abs(dopp - ms_tracked / 1000.0 * acc)
  else:
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
  lens, snr, l_dop, acc, l_chip, cn0, iqgenCmd = runIqGen(lens, snr, dop, acc)
  trackerCmd, trackSuccess = runTracker(l_dop, l_chip, lens)
  if trackSuccess:
    avgCN0, lockRate, dopSigma1, dopSigma2, dopSigma3, maxDopErr = processTrackResults(
        acc)
    fpout = open(cfg.TRACK_RES_DATA, "a")
    d = datetime.datetime(2000, 1, 1)
    js = json.dumps({"stamp": d.utcnow().isoformat(),
                     "snr": snr,
                     "duration": float(lens),
                     "iqgencn0": float(cn0),
                     "l_dop": float(l_dop),
                     "l_chip": float(l_chip),
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
    return lockRate, dopSigma1, dopSigma2, trackSuccess
  else:
    return 0, 0, 0, trackSuccess


def runCn0Range():
  length = 30                    # Duration (s)
  snrRng = range(-200, -350, -10)  # SNR for iqgen command. Unit 0.1 dBHz
  doppler = 0                   # Hz
  acceleration = 0.0            # Hz / s
  for snr in snrRng:
    lockRate, dopSigma1, dopSigma2, success = produce(
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

      lockRate, dopSigma1, dopSigma2, success = produce(
          length, snr / 10.0, doppler, acc)
      print "SNR", snr / 10.0, "ACC", acc, "LOCKRATE", lockRate
      if lockRate >= lockRateThreshold and success:
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
  if cfg.isL1CA():
    # 1/12T, Tcoh=5 ms. Failure threshold.
    freqErrThreshold = 1.0 / (12 * 0.005)
  else:
    # 1/12T, Tcoh=20 ms. Failure threshold.
    freqErrThreshold = 1.0 / (12 * 0.02)
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

      lockRate, dopSigma1, dopSigma2, trackSuccess = produce(
          length, snr / 10.0, doppler, acc)
      freqErr = dopSigma1
      print "SNR", snr / 10.0, "ACC", acc, "1-SIGMA", freqErr
      if freqErr <= freqErrThreshold and trackSuccess:
        acc = acc + accStep
      else:
        print "BEST ACC", bestAcc, "1-SIGMA", bestFreqErr
        break


def peregrinePath():
  p = os.path.realpath(__file__)
  return os.path.split(os.path.split(os.path.split(p)[0])[0])[0]


def main():
  parser = argparse.ArgumentParser()
  parser.add_argument("-l", "--lockrate",
                      help="Simple lockrate vs. CN0",
                      action="store_true")
  parser.add_argument("-f", "--filename",
                      help="Output file which is appended. Default " + cfg.TRACK_RES_DATA)
  parser.add_argument("-d", "--dyn-lockrate",
                      help="Lockrate, acceleration, CN0",
                      action="store_true")
  parser.add_argument("-e", "--dyn-freq",
                      help="Fequency error, acceleration, CN0",
                      action="store_true")
  parser.add_argument("-b", "--band",
                      help="l1ca or l2c (default)")
  parser.add_argument("-s", "--short-long-cycles",
                      help="FPGA delay control simulation",
                      action="store_true")

  args = parser.parse_args()
  if args.filename:
    cfg.TRACK_RES_DATA = args.filename
  if args.band:
    cfg.BAND = args.band
  if args.short_long_cycles:
    cfg.fpgaSim = "--short-long-cycles "

  if args.lockrate:
    runCn0Range()
  elif args.dyn_lockrate:
    runDynamicLockRate()
  elif args.dyn_freq:
    runDynamicFreq()


if __name__ == '__main__':
  main()

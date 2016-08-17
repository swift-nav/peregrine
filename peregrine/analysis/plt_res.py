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
import json
import numpy as np
import matplotlib.pyplot as plt
import peregrine.gps_constants


class CfgClass:

  def __init__(self):
    # self.CN0STRING = "avgcn0"     # CN0 from tracking
    self.CN0STRING = "iqgencn0"  # CN0 from iqgen
    self.BAND = "l2c"

  def isL1CA(self):
    if "l1ca" == self.BAND:
      return True
    return False

cfg = CfgClass()


def sigmaFreqPlot(filename):
  fp = open(filename, "r")
  s = fp.read()
  fp.close()
  # Append '[', remove the last ',\n' and append the last ']'
  s = '[' + s[:-1] + ']'
  jsarray = json.loads(s)
  r = []
  for j in jsarray:
    r.append((j["dopSigma1"], j[cfg.CN0STRING]))
  r = sorted(r, key=lambda x: x[1])

  dopSigma1 = map(lambda x: x[0], r)
  avgcn0 = map(lambda x: x[1], r)

  fig = plt.figure()
  plt.plot(avgcn0, dopSigma1, 'o-')
  plt.xlabel('CN0')
  plt.ylabel('Doppler sigma-1 error (Hz)')
  plt.grid(True)
  plt.show()


def lockrateCn0Plot(filename):
  fp = open(filename, "r")
  s = fp.read()
  fp.close()
  # Append '[', remove the last ',\n' and append the last ']'
  s = '[' + s[:-1] + ']'
  jsarray = json.loads(s)
  r = []
  for j in jsarray:
    r.append((j["lockrate"], j[cfg.CN0STRING]))
  r = sorted(r, key=lambda x: x[1])

  lockrate = map(lambda x: x[0], r)
  avgcn0 = map(lambda x: x[1], r)

  x, y = zip(*sorted((xVal, np.mean([yVal for a, yVal in zip(
      avgcn0, lockrate) if xVal == a])) for xVal in set(avgcn0)))

  fig = plt.figure()
  plt.plot(avgcn0, lockrate, 'o')
  plt.plot(x, y, '-')
  plt.xlabel('CN0')
  plt.ylabel('PLL lock rate')
  #plt.scatter(avgcn0, lockrate)
  plt.grid(True)
  plt.show()


def dynamicAccPlot(filename, mode):
  GRAV_G = 9.80665  # m/s^2
  HzToMps = (peregrine.gps_constants.c / peregrine.gps_constants.l1)
  HzToG = HzToMps / GRAV_G
  fp = open(filename, "r")
  s = fp.read()
  fp.close()
  # Append '[', remove the last ',\n' and append the last ']'
  s = '[' + s[:-1] + ']'
  jsarray = json.loads(s)

  minCN0 = 65535.0
  maxCN0 = 0.0
  r = []
  for j in jsarray:
    minCN0 = min(minCN0, j[cfg.CN0STRING])
    maxCN0 = max(maxCN0, j[cfg.CN0STRING])
    #r.append( (float(j["acc"]),j[CN0STRING]) )
  #accVecAll = map(lambda x:x[0], r)
  #cn0VecAll = map(lambda x:x[1], r)

  cn0Range = range(int(minCN0 - 1), int(maxCN0 + 1))

  fig = plt.figure()

  r = []
  if cfg.isL1CA():
    Tcoh = 0.005  # Integration time 5 ms
  else:
    Tcoh = 0.02  # Integration time 20 ms

  for cn0bin in cn0Range:
    bestAcc = -1000.0
    bestCN0 = 0
    print "BIN", cn0bin,
    for j in jsarray:
      cn0 = j[cfg.CN0STRING]
      lockrate = j["lockrate"]
      doperr = j["dopSigma1"]
      acc = float(j["acc"]) * HzToG
      if cn0bin - 0.5 <= cn0 and cn0 < cn0bin + 0.5:
        if acc > bestAcc:
          if mode == "lockrate" and lockrate >= 0.68:
            bestAcc = acc
            bestCN0 = cn0
            plt.plot(bestCN0, bestAcc, 'bo')
          # 1/12T, Tcoh=20 ms, Tcoh=5 ms
          elif mode == "doperr" and doperr <= 1.0 / (12 * Tcoh):
            bestAcc = acc
            bestCN0 = cn0
            plt.plot(bestCN0, bestAcc, 'bo')
    if bestAcc >= 0:
      print "BEST", bestAcc, bestCN0
      r.append((bestAcc, bestCN0))

  bestAcc = map(lambda x: x[0], r)
  bestCN0 = map(lambda x: x[1], r)

  print "ACC", bestAcc
  print "CN0", bestCN0

  #plt.plot(cn0VecAll, accVecAll, 'bo')
  plt.plot(bestCN0, bestAcc, 'r.-')
  plt.xlabel('CN0')
  plt.ylabel('Acceleration (g)')
  plt.grid(True)
  if mode == "lockrate":
    plt.title("PLL lock rate >= 0.68 (1-sigma)")
  elif mode == "doperr":
    if cfg.isL1CA():
      plt.title("Doppler 1-sigma error <= 1/(12*0.005) = 16.7 Hz")
    else:
      plt.title("Doppler 1-sigma error <= 1/(12*0.02) = 4.2 Hz")
  plt.show()


def main():
  parser = argparse.ArgumentParser()
  parser.add_argument("-l", "--lockrate",
                      help="Simple lockrate vs. CN0 plot",
                      action="store_true")
  parser.add_argument("-s", "--sigma-freq",
                      help="Freq error sigma-1",
                      action="store_true")
  parser.add_argument("-f", "--filename",
                      help="json file to read")
  parser.add_argument("-d", "--dyn-acc-lockrate",
                      help="Lockrate acceleration tolerance vs. CN0",
                      action="store_true")
  parser.add_argument("-e", "--dyn-acc-dop",
                      help="x-sigma Doppler error acceleration tolerance vs. CN0",
                      action="store_true")
  parser.add_argument("-b", "--band",
                      help="l1ca or l2c (default)")

  args = parser.parse_args()
  if args.band:
    cfg.BAND = args.band
  if args.lockrate:
    lockrateCn0Plot(args.filename)
  elif args.dyn_acc_lockrate:
    dynamicAccPlot(args.filename, "lockrate")
  elif args.dyn_acc_dop:
    dynamicAccPlot(args.filename, "doperr")
  elif args.sigma_freq:
    sigmaFreqPlot(args.filename)

if __name__ == '__main__':
  main()

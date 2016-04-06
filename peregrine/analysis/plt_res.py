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
import numpy
import matplotlib.pyplot as plt

CN0STRING = "avgcn0"     # CN0 from tracking
# CN0STRING="iqgencn0"  # CN0 from iqgen


def sigmaFreqPlot(filename):
  fp = open(filename, "r")
  s = fp.read()
  fp.close()
  # Append '[', remove the last ',\n' and append the last ']'
  s = '[' + s[:-1] + ']'
  jsarray = json.loads(s)
  r = []
  for j in jsarray:
    r.append((j["dopSigma1"], j[CN0STRING]))
  r = sorted(r, key=lambda x: x[1])

  dopSigma1 = map(lambda x: x[0], r)
  avgcn0 = map(lambda x: x[1], r)

  fig = plt.figure()
  plt.plot(avgcn0, dopSigma1, 'o-')
  plt.xlabel('CN0')
  plt.ylabel('Doppler sigma-1 error (Hz)')
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
    r.append((j["lockrate"], j[CN0STRING]))
  r = sorted(r, key=lambda x: x[1])

  lockrate = map(lambda x: x[0], r)
  avgcn0 = map(lambda x: x[1], r)

  fig = plt.figure()
  plt.plot(avgcn0, lockrate, 'o-')
  plt.xlabel('CN0')
  plt.ylabel('PLL lock rate')
  #plt.scatter(avgcn0, lockrate)
  plt.show()


def dynamicAccPlot(filename, mode):
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
    minCN0 = min(minCN0, j[CN0STRING])
    maxCN0 = max(maxCN0, j[CN0STRING])
    #r.append( (float(j["acc"]),j[CN0STRING]) )
  #accVecAll = map(lambda x:x[0], r)
  #cn0VecAll = map(lambda x:x[1], r)

  cn0Range = range(int(minCN0 - 1), int(maxCN0 + 1))

  fig = plt.figure()

  r = []
  for cn0bin in cn0Range:
    bestAcc = -1000.0
    bestCN0 = 0
    print "BIN", cn0bin,
    for j in jsarray:
      cn0 = j[CN0STRING]
      lockrate = j["lockrate"]
      doperr = j["dopSigma1"]
      acc = float(j["acc"])
      if cn0bin - 0.5 <= cn0 and cn0 < cn0bin + 0.5:
        if acc > bestAcc:
          if mode == "lockrate" and lockrate >= 0.68:
            bestAcc = acc
            bestCN0 = cn0
            plt.plot(bestCN0, bestAcc, 'bo')
          # 1/12T, Tcoh=20 ms
          elif mode == "doperr" and doperr <= 1.0 / (12 * 0.02):
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
  plt.ylabel('Acceleration Hz/s')
  plt.grid()
  if mode == "lockrate":
    plt.title("PLL lock rate >= 0.68 (1-sigma)")
  elif mode == "doperr":
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

  args = parser.parse_args()
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

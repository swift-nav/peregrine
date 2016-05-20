#!/usr/bin/env python

# Copyright (C) 2016 Swift Navigation Inc.
# Contact: Adel Mamin <adelm@exafore.com>
#
# This source is subject to the license found in the file 'LICENSE' which must
# be be distributed together with this source. All other rights reserved.
#
# THIS CODE AND INFORMATION IS PROVIDED "AS IS" WITHOUT WARRANTY OF ANY KIND,
# EITHER EXPRESSED OR IMPLIED, INCLUDING BUT NOT LIMITED TO THE IMPLIED
# WARRANTIES OF MERCHANTABILITY AND/OR FITNESS FOR A PARTICULAR PURPOSE.

import numpy as np
import matplotlib.pyplot as plt
import argparse
from peregrine import defaults

def main():
  parser = argparse.ArgumentParser()

  parser.add_argument("-f", "--file", default="tracking_res.csv",
                      help="the input CSV file to process")

  parser.add_argument("-p", "--par-to-print", default="CN0",
                      help="parameter to print")

  parser.add_argument("--profile",
                      choices=['peregrine', 'custom_rate', 'low_rate',
                               'normal_rate', 'piksi_v3', 'high_rate'],
                      metavar='PROFILE',
                      help="L1C/A & L2C IF + sampling frequency profile"
                      "('peregrine'/'custom_rate', 'low_rate', "
                      "'normal_rate', 'piksi_v3', 'high_rate')",
                      default='peregrine')

  args = parser.parse_args()

  if args.profile == 'peregrine' or args.profile == 'custom_rate':
    freq_profile = defaults.freq_profile_peregrine
  elif args.profile == 'low_rate':
    freq_profile = defaults.freq_profile_low_rate
  elif args.profile == 'normal_rate':
    freq_profile = defaults.freq_profile_normal_rate
  elif args.profile == 'high_rate':
    freq_profile = defaults.freq_profile_high_rate
  else:
    raise NotImplementedError()

  fig = plt.figure()
  plt.title(args.par_to_print.replace('_', ' ').title() + ' vs Time')
  ax1 = fig.add_subplot(111)

  plt.ylabel(args.par_to_print.replace('_', ' ').title(), color='b')
  plt.xlabel('Time [s]')

  data = np.genfromtxt(args.file, dtype=float, delimiter=',', names=True)

  time_stamps = np.array(data['sample_index'])
  time_stamps = time_stamps - data['sample_index'][0]
  time_stamps = time_stamps / freq_profile['sampling_freq']
  
  plt.plot(time_stamps, np.array(data[args.par_to_print]), 'r.')

  plt.legend(loc='upper right')

  plt.grid()
  plt.axis('tight')
  plt.show()

if __name__ == '__main__':
  main()

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

  parser.add_argument("--no-toolbar",
                      action='store_true',
                      help="Disable toolbar")

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

  if args.no_toolbar:
    plt.rcParams['toolbar'] = 'None'

  params = [x.strip() for x in args.par_to_print.split(',')]
  params_num = len(params)
  if params_num == 1:
    params.append('111')

  params = [tuple(params[i:i + 2]) for i in range(0, params_num, 2)]

  data = np.genfromtxt(args.file, dtype=float, delimiter=',', names=True)

  time_stamps = np.array(data['sample'])
  time_stamps = time_stamps - data['sample'][0]
  time_stamps = time_stamps / freq_profile['sampling_freq']
  time_stamp_min = min(time_stamps)
  time_stamp_max = max(time_stamps)

  fig = plt.figure(figsize=(11, 15))
  fig.patch.set_facecolor('white')
  plt.subplots_adjust(wspace=0.25, hspace=0.75)

  for (par_to_print, layout) in params:
    sub = fig.add_subplot(layout)
    sub.set_title(par_to_print.replace('_', ' ').title() + ' vs Time')
    sub.grid()
    sub.set_xlim([time_stamp_min, time_stamp_max])

    sub.set_ylabel(par_to_print.replace('_', ' ').title(), color='b')
    sub.set_xlabel('Time [s]')
    sub.legend(loc='upper right')

    sub.plot(time_stamps, np.array(data[par_to_print]), 'r.')

  plt.axis('tight')
  plt.show()

if __name__ == '__main__':
  main()

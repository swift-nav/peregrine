# Copyright (C) 2016 Swift Navigation Inc.
# Contact: Adel Mamin <adelm@exafore.com>
#
# This source is subject to the license found in the file 'LICENSE' which must
# be be distributed together with this source. All other rights reserved.
#
# THIS CODE AND INFORMATION IS PROVIDED "AS IS" WITHOUT WARRANTY OF ANY KIND,
# EITHER EXPRESSED OR IMPLIED, INCLUDING BUT NOT LIMITED TO THE IMPLIED
# WARRANTIES OF MERCHANTABILITY AND/OR FITNESS FOR A PARTICULAR PURPOSE.

import os
import argparse
from peregrine.samples import load_samples
from peregrine.acquisition import AcquisitionResult
from peregrine import defaults
from peregrine.log import default_logging_config
from peregrine.tracking import track
from peregrine.gps_constants import L1CA, L2C
from peregrine.initSettings import initSettings

def dump_tracking_results_for_analysis(output_file, track_results):
  output_filename, output_file_extension = os.path.splitext(output_file)

  for j in range(len(track_results)):

    if len(track_results) > 1:
      # mangle the result file name with the tracked signal name
      filename = output_filename + \
                 (".%s.%d" % (track_results[j].signal, track_results[j].prn + 1)) +\
                 output_file_extension
    else:
      filename = output_file

    with open(filename, 'w') as f1:
      f1.write("IF,doppler_phase,carr_doppler,code_phase,code_freq,"
               "CN0,E_I,E_Q,P_I,P_Q,L_I,L_Q,"
               "lock_detect_outp,lock_detect_outo,"
               "lock_detect_pcount1,lock_detect_pcount2,"
               "lock_detect_lpfi,lock_detect_lpfq,alias_detect_err_hz\n")
      for i in range(len(track_results[j].carr_phase)):
        f1.write("%s," % track_results[j].IF)
        f1.write("%s," % track_results[j].carr_phase[i])
        f1.write("%s," % (track_results[j].carr_freq[i] -
                          track_results[j].IF))
        f1.write("%s," % track_results[j].code_phase[i])
        f1.write("%s," % track_results[j].code_freq[i])
        f1.write("%s," % track_results[j].cn0[i])
        f1.write("%s," % track_results[j].E[i].real)
        f1.write("%s," % track_results[j].E[i].imag)
        f1.write("%s," % track_results[j].P[i].real)
        f1.write("%s," % track_results[j].P[i].imag)
        f1.write("%s," % track_results[j].L[i].real)
        f1.write("%s," % track_results[j].L[i].imag)
        f1.write("%s," % track_results[j].lock_detect_outp[i])
        f1.write("%s," % track_results[j].lock_detect_outo[i])
        f1.write("%s," % track_results[j].lock_detect_pcount1[i])
        f1.write("%s," % track_results[j].lock_detect_pcount2[i])
        f1.write("%s," % track_results[j].lock_detect_lpfi[i])
        f1.write("%s," % track_results[j].lock_detect_lpfq[i])
        f1.write("%s\n" % track_results[j].alias_detect_err_hz[i])

def main():
  default_logging_config()

  parser = argparse.ArgumentParser()
  parser.add_argument("file",
                      help = "the sample data file to process")

  parser.add_argument("-f", "--file-format",
                      help = "the format of the sample data file "
                      "('piksi', 'int8', '1bit', '1bitrev', "
                      "'1bit_x2', '2bits', '2bits_x2', '2bits_x4')")

  parser.add_argument("-t", "--ms-to-track",
                      help = "the number of milliseconds to track."
                      "(-1: use all available data",
                      default = "-1")

  parser.add_argument("-I", "--IF",
                      help = "intermediate frequency [Hz]. ")

  parser.add_argument("-s", "--sampling-freq",
                      help = "sampling frequency [Hz]. ");

  parser.add_argument("--profile",
                      help="L1C/A & L2C IF + sampling frequency profile"
                      "('peregrine', 'low_rate', 'normal_rate' (piksi_v3)"
                      "'high_rate')",
                      default = 'peregrine')

  parser.add_argument("-P", "--prn",
                      help = "PRN to track. ")

  parser.add_argument("-p", "--code-phase",
                      help = "code phase [chips]. ")

  parser.add_argument("-d", "--carr-doppler",
                      help = "carrier Doppler frequency [Hz]. ")

  parser.add_argument("-o", "--output-file", default = "track.csv",
                      help = "Track results file name. "
                      "Default: %s" % "track.csv")

  parser.add_argument("-S", "--signal",
                      choices = [L1CA, L2C],
                      help = "Signal type (l1ca / l2c)")

  args = parser.parse_args()

  if args.profile == 'peregrine':
    freq_profile = defaults.freq_profile_peregrine
  elif args.profile == 'low_rate':
    freq_profile = defaults.freq_profile_low_rate
  elif args.profile == 'normal_rate':
    freq_profile = defaults.freq_profile_normal_rate
  elif args.profile == 'high_rate':
    freq_profile = defaults.freq_profile_high_rate
  else:
    raise NotImplementedError()

  isL1CA = (args.signal == L1CA)
  isL2C = (args.signal == L2C)

  if isL1CA:
    signal = L1CA
    IF = freq_profile['GPS_L1_IF']
  elif isL2C:
    signal = L2C
    IF = freq_profile['GPS_L2_IF']
  else:
    raise NotImplementedError()

  if args.IF is not None:
    IF = float(args.IF)

  if args.sampling_freq is not None:
    sampling_freq = float(args.sampling_freq)  # [Hz]
  else:
    sampling_freq = freq_profile['sampling_freq'] # [Hz]

  # Initialize constants, settings
  settings = initSettings(freq_profile)

  settings.fileName = args.file

  samplesPerCode = int(round(sampling_freq /
                             (settings.codeFreqBasis / settings.codeLength)))

  carr_doppler = float(args.carr_doppler)
  code_phase = float(args.code_phase)
  prn = int(args.prn) - 1

  ms_to_track = int(args.ms_to_track)

  if ms_to_track > 0:
    samples_num = sampling_freq * 1e-3 * ms_to_track
  else:
    samples_num = -1 # all available samples
  signals = load_samples(args.file,
                         int(samples_num),
                         0,  # skip samples
                         file_format = args.file_format)

  if ms_to_track < 0:
    # use all available data
    ms_to_track = int(1e3 * len(signals[0]) / sampling_freq)

  print "==================== Tracking parameters ============================="
  print "File:                                   %s" % args.file
  print "File format:                            %s" % args.file_format
  print "PRN to track [1-32]:                    %s" % args.prn
  print "Time to process [ms]:                   %s" % ms_to_track
  print "IF [Hz]:                                %f" % IF
  print "Sampling frequency [Hz]:                %f" % sampling_freq
  print "Initial carrier Doppler frequency [Hz]: %s" % carr_doppler
  print "Initial code phase [chips]:             %s" % code_phase
  print "Track results file name:                %s" % args.output_file
  print "Signal:                                 %s" % args.signal
  print "======================================================================"

  channel = 0
  if len(signals) > 1:
    if isL1CA:
      channel = 0
    else:
      channel = 1
    pass

  acq_result = AcquisitionResult(prn = prn,
                    snr = 25, # dB
                    carr_freq = IF + carr_doppler,
                    doppler = carr_doppler,
                    code_phase = code_phase,
                    status = 'A',
                    signal = signal,
                    sample_channel = channel,
                    sample_index = 0)

  track_results = track(samples = [
    {'data': signals[defaults.sample_channel_GPS_L1], 'IF': IF},
    {'data': signals[defaults.sample_channel_GPS_L2], 'IF': IF} ],
    channels = [acq_result],
    ms_to_track = ms_to_track,
    sampling_freq = sampling_freq,  # [Hz]
    l2c_handover = False)

  dump_tracking_results_for_analysis(args.output_file, track_results)

if __name__ == '__main__':
  main()

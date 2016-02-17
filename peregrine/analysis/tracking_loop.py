# Copyright (C) 2016 Swift Navigation Inc.
# Contact: Adel Mamin <adelm@exafore.com>
#
# This source is subject to the license found in the file 'LICENSE' which must
# be be distributed together with this source. All other rights reserved.
#
# THIS CODE AND INFORMATION IS PROVIDED "AS IS" WITHOUT WARRANTY OF ANY KIND,
# EITHER EXPRESSED OR IMPLIED, INCLUDING BUT NOT LIMITED TO THE IMPLIED
# WARRANTIES OF MERCHANTABILITY AND/OR FITNESS FOR A PARTICULAR PURPOSE.

import argparse
from peregrine.samples import load_samples
from peregrine.acquisition import AcquisitionResult
from peregrine import defaults
from peregrine.log import default_logging_config
from peregrine.tracking import track

from peregrine.initSettings import initSettings

def main():
  default_logging_config()

  # Initialize constants, settings
  settings = initSettings()

  parser = argparse.ArgumentParser()
  parser.add_argument("file",
                      help="the sample data file to process")

  parser.add_argument("-f", "--file-format",
                      help="the format of the sample data file "
                      "(e.g. 'piksi', 'int8', '1bit', '1bitrev')")

  parser.add_argument("-t", "--ms-to-track",
                      help="the number of milliseconds to process. ")

  parser.add_argument("-I", "--IF",
                      help="intermediate frequency [Hz]. ")

  parser.add_argument("-s", "--sampling-freq",
                      help="sampling frequency [Hz]. ");

  parser.add_argument("-P", "--prn",
                      help="PRN to track. ")

  parser.add_argument("-p", "--code-phase",
                      help="code phase [chips]. ")

  parser.add_argument("-d", "--carr-doppler",
                      help="carrier Doppler frequency [Hz]. ")

  parser.add_argument("-o", "--output-file", default="track.csv",
                      help="Track results file name. "
                      "Default: %s" % "track.csv")

  parser.add_argument("-S", "--signal",
                      choices=["l1ca", "l2c"],
                      help="Signal type (l1ca / l2c)")

  args = parser.parse_args()
  settings.fileName = args.file

  samplesPerCode = int(round(settings.samplingFreq /
                             (settings.codeFreqBasis / settings.codeLength)))

  IF = float(args.IF)
  carr_doppler = float(args.carr_doppler)
  code_phase = float(args.code_phase)
  prn = int(args.prn) - 1

  ms_to_track = int(args.ms_to_track)
  sampling_freq = float(args.sampling_freq)  # [Hz]

  if args.signal == "l1ca":
    acq_result = AcquisitionResult(prn = prn,
                      snr = 25, # dB
                      carr_freq = IF + carr_doppler,
                      doppler = carr_doppler,
                      code_phase = code_phase,
                      status = 'A',
                      signal = 'l1ca')
  else: # L2C signal clause
    acq_result = AcquisitionResult(prn = prn,
                      snr = 25, # dB
                      carr_freq = IF + carr_doppler,
                      doppler = carr_doppler,
                      code_phase = code_phase,
                      status = 'A',
                      signal = 'l2c')

  print "==================== Tracking parameters ============================="
  print "File:                                   %s" % args.file
  print "File format:                            %s" % args.file_format
  print "PRN to track [1-32]:                    %s" % args.prn
  print "Time to process [ms]:                   %s" % args.ms_to_track
  print "IF [Hz]:                                %s" % args.IF
  print "Sampling frequency [Hz]:                %s" % args.sampling_freq
  print "Initial carrier Doppler frequency [Hz]: %s" % carr_doppler
  print "Initial code phase [chips]:             %s" % code_phase
  print "Track results file name:                %s" % args.output_file
  print "Signal:                                 %s" % args.signal
  print "======================================================================"

  samples_num = int(args.sampling_freq) * 1e-3 * ms_to_track
  signals = load_samples(args.file,
                        int(samples_num),
                        0,  # skip samples
                        file_format=args.file_format)

  index = 0
  if len(signals) > 1:
    if args.signal == 'l1ca':
      index = 0
    else:
      index = 1
    pass

  track_results = track(samples=signals[index],
                        channels=[acq_result],
                        ms_to_track=ms_to_track,
                        sampling_freq=sampling_freq,  # [Hz]
                        chipping_rate=defaults.chipping_rate,
                        IF=IF)

  with open(args.output_file, 'w') as f1:
    f1.write("doppler_phase,carr_doppler,code_phase,code_freq,CN0,E_I,E_Q,P_I,P_Q,L_I,L_Q,lock_detect_outp,lock_detect_outo\n")
    for i in range(len(track_results[0].carr_phase)):
      f1.write("%s," % track_results[0].carr_phase[i])
      f1.write("%s," % (track_results[0].carr_freq[i] - IF))
      f1.write("%s," % track_results[0].code_phase[i])
      f1.write("%s," % track_results[0].code_freq[i])
      f1.write("%s," % track_results[0].cn0[i])
      f1.write("%s," % track_results[0].E[i].real)
      f1.write("%s," % track_results[0].E[i].imag)
      f1.write("%s," % track_results[0].P[i].real)
      f1.write("%s," % track_results[0].P[i].imag)
      f1.write("%s," % track_results[0].L[i].real)
      f1.write("%s," % track_results[0].L[i].imag)
      f1.write("%s," % track_results[0].lock_detect_outp[i])
      f1.write("%s\n" % track_results[0].lock_detect_outo[i])

if __name__ == '__main__':
  main()

# Copyright (C) 2014 Swift Navigation Inc.
#
# This source is subject to the license found in the file 'LICENSE' which must
# be be distributed together with this source. All other rights reserved.
#
# THIS CODE AND INFORMATION IS PROVIDED "AS IS" WITHOUT WARRANTY OF ANY KIND,
# EITHER EXPRESSED OR IMPLIED, INCLUDING BUT NOT LIMITED TO THE IMPLIED
# WARRANTIES OF MERCHANTABILITY AND/OR FITNESS FOR A PARTICULAR PURPOSE.

ms_to_track = 37*1e3
skip_samples = 1000
file_format = 'piksi'
IF = 4.092e6 # Hz
sampling_freq = 16.368e6 # Hz
chipping_rate = 1.023e6 # Hz
code_length = 1023 # chips

code_period = code_length / chipping_rate
samples_per_code = code_period * sampling_freq

l1ca_stage1_loop_filter_params = {
    "loop_freq"    : 1e3,       # loop frequency [Hz]
    "code_bw"      : 1,         # Code loop NBW
    "code_zeta"    : 0.707,     # Code loop zeta
    "code_k"       : 1,         # Code loop k
    "carr_to_code" : 0,         # Carrier-to-code freq ratio (carrier aiding)
    "carr_bw"      : 25,        # Carrier loop NBW
    "carr_zeta"    : 0.707,     # Carrier loop zeta
    "carr_k"       : 1,         # Carrier loop k
    "carr_freq_b1" : 5}         # Carrier loop aiding_igain

l2c_loop_filter_params = {
    "loop_freq"    : 50,        # loop frequency [Hz]
    "code_bw"      : 1,         # Code loop NBW
    "code_zeta"    : 0.707,     # Code loop zeta
    "code_k"       : 1,         # Code loop k
    "carr_to_code" : 0,         # Carrier-to-code freq ratio (carrier aiding)
    "carr_bw"      : 13,        # Carrier loop NBW
    "carr_zeta"    : 0.707,     # Carrier loop zeta
    "carr_k"       : 1,         # Carrier loop k
    "carr_freq_b1" : 5}         # Carrier loop aiding_igain


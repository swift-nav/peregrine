# Copyright (C) 2014 Swift Navigation Inc.
# Contact: Adel Mamin <adelm@exafore.com>
#
# This source is subject to the license found in the file 'LICENSE' which must
# be be distributed together with this source. All other rights reserved.
#
# THIS CODE AND INFORMATION IS PROVIDED "AS IS" WITHOUT WARRANTY OF ANY KIND,
# EITHER EXPRESSED OR IMPLIED, INCLUDING BUT NOT LIMITED TO THE IMPLIED
# WARRANTIES OF MERCHANTABILITY AND/OR FITNESS FOR A PARTICULAR PURPOSE.

ms_to_track = 37 * 1e3
skip_samples = 1000
file_format = 'piksi'

chipping_rate = 1.023e6  # Hz
code_length = 1023  # chips

code_period = code_length / chipping_rate

# 'peregrine' frequencies profile
freq_profile_peregrine = {
    'L1_IF': 4.092e6,
    'L2_IF': 4.092e6,
    'sampling_freq': 16.368e6,
    'samples_per_l1ca_code': code_period * 16.368e6}

# 'low_rate' frequencies profile
freq_profile_low = {
    'L1_IF': 1450000.0,
    'L2_IF': 750000.0,
    'sampling_freq': 2484375.0,
    'samples_per_l1ca_code': code_period * 2484375.0}

L1CA_CHANNEL_BANDWIDTH_HZ=1000
L2C_CHANNEL_BANDWIDTH_HZ=1000

l1ca_stage1_loop_filter_params = {
    "loop_freq": 1e3,     # loop frequency [Hz]
    "code_bw": 1,         # Code loop NBW
    "code_zeta": 0.7,     # Code loop zeta
    "code_k": 1,          # Code loop k
    "carr_to_code": 1540, # Carrier-to-code freq ratio (carrier aiding)
    "carr_bw": 10,        # Carrier loop NBW
    "carr_zeta": 0.7,     # Carrier loop zeta
    "carr_k": 1,          # Carrier loop k
    "carr_freq_b1": 5}    # Carrier loop aiding_igain

l2c_loop_filter_params = {
    "loop_freq": 50,      # loop frequency [Hz]
    "code_bw": 1,         # Code loop NBW
    "code_zeta": 0.707,   # Code loop zeta
    "code_k": 1,          # Code loop k
    "carr_to_code": 1200, # Carrier-to-code freq ratio (carrier aiding)
    "carr_bw": 13,        # Carrier loop NBW
    "carr_zeta": 0.707,   # Carrier loop zeta
    "carr_k": 1,          # Carrier loop k
    "carr_freq_b1": 5}    # Carrier loop aiding_igain

# pessimistic set
l1ca_lock_detect_params_pess = {"k1": 0.10, "k2": 1.4, "lp": 200, "lo": 50}

# normal set
l1ca_lock_detect_params_normal = {"k1": 0.05, "k2": 1.4, "lp": 150, "lo": 50}

# optimal set
l1ca_lock_detect_params_opt = {"k1": 0.02, "k2": 1.1, "lp": 150, "lo": 50}

# extra optimal set
l1ca_lock_detect_params_extraopt = {"k1": 0.02, "k2": 0.8, "lp": 150, "lo": 50}

# disable lock detect
l1ca_lock_detect_params_disable = {"k1": 0.02, "k2": 1e-6, "lp": 1, "lo": 1}


# L2C 20ms lock detect profile
# References:
# - Understanding GPS: Principles and Applications.
#   Elliott D. Kaplan. Artech House, 2006. 2nd edition
#   p.235
l2c_lock_detect_params_20ms = {
    'k1': 0.0247,  # LPF with -3dB at ~0.4 Hz
    'k2': 1.5,     # use ~26 degrees I/Q phase angle as a threshold
    'lp': 50,      # 1000ms worth of I/Q samples to reach pessimistic lock
    'lo': 240}     # 4800ms worth of I/Q samples to lower optimistic lock

alias_detect_interval_ms = 500

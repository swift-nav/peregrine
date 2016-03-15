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

# original
sample_channel_GPS_L1 = 0
sample_channel_GPS_L2 = 1
sample_channel_GLO_L1 = 2
sample_channel_GLO_L2 = 3

file_encoding_1bit_x2 = [
    sample_channel_GPS_L1,  # GPS L1
    sample_channel_GPS_L2]  # GPS L2

file_encoding_2bits_x2 = file_encoding_1bit_x2

# encoding is taken from here:
# https://swiftnav.hackpad.com/MicroZed-Sample-Grabber-IFgt5DbAunD
# 2 bits per frontend channel in every byte:
#    RF4 RF3 RF2 RF1
#    00  00  00  00
#
# RF 1:
# GPS L1 @ 14.58MHz (1575.42MHz)
# Galileo E1 @ 14.58MHz (1575.42MHz)
# Beidou B1 @ 28.902 MHz (1561.098 MHz)
#
# RF 2:
# GLONASS L1 @ 12MHz (1602MHz)
#
# RF 3:
# GLONASS L2 @ 11MHz (1246MHz)
# Beidou B3 @ 33.52MHz (1268.52MHz)
# Galileo E6 @ 43.75 MHz(1278.75MHz)
#
# RF 4:
# GPS L2 @ 7.4MHz (1227.6MHz)
# Galileo E5b-I/Q @ 27.86MHz (1207.14MHz)
# Beidou B2 @ 27.86MHz  (1207.14MHz)
file_encoding_2bits_x4 = [
    sample_channel_GPS_L2,  # RF4
    sample_channel_GLO_L2,  # RF3
    sample_channel_GLO_L1,  # RF2
    sample_channel_GPS_L1]  # RF1

file_encoding_profile = {
    '1bit_x2': file_encoding_1bit_x2,
    '2bits_x2': file_encoding_2bits_x2,
    '2bits_x4': file_encoding_2bits_x4}

# 'peregrine' frequencies profile
freq_profile_peregrine = {
    'GPS_L1_IF': 4.092e6,
    'GPS_L2_IF': 4.092e6,
    'sampling_freq': 16.368e6}

# 'low_rate' frequencies profile
freq_profile_low_rate = {
    'GPS_L1_IF': 14.58e5,
    'GPS_L2_IF': 7.4e5,
    'sampling_freq': 24.84375e5}

# 'normal_rate' frequencies profile
freq_profile_normal_rate = {
    'GPS_L1_IF': 14.58e6,
    'GPS_L2_IF': 7.4e6,
    'sampling_freq': 24.84375e6}

# 'normal_rate' frequencies profile
freq_profile_high_rate = {
    'GPS_L1_IF': freq_profile_normal_rate['GPS_L1_IF'],
    'GPS_L2_IF': freq_profile_normal_rate['GPS_L2_IF'],
    'sampling_freq': 99.375e6}

L1CA_CHANNEL_BANDWIDTH_HZ = 1000
L2C_CHANNEL_BANDWIDTH_HZ = 1000

l1ca_stage1_loop_filter_params = {
    "loop_freq": 1e3,     # loop frequency [Hz]
    "code_bw": 1,         # Code loop NBW
    "code_zeta": 0.7,     # Code loop zeta
    "code_k": 1,          # Code loop k
    "carr_to_code": 1540,  # Carrier-to-code freq ratio (carrier aiding)
    "carr_bw": 10,        # Carrier loop NBW
    "carr_zeta": 0.7,     # Carrier loop zeta
    "carr_k": 1,          # Carrier loop k
    "carr_freq_b1": 5}    # Carrier loop aiding_igain

l2c_loop_filter_params = {
    "loop_freq": 50,      # loop frequency [Hz]
    "code_bw": 1.4,       # Code loop NBW
    "code_zeta": 0.707,   # Code loop zeta
    "code_k": 1,          # Code loop k
    "carr_to_code": 1200,  # Carrier-to-code freq ratio (carrier aiding)
    "carr_bw": 13,        # Carrier loop NBW
    "carr_zeta": 0.707,   # Carrier loop zeta
    "carr_k": 1,          # Carrier loop k
    "carr_freq_b1": 5}    # Carrier loop aiding_igain


# Tracking stages. See track.c for more details.
# 1;20 ms stages
l1ca_stage_params_slow = \
    ({'coherent_ms': 1,
      'loop_filter_params': {'code_params': (1., 0.7, 1.),   # NBW, zeta, k
                             'carr_params': (10., 0.7, 1.),  # NBW, zeta, k
                             'loop_freq': 1000.,             # 1000/coherent_ms
                             'carr_freq_igain': 5.,          # fll_aid
                             'carr_to_code': 1540.           # carr_to_code
                             }
      },
     {'coherent_ms': 20,
      'loop_filter_params': {'code_params': (1., 0.7, 1.),   # NBW, zeta, k
                             'carr_params': (12., 0.7, 1.),  # NBW, zeta, k
                             'loop_freq': 1000. / 20,        # 1000/coherent_ms
                             'carr_freq_igain': 0.,          # fll_aid
                             'carr_to_code': 1540.           # carr_to_code
                             }
      }
     )

# 1;5 ms stages
l1ca_stage_params_med = \
    ({'coherent_ms': 1,
      'loop_filter_params': {'code_params': (1., 0.7, 1.),   # NBW, zeta, k
                             'carr_params': (10., 0.7, 1.),  # NBW, zeta, k
                             'loop_freq': 1000.,             # 1000/coherent_ms
                             'carr_freq_igain': 5.,          # fll_aid
                             'carr_to_code': 1540.           # carr_to_code
                             }
      },

     {'coherent_ms': 5,
      'loop_filter_params': {'code_params': (1., 0.7, 1.),   # NBW, zeta, k
                             'carr_params': (50., 0.7, 1.),  # NBW, zeta, k
                             'loop_freq': 1000. / 5,         # 1000/coherent_ms
                             'carr_freq_igain': 0.,          # fll_aid
                             'carr_to_code': 1540.           # carr_to_code
                             }
      }
     )

# 1;4 ms stages
l1ca_stage_params_fast = \
    ({'coherent_ms': 1,
      'loop_filter_params': {'code_params': (1., 0.7, 1.),   # NBW, zeta, k
                             'carr_params': (10., 0.7, 1.),  # NBW, zeta, k
                             'loop_freq': 1000.,             # 1000/coherent_ms
                             'carr_freq_igain': 5.,          # fll_aid
                             'carr_to_code': 1540.           # carr_to_code
                             }
      },
     {'coherent_ms': 4,
      'loop_filter_params': {'code_params': (1., 0.7, 1.),   # NBW, zeta, k
                             'carr_params': (62., 0.7, 1.),  # NBW, zeta, k
                             'loop_freq': 1000. / 4,         # 1000/coherent_ms
                             'carr_freq_igain': 0.,          # fll_aid
                             'carr_to_code': 1540.           # carr_to_code
                             }
      }
     )

# 1;2 ms stages
l1ca_stage_params_extrafast = \
    ({'coherent_ms': 1,
      'loop_filter_params': {'code_params': (1., 0.7, 1.),   # NBW, zeta, k
                             'carr_params': (10., 0.7, 1.),  # NBW, zeta, k
                             'loop_freq': 1000.,             # 1000/coherent_ms
                             'carr_freq_igain': 5.,          # fll_aid
                             'carr_to_code': 1540.           # carr_to_code
                             }
      },
     {'coherent_ms': 2,
      'loop_filter_params': {'code_params': (1., 0.7, 1.),   # NBW, zeta, k
                             'carr_params': (100., 0.7, 1.),  # NBW, zeta, k
                             'loop_freq': 1000. / 2,         # 1000/coherent_ms
                             'carr_freq_igain': 0.,          # fll_aid
                             'carr_to_code': 1540.           # carr_to_code
                             }
      }
     )

# L1 C/A stage profiles
l1ca_stage_profiles = {'slow': l1ca_stage_params_slow,
                       'med': l1ca_stage_params_med,
                       'fast': l1ca_stage_params_fast,
                       'extrafast': l1ca_stage_params_extrafast}

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

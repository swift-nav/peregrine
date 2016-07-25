# Copyright (C) 2014,2016 Swift Navigation Inc.
# Contact: Adel Mamin <adelm@exafore.com>
#
# This source is subject to the license found in the file 'LICENSE' which must
# be be distributed together with this source. All other rights reserved.
#
# THIS CODE AND INFORMATION IS PROVIDED "AS IS" WITHOUT WARRANTY OF ANY KIND,
# EITHER EXPRESSED OR IMPLIED, INCLUDING BUT NOT LIMITED TO THE IMPLIED
# WARRANTIES OF MERCHANTABILITY AND/OR FITNESS FOR A PARTICULAR PURPOSE.

acqThreshold = 21.0  # SNR (unitless)
acqSanityCheck = True  # Check for sats known to be below the horizon
navSanityMaxResid = 25.0  # meters per SV, normalized nav residuals
abortIfInsane = True  # Abort the whole attempt if sanity check fails
useCache = True
cacheDir = 'cache'
ephemMaxAge = 4 * 3600.0  # Reject an ephemeris entry if older than this

# the size of the sample data block processed at a time
processing_block_size = int(20e6)  # [samples]

# used to simulate real HW
# [0..10230]
l2c_short_step_chips = 300  # used to simulate real HW

chipping_rate = 1.023e6  # Hz
code_length = 1023  # chips

code_period = code_length / chipping_rate

# original
sample_channel_GPS_L1 = 0
sample_channel_GPS_L2 = 1
sample_channel_GLO_L1 = 2
sample_channel_GLO_L2 = 3

file_encoding_x1_gpsl1 = [
    sample_channel_GPS_L1]  # GPS L1

file_encoding_x1_gpsl2 = [
    sample_channel_GPS_L2]  # GPS L2

file_encoding_x1_glol1 = [
    sample_channel_GLO_L1]  # GLO L1

file_encoding_x1_glol2 = [
    sample_channel_GLO_L2]  # GLO L2

file_encoding_x2_gpsl1l2 = [
    sample_channel_GPS_L1,  # GPS L1
    sample_channel_GPS_L2]  # GPS L2

file_encoding_x2_glol1l2 = [
    sample_channel_GLO_L1,  # GLO L1
    sample_channel_GLO_L2]  # GLO L2

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
file_encoding_x4_gps_glo = [
    sample_channel_GPS_L2,  # RF4
    sample_channel_GLO_L2,  # RF3
    sample_channel_GLO_L1,  # RF2
    sample_channel_GPS_L1]  # RF1

# Some of the format names for use with other components
# The format has the following pattern: <encoding>_x<count>.<signals>
FORMAT_PIKSI_X1_GPS_L1 = 'piksi_x1.gpsl1'
FORMAT_PIKSI_X1_GPS_L2 = 'piksi_x1.gpsl2'
FORMAT_PIKSI_X1_GLO_L1 = 'piksi_x1.glol1'
FORMAT_PIKSI_X1_GLO_L2 = 'piksi_x1.glol2'

FORMAT_1BIT_X1_GPS_L1 = '1bit_x1.gpsl1'
FORMAT_1BIT_X1_GPS_L2 = '1bit_x1.gpsl2'
FORMAT_1BIT_X2_GPS_L1L2 = '1bit_x2.gps'
FORMAT_1BIT_X1_GLO_L1 = '1bit_x1.glol1'
FORMAT_1BIT_X1_GLO_L2 = '1bit_x1.glol2'
FORMAT_1BIT_X2_GLO_L1L2 = '1bit_x2.glo'
FORMAT_1BIT_X4_GPS_L1L2_GLO_L1L2 = '1bit_x4'

FORMAT_2BITS_X1_GPS_L1 = '2bits_x1.gpsl1'
FORMAT_2BITS_X1_GPS_L2 = '2bits_x1.gpsl2'
FORMAT_2BITS_X2_GPS_L1L2 = '2bits_x2.gps'
FORMAT_2BITS_X1_GLO_L1 = '2bits_x1.glol1'
FORMAT_2BITS_X1_GLO_L2 = '2bits_x1.glol2'
FORMAT_2BITS_X2_GLO_L1L2 = '2bits_x2.glo'
FORMAT_2BITS_X4_GPS_L1L2_GLO_L1L2 = '2bits_x4'

# All supported file formats
# The map contains encoding name as a key and value as a list of channels in
# the file.
file_encoding_profile = {
    'piksi': file_encoding_x1_gpsl1,
    FORMAT_PIKSI_X1_GPS_L1: file_encoding_x1_gpsl1,
    FORMAT_PIKSI_X1_GPS_L2: file_encoding_x1_gpsl2,
    FORMAT_PIKSI_X1_GLO_L1: file_encoding_x1_glol1,
    FORMAT_PIKSI_X1_GLO_L2: file_encoding_x1_glol2,
    'piksinew': file_encoding_x1_gpsl1,
    'int8': file_encoding_x1_gpsl1,
    'c8c8': file_encoding_x2_gpsl1l2,
    '1bit': file_encoding_x1_gpsl1,
    '1bitrev': file_encoding_x1_gpsl1,
    '1bit_x1': file_encoding_x1_gpsl1,
    FORMAT_1BIT_X1_GPS_L1: file_encoding_x1_gpsl1,
    FORMAT_1BIT_X1_GPS_L2: file_encoding_x1_gpsl2,
    FORMAT_1BIT_X1_GLO_L1: file_encoding_x1_glol1,
    FORMAT_1BIT_X1_GLO_L2: file_encoding_x1_glol2,
    '1bit_x2': file_encoding_x2_gpsl1l2,
    FORMAT_1BIT_X2_GPS_L1L2: file_encoding_x2_gpsl1l2,
    FORMAT_1BIT_X2_GLO_L1L2: file_encoding_x2_glol1l2,
    FORMAT_1BIT_X4_GPS_L1L2_GLO_L1L2: file_encoding_x4_gps_glo,
    '2bits': file_encoding_x1_gpsl1,
    '2bits_x2': file_encoding_x2_gpsl1l2,
    FORMAT_2BITS_X1_GPS_L1: file_encoding_x1_gpsl1,
    FORMAT_2BITS_X1_GPS_L2: file_encoding_x1_gpsl2,
    FORMAT_2BITS_X1_GLO_L1: file_encoding_x1_glol1,
    FORMAT_2BITS_X1_GLO_L2: file_encoding_x1_glol2,
    FORMAT_2BITS_X2_GPS_L1L2: file_encoding_x2_gpsl1l2,
    FORMAT_2BITS_X2_GLO_L1L2: file_encoding_x2_glol1l2,
    FORMAT_2BITS_X4_GPS_L1L2_GLO_L1L2: file_encoding_x4_gps_glo}

# 'peregrine' frequencies profile
freq_profile_peregrine = {
    'GPS_L1_IF': 4.092e6,
    'GPS_L2_IF': 4.092e6,
    'GLO_L1_IF': 6e6,
    'GLO_L2_IF': 6e6,
    'sampling_freq': 16.368e6}

# 'low_rate' frequencies profile
freq_profile_low_rate = {
    'GPS_L1_IF': 1026375.0,
    'GPS_L2_IF': 7.4e5,
    'GLO_L1_IF': 12e5,
    'GLO_L2_IF': 12e5,
    'sampling_freq': 24.84375e5}

# 'normal_rate' frequencies profile
freq_profile_normal_rate = {
    'GPS_L1_IF': 10263750.0,
    'GPS_L2_IF': 7.4e6,
    'GLO_L1_IF': 12e6,
    'GLO_L2_IF': 5.6e6,
    'sampling_freq': 24.84375e6}

# 'high_rate' frequencies profile
freq_profile_high_rate = {
    'GPS_L1_IF': freq_profile_normal_rate['GPS_L1_IF'],
    'GPS_L2_IF': freq_profile_normal_rate['GPS_L2_IF'],
    'GLO_L1_IF': freq_profile_normal_rate['GLO_L1_IF'],
    'GLO_L2_IF': freq_profile_normal_rate['GLO_L2_IF'],
    'sampling_freq': 99.375e6}

freq_profile_lookup = {
    'custom_rate': freq_profile_peregrine,
    'low_rate': freq_profile_low_rate,
    'normal_rate': freq_profile_normal_rate,
    'high_rate': freq_profile_high_rate}

L1CA_CHANNEL_BANDWIDTH_HZ = 1000
L2C_CHANNEL_BANDWIDTH_HZ = 1000
GLOL1_CHANNEL_BANDWIDTH_HZ = 1000

l1ca_stage1_loop_filter_params = {
    "loop_freq": 1e3,     # loop frequency [Hz]
    "code_bw": 1,         # Code loop NBW
    "code_zeta": 0.7,     # Code loop zeta
    "code_k": 1,          # Code loop k
    "carr_to_code": 1540,  # Carrier-to-code freq ratio (carrier aiding)
    "carr_bw": 15,        # Carrier loop NBW
    "carr_zeta": 0.7,     # Carrier loop zeta
    "carr_k": 1,          # Carrier loop k
    "carr_freq_b1": 1}    # Carrier loop aiding_igain

l2c_loop_filter_params = {
    "loop_freq": 50,      # loop frequency [Hz]
    "code_bw": 1,       # Code loop NBW
    "code_zeta": 0.707,   # Code loop zeta
    "code_k": 1,          # Code loop k
    "carr_to_code": 1200,  # Carrier-to-code freq ratio (carrier aiding)
    "carr_bw": 13,        # Carrier loop NBW
    "carr_zeta": 0.707,   # Carrier loop zeta
    "carr_k": 1,          # Carrier loop k
    "carr_freq_b1": 1}    # Carrier loop aiding_igain


# Tracking stages. See track.c for more details.
# 1;20 ms stages
l1ca_stage_params_slow = \
    ({'coherent_ms': 1,
      'loop_filter_params': {'code_params': (1., 0.7, 1.),   # NBW, zeta, k
                             'carr_params': (10., 0.7, 1.),  # NBW, zeta, k
                             'loop_freq': 1000.,             # 1000/coherent_ms
                             'carr_freq_b1': 5.,          # fll_aid
                             'carr_to_code': 1540.           # carr_to_code
                             }
      },
     {'coherent_ms': 20,
      'loop_filter_params': {'code_params': (1., 0.7, 1.),   # NBW, zeta, k
                             'carr_params': (2., 0.7, 1.),  # NBW, zeta, k
                             'loop_freq': 1000. / 20,        # 1000/coherent_ms
                             'carr_freq_b1': 0.,          # fll_aid
                             'carr_to_code': 1540.           # carr_to_code
                             }
      }
     )

l1ca_stage_params_slow2 = \
    ({'coherent_ms': 1,
      'loop_filter_params': {'code_params': (1., 0.7, 1.),   # NBW, zeta, k
                             'carr_params': (10., 0.7, 1.),  # NBW, zeta, k
                             'loop_freq': 1000.,             # 1000/coherent_ms
                             'carr_freq_b1': 5.,          # fll_aid
                             'carr_to_code': 1540.           # carr_to_code
                             }
      },
     {'coherent_ms': 10,
      'loop_filter_params': {'code_params': (1., 0.7, 1.),   # NBW, zeta, k
                             'carr_params': (12., 0.7, 1.),  # NBW, zeta, k
                             'loop_freq': 1000. / 10,        # 1000/coherent_ms
                             'carr_freq_b1': 0.,          # fll_aid
                             'carr_to_code': 1540.           # carr_to_code
                             }
      }
     )

# 1;5 ms stages
# l1ca_stage_params_med = \
#     ({'coherent_ms': 1,
#       'loop_filter_params': {'code_params': (3., 0.7, 1.),   # NBW, zeta, k
#                              'carr_params': (15., 0.7, 1.),  # NBW, zeta, k
#                              'loop_freq': 1000.,             # 1000/coherent_ms
#                              'carr_freq_b1': 5.,          # fll_aid
#                              'carr_to_code': 1540.           # carr_to_code
#                              }
#       },

#      {'coherent_ms': 2,
#       'loop_filter_params': {'code_params': (1., 0.7, 1.),   # NBW, zeta, k
#                              'carr_params': (30., 0.7, 1.),  # NBW, zeta, k
#                              'loop_freq': 1000./2,         # 1000/coherent_ms
#                              'carr_freq_b1': 0,          # fll_aid
#                              'carr_to_code': 1540.           # carr_to_code
#                              }
#       }
#      )

# 1;5 ms stages
l1ca_stage_params_med = \
    ({'coherent_ms': 1,
      'loop_filter_params': {'code_params': (1., 0.7, 1.),   # NBW, zeta, k
                             'carr_params': (10., 0.7, 1.),  # NBW, zeta, k
                             'loop_freq': 1000.,             # 1000/coherent_ms
                             'carr_freq_b1': 5.,          # fll_aid
                             'carr_to_code': 1540.           # carr_to_code
                             }
      },

     {'coherent_ms': 20,
      'loop_filter_params': {'code_params': (1., 0.707, 1.),   # NBW, zeta, k
                             'carr_params': (3, 0.707, 1.),  # NBW, zeta, k
                             'loop_freq': 1000. / 20,         # 1000/coherent_ms
                             'carr_freq_b1': 0.,          # fll_aid
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
                             'carr_freq_b1': 5.,          # fll_aid
                             'carr_to_code': 1540.           # carr_to_code
                             }
      },
     {'coherent_ms': 4,
      'loop_filter_params': {'code_params': (1., 0.7, 1.),   # NBW, zeta, k
                             'carr_params': (62., 0.7, 1.),  # NBW, zeta, k
                             'loop_freq': 1000. / 4,         # 1000/coherent_ms
                             'carr_freq_b1': 0.,          # fll_aid
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
                             'carr_freq_b1': 5.,          # fll_aid
                             'carr_to_code': 1540.           # carr_to_code
                             }
      },
     {'coherent_ms': 2,
      'loop_filter_params': {'code_params': (1., 0.7, 1.),   # NBW, zeta, k
                             'carr_params': (100., 0.7, 1.),  # NBW, zeta, k
                             'loop_freq': 1000. / 2,         # 1000/coherent_ms
                             'carr_freq_b1': 0.,          # fll_aid
                             'carr_to_code': 1540.           # carr_to_code
                             }
      }
     )

# L1 C/A stage profiles
l1ca_stage_profiles = {'slow': l1ca_stage_params_slow,
                       'slow2': l1ca_stage_params_slow2,
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

# The time interval, over which the alias detection is done.
# The alias detect algorithm averages the phase angle over this time [ms]
alias_detect_interval_ms = 500

# The correlator intermediate results are read with this timeout in [ms].
# The intermediate results are the input for the alias lock detector.
alias_detect_slice_ms = 1

# Default pipelining prediction coefficient
pipelining_k = .9549

# Default coherent integration time for L2C tracker
l2c_coherent_integration_time_ms = 20

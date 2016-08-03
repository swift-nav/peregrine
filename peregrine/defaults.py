# Copyright (C) 2014,2016 Swift Navigation Inc.
# Contact: Adel Mamin <adelm@exafore.com>
#
# This source is subject to the license found in the file 'LICENSE' which must
# be be distributed together with this source. All other rights reserved.
#
# THIS CODE AND INFORMATION IS PROVIDED "AS IS" WITHOUT WARRANTY OF ANY KIND,
# EITHER EXPRESSED OR IMPLIED, INCLUDING BUT NOT LIMITED TO THE IMPLIED
# WARRANTIES OF MERCHANTABILITY AND/OR FITNESS FOR A PARTICULAR PURPOSE.

import gps_constants

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

l1ca_track_params = {
    'fll_bw': (0,),
    'pll_bw': (20,), #, 20, 14, 10, 8, 6, 4, 2),
    'coherent_ms': (1,) }# 2, 4, 5, 10, 20) }

l1ca_loop_filter_params_template = {
     'code_params': (1., 0.7, 1.),   # NBW, zeta, k
     'carr_params': (20., 0.7, 1.),   # NBW, zeta, k
     'loop_freq': 1000.,             # 1000/coherent_ms
     'carr_freq_b1': 1.,             # FLL NBW
     'carr_to_code': 1540.           # carr_to_code
    }

# l1ca_track_profiles_fll = {
#   0: ({'coherent_ms': 1,
#       'stabilization_time_ms': 50,
#       'loop_filter_params': {'code_params': (1., 0.7, 1.),   # NBW, zeta, k
#                              'carr_params': (20., 0.7, 1.),   # NBW, zeta, k
#                              'loop_freq': 1000.,             # 1000/coherent_ms
#                              'carr_freq_b1': 1.,             # FLL NBW
#                              'carr_to_code': 1540.           # carr_to_code
#                              }
#       }, 1),
#   1: ({'coherent_ms': 4,
#       'stabilization_time_ms': 50,
#       'loop_filter_params': {'code_params': (1., 0.7, 1.),   # NBW, zeta, k
#                              'carr_params': (8, 0.7, 1.),  # NBW, zeta, k
#                              'loop_freq': 1000./4,             # 1000/coherent_ms
#                              'carr_freq_b1': 0.,             # FLL NBW
#                              'carr_to_code': 1540.           # carr_to_code
#                              }
#       }, 1) }

# l1ca_track_response = {
#   0: ({'coherent_ms': 1,
#       'stabilization_time_ms': 50,
#       'loop_filter_params': {'code_params': (1., 0.7, 1.),   # NBW, zeta, k
#                              'carr_params': (20., 0.7, 1.),   # NBW, zeta, k
#                              'loop_freq': 1000.,             # 1000/coherent_ms
#                              'carr_freq_b1': 1.,             # FLL NBW
#                              'carr_to_code': 1540.           # carr_to_code
#                              }
#       }, 0 }

# l1ca_track_recovery = {
#   0: ({'coherent_ms': 1,
#       'stabilization_time_ms': 50,
#       'loop_filter_params': {'code_params': (1., 0.7, 1.),   # NBW, zeta, k
#                              'carr_params': (20., 0.7, 1.),  # NBW, zeta, k
#                              'loop_freq': 1000.,             # 1000/coherent_ms
#                              'carr_freq_b1': 0.,             # FLL NBW
#                              'carr_to_code': 1540.           # carr_to_code
#                              }
#       }, 0 }

# l1ca_track_profiles = {
#   # init state
#   0: ({'coherent_ms': 1,
#       'stabilization_time_ms': 50,
#       'loop_filter_params': {'code_params': (1., 0.7, 1.),   # NBW, zeta, k
#                              'carr_params': (20., 0.7, 1.),   # NBW, zeta, k
#                              'loop_freq': 1000.,             # 1000/coherent_ms
#                              'carr_freq_b1': 1.,             # FLL NBW
#                              'carr_to_code': 1540.           # carr_to_code
#                              }
#       }, {'next_bw': 1, 'next_time': 1}),

#   # 1ms
#   1: ({'coherent_ms': 1,
#       'stabilization_time_ms': 50,
#       'loop_filter_params': {'code_params': (1., 0.7, 1.),   # NBW, zeta, k
#                              'carr_params': (20., 0.7, 1.),  # NBW, zeta, k
#                              'loop_freq': 1000.,             # 1000/coherent_ms
#                              'carr_freq_b1': 0.,             # FLL NBW
#                              'carr_to_code': 1540.           # carr_to_code
#                              }
#       }, {'next_bw': 2, 'next_time': 8}),

#   2: ({'coherent_ms': 1,
#       'stabilization_time_ms': 50,
#       'loop_filter_params': {'code_params': (1., 0.7, 1.),   # NBW, zeta, k
#                              'carr_params': (14., 0.7, 1.),  # NBW, zeta, k
#                              'loop_freq': 1000.,             # 1000/coherent_ms
#                              'carr_freq_b1': 0.,             # FLL NBW
#                              'carr_to_code': 1540.           # carr_to_code
#                              }
#       }, {'next_bw': 3, 'next_time': 9}),

#   3: ({'coherent_ms': 1,
#       'stabilization_time_ms': 50,
#       'loop_filter_params': {'code_params': (1., 0.7, 1.),   # NBW, zeta, k
#                              'carr_params': (10, 0.7, 1.),  # NBW, zeta, k
#                              'loop_freq': 1000.,             # 1000/coherent_ms
#                              'carr_freq_b1': 0.,             # FLL NBW
#                              'carr_to_code': 1540.           # carr_to_code
#                              }
#       }, {'next_bw': 4, 'next_time': 10}),

#   4: ({'coherent_ms': 1,
#       'stabilization_time_ms': 50,
#       'loop_filter_params': {'code_params': (1., 0.7, 1.),   # NBW, zeta, k
#                              'carr_params': (8, 0.7, 1.),  # NBW, zeta, k
#                              'loop_freq': 1000.,             # 1000/coherent_ms
#                              'carr_freq_b1': 0.,             # FLL NBW
#                              'carr_to_code': 1540.           # carr_to_code
#                              }
#       }, {'next_bw': 5, 'next_time': 11}),

#   5: ({'coherent_ms': 1,
#       'stabilization_time_ms': 50,
#       'loop_filter_params': {'code_params': (1., 0.7, 1.),   # NBW, zeta, k
#                              'carr_params': (6, 0.7, 1.),  # NBW, zeta, k
#                              'loop_freq': 1000.,             # 1000/coherent_ms
#                              'carr_freq_b1': 0.,             # FLL NBW
#                              'carr_to_code': 1540.           # carr_to_code
#                              }
#       }, {'next_bw': 6, 'next_time': 12}),

#   6: ({'coherent_ms': 1,
#       'stabilization_time_ms': 50,
#       'loop_filter_params': {'code_params': (1., 0.7, 1.),   # NBW, zeta, k
#                              'carr_params': (4, 0.7, 1.),  # NBW, zeta, k
#                              'loop_freq': 1000.,             # 1000/coherent_ms
#                              'carr_freq_b1': 0.,             # FLL NBW
#                              'carr_to_code': 1540.           # carr_to_code
#                              }
#       }, {'next_bw': 7, 'next_time': 13}),

#   7: ({'coherent_ms': 1,
#       'stabilization_time_ms': 50,
#       'loop_filter_params': {'code_params': (1., 0.7, 1.),   # NBW, zeta, k
#                              'carr_params': (2, 0.7, 1.),  # NBW, zeta, k
#                              'loop_freq': 1000.,             # 1000/coherent_ms
#                              'carr_freq_b1': 0.,             # FLL NBW
#                              'carr_to_code': 1540.           # carr_to_code
#                              }
#       }, {'next_bw': 7, 'next_time': 14}),

#   # 2ms
#   8: ({'coherent_ms': 2,
#       'stabilization_time_ms': 50,
#       'loop_filter_params': {'code_params': (1., 0.7, 1.),   # NBW, zeta, k
#                              'carr_params': (20., 0.7, 1.),  # NBW, zeta, k
#                              'loop_freq': 1000. / 2,         # 1000/coherent_ms
#                              'carr_freq_b1': 0.,             # FLL NBW
#                              'carr_to_code': 1540.           # carr_to_code
#                              }
#       }, {'next_bw': 9, 'next_time': 15}),

#   9: ({'coherent_ms': 2,
#       'stabilization_time_ms': 50,
#       'loop_filter_params': {'code_params': (1., 0.7, 1.),   # NBW, zeta, k
#                              'carr_params': (14., 0.7, 1.),  # NBW, zeta, k
#                              'loop_freq': 1000. / 2,         # 1000/coherent_ms
#                              'carr_freq_b1': 0.,             # FLL NBW
#                              'carr_to_code': 1540.           # carr_to_code
#                              }
#       }, {'next_bw': 10, 'next_time': 16}),

#   10: ({'coherent_ms': 2,
#       'stabilization_time_ms': 50,
#       'loop_filter_params': {'code_params': (1., 0.7, 1.),   # NBW, zeta, k
#                              'carr_params': (10, 0.7, 1.),  # NBW, zeta, k
#                              'loop_freq': 1000. / 2,         # 1000/coherent_ms
#                              'carr_freq_b1': 0.,             # FLL NBW
#                              'carr_to_code': 1540.           # carr_to_code
#                              }
#       }, {'next_bw': 11, 'next_time': 17}),

#   11: ({'coherent_ms': 2,
#       'stabilization_time_ms': 50,
#       'loop_filter_params': {'code_params': (1., 0.7, 1.),   # NBW, zeta, k
#                              'carr_params': (8, 0.7, 1.),  # NBW, zeta, k
#                              'loop_freq': 1000. / 2,         # 1000/coherent_ms
#                              'carr_freq_b1': 0.,             # FLL NBW
#                              'carr_to_code': 1540.           # carr_to_code
#                              }
#       }, {'next_bw': 12, 'next_time': 18}),

#   12: ({'coherent_ms': 2,
#       'stabilization_time_ms': 50,
#       'loop_filter_params': {'code_params': (1., 0.7, 1.),   # NBW, zeta, k
#                              'carr_params': (6, 0.7, 1.),  # NBW, zeta, k
#                              'loop_freq': 1000. / 2,         # 1000/coherent_ms
#                              'carr_freq_b1': 0.,             # FLL NBW
#                              'carr_to_code': 1540.           # carr_to_code
#                              }
#       }, {'next_bw': 13, 'next_time': 19}),

#   13: ({'coherent_ms':21,
#       'stabilization_time_ms': 50,
#       'loop_filter_params': {'code_params': (1., 0.7, 1.),   # NBW, zeta, k
#                              'carr_params': (4, 0.7, 1.),  # NBW, zeta, k
#                              'loop_freq': 1000. / 2,         # 1000/coherent_ms
#                              'carr_freq_b1': 0.,             # FLL NBW
#                              'carr_to_code': 1540.           # carr_to_code
#                              }
#       }, {'next_bw': 14, 'next_time': 20}),

#   14: ({'coherent_ms': 2,
#       'stabilization_time_ms': 50,
#       'loop_filter_params': {'code_params': (1., 0.7, 1.),   # NBW, zeta, k
#                              'carr_params': (2, 0.7, 1.),  # NBW, zeta, k
#                              'loop_freq': 1000. / 2,         # 1000/coherent_ms
#                              'carr_freq_b1': 0.,             # FLL NBW
#                              'carr_to_code': 1540.           # carr_to_code
#                              }
#       }, {'next_bw': 14, 'next_time': 21}),

#   # 4ms

#   15: ({'coherent_ms': 4,
#       'stabilization_time_ms': 50,
#       'loop_filter_params': {'code_params': (1., 0.7, 1.),   # NBW, zeta, k
#                              'carr_params': (20., 0.7, 1.),  # NBW, zeta, k
#                              'loop_freq': 1000. / 4,         # 1000/coherent_ms
#                              'carr_freq_b1': 0.,             # FLL NBW
#                              'carr_to_code': 1540.           # carr_to_code
#                              }
#       }, {'next_bw': 16, 'next_time': 22}),

#   16: ({'coherent_ms': 4,
#       'stabilization_time_ms': 50,
#       'loop_filter_params': {'code_params': (1., 0.7, 1.),   # NBW, zeta, k
#                              'carr_params': (14., 0.7, 1.),  # NBW, zeta, k
#                              'loop_freq': 1000. / 4,         # 1000/coherent_ms
#                              'carr_freq_b1': 0.,             # FLL NBW
#                              'carr_to_code': 1540.           # carr_to_code
#                              }
#       }, {'next_bw': 17, 'next_time': 23}),

#   17: ({'coherent_ms': 4,
#       'stabilization_time_ms': 50,
#       'loop_filter_params': {'code_params': (1., 0.7, 1.),   # NBW, zeta, k
#                              'carr_params': (10, 0.7, 1.),   # NBW, zeta, k
#                              'loop_freq': 1000. / 4,         # 1000/coherent_ms
#                              'carr_freq_b1': 0.,             # FLL NBW
#                              'carr_to_code': 1540.           # carr_to_code
#                              }
#       }, {'next_bw': 18, 'next_time':24}),

#   18: ({'coherent_ms': 4,
#       'stabilization_time_ms': 50,
#       'loop_filter_params': {'code_params': (1., 0.7, 1.),   # NBW, zeta, k
#                              'carr_params': (8, 0.7, 1.),    # NBW, zeta, k
#                              'loop_freq': 1000. / 4,         # 1000/coherent_ms
#                              'carr_freq_b1': 0.,             # FLL NBW
#                              'carr_to_code': 1540.           # carr_to_code
#                              }
#       }, {'next_bw': 19, 'next_time': 25}),

#   19: ({'coherent_ms': 4,
#       'stabilization_time_ms': 50,
#       'loop_filter_params': {'code_params': (1., 0.7, 1.),   # NBW, zeta, k
#                              'carr_params': (6, 0.7, 1.),    # NBW, zeta, k
#                              'loop_freq': 1000. / 4,         # 1000/coherent_ms
#                              'carr_freq_b1': 0.,             # FLL NBW
#                              'carr_to_code': 1540.           # carr_to_code
#                              }
#       }, {'next_bw': 20, 'next_time': 26}),

#   20: ({'coherent_ms': 4,
#       'stabilization_time_ms': 50,
#       'loop_filter_params': {'code_params': (1., 0.7, 1.),   # NBW, zeta, k
#                              'carr_params': (4, 0.7, 1.),    # NBW, zeta, k
#                              'loop_freq': 1000. / 4,         # 1000/coherent_ms
#                              'carr_freq_b1': 0.,             # FLL NBW
#                              'carr_to_code': 1540.           # carr_to_code
#                              }
#       }, {'next_bw': 21, 'next_time': 27}),

#   21: ({'coherent_ms': 4,
#       'stabilization_time_ms': 50,
#       'loop_filter_params': {'code_params': (1., 0.7, 1.),   # NBW, zeta, k
#                              'carr_params': (2, 0.7, 1.),    # NBW, zeta, k
#                              'loop_freq': 1000. / 4,         # 1000/coherent_ms
#                              'carr_freq_b1': 0.,             # FLL NBW
#                              'carr_to_code': 1540.           # carr_to_code
#                              }
#       }, {'next_bw': 21, 'next_time': 28}),

#   # 5ms
#   22: ({'coherent_ms': 5,
#       'stabilization_time_ms': 50,
#       'loop_filter_params': {'code_params': (1., 0.7, 1.),   # NBW, zeta, k
#                              'carr_params': (20., 0.7, 1.),  # NBW, zeta, k
#                              'loop_freq': 1000. / 5,         # 1000/coherent_ms
#                              'carr_freq_b1': 0.,             # FLL NBW
#                              'carr_to_code': 1540.           # carr_to_code
#                              }
#       }, {'next_bw': 23, 'next_time': 29}),

#   23: ({'coherent_ms': 5,
#       'stabilization_time_ms': 50,
#       'loop_filter_params': {'code_params': (1., 0.7, 1.),   # NBW, zeta, k
#                              'carr_params': (14., 0.7, 1.),  # NBW, zeta, k
#                              'loop_freq': 1000. / 5,         # 1000/coherent_ms
#                              'carr_freq_b1': 0.,             # FLL NBW
#                              'carr_to_code': 1540.           # carr_to_code
#                              }
#       }, {'next_bw': 24, 'next_time': 30}),

#   24: ({'coherent_ms': 5,
#       'stabilization_time_ms': 50,
#       'loop_filter_params': {'code_params': (1., 0.7, 1.),   # NBW, zeta, k
#                              'carr_params': (10, 0.7, 1.),  # NBW, zeta, k
#                              'loop_freq': 1000. / 5,         # 1000/coherent_ms
#                              'carr_freq_b1': 0.,             # FLL NBW
#                              'carr_to_code': 1540.           # carr_to_code
#                              }
#       }, {'next_bw': 25, 'next_time': 31}),

#   25: ({'coherent_ms': 5,
#       'stabilization_time_ms': 50,
#       'loop_filter_params': {'code_params': (1., 0.7, 1.),   # NBW, zeta, k
#                              'carr_params': (8, 0.7, 1.),  # NBW, zeta, k
#                              'loop_freq': 1000. / 5,         # 1000/coherent_ms
#                              'carr_freq_b1': 0.,             # FLL NBW
#                              'carr_to_code': 1540.           # carr_to_code
#                              }
#       }, {'next_bw': 26, 'next_time': 32}),

#   26: ({'coherent_ms': 5,
#       'stabilization_time_ms': 50,
#       'loop_filter_params': {'code_params': (1., 0.7, 1.),   # NBW, zeta, k
#                              'carr_params': (6, 0.7, 1.),  # NBW, zeta, k
#                              'loop_freq': 1000. / 5,         # 1000/coherent_ms
#                              'carr_freq_b1': 0.,             # FLL NBW
#                              'carr_to_code': 1540.           # carr_to_code
#                              }
#       }, {'next_bw': 27, 'next_time': 33}),

#   27: ({'coherent_ms': 5,
#       'stabilization_time_ms': 50,
#       'loop_filter_params': {'code_params': (1., 0.7, 1.),   # NBW, zeta, k
#                              'carr_params': (4, 0.7, 1.),  # NBW, zeta, k
#                              'loop_freq': 1000. / 5,         # 1000/coherent_ms
#                              'carr_freq_b1': 0.,             # FLL NBW
#                              'carr_to_code': 1540.           # carr_to_code
#                              }
#       }, {'next_bw': 28, 'next_time': 34}),

#   28: ({'coherent_ms': 5,
#       'stabilization_time_ms': 50,
#       'loop_filter_params': {'code_params': (1., 0.7, 1.),   # NBW, zeta, k
#                              'carr_params': (2, 0.7, 1.),  # NBW, zeta, k
#                              'loop_freq': 1000. / 5,         # 1000/coherent_ms
#                              'carr_freq_b1': 0.,             # FLL NBW
#                              'carr_to_code': 1540.           # carr_to_code
#                              }
#       }, {'next_bw': 28, 'next_time': 35}),

#   # 10ms

#   29: ({'coherent_ms': 10,
#       'stabilization_time_ms': 50,
#       'loop_filter_params': {'code_params': (1., 0.7, 1.),   # NBW, zeta, k
#                              'carr_params': (20., 0.7, 1.),  # NBW, zeta, k
#                              'loop_freq': 1000. / 10,        # 1000/coherent_ms
#                              'carr_freq_b1': 0.,             # FLL NBW
#                              'carr_to_code': 1540.           # carr_to_code
#                              }
#       }, {'next_bw': 30, 'next_time': 36}),

#   30: ({'coherent_ms': 10,
#       'stabilization_time_ms': 50,
#       'loop_filter_params': {'code_params': (1., 0.7, 1.),   # NBW, zeta, k
#                              'carr_params': (14., 0.7, 1.),  # NBW, zeta, k
#                              'loop_freq': 1000. / 10,        # 1000/coherent_ms
#                              'carr_freq_b1': 0.,             # FLL NBW
#                              'carr_to_code': 1540.           # carr_to_code
#                              }
#       }, {'next_bw': 31, 'next_time': 37}),

#   31: ({'coherent_ms': 10,
#       'stabilization_time_ms': 50,
#       'loop_filter_params': {'code_params': (1., 0.7, 1.),   # NBW, zeta, k
#                              'carr_params': (10, 0.7, 1.),  # NBW, zeta, k
#                              'loop_freq': 1000. / 10,        # 1000/coherent_ms
#                              'carr_freq_b1': 0.,             # FLL NBW
#                              'carr_to_code': 1540.           # carr_to_code
#                              }
#       }, {'next_bw': 32, 'next_time': 38}),

#   32: ({'coherent_ms': 10,
#       'stabilization_time_ms': 50,
#       'loop_filter_params': {'code_params': (1., 0.7, 1.),   # NBW, zeta, k
#                              'carr_params': (8, 0.7, 1.),  # NBW, zeta, k
#                              'loop_freq': 1000. / 10,        # 1000/coherent_ms
#                              'carr_freq_b1': 0.,             # FLL NBW
#                              'carr_to_code': 1540.           # carr_to_code
#                              }
#       }, {'next_bw': 33, 'next_time': 39}),

#   33: ({'coherent_ms': 10,
#       'stabilization_time_ms': 50,
#       'loop_filter_params': {'code_params': (1., 0.7, 1.),   # NBW, zeta, k
#                              'carr_params': (6, 0.7, 1.),  # NBW, zeta, k
#                              'loop_freq': 1000. / 10,        # 1000/coherent_ms
#                              'carr_freq_b1': 0.,             # FLL NBW
#                              'carr_to_code': 1540.           # carr_to_code
#                              }
#       }, {'next_bw': 34, 'next_time': 40}),

#   34: ({'coherent_ms': 10,
#       'stabilization_time_ms': 50,
#       'loop_filter_params': {'code_params': (1., 0.7, 1.),   # NBW, zeta, k
#                              'carr_params': (4, 0.7, 1.),  # NBW, zeta, k
#                              'loop_freq': 1000. / 10,        # 1000/coherent_ms
#                              'carr_freq_b1': 0.,             # FLL NBW
#                              'carr_to_code': 1540.           # carr_to_code
#                              }
#       }, {'next_bw': 35, 'next_time': 41}),

#   35: ({'coherent_ms': 10,
#       'stabilization_time_ms': 50,
#       'loop_filter_params': {'code_params': (1., 0.7, 1.),   # NBW, zeta, k
#                              'carr_params': (2, 0.7, 1.),  # NBW, zeta, k
#                              'loop_freq': 1000. / 10,        # 1000/coherent_ms
#                              'carr_freq_b1': 0.,             # FLL NBW
#                              'carr_to_code': 1540.           # carr_to_code
#                              }
#       }, {'next_bw': 35, 'next_time': 42}),

#   # 20ms

#   36: ({'coherent_ms': 20,
#       'stabilization_time_ms': 50,
#       'loop_filter_params': {'code_params': (1., 0.7, 1.),   # NBW, zeta, k
#                              'carr_params': (20., 0.7, 1.),  # NBW, zeta, k
#                              'loop_freq': 1000. / 20,        # 1000/coherent_ms
#                              'carr_freq_b1': 0.,             # FLL NBW
#                              'carr_to_code': 1540.           # carr_to_code
#                              }
#       }, {'next_bw': 37, 'next_time': 36}),

#   37: ({'coherent_ms': 20,
#       'stabilization_time_ms': 50,
#       'loop_filter_params': {'code_params': (1., 0.7, 1.),   # NBW, zeta, k
#                              'carr_params': (14., 0.7, 1.),  # NBW, zeta, k
#                              'loop_freq': 1000. / 20,        # 1000/coherent_ms
#                              'carr_freq_b1': 0.,             # FLL NBW
#                              'carr_to_code': 1540.           # carr_to_code
#                              }
#       }, {'next_bw': 38, 'next_time': 37}),

#   38: ({'coherent_ms': 20,
#       'stabilization_time_ms': 50,
#       'loop_filter_params': {'code_params': (1., 0.7, 1.),   # NBW, zeta, k
#                              'carr_params': (10, 0.7, 1.),  # NBW, zeta, k
#                              'loop_freq': 1000. / 20,        # 1000/coherent_ms
#                              'carr_freq_b1': 0.,             # FLL NBW
#                              'carr_to_code': 1540.           # carr_to_code
#                              }
#       }, {'next_bw': 39, 'next_time': 38}),

#   39: ({'coherent_ms': 20,
#       'stabilization_time_ms': 50,
#       'loop_filter_params': {'code_params': (1., 0.7, 1.),   # NBW, zeta, k
#                              'carr_params': (8, 0.7, 1.),  # NBW, zeta, k
#                              'loop_freq': 1000. / 20,        # 1000/coherent_ms
#                              'carr_freq_b1': 0.,             # FLL NBW
#                              'carr_to_code': 1540.           # carr_to_code
#                              }
#       }, {'next_bw': 40, 'next_time': 39}),

#   40: ({'coherent_ms': 20,
#       'stabilization_time_ms': 50,
#       'loop_filter_params': {'code_params': (1., 0.7, 1.),   # NBW, zeta, k
#                              'carr_params': (6, 0.7, 1.),  # NBW, zeta, k
#                              'loop_freq': 1000. / 20,        # 1000/coherent_ms
#                              'carr_freq_b1': 0.,             # FLL NBW
#                              'carr_to_code': 1540.           # carr_to_code
#                              }
#       }, {'next_bw': 41, 'next_time': 40}),

#   41: ({'coherent_ms': 20,
#       'stabilization_time_ms': 50,
#       'loop_filter_params': {'code_params': (1., 0.7, 1.),   # NBW, zeta, k
#                              'carr_params': (4, 0.7, 1.),  # NBW, zeta, k
#                              'loop_freq': 1000. / 20,        # 1000/coherent_ms
#                              'carr_freq_b1': 0.,             # FLL NBW
#                              'carr_to_code': 1540.           # carr_to_code
#                              }
#       }, {'next_bw': 42, 'next_time': 41}),

#   42: ({'coherent_ms': 20,
#       'stabilization_time_ms': 50,
#       'loop_filter_params': {'code_params': (1., 0.7, 1.),   # NBW, zeta, k
#                              'carr_params': (2, 0.7, 1.),  # NBW, zeta, k
#                              'loop_freq': 1000. / 20,        # 1000/coherent_ms
#                              'carr_freq_b1': 0.,             # FLL NBW
#                              'carr_to_code': 1540.           # carr_to_code
#                              }
#       }, {'next_bw': 42, 'next_time': 42}) }


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

ALIAS_DETECT_1ST = 1
ALIAS_DETECT_2ND = 2
ALIAS_DETECT_BOTH = 3
RUN_LD = 4
APPLY_CORR_1 = 5
APPLY_CORR_2 = 6
GET_CORR_1 = 7
GET_CORR_2 = 8

fsm_states = \
  { '1ms':
    { 'no_bit_sync':
      { 'short_n_long':
        { 'coherent_ms': 1,
          'alias_acc_length_ms': 500,
          0: (1023, 1, {'pre': (APPLY_CORR_1,), 'post': (RUN_LD, GET_CORR_1)}),
          1: (1023, 0, {'pre': (APPLY_CORR_2,), 'post': (RUN_LD, GET_CORR_2)}) },

        'ideal':
        { 'coherent_ms': 1,
          'alias_acc_length_ms': 500,
          0: (1023, 0, {'pre': (APPLY_CORR_1,), 'post': (RUN_LD, GET_CORR_1)}) }
      },
      'bit_sync':
      { 'short_n_long':
        {  'coherent_ms': 1,
           'alias_acc_length_ms': 500,

           0: (1023, 1, {'pre': (APPLY_CORR_1,),
                         'post': (RUN_LD, ALIAS_DETECT_1ST, GET_CORR_1) }),
           1: (1023, 2, {'pre': (APPLY_CORR_2,),
                         'post': (RUN_LD, ALIAS_DETECT_BOTH, GET_CORR_2) }),
           2: (1023, 3, {'pre': (APPLY_CORR_1,),
                         'post': (RUN_LD, ALIAS_DETECT_BOTH, GET_CORR_1) }),
           3: (1023, 4, {'pre': (APPLY_CORR_2,),
                         'post': (RUN_LD, ALIAS_DETECT_BOTH, GET_CORR_2) }),
           4: (1023, 5, {'pre': (APPLY_CORR_1,),
                         'post': (RUN_LD, ALIAS_DETECT_BOTH, GET_CORR_1) }),
           5: (1023, 6, {'pre': (APPLY_CORR_2,),
                         'post': (RUN_LD, ALIAS_DETECT_BOTH, GET_CORR_2) }),
           6: (1023, 7, {'pre': (APPLY_CORR_1,),
                         'post': (RUN_LD, ALIAS_DETECT_BOTH, GET_CORR_1) }),
           7: (1023, 8, {'pre': (APPLY_CORR_2,),
                         'post': (RUN_LD, ALIAS_DETECT_BOTH, GET_CORR_2) }),
           8: (1023, 9, {'pre': (APPLY_CORR_1,),
                         'post': (RUN_LD, ALIAS_DETECT_BOTH, GET_CORR_1) }),
           9: (1023, 10, {'pre': (APPLY_CORR_2,),
                          'post': (RUN_LD, ALIAS_DETECT_BOTH, GET_CORR_2) }),
           10: (1023, 11, {'pre': (APPLY_CORR_1,),
                          'post': (RUN_LD, ALIAS_DETECT_BOTH, GET_CORR_1) }),
           11: (1023, 12, {'pre': (APPLY_CORR_2,),
                          'post': (RUN_LD, ALIAS_DETECT_BOTH, GET_CORR_2) }),
           12: (1023, 13, {'pre': (APPLY_CORR_1,),
                          'post': (RUN_LD, ALIAS_DETECT_BOTH, GET_CORR_1) }),
           13: (1023, 14, {'pre': (APPLY_CORR_2,),
                          'post': (RUN_LD, ALIAS_DETECT_BOTH, GET_CORR_2) }),
           14: (1023, 15, {'pre': (APPLY_CORR_1,),
                          'post': (RUN_LD, ALIAS_DETECT_BOTH, GET_CORR_1) }),
           15: (1023, 16, {'pre': (APPLY_CORR_2,),
                          'post': (RUN_LD, ALIAS_DETECT_BOTH, GET_CORR_2) }),
           16: (1023, 17, {'pre': (APPLY_CORR_1,),
                          'post': (RUN_LD, ALIAS_DETECT_BOTH, GET_CORR_1) }),
           17: (1023, 18, {'pre': (APPLY_CORR_2,),
                          'post': (RUN_LD, ALIAS_DETECT_BOTH, GET_CORR_2) }),
           18: (1023, 19, {'pre': (APPLY_CORR_1,),
                          'post': (RUN_LD, ALIAS_DETECT_BOTH, GET_CORR_1) }),
           19: (1023, 0, {'pre': (APPLY_CORR_2,),
                          'post': (RUN_LD, ALIAS_DETECT_2ND, GET_CORR_2) }) },
        'ideal':
        {  'coherent_ms': 1,
           'alias_acc_length_ms': 500,

           0: (1023, 1, {'pre': (APPLY_CORR_1,),
                         'post': (RUN_LD, ALIAS_DETECT_1ST, GET_CORR_1) }),
           1: (1023, 2, {'pre': (APPLY_CORR_1,),
                         'post': (RUN_LD, ALIAS_DETECT_BOTH, GET_CORR_1) }),
           2: (1023, 3, {'pre': (APPLY_CORR_1,),
                         'post': (RUN_LD, ALIAS_DETECT_BOTH, GET_CORR_1) }),
           3: (1023, 4, {'pre': (APPLY_CORR_1,),
                         'post': (RUN_LD, ALIAS_DETECT_BOTH, GET_CORR_1) }),
           4: (1023, 5, {'pre': (APPLY_CORR_1,),
                         'post': (RUN_LD, ALIAS_DETECT_BOTH, GET_CORR_1) }),
           5: (1023, 6, {'pre': (APPLY_CORR_1,),
                         'post': (RUN_LD, ALIAS_DETECT_BOTH, GET_CORR_1) }),
           6: (1023, 7, {'pre': (APPLY_CORR_1,),
                         'post': (RUN_LD, ALIAS_DETECT_BOTH, GET_CORR_1) }),
           7: (1023, 8, {'pre': (APPLY_CORR_1,),
                         'post': (RUN_LD, ALIAS_DETECT_BOTH, GET_CORR_1) }),
           8: (1023, 9, {'pre': (APPLY_CORR_1,),
                         'post': (RUN_LD, ALIAS_DETECT_BOTH, GET_CORR_1) }),
           9: (1023, 10, {'pre': (APPLY_CORR_1,),
                          'post': (RUN_LD, ALIAS_DETECT_BOTH, GET_CORR_1) }),
           10: (1023, 11, {'pre': (APPLY_CORR_1,),
                          'post': (RUN_LD, ALIAS_DETECT_BOTH, GET_CORR_1) }),
           11: (1023, 12, {'pre': (APPLY_CORR_1,),
                          'post': (RUN_LD, ALIAS_DETECT_BOTH, GET_CORR_1) }),
           12: (1023, 13, {'pre': (APPLY_CORR_1,),
                           'post': (RUN_LD, ALIAS_DETECT_BOTH, GET_CORR_1) }),
           13: (1023, 14, {'pre': (APPLY_CORR_1,),
                          'post': (RUN_LD, ALIAS_DETECT_BOTH, GET_CORR_1) }),
           14: (1023, 15, {'pre': (APPLY_CORR_1,),
                           'post': (RUN_LD, ALIAS_DETECT_BOTH, GET_CORR_1) }),
           15: (1023, 16, {'pre': (APPLY_CORR_1,),
                          'post': (RUN_LD, ALIAS_DETECT_BOTH, GET_CORR_1) }),
           16: (1023, 17, {'pre': (APPLY_CORR_1,),
                           'post': (RUN_LD, ALIAS_DETECT_BOTH, GET_CORR_1) }),
           17: (1023, 18, {'pre': (APPLY_CORR_1,),
                          'post': (RUN_LD, ALIAS_DETECT_BOTH, GET_CORR_1) }),
           18: (1023, 19, {'pre': (APPLY_CORR_1,),
                           'post': (RUN_LD, ALIAS_DETECT_BOTH, GET_CORR_1) }),
           19: (1023, 0, {'pre': (APPLY_CORR_1,),
                          'post': (RUN_LD, ALIAS_DETECT_2ND, GET_CORR_1) }) },
        }
      },

    '2ms':
    { 'no_bit_sync':
      { 'short_n_long':
        { 'coherent_ms': 2,
          'alias_acc_length_ms': 500,
          0: (1023, 1, {'pre': (APPLY_CORR_1,), 'post': (RUN_LD, GET_CORR_1)}),
          1: (1023, 0, {'pre': (APPLY_CORR_2,), 'post': (RUN_LD, GET_CORR_2)}) },

        'ideal':
        { 'coherent_ms': 2,
          'alias_acc_length_ms': 500,
          0: (1023, 1, {'pre': (APPLY_CORR_1,), 'post': (RUN_LD,)}),
          1: (1023, 0, {'pre': (), 'post': (RUN_LD, GET_CORR_1)}) }
      },
      'bit_sync':
      { 'short_n_long':
        {  'coherent_ms': 2,
           'alias_acc_length_ms': 500,

           0: (1023, 1, {'pre': (),
                         'post': (RUN_LD, ALIAS_DETECT_1ST) }),
           1: (1023, 2, {'pre': (APPLY_CORR_1,),
                         'post': (RUN_LD, ALIAS_DETECT_BOTH, GET_CORR_1) }),
           2: (1023, 3, {'pre': (),
                         'post': (RUN_LD, ALIAS_DETECT_BOTH) }),
           3: (1023, 4, {'pre': (APPLY_CORR_1,),
                         'post': (RUN_LD, ALIAS_DETECT_BOTH, GET_CORR_1) }),
           4: (1023, 5, {'pre': (),
                         'post': (RUN_LD, ALIAS_DETECT_BOTH) }),
           5: (1023, 6, {'pre': (APPLY_CORR_1,),
                         'post': (RUN_LD, ALIAS_DETECT_BOTH, GET_CORR_1) }),
           6: (1023, 7, {'pre': (),
                         'post': (RUN_LD, ALIAS_DETECT_BOTH) }),
           7: (1023, 8, {'pre': (APPLY_CORR_1,),
                         'post': (RUN_LD, ALIAS_DETECT_BOTH, GET_CORR_1) }),
           8: (1023, 9, {'pre': (),
                         'post': (RUN_LD, ALIAS_DETECT_BOTH) }),
           9: (1023, 10, {'pre': (APPLY_CORR_1,),
                          'post': (RUN_LD, ALIAS_DETECT_BOTH, GET_CORR_1) }),
           10: (1023, 11, {'pre': (),
                          'post': (RUN_LD, ALIAS_DETECT_BOTH) }),
           11: (1023, 12, {'pre': (APPLY_CORR_1,),
                           'post': (RUN_LD, ALIAS_DETECT_BOTH, GET_CORR_1) }),
           12: (1023, 13, {'pre': (),
                          'post': (RUN_LD, ALIAS_DETECT_BOTH) }),
           13: (1023, 14, {'pre': (APPLY_CORR_1,),
                           'post': (RUN_LD, ALIAS_DETECT_BOTH, GET_CORR_1) }),
           14: (1023, 15, {'pre': (),
                          'post': (RUN_LD, ALIAS_DETECT_BOTH) }),
           15: (1023, 16, {'pre': (APPLY_CORR_1,),
                           'post': (RUN_LD, ALIAS_DETECT_BOTH, GET_CORR_1) }),
           16: (1023, 17, {'pre': (),
                          'post': (RUN_LD, ALIAS_DETECT_BOTH) }),
           17: (1023, 18, {'pre': (APPLY_CORR_1,),
                           'post': (RUN_LD, ALIAS_DETECT_BOTH, GET_CORR_1) }),
           18: (1023, 19, {'pre': (),
                          'post': (RUN_LD, ALIAS_DETECT_BOTH) }),
           19: (1023, 0, {'pre': (APPLY_CORR_1,),
                          'post': (RUN_LD, ALIAS_DETECT_2ND, GET_CORR_1) }) },
        'ideal':
        {  'coherent_ms': 2,
           'alias_acc_length_ms': 500,

           0: (1023, 1, {'pre': (APPLY_CORR_1,),
                         'post': (RUN_LD, ALIAS_DETECT_1ST) }),
           1: (1023, 2, {'pre': (),
                         'post': (RUN_LD, ALIAS_DETECT_BOTH, GET_CORR_1) }),
           2: (1023, 3, {'pre': (APPLY_CORR_1,),
                         'post': (RUN_LD, ALIAS_DETECT_BOTH) }),
           3: (1023, 4, {'pre': (),
                         'post': (RUN_LD, ALIAS_DETECT_BOTH, GET_CORR_1) }),
           4: (1023, 5, {'pre': (APPLY_CORR_1,),
                         'post': (RUN_LD, ALIAS_DETECT_BOTH) }),
           5: (1023, 6, {'pre': (),
                         'post': (RUN_LD, ALIAS_DETECT_BOTH, GET_CORR_1) }),
           6: (1023, 7, {'pre': (APPLY_CORR_1,),
                         'post': (RUN_LD, ALIAS_DETECT_BOTH) }),
           7: (1023, 8, {'pre': (),
                         'post': (RUN_LD, ALIAS_DETECT_BOTH, GET_CORR_1) }),
           8: (1023, 9, {'pre': (APPLY_CORR_1,),
                         'post': (RUN_LD, ALIAS_DETECT_BOTH) }),
           9: (1023, 10, {'pre': (),
                          'post': (RUN_LD, ALIAS_DETECT_BOTH, GET_CORR_1) }),
           10: (1023, 11, {'pre': (APPLY_CORR_1,),
                          'post': (RUN_LD, ALIAS_DETECT_BOTH) }),
           11: (1023, 12, {'pre': (),
                          'post': (RUN_LD, ALIAS_DETECT_BOTH, GET_CORR_1) }),
           12: (1023, 13, {'pre': (APPLY_CORR_1,),
                           'post': (RUN_LD, ALIAS_DETECT_BOTH) }),
           13: (1023, 14, {'pre': (),
                          'post': (RUN_LD, ALIAS_DETECT_BOTH, GET_CORR_1) }),
           14: (1023, 15, {'pre': (APPLY_CORR_1,),
                           'post': (RUN_LD, ALIAS_DETECT_BOTH) }),
           15: (1023, 16, {'pre': (),
                          'post': (RUN_LD, ALIAS_DETECT_BOTH, GET_CORR_1) }),
           16: (1023, 17, {'pre': (APPLY_CORR_1,),
                           'post': (RUN_LD, ALIAS_DETECT_BOTH) }),
           17: (1023, 18, {'pre': (),
                          'post': (RUN_LD, ALIAS_DETECT_BOTH, GET_CORR_1) }),
           18: (1023, 19, {'pre': (APPLY_CORR_1,),
                           'post': (RUN_LD, ALIAS_DETECT_BOTH) }),
           19: (1023, 0, {'pre': (),
                          'post': (RUN_LD, ALIAS_DETECT_2ND, GET_CORR_1) }) },
        }
      },

    '4ms':
    { 'no_bit_sync':
      { 'short_n_long':
        { 'coherent_ms': 4,
          'alias_acc_length_ms': 500,
          0: (1023, 1, {'pre': (), 'post': (RUN_LD,)}),
          1: (1023, 2, {'pre': (APPLY_CORR_1,), 'post': (RUN_LD,)}),
          2: (1023, 3, {'pre': (), 'post': (RUN_LD,)}),
          3: (1023, 0, {'pre': (), 'post': (RUN_LD, GET_CORR_1)}) },

        'ideal':
        { 'coherent_ms': 4,
          'alias_acc_length_ms': 500,
          0: (1023, 1, {'pre': (APPLY_CORR_1,), 'post': (RUN_LD,)}),
          1: (1023, 2, {'pre': (), 'post': (RUN_LD,)}),
          2: (1023, 3, {'pre': (), 'post': (RUN_LD,)}),
          3: (1023, 0, {'pre': (), 'post': (RUN_LD, GET_CORR_1)}) }
      },
      'bit_sync':
      { 'short_n_long':
        {  'coherent_ms': 4,
           'alias_acc_length_ms': 500,

           0: (1023, 1, {'pre': (),
                         'post': (RUN_LD, ALIAS_DETECT_1ST) }),
           1: (1023, 2, {'pre': (APPLY_CORR_1,),
                         'post': (RUN_LD, ALIAS_DETECT_BOTH) }),
           2: (1023, 3, {'pre': (),
                         'post': (RUN_LD, ALIAS_DETECT_BOTH) }),
           3: (1023, 4, {'pre': (),
                         'post': (RUN_LD, ALIAS_DETECT_BOTH, GET_CORR_1) }),
           4: (1023, 5, {'pre': (),
                         'post': (RUN_LD, ALIAS_DETECT_BOTH) }),
           5: (1023, 6, {'pre': (APPLY_CORR_1,),
                         'post': (RUN_LD, ALIAS_DETECT_BOTH) }),
           6: (1023, 7, {'pre': (),
                         'post': (RUN_LD, ALIAS_DETECT_BOTH) }),
           7: (1023, 8, {'pre': (),
                         'post': (RUN_LD, ALIAS_DETECT_BOTH, GET_CORR_1) }),
           8: (1023, 9, {'pre': (),
                         'post': (RUN_LD, ALIAS_DETECT_BOTH) }),
           9: (1023, 10, {'pre': (APPLY_CORR_1,),
                          'post': (RUN_LD, ALIAS_DETECT_BOTH) }),
           10: (1023, 11, {'pre': (),
                          'post': (RUN_LD, ALIAS_DETECT_BOTH) }),
           11: (1023, 12, {'pre': (),
                           'post': (RUN_LD, ALIAS_DETECT_BOTH, GET_CORR_1) }),
           12: (1023, 13, {'pre': (),
                          'post': (RUN_LD, ALIAS_DETECT_BOTH) }),
           13: (1023, 14, {'pre': (APPLY_CORR_1,),
                           'post': (RUN_LD, ALIAS_DETECT_BOTH) }),
           14: (1023, 15, {'pre': (),
                          'post': (RUN_LD, ALIAS_DETECT_BOTH) }),
           15: (1023, 16, {'pre': (),
                           'post': (RUN_LD, ALIAS_DETECT_BOTH, GET_CORR_1) }),
           16: (1023, 17, {'pre': (),
                          'post': (RUN_LD, ALIAS_DETECT_BOTH) }),
           17: (1023, 18, {'pre': (APPLY_CORR_1,),
                           'post': (RUN_LD, ALIAS_DETECT_BOTH) }),
           18: (1023, 19, {'pre': (),
                          'post': (RUN_LD, ALIAS_DETECT_BOTH) }),
           19: (1023, 0, {'pre': (),
                          'post': (RUN_LD, ALIAS_DETECT_2ND, GET_CORR_1) }) },
        'ideal':
        {  'coherent_ms': 4,
           'alias_acc_length_ms': 500,

           0: (1023, 1, {'pre': (APPLY_CORR_1,),
                         'post': (RUN_LD, ALIAS_DETECT_1ST) }),
           1: (1023, 2, {'pre': (),
                         'post': (RUN_LD, ALIAS_DETECT_BOTH) }),
           2: (1023, 3, {'pre': (),
                         'post': (RUN_LD, ALIAS_DETECT_BOTH) }),
           3: (1023, 4, {'pre': (),
                         'post': (RUN_LD, ALIAS_DETECT_BOTH, GET_CORR_1) }),
           4: (1023, 5, {'pre': (APPLY_CORR_1,),
                         'post': (RUN_LD, ALIAS_DETECT_BOTH) }),
           5: (1023, 6, {'pre': (),
                         'post': (RUN_LD, ALIAS_DETECT_BOTH) }),
           6: (1023, 7, {'pre': (),
                         'post': (RUN_LD, ALIAS_DETECT_BOTH) }),
           7: (1023, 8, {'pre': (),
                         'post': (RUN_LD, ALIAS_DETECT_BOTH, GET_CORR_1) }),
           8: (1023, 9, {'pre': (APPLY_CORR_1,),
                         'post': (RUN_LD, ALIAS_DETECT_BOTH) }),
           9: (1023, 10, {'pre': (),
                          'post': (RUN_LD, ALIAS_DETECT_BOTH) }),
           10: (1023, 11, {'pre': (),
                          'post': (RUN_LD, ALIAS_DETECT_BOTH) }),
           11: (1023, 12, {'pre': (),
                          'post': (RUN_LD, ALIAS_DETECT_BOTH, GET_CORR_1) }),
           12: (1023, 13, {'pre': (APPLY_CORR_1,),
                           'post': (RUN_LD, ALIAS_DETECT_BOTH) }),
           13: (1023, 14, {'pre': (),
                          'post': (RUN_LD, ALIAS_DETECT_BOTH) }),
           14: (1023, 15, {'pre': (),
                           'post': (RUN_LD, ALIAS_DETECT_BOTH) }),
           15: (1023, 16, {'pre': (),
                          'post': (RUN_LD, ALIAS_DETECT_BOTH, GET_CORR_1) }),
           16: (1023, 17, {'pre': (APPLY_CORR_1,),
                           'post': (RUN_LD, ALIAS_DETECT_BOTH) }),
           17: (1023, 18, {'pre': (),
                          'post': (RUN_LD, ALIAS_DETECT_BOTH) }),
           18: (1023, 19, {'pre': (),
                           'post': (RUN_LD, ALIAS_DETECT_BOTH) }),
           19: (1023, 0, {'pre': (),
                          'post': (RUN_LD, ALIAS_DETECT_2ND, GET_CORR_1) }) },
        }
      },

    '5ms':
    { 'no_bit_sync':
      { 'short_n_long':
        { 'coherent_ms': 5,
          'alias_acc_length_ms': 500,
          0: (1023, 1, {'pre': (), 'post': (RUN_LD,)}),
          1: (1023, 2, {'pre': (APPLY_CORR_1,), 'post': (RUN_LD,)}),
          2: (1023, 3, {'pre': (), 'post': (RUN_LD,)}),
          3: (1023, 4, {'pre': (), 'post': (RUN_LD,)}),
          4: (1023, 0, {'pre': (), 'post': (RUN_LD, GET_CORR_1)}) },

        'ideal':
        { 'coherent_ms': 5,
          'alias_acc_length_ms': 500,
          0: (1023, 1, {'pre': (APPLY_CORR_1,), 'post': (RUN_LD,)}),
          1: (1023, 2, {'pre': (), 'post': (RUN_LD,)}),
          2: (1023, 3, {'pre': (), 'post': (RUN_LD,)}),
          3: (1023, 4, {'pre': (), 'post': (RUN_LD,)}),
          4: (1023, 0, {'pre': (), 'post': (RUN_LD, GET_CORR_1)}) }
      },
      'bit_sync':
      { 'short_n_long':
        {  'coherent_ms': 5,
           'alias_acc_length_ms': 500,

           0: (1023, 1, {'pre': (),
                         'post': (RUN_LD, ALIAS_DETECT_1ST) }),
           1: (1023, 2, {'pre': (APPLY_CORR_1,),
                         'post': (RUN_LD, ALIAS_DETECT_BOTH) }),
           2: (1023, 3, {'pre': (),
                         'post': (RUN_LD, ALIAS_DETECT_BOTH) }),
           3: (1023, 4, {'pre': (),
                         'post': (RUN_LD, ALIAS_DETECT_BOTH) }),
           4: (1023, 5, {'pre': (),
                         'post': (RUN_LD, ALIAS_DETECT_BOTH, GET_CORR_1) }),
           5: (1023, 6, {'pre': (),
                         'post': (RUN_LD, ALIAS_DETECT_BOTH) }),
           6: (1023, 7, {'pre': (APPLY_CORR_1,),
                         'post': (RUN_LD, ALIAS_DETECT_BOTH) }),
           7: (1023, 8, {'pre': (),
                         'post': (RUN_LD, ALIAS_DETECT_BOTH) }),
           8: (1023, 9, {'pre': (),
                         'post': (RUN_LD, ALIAS_DETECT_BOTH) }),
           9: (1023, 10, {'pre': (),
                          'post': (RUN_LD, ALIAS_DETECT_BOTH, GET_CORR_1) }),
           10: (1023, 11, {'pre': (),
                          'post': (RUN_LD, ALIAS_DETECT_BOTH) }),
           11: (1023, 12, {'pre': (APPLY_CORR_1,),
                           'post': (RUN_LD, ALIAS_DETECT_BOTH) }),
           12: (1023, 13, {'pre': (),
                          'post': (RUN_LD, ALIAS_DETECT_BOTH) }),
           13: (1023, 14, {'pre': (),
                           'post': (RUN_LD, ALIAS_DETECT_BOTH) }),
           14: (1023, 15, {'pre': (),
                          'post': (RUN_LD, ALIAS_DETECT_BOTH, GET_CORR_1) }),
           15: (1023, 16, {'pre': (),
                           'post': (RUN_LD, ALIAS_DETECT_BOTH) }),
           16: (1023, 17, {'pre': (APPLY_CORR_1,),
                          'post': (RUN_LD, ALIAS_DETECT_BOTH) }),
           17: (1023, 18, {'pre': (),
                           'post': (RUN_LD, ALIAS_DETECT_BOTH) }),
           18: (1023, 19, {'pre': (),
                          'post': (RUN_LD, ALIAS_DETECT_BOTH) }),
           19: (1023, 0, {'pre': (),
                          'post': (RUN_LD, ALIAS_DETECT_2ND, GET_CORR_1) }) },
        'ideal':
        {  'coherent_ms': 5,
           'alias_acc_length_ms': 500,

           0: (1023, 1, {'pre': (APPLY_CORR_1,),
                         'post': (RUN_LD, ALIAS_DETECT_1ST) }),
           1: (1023, 2, {'pre': (),
                         'post': (RUN_LD, ALIAS_DETECT_BOTH) }),
           2: (1023, 3, {'pre': (),
                         'post': (RUN_LD, ALIAS_DETECT_BOTH) }),
           3: (1023, 4, {'pre': (),
                         'post': (RUN_LD, ALIAS_DETECT_BOTH) }),
           4: (1023, 5, {'pre': (),
                         'post': (RUN_LD, ALIAS_DETECT_BOTH, GET_CORR_1) }),
           5: (1023, 6, {'pre': (APPLY_CORR_1,),
                         'post': (RUN_LD, ALIAS_DETECT_BOTH) }),
           6: (1023, 7, {'pre': (),
                         'post': (RUN_LD, ALIAS_DETECT_BOTH) }),
           7: (1023, 8, {'pre': (),
                         'post': (RUN_LD, ALIAS_DETECT_BOTH) }),
           8: (1023, 9, {'pre': (),
                         'post': (RUN_LD, ALIAS_DETECT_BOTH) }),
           9: (1023, 10, {'pre': (),
                          'post': (RUN_LD, ALIAS_DETECT_BOTH, GET_CORR_1) }),
           10: (1023, 11, {'pre': (APPLY_CORR_1,),
                          'post': (RUN_LD, ALIAS_DETECT_BOTH) }),
           11: (1023, 12, {'pre': (),
                          'post': (RUN_LD, ALIAS_DETECT_BOTH) }),
           12: (1023, 13, {'pre': (),
                           'post': (RUN_LD, ALIAS_DETECT_BOTH) }),
           13: (1023, 14, {'pre': (),
                          'post': (RUN_LD, ALIAS_DETECT_BOTH) }),
           14: (1023, 15, {'pre': (),
                           'post': (RUN_LD, ALIAS_DETECT_BOTH, GET_CORR_1) }),
           15: (1023, 16, {'pre': (APPLY_CORR_1,),
                          'post': (RUN_LD, ALIAS_DETECT_BOTH) }),
           16: (1023, 17, {'pre': (),
                           'post': (RUN_LD, ALIAS_DETECT_BOTH) }),
           17: (1023, 18, {'pre': (),
                          'post': (RUN_LD, ALIAS_DETECT_BOTH) }),
           18: (1023, 19, {'pre': (),
                           'post': (RUN_LD, ALIAS_DETECT_BOTH) }),
           19: (1023, 0, {'pre': (),
                          'post': (RUN_LD, ALIAS_DETECT_2ND, GET_CORR_1) }) },
        }
      },

    '10ms':
    { 'no_bit_sync':
      { 'short_n_long':
        { 'coherent_ms': 10,
          'alias_acc_length_ms': 500,
          0: (1023, 1, {'pre': (), 'post': (RUN_LD,)}),
          1: (1023, 2, {'pre': (APPLY_CORR_1,), 'post': (RUN_LD,)}),
          2: (1023, 3, {'pre': (), 'post': (RUN_LD,)}),
          3: (1023, 4, {'pre': (), 'post': (RUN_LD,)}),
          4: (1023, 5, {'pre': (), 'post': (RUN_LD,)}),
          5: (1023, 6, {'pre': (), 'post': (RUN_LD,)}),
          6: (1023, 7, {'pre': (), 'post': (RUN_LD,)}),
          7: (1023, 8, {'pre': (), 'post': (RUN_LD,)}),
          8: (1023, 9, {'pre': (), 'post': (RUN_LD,)}),
          9: (1023, 0, {'pre': (), 'post': (RUN_LD, GET_CORR_1)}) },

        'ideal':
        { 'coherent_ms': 10,
          'alias_acc_length_ms': 500,
          0: (1023, 1, {'pre': (APPLY_CORR_1,), 'post': (RUN_LD,)}),
          1: (1023, 2, {'pre': (), 'post': (RUN_LD,)}),
          2: (1023, 3, {'pre': (), 'post': (RUN_LD,)}),
          3: (1023, 4, {'pre': (), 'post': (RUN_LD,)}),
          4: (1023, 5, {'pre': (), 'post': (RUN_LD,)}),
          5: (1023, 6, {'pre': (), 'post': (RUN_LD,)}),
          6: (1023, 7, {'pre': (), 'post': (RUN_LD,)}),
          7: (1023, 8, {'pre': (), 'post': (RUN_LD,)}),
          8: (1023, 9, {'pre': (), 'post': (RUN_LD,)}),
          9: (1023, 0, {'pre': (), 'post': (RUN_LD, GET_CORR_1)}) }
      },
      'bit_sync':
      { 'short_n_long':
        {  'coherent_ms': 10,
           'alias_acc_length_ms': 500,

           0: (1023, 1, {'pre': (),
                         'post': (RUN_LD, ALIAS_DETECT_1ST) }),
           1: (1023, 2, {'pre': (APPLY_CORR_1,),
                         'post': (RUN_LD, ALIAS_DETECT_BOTH) }),
           2: (1023, 3, {'pre': (),
                         'post': (RUN_LD, ALIAS_DETECT_BOTH) }),
           3: (1023, 4, {'pre': (),
                         'post': (RUN_LD, ALIAS_DETECT_BOTH) }),
           4: (1023, 5, {'pre': (),
                         'post': (RUN_LD, ALIAS_DETECT_BOTH) }),
           5: (1023, 6, {'pre': (),
                         'post': (RUN_LD, ALIAS_DETECT_BOTH) }),
           6: (1023, 7, {'pre': (),
                         'post': (RUN_LD, ALIAS_DETECT_BOTH) }),
           7: (1023, 8, {'pre': (),
                         'post': (RUN_LD, ALIAS_DETECT_BOTH) }),
           8: (1023, 9, {'pre': (),
                         'post': (RUN_LD, ALIAS_DETECT_BOTH) }),
           9: (1023, 10, {'pre': (),
                          'post': (RUN_LD, ALIAS_DETECT_BOTH, GET_CORR_1) }),
           10: (1023, 11, {'pre': (),
                          'post': (RUN_LD, ALIAS_DETECT_BOTH) }),
           11: (1023, 12, {'pre': (APPLY_CORR_1,),
                           'post': (RUN_LD, ALIAS_DETECT_BOTH) }),
           12: (1023, 13, {'pre': (),
                          'post': (RUN_LD, ALIAS_DETECT_BOTH) }),
           13: (1023, 14, {'pre': (),
                           'post': (RUN_LD, ALIAS_DETECT_BOTH) }),
           14: (1023, 15, {'pre': (),
                          'post': (RUN_LD, ALIAS_DETECT_BOTH) }),
           15: (1023, 16, {'pre': (),
                           'post': (RUN_LD, ALIAS_DETECT_BOTH) }),
           16: (1023, 17, {'pre': (),
                          'post': (RUN_LD, ALIAS_DETECT_BOTH) }),
           17: (1023, 18, {'pre': (),
                           'post': (RUN_LD, ALIAS_DETECT_BOTH) }),
           18: (1023, 19, {'pre': (),
                          'post': (RUN_LD, ALIAS_DETECT_BOTH) }),
           19: (1023, 0, {'pre': (),
                          'post': (RUN_LD, ALIAS_DETECT_2ND, GET_CORR_1) }) },
        'ideal':
        {  'coherent_ms': 10,
           'alias_acc_length_ms': 500,

           0: (1023, 1, {'pre': (APPLY_CORR_1,),
                         'post': (RUN_LD, ALIAS_DETECT_1ST) }),
           1: (1023, 2, {'pre': (),
                         'post': (RUN_LD, ALIAS_DETECT_BOTH) }),
           2: (1023, 3, {'pre': (),
                         'post': (RUN_LD, ALIAS_DETECT_BOTH) }),
           3: (1023, 4, {'pre': (),
                         'post': (RUN_LD, ALIAS_DETECT_BOTH) }),
           4: (1023, 5, {'pre': (),
                         'post': (RUN_LD, ALIAS_DETECT_BOTH) }),
           5: (1023, 6, {'pre': (),
                         'post': (RUN_LD, ALIAS_DETECT_BOTH) }),
           6: (1023, 7, {'pre': (),
                         'post': (RUN_LD, ALIAS_DETECT_BOTH) }),
           7: (1023, 8, {'pre': (),
                         'post': (RUN_LD, ALIAS_DETECT_BOTH) }),
           8: (1023, 9, {'pre': (),
                         'post': (RUN_LD, ALIAS_DETECT_BOTH) }),
           9: (1023, 10, {'pre': (),
                          'post': (RUN_LD, ALIAS_DETECT_BOTH, GET_CORR_1) }),
           10: (1023, 11, {'pre': (APPLY_CORR_1,),
                          'post': (RUN_LD, ALIAS_DETECT_BOTH) }),
           11: (1023, 12, {'pre': (),
                          'post': (RUN_LD, ALIAS_DETECT_BOTH) }),
           12: (1023, 13, {'pre': (),
                           'post': (RUN_LD, ALIAS_DETECT_BOTH) }),
           13: (1023, 14, {'pre': (),
                          'post': (RUN_LD, ALIAS_DETECT_BOTH) }),
           14: (1023, 15, {'pre': (),
                           'post': (RUN_LD, ALIAS_DETECT_BOTH) }),
           15: (1023, 16, {'pre': (),
                          'post': (RUN_LD, ALIAS_DETECT_BOTH) }),
           16: (1023, 17, {'pre': (),
                           'post': (RUN_LD, ALIAS_DETECT_BOTH) }),
           17: (1023, 18, {'pre': (),
                          'post': (RUN_LD, ALIAS_DETECT_BOTH) }),
           18: (1023, 19, {'pre': (),
                           'post': (RUN_LD, ALIAS_DETECT_BOTH) }),
           19: (1023, 0, {'pre': (),
                          'post': (RUN_LD, ALIAS_DETECT_2ND, GET_CORR_1) }) },
        }
      },

    '20ms':
    { 'bit_sync':
      { 'short_n_long':
        {  'coherent_ms': 20,
           't_diff_s': 1023 * 1 / gps_constants.l1ca_chip_rate,
           'alias_acc_length_ms': 500,

           0: (1023, 1, {'pre': (),
                         'post': (RUN_LD, ALIAS_DETECT_1ST,) }),
           1: (1023, 2, {'pre': (APPLY_CORR_1,),
                         'post': (RUN_LD, ALIAS_DETECT_BOTH,) }),
           2: (1023, 3, {'pre': (),
                         'post': (RUN_LD, ALIAS_DETECT_BOTH,) }),
           3: (1023, 4, {'pre': (),
                         'post': (RUN_LD, ALIAS_DETECT_BOTH,) }),
           4: (1023, 5, {'pre': (),
                         'post': (RUN_LD, ALIAS_DETECT_BOTH,) }),
           5: (1023, 6, {'pre': (),
                         'post': (RUN_LD, ALIAS_DETECT_BOTH,) }),
           6: (1023, 7, {'pre': (),
                         'post': (RUN_LD, ALIAS_DETECT_BOTH,) }),
           7: (1023, 8, {'pre': (),
                         'post': (RUN_LD, ALIAS_DETECT_BOTH,) }),
           8: (1023, 9, {'pre': (),
                         'post': (RUN_LD, ALIAS_DETECT_BOTH,) }),
           9: (1023, 10, {'pre': (),
                         'post': (RUN_LD, ALIAS_DETECT_BOTH,) }),
           10: (1023, 11, {'pre': (),
                          'post': (RUN_LD, ALIAS_DETECT_BOTH,) }),
           11: (1023, 12, {'pre': (),
                          'post': (RUN_LD, ALIAS_DETECT_BOTH,) }),
           12: (1023, 13, {'pre': (),
                          'post': (RUN_LD, ALIAS_DETECT_BOTH,) }),
           13: (1023, 14, {'pre': (),
                          'post': (RUN_LD, ALIAS_DETECT_BOTH,) }),
           14: (1023, 15, {'pre': (),
                          'post': (RUN_LD, ALIAS_DETECT_BOTH,) }),
           15: (1023, 16, {'pre': (),
                          'post': (RUN_LD, ALIAS_DETECT_BOTH,) }),
           16: (1023, 17, {'pre': (),
                          'post': (RUN_LD, ALIAS_DETECT_BOTH,) }),
           17: (1023, 18, {'pre': (),
                          'post': (RUN_LD, ALIAS_DETECT_BOTH,) }),
           18: (1023, 19, {'pre': (),
                          'post': (RUN_LD, ALIAS_DETECT_BOTH,) }),
           19: (1023, 0, {'pre': (),
                          'post': (RUN_LD, ALIAS_DETECT_2ND, GET_CORR_1) }) },
        'ideal':
        {  'coherent_ms': 20,
           't_diff_s': 1023 * 1 / gps_constants.l1ca_chip_rate,
           'alias_acc_length_ms': 500,

           0: (1023, 1, {'pre': (APPLY_CORR_1,),
                         'post': (RUN_LD, ALIAS_DETECT_1ST,) }),
           1: (1023, 2, {'pre': (),
                         'post': (RUN_LD, ALIAS_DETECT_BOTH,) }),
           2: (1023, 3, {'pre': (),
                         'post': (RUN_LD, ALIAS_DETECT_BOTH,) }),
           3: (1023, 4, {'pre': (),
                         'post': (RUN_LD, ALIAS_DETECT_BOTH,) }),
           4: (1023, 5, {'pre': (),
                         'post': (RUN_LD, ALIAS_DETECT_BOTH,) }),
           5: (1023, 6, {'pre': (),
                         'post': (RUN_LD, ALIAS_DETECT_BOTH,) }),
           6: (1023, 7, {'pre': (),
                         'post': (RUN_LD, ALIAS_DETECT_BOTH,) }),
           7: (1023, 8, {'pre': (),
                         'post': (RUN_LD, ALIAS_DETECT_BOTH,) }),
           8: (1023, 9, {'pre': (),
                         'post': (RUN_LD, ALIAS_DETECT_BOTH,) }),
           9: (1023, 10, {'pre': (),
                         'post': (RUN_LD, ALIAS_DETECT_BOTH,) }),
           10: (1023, 11, {'pre': (),
                          'post': (RUN_LD, ALIAS_DETECT_BOTH,) }),
           11: (1023, 12, {'pre': (),
                          'post': (RUN_LD, ALIAS_DETECT_BOTH,) }),
           12: (1023, 13, {'pre': (),
                          'post': (RUN_LD, ALIAS_DETECT_BOTH,) }),
           13: (1023, 14, {'pre': (),
                          'post': (RUN_LD, ALIAS_DETECT_BOTH,) }),
           14: (1023, 15, {'pre': (),
                          'post': (RUN_LD, ALIAS_DETECT_BOTH,) }),
           15: (1023, 16, {'pre': (),
                          'post': (RUN_LD, ALIAS_DETECT_BOTH,) }),
           16: (1023, 17, {'pre': (),
                          'post': (RUN_LD, ALIAS_DETECT_BOTH,) }),
           17: (1023, 18, {'pre': (),
                          'post': (RUN_LD, ALIAS_DETECT_BOTH,) }),
           18: (1023, 19, {'pre': (),
                          'post': (RUN_LD, ALIAS_DETECT_BOTH,) }),
           19: (1023, 0, {'pre': (),
                          'post': (RUN_LD, ALIAS_DETECT_2ND, GET_CORR_1) }) }
        }
      }
    }

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

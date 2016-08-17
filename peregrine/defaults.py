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
    'fll_bw': (1, 0),
    'pll_bw': (40, 35, 30, 25, 20, 18, 16, 14, 12, 10, 8, 7, 6.5, 6, 5.5, 5),
    'coherent_ms': (1, 2, 4, 5, 10, 20) }

l2c_track_params = {
    'fll_bw': (1, 0),
    'pll_bw': (20, 18, 16, 14, 12, 10, 8, 7, 6.5, 6, 5.5, 5),
    'coherent_ms': (20,) }

glol1_track_params = {
    'fll_bw': (2, 1, 0),
    'pll_bw': (40, 20, 18, 16, 14, 12, 10, 8, 7, 6.5, 6, 5.5, 5),
    'coherent_ms': (1,) }

l1ca_loop_filter_params_template = {
     'code_params': (1., 0.7, 1.),   # NBW, zeta, k
     'carr_params': (20., 0.7, 1.),   # NBW, zeta, k
     'loop_freq': 1000.,             # 1000/coherent_ms
     'carr_freq_b1': 1.,             # FLL NBW
     'carr_to_code': 1540.           # carr_to_code
    }

l2c_loop_filter_params_template = {
     'code_params': (1., 0.7, 1.),   # NBW, zeta, k
     'carr_params': (20., 0.7, 1.),   # NBW, zeta, k
     'loop_freq': 1000.,             # 1000/coherent_ms
     'carr_freq_b1': 1.,             # FLL NBW
     'carr_to_code': 1200.           # carr_to_code
    }

glol1_loop_filter_params_template = {
     'code_params': (1., 0.7, 1.),   # NBW, zeta, k
     'carr_params': (20., 0.7, 1.),   # NBW, zeta, k
     'loop_freq': 1000.,             # 1000/coherent_ms
     'carr_freq_b1': 1.,             # FLL NBW
     'carr_to_code': 3135.0293542074364 # carr_to_code
    }

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
COMPENSATE_BIT_POLARITY = 9
USE_COMPENSATED_BIT = 10
PREPARE_BIT_COMPENSATION = 11

glo_fsm_states = \
  { '1ms':
    { 'no_bit_sync':
      { 'short_n_long':
        { 0: (511, 1, {'pre': (APPLY_CORR_1,),
                       'post': (RUN_LD, GET_CORR_1, ALIAS_DETECT_1ST)}),
          1: (511, 0, {'pre': (APPLY_CORR_2,),
                       'post': (RUN_LD, GET_CORR_2, ALIAS_DETECT_2ND)}) },

        'ideal':
        { 0: (511, 1, {'pre': (APPLY_CORR_1,),
                       'post': (RUN_LD, GET_CORR_1, ALIAS_DETECT_1ST)}),
          1: (511, 0, {'pre': (APPLY_CORR_1,),
                       'post': (RUN_LD, GET_CORR_1, ALIAS_DETECT_2ND)}) }
      }
    }
  }

gps_fsm_states = \
  { '1ms':
    { 'no_bit_sync':
      { 'short_n_long':
        { 0: (1023, 1, {'pre': (APPLY_CORR_1,),
                        'post': (RUN_LD, GET_CORR_1, ALIAS_DETECT_1ST)}),
          1: (1023, 0, {'pre': (APPLY_CORR_2,),
                        'post': (RUN_LD, GET_CORR_2, ALIAS_DETECT_2ND)}) },

        'ideal':
        { 0: (1023, 1, {'pre': (APPLY_CORR_1,),
                        'post': (RUN_LD, GET_CORR_1, ALIAS_DETECT_1ST)}),
          1: (1023, 0, {'pre': (APPLY_CORR_1,),
                        'post': (RUN_LD, GET_CORR_1, ALIAS_DETECT_2ND)}) }
      },
      'bit_sync':
      { 'short_n_long':
        {  0: (1023, 1, {'pre': (APPLY_CORR_1,),
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
        {  0: (1023, 1, {'pre': (APPLY_CORR_1,),
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
    { 'bit_sync':
      { 'short_n_long':
        {  0: (1023, 1, {'pre': (),
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
        {  0: (1023, 1, {'pre': (APPLY_CORR_1,),
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
    { 'bit_sync':
      { 'short_n_long':
        {  0: (1023, 1, {'pre': (),
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
        {  0: (1023, 1, {'pre': (APPLY_CORR_1,),
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
    { 'bit_sync':
      { 'short_n_long':
        {  0: (1023, 1, {'pre': (),
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
        {  0: (1023, 1, {'pre': (APPLY_CORR_1,),
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
    { 'bit_sync':
      { 'short_n_long':
        {  0: (1023, 1, {'pre': (),
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
        {  0: (1023, 1, {'pre': (APPLY_CORR_1,),
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
        {  0: (1023, 1, {'pre': (),
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
        {  0: (1023, 1, {'pre': (APPLY_CORR_1,),
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
                          'post': (RUN_LD, ALIAS_DETECT_2ND, GET_CORR_1) }) },
        }
      },

    '40ms':
    { 'bit_sync':
      { 'short_n_long':
        {  0: (1023, 1, {'pre': (PREPARE_BIT_COMPENSATION,),
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
                          'post': (RUN_LD, ALIAS_DETECT_2ND,) }),
           19: (1023, 20, {'pre': (),
                          'post': (RUN_LD,
                                   ALIAS_DETECT_1ST,
                                   COMPENSATE_BIT_POLARITY) }),
           20: (1023, 21, {'pre': (),
                         'post': (RUN_LD, ALIAS_DETECT_BOTH,) }),
           21: (1023, 22, {'pre': (),
                         'post': (RUN_LD, ALIAS_DETECT_BOTH,) }),
           22: (1023, 23, {'pre': (),
                         'post': (RUN_LD, ALIAS_DETECT_BOTH,) }),
           23: (1023, 24, {'pre': (),
                         'post': (RUN_LD, ALIAS_DETECT_BOTH,) }),
           24: (1023, 25, {'pre': (),
                         'post': (RUN_LD, ALIAS_DETECT_BOTH,) }),
           25: (1023, 26, {'pre': (),
                         'post': (RUN_LD, ALIAS_DETECT_BOTH,) }),
           26: (1023, 27, {'pre': (),
                         'post': (RUN_LD, ALIAS_DETECT_BOTH,) }),
           27: (1023, 28, {'pre': (),
                         'post': (RUN_LD, ALIAS_DETECT_BOTH,) }),
           28: (1023, 29, {'pre': (),
                         'post': (RUN_LD, ALIAS_DETECT_BOTH,) }),
           29: (1023, 30, {'pre': (),
                         'post': (RUN_LD, ALIAS_DETECT_BOTH,) }),
           30: (1023, 31, {'pre': (),
                          'post': (RUN_LD, ALIAS_DETECT_BOTH,) }),
           31: (1023, 32, {'pre': (),
                          'post': (RUN_LD, ALIAS_DETECT_BOTH,) }),
           32: (1023, 33, {'pre': (),
                          'post': (RUN_LD, ALIAS_DETECT_BOTH,) }),
           33: (1023, 34, {'pre': (),
                          'post': (RUN_LD, ALIAS_DETECT_BOTH,) }),
           34: (1023, 35, {'pre': (),
                          'post': (RUN_LD, ALIAS_DETECT_BOTH,) }),
           35: (1023, 36, {'pre': (),
                          'post': (RUN_LD, ALIAS_DETECT_BOTH,) }),
           36: (1023, 37, {'pre': (),
                          'post': (RUN_LD, ALIAS_DETECT_BOTH,) }),
           37: (1023, 38, {'pre': (),
                          'post': (RUN_LD, ALIAS_DETECT_BOTH,) }),
           38: (1023, 39, {'pre': (),
                          'post': (RUN_LD, ALIAS_DETECT_BOTH,) }),
           39: (1023, 0, {'pre': (),
                          'post': (RUN_LD,
                                   ALIAS_DETECT_2ND,
                                   GET_CORR_1,
                                   COMPENSATE_BIT_POLARITY,
                                   USE_COMPENSATED_BIT) }) },
        'ideal':
        {  0: (1023, 1, {'pre': (APPLY_CORR_1,),
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
                          'post': (RUN_LD, ALIAS_DETECT_2ND, GET_CORR_1) }) },
        }
      },

    '80ms':
    { 'bit_sync':
      { 'short_n_long':
        {  0: (1023, 1, {'pre': (PREPARE_BIT_COMPENSATION,),
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
                          'post': (RUN_LD, ALIAS_DETECT_2ND,) }),
           19: (1023, 20, {'pre': (),
                          'post': (RUN_LD,
                                   ALIAS_DETECT_1ST,
                                   COMPENSATE_BIT_POLARITY) }),
           20: (1023, 21, {'pre': (),
                         'post': (RUN_LD, ALIAS_DETECT_BOTH,) }),
           21: (1023, 22, {'pre': (),
                         'post': (RUN_LD, ALIAS_DETECT_BOTH,) }),
           22: (1023, 23, {'pre': (),
                         'post': (RUN_LD, ALIAS_DETECT_BOTH,) }),
           23: (1023, 24, {'pre': (),
                         'post': (RUN_LD, ALIAS_DETECT_BOTH,) }),
           24: (1023, 25, {'pre': (),
                         'post': (RUN_LD, ALIAS_DETECT_BOTH,) }),
           25: (1023, 26, {'pre': (),
                         'post': (RUN_LD, ALIAS_DETECT_BOTH,) }),
           26: (1023, 27, {'pre': (),
                         'post': (RUN_LD, ALIAS_DETECT_BOTH,) }),
           27: (1023, 28, {'pre': (),
                         'post': (RUN_LD, ALIAS_DETECT_BOTH,) }),
           28: (1023, 29, {'pre': (),
                         'post': (RUN_LD, ALIAS_DETECT_BOTH,) }),
           29: (1023, 30, {'pre': (),
                         'post': (RUN_LD, ALIAS_DETECT_BOTH,) }),
           30: (1023, 31, {'pre': (),
                          'post': (RUN_LD, ALIAS_DETECT_BOTH,) }),
           31: (1023, 32, {'pre': (),
                          'post': (RUN_LD, ALIAS_DETECT_BOTH,) }),
           32: (1023, 33, {'pre': (),
                          'post': (RUN_LD, ALIAS_DETECT_BOTH,) }),
           33: (1023, 34, {'pre': (),
                          'post': (RUN_LD, ALIAS_DETECT_BOTH,) }),
           34: (1023, 35, {'pre': (),
                          'post': (RUN_LD, ALIAS_DETECT_BOTH,) }),
           35: (1023, 36, {'pre': (),
                          'post': (RUN_LD, ALIAS_DETECT_BOTH,) }),
           36: (1023, 37, {'pre': (),
                          'post': (RUN_LD, ALIAS_DETECT_BOTH,) }),
           37: (1023, 38, {'pre': (),
                          'post': (RUN_LD, ALIAS_DETECT_BOTH,) }),
           38: (1023, 39, {'pre': (),
                          'post': (RUN_LD, ALIAS_DETECT_BOTH,) }),
           39: (1023, 40, {'pre': (),
                          'post': (RUN_LD,
                                   ALIAS_DETECT_2ND,
                                   COMPENSATE_BIT_POLARITY,) }),
           40: (1023, 41, {'pre': (),
                         'post': (RUN_LD, ALIAS_DETECT_1ST,) }),
           41: (1023, 42, {'pre': (),
                         'post': (RUN_LD, ALIAS_DETECT_BOTH,) }),
           42: (1023, 43, {'pre': (),
                         'post': (RUN_LD, ALIAS_DETECT_BOTH,) }),
           43: (1023, 44, {'pre': (),
                         'post': (RUN_LD, ALIAS_DETECT_BOTH,) }),
           44: (1023, 45, {'pre': (),
                         'post': (RUN_LD, ALIAS_DETECT_BOTH,) }),
           45: (1023, 46, {'pre': (),
                         'post': (RUN_LD, ALIAS_DETECT_BOTH,) }),
           46: (1023, 47, {'pre': (),
                         'post': (RUN_LD, ALIAS_DETECT_BOTH,) }),
           47: (1023, 48, {'pre': (),
                         'post': (RUN_LD, ALIAS_DETECT_BOTH,) }),
           48: (1023, 49, {'pre': (),
                         'post': (RUN_LD, ALIAS_DETECT_BOTH,) }),
           49: (1023, 50, {'pre': (),
                         'post': (RUN_LD, ALIAS_DETECT_BOTH,) }),
           50: (1023, 51, {'pre': (),
                          'post': (RUN_LD, ALIAS_DETECT_BOTH,) }),
           51: (1023, 52, {'pre': (),
                          'post': (RUN_LD, ALIAS_DETECT_BOTH,) }),
           52: (1023, 53, {'pre': (),
                          'post': (RUN_LD, ALIAS_DETECT_BOTH,) }),
           53: (1023, 54, {'pre': (),
                          'post': (RUN_LD, ALIAS_DETECT_BOTH,) }),
           54: (1023, 55, {'pre': (),
                          'post': (RUN_LD, ALIAS_DETECT_BOTH,) }),
           55: (1023, 56, {'pre': (),
                          'post': (RUN_LD, ALIAS_DETECT_BOTH,) }),
           56: (1023, 57, {'pre': (),
                          'post': (RUN_LD, ALIAS_DETECT_BOTH,) }),
           57: (1023, 58, {'pre': (),
                          'post': (RUN_LD, ALIAS_DETECT_BOTH,) }),
           58: (1023, 59, {'pre': (),
                          'post': (RUN_LD, ALIAS_DETECT_2ND,) }),
           59: (1023, 60, {'pre': (),
                          'post': (RUN_LD,
                                   ALIAS_DETECT_1ST,
                                   COMPENSATE_BIT_POLARITY) }),
           60: (1023, 61, {'pre': (),
                         'post': (RUN_LD, ALIAS_DETECT_BOTH,) }),
           61: (1023, 62, {'pre': (),
                         'post': (RUN_LD, ALIAS_DETECT_BOTH,) }),
           62: (1023, 63, {'pre': (),
                         'post': (RUN_LD, ALIAS_DETECT_BOTH,) }),
           63: (1023, 64, {'pre': (),
                         'post': (RUN_LD, ALIAS_DETECT_BOTH,) }),
           64: (1023, 65, {'pre': (),
                         'post': (RUN_LD, ALIAS_DETECT_BOTH,) }),
           65: (1023, 66, {'pre': (),
                         'post': (RUN_LD, ALIAS_DETECT_BOTH,) }),
           66: (1023, 67, {'pre': (),
                         'post': (RUN_LD, ALIAS_DETECT_BOTH,) }),
           67: (1023, 68, {'pre': (),
                         'post': (RUN_LD, ALIAS_DETECT_BOTH,) }),
           68: (1023, 69, {'pre': (),
                         'post': (RUN_LD, ALIAS_DETECT_BOTH,) }),
           69: (1023, 70, {'pre': (),
                         'post': (RUN_LD, ALIAS_DETECT_BOTH,) }),
           70: (1023, 71, {'pre': (),
                          'post': (RUN_LD, ALIAS_DETECT_BOTH,) }),
           71: (1023, 72, {'pre': (),
                          'post': (RUN_LD, ALIAS_DETECT_BOTH,) }),
           72: (1023, 73, {'pre': (),
                          'post': (RUN_LD, ALIAS_DETECT_BOTH,) }),
           73: (1023, 74, {'pre': (),
                          'post': (RUN_LD, ALIAS_DETECT_BOTH,) }),
           74: (1023, 75, {'pre': (),
                          'post': (RUN_LD, ALIAS_DETECT_BOTH,) }),
           75: (1023, 76, {'pre': (),
                          'post': (RUN_LD, ALIAS_DETECT_BOTH,) }),
           76: (1023, 77, {'pre': (),
                          'post': (RUN_LD, ALIAS_DETECT_BOTH,) }),
           77: (1023, 78, {'pre': (),
                          'post': (RUN_LD, ALIAS_DETECT_BOTH,) }),
           78: (1023, 79, {'pre': (),
                          'post': (RUN_LD, ALIAS_DETECT_BOTH,) }),
           79: (1023, 0, {'pre': (),
                          'post': (RUN_LD,
                                   ALIAS_DETECT_2ND,
                                   GET_CORR_1,
                                   COMPENSATE_BIT_POLARITY,
                                   USE_COMPENSATED_BIT) }) },
        }
      }
    }

# pessimistic set
l1ca_lock_detect_params_pess = {"k1": 0.10, "k2": 1.4, "lp": 200, "lo": 50}

# normal set
l1ca_lock_detect_params_normal = {"k1": 0.2, "k2": .8, "lp": 150, "lo": 50}

# optimal set
l1ca_lock_detect_params_opt = {"k1": 0.02, "k2": 1.1, "lp": 150, "lo": 50}

# extra optimal set
l1ca_lock_detect_params_extraopt = {"k1": 0.02, "k2": 0.8, "lp": 150, "lo": 50}

# disable lock detect
l1ca_lock_detect_params_disable = {"k1": 0.02, "k2": 1e-6, "lp": 1, "lo": 1}

lock_detect_params_slow = {"k1": 0.005, "k2": 1.4, "lp": 200, "lo": 50}
lock_detect_params_fast = (
  (40, {"k1": 0.2, "k2": .80, "lp": 50, "lo": 50}),
  (35, {"k1": 0.2, "k2": .83, "lp": 50, "lo": 50}),
  (30, {"k1": 0.2, "k2": .86, "lp": 50, "lo": 50}),
  (25, {"k1": 0.2, "k2": .89, "lp": 50, "lo": 50}),
  (20, {"k1": 0.2, "k2": .92, "lp": 50, "lo": 50}),
  (15, {"k1": 0.2, "k2": .95, "lp": 50, "lo": 50}),
  (10, {"k1": 0.2, "k2": .98, "lp": 50, "lo": 50}),
  ( 5, {"k1": 0.2, "k2": 1.0, "lp": 50, "lo": 50}) )

tracking_loop_stabilization_time_ms = 50

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

glol1_lock_detect_params = l1ca_lock_detect_params_opt

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

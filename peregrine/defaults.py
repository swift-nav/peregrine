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
file_format = 'int8'
IF = 4.092e6 # Hz
sampling_freq = 16.368e6 # Hz
chipping_rate = 1.023e6 # Hz
code_length = 1023 # chips

code_period = code_length / chipping_rate
samples_per_code = code_period * sampling_freq


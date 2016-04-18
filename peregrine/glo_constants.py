# -*- coding: utf-8 -*-
from gps_constants import c
# GLO system parameters
glo_l1 = 1.602e9  # Hz
glo_l2 = 1.246e9  # Hz
glo_code_len = 511
glo_chip_rate = 0.511e6  # Hz
glo_l1_step = 0.5625e6  # Hz

glo_code_period = glo_code_len / glo_chip_rate
glo_code_wavelength = glo_code_period * c

GLO_L1 = 'glo_l1'

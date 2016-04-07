# These are all from IS-GPS-200G unless otherwise noted

# Some fundamental constants have specific numeric definitions to ensure
# consistent results in curve fits:
c = 2.99792458e8  # m/s
pi = 3.1415926535898

# Physical parameters of the Earth
earth_gm = 3.986005e14  # m^3/s^2 (WGS84 earth's gravitational constant)
omegae_dot = 7.2921151467e-005  # rad/s (WGS84 earth rotation rate)

# GPS system parameters:
l1 = 1.57542e9  # Hz
l2 = 1.22760e9  # Hz
chips_per_code = 1023
chip_rate = 1.023e6  # Hz
nominal_range = 26000e3  # m

# GLO system parameters
glo_l1 = 1.602e9  # Hz
glo_l2 = 1.246e9  # Hz
glo_chips_per_code = 511
glo_chip_rate = 0.511e6  # Hz
glo_l1_step = 0.5625e6  # Hz

# Useful derived quantities:
code_period = chips_per_code / chip_rate
code_wavelength = code_period * c
glo_code_period = glo_chips_per_code / glo_chip_rate
glo_code_wavelength = glo_code_period * c

L1CA = 'l1ca'
L2C = 'l2c'
GLO_L1 = 'glo_l1'

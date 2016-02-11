# These are all from IS-GPS-200G unless otherwise noted

# Some fundamental constants have specific numeric definitions to ensure
# consistent results in curve fits:
c = 2.99792458e8 # m/s
pi = 3.1415926535898

# Physical parameters of the Earth
earth_gm = 3.986005e14 # m^3/s^2 (WGS84 earth's gravitational constant)
omegae_dot = 7.2921151467e-005 # rad/s (WGS84 earth rotation rate)

# GPS system parameters:
l1 = 1.57542e9 # Hz
l2 = 1.22760e9 # Hz
chips_per_code = 1023
chip_rate = 1.023e6 # Hz
nominal_range = 26000e3 # m

# Useful derived quantities:
code_period = chips_per_code / chip_rate
code_wavelength = code_period * c

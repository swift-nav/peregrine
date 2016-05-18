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

l1ca_chip_rate = 1.023e6 # Hz
l1ca_code_length = 1023
l1ca_code_period = l1ca_code_length / l1ca_chip_rate
l1ca_code_wavelength = l1ca_code_period * c

l2c_chip_rate = 1.023e6 # Hz

nominal_range = 26000e3 # m

L1CA = 'l1ca'
L2C = 'l2c'

# This mask describes what GPS satellites are L2C capable
# It is valid as of 2016-05-18
# Up-to-date information is available at for example:
# https://www.unavco.org/projects/project-support/gnss-support/gnss-modernization/gnss-modernization.html
L2C_CAPB = 0xf7814bfd

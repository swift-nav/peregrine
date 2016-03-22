# Copyright (C) 2016 Swift Navigation Inc.
#
# Contact: Dmitry Tatarinov <dmitry.tatarinov@exafore.com>
# This source is subject to the license found in the file 'LICENSE' which must
# be be distributed together with this source. All other rights reserved.
#
# THIS CODE AND INFORMATION IS PROVIDED "AS IS" WITHOUT WARRANTY OF ANY KIND,
# EITHER EXPRESSED OR IMPLIED, INCLUDING BUT NOT LIMITED TO THE IMPLIED
# WARRANTIES OF MERCHANTABILITY AND/OR FITNESS FOR A PARTICULAR PURPOSE.

import numpy as np

__xor_mask = 0
__xor_mask ^= 1 << 3
__xor_mask ^= 1 << 4
__xor_mask ^= 1 << 5
__xor_mask ^= 1 << 6
__xor_mask ^= 1 << 9
__xor_mask ^= 1 << 11
__xor_mask ^= 1 << 13
__xor_mask ^= 1 << 16
__xor_mask ^= 1 << 19
__xor_mask ^= 1 << 21
__xor_mask ^= 1 << 24
__or_mask = 1 << 26

def generateL2CMcode(PRN):
  """
  The function generates PRN sequence for a particular SV.
  In the sequence '0' is represented as '1', 1 as -1

  INPUT: SV number from 0 (SV1) to 31 (SV32)
  OUTPUT:
    - PRN seequence array of 10230,
    - end state of shift register for testing purpuses
  """
  #--- Sanity sheck for PRN number ------------------------------------------
  if PRN < 0 or PRN > 31:
    raise ValueError('PRN number(', PRN, ') is not in range [0..31]')

  #--- Initial states for shift register for each PRN[1..32], ---------------
  # see IS-GPS-200H, Table 3-IIa
  initL2CM = [\
      0742417664,  # PRN 1
      0756014035,
      0002747144,
      0066265724,
      0601403471,
      0703232733,
      0124510070,
      0617316361,
      0047541621,
      0733031046,
      0713512145,
      0024437606,
      0021264003,
      0230655351,
      0001314400,
      0222021506,
      0540264026,
      0205521705,
      0064022144,
      0120161274,
      0044023533,
      0724744327,
      0045743577,
      0741201660,
      0700274134,
      0010247261,
      0713433445,
      0737324162,
      0311627434,
      0710452007,
      0722462133,
      0050172213  # PRN 32
  ]

  #--- Init L2CM PRN and shift reg ------------------------------------------
  L2CM_PRN = np.zeros(10230, np.int8)

  #--- Load Shift register --------------------------------------------------
  shift_cm = initL2CM[PRN]

  #--- Generate L2CM PRN chips ----------------------------------------------
  for i in range(10230):
    # remember last value for verification
    shift_reg_out = shift_cm

    out = shift_cm & 1
    if out:
      L2CM_PRN[i] = -1  # -1 to represent '1'
      shift_cm = ((shift_cm ^ __xor_mask) >> 1) | __or_mask
    else:
      L2CM_PRN[i] = 1  # 1 to represent '0'
      shift_cm >>= 1

  return (L2CM_PRN, shift_reg_out)

L2CMCodes = np.empty((32, 10230), dtype=np.int8)
for PRN in range(32):
  L2CMCodes[PRN][:] = generateL2CMcode(PRN)[0]


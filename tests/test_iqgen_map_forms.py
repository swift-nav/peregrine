# -*- coding: utf-8 -*-
# Copyright (C) 2016 Swift Navigation Inc.
#
# Contact: Pasi Miettinen <pasi.miettinen@exafore.com>
# This source is subject to the license found in the file 'LICENSE' which must
# be be distributed together with this source. All other rights reserved.
#
# THIS CODE AND INFORMATION IS PROVIDED "AS IS" WITHOUT WARRANTY OF ANY KIND,
# EITHER EXPRESSED OR IMPLIED, INCLUDING BUT NOT LIMITED TO THE IMPLIED
# WARRANTIES OF MERCHANTABILITY AND/OR FITNESS FOR A PARTICULAR PURPOSE.

'''
Unit tests for IQgen factories
'''

from peregrine.iqgen.bits.amplitude_factory import factoryObject as AFO
from peregrine.iqgen.bits.doppler_factory import factoryObject as DFO
from peregrine.iqgen.bits.message_factory import factoryObject as MFO
from peregrine.iqgen.bits.satellite_factory import factoryObject as SFO
from peregrine.iqgen.bits.tcxo_factory import factoryObject as TFO

from peregrine.iqgen.bits.amplitude_base import AmplitudeBase
from peregrine.iqgen.bits.amplitude_poly import AmplitudePoly
from peregrine.iqgen.bits.amplitude_sine import AmplitudeSine

from peregrine.iqgen.bits.doppler_poly import Doppler as DopplerPoly
from peregrine.iqgen.bits.doppler_sine import Doppler as DopplerSine

from peregrine.iqgen.bits.message_block import Message as BlockMessage
from peregrine.iqgen.bits.message_cnav import Message as CNAVMessage
from peregrine.iqgen.bits.message_const import Message as ConstMessage
from peregrine.iqgen.bits.message_lnav import Message as LNAVMessage
from peregrine.iqgen.bits.message_zeroone import Message as ZeroOneMessage

from peregrine.iqgen.bits.satellite_gps import GPSSatellite

from peregrine.iqgen.bits.tcxo_poly import TCXOPoly as PolyTcxo
from peregrine.iqgen.bits.tcxo_sine import TCXOSine as SineTcxo

from peregrine.iqgen.iqgen_main import prepareArgsParser

import numpy as np
import os


class Dummy(object):
  pass


def to_map_and_back(factory, instance):
  mapped = factory.fromMapForm(factory.toMapForm(instance))

  assert isinstance(mapped, instance.__class__)
  for key, value in mapped.__dict__.iteritems():
    if isinstance(mapped.__dict__[key], np.ndarray):
      assert (mapped.__dict__[key] == mapped.__dict__[key]).all()
    else:
      assert mapped.__dict__[key] == mapped.__dict__[key]


def value_error(factory):
  try:
    factory.toMapForm(Dummy())
    assert False
  except ValueError:
    pass

  try:
    factory.fromMapForm({'type': 'Dummy'})
    assert False
  except ValueError:
    pass


def test_factories():
  '''
  Test factories
  '''
  to_map_and_back(AFO, AmplitudePoly(AmplitudeBase.UNITS_AMPLITUDE, (1, )))
  to_map_and_back(AFO, AmplitudeSine(AmplitudeBase.UNITS_AMPLITUDE, 1., 2., 1.))
  value_error(AFO)

  to_map_and_back(DFO, DopplerPoly(1000., 77., (1., 1.)))
  to_map_and_back(DFO, DopplerSine(1000., 55., 4., 3., 5.))
  value_error(DFO)

  to_map_and_back(MFO, BlockMessage(np.random.rand(1023)))
  to_map_and_back(MFO, CNAVMessage(1))
  to_map_and_back(MFO, ConstMessage(1))
  to_map_and_back(MFO, LNAVMessage(1))
  to_map_and_back(MFO, ZeroOneMessage())
  value_error(MFO)

  to_map_and_back(SFO, GPSSatellite(1))
  value_error(SFO)

  to_map_and_back(TFO, PolyTcxo((1., 1.)))
  to_map_and_back(TFO, SineTcxo(0., 1e6, 0.004))
  value_error(TFO)


def test_config():
  '''
  Test config
  '''
  try:
    CONFIG_FILE = 'test.conf'
    parser = prepareArgsParser()
    saved = parser.parse_args('--save-config {0}'.format(CONFIG_FILE).split())
    loaded = parser.parse_args('--load-config {0}'.format(CONFIG_FILE).split())

  finally:
    if os.path.isfile(CONFIG_FILE):
      os.remove(CONFIG_FILE)

  assert saved.__dict__['tcxo'].__dict__ == loaded.__dict__['tcxo'].__dict__

  for key, value in saved.__dict__.iteritems():
    if key == 'no_run' or key == 'tcxo':
      continue
    assert saved.__dict__[key] == loaded.__dict__[key]

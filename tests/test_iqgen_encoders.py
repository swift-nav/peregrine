# Copyright (C) 2016 Swift Navigation Inc.
#
# Contact: Valeri Atamaniouk <valeri@swiftnav.com>
# This source is subject to the license found in the file 'LICENSE' which must
# be be distributed together with this source. All other rights reserved.
#
# THIS CODE AND INFORMATION IS PROVIDED "AS IS" WITHOUT WARRANTY OF ANY KIND,
# EITHER EXPRESSED OR IMPLIED, INCLUDING BUT NOT LIMITED TO THE IMPLIED
# WARRANTIES OF MERCHANTABILITY AND/OR FITNESS FOR A PARTICULAR PURPOSE.

'''
Unit tests for IQgen band encoders
'''

# General
from peregrine.iqgen.bits.encoder_base import Encoder as EncoderBase
from peregrine.iqgen.bits.encoder_1bit import BandBitEncoder
from peregrine.iqgen.bits.encoder_1bit import TwoBandsBitEncoder
from peregrine.iqgen.bits.encoder_1bit import FourBandsBitEncoder
from peregrine.iqgen.bits.encoder_2bits import BandTwoBitsEncoder
from peregrine.iqgen.bits.encoder_2bits import TwoBandsTwoBitsEncoder
from peregrine.iqgen.bits.encoder_2bits import FourBandsTwoBitsEncoder

# GPS only
from peregrine.iqgen.bits.encoder_gps import GPSL1BitEncoder
from peregrine.iqgen.bits.encoder_gps import GPSL2BitEncoder
from peregrine.iqgen.bits.encoder_gps import GPSL1L2BitEncoder
from peregrine.iqgen.bits.encoder_gps import GPSL1TwoBitsEncoder
from peregrine.iqgen.bits.encoder_gps import GPSL2TwoBitsEncoder
from peregrine.iqgen.bits.encoder_gps import GPSL1L2TwoBitsEncoder

# Utilities
import numpy
from peregrine.iqgen.if_iface import NormalRateConfig


def test_EncoderBase_init():
  '''
  Test EncoderBase construction 
  '''
  encoder = EncoderBase(bufferSize=10, attDb=5.)
  assert encoder.getAttenuationLevel() == 5.
  assert len(encoder.bits) == 10
  assert encoder.n_bits == 0


def test_EncoderBase_addSamples():
  '''
  Test EncoderBase.encodeValues() 
  '''
  encoder = EncoderBase(bufferSize=10, attDb=5.)
  samples = numpy.zeros(10, dtype=numpy.float)
  try:
    encoder.addSamples(samples)
    assert False
  except NotImplementedError:
    pass


def test_EncoderBase_encodeValues0():
  '''
  Test EncoderBase.encodeValues() with empty data
  '''
  encoder = EncoderBase(bufferSize=10, attDb=5.)
  assert len(encoder.encodeValues()) == 0
  assert encoder.n_bits == 0


def test_EncoderBase_encodeValues1():
  '''
  Test EncoderBase.encodeValues() with some data
  '''
  encoder = EncoderBase(bufferSize=10, attDb=5.)
  encoder.bits.fill(1)
  encoder.n_bits = 8
  encoded = encoder.encodeValues()
  assert len(encoded) == 1
  assert encoder.n_bits == 0
  assert (encoder.bits == 0).all()
  assert encoded[0] == 255


def test_EncoderBase_encodeValues2():
  '''
  Test EncoderBase.encodeValues() with some data
  '''
  encoder = EncoderBase(bufferSize=10, attDb=5.)
  encoder.bits.fill(1)
  encoder.n_bits = 10
  encoded = encoder.encodeValues()
  assert len(encoded) == 1
  assert encoder.n_bits == 2
  assert (encoder.bits[:2] == 1).all()
  assert (encoder.bits[2:] == 0).all()
  assert encoded[0] == 255


def test_EncoderBase_flush0():
  '''
  Test EncoderBase.encodeValues() with some data
  '''
  encoder = EncoderBase(bufferSize=10, attDb=5.)
  encoder.bits[:2].fill(1)
  encoder.n_bits = 2
  encoded = encoder.flush()
  assert len(encoded) == 1
  assert encoder.n_bits == 0
  assert (encoder.bits == 0).all()
  assert encoded[0] == 192


def test_EncoderBase_flush1():
  '''
  Test EncoderBase.encodeValues() with some data
  '''
  encoder = EncoderBase(bufferSize=10, attDb=5.)
  encoder.bits.fill(1)
  encoder.n_bits = 10
  encoded = encoder.flush()
  assert len(encoded) == 2
  assert encoder.n_bits == 0
  assert (encoder.bits == 0).all()
  assert encoded[0] == 255
  assert encoded[1] == 192


def test_EncoderBase_ensureExtraCapacity0():
  '''
  Test EncoderBase noop extension
  '''
  encoder = EncoderBase(bufferSize=10, attDb=5.)
  encoder.ensureExtraCapacity(10)
  assert len(encoder.bits) == 10
  assert encoder.n_bits == 0


def test_EncoderBase_ensureExtraCapacity1():
  '''
  Test EncoderBase capacity extension
  '''
  encoder = EncoderBase(bufferSize=10, attDb=5.)
  encoder.n_bits = 5
  encoder.bits[:5].fill(1)
  encoder.ensureExtraCapacity(10)
  assert len(encoder.bits) == 15
  assert encoder.n_bits == 5
  assert (encoder.bits[:5] == 1).all()
  assert (encoder.bits[5:] == 0).all()


def test_BandBitEncoder_init():
  '''
  Test single bit encoder constructor
  '''
  encoder = BandBitEncoder(0)
  assert encoder.bandIndex == 0
  encoder = BandBitEncoder(1)
  assert encoder.bandIndex == 1


def test_BandBitEncoder_convertBand():
  '''
  Test single bit encoder band conversion
  '''
  samples = numpy.ndarray(10, dtype=numpy.float)
  samples[1::2].fill(-1.)
  samples[0::2].fill(1.)
  converted = BandBitEncoder.convertBand(samples)
  assert len(converted) == len(samples)
  assert converted.dtype == numpy.bool
  assert (converted[1::2] == 1).all()
  assert (converted[0::2] == 0).all()


def test_BandBitEncoder_addSamples0():
  '''
  Test single bit encoder samples adding and conversion
  '''
  encoder = BandBitEncoder(0)
  samples = numpy.ndarray((1, EncoderBase.BLOCK_SIZE + 6), dtype=numpy.float)
  samples[0][1::2].fill(-1.)
  samples[0][0::2].fill(1.)
  converted = encoder.addSamples(samples)
  assert len(converted) == len(samples[0]) / 8
  assert converted.dtype == numpy.uint8
  assert (converted == 0x55).all()
  converted = encoder.flush()
  assert len(converted) == 1
  assert converted.dtype == numpy.uint8
  assert converted[0] == 0x54


def test_BandBitEncoder_addSamples1():
  '''
  Test single bit encoder samples adding and conversion
  '''
  encoder = BandBitEncoder(0)
  samples = numpy.ndarray((1, 2), dtype=numpy.float)
  samples[0][1::2].fill(-1.)
  samples[0][0::2].fill(1.)
  converted = encoder.addSamples(samples)
  assert len(converted) == 0
  assert converted.dtype == numpy.uint8
  assert encoder.n_bits == 2


def test_TwoBandsBitEncoder_init():
  '''
  Test single bit two band encoder constructor
  '''
  encoder = TwoBandsBitEncoder(0, 1)
  assert encoder.l1Index == 0
  assert encoder.l2Index == 1
  encoder = TwoBandsBitEncoder(1, 0)
  assert encoder.l1Index == 1
  assert encoder.l2Index == 0


def test_TwoBandsBitEncoder_addSamples0():
  '''
  Test single bit encoder samples adding and conversion
  '''
  encoder = TwoBandsBitEncoder(0, 1)
  samples = numpy.ndarray((2, EncoderBase.BLOCK_SIZE + 2), dtype=numpy.float)
  samples[0].fill(-1.)
  samples[1].fill(1.)
  converted = encoder.addSamples(samples)
  assert len(converted) == len(samples[0]) / 4
  assert converted.dtype == numpy.uint8
  assert (converted == 0xAA).all()
  converted = encoder.flush()
  assert len(converted) == 1
  assert converted.dtype == numpy.uint8
  assert converted[0] == 0xA0


def test_TwoBandsBitEncoder_addSamples1():
  '''
  Test single bit encoder samples adding and conversion
  '''
  encoder = TwoBandsBitEncoder(0, 1)
  samples = numpy.ndarray((2, 2), dtype=numpy.float)
  samples[0].fill(-1.)
  samples[1].fill(1.)
  converted = encoder.addSamples(samples)
  assert len(converted) == 0
  assert converted.dtype == numpy.uint8
  assert encoder.n_bits == 4


def test_FourBandsBitEncoder_init():
  '''
  Test single bit four band encoder constructor
  '''
  encoder = FourBandsBitEncoder(0, 1, 2, 3)
  assert encoder.bandIndexes[0] == 0
  assert encoder.bandIndexes[1] == 1
  assert encoder.bandIndexes[2] == 2
  assert encoder.bandIndexes[3] == 3
  encoder = FourBandsBitEncoder(3, 2, 1, 0)
  assert encoder.bandIndexes[0] == 3
  assert encoder.bandIndexes[1] == 2
  assert encoder.bandIndexes[2] == 1
  assert encoder.bandIndexes[3] == 0


def test_FourBandsBitEncoder_addSamples0():
  '''
  Test single bit encoder samples adding and conversion
  '''
  encoder = FourBandsBitEncoder(0, 1, 0, 1)
  samples = numpy.ndarray((2, EncoderBase.BLOCK_SIZE + 1), dtype=numpy.float)
  samples[0].fill(-1.)
  samples[1].fill(1.)
  converted = encoder.addSamples(samples)
  assert len(converted) == len(samples[0]) / 2
  assert converted.dtype == numpy.uint8
  assert (converted == 0xAA).all()
  converted = encoder.flush()
  assert len(converted) == 1
  assert converted.dtype == numpy.uint8
  assert converted[0] == 0xA0


def test_FourBandsBitEncoder_addSamples1():
  '''
  Test single bit encoder samples adding and conversion
  '''
  encoder = FourBandsBitEncoder(0, 1, 0, 1)
  samples = numpy.ndarray((2, 1), dtype=numpy.float)
  samples[0].fill(-1.)
  samples[1].fill(1.)
  converted = encoder.addSamples(samples)
  assert len(converted) == 0
  assert converted.dtype == numpy.uint8
  assert encoder.n_bits == 4


def test_BandTwoBitsEncoder_init():
  '''
  Test dual bit encoder constructor
  '''
  encoder = BandTwoBitsEncoder(0)
  assert encoder.bandIndex == 0
  encoder = BandTwoBitsEncoder(1)
  assert encoder.bandIndex == 1


def test_BandTwoBitsEncoder_convertBand0():
  '''
  Test dual bit encoder band conversion
  '''
  samples = numpy.ndarray(10, dtype=numpy.float)
  samples[1::2].fill(-1.)
  samples[0::2].fill(1.)
  signs, amps = BandTwoBitsEncoder.convertBand(samples)
  assert signs.dtype == numpy.bool
  assert amps.dtype == numpy.bool
  assert len(signs) == len(samples)
  assert len(amps) == len(samples)
  assert (amps == 0).all()
  assert (signs[1::2] == 0).all()
  assert (signs[0::2] == 1).all()


def test_BandTwoBitsEncoder_convertBand1():
  '''
  Test dual bit encoder band conversion
  '''
  samples = numpy.ndarray(10, dtype=numpy.float)
  samples[1::2].fill(-1.)
  samples[0::2].fill(1.)
  samples[5] = -3.
  samples[4] = 3.
  signs, amps = BandTwoBitsEncoder.convertBand(samples)
  assert signs.dtype == numpy.bool
  assert amps.dtype == numpy.bool
  assert len(signs) == len(samples)
  assert len(amps) == len(samples)
  assert (amps[4:6] == 1).all()
  assert (amps[:4] == 0).all()
  assert (amps[6:] == 0).all()
  assert (signs[1::2] == 0).all()
  assert (signs[0::2] == 1).all()


def test_BandTwoBitsEncoder_addSamples0():
  '''
  Test dual bit encoder samples adding and conversion
  '''
  encoder = BandTwoBitsEncoder(0)
  samples = numpy.ndarray((1, EncoderBase.BLOCK_SIZE + 3), dtype=numpy.float)
  samples[0][1::2].fill(-1.)
  samples[0][0::2].fill(1.)
  converted = encoder.addSamples(samples)
  assert len(converted) == len(samples[0]) / 4
  assert converted.dtype == numpy.uint8
  assert (converted == 0x88).all()
  converted = encoder.flush()
  assert len(converted) == 1
  assert converted.dtype == numpy.uint8
  assert converted[0] == 0x88


def test_BandTwoBitsEncoder_addSamples1():
  '''
  Test dual bit encoder samples adding and conversion
  '''
  encoder = BandTwoBitsEncoder(0)
  samples = numpy.ndarray((1, 2), dtype=numpy.float)
  samples[0][1::2].fill(-1.)
  samples[0][0::2].fill(1.)
  converted = encoder.addSamples(samples)
  assert len(converted) == 0
  assert converted.dtype == numpy.uint8
  assert encoder.n_bits == 4


def test_TwoBandsTwoBitsEncoder_init():
  '''
  Test dual bit two band encoder constructor
  '''
  encoder = TwoBandsTwoBitsEncoder(0, 1)
  assert encoder.l1Index == 0
  assert encoder.l2Index == 1
  encoder = TwoBandsTwoBitsEncoder(1, 0)
  assert encoder.l1Index == 1
  assert encoder.l2Index == 0


def test_TwoBandsTwoBitsEncoder_addSamples0():
  '''
  Test dual bit encoder samples adding and conversion
  '''
  encoder = TwoBandsTwoBitsEncoder(0, 1)
  samples = numpy.ndarray((2, EncoderBase.BLOCK_SIZE + 1), dtype=numpy.float)
  samples[0].fill(-1.)
  samples[1].fill(1.)
  converted = encoder.addSamples(samples)
  assert len(converted) == len(samples[0]) / 2
  assert converted.dtype == numpy.uint8
  assert (converted == 0x22).all()
  converted = encoder.flush()
  assert len(converted) == 1
  assert converted.dtype == numpy.uint8
  assert converted[0] == 0x20


def test_TwoBandsTwoBitsEncoder_addSamples1():
  '''
  Test dual bit encoder samples adding and conversion
  '''
  encoder = TwoBandsTwoBitsEncoder(0, 1)
  samples = numpy.ndarray((2, 2), dtype=numpy.float)
  samples[0].fill(-1.)
  samples[1].fill(1.)
  converted = encoder.addSamples(samples)
  assert len(converted) == 0
  assert converted.dtype == numpy.uint8
  assert encoder.n_bits == 8


def test_FourBandsTwoBitsEncoder_init():
  '''
  Test dual bit four band encoder constructor
  '''
  encoder = FourBandsTwoBitsEncoder(0, 1, 2, 3)
  assert encoder.bandIndexes[0] == 0
  assert encoder.bandIndexes[1] == 1
  assert encoder.bandIndexes[2] == 2
  assert encoder.bandIndexes[3] == 3
  encoder = FourBandsTwoBitsEncoder(3, 2, 1, 0)
  assert encoder.bandIndexes[0] == 3
  assert encoder.bandIndexes[1] == 2
  assert encoder.bandIndexes[2] == 1
  assert encoder.bandIndexes[3] == 0


def test_FourBandsTwoBitsEncoder_addSamples0():
  '''
  Test dual bit encoder samples adding and conversion
  '''
  encoder = FourBandsTwoBitsEncoder(0, 1, 0, 1)
  samples = numpy.ndarray((2, EncoderBase.BLOCK_SIZE + 1), dtype=numpy.float)
  samples[0].fill(-1.)
  samples[1].fill(1.)
  converted = encoder.addSamples(samples)
  assert len(converted) == len(samples[0])
  assert converted.dtype == numpy.uint8
  assert (converted == 0x22).all()
  converted = encoder.flush()
  assert len(converted) == 0
  assert converted.dtype == numpy.uint8


def test_FourBandsTwoBitsEncoder_addSamples1():
  '''
  Test single bit encoder samples adding and conversion
  '''
  encoder = FourBandsTwoBitsEncoder(0, 1, 0, 1)
  samples = numpy.ndarray((2, 1), dtype=numpy.float)
  samples[0].fill(-1.)
  samples[1].fill(1.)
  converted = encoder.addSamples(samples)
  assert len(converted) == 0
  assert converted.dtype == numpy.uint8
  assert encoder.n_bits == 8


def test_GPSL1BitEncoder_init():
  '''
  Test construction of GPS L1 single bit encoder
  '''
  encoder = GPSL1BitEncoder(NormalRateConfig)
  assert isinstance(encoder, EncoderBase)
  assert isinstance(encoder, BandBitEncoder)
  assert encoder.bandIndex == NormalRateConfig.GPS.L1.INDEX


def test_GPSL2BitEncoder_init():
  '''
  Test construction of GPS L2 single bit encoder
  '''
  encoder = GPSL2BitEncoder(NormalRateConfig)
  assert isinstance(encoder, EncoderBase)
  assert isinstance(encoder, BandBitEncoder)
  assert encoder.bandIndex == NormalRateConfig.GPS.L2.INDEX


def test_GPSL1L2BitEncoder_init():
  '''
  Test construction of GPS L1/L2 single bit dual band encoder
  '''
  encoder = GPSL1L2BitEncoder(NormalRateConfig)
  assert isinstance(encoder, EncoderBase)
  assert isinstance(encoder, TwoBandsBitEncoder)
  assert encoder.l1Index == NormalRateConfig.GPS.L1.INDEX
  assert encoder.l2Index == NormalRateConfig.GPS.L2.INDEX


def test_GPSL1TwoBitsEncoder_init():
  '''
  Test construction of GPS L1 two bit encoder
  '''
  encoder = GPSL1TwoBitsEncoder(NormalRateConfig)
  assert isinstance(encoder, EncoderBase)
  assert isinstance(encoder, BandTwoBitsEncoder)
  assert encoder.bandIndex == NormalRateConfig.GPS.L1.INDEX


def test_GPSL2TwoBitsEncoder_init():
  '''
  Test construction of GPS L2 two bit encoder
  '''
  encoder = GPSL2TwoBitsEncoder(NormalRateConfig)
  assert isinstance(encoder, EncoderBase)
  assert isinstance(encoder, BandTwoBitsEncoder)
  assert encoder.bandIndex == NormalRateConfig.GPS.L2.INDEX


def test_GPSL1L2TwoBitsEncoder_init():
  '''
  Test construction of GPS L1/L2 two bit dual band encoder
  '''
  encoder = GPSL1L2TwoBitsEncoder(NormalRateConfig)
  assert isinstance(encoder, EncoderBase)
  assert isinstance(encoder, TwoBandsTwoBitsEncoder)
  assert encoder.l1Index == NormalRateConfig.GPS.L1.INDEX
  assert encoder.l2Index == NormalRateConfig.GPS.L2.INDEX

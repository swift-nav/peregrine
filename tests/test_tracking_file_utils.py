# Copyright (C) 2016 Swift Navigation Inc.
#
# Contact: Valeri Atamaniouk <valeri@swiftnav.com>
# This source is subject to the license found in the file 'LICENSE' which must
# be be distributed together with this source. All other rights reserved.
#
# THIS CODE AND INFORMATION IS PROVIDED "AS IS" WITHOUT WARRANTY OF ANY KIND,
# EITHER EXPRESSED OR IMPLIED, INCLUDING BUT NOT LIMITED TO THE IMPLIED
# WARRANTIES OF MERCHANTABILITY AND/OR FITNESS FOR A PARTICULAR PURPOSE.

from peregrine.tracking_file_utils import collectTrackingOutputFileEntries
from peregrine.tracking_file_utils import createTrackingDumpOutputFileName
from peregrine.tracking_file_utils import createTrackingOutputFileNames
from peregrine.tracking_file_utils import PickleLoadObject
from peregrine.tracking_file_utils import removeTrackingOutputFiles
from peregrine.tracking_file_utils import TrackingResults
from peregrine.tracking_file_utils import TrackResultFile
from peregrine.tracking import TrackResults


def __testSetup():
  '''
  Test utility
  '''
  removeTrackingOutputFiles("test_output.bin")
  tr1 = TrackResults(500, 0, 'l1ca')
  for i in range(500):
    tr1.ms_tracked[i] = i * 2
    tr1.absolute_sample[i] = i * 2
  tr1.status = 'A'
  tr1.dump('test_output.bin', 500)
  tr2 = TrackResults(500, 1, 'l1ca')
  for i in range(500):
    tr2.ms_tracked[i] = i * 2 + 1
    tr2.absolute_sample[i] = i * 2 + 1
  tr2.status = 'B'
  tr2.dump('test_output.bin', 500)


def test_OutputFileName0s():
  '''
  Name mangling test
  '''
  aName, rName = createTrackingOutputFileNames("output.bin", 1, "l1ca")
  assert aName == "output.PRN-1.l1ca.bin"
  assert rName == "output.PRN-1.l1ca.bin.track_results"


def test_OutputFileNames1():
  '''
  Name mangling test
  '''
  aName, rName = createTrackingOutputFileNames("/mnt/usr/output.bin", 2, "l2c")
  assert aName == "/mnt/usr/output.PRN-2.l2c.bin"
  assert rName == "/mnt/usr/output.PRN-2.l2c.bin.track_results"


def test_DumpOutputFileName():
  '''
  Name mangling test
  '''
  fname = createTrackingDumpOutputFileName('output.bin')
  assert fname == 'output.combined_track.bin'


def test_CollectTrackingOutputFileEntries0():
  '''
  Test for locating tracking results (empty)
  '''
  removeTrackingOutputFiles("test_output.bin")
  entries = collectTrackingOutputFileEntries("test_output.bin")
  assert isinstance(entries, list)
  assert len(entries) == 0


def test_CollectTrackingOutputFileEntries1():
  '''
  Test for locating tracking results (non-empty)
  '''
  removeTrackingOutputFiles("test_output.bin")
  aName1, rName1 = createTrackingOutputFileNames("test_output.bin", 1, "l1ca")
  aName2, rName2 = createTrackingOutputFileNames("test_output.bin", 2, "l1ca")
  aName3, rName3 = createTrackingOutputFileNames("test_output.bin", 1, "l2c")
  for f in [aName1, aName2, aName3, rName1, rName2, rName3]:
    with file(f, "wb"):
      pass

  entries = collectTrackingOutputFileEntries("test_output.bin")
  assert isinstance(entries, list)
  assert len(entries) == 3
  assert entries[0]['filename'] == rName1
  assert entries[1]['filename'] == rName2
  assert entries[2]['filename'] == rName3
  removeTrackingOutputFiles("test_output.bin")


def test_RemoveTrackingOutputFiles():
  '''
  File system cleanup test
  '''
  aName1, rName1 = createTrackingOutputFileNames("test_output.bin", 1, "l1ca")
  aName2, rName2 = createTrackingOutputFileNames("test_output.bin", 2, "l1ca")
  aName3, rName3 = createTrackingOutputFileNames("test_output.bin", 1, "l2c")
  for f in [aName1, aName2, aName3, rName1, rName2, rName3]:
    with file(f, "wb"):
      pass
  removeTrackingOutputFiles("test_output.bin")
  entries = collectTrackingOutputFileEntries("test_output.bin")
  assert isinstance(entries, list)
  assert len(entries) == 0


def test_PickleLoadObject():
  '''
  Test for PickleLoadObject object
  '''
  tr = TrackResults(500, 1, 'l1ca')
  for i in range(500):
    tr.ms_tracked[i] = i
    tr.absolute_sample[i] = i
  tr.dump('test_output.bin', 500)
  for i in range(500):
    tr.ms_tracked[i] = i + 500
    tr.absolute_sample[i] = i + 500
  tr.dump('test_output.bin', 500)
  loadObj = PickleLoadObject('test_output.PRN-2.l1ca.bin.track_results')
  it = iter(loadObj)
  o0 = it.next()
  o1 = it.next()
  try:
    it.next()
    assert False
  except StopIteration:
    pass
  try:
    it.next()
    assert False
  except StopIteration:
    pass
  assert isinstance(o0, TrackResults)
  for i in range(500):
    assert o0.ms_tracked[i] == i
    assert o0.absolute_sample[i] == i
  assert isinstance(o1, TrackResults)
  for i in range(500):
    assert o1.ms_tracked[i] == i + 500
    assert o1.absolute_sample[i] == i + 500


def test_TrackResultsFile():
  '''
  Test for TrackResults object
  '''
  tr = TrackResults(500, 1, 'l1ca')
  for i in range(500):
    tr.ms_tracked[i] = i
    tr.absolute_sample[i] = i
  tr.status = 'A'
  tr.dump('test_output.bin', 500)
  for i in range(500):
    tr.ms_tracked[i] = i + 500
    tr.absolute_sample[i] = i + 500
  tr.status = 'B'
  tr.dump('test_output.bin', 500)
  obj = TrackResultFile(
      PickleLoadObject('test_output.PRN-2.l1ca.bin.track_results'))
  it = iter(obj)
  for i in range(500):
    o, idx = it.next()
    assert o.status == 'A'
    assert idx == i
    assert o.ms_tracked[i] == i
    assert o.absolute_sample[i] == i
  for i in range(500):
    o, idx = it.next()
    assert o.status == 'B'
    assert idx == i
    assert o.ms_tracked[i] == i + 500
    assert o.absolute_sample[i] == i + 500

  try:
    it.next()
    assert False
  except StopIteration:
    pass

  try:
    it.next()
    assert False
  except StopIteration:
    pass


def test_TrackResultsObj0():
  removeTrackingOutputFiles("test_output.bin")
  tr = TrackingResults('test_output.bin')
  assert tr.channelCount() == 0
  assert isinstance(tr.getEntries(), list)
  assert len(tr.getEntries()) == 0
  co = tr.combinedResult()
  assert isinstance(co, TrackingResults.MultiChannel)
  try:
    iter(co).next()
    assert False
  except StopIteration:
    pass


def test_TrackResultsObj1():
  '''
  Test for combined channel data iterations.
  '''
  __testSetup()

  tr = TrackingResults('test_output.bin')
  assert tr.channelCount() == 2
  assert isinstance(tr.getEntries(), list)
  assert len(tr.getEntries()) == 2
  co = tr.combinedResult()
  assert isinstance(co, TrackingResults.MultiChannel)

  it = iter(co)
  for i in range(500):
    tr1, idx1 = it.next()
    tr2, idx2 = it.next()
    assert tr1.status == 'A'
    assert tr2.status == 'B'
    assert idx1 == idx2 == i
    assert tr1.ms_tracked[i] == i * 2
    assert tr2.ms_tracked[i] == i * 2 + 1

  try:
    it.next()
    assert False
  except StopIteration:
    pass
  removeTrackingOutputFiles("test_output.bin")


def test_TrackResultsObj_single1():
  '''
  Test for individual channel data iterations.
  '''
  __testSetup()

  tr = TrackingResults('test_output.bin')
  assert tr.channelCount() == 2
  assert isinstance(tr.getEntries(), list)
  assert len(tr.getEntries()) == 2
  c0 = tr.channelResult(0)
  c1 = tr.channelResult(1)
  assert isinstance(c0, TrackingResults.SingleChannel)
  assert isinstance(c1, TrackingResults.SingleChannel)

  it1 = iter(c0)
  it2 = iter(c1)
  for i in range(500):
    tr1, idx1 = it1.next()
    tr2, idx2 = it2.next()
    assert tr1.status == 'A'
    assert tr2.status == 'B'
    assert idx1 == idx2 == i
    assert tr1.ms_tracked[i] == i * 2
    assert tr2.ms_tracked[i] == i * 2 + 1
  try:
    it1.next()
    assert False
  except StopIteration:
    pass
  try:
    it2.next()
    assert False
  except StopIteration:
    pass

  removeTrackingOutputFiles("test_output.bin")


def test_TrackResultsObj_dump():
  '''
  Sanity test for combined data output in a textual form.
  '''
  __testSetup()
  tr = TrackingResults('test_output.bin')
  tr.dump()

  removeTrackingOutputFiles("test_output.bin")

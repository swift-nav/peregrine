# Copyright (C) 2016 Swift Navigation Inc.
# Contact: Valeri Atamaniouk <valeri@swiftnav.com>
#
# This source is subject to the license found in the file 'LICENSE' which must
# be be distributed together with this source. All other rights reserved.
#
# THIS CODE AND INFORMATION IS PROVIDED "AS IS" WITHOUT WARRANTY OF ANY KIND,
# EITHER EXPRESSED OR IMPLIED, INCLUDING BUT NOT LIMITED TO THE IMPLIED
# WARRANTIES OF MERCHANTABILITY AND/OR FITNESS FOR A PARTICULAR PURPOSE.

import os
import re
import logging
import cPickle
import copy
import sys

logger = logging.getLogger(__name__)


def createTrackingOutputFileNames(outputFileName, prn, signalName):
  '''
  Constructs output file names for tracker by mangling output file name

  Parameters
  ----------
  outputFile : string
    File name template for the output data.
  prn : int
    Satellite vehicle number
  signalName : string
    Signal name

  Returns
  -------
  analysysFileName : string, resultsFileName : string
    File names for analysis and tracking output content  
  '''
  output_filename, output_file_extension = os.path.splitext(outputFileName)

  # mangle the analysis file name with the tracked signal name
  analysysFileName = (output_filename +
                      (".PRN-%d.%s" % (prn, signalName)) +
                      output_file_extension)

  # mangle the results file name with the tracked signal name
  resultsFileName = (output_filename +
                     (".PRN-%d.%s" % (prn, signalName)) +
                     output_file_extension + '.track_results')

  return analysysFileName, resultsFileName


def createTrackingDumpOutputFileName(outputFileName):
  output_filename, output_file_extension = os.path.splitext(outputFileName)
  return (output_filename + '.combined_track' + output_file_extension)


def collectTrackingOutputFileEntries(outputFileName):
  '''
  Collects tracking file information by listing file names that are constructed
  from the output file name template.

  Parameters
  ----------
  outputFileName : string
    Output file name template

  Returns
  -------
  list
    List of dictionaries with the following keys: 'prn', 'band' and 'filename'. 
  '''

  # First, split output file name into directory and file components
  dirname, filename = os.path.split(outputFileName)
  listdirname = dirname if dirname else '.'
  # Split file name component into base name part and extension
  basename, extension = os.path.splitext(filename)
  # Compile regular expression
  pattern = (re.escape(basename) + '\.PRN-(.*)\.(.*)' +
             re.escape(extension) + '\.track_results')
  expr = re.compile(pattern)
  tracking_channels = []
  for fname in os.listdir(listdirname):
    match = expr.match(fname)
    if match:
      filepath = os.path.join(dirname, fname)
      fname2 = basename + '.PRN-' + \
          match.group(1) + '.' + match.group(2) + extension
      filepath2 = os.path.join(dirname, fname2)
      if os.path.isfile(filepath):
        tracking_channel = {'prn': int(match.group(1)),
                            'band': match.group(2),
                            'filename': filepath,
                            'filename2': filepath2}
        tracking_channels.append(tracking_channel)

  tracking_channels.sort()
  return tracking_channels


def removeTrackingOutputFiles(outputFileName):
  '''
  Removes tracking result files from the file system.

  Parameters
  ----------
  outputFileName : string
    Output file name template
  '''
  fileEntries = collectTrackingOutputFileEntries(outputFileName)
  filenames = [fileEntry['filename'] for fileEntry in fileEntries]
  filenames += [fileEntry['filename2'] for fileEntry in fileEntries]
  filenames.append(createTrackingDumpOutputFileName(outputFileName))
  filenames.sort()
  for filename in filenames:
    if os.path.isfile(filename):
      logger.debug("Removing old tracking file: %s" % filename)
      os.remove(filename)


class PickleLoadObject(object):
  '''
  Container type for pickle object loading
  '''

  class It(object):
    '''
    Iterator type for pickle object loading
    '''

    def __init__(self, fileName):
      self.file = open(fileName, "rb", 16384)

    def next(self):
      if self.file is not None:
        try:
          data = cPickle.load(self.file)
          # print data.signal, data.prn, len(data.P)
          return data
        except EOFError:
          self.file.close()
          self.file = None
      raise StopIteration

  def __init__(self, fileName):
    self.file = None
    self.fileName = fileName

  def __iter__(self):
    return PickleLoadObject.It(self.fileName)


class TrackResultObj(object):
  '''
  Container for TrackResult object
  '''
  class It(object):
    '''
    Iterator for TrackResult object
    '''

    def __init__(self, trackResult):
      self.trackResult = trackResult
      self.nextIdx = 0
      self.len = trackResult.absolute_sample.shape[0]

    def next(self):
      if self.nextIdx >= self.len:
        raise StopIteration
      else:
        idx = self.nextIdx
        self.nextIdx = idx + 1
        return self.trackResult, idx

  def __init__(self, fileObj):
    self.fileObj = fileObj

  def __iter__(self):
    return TrackResultObj.It(self.fileObj)


class TrackResultFile(object):
  '''
  Iteratable object for TrackResult objects
  '''

  class It(object):

    def __init__(self, fileObj):
      self.blockIt = iter(fileObj)
      self.trackIt = None

    def next(self):
      while self.blockIt is not None:
        while self.trackIt is None:
          try:
            nextTrackRes = self.blockIt.next()
          except StopIteration, e:
            self.blockIt = None
            raise e
          self.trackIt = iter(TrackResultObj(nextTrackRes))

        try:
          return self.trackIt.next()
        except StopIteration:
          self.trackIt = None
      raise StopIteration

  def __init__(self, fileObj):
    self.fileObj = fileObj

  def __iter__(self):
    return TrackResultFile.It(self.fileObj)


class TrackingResults(object):
  '''
  Persistent tracking result operations objects
  '''

  class SingleChannel(object):
    '''
    Single tracking channel data support
    '''

    class It(object):

      def __init__(self, blockObj):
        self.nextResultIt = iter(blockObj)
        self.resultObj = None

      def next(self):
        return self.nextResultIt.next()

    def __init__(self, outputEntry):
      self.outputEntry = copy.deepcopy(outputEntry)
      fileObj = PickleLoadObject(outputEntry['filename'])
      self.blockObj = TrackResultFile(fileObj)

    def __iter__(self):
      return TrackingResults.SingleChannel.It(self.blockObj)

  class MultiChannel(object):
    '''
    Combined tracking channel data support
    '''

    class It(object):

      def __init__(self, outputEntries):
        self.outputEntries = copy.deepcopy(outputEntries)
        for fileEntry in self.outputEntries:
          fileObj = PickleLoadObject(fileEntry['filename'])
          blockObj = TrackResultFile(fileObj)
          fileEntry['nextResultIt'] = iter(blockObj)
          fileEntry['resultObj'] = None

      def next(self):
        minIndex = long(1e12)
        minResultObj = None
        minEntry = None
        for fileEntry in self.outputEntries:
          nextResultIt = fileEntry['nextResultIt']
          resultObj = fileEntry['resultObj']
          if nextResultIt is not None and resultObj is None:
            try:
              resultObj = nextResultIt.next()
              fileEntry['resultObj'] = resultObj
            except StopIteration:
              resultObj = None
              fileEntry['nextResultIt'] = None
              continue

          if resultObj is not None:
            trackResult, idx = resultObj
            sampleIndex = trackResult.absolute_sample[idx]

            if sampleIndex < minIndex:
              minIndex = sampleIndex
              minResultObj = resultObj
              minEntry = fileEntry

        if minResultObj is not None:
          minEntry['resultObj'] = None
          return minResultObj
        else:
          raise StopIteration

    def __init__(self, entries):
      self.entries = entries

    def __iter__(self):
      return TrackingResults.MultiChannel.It(self.entries)

  def __init__(self, fileName):
    self.entries = collectTrackingOutputFileEntries(fileName)

  def channelCount(self):
    '''
    Queries tracking channel count

    Returns
    -------
    int
      Number of tracking channels in the file system
    '''
    return len(self.entries)

  def getEntries(self):
    '''
    Queries tracking channel data

    Returns
    -------
    list
      List of tracking channel entries
    '''
    return self.entries

  def combinedResult(self):
    '''
    Queries object that combines data from all tracking channel according to
    sample index number.

    Returns
    -------
    object
      Iteratable object for combined data output
    '''
    return TrackingResults.MultiChannel(self.entries)

  def channelResult(self, entryIdx):
    '''
    Queries object that provides data from one tracking channel according to
    channel index number.

    Parameters
    ----------
    entryIdx : int
      Channel index number

    Returns
    -------
    object
      Iteratable object for a single channel data output
    '''
    return TrackingResults.SingleChannel(self.entries[entryIdx])

  def dump(self, dest=sys.stdout):
    '''
    Produces textual output of the combined tracking data into destination
    file.

    Parameters
    ----------
    dest : file, optional
      Destination file, default it sys.stdout
    '''
    print >> dest, '       N  SIGNAL  TRIDX   SAMPLE   MS_TRACK OLOCK PLOCK'
    print >> dest, '-------------------------------------------------------'
    for n, minResultObj in enumerate(self.combinedResult()):
      trackResult, idx = minResultObj
      print >> dest, '[%7d]' % n, \
          "%4s[%d]" % (trackResult.signal, trackResult.prn), \
          "[%3d]" % idx, \
          "%9d" % trackResult.absolute_sample[idx], \
          "%9.03f" % trackResult.ms_tracked[idx], \
          "%5.1f" % trackResult.lock_detect_outo[idx], \
          "%5.1f" % trackResult.lock_detect_outp[idx]
    print >> dest, '-------------------------------------------------------'

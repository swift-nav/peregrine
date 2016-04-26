# Copyright (C) 2012-2016 Swift Navigation Inc.
# Contact: Fergus Noble <fergus@swiftnav.com>
#
# This source is subject to the license found in the file 'LICENSE' which must
# be be distributed together with this source. All other rights reserved.
#
# THIS CODE AND INFORMATION IS PROVIDED "AS IS" WITHOUT WARRANTY OF ANY KIND,
# EITHER EXPRESSED OR IMPLIED, INCLUDING BUT NOT LIMITED TO THE IMPLIED
# WARRANTIES OF MERCHANTABILITY AND/OR FITNESS FOR A PARTICULAR PURPOSE.

import datetime
import numpy as np
import swiftnav.nav_msg
import swiftnav.pvt
import swiftnav.track
import swiftnav.signal
import logging
from math import isnan
from peregrine.gps_constants import L1CA
from peregrine.gps_constants import L2C

logger = logging.getLogger(__name__)


def extract_ephemerides(combinedResultObject):
  ephems = {}
  for n, entry in enumerate(combinedResultObject.entries):
    prn = entry['prn']
    band = entry['band']
    isL1CA = band == L1CA
    isL2C = band == L2C
    if isL1CA:
      nav_msg = swiftnav.nav_msg.NavMsg()
      tow_index = None
      for i, x in enumerate(combinedResultObject.channelResult(n)):
        tr, idx = x
        tow = nav_msg.update(tr.P[idx])
        if tow is not None:
          # print tr.prn, tow
          tow_index = (i, tow)
      if nav_msg.eph_valid:
        ephems[prn] = (nav_msg, tow_index)
    elif isL2C:
      logger.info("No ephemerides decoding for PRN=%d band=%s" %
                  (prn, band))
    else:
      logger.warn("SV channel PRN=%d band=%s is not supported" %
                  (prn, band))
      continue

  return ephems


def make_chan_meas(combinedResultObject, mss, ephems, samplingFreq):
  '''
  Parameters
  ----------
  combinedResultObject : object
    Object with tracking results.
  mss : list
    List of sample reference time in milliseconds in growing order.
  epems : list
    List of ephemerides object corresponding to tracking result channels.

  Returns
  -------
  list
    List of len(mss), where each element is a tuple of ms index and a list of
    measurement.
  '''
  result = [(ms, {}) for ms in mss]
  for n, entry in enumerate(combinedResultObject.getEntries()):
    band = entry['band']
    prn = entry['prn']
    if band != L1CA:
      continue
    ms_idx = 0
    ms = mss[ms_idx]
    for tr, idx in combinedResultObject.channelResult(n):
      ms_tracked = tr.ms_tracked[idx]
      if ms_tracked < ms:
        continue
      tow = tr.tow[idx]
      if not isnan(tow):
        # If ToW is known, make a measurement object.
        # The actual sample time is usually greater than the requested time.
        # i, tow_e = ephems[tr.prn][1]
        cm = swiftnav.track.ChannelMeasurement(
            swiftnav.signal.GNSSSignal(sat=prn - 1, code=0),
            tr.code_phase[idx],
            tr.code_freq[idx],
            0,
            tr.carr_freq[idx] - tr.IF,
            tow,
            ms_tracked,
            41,  # SNR
            100  # Lock
        )
        result[ms_idx][1][prn - 1] = cm
      ms_idx += 1
      if ms_idx > len(mss):
        break
      else:
        ms = mss[ms_idx]
  return result


def make_nav_meas(cmss, ephems):
  nms = []
  for ms, cms in cmss:
    navMsgs = []
    for key in cms.keys():
      if ephems.has_key(key):
        navMsgs.append(ephems[key][0])
    nms.append(swiftnav.track.calc_navigation_measurement(ms / 1000.0,
                                                          cms,
                                                          navMsgs))
  return nms


def make_meas(track_results, ms, ephems, sampling_freq=16.368e6, IF=4.092e6):
  nms = []
  TOTs = np.empty(len(track_results))
  prrs = np.empty(len(track_results))
  prs = np.empty(len(track_results))
  mean_TOT = 0
  for i in len(track_results):
    tow_i, tow_e = ephems[track_results[i].prn][1]
    tow = tow_e + (ms - tow_i)
    TOTs[i] = 1e-3 * tow
    TOTs[i] += tr.code_phase[ms] / 1.023e6
    TOTs[i] += (ms / 1000.0 - track_results[i].absolute_sample[ms] / sampling_freq) * \
        track_results[i].code_freq[ms] / 1.023e6
    mean_TOT += TOTs[i]
    prrs[i] = 299792458 * -(track_results[i].carr_freq[ms] - IF) / 1.57542e9
  mean_TOT = mean_TOT / len(track_channels)
  clock_err, clock_rate_err = (0, 0)
  # double az, el;
  ref_ecef = np.array([3428027.88064438,   603837.64228578,  5326788.33674493])
  for i in len(track_results):
    prs[i] = (mean_TOT - TOTs[i]) * 299792458 + 22980e3
    # calc_sat_pos(nav_meas[i]->sat_pos, nav_meas[i]->sat_vel, &clock_err, &clock_rate_err, ephemerides[i], TOTs[i]);
    # wgsecef2azel(nav_meas[i]->sat_pos, ref_ecef, &az, &el);
    # nav_meas[i]->pseudorange -= tropo_correction(el);
    prs[i] += clock_err * 299792458
    prrs[i] -= clock_rate_err * 299792458
    nms += [NavigationMeasurement(prs[i], prrs[i], ephems[track_results[i].prn][
                                  0].gps_week_num(), TOTs[i], (0, 0, 0), (0, 0, 0))]
  return nms


def make_solns(nms):
  return map(swiftnav.pvt.calc_PVT, nms)


def navigation(combinedResultObject,
               sampling_freq,
               ephems=None,
               mss=range(10000, 35000, 200)):

  if ephems is None:
    ephems = extract_ephemerides(combinedResultObject)
  if combinedResultObject.channelCount() < 4:
    raise Exception('Too few satellites to calculate nav solution')
  cmss = make_chan_meas(combinedResultObject, mss, ephems, sampling_freq)
  nms = make_nav_meas(cmss, ephems)
  ss = make_solns(nms)
  wn = ephems.values()[0][0].gps_week_num()
  ts = []
  for s in ss:
    t = datetime.datetime(1980, 1, 5) + \
        datetime.timedelta(weeks=wn) + \
        datetime.timedelta(seconds=s.tow)
    ts += [t]

  return zip(ss, ts)


def show_kml(kml):
  import uuid
  from IPython.display import display, HTML, Javascript

  html_string = """
  <div id="map3d-{uuid}" style="height: 400px; width: 600px;"></div>
  <script type="text/javascript">
  var ge;

  function init() {{
    google.earth.createInstance('map3d-{uuid}', initCB, failureCB);
  }}

  function initCB(instance) {{
    ge = instance;
    ge.getWindow().setVisibility(true);
    ge.getNavigationControl().setVisibility(ge.VISIBILITY_SHOW);
    $('#map3d-{uuid}').data('ge', ge);
    var kmlObject = ge.parseKml('{kmlstring}');
    $('#map3d-{uuid}').data('kmlobj', kmlObject);
    ge.getFeatures().appendChild(kmlObject);
    //ge.getView().setAbstractView(kmlObject.getAbstractView());
    ge.getView().setAbstractView(kmlObject.getFeatures().getFirstChild().getAbstractView());
    $('#map3d-{uuid}').resizable();
  }}

  function failureCB(errorCode) {{
  }}

  function googleLoaded(data, textStatus, jqxhr) {{
    google.load("earth", "1", {{"callback": init}});
  }}

  if (typeof google == "undefined") {{
    $.getScript("https://www.google.com/jsapi", googleLoaded);
  }} else {{
    googleLoaded();
  }}
  </script>
  """.format(uuid=str(uuid.uuid4()), kmlstring=kml.kml().replace('\n', ' '))
  display(HTML(html_string))


def nav_to_kml(nav_solns):
  import simplekml
  kml = simplekml.Kml()

  nav_results = [s.pos_llh for s, t in nav_solns]
  lats = np.array([lat * 180 / np.pi for (lat, lng, hgt) in nav_results])
  lngs = np.array([lng * 180 / np.pi for (lat, lng, hgt) in nav_results])
  hgts = np.array([hgt for (lat, lng, hgt) in nav_results])
  coords = zip(lngs, lats, hgts)

  ls = kml.newlinestring(name="Navigation Solutions",
                         description="Navigation Solutions",
                         altitudemode=simplekml.AltitudeMode.absolute,
                         coords=coords)
  ls.style.linestyle.color = simplekml.Color.red
  # TODO: taking the mean of the lats and lngs is not really correct.
  ls.lookat = simplekml.LookAt(gxaltitudemode=simplekml.GxAltitudeMode.relativetoseafloor,
                               latitude=np.mean(lats), longitude=np.mean(lngs),
                               range=300, heading=0, tilt=10)
  return kml


def nav_stats(nav_solns):
  xyzs = np.array([s.pos_ecef for s, t in nav_solns])
  means = np.mean(xyzs, axis=0)
  vars = np.var(xyzs, axis=0)
  return (means, vars, np.sqrt(np.sum(vars)))

#!/usr/bin/env python
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
import sys

def extract_ephemerides(track_results):
  track_results = [tr for tr in track_results if tr.status == 'T']

#  for tr in track_results:
#    if len(tr.P) < 36000:
#      raise Exception('Length of tracking too short to extract ephemeris')

  nav_msgs = [swiftnav.nav_msg.NavMsg() for tr in track_results]
  tow_indicies = [[] for tr in track_results]
  ephems = {}
  for n, tr in enumerate(track_results):
    for i, cpi in enumerate(np.real(tr.P)):
      tow = nav_msgs[n].update(cpi, tr.coherent_ms[i])
      if tow is not None:
        #print tr.prn, tow
        tow_indicies[n] = (i, tow)
    if nav_msgs[n].eph_valid:
      ephems[tr.prn] = (nav_msgs[n], tow_indicies[n])
  return ephems

def make_chan_meas(track_results, ms, ephems, sampling_freq=16.368e6):
  cms = []
  for tr in track_results:
    i, tow_e = ephems[tr.prn][1]
    tow = tr.tow[ms]
    cm = swiftnav.track.ChannelMeasurement(
      tr.prn,
      tr.code_phase[ms],
      tr.code_freq[ms],
      0,
      tr.carr_freq[ms] - tr.IF,
      tow,
      tr.absolute_sample[ms] / sampling_freq,
      100
    )
    cms += [cm]
  return (ms, cms)

def make_nav_meas(cmss, ephems):
  nms = []
  for ms, cms in cmss:
    navMsgs = [ephems[cm.prn][0] for cm in cms]
    nms += [swiftnav.track.calc_navigation_measurement(ms/1000.0, cms, navMsgs)]
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
    TOTs[i] += (ms/1000.0 - track_results[i].absolute_sample[ms]/sampling_freq) * \
               track_results[i].code_freq[ms] / 1.023e6
    mean_TOT += TOTs[i]
    prrs[i] = 299792458 * -(track_results[i].carr_freq[ms] - IF) / 1.57542e9;
  mean_TOT = mean_TOT/len(track_channels)
  clock_err, clock_rate_err = (0,0)
  #double az, el;
  ref_ecef = np.array([3428027.88064438,   603837.64228578,  5326788.33674493])
  for i in len(track_results):
    prs[i] = (mean_TOT - TOTs[i])*299792458 + 22980e3
    #calc_sat_pos(nav_meas[i]->sat_pos, nav_meas[i]->sat_vel, &clock_err, &clock_rate_err, ephemerides[i], TOTs[i]);
    #wgsecef2azel(nav_meas[i]->sat_pos, ref_ecef, &az, &el);
    #nav_meas[i]->pseudorange -= tropo_correction(el);
    prs[i] += clock_err*299792458
    prrs[i] -= clock_rate_err*299792458
    nms += [NavigationMeasurement(prs[i], prrs[i], ephems[track_results[i].prn][0].gps_week_num(), TOTs[i], (0,0,0), (0,0,0))]
  return nms

def make_solns(nms):
  return map(swiftnav.pvt.calc_PVT, nms)


def navigation(track_results, sampling_freq,
               ephems=None, mss=range(10000, 35000, 200)):

  if ephems is None:
    ephems = extract_ephemerides(track_results)
  track_results = [tr for tr in track_results if tr.status == 'T' and tr.prn in ephems]
  if len(track_results) < 4:
    raise Exception('Too few satellites to calculate nav solution')
  cmss = [make_chan_meas(track_results, ms, ephems, sampling_freq) for ms in mss]
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
  lats = np.array([lat*180/np.pi for (lat, lng, hgt) in nav_results])
  lngs = np.array([lng*180/np.pi for (lat, lng, hgt) in nav_results])
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

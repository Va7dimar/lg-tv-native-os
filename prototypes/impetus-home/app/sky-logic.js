// Pure logic for the overhead room (issue #23): the home position, the
// feeds' text, where the ISS, the Starlink trains and the planes are on the
// sky seen from home, and the ISS's next visible pass. No DOM, no luna.
// Host-tested with node. Chromium 79 on the TV: ES5 only.
// Orbits: SGP4 from satellite.js (app/sky/satellite.min.js, MIT), loaded
// before this file on the TV and by require() on the host.
(function (root) {
  "use strict";

  var S = root.satellite || (typeof require === "function" ? require("./sky/satellite.min.js") : null);
  var RAD = Math.PI / 180, DEG = 180 / Math.PI;
  var EARTH_KM = 6378.137;
  // The repo's stand-in: central Reykjavik. The real home lives only on the TV.
  var PLACEHOLDER = { lat: 64.1466, lon: -21.9426 };
  var COMPASS = ["N", "NE", "E", "SE", "S", "SW", "W", "NW"];
  var DAYS = ["SUNDAY", "MONDAY", "TUESDAY", "WEDNESDAY", "THURSDAY", "FRIDAY", "SATURDAY"];
  // Degrees up a pass counts from. Not the usual 10: from 64° N the ISS (its
  // track reaches 51.6° N) never climbs past about 10°.
  var VISIBLE_EL = 5;
  var DARK_SUN = -6;        // the sun at least this far down: dark enough to see it
  var NOTE_HOURS = 12;      // the control room's note looks this far ahead
  var TRAIN_GAP = 12;       // degrees between two of a launch still drawn as one train

  function pad2(n) { return (n < 10 ? "0" : "") + n; }
  function clock(ms) { var d = new Date(ms); return pad2(d.getHours()) + ":" + pad2(d.getMinutes()); }

  // ---------- the home position ----------

  // What the owner types on the phone: "64.1466, -21.9426" (as a map app
  // copies it), with or without the comma, or "64.1466 N 21.9426 W" with
  // degree signs. -> {lat, lon} to 5 decimals (about a metre), or null.
  function parsePlace(s) {
    if (typeof s !== "string") return null;
    var t = s.replace(/°/g, " ").replace(/\s+/g, " ").trim().toUpperCase();
    var m = /^(-?\d{1,2}(?:\.\d+)?) ?([NS])?[ ,;]+ ?(-?\d{1,3}(?:\.\d+)?) ?([EW])?$/.exec(t);
    if (!m) return null;
    var lat = Number(m[1]), lon = Number(m[3]);
    if ((m[2] && lat < 0) || (m[4] && lon < 0)) return null;
    if (m[2] === "S") lat = -lat;
    if (m[4] === "W") lon = -lon;
    if (!(Math.abs(lat) <= 90) || !(Math.abs(lon) <= 180)) return null;
    return { lat: round(lat, 5), lon: round(lon, 5) };
  }

  function round(x, d) { var f = Math.pow(10, d); return Math.round(x * f) / f; }
  // A plain decimal for the helper: no exponent, no "-0".
  function dec(x, d) {
    var s = x.toFixed(d);
    if (s.indexOf(".") >= 0) s = s.replace(/0+$/, "").replace(/\.$/, "");
    return s === "-0" ? "0" : s;
  }

  // The helper words that store a position.
  function placeWords(p) {
    if (!p || typeof p.lat !== "number" || typeof p.lon !== "number") return null;
    if (!(Math.abs(p.lat) <= 90) || !(Math.abs(p.lon) <= 180)) return null;
    return ["sky", "place", "set", "lat=" + dec(p.lat, 5), "lon=" + dec(p.lon, 5)];
  }

  // The helper's `sky place` answer (parsed key=value) -> {lat, lon} or null.
  function readPlace(kv) {
    if (!kv || kv.lat === undefined || kv.lon === undefined) return null;
    var lat = Number(kv.lat), lon = Number(kv.lon);
    if (!isFinite(lat) || !isFinite(lon) || Math.abs(lat) > 90 || Math.abs(lon) > 180) return null;
    return { lat: lat, lon: lon };
  }

  // The neighbourhood the planes feed is asked about: one decimal (~10 km).
  function placeAt(p) { return dec(round(p.lat, 1), 1) + "," + dec(round(p.lon, 1), 1); }

  function placeText(p) {
    return Math.abs(p.lat).toFixed(4) + "° " + (p.lat < 0 ? "S" : "N") + "  " +
      Math.abs(p.lon).toFixed(4) + "° " + (p.lon < 0 ? "W" : "E");
  }

  // ---------- the feeds ----------

  // "kind=fresh age=12\n<body>" -> {kind, age, body}.
  function parseFeed(text) {
    var t = String(text || ""), nl = t.indexOf("\n");
    var head = nl < 0 ? t : t.slice(0, nl);
    var m = /^kind=(fresh|last|none) age=(\d+)/.exec(head);
    if (!m) return { kind: "none", age: 0, body: "" };
    return { kind: m[1], age: Number(m[2]), body: nl < 0 ? "" : t.slice(nl + 1) };
  }

  // TLE text -> [{name, l1, l2, num, launch}]. launch is year * 1000 + the
  // launch number of that year, from the international designator.
  function parseTle(text) {
    var lines = String(text || "").replace(/\r/g, "").split("\n"), out = [];
    for (var i = 0; i < lines.length; i++) {
      var a = lines[i], b = lines[i + 1];
      if (!/^1 \d{5}/.test(a) || !b || !/^2 \d{5}/.test(b) || a.slice(2, 7) !== b.slice(2, 7)) continue;
      var name = i > 0 && !/^[12] \d{5}/.test(lines[i - 1]) ? lines[i - 1].trim() : a.slice(2, 7);
      var y = Number(a.slice(9, 11)), n = Number(a.slice(11, 14));
      out.push({ name: name, l1: a, l2: b, num: Number(a.slice(2, 7)),
        launch: isFinite(y) && isFinite(n) ? (y < 57 ? 2000 + y : 1900 + y) * 1000 + n : 0 });
      i++;
    }
    return out;
  }

  // Each object with its SGP4 record; one SGP4 cannot read is left out.
  function withOrbits(list) {
    var out = [];
    (list || []).forEach(function (o) {
      try {
        var rec = S.twoline2satrec(o.l1, o.l2);
        if (rec && !rec.error) { o.rec = rec; out.push(o); }
      } catch (e) { /* left out */ }
    });
    return out;
  }

  // ---------- the sun ----------

  // The sun's direction (unit vector, equatorial frame of date), from the
  // same short series as logic.js's sunAltitude.
  function sunDir(ms) {
    var n = ms / 86400000 + 2440587.5 - 2451545.0;
    var L = (280.460 + 0.9856474 * n) % 360;
    var g = (357.528 + 0.9856003 * n) * RAD;
    var lambda = (L + 1.915 * Math.sin(g) + 0.020 * Math.sin(2 * g)) * RAD;
    var eps = (23.439 - 0.0000004 * n) * RAD;
    return { x: Math.cos(lambda), y: Math.cos(eps) * Math.sin(lambda), z: Math.sin(eps) * Math.sin(lambda) };
  }

  // The sun's altitude in degrees seen from p.
  function sunAlt(ms, p) {
    var s = sunDir(ms), g = S.gstime(new Date(ms));
    var x = s.x * Math.cos(g) + s.y * Math.sin(g), y = -s.x * Math.sin(g) + s.y * Math.cos(g);
    var la = p.lat * RAD, lo = p.lon * RAD;
    return Math.asin(Math.cos(la) * Math.cos(lo) * x + Math.cos(la) * Math.sin(lo) * y + Math.sin(la) * s.z) * DEG;
  }

  // True when a point (km, equatorial frame) is out of the earth's shadow
  // (a cylinder behind the earth: good enough for when it is seen).
  function inSun(r, s) {
    var d = r.x * s.x + r.y * s.y + r.z * s.z;
    if (d > 0) return true;
    return r.x * r.x + r.y * r.y + r.z * r.z - d * d > EARTH_KM * EARTH_KM;
  }

  function observer(p) { return { latitude: p.lat * RAD, longitude: p.lon * RAD, height: 0 }; }

  // Where an object is at ms seen from p: {az, el (degrees), km (range),
  // sunlit, lat, lon, alt (km)}, or null when SGP4 cannot place it.
  function look(rec, ms, p) {
    var when = new Date(ms), pv;
    try { pv = S.propagate(rec, when); } catch (e) { return null; }
    var r = pv && pv.position;
    if (!r || !isFinite(r.x)) return null;
    var g = S.gstime(when);
    var la = S.ecfToLookAngles(observer(p), S.eciToEcf(r, g));
    var gd = S.eciToGeodetic(r, g);
    return { az: (la.azimuth * DEG + 360) % 360, el: la.elevation * DEG, km: la.rangeSat,
      sunlit: inSun(r, sunDir(ms)), lat: gd.latitude * DEG, lon: ((gd.longitude * DEG + 540) % 360) - 180,
      alt: gd.height };
  }

  // ---------- passes ----------

  // The passes over p from fromMs for `hours`, sampled every stepS seconds.
  // Each: {rise, set, peak, peakEl, riseAz, setAz, path: [{t, az, el}],
  // visible}. visible (null when none of it can be seen) is the part where
  // the object is 5° up or more, sunlit, and the sky at home is dark:
  // {start, end, peak, peakEl, startAz, endAz}.
  function passes(rec, p, fromMs, hours, stepS) {
    var step = (stepS || 30) * 1000, end = fromMs + hours * 3600000, out = [], cur = null;
    for (var t = fromMs; t <= end; t += step) {
      var at = look(rec, t, p);
      if (!at) { cur = null; continue; }
      if (at.el > 0) {
        if (!cur) {
          cur = { rise: t, set: t, peak: t, peakEl: at.el, riseAz: at.az, setAz: at.az, path: [], visible: null };
          out.push(cur);
        }
        cur.set = t; cur.setAz = at.az;
        cur.path.push({ t: t, az: at.az, el: at.el });
        if (at.el > cur.peakEl) { cur.peakEl = at.el; cur.peak = t; }
        if (at.el >= VISIBLE_EL && at.sunlit && sunAlt(t, p) <= DARK_SUN) {
          var v = cur.visible;
          if (!v) v = cur.visible = { start: t, end: t, peak: t, peakEl: at.el, startAz: at.az, endAz: at.az };
          v.end = t; v.endAz = at.az;
          if (at.el > v.peakEl) { v.peakEl = at.el; v.peak = t; }
        }
      } else {
        cur = null;
      }
    }
    // A pass cut off by the window's start or end is not whole: dropped.
    return out.filter(function (q) { return q.rise > fromMs && q.set < end; });
  }

  // The next pass that can be seen (or the one being seen now), searched
  // `hours` ahead of nowMs. null when none.
  function nextVisible(rec, p, nowMs, hours) {
    var list = passes(rec, p, nowMs - 20 * 60000, (hours || 48) + 1 / 3, 30);
    for (var i = 0; i < list.length; i++) if (list[i].visible && list[i].visible.end >= nowMs) return list[i];
    return null;
  }

  function compass(az) { return COMPASS[Math.round(((az % 360) + 360) % 360 / 45) % 8]; }

  // The control room's note: "ISS NOW" during a visible pass, "ISS 18:42"
  // when the next one starts within 12 hours, else null.
  function passNote(pass, nowMs) {
    var v = pass && pass.visible;
    if (!v) return null;
    if (nowMs >= v.start && nowMs <= v.end) return "ISS NOW";
    if (v.start > nowMs && v.start - nowMs <= NOTE_HOURS * 3600000) return "ISS " + clock(v.start);
    return null;
  }

  // The day a pass falls on, from nowMs: TODAY, TOMORROW or the weekday.
  function passDay(ms, nowMs) {
    var a = new Date(nowMs), b = new Date(ms);
    var d0 = new Date(a.getFullYear(), a.getMonth(), a.getDate()).getTime();
    var d1 = new Date(b.getFullYear(), b.getMonth(), b.getDate()).getTime();
    var days = Math.round((d1 - d0) / 86400000);
    return days <= 0 ? "TODAY" : days === 1 ? "TOMORROW" : DAYS[b.getDay()];
  }

  // "6 min · from SW · 54° high · to NE"
  function passLine(v) {
    var min = Math.max(1, Math.round((v.end - v.start) / 60000));
    return min + " min · from " + compass(v.startAz) + " · " + Math.round(v.peakEl) + "° high · to " + compass(v.endAz);
  }

  // ---------- the dome ----------

  // A sky chart seen from below: the zenith in the middle, the horizon the
  // rim, north up and east to the left (as the sky is when you look up).
  function domeXY(az, el, cx, cy, r) {
    var d = r * (90 - Math.max(-5, el)) / 90, a = az * RAD;
    return { x: cx - d * Math.sin(a), y: cy - d * Math.cos(a) };
  }

  // The angle between two places on the sky, in degrees.
  function apart(a, b) {
    var c = Math.sin(a.el * RAD) * Math.sin(b.el * RAD) +
      Math.cos(a.el * RAD) * Math.cos(b.el * RAD) * Math.cos((a.az - b.az) * RAD);
    return Math.acos(Math.max(-1, Math.min(1, c))) * DEG;
  }

  // Trains: the objects of one launch in catalogue order, joined while each
  // is within 12° of the next. -> [[{az, el, ...}, ...], ...], two or more each.
  function trains(points) {
    var byLaunch = {}, out = [];
    points.forEach(function (q) { (byLaunch[q.launch] = byLaunch[q.launch] || []).push(q); });
    Object.keys(byLaunch).forEach(function (k) {
      var list = byLaunch[k].sort(function (a, b) { return a.num - b.num; }), run = [];
      list.forEach(function (q) {
        if (run.length && apart(run[run.length - 1], q) > TRAIN_GAP) { if (run.length > 1) out.push(run); run = []; }
        run.push(q);
      });
      if (run.length > 1) out.push(run);
    });
    return out;
  }

  // ---------- planes ----------

  function kmBetween(a, b) {
    var dLat = (b.lat - a.lat) * RAD, dLon = (b.lon - a.lon) * RAD;
    var h = Math.sin(dLat / 2) * Math.sin(dLat / 2) +
      Math.cos(a.lat * RAD) * Math.cos(b.lat * RAD) * Math.sin(dLon / 2) * Math.sin(dLon / 2);
    return 2 * 6371 * Math.asin(Math.min(1, Math.sqrt(h)));
  }

  function bearing(a, b) {
    var y = Math.sin((b.lon - a.lon) * RAD) * Math.cos(b.lat * RAD);
    var x = Math.cos(a.lat * RAD) * Math.sin(b.lat * RAD) -
      Math.sin(a.lat * RAD) * Math.cos(b.lat * RAD) * Math.cos((b.lon - a.lon) * RAD);
    return (Math.atan2(y, x) * DEG + 360) % 360;
  }

  // adsb.lol's JSON (the body of `sky planes`) -> the planes in the air
  // within 100 km of p, nearest first: {id, call, lat, lon, altM, track, km,
  // dir (compass from home), az, el}. Ground traffic, planes without a
  // position or height and fixes older than a minute are left out.
  function parsePlanes(body, p) {
    var res;
    try { res = JSON.parse(body); } catch (e) { return null; }
    if (!res || !(res.ac instanceof Array)) return null;
    var out = [];
    res.ac.forEach(function (a) {
      if (!a || typeof a.lat !== "number" || typeof a.lon !== "number") return;
      if (typeof a.alt_baro !== "number" && typeof a.alt_geom !== "number") return;   // "ground"
      if (typeof a.seen_pos === "number" && a.seen_pos > 60) return;
      var ft = typeof a.alt_geom === "number" ? a.alt_geom : a.alt_baro;
      if (ft < 100) return;
      var q = { id: String(a.hex || ""), call: typeof a.flight === "string" ? a.flight.trim() : "",
        lat: a.lat, lon: a.lon, altM: Math.round(ft * 0.3048), track: typeof a.track === "number" ? a.track : null };
      q.km = kmBetween(p, q);
      if (q.km > 100) return;
      q.dir = compass(bearing(p, q));
      var la = S.ecfToLookAngles(observer(p),
        S.geodeticToEcf({ latitude: q.lat * RAD, longitude: q.lon * RAD, height: q.altM / 1000 }));
      q.az = (la.azimuth * DEG + 360) % 360;
      q.el = la.elevation * DEG;
      if (!q.call) q.call = q.id.toUpperCase();
      out.push(q);
    });
    return out.sort(function (a, b) { return a.km - b.km; });
  }

  function thousands(n) { return String(n).replace(/\B(?=(\d{3})+(?!\d))/g, ","); }

  // "11,300 m · 38 km NW"
  function planeLine(q) {
    return thousands(Math.round(q.altM / 100) * 100) + " m · " + Math.round(q.km) + " km " + q.dir;
  }

  // ---------- the source lines ----------

  function ageText(sec) {
    if (sec < 120) return "just now";
    if (sec < 7200) return Math.round(sec / 60) + " min old";
    if (sec < 172800) return Math.round(sec / 3600) + " h old";
    return Math.round(sec / 86400) + " days old";
  }

  // Elements stay good for days; past 3 days (or none at all) the feed is
  // called down, quietly.
  function orbitsLine(feed) {
    if (!feed || feed.kind === "none") return "Orbits: CelesTrak · feed down";
    if (feed.age > 3 * 86400) return "Orbits: CelesTrak · feed down · elements " + ageText(feed.age);
    return "Orbits: CelesTrak · " + ageText(feed.age);
  }

  // st: {goodAt (ms of the last good answer), down (true when the last ask failed)}
  function planesLine(st) {
    if (!st || !st.goodAt) return "Aircraft: adsb.lol (ODbL) · feed down";
    return "Aircraft: adsb.lol (ODbL) · " + (st.down ? "feed down since " : "updated ") + clock(st.goodAt);
  }

  var api = { PLACEHOLDER: PLACEHOLDER, parsePlace: parsePlace, placeWords: placeWords, readPlace: readPlace,
    placeAt: placeAt, placeText: placeText, parseFeed: parseFeed, parseTle: parseTle, withOrbits: withOrbits,
    sunDir: sunDir, sunAlt: sunAlt, inSun: inSun, look: look, passes: passes, nextVisible: nextVisible,
    compass: compass, passNote: passNote, passDay: passDay, passLine: passLine, domeXY: domeXY,
    apart: apart, trains: trains, parsePlanes: parsePlanes, planeLine: planeLine, kmBetween: kmBetween,
    ageText: ageText, orbitsLine: orbitsLine, planesLine: planesLine, clock: clock };
  if (typeof module !== "undefined" && module.exports) module.exports = api;
  else root.ImpetusSky = api;
})(this);

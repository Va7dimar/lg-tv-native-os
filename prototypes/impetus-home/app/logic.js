// Pure logic for Impetus Home: no DOM, no luna. Host-tested with node.
// Chromium 79 on the TV: no optional chaining, no nullish coalescing.
(function (root) {
  "use strict";

  var DAYS = ["sunnudagur", "mánudagur", "þriðjudagur", "miðvikudagur",
    "fimmtudagur", "föstudagur", "laugardagur"];
  var MONTHS = ["janúar", "febrúar", "mars", "apríl", "maí", "júní", "júlí",
    "ágúst", "september", "október", "nóvember", "desember"];
  var SAFE_ID = /^[A-Za-z0-9._-]+$/;
  var RAD = Math.PI / 180;
  var REYKJAVIK = { lat: 64.1466, lon: -21.9426 };

  function pad2(n) { return (n < 10 ? "0" : "") + n; }

  function formatClock(d) { return pad2(d.getHours()) + ":" + pad2(d.getMinutes()); }

  function formatDate(d) {
    return DAYS[d.getDay()] + " " + d.getDate() + ". " + MONTHS[d.getMonth()];
  }

  function formatDuration(minutes) {
    var m = Math.round(minutes);
    return Math.floor(m / 60) + " klst. " + (m % 60) + " mín.";
  }

  function isSafeId(id) { return typeof id === "string" && SAFE_ID.test(id); }

  // ---- Sun (low-precision solar position, good to about a minute) ----

  // Altitude of the sun's centre in degrees at time t (ms) seen from loc.
  function sunAltitude(t, loc) {
    loc = loc || REYKJAVIK;
    var n = t / 86400000 + 2440587.5 - 2451545.0;
    var L = (280.460 + 0.9856474 * n) % 360;
    var g = (357.528 + 0.9856003 * n) * RAD;
    var lambda = (L + 1.915 * Math.sin(g) + 0.020 * Math.sin(2 * g)) * RAD;
    var eps = (23.439 - 0.0000004 * n) * RAD;
    var ra = Math.atan2(Math.cos(eps) * Math.sin(lambda), Math.cos(lambda));
    var dec = Math.asin(Math.sin(eps) * Math.sin(lambda));
    var gmst = (18.697374558 + 24.06570982441908 * n) % 24;
    var ha = (gmst * 15 + loc.lon) * RAD - ra;
    var lat = loc.lat * RAD;
    return Math.asin(Math.sin(lat) * Math.sin(dec) + Math.cos(lat) * Math.cos(dec) * Math.cos(ha)) / RAD;
  }

  // The daylight span around solar noon of the local day of `day`: the
  // upward crossing of -0.833° (refraction) before the peak and the downward
  // one after it, searched up to 12 h out, so a midsummer sunset after
  // midnight still belongs to its day. rise/set are null when the sun never
  // crosses (polar day or night). Times in ms.
  function sunDay(day, loc) {
    var start = new Date(day.getFullYear(), day.getMonth(), day.getDate()).getTime();
    var peak = start, best = -91, m, t;
    for (m = 0; m < 1440; m += 2) {
      t = start + m * 60000;
      var a = sunAltitude(t, loc);
      if (a > best) { best = a; peak = t; }
    }
    function up(x) { return sunAltitude(x, loc) + 0.833 >= 0; }
    var rise = null, set = null;
    if (up(peak)) {
      for (m = 1; m <= 720 && rise === null; m++) if (!up(peak - m * 60000)) rise = peak - (m - 1) * 60000;
      for (m = 1; m <= 720 && set === null; m++) if (!up(peak + m * 60000)) set = peak + m * 60000;
      if (rise === null || set === null) rise = set = null;
    }
    return { rise: rise, set: set, peak: peak, peakAlt: best, start: start };
  }

  // ---- Apps ----

  function label(app, cfg) {
    if (cfg.labels && cfg.labels[app.id]) return cfg.labels[app.id];
    var t = String(app.title || app.id);
    var cut = t.indexOf(" - ");
    return cut > 0 ? t.slice(0, cut) : t;
  }

  // Visible, non-system, non-hidden apps; never ourselves or a hidden id.
  // Ids in cfg.order come first in that order, the rest by name.
  function pickApps(apps, cfg) {
    var hide = cfg.hide || [];
    var order = cfg.order || [];
    var out = (apps || []).filter(function (a) {
      if (!a || !isSafeId(a.id)) return false;
      if (a.id === cfg.selfId || hide.indexOf(a.id) >= 0) return false;
      if (a.visible !== true || a.systemApp === true) return false;
      if (a["class"] && a["class"].hidden === true) return false;
      return true;
    }).map(function (a) { return { id: a.id, label: label(a, cfg) }; });
    out.sort(function (x, y) {
      var ix = order.indexOf(x.id), iy = order.indexOf(y.id);
      if (ix < 0) ix = 1e6;
      if (iy < 0) iy = 1e6;
      if (ix !== iy) return ix - iy;
      return x.label.localeCompare(y.label);
    });
    return out;
  }

  // A launch payload is safe when the id is safe and the params JSON has no
  // single quote (it may travel inside a single-quoted shell argument).
  function launchPayload(id, params) {
    if (!isSafeId(id)) return null;
    var p = { id: id };
    if (params) p.params = params;
    var json = JSON.stringify(p);
    return json.indexOf("'") >= 0 ? null : p;
  }

  // ---- Connections ----

  function isLoopback(ip) {
    return /^127\./.test(ip) || ip === "::1" || ip === "0.0.0.0" || ip === "::";
  }

  // busybox `netstat -tnp` text -> [{ip, port, prog}] for ESTABLISHED, non-loopback.
  function parseNetstat(text) {
    var out = [];
    String(text || "").split("\n").forEach(function (line) {
      var f = line.trim().split(/\s+/);
      if (f.length < 6 || f[5] !== "ESTABLISHED") return;
      var foreign = f[4];
      var cut = foreign.lastIndexOf(":");
      if (cut < 0) return;
      var ip = foreign.slice(0, cut).replace(/^::ffff:/, "");
      if (isLoopback(ip)) return;
      var prog = f[6] && f[6] !== "-" ? f[6].replace(/^\d+\//, "") : "?";
      out.push({ ip: ip, port: foreign.slice(cut + 1), prog: prog });
    });
    return out;
  }

  // nslookup output (busybox or bind style) -> hostname or null.
  function parseNslookup(text, ip) {
    var m = /name = ([A-Za-z0-9.-]+?)\.?\s*$/m.exec(text || "");
    if (m) return m[1];
    var re = /^Address(?: \d+)?:\s+(\S+)\s+([A-Za-z0-9.-]+\.[A-Za-z]{2,})\s*$/mg;
    while ((m = re.exec(text || ""))) if (m[1] === ip) return m[2];
    return null;
  }

  // ---- Spatial focus ----

  // Gap between two ranges on one axis; 0 when they overlap.
  function gapOf(a0, a1, b0, b1) { return b0 > a1 ? b0 - a1 : a0 > b1 ? a0 - b1 : 0; }

  // rects: [{x,y,w,h}] in reading order. Returns the index of the nearest
  // rect in `dir` from rects[from], or `from` when there is none. A rect that
  // overlaps on the cross axis counts as aligned; ties go to reading order.
  function nearest(rects, from, dir) {
    var a = rects[from];
    var ax = a.x + a.w / 2, ay = a.y + a.h / 2;
    var best = from, bestScore = Infinity;
    for (var i = 0; i < rects.length; i++) {
      if (i === from) continue;
      var b = rects[i];
      var bx = b.x + b.w / 2, by = b.y + b.h / 2;
      var main, side;
      var sideY = gapOf(a.y, a.y + a.h, b.y, b.y + b.h), sideX = gapOf(a.x, a.x + a.w, b.x, b.x + b.w);
      if (dir === "right") { main = b.x - (a.x + a.w); side = sideY; if (main < -8) continue; }
      else if (dir === "left") { main = a.x - (b.x + b.w); side = sideY; if (main < -8) continue; }
      else if (dir === "down") { main = b.y - (a.y + a.h); side = sideX; if (main < -8) continue; }
      else { main = a.y - (b.y + b.h); side = sideX; if (main < -8) continue; }
      var score = Math.max(0, main) + 2 * side;
      if (score < bestScore) { bestScore = score; best = i; }
    }
    return best;
  }

  var api = { formatClock: formatClock, formatDate: formatDate, formatDuration: formatDuration,
    isSafeId: isSafeId, sunAltitude: sunAltitude, sunDay: sunDay, pickApps: pickApps,
    launchPayload: launchPayload, parseNetstat: parseNetstat, parseNslookup: parseNslookup,
    nearest: nearest };
  if (typeof module !== "undefined" && module.exports) module.exports = api;
  else root.ImpetusLogic = api;
})(this);

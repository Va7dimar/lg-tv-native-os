// Pure logic for Impetus Home: no DOM, no luna. Host-tested with node.
// Chromium 79 on the TV: no optional chaining, no nullish coalescing.
(function (root) {
  "use strict";

  var DAYS = ["Sunday", "Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday"];
  var MONTHS = ["January", "February", "March", "April", "May", "June", "July",
    "August", "September", "October", "November", "December"];
  var SAFE_ID = /^[A-Za-z0-9._-]+$/;
  // One word of a helper command: no space, quote, $, ;, |, & or backtick.
  var SAFE_WORD = /^[A-Za-z0-9._:,=+@\/-]+$/;
  var SAFE_DIR = /^\/[A-Za-z0-9._\/-]+$/;
  var PICTURE_KEYS = ["backlight", "contrast", "brightness", "color", "sharpness",
    "colorTemperature", "energySaving"];
  var PICTURE_VALUE = /^-?[A-Za-z0-9_]{1,24}$/;
  var RAD = Math.PI / 180;
  var REYKJAVIK = { lat: 64.1466, lon: -21.9426 };

  function pad2(n) { return (n < 10 ? "0" : "") + n; }

  function formatClock(d) { return pad2(d.getHours()) + ":" + pad2(d.getMinutes()); }

  function formatDate(d) {
    return DAYS[d.getDay()] + " " + d.getDate() + " " + MONTHS[d.getMonth()];
  }

  function formatDuration(minutes) {
    var m = Math.round(minutes);
    return Math.floor(m / 60) + " h " + (m % 60) + " min";
  }

  function isSafeId(id) { return typeof id === "string" && SAFE_ID.test(id); }
  function isSafeWord(w) { return typeof w === "string" && SAFE_WORD.test(w); }

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

  // The night SUN MODE works in, seen from `nowMs`: {start, end} in epoch
  // seconds. start is 0 when it is night already; end is the next sunrise.
  // null when the sun does not rise or set (no night to follow).
  function nightWindow(nowMs, loc) {
    var today = sunDay(new Date(nowMs), loc);
    if (today.rise === null) return null;
    function sec(ms) { return Math.round(ms / 1000); }
    if (nowMs < today.rise) return { start: 0, end: sec(today.rise) };
    var tomorrow = sunDay(new Date(today.start + 36 * 3600000), loc);
    if (tomorrow.rise === null) return null;
    return { start: nowMs < today.set ? sec(today.set) : 0, end: sec(tomorrow.rise) };
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

  // Launch params arrive as a JSON string (first launch) or an object
  // (relaunch). Anything else is no params.
  function parseLaunchParams(raw) {
    if (raw && typeof raw === "object") return raw;
    if (typeof raw !== "string" || !raw) return {};
    try { var o = JSON.parse(raw); return o && typeof o === "object" ? o : {}; } catch (e) { return {}; }
  }

  // ---- The helper (bin/impetus-ctl) ----

  // The one shell line the page may send: `sh <dir>/bin/impetus-ctl <words>`.
  // null when the dir or any word holds a character outside the safe set.
  function ctlCommand(dir, words) {
    if (typeof dir !== "string" || !SAFE_DIR.test(dir) || dir.indexOf("..") >= 0) return null;
    if (!words || !words.length) return null;
    for (var i = 0; i < words.length; i++) if (!isSafeWord(words[i])) return null;
    return "sh " + dir + "/bin/impetus-ctl " + words.join(" ");
  }

  // "a=1\nb=two" -> {a: "1", b: "two"}. Lines without = are skipped.
  function parseKv(text) {
    var out = {};
    String(text || "").split("\n").forEach(function (line) {
      var cut = line.indexOf("=");
      if (cut > 0) out[line.slice(0, cut).trim()] = line.slice(cut + 1).trim();
    });
    return out;
  }

  // "@a\n...\n@b\n..." -> {a: "...", b: "..."} (one helper call, several answers).
  function parseSections(text) {
    var out = {}, name = null;
    String(text || "").split("\n").forEach(function (line) {
      var m = /^@([a-z]+)$/.exec(line);
      if (m) { name = m[1]; out[name] = ""; }
      else if (name) out[name] += (out[name] ? "\n" : "") + line;
    });
    return out;
  }

  // probe output -> {exec, capture, picture, screenoff, volume, sleep, bind, count, log, temp}
  function parseCaps(text) {
    var kv = parseKv(text), caps = {};
    Object.keys(kv).forEach(function (k) { caps[k] = kv[k] === "1"; });
    return caps;
  }

  // ---- Scenes ----

  function picturePairs(obj) {
    if (!obj) return "";
    var out = [];
    for (var i = 0; i < PICTURE_KEYS.length; i++) {
      var k = PICTURE_KEYS[i];
      if (obj[k] === undefined) continue;
      var v = String(obj[k]);
      if (!PICTURE_VALUE.test(v)) return null;
      out.push(k + ":" + v);
    }
    return out.join(",");
  }

  function wholeIn(n, lo, hi) { return typeof n === "number" && n === Math.floor(n) && n >= lo && n <= hi; }

  // One scene from config.js -> the words for `impetus-ctl scene on`, with
  // the parts this TV cannot do (ctx.caps) left out. null when the scene is
  // malformed, or when none of its TV parts is left: a scene that would only
  // open an app is not drawn.
  // ctx: {caps, night: nightWindow() or null, fallback: app id for "last"}.
  function sceneWords(scene, ctx) {
    ctx = ctx || {};
    var caps = ctx.caps || {};
    if (!scene || !isSafeId(scene.id)) return null;
    var w = ["id=" + scene.id], parts = 0;
    if (scene.launch === "last") {
      w.push("launch=@last");
      if (isSafeId(ctx.fallback)) w.push("fallback=" + ctx.fallback);
    } else if (scene.launch !== undefined) {
      if (!isSafeId(scene.launch)) return null;
      w.push("launch=" + scene.launch);
    }
    if (caps.picture) {
      if (scene.pictureMode !== undefined) {
        if (!PICTURE_VALUE.test(String(scene.pictureMode))) return null;
        w.push("mode=" + scene.pictureMode); parts++;
      }
      var set = picturePairs(scene.picture), night = picturePairs(scene.sunMode);
      if (set === null || night === null) return null;
      if (set) { w.push("set=" + set); parts++; }
      if (night && ctx.night) {
        w.push("night=" + night, "nightstart=" + ctx.night.start, "end=" + ctx.night.end); parts++;
      }
    }
    if (caps.screenoff && scene.screenOffAfterSeconds !== undefined) {
      if (!wholeIn(scene.screenOffAfterSeconds, 0, 600)) return null;
      w.push("screenoff=" + scene.screenOffAfterSeconds); parts++;
    }
    if (caps.volume && scene.volumeMax !== undefined) {
      if (!wholeIn(scene.volumeMax, 0, 100)) return null;
      w.push("volmax=" + scene.volumeMax); parts++;
    }
    if (caps.sleep && scene.sleepMinutes !== undefined) {
      if (!wholeIn(scene.sleepMinutes, 1, 600)) return null;
      w.push("sleep=" + scene.sleepMinutes); parts++;
    }
    return parts ? w : null;
  }

  // The state line of a latched scene key, or null when the scene is off.
  // state: parseKv of `impetus-ctl state` (scene, sleep, end, screenoff in epoch s).
  function sceneLine(state, sceneId) {
    if (!state || !sceneId || state.scene !== sceneId) return null;
    function at(s) { return formatClock(new Date(Number(s) * 1000)); }
    if (Number(state.sleep) > 0) return "ON · SLEEPS " + at(state.sleep);
    if (Number(state.end) > 0) return "ON · UNTIL " + at(state.end);
    if (Number(state.screenoff) > 0) return "ON · SCREEN OFF " + at(state.screenoff);
    return "ON";
  }

  function shieldText(state) {
    if (!state || state.shield !== "on") return "OFF";
    return /^\d+$/.test(state.hits || "") ? state.hits : "ON";
  }

  // The state line on the engine room's SHIELD key.
  function shieldLine(state) {
    var t = shieldText(state);
    if (t === "OFF" || t === "ON") return t;
    return "ON · " + t + " BLOCKED";
  }

  // m:ss until `untilSec` (epoch s), never below 0:00.
  function countdown(untilSec, nowMs) {
    var left = Math.max(0, Math.round(untilSec - nowMs / 1000));
    return Math.floor(left / 60) + ":" + pad2(left % 60);
  }

  // The answer of `impetus-ctl still` (a binary string): one header line
  // "kind=live|last|none age=<s>", then the JPG. -> {kind, age, body}.
  function parseStill(bin) {
    bin = String(bin || "");
    var cut = bin.indexOf("\n");
    var head = parseKv((cut < 0 ? bin : bin.slice(0, cut)).split(" ").join("\n"));
    var kind = head.kind === "live" || head.kind === "last" ? head.kind : "none";
    var body = cut < 0 ? "" : bin.slice(cut + 1);
    // A JPG starts with FF D8; anything else is not a picture.
    if (body.charCodeAt(0) !== 0xFF || body.charCodeAt(1) !== 0xD8) return { kind: "none", age: 0, body: "" };
    return { kind: kind, age: Number(head.age) || 0, body: kind === "none" ? "" : body };
  }

  function stillAge(kind, ageSec) {
    if (kind === "live") return "LIVE";
    var min = Math.max(1, Math.round(Number(ageSec) / 60));
    return min < 90 ? min + " MIN AGO" : Math.round(min / 60) + " H AGO";
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

  var OWNERS = [
    ["LG", ["lge.com", "lg.com", "lgtvsdp.com", "lgappstv.com", "lgsmartad.com", "lgtvcommon.com",
      "lgeapi.com", "lgads.tv", "alphonso.tv", "lgthinq.com"]],
    ["Google", ["1e100.net", "google.com", "googleapis.com", "gstatic.com", "googlevideo.com",
      "youtube.com", "ytimg.com", "googleusercontent.com", "doubleclick.net", "ggpht.com"]],
    ["Apple", ["apple.com", "icloud.com", "aaplimg.com", "mzstatic.com", "apple-dns.net"]],
    ["Netflix", ["netflix.com", "nflxvideo.net", "nflxso.net", "nflximg.net", "nflxext.com"]],
    ["Amazon", ["amazon.com", "amazonvideo.com", "primevideo.com", "aiv-cdn.net", "media-amazon.com"]],
    ["Spotify", ["spotify.com", "scdn.co", "spotifycdn.com"]],
    ["Disney", ["disneyplus.com", "bamgrid.com", "dssott.com", "disney-plus.net"]],
    ["Twitch", ["twitch.tv", "ttvnw.net", "jtvnw.net"]],
    ["Meta", ["facebook.com", "fbcdn.net"]],
    ["Microsoft", ["microsoft.com", "azure.com", "azureedge.net", "msedge.net", "windows.net"]],
    ["Amazon cloud", ["amazonaws.com", "cloudfront.net"]],
    ["Akamai", ["akamaitechnologies.com", "akamaiedge.net", "akamai.net", "akamaized.net"]],
    ["Cloudflare", ["cloudflare.com", "cloudflare.net"]],
    ["Fastly", ["fastly.net", "fastlylb.net"]]
  ];

  function isPrivateIp(ip) {
    return /^10\./.test(ip) || /^192\.168\./.test(ip) || /^172\.(1[6-9]|2\d|3[01])\./.test(ip) ||
      /^169\.254\./.test(ip) || /^f[cde]/i.test(ip);
  }

  // Who owns the far end, from its hostname (suffix match), else from the address.
  function ownerOf(host, ip) {
    var h = String(host || "").toLowerCase();
    if (h) {
      for (var i = 0; i < OWNERS.length; i++) {
        var list = OWNERS[i][1];
        for (var j = 0; j < list.length; j++) {
          var s = list[j];
          if (h === s || h.slice(-(s.length + 1)) === "." + s) return OWNERS[i][0];
        }
      }
    }
    if (isPrivateIp(String(ip || ""))) return "Home network";
    return "Unknown";
  }

  // parseNetstat rows + {ip: host} -> {total, rows: [{prog, owner, count}]}, most first.
  function groupTalkers(conns, hosts) {
    var by = {}, rows = [];
    (conns || []).forEach(function (c) {
      var owner = ownerOf(hosts && hosts[c.ip], c.ip), k = c.prog + "|" + owner;
      if (!by[k]) { by[k] = { prog: c.prog, owner: owner, count: 0 }; rows.push(by[k]); }
      by[k].count++;
    });
    rows.sort(function (a, b) {
      return b.count - a.count || a.prog.localeCompare(b.prog) || a.owner.localeCompare(b.owner);
    });
    return { total: (conns || []).length, rows: rows };
  }

  // ---- System log ----

  // Device ids never reach the screen: hardware addresses, UUIDs, long hex
  // runs, the last half of a private address, and the value after an id-like key.
  function scrubLog(s) {
    return String(s)
      .replace(/((?:serial|nduid|device_?id|deviceuuid|mac_?addr(?:ess)?|macaddress|wifi_?mac|wired_?mac|bssid|ssid|imei|uuid)[A-Za-z_]*)(["']?\s*[:=]\s*["']?)[^\s"',}\]]+/gi, "$1$2[hidden]")
      .replace(/\b[0-9A-Fa-f]{2}(?:[:-][0-9A-Fa-f]{2}){5}\b/g, "[mac]")
      .replace(/\b[0-9A-Fa-f]{8}-[0-9A-Fa-f]{4}-[0-9A-Fa-f]{4}-[0-9A-Fa-f]{4}-[0-9A-Fa-f]{12}\b/g, "[id]")
      .replace(/\b[0-9A-Fa-f]{16,}\b/g, "[id]")
      .replace(/\b(10|192\.168|172\.(?:1[6-9]|2\d|3[01]))\.\d{1,3}\.\d{1,3}(?:\.\d{1,3})?\b/g, "$1.x.x");
  }

  // One log line -> {t, who, msg}. Knows the webOS PmLog shape and classic
  // syslog; anything else comes back whole in msg.
  function shortLog(line) {
    var m = /^\d{4}-\d\d-\d\dT(\d\d:\d\d:\d\d)\S*\s+(?:\[[^\]]*\]\s+)?\S+\s+(\S+)\s+(.*)$/.exec(line);
    if (!m) m = /^[A-Z][a-z]{2}\s+\d+\s+(\d\d:\d\d:\d\d)\s+\S+\s+([^:\[\s]+)(?:\[\d+\])?:\s*(.*)$/.exec(line);
    if (!m) return { t: "", who: "", msg: line };
    return { t: m[1], who: m[2], msg: m[3] };
  }

  // Raw log text -> the newest `max` lines, shortened and scrubbed. Lines
  // made by Impetus looking at the TV (its own polling) are left out.
  function filterLog(text, max) {
    var out = [];
    String(text || "").split("\n").forEach(function (line) {
      line = line.replace(/\s+/g, " ").trim();
      if (!line) return;
      if (/org\.va7dimar\.home|impetus|hbchannel|luna-send/i.test(line)) return;
      var s = shortLog(line);
      var msg = scrubLog(s.msg).replace(/^\[\]\s*/, "");
      if (msg.length > 120) msg = msg.slice(0, 119) + "…";
      out.push({ t: s.t, who: scrubLog(s.who), msg: msg });
    });
    return out.slice(-(max || 20));
  }

  // ---- Vitals ----

  function formatUptime(sec) {
    var s = Math.max(0, Math.floor(Number(sec) || 0));
    var d = Math.floor(s / 86400), h = Math.floor(s % 86400 / 3600), m = Math.floor(s % 3600 / 60);
    if (d > 0) return d + " d " + h + " h";
    if (h > 0) return h + " h " + m + " min";
    return m + " min";
  }

  function gb(kb) { return (kb / 1048576).toFixed(1); }

  // `impetus-ctl vitals` kv -> display values; a missing reading is null.
  function parseVitals(kv) {
    kv = kv || {};
    function num(k) { var n = Number(kv[k]); return kv[k] !== undefined && kv[k] !== "" && isFinite(n) ? n : null; }
    var temp = num("temp"), total = num("memtotal"), avail = num("memavail");
    var dUsed = num("diskused"), dTotal = num("disktotal"), up = num("uptime");
    var out = { tempC: null, uptime: null, mem: null, disk: null };
    if (temp !== null) out.tempC = Math.round(temp > 1000 ? temp / 1000 : temp);
    if (up !== null) out.uptime = formatUptime(up);
    if (total && avail !== null) {
      out.mem = { pct: Math.round((total - avail) / total * 100), text: gb(total - avail) + " / " + gb(total) + " GB" };
    }
    if (dTotal && dUsed !== null) {
      out.disk = { pct: Math.round(dUsed / dTotal * 100), text: gb(dUsed) + " / " + gb(dTotal) + " GB" };
    }
    return out;
  }

  // ---- Spatial focus ----

  // Gap between two ranges on one axis; 0 when they overlap.
  function gapOf(a0, a1, b0, b1) { return b0 > a1 ? b0 - a1 : a0 > b1 ? a0 - b1 : 0; }

  // rects: [{x,y,w,h}] in reading order. Returns the index of the nearest
  // rect in `dir` from rects[from], or `from` when there is none. A rect that
  // overlaps on the cross axis counts as aligned; ties go to reading order.
  function nearest(rects, from, dir) {
    var a = rects[from];
    var best = from, bestScore = Infinity;
    for (var i = 0; i < rects.length; i++) {
      if (i === from) continue;
      var b = rects[i];
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
    isSafeId: isSafeId, isSafeWord: isSafeWord, sunAltitude: sunAltitude, sunDay: sunDay,
    nightWindow: nightWindow, pickApps: pickApps, launchPayload: launchPayload,
    parseLaunchParams: parseLaunchParams, ctlCommand: ctlCommand, parseKv: parseKv,
    parseSections: parseSections, parseCaps: parseCaps, sceneWords: sceneWords,
    sceneLine: sceneLine, shieldText: shieldText, shieldLine: shieldLine, countdown: countdown,
    parseStill: parseStill, stillAge: stillAge,
    parseNetstat: parseNetstat, parseNslookup: parseNslookup, ownerOf: ownerOf,
    groupTalkers: groupTalkers, scrubLog: scrubLog, shortLog: shortLog, filterLog: filterLog,
    formatUptime: formatUptime, parseVitals: parseVitals, nearest: nearest };
  if (typeof module !== "undefined" && module.exports) module.exports = api;
  else root.ImpetusLogic = api;
})(this);

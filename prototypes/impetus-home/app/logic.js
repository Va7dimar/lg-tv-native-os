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
    // The music piece instead of a dark screen: the helper opens Impetus with
    // the piece after this long. When both are set, the piece wins.
    var piece = caps.exec && scene.pieceAfterSeconds !== undefined;
    if (piece) {
      if (!wholeIn(scene.pieceAfterSeconds, 0, 600)) return null;
      w.push("piece=" + scene.pieceAfterSeconds); parts++;
    }
    if (!piece && caps.screenoff && scene.screenOffAfterSeconds !== undefined) {
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
  // state: parseKv of `impetus-ctl state` (scene, sleep, end, screenoff, piece in epoch s).
  function sceneLine(state, sceneId) {
    if (!state || !sceneId || state.scene !== sceneId) return null;
    function at(s) { return formatClock(new Date(Number(s) * 1000)); }
    if (Number(state.sleep) > 0) return "ON · SLEEPS " + at(state.sleep);
    if (Number(state.end) > 0) return "ON · UNTIL " + at(state.end);
    if (Number(state.screenoff) > 0) return "ON · SCREEN OFF " + at(state.screenoff);
    if (Number(state.piece) > 0) return "ON · DRAWN FROM " + at(state.piece);
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

  // ---- The bedtime nudge (#24) ----

  var BED_WINDOW = 10800; // the keeper still asks this long after the hour

  // "22:30" -> the hour to send, in epoch seconds: tonight's while it is not
  // more than BED_WINDOW past (a TV turned on late is still asked), else
  // tomorrow's. Local time, so a clock change is followed. null when malformed.
  function nextBedtime(nowMs, at) {
    var m = /^([01]\d|2[0-3]):([0-5]\d)$/.exec(String(at || ""));
    if (!m) return null;
    var d = new Date(nowMs);
    var t = new Date(d.getFullYear(), d.getMonth(), d.getDate(), Number(m[1]), Number(m[2])).getTime();
    if (nowMs >= t + BED_WINDOW * 1000) {
      t = new Date(d.getFullYear(), d.getMonth(), d.getDate() + 1, Number(m[1]), Number(m[2])).getTime();
    }
    return Math.round(t / 1000);
  }

  // cfg.bedtime -> the words for `impetus-ctl bedtime set`, or null when the
  // nudge is off or malformed.
  function bedtimeWords(bed, nowMs) {
    if (!bed || !bed.at) return null;
    var at = nextBedtime(nowMs, bed.at);
    if (at === null) return null;
    var w = ["bedtime", "set", "at=" + at];
    var step = bed.stepBacklight === undefined ? 10 : bed.stepBacklight;
    var every = bed.everyMinutes === undefined ? 15 : bed.everyMinutes;
    var floor = bed.floorBacklight === undefined ? 10 : bed.floorBacklight;
    if (!wholeIn(step, 1, 50) || !wholeIn(every, 1, 120) || !wholeIn(floor, 0, 100)) return null;
    w.push("step=" + step, "every=" + every, "floor=" + floor);
    return w;
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

  // ---------- Iceland: the Met Office's 48-hour quake list ----------
  // The earthquakes page carries one inline array:
  //   quakeInfo = [{'t':new Date(2026,11-1,15,0,4,18),'lat':'63.910','lon':'-21.186',
  //                 'dep':'5.5','s':'0.4','q':'50.0','dR':'Selfoss', ...}, ...];
  // Times are UTC. Read with patterns, never evaluated. Returns null when the
  // text has no such array (the page changed or did not arrive), else the
  // quakes that pass every range check, newest first.
  var QUAKE_DATE = /'t'\s*:\s*new Date\((\d{4}),(\d{1,2})-1,(\d{1,2}),(\d{1,2}),(\d{1,2}),(\d{1,2})\)/;
  var QUAKE_MAX_AGE = 49 * 3600 * 1000;
  function quakeField(obj, key) {
    var m = new RegExp("'" + key + "'\\s*:\\s*'([^']*)'").exec(obj);
    return m ? m[1] : null;
  }
  function quakeNum(obj, key) {
    var s = quakeField(obj, key);
    if (s === null || !/^\s*-?\d+(\.\d+)?\s*$/.test(s)) return NaN;
    return parseFloat(s);
  }
  function parseQuakeInfo(text, nowMs) {
    if (typeof text !== "string") return null;
    var start = text.search(/quakeInfo\s*=\s*\[/);
    if (start < 0) return null;
    var end = text.indexOf("];", start);
    if (end < 0) return null;
    var body = text.slice(text.indexOf("[", start) + 1, end);
    var objs = body.match(/\{[^{}]*\}/g) || [];
    var out = [];
    for (var i = 0; i < objs.length; i++) {
      var o = objs[i], d = QUAKE_DATE.exec(o);
      if (!d) continue;
      var t = Date.UTC(+d[1], +d[2] - 1, +d[3], +d[4], +d[5], +d[6]);
      var q = { t: t, lat: quakeNum(o, "lat"), lon: quakeNum(o, "lon"), dep: quakeNum(o, "dep"),
        m: quakeNum(o, "s"), quality: quakeNum(o, "q"), place: (quakeField(o, "dR") || "").replace(/^\s+|\s+$/g, "") };
      if (!(q.lat >= 62.5 && q.lat <= 67.5 && q.lon >= -25.5 && q.lon <= -12.5)) continue;
      if (!(q.m >= -1 && q.m <= 8)) continue;
      if (typeof nowMs === "number" && (t > nowMs + 600000 || nowMs - t > QUAKE_MAX_AGE)) continue;
      if (isNaN(q.dep)) q.dep = null;
      if (isNaN(q.quality)) q.quality = null;
      out.push(q);
    }
    out.sort(function (a, b) { return b.t - a.t; });
    return out;
  }

  // The helper's answer to `iceland quakes`: a head line `kind=fresh|last|none
  // age=<s>`, then the page's quakeInfo lines. A list that does not parse is
  // "none": the room shows what it had, never an error.
  function parseQuakeReply(text, nowMs) {
    var s = typeof text === "string" ? text : "", nl = s.indexOf("\n");
    var head = nl < 0 ? s : s.slice(0, nl);
    var kind = /(?:^|\s)kind=(fresh|last|none)(?=\s|$)/.exec(head), age = /(?:^|\s)age=(\d+)(?=\s|$)/.exec(head);
    var body = nl >= 0 ? s.slice(nl + 1) : "";
    var quakes = kind && kind[1] !== "none" ? parseQuakeInfo(body, nowMs) : null;
    // Entries on the page but none we can read: the page changed, so the feed is down.
    if (quakes && !quakes.length && /\{\s*'t'\s*:/.test(body)) quakes = null;
    return { kind: quakes ? kind[1] : "none", age: quakes && age ? Number(age[1]) : 0, quakes: quakes };
  }

  // The room's feed state after one reply: { quakes, goodAt (ms of the list
  // shown), down }. A failed fetch keeps the list it had; the lights age on
  // their own clock.
  function isleStep(prev, reply, nowMs) {
    var kept = prev && prev.quakes ? prev : null;
    if (reply.kind === "fresh") return { quakes: reply.quakes, goodAt: nowMs - reply.age * 1000, down: false };
    if (reply.kind === "last") {
      var at = nowMs - reply.age * 1000;
      if (kept && kept.goodAt >= at) return { quakes: kept.quakes, goodAt: kept.goodAt, down: true };
      return { quakes: reply.quakes, goodAt: at, down: true };
    }
    return { quakes: kept ? kept.quakes : null, goodAt: kept ? kept.goodAt : null, down: true };
  }

  function isleSource(st) {
    var src = "Icelandic Met Office · ";
    if (!st) return src + "waiting for the list";
    if (!st.down) return src + "updated " + formatClock(new Date(st.goodAt));
    return src + "feed down" + (st.goodAt ? " since " + formatClock(new Date(st.goodAt)) : "");
  }

  // ---------- Iceland: aircraft (adsb.lol) ----------
  var TRAIL = 10, FLIGHT_STALE = 180000;   // points per trail; a plane not heard for 3 min is gone

  // The helper's "iceland flights" reply -> { kind, age, flights } where each
  // flight is { id, call, lat, lon, track, t (ms of its fix) }. Read with
  // JSON.parse, never evaluated. Ground traffic, planes without a position or
  // track, and fixes older than 60 s are left out.
  function parseFlightReply(text, nowMs) {
    var none = { kind: "none", age: 0, flights: null };
    var s = typeof text === "string" ? text : "", nl = s.indexOf("\n");
    if (nl < 0) return none;
    var head = s.slice(0, nl);
    var kind = /(?:^|\s)kind=(fresh|last)(?=\s|$)/.exec(head), age = /(?:^|\s)age=(\d+)(?=\s|$)/.exec(head);
    if (!kind) return none;
    var data;
    try { data = JSON.parse(s.slice(nl + 1)); } catch (e) { return none; }
    if (!data || !isArray(data.ac)) return none;
    var at = typeof data.now === "number" && isFinite(data.now) ? data.now : nowMs, out = [];
    for (var i = 0; i < data.ac.length; i++) {
      var a = data.ac[i];
      if (!a || typeof a.hex !== "string" || !/^~?[0-9a-f]{6}$/.test(a.hex)) continue;
      if (a.alt_baro === "ground" || !isNum(a.lat) || !isNum(a.lon) || !isNum(a.track)) continue;
      if (a.lat < 60 || a.lat > 70 || a.lon < -32 || a.lon > -6) continue;
      var seen = isNum(a.seen_pos) ? a.seen_pos : isNum(a.seen) ? a.seen : 999;
      if (seen < 0 || seen > 60) continue;
      var call = typeof a.flight === "string" ? a.flight.replace(/\s+$/, "") : "";
      out.push({ id: a.hex, call: /^[A-Z0-9]{1,8}$/.test(call) ? call : "", lat: a.lat, lon: a.lon,
        track: ((a.track % 360) + 360) % 360, t: Math.round(at - seen * 1000) });
    }
    return { kind: kind[1], age: age ? Number(age[1]) : 0, flights: out };
  }

  function isNum(v) { return typeof v === "number" && isFinite(v); }
  function isArray(v) { return Object.prototype.toString.call(v) === "[object Array]"; }

  // Trails: { id: [fix, ...] } oldest first, at most TRAIL fixes; a fix is
  // added only when newer than the trail's last; a trail whose last fix is
  // older than 3 min is dropped. Returns a new object.
  function flightTrails(prev, flights, nowMs) {
    var next = {}, id, k;
    for (id in prev) if (Object.prototype.hasOwnProperty.call(prev, id)) next[id] = prev[id].slice();
    for (k = 0; k < flights.length; k++) {
      var f = flights[k], tr = next[f.id] || (next[f.id] = []);
      if (!tr.length || f.t > tr[tr.length - 1].t) tr.push(f);
      if (tr.length > TRAIL) tr.splice(0, tr.length - TRAIL);
    }
    for (id in next) if (Object.prototype.hasOwnProperty.call(next, id) && nowMs - next[id][next[id].length - 1].t > FLIGHT_STALE) delete next[id];
    return next;
  }

  // The flights' state after one reply: { trails, goodAt, down }, as isleStep.
  function flightStep(prev, reply, nowMs) {
    var trails = prev ? prev.trails : {}, goodAt = prev ? prev.goodAt : null;
    if (reply.kind === "fresh") return { trails: flightTrails(trails, reply.flights, nowMs), goodAt: nowMs - reply.age * 1000, down: false };
    if (reply.kind === "last") {
      var at = nowMs - reply.age * 1000;
      return { trails: flightTrails(trails, reply.flights, nowMs), goodAt: goodAt !== null && goodAt >= at ? goodAt : at, down: true };
    }
    return { trails: flightTrails(trails, [], nowMs), goodAt: goodAt, down: true };
  }

  function flightSource(st) {
    var src = "Aircraft: adsb.lol (ODbL) · ";
    if (!st) return src + "waiting";
    if (st.down) return src + "feed down" + (st.goodAt ? " since " + formatClock(new Date(st.goodAt)) : "");
    var n = 0;
    for (var id in st.trails) if (Object.prototype.hasOwnProperty.call(st.trails, id)) n++;
    return src + n + " in the air · updated " + formatClock(new Date(st.goodAt));
  }

  // ---------- Iceland: the road camera (Vegagerðin, Gíghæð) ----------
  var CAM_LOC = { lat: 63.903, lon: -22.422 };

  // The helper's "iceland webcam" bytes -> { kind: "fresh"|"last"|"none", age, body }.
  function parseWebcam(bin) {
    bin = String(bin || "");
    var cut = bin.indexOf("\n");
    var head = parseKv((cut < 0 ? bin : bin.slice(0, cut)).split(" ").join("\n"));
    var kind = head.kind === "fresh" || head.kind === "last" ? head.kind : "none";
    var body = cut < 0 ? "" : bin.slice(cut + 1);
    if (kind === "none" || body.charCodeAt(0) !== 0xFF || body.charCodeAt(1) !== 0xD8) return { kind: "none", age: 0, body: "" };
    return { kind: kind, age: Number(head.age) || 0, body: body };
  }

  // The window shows a frame no older than 5 min, and only in daylight at
  // the camera (sun above -6°: its night frames are lifted to grey noise).
  function webcamShown(kind, ageSec, nowMs) {
    if (kind !== "fresh" && !(kind === "last" && ageSec >= 0 && ageSec <= 300)) return false;
    return sunAltitude(nowMs, CAM_LOC) > -6;
  }

  // The credit CC BY 4.0 asks for: licensor, licence, and when the frame was taken.
  function webcamCredit(ageSec, nowMs) {
    return "Road camera: Vegagerðin (IRCA), CC BY 4.0 · " + formatClock(new Date(nowMs - (Number(ageSec) || 0) * 1000));
  }

  // ---- The phone remote (issue #21) ----

  // One request body for bin/impetus-phone: "key=value" lines, the helper
  // words as w= lines. null when any value is outside the safe set.
  function phoneBody(fields, words) {
    var lines = [];
    var keys = Object.keys(fields || {});
    for (var i = 0; i < keys.length; i++) {
      var v = fields[keys[i]];
      if (v === undefined || v === null || v === "") continue;
      if (!/^[a-z]+$/.test(keys[i]) || !isSafeWord(String(v))) return null;
      lines.push(keys[i] + "=" + v);
    }
    for (var j = 0; j < (words || []).length; j++) {
      if (!isSafeWord(words[j])) return null;
      lines.push("w=" + words[j]);
    }
    return lines.join("\n") + "\n";
  }

  // A short name for the engine room's list, from the phone's user agent.
  function phoneName(ua) {
    ua = String(ua || "");
    if (/iPhone/.test(ua)) return "iPhone";
    if (/iPad/.test(ua)) return "iPad";
    if (/Android/.test(ua)) return "Android";
    return "Phone";
  }

  // Six digits, typed with or without spaces -> "123456", else null.
  function pairCode(s) {
    var c = String(s || "").replace(/\s+/g, "");
    return /^\d{6}$/.test(c) ? c : null;
  }

  // `impetus-ctl phone list` (phone=..) or the engine's state part (paired=..)
  // -> [{id, name, at}] (at in epoch s).
  function parsePhones(text) {
    var out = [];
    String(text || "").split("\n").forEach(function (line) {
      var m = /^(?:phone|paired)=([0-9a-f]{6}) ([A-Za-z0-9-]{1,20}) (\d+)$/.exec(line.trim());
      if (m) out.push({ id: m[1], name: m[2], at: Number(m[3]) });
    });
    return out;
  }

  // "PAIRED 14 NOV" for one phone.
  function pairedLine(at) {
    var d = new Date(at * 1000);
    return "PAIRED " + d.getDate() + " " + MONTHS[d.getMonth()].slice(0, 3).toUpperCase();
  }

  // The state line on the engine room's PHONE key.
  function phoneLine(state) {
    if (!state || state.phone !== "on") return "OFF";
    var port = /^\d+$/.test(state.phoneport || "") ? state.phoneport : "";
    var addr = /^[0-9.]+$/.test(state.phoneaddr || "") ? state.phoneaddr : "";
    if (addr && port) return "ON · " + addr + ":" + port;
    return port ? "ON · PORT " + port : "ON";
  }

  // The helper words that open an app from the phone. Deep-link params
  // travel base64-coded (b64: btoa in a browser), so they pass the word check.
  function openWords(id, params, b64) {
    if (!isSafeId(id)) return null;
    var w = ["open", "id=" + id];
    if (params && b64) {
      var p = b64(JSON.stringify(params));
      if (p.length <= 700 && isSafeWord(p)) w.push("params=" + p);
    }
    return w;
  }

  // ---------- The morning room (#25) ----------
  var DAY_SHORT = ["MON", "TUE", "WED", "THU", "FRI", "SAT", "SUN"];

  // "2026-11-15 07:00:00" (the Met Office's local time; Iceland keeps UTC) -> ms, or null.
  function metTime(s) {
    var m = /^(\d{4})-(\d\d)-(\d\d) (\d\d):(\d\d)/.exec(String(s || ""));
    if (!m) return null;
    return new Date(Number(m[1]), Number(m[2]) - 1, Number(m[3]), Number(m[4]), Number(m[5])).getTime();
  }

  function xmlText(s) {
    return String(s || "").replace(/<!\[CDATA\[([\s\S]*?)\]\]>/g, "$1").replace(/&lt;/g, "<").replace(/&gt;/g, ">")
      .replace(/&quot;/g, '"').replace(/&#39;|&apos;/g, "'").replace(/&amp;/g, "&").trim();
  }

  // The Met Office's XML forecast for one station -> { name, issued (ms),
  // rows: [{ t, temp, wind, dir, words }] } in time order, or null when it
  // holds no forecast we can read.
  function parseForecast(xml) {
    var s = typeof xml === "string" ? xml : "";
    var st = /<station\b[^>]*>([\s\S]*?)<\/station>/.exec(s);
    if (!st) return null;
    var body = st[1], rows = [], re = /<forecast>([\s\S]*?)<\/forecast>/g, f;
    function tag(src, name) { var m = new RegExp("<" + name + ">([\\s\\S]*?)</" + name + ">").exec(src); return m ? xmlText(m[1]) : ""; }
    while ((f = re.exec(body))) {
      var t = metTime(tag(f[1], "ftime")), temp = tag(f[1], "T"), wind = tag(f[1], "F");
      if (t === null || !/^-?\d+(\.\d+)?$/.test(temp)) continue;
      rows.push({ t: t, temp: Math.round(Number(temp)), wind: /^\d+$/.test(wind) ? Number(wind) : null,
        dir: /^[NSEWC]{1,3}$/.test(tag(f[1], "D")) ? tag(f[1], "D") : "", words: tag(f[1], "W").slice(0, 40) });
    }
    if (!rows.length) return null;
    rows.sort(function (a, b) { return a.t - b.t; });
    return { name: tag(body, "name").slice(0, 40), issued: metTime(tag(body, "atime")), rows: rows };
  }

  // The helper's `morning weather` answer -> { kind, age, forecast }. A
  // forecast that does not parse is "none": the view shows its quiet line.
  function parseWeatherReply(text) {
    var s = typeof text === "string" ? text : "", nl = s.indexOf("\n");
    var head = nl < 0 ? s : s.slice(0, nl);
    var kind = /(?:^|\s)kind=(fresh|last|none)(?=\s|$)/.exec(head), age = /(?:^|\s)age=(\d+)(?=\s|$)/.exec(head);
    var fc = kind && kind[1] !== "none" ? parseForecast(s.slice(nl + 1)) : null;
    return { kind: fc ? kind[1] : "none", age: fc && age ? Number(age[1]) : 0, forecast: fc };
  }

  // What the view draws: the hour now (the last row at or before now, else
  // the first), and the rest of today in steps of at least 3 hours, up to 5.
  // null when the forecast holds nothing from today on.
  function morningWeather(fc, nowMs) {
    if (!fc || !fc.rows || !fc.rows.length) return null;
    var rows = fc.rows, cur = null, i;
    for (i = 0; i < rows.length; i++) if (rows[i].t <= nowMs) cur = rows[i];
    if (!cur || nowMs - cur.t > 3 * 3600000) cur = rows[0].t > nowMs ? rows[0] : null;
    if (!cur) return null;
    var d = new Date(nowMs), end = new Date(d.getFullYear(), d.getMonth(), d.getDate() + 1).getTime();
    var later = [], last = cur.t;
    for (i = 0; i < rows.length && later.length < 5; i++) {
      if (rows[i].t >= last + 3 * 3600000 && rows[i].t < end) { later.push(rows[i]); last = rows[i].t; }
    }
    return { now: cur, later: later };
  }

  // -6 -> "−6°" (a true minus sign, figures of one width in the view).
  function formatTemp(t) { return (t < 0 ? "−" + (-t) : String(t)) + "°"; }

  function windLine(row) {
    if (!row || row.wind === null) return "";
    if (row.wind === 0) return "calm";
    return row.wind + " m/s" + (row.dir ? " " + row.dir : "");
  }

  // The source line under the weather: calm in every failure.
  function weatherSource(reply, nowMs, hasStation) {
    var src = "Icelandic Met Office";
    if (!hasStation) return src + " · no station set: pick one on the phone";
    if (!reply) return src + " · waiting for the forecast";
    var fc = reply.forecast, name = fc && fc.name ? " · " + fc.name : "";
    if (!fc) return src + " · feed down";
    var made = fc.issued ? " · forecast of " + formatClock(new Date(fc.issued)) : "";
    if (reply.kind === "last") return src + name + " · feed down since " + formatClock(new Date(nowMs - reply.age * 1000));
    return src + name + made;
  }

  // "1234567" style days -> "MON–FRI", "SAT SUN", "EVERY DAY".
  function daysLine(days) {
    var s = String(days || ""), on = [], i;
    for (i = 1; i <= 7; i++) if (s.indexOf(String(i)) >= 0) on.push(i);
    if (!on.length) return "";
    if (on.length === 7) return "EVERY DAY";
    var run = on.length > 2 && on[on.length - 1] - on[0] === on.length - 1;
    if (run) return DAY_SHORT[on[0] - 1] + "–" + DAY_SHORT[on[on.length - 1] - 1];
    return on.map(function (n) { return DAY_SHORT[n - 1]; }).join(" ");
  }

  // The helper's state -> the phone's line: "07:30 · MON–FRI", or "OFF".
  function morningLine(state) {
    var at = /^([01]\d|2[0-3])([0-5]\d)$/.exec((state && state.morningat) || "");
    if (!at) return "OFF";
    return at[1] + ":" + at[2] + " · " + (daysLine(state.morningdays) || "MON–FRI");
  }

  // The phone's form -> the words for `impetus-ctl morning set`, or null.
  // at "07:30", days an array of 1-7 (Monday is 1), station digits or "".
  function morningWords(at, days, station) {
    var m = /^([01]\d|2[0-3]):?([0-5]\d)$/.exec(String(at || ""));
    if (!m) return null;
    var d = (days || []).filter(function (n) { return n >= 1 && n <= 7 && Math.floor(n) === n; })
      .sort().filter(function (n, i, a) { return a.indexOf(n) === i; }).join("");
    if (!d) return null;
    var w = ["morning", "set", "at=" + m[1] + m[2], "days=" + d];
    var st = String(station === undefined || station === null ? "" : station).trim();
    if (st) {
      if (!/^[1-9]\d{0,6}$/.test(st)) return null;
      w.push("station=" + st);
    }
    return w;
  }

  var api = { metTime: metTime, parseForecast: parseForecast, parseWeatherReply: parseWeatherReply, morningWeather: morningWeather,
    formatTemp: formatTemp, windLine: windLine, weatherSource: weatherSource, daysLine: daysLine, morningLine: morningLine, morningWords: morningWords,
    parseWebcam: parseWebcam, webcamShown: webcamShown, webcamCredit: webcamCredit, parseFlightReply: parseFlightReply, flightTrails: flightTrails, flightStep: flightStep, flightSource: flightSource,
    parseQuakeInfo: parseQuakeInfo, parseQuakeReply: parseQuakeReply, isleStep: isleStep, isleSource: isleSource, formatClock: formatClock, formatDate: formatDate, formatDuration: formatDuration,
    isSafeId: isSafeId, isSafeWord: isSafeWord, sunAltitude: sunAltitude, sunDay: sunDay,
    nightWindow: nightWindow, pickApps: pickApps, launchPayload: launchPayload,
    parseLaunchParams: parseLaunchParams, ctlCommand: ctlCommand, parseKv: parseKv,
    parseSections: parseSections, parseCaps: parseCaps, sceneWords: sceneWords,
    sceneLine: sceneLine, shieldText: shieldText, shieldLine: shieldLine, countdown: countdown,
    nextBedtime: nextBedtime, bedtimeWords: bedtimeWords,
    parseStill: parseStill, stillAge: stillAge,
    parseNetstat: parseNetstat, parseNslookup: parseNslookup, ownerOf: ownerOf,
    groupTalkers: groupTalkers, scrubLog: scrubLog, shortLog: shortLog, filterLog: filterLog,
    formatUptime: formatUptime, parseVitals: parseVitals, nearest: nearest,
    phoneBody: phoneBody, phoneName: phoneName, pairCode: pairCode, parsePhones: parsePhones,
    pairedLine: pairedLine, phoneLine: phoneLine, openWords: openWords };
  if (typeof module !== "undefined" && module.exports) module.exports = api;
  else root.ImpetusLogic = api;
})(this);

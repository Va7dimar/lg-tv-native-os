// The music piece (#22): a full-screen generative drawing of what plays.
// Rules: DESIGN.md, "Music made visible". Chromium 79: ES5 only.
//
//   the sky      a deep colour field and a flow of light, in the cover's colours
//   the arc      the track's progress, drawn like the sun's day in the living room
//   the ground   the cover, the title and the artist, under the horizon
//
// Two drivers, one piece: with a beat source (ImpetusBeat, once the TV can
// hand over its sound) the flow breathes with the energy and flares on the
// beat; without one, the cover's colours and the track's progress move it.
// No sign-in, no answer, nothing playing: a quiet teal drift, no words.
// Nothing here ever shows an error or a spinner.
(function (root) {
  "use strict";

  var M = root.ImpetusMusicLogic, L = root.ImpetusLogic, LUNA = root.ImpetusLuna;
  var CFG = (root.IMPETUS_CONFIG && root.IMPETUS_CONFIG.music) || {};
  var $ = function (id) { return document.getElementById(id); };

  var TOKEN_URL = "https://accounts.spotify.com/api/token";
  var NOW_URL = "https://api.spotify.com/v1/me/player/currently-playing?additional_types=track,episode";
  var FIELD_W = 320, FIELD_H = 180;       // the colour field, stretched soft to 1920x1080
  var FLOW_W = 960, FLOW_H = 540;         // the flow of light, at half size
  var HORIZON = 820, ARC_RISE = 360, X0 = -140, X1 = 2060;
  var MIX_MS = 3500;                      // palette crossfade at a new track
  var WORDS_MS = 15000;                   // the ground's words dim after this long

  var running = false, raf = 0, pollTimer = 0, lastFrame = 0, frameMs = 1000 / (CFG.fps || 30);
  var link = null, access = null, expiresAt = 0, dead = false, busy = false, delay = 0;
  var np = { kind: "idle" }, trackId = null, wordsAt = 0;
  var palFrom = M.idlePalette(), palTo = M.idlePalette(), palAt = 0, pal = M.idlePalette();
  var seed = 1, field = null, flow = null, fg = null, lg = null, parts = [];
  var beat = root.ImpetusBeat || M.silentSource;

  // ---------- network: small, quiet, never thrown at the screen ----------

  function http(method, url, body, headers) {
    return new Promise(function (resolve) {
      var x = new XMLHttpRequest();
      x.open(method, url, true);
      x.timeout = 8000;
      Object.keys(headers || {}).forEach(function (k) { x.setRequestHeader(k, headers[k]); });
      x.onload = function () {
        var json = null;
        try { json = x.responseText ? JSON.parse(x.responseText) : null; } catch (e) { json = null; }
        resolve({ status: x.status, json: json, retryAfter: x.getResponseHeader("Retry-After") });
      };
      x.onerror = x.ontimeout = function () { resolve({ status: 0, json: null }); };
      x.send(body || null);
    });
  }

  // The sign-in lives on the TV only, in the helper's state folder.
  function loadLink() {
    if (link || dead) return Promise.resolve(link);
    return LUNA.ctl(["spotify", "get"]).then(function (text) {
      link = M.parseLink(L.parseKv(text));
      return link;
    }, function () { return null; });
  }

  function refreshToken() {
    var old = link.refresh;
    return http("POST", TOKEN_URL, M.tokenBody(link), { "Content-Type": "application/x-www-form-urlencoded" })
      .then(function (r) {
        var t = M.parseToken(r.status, r.json, Date.now(), old);
        if (t.ok) {
          access = t.access; expiresAt = t.expiresAt;
          if (t.refresh !== old) {
            // Spotify may hand out a new refresh token: keep it, unless the
            // phone wrote a new sign-in in the meantime (was= guards that).
            link.refresh = t.refresh;
            LUNA.ctl(["spotify", "set", "client=" + link.client, "refresh=" + t.refresh, "was=" + old]).then(null, function () {});
          }
          return true;
        }
        // A revoked or wrong sign-in: stop asking until the page is opened
        // again (the phone may sign in anew by then).
        if (t.dead) { dead = true; link = null; }
        return false;
      });
  }

  function ask() {
    if (root.MOCK_NOWPLAYING) return Promise.resolve(root.MOCK_NOWPLAYING(Date.now()));
    return loadLink().then(function (l) {
      if (!l) return { kind: "idle" };
      var token = access && Date.now() < expiresAt ? Promise.resolve(true) : refreshToken();
      return token.then(function (ok) {
        if (!ok) return dead ? { kind: "idle" } : { kind: "retry", afterMs: 0 };
        return http("GET", NOW_URL, null, { Authorization: "Bearer " + access }).then(function (r) {
          var got = M.parseNowPlaying(r.status, r.json, Date.now(), r.retryAfter);
          if (got.kind === "auth") { access = null; got = { kind: "retry", afterMs: 1000 }; }
          return got;
        });
      });
    });
  }

  function poll() {
    if (!running || busy) return;
    busy = true;
    ask().then(null, function () { return { kind: "retry", afterMs: 0 }; }).then(function (got) {
      busy = false;
      if (!running) return;
      // Trouble keeps what is on the screen; only a real answer changes it.
      if (got.kind !== "retry") take(got);
      delay = dead ? 0 : M.nextPollMs(got, Date.now(), delay);
      clearTimeout(pollTimer);
      if (delay) pollTimer = setTimeout(poll, delay);
    });
  }

  // ---------- what plays ----------

  function take(got) {
    np = got;
    var cap = $("mcaption");
    if (got.kind !== "track") {
      if (trackId !== null) { trackId = null; setPalette(M.idlePalette(), 1); }
      cap.classList.remove("shown");
      $("music").classList.add("idle");
      return;
    }
    $("music").classList.remove("idle");
    if (got.id === trackId) return;
    trackId = got.id;
    seed = M.hash(got.id);
    $("mtitle").textContent = got.title;
    $("martist").textContent = got.artist;
    wordsAt = Date.now();
    cap.classList.add("shown");
    cap.classList.remove("dim");
    setPalette(M.paletteFromSeed(seed), 0);
    loadCover(got.cover, got.id);
  }

  // The cover is shown as it is; its colours are read from a 24 px drawing
  // when the picture host allows it (CORS), else the seed's palette stays.
  function loadCover(url, id) {
    var shown = $("mcover");
    shown.hidden = !url;
    if (!url) return;
    shown.src = url;
    var probe = new Image();
    probe.crossOrigin = "anonymous";
    probe.onload = function () {
      if (id !== trackId) return;
      try {
        var c = document.createElement("canvas");
        c.width = 24; c.height = 24;
        var g = c.getContext("2d");
        g.drawImage(probe, 0, 0, 24, 24);
        var p = M.paletteFromPixels(g.getImageData(0, 0, 24, 24).data, seed);
        if (p) setPalette(p, 0);
      } catch (e) { /* a tainted canvas: the seed's palette stays */ }
    };
    probe.src = url;
  }

  function setPalette(p, now) {
    palFrom = pal; palTo = p; palAt = now ? 0 : Date.now();
  }

  // ---------- the sky ----------

  function spawn(p, r) {
    p.x = r() * FLOW_W; p.y = r() * FLOW_H * 0.86;
    p.life = 80 + Math.floor(r() * 220);
    p.c = Math.floor(r() * 4);
  }

  function makeParts() {
    var n = Math.max(80, Math.min(1500, CFG.particles || 560)), r = M.rng(7);
    parts = [];
    for (var i = 0; i < n; i++) { var p = {}; spawn(p, r); p.life = Math.floor(r() * 300); parts.push(p); }
  }

  // The flow's direction at a point: a few slow waves laid over each other,
  // turned by the track's seed and its progress. Cheap enough for the TV.
  function angle(x, y, t, s, prog) {
    var a = Math.sin(x * 0.0061 + t * 0.00011 + s) + Math.sin(y * 0.0083 - t * 0.00007 + s * 1.7) +
      Math.sin((x + y) * 0.0037 + t * 0.00005 + prog * 6.283);
    return a * 1.05 + prog * 3.1416;
  }

  function drawField(t, prog, drive, ph) {
    var g = fg, i;
    g.globalCompositeOperation = "source-over";
    g.fillStyle = M.css(pal.bg);
    g.fillRect(0, 0, FIELD_W, FIELD_H);
    g.globalCompositeOperation = "lighter";
    var r = M.rng(seed ^ 0x5bd1e995);
    for (i = 0; i < 5; i++) {
      var sp = 0.00004 + r() * 0.00005, o = r() * 6.283;
      // The light drifts from left to right through the track, as the sun does through the day.
      var cx = FIELD_W * (0.12 + 0.76 * (0.35 * prog + 0.65 * (0.5 + 0.5 * Math.sin(t * sp + o + i))));
      var cy = FIELD_H * (0.3 + 0.28 * Math.sin(t * sp * 1.3 + o * 2));
      var rad = FIELD_H * (0.42 + 0.22 * r()) * (1 + 0.28 * ph.beat);
      var c = pal.colors[i % 4];
      var grad = g.createRadialGradient(cx, cy, 0, cx, cy, rad);
      grad.addColorStop(0, M.css(c, (0.2 + 0.18 * drive) * (i === 4 ? 0.6 : 1)));
      grad.addColorStop(1, M.css(c, 0));
      g.fillStyle = grad;
      g.fillRect(0, 0, FIELD_W, FIELD_H);
    }
    // The ground under the horizon goes deep, so the words read.
    g.globalCompositeOperation = "source-over";
    var h = HORIZON / 1080 * FIELD_H, foot = g.createLinearGradient(0, h - 20, 0, FIELD_H);
    foot.addColorStop(0, M.css(pal.bg, 0));
    foot.addColorStop(1, M.css(pal.bg, 0.92));
    g.fillStyle = foot;
    g.fillRect(0, h - 20, FIELD_W, FIELD_H);
  }

  function drawFlow(t, prog, drive, ph, speedK) {
    var g = lg, s = (seed % 1000) / 159.2;
    // Fade what was drawn: long silky trails when calm, shorter on a loud beat.
    g.globalCompositeOperation = "destination-out";
    g.fillStyle = "rgba(0,0,0," + (0.045 + 0.05 * ph.energy).toFixed(3) + ")";
    g.fillRect(0, 0, FLOW_W, FLOW_H);
    g.globalCompositeOperation = "lighter";
    g.lineWidth = 1.2 + 1.4 * ph.beat;
    var speed = (0.9 + 2.6 * ph.energy) * speedK, r = M.rng((t | 0) ^ seed);
    var alpha = 0.16 + 0.22 * drive + 0.3 * ph.beat;
    for (var c = 0; c < 4; c++) {
      g.strokeStyle = M.css(pal.colors[c], alpha);
      g.beginPath();
      for (var i = c; i < parts.length; i += 4) {
        var p = parts[i];
        var a = angle(p.x, p.y, t, s, prog);
        var nx = p.x + Math.cos(a) * speed, ny = p.y + Math.sin(a) * speed * 0.7;
        g.moveTo(p.x, p.y); g.lineTo(nx, ny);
        p.x = nx; p.y = ny; p.life--;
        if (p.life <= 0 || nx < -10 || nx > FLOW_W + 10 || ny < -10 || ny > FLOW_H * 0.9) spawn(p, r);
      }
      g.stroke();
    }
  }

  // ---------- the arc: the track's day ----------

  function arcPoint(f) {
    var x = X0 + f * (X1 - X0), u = (x - 960) / 1100;
    return { x: x, y: HORIZON - ARC_RISE * (1 - u * u) };
  }

  function arcPath(from, to) {
    var d = "";
    for (var f = from; f <= to + 1e-9; f += 0.01) {
      var p = arcPoint(Math.min(f, to));
      d += (d ? " L" : "M") + p.x.toFixed(1) + " " + p.y.toFixed(1);
    }
    return d;
  }

  function drawArc(prog, ph) {
    var on = np.kind === "track";
    $("marc").setAttribute("d", on ? arcPath(0, 1) : "");
    $("mdone").setAttribute("d", on && prog > 0 ? arcPath(0, prog) : "");
    var pt = arcPoint(prog), sun = $("msun"), glow = $("mglow");
    sun.setAttribute("cx", pt.x); sun.setAttribute("cy", pt.y);
    glow.setAttribute("cx", pt.x); glow.setAttribute("cy", pt.y);
    glow.setAttribute("r", (120 + 90 * ph.beat).toFixed(1));
    sun.style.display = glow.style.display = on ? "" : "none";
    $("mstop0").setAttribute("stop-color", M.css(pal.colors[0]));
    $("mstop1").setAttribute("stop-color", M.css(pal.colors[1]));
    $("mdone").style.stroke = M.css(pal.colors[0]);
  }

  // ---------- one frame ----------

  function frame(now) {
    if (!running) return;
    raf = requestAnimationFrame(frame);
    if (now - lastFrame < frameMs - 2) return;
    lastFrame = now;
    var t = Date.now();
    pal = palAt ? M.mixPalette(palFrom, palTo, (t - palAt) / MIX_MS) : palTo;
    if (palAt && t - palAt >= MIX_MS) { palAt = 0; pal = palTo; }
    var live = beat.read(t);                         // null: no sound tap, the cover drives
    var playing = np.kind === "track" && np.playing;
    var prog = M.progressAt(np, t);
    var ph = live ? { energy: live.energy, beat: live.beat }
      : { energy: playing ? 0.18 + 0.1 * Math.sin(t / 5200) : 0.05, beat: 0 };
    var drive = np.kind === "track" ? 1 : 0.35;      // idle: the same sky, quieter
    var speedK = playing ? 1 : np.kind === "track" ? 0.3 : 0.45;
    drawField(t, prog, drive, ph);
    drawFlow(t, prog, drive, ph, speedK);
    drawArc(prog, ph);
    if (wordsAt && t - wordsAt > WORDS_MS) { $("mcaption").classList.add("dim"); wordsAt = 0; }
  }

  // ---------- start and stop ----------

  function start() {
    if (running) return;
    running = true;
    if (!fg) {
      field = $("mfield"); flow = $("mflow");
      field.width = FIELD_W; field.height = FIELD_H; flow.width = FLOW_W; flow.height = FLOW_H;
      fg = field.getContext("2d"); lg = flow.getContext("2d");
      makeParts();
    }
    // A sign-in that failed last time is tried again on each opening.
    dead = false; delay = 0;
    beat = root.ImpetusBeat || M.silentSource;
    lastFrame = 0;
    raf = requestAnimationFrame(frame);
    poll();
  }

  function stop() {
    running = false;
    cancelAnimationFrame(raf);
    clearTimeout(pollTimer);
    // The access token stays in memory only while the page lives; nothing is written.
  }

  root.ImpetusMusic = { start: start, stop: stop };
})(this);

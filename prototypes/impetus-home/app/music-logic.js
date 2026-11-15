// Pure logic for the music piece (#22): no DOM, no network. Host-tested with
// node (tests/test_music.js). Chromium 79 on the TV: ES5 only.
//
// Three parts:
//   the Spotify sign-in file and token answers   (what the TV keeps, what it asks)
//   "currently playing" answers                  (what is on, how far in)
//   colours                                      (a palette from the cover, or from a seed)
(function (root) {
  "use strict";

  // A Spotify client id or refresh token: base64url-ish, nothing a shell or
  // a helper word could misread. Same rule as `impetus-ctl spotify`.
  var TOKEN = /^[A-Za-z0-9._-]{1,512}$/;
  var IDLE_POLL = 15000, PLAY_POLL = 5000, MAX_BACKOFF = 120000;

  function isToken(s) { return typeof s === "string" && TOKEN.test(s); }

  // ---------- the sign-in file ----------
  //
  // `impetus-ctl spotify get` answers with key=value lines:
  //   linked=1
  //   client=<Spotify app client id>
  //   refresh=<refresh token>
  // or `linked=0` when there is no usable sign-in. -> {client, refresh} | null
  function parseLink(kv) {
    if (!kv || kv.linked !== "1") return null;
    if (!isToken(kv.client) || !isToken(kv.refresh)) return null;
    return { client: kv.client, refresh: kv.refresh };
  }

  // The form body for Spotify's token endpoint (PKCE: no client secret).
  function tokenBody(link) {
    return "grant_type=refresh_token&refresh_token=" + encodeURIComponent(link.refresh) +
      "&client_id=" + encodeURIComponent(link.client);
  }

  // The token endpoint's answer -> one of
  //   {ok: true, access, expiresAt, refresh}   refresh is the one to keep (may be new)
  //   {ok: false, dead: true}                  the sign-in is revoked or wrong: stop asking
  //   {ok: false, dead: false}                 try again later (network, 5xx, 429)
  function parseToken(status, json, nowMs, oldRefresh) {
    if (status === 200 && json && typeof json.access_token === "string" && json.access_token) {
      var life = Number(json.expires_in);
      if (!(life > 0)) life = 3600;
      var next = isToken(json.refresh_token) ? json.refresh_token : oldRefresh;
      // A minute early, so a call never goes out with a token that just ran out.
      return { ok: true, access: json.access_token, expiresAt: nowMs + (life - 60) * 1000, refresh: next };
    }
    if (status === 400 || status === 401) return { ok: false, dead: true };
    return { ok: false, dead: false };
  }

  // ---------- currently playing ----------

  function pickCover(images) {
    // The smallest picture of at least 300 px: big enough to read colours from
    // and to show at 240 px, small enough to load fast.
    var best = null;
    (images || []).forEach(function (im) {
      if (!im || typeof im.url !== "string" || !/^https:\/\//.test(im.url)) return;
      var w = Number(im.width) || 0;
      if (!best) { best = im; return; }
      var bw = Number(best.width) || 0;
      if ((w >= 300 && (bw < 300 || w < bw)) || (bw < 300 && w > bw)) best = im;
    });
    return best ? best.url : null;
  }

  // GET /v1/me/player/currently-playing -> what to draw.
  //   {kind: "track", id, title, artist, cover, playing, progressMs, durationMs, at}
  //   {kind: "idle"}     nothing playing, an ad, a podcast without art, ...
  //   {kind: "retry", afterMs}   rate limit or server trouble
  //   {kind: "auth"}     the access token ran out
  function parseNowPlaying(status, json, nowMs, retryAfterSec) {
    if (status === 204) return { kind: "idle" };
    if (status === 401) return { kind: "auth" };
    if (status === 429) {
      var s = Number(retryAfterSec);
      return { kind: "retry", afterMs: (s > 0 ? Math.min(s, 600) : 30) * 1000 };
    }
    if (status !== 200 || !json || typeof json !== "object") return { kind: "retry", afterMs: 0 };
    var it = json.item;
    if (!it || typeof it !== "object" || !it.id) return { kind: "idle" };
    var artists = (it.artists || []).map(function (a) { return a && a.name; }).filter(Boolean);
    if (!artists.length && it.show && it.show.name) artists = [it.show.name];
    var images = (it.album && it.album.images) || it.images || [];
    var dur = Number(it.duration_ms) || 0, prog = Number(json.progress_ms) || 0;
    return {
      kind: "track",
      id: String(it.id),
      title: String(it.name || ""),
      artist: artists.join(", "),
      cover: pickCover(images),
      playing: json.is_playing === true,
      progressMs: Math.max(0, Math.min(prog, dur || prog)),
      durationMs: dur,
      at: nowMs
    };
  }

  // How far into the track, 0..1, counting on from the last answer while it plays.
  function progressAt(np, nowMs) {
    if (!np || np.kind !== "track" || !(np.durationMs > 0)) return 0;
    var p = np.progressMs + (np.playing ? Math.max(0, nowMs - np.at) : 0);
    return Math.max(0, Math.min(1, p / np.durationMs));
  }

  // When to ask again. Playing: every few seconds, and just after the track
  // should end. Nothing playing: slowly. Trouble: back off, doubling.
  function nextPollMs(np, nowMs, prevDelay) {
    if (!np) return IDLE_POLL;
    if (np.kind === "retry") {
      if (np.afterMs > 0) return np.afterMs;
      return Math.min(MAX_BACKOFF, Math.max(PLAY_POLL, (prevDelay || PLAY_POLL) * 2));
    }
    if (np.kind !== "track" || !np.playing) return IDLE_POLL;
    var left = np.durationMs > 0 ? np.durationMs - (np.progressMs + Math.max(0, nowMs - np.at)) : PLAY_POLL;
    return Math.max(1000, Math.min(PLAY_POLL, left + 800));
  }

  // ---------- colours ----------

  // FNV-1a: a stable 32-bit seed from a track id.
  function hash(str) {
    var h = 0x811c9dc5;
    str = String(str || "");
    for (var i = 0; i < str.length; i++) {
      h ^= str.charCodeAt(i);
      h = Math.imul(h, 0x01000193) >>> 0;
    }
    return h >>> 0;
  }

  // mulberry32: a small repeatable random source.
  function rng(seed) {
    var a = seed >>> 0;
    return function () {
      a = (a + 0x6D2B79F5) >>> 0;
      var t = a;
      t = Math.imul(t ^ (t >>> 15), t | 1);
      t ^= t + Math.imul(t ^ (t >>> 7), t | 61);
      return ((t ^ (t >>> 14)) >>> 0) / 4294967296;
    };
  }

  function rgbToHsv(r, g, b) {
    r /= 255; g /= 255; b /= 255;
    var mx = Math.max(r, g, b), mn = Math.min(r, g, b), d = mx - mn, h = 0;
    if (d > 0) {
      if (mx === r) h = ((g - b) / d) % 6;
      else if (mx === g) h = (b - r) / d + 2;
      else h = (r - g) / d + 4;
      h *= 60; if (h < 0) h += 360;
    }
    return [h, mx === 0 ? 0 : d / mx, mx];
  }

  function hsvToRgb(h, s, v) {
    h = ((h % 360) + 360) % 360;
    var c = v * s, x = c * (1 - Math.abs((h / 60) % 2 - 1)), m = v - c, r, g, b;
    if (h < 60) { r = c; g = x; b = 0; } else if (h < 120) { r = x; g = c; b = 0; }
    else if (h < 180) { r = 0; g = c; b = x; } else if (h < 240) { r = 0; g = x; b = c; }
    else if (h < 300) { r = x; g = 0; b = c; } else { r = c; g = 0; b = x; }
    return [Math.round((r + m) * 255), Math.round((g + m) * 255), Math.round((b + m) * 255)];
  }

  function hueGap(a, b) { var d = Math.abs(a - b) % 360; return d > 180 ? 360 - d : d; }

  // Lights for a dark room: colours kept vivid enough to glow, never white-hot.
  function lift(hsv) { return hsvToRgb(hsv[0], Math.min(0.95, Math.max(0.45, hsv[1] * 1.15)), Math.min(0.98, Math.max(0.72, hsv[2]))); }
  // The deep ground under them: the darkest tone of the main colour.
  function ground(hsv) { return hsvToRgb(hsv[0], Math.min(0.85, hsv[1] * 0.9 + 0.1), 0.07); }

  // A palette from a seed alone (no cover, or a cover the page may not read):
  // {bg, colors: [4 x [r,g,b]]}. Same seed, same palette.
  function paletteFromSeed(seed) {
    var r = rng(seed), h = r() * 360, spread = 25 + r() * 60, out = [];
    for (var i = 0; i < 4; i++) {
      var hh = h + (i - 1.5) * spread + (i === 3 ? 150 : 0);
      out.push(hsvToRgb(hh, 0.55 + r() * 0.35, 0.7 + r() * 0.28));
    }
    return { bg: hsvToRgb(h, 0.6, 0.07), colors: out };
  }

  // The quiet state: the living room's own teal, dim.
  function idlePalette() {
    return { bg: [3, 8, 9], colors: [[31, 180, 135], [44, 140, 134], [24, 92, 96], [90, 120, 140]] };
  }

  // RGBA pixels (a small drawing of the cover) -> {bg, colors: [4]}.
  // Hues are binned, each bin weighted by how much colour it carries; the
  // strongest bins that sit apart from each other become the lights. A grey
  // cover takes its hue from the seed instead. null when there is nothing to read.
  function paletteFromPixels(data, seed) {
    var BINS = 18, bins = [], i, n = 0;
    for (i = 0; i < BINS; i++) bins.push({ w: 0, s: 0, v: 0, x: 0, y: 0 });
    if (!data || data.length < 4) return null;
    for (i = 0; i + 3 < data.length; i += 4) {
      if (data[i + 3] < 128) continue;
      n++;
      var hsv = rgbToHsv(data[i], data[i + 1], data[i + 2]);
      var w = hsv[1] * hsv[1] * (0.25 + hsv[2]);
      if (hsv[2] < 0.12 || hsv[1] < 0.12) w *= 0.05;
      var b = bins[Math.floor(hsv[0] / (360 / BINS)) % BINS];
      // Hue is summed as a vector so 359 and 1 average to 0, not 180.
      b.w += w; b.s += hsv[1] * w; b.v += hsv[2] * w;
      b.x += Math.cos(hsv[0] * Math.PI / 180) * w;
      b.y += Math.sin(hsv[0] * Math.PI / 180) * w;
    }
    if (!n) return null;
    var picked = [], total = 0;
    bins.forEach(function (b) { total += b.w; });
    var ranked = bins.filter(function (b) { return b.w > 0; }).map(function (b) {
      var h = Math.atan2(b.y, b.x) * 180 / Math.PI; if (h < 0) h += 360;
      return { w: b.w, hsv: [h, b.s / b.w, b.v / b.w] };
    }).sort(function (a, b) { return b.w - a.w; });
    ranked.forEach(function (c) {
      if (picked.length >= 4 || c.w < total * 0.04) return;
      for (var j = 0; j < picked.length; j++) if (hueGap(picked[j][0], c.hsv[0]) < 24) return;
      picked.push(c.hsv);
    });
    var rand = rng(seed >>> 0);
    if (!picked.length) {
      // A grey or black-and-white cover: one hue from the seed, kept soft.
      picked.push([rand() * 360, 0.35, 0.8]);
    }
    // Fewer than four: neighbours of the main hue fill the rest.
    var base = picked[0];
    var k = 1;
    while (picked.length < 4) {
      picked.push([base[0] + (k % 2 ? 1 : -1) * (18 + 14 * k), Math.max(0.3, base[1] * (0.9 - 0.1 * k)), Math.min(1, base[2] + 0.1 * k)]);
      k++;
    }
    return { bg: ground(base), colors: picked.map(lift) };
  }

  function mixColor(a, b, t) {
    return [Math.round(a[0] + (b[0] - a[0]) * t), Math.round(a[1] + (b[1] - a[1]) * t), Math.round(a[2] + (b[2] - a[2]) * t)];
  }

  function mixPalette(a, b, t) {
    t = Math.max(0, Math.min(1, t));
    return { bg: mixColor(a.bg, b.bg, t), colors: a.colors.map(function (c, i) { return mixColor(c, b.colors[i], t); }) };
  }

  function css(c, alpha) {
    return alpha === undefined ? "rgb(" + c[0] + "," + c[1] + "," + c[2] + ")" :
      "rgba(" + c[0] + "," + c[1] + "," + c[2] + "," + Math.max(0, Math.min(1, alpha)).toFixed(3) + ")";
  }

  // ---------- the beat ----------
  //
  // The piece reads one value a frame from a beat source:
  //   source.read(nowMs) -> null                        no sound tap: the cover drives the piece
  //                       | {energy: 0..1, beat: 0..1}  energy = loudness, beat = a pulse that
  //                                                    jumps to 1 on a beat and decays
  // `silentSource` is the stand-in until the TV probe says where sound can be read.
  var silentSource = { read: function () { return null; } };

  // A made-up beat for the PC preview: bpm, with a slow swell.
  function demoSource(bpm) {
    var period = 60000 / (bpm || 120);
    return {
      read: function (nowMs) {
        var ph = (nowMs % period) / period;
        var swell = 0.55 + 0.45 * Math.sin(nowMs / 9000);
        return { energy: Math.max(0, Math.min(1, swell * (0.7 + 0.3 * Math.exp(-ph * 4)))), beat: Math.exp(-ph * 6) };
      }
    };
  }

  // ---------- launch params ----------

  // The keeper opens Impetus with {show: "music", at: <epoch s>}. A param set
  // is taken once (the same object comes back on every return to the page)
  // and only while it is fresh.
  function showMusic(p, nowMs, taken) {
    if (!p || p.show !== "music") return false;
    var at = Number(p.at);
    if (!(at > 0) || at === taken) return false;
    return Math.abs(nowMs / 1000 - at) <= 120;
  }

  var api = { isToken: isToken, parseLink: parseLink, tokenBody: tokenBody, parseToken: parseToken,
    pickCover: pickCover, parseNowPlaying: parseNowPlaying, progressAt: progressAt, nextPollMs: nextPollMs,
    hash: hash, rng: rng, rgbToHsv: rgbToHsv, hsvToRgb: hsvToRgb, paletteFromSeed: paletteFromSeed,
    idlePalette: idlePalette, paletteFromPixels: paletteFromPixels, mixPalette: mixPalette, css: css,
    silentSource: silentSource, demoSource: demoSource, showMusic: showMusic,
    IDLE_POLL: IDLE_POLL, PLAY_POLL: PLAY_POLL, MAX_BACKOFF: MAX_BACKOFF };
  if (typeof module !== "undefined" && module.exports) module.exports = api;
  else root.ImpetusMusicLogic = api;
})(this);

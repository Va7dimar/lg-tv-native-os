// Host checks for app/music-logic.js and the MUSIC scene words (#22).
// Run: node tests/test_music.js
"use strict";
const assert = require("assert");
const fs = require("fs");
const path = require("path");
const M = require("../app/music-logic.js");
const L = require("../app/logic.js");

let n = 0;
function t(name, fn) { fn(); n++; console.log("ok  " + name); }

// ---------- the sign-in ----------

t("parseLink: a sign-in, or none", () => {
  assert.deepStrictEqual(M.parseLink(L.parseKv("linked=1\nclient=abc123\nrefresh=AQB-x_y.z")), { client: "abc123", refresh: "AQB-x_y.z" });
  assert.strictEqual(M.parseLink(L.parseKv("linked=0")), null);
  assert.strictEqual(M.parseLink(L.parseKv("")), null);
  assert.strictEqual(M.parseLink(L.parseKv("linked=1\nclient=abc\nrefresh=a b")), null);
  assert.strictEqual(M.parseLink(L.parseKv("linked=1\nclient=a'b\nrefresh=x")), null);
});

t("tokenBody: PKCE refresh, no secret, encoded", () => {
  const b = M.tokenBody({ client: "abc", refresh: "x.y-z" });
  assert.strictEqual(b, "grant_type=refresh_token&refresh_token=x.y-z&client_id=abc");
  assert.ok(!/secret/.test(b));
});

t("parseToken: ok, rotated, revoked, trouble", () => {
  const ok = M.parseToken(200, { access_token: "AT", expires_in: 3600 }, 1000, "OLD");
  assert.deepStrictEqual(ok, { ok: true, access: "AT", expiresAt: 1000 + 3540 * 1000, refresh: "OLD" });
  assert.strictEqual(M.parseToken(200, { access_token: "AT", refresh_token: "NEW" }, 0, "OLD").refresh, "NEW");
  assert.strictEqual(M.parseToken(200, { access_token: "AT", refresh_token: "bad token" }, 0, "OLD").refresh, "OLD");
  assert.deepStrictEqual(M.parseToken(400, { error: "invalid_grant" }, 0, "OLD"), { ok: false, dead: true });
  assert.deepStrictEqual(M.parseToken(0, null, 0, "OLD"), { ok: false, dead: false });
  assert.deepStrictEqual(M.parseToken(503, null, 0, "OLD"), { ok: false, dead: false });
  assert.deepStrictEqual(M.parseToken(200, {}, 0, "OLD"), { ok: false, dead: false });
});

// ---------- currently playing ----------

const answer = {
  is_playing: true, progress_ms: 60000,
  item: { id: "4uLU6hMCjMI75M1A2tKUQC", name: "A Song", duration_ms: 240000,
    artists: [{ name: "One" }, { name: "Two" }],
    album: { images: [
      { url: "https://i.scdn.co/image/640", width: 640, height: 640 },
      { url: "https://i.scdn.co/image/300", width: 300, height: 300 },
      { url: "https://i.scdn.co/image/64", width: 64, height: 64 }] } }
};

t("parseNowPlaying: a track", () => {
  const np = M.parseNowPlaying(200, answer, 5000);
  assert.deepStrictEqual(np, { kind: "track", id: "4uLU6hMCjMI75M1A2tKUQC", title: "A Song", artist: "One, Two",
    cover: "https://i.scdn.co/image/300", playing: true, progressMs: 60000, durationMs: 240000, at: 5000 });
});

t("parseNowPlaying: nothing, an ad, auth, rate limit, trouble", () => {
  assert.deepStrictEqual(M.parseNowPlaying(204, null, 0), { kind: "idle" });
  assert.deepStrictEqual(M.parseNowPlaying(200, { is_playing: true, item: null, currently_playing_type: "ad" }, 0), { kind: "idle" });
  assert.deepStrictEqual(M.parseNowPlaying(401, null, 0), { kind: "auth" });
  assert.deepStrictEqual(M.parseNowPlaying(429, null, 0, "7"), { kind: "retry", afterMs: 7000 });
  assert.deepStrictEqual(M.parseNowPlaying(429, null, 0, null), { kind: "retry", afterMs: 30000 });
  assert.deepStrictEqual(M.parseNowPlaying(0, null, 0), { kind: "retry", afterMs: 0 });
  assert.deepStrictEqual(M.parseNowPlaying(502, null, 0), { kind: "retry", afterMs: 0 });
});

t("parseNowPlaying: an episode takes the show's name and its own images", () => {
  const np = M.parseNowPlaying(200, { is_playing: false, progress_ms: 10,
    item: { id: "ep1", name: "Episode", duration_ms: 100, show: { name: "The Show" },
      images: [{ url: "https://i.scdn.co/image/e", width: 640 }] } }, 0);
  assert.strictEqual(np.artist, "The Show");
  assert.strictEqual(np.cover, "https://i.scdn.co/image/e");
  assert.strictEqual(np.playing, false);
});

t("pickCover: https only, smallest of at least 300 px", () => {
  assert.strictEqual(M.pickCover([{ url: "http://x/a", width: 640 }]), null);
  assert.strictEqual(M.pickCover([{ url: "https://x/64", width: 64 }]), "https://x/64");
  assert.strictEqual(M.pickCover([{ url: "https://x/64", width: 64 }, { url: "https://x/640", width: 640 }]), "https://x/640");
  assert.strictEqual(M.pickCover([]), null);
});

t("progressAt: counts on while playing, holds when paused, stays in 0..1", () => {
  const np = M.parseNowPlaying(200, answer, 0);
  assert.strictEqual(M.progressAt(np, 0), 0.25);
  assert.strictEqual(M.progressAt(np, 60000), 0.5);
  assert.strictEqual(M.progressAt(np, 10 * 60000), 1);
  const paused = Object.assign({}, np, { playing: false });
  assert.strictEqual(M.progressAt(paused, 60000), 0.25);
  assert.strictEqual(M.progressAt({ kind: "idle" }, 0), 0);
});

t("nextPollMs: often while playing, at the track's end, slowly when idle, backing off in trouble", () => {
  const np = M.parseNowPlaying(200, answer, 0);
  assert.strictEqual(M.nextPollMs(np, 0, 0), M.PLAY_POLL);
  assert.strictEqual(M.nextPollMs(np, 178000, 0), 2800);          // 2 s left + 0.8 s
  assert.strictEqual(M.nextPollMs(np, 300000, 0), 1000);
  assert.strictEqual(M.nextPollMs({ kind: "idle" }, 0, 0), M.IDLE_POLL);
  assert.strictEqual(M.nextPollMs(Object.assign({}, np, { playing: false }), 0, 0), M.IDLE_POLL);
  assert.strictEqual(M.nextPollMs({ kind: "retry", afterMs: 7000 }, 0, 0), 7000);
  assert.strictEqual(M.nextPollMs({ kind: "retry", afterMs: 0 }, 0, 5000), 10000);
  assert.strictEqual(M.nextPollMs({ kind: "retry", afterMs: 0 }, 0, 100000), M.MAX_BACKOFF);
});

// ---------- colours ----------

function pixels(list) {
  const out = [];
  list.forEach(([rgb, count]) => { for (let i = 0; i < count; i++) out.push(rgb[0], rgb[1], rgb[2], 255); });
  return out;
}
function hueOf(c) { return M.rgbToHsv(c[0], c[1], c[2])[0]; }
function near(h, want, tol) { const d = Math.abs(h - want) % 360; return Math.min(d, 360 - d) <= tol; }
function valid(p) {
  assert.strictEqual(p.colors.length, 4);
  [p.bg].concat(p.colors).forEach(c => c.forEach(v => assert.ok(Number.isInteger(v) && v >= 0 && v <= 255)));
}

t("hash and rng: stable", () => {
  assert.strictEqual(M.hash("abc"), M.hash("abc"));
  assert.notStrictEqual(M.hash("abc"), M.hash("abd"));
  const a = M.rng(5), b = M.rng(5);
  for (let i = 0; i < 5; i++) assert.strictEqual(a(), b());
});

t("hsv round trip", () => {
  [[255, 0, 0], [12, 200, 90], [30, 30, 30], [250, 240, 10]].forEach(c => {
    const h = M.rgbToHsv(c[0], c[1], c[2]);
    const back = M.hsvToRgb(h[0], h[1], h[2]);
    back.forEach((v, i) => assert.ok(Math.abs(v - c[i]) <= 1, c + " -> " + back));
  });
});

t("paletteFromPixels: a red and blue cover gives red and blue lights on a dark ground", () => {
  const p = M.paletteFromPixels(pixels([[[220, 30, 40], 300], [[30, 60, 210], 200], [[10, 10, 10], 76]]), 1);
  valid(p);
  assert.ok(near(hueOf(p.colors[0]), 356, 15), "main " + hueOf(p.colors[0]));
  assert.ok(p.colors.slice(1).some(c => near(hueOf(c), 228, 20)), "blue somewhere");
  assert.ok(Math.max.apply(null, p.bg) < 40, "ground is dark " + p.bg);
  p.colors.forEach(c => assert.ok(Math.max.apply(null, c) >= 150, "lights glow " + c));
});

t("paletteFromPixels: reds either side of 0 are one colour, not cyan", () => {
  const p = M.paletteFromPixels(pixels([[[230, 20, 30], 100], [[230, 30, 15], 100]]), 1);
  assert.ok(near(hueOf(p.colors[0]), 0, 15), hueOf(p.colors[0]));
});

t("paletteFromPixels: a grey cover takes a hue from the seed, the same every time", () => {
  const grey = pixels([[[128, 128, 128], 200], [[20, 20, 20], 200]]);
  const a = M.paletteFromPixels(grey, 42), b = M.paletteFromPixels(grey, 42);
  valid(a);
  assert.deepStrictEqual(a, b);
});

t("paletteFromPixels: nothing to read", () => {
  assert.strictEqual(M.paletteFromPixels([], 1), null);
  assert.strictEqual(M.paletteFromPixels([1, 2, 3, 0], 1), null);
});

t("paletteFromSeed, idlePalette, mixPalette, css", () => {
  valid(M.paletteFromSeed(7));
  assert.deepStrictEqual(M.paletteFromSeed(7), M.paletteFromSeed(7));
  valid(M.idlePalette());
  const a = M.idlePalette(), b = M.paletteFromSeed(9);
  assert.deepStrictEqual(M.mixPalette(a, b, 0), a);
  assert.deepStrictEqual(M.mixPalette(a, b, 1), b);
  assert.deepStrictEqual(M.mixPalette(a, b, 5), b);
  assert.strictEqual(M.css([1, 2, 3]), "rgb(1,2,3)");
  assert.strictEqual(M.css([1, 2, 3], 0.5), "rgba(1,2,3,0.500)");
  assert.strictEqual(M.css([1, 2, 3], 2), "rgba(1,2,3,1.000)");
});

// ---------- the beat ----------

t("beat sources: the stand-in is silent, the demo stays in range", () => {
  assert.strictEqual(M.silentSource.read(0), null);
  const d = M.demoSource(120);
  for (let ms = 0; ms < 20000; ms += 37) {
    const v = d.read(ms);
    assert.ok(v.energy >= 0 && v.energy <= 1 && v.beat >= 0 && v.beat <= 1);
  }
  assert.ok(d.read(0).beat > 0.99 && d.read(400).beat < 0.1);
});

// ---------- how the piece is opened ----------

t("showMusic: fresh params once", () => {
  const now = 1794650000 * 1000;
  assert.strictEqual(M.showMusic({ show: "music", at: 1794650000 }, now, 0), true);
  assert.strictEqual(M.showMusic({ show: "music", at: 1794650000 }, now, 1794650000), false);
  assert.strictEqual(M.showMusic({ show: "music", at: 1794649000 }, now, 0), false);
  assert.strictEqual(M.showMusic({ show: "music" }, now, 0), false);
  assert.strictEqual(M.showMusic({ notice: "sleep" }, now, 0), false);
  assert.strictEqual(M.showMusic(null, now, 0), false);
});

t("sceneWords: piece instead of screen off; needs the helper", () => {
  const caps = { exec: true, screenoff: true };
  const both = { id: "music", launch: "spotify-beehive", pieceAfterSeconds: 20, screenOffAfterSeconds: 20 };
  assert.deepStrictEqual(L.sceneWords(both, { caps }), ["id=music", "launch=spotify-beehive", "piece=20"]);
  assert.strictEqual(L.sceneWords({ id: "music", launch: "x", pieceAfterSeconds: 20 }, { caps: {} }), null);
  assert.deepStrictEqual(L.sceneWords(both, { caps: { screenoff: true } }), ["id=music", "launch=spotify-beehive", "screenoff=20"]);
  assert.strictEqual(L.sceneWords({ id: "music", pieceAfterSeconds: 601 }, { caps }), null);
  assert.strictEqual(L.sceneWords({ id: "music", pieceAfterSeconds: 2.5 }, { caps }), null);
});

t("sceneLine: the piece's hour", () => {
  const at = new Date(2026, 10, 14, 21, 4).getTime() / 1000;
  assert.strictEqual(L.sceneLine({ scene: "music", piece: String(at) }, "music"), "ON · DRAWN FROM 21:04");
});

t("the shipped config: MUSIC draws the piece", () => {
  global.window = {};
  require("../app/config.js");
  const cfg = global.window.IMPETUS_CONFIG, music = cfg.scenes.filter(s => s.id === "music")[0];
  assert.ok(music && music.pieceAfterSeconds > 0);
  assert.ok(cfg.music.fps > 0 && cfg.music.particles > 0);
});

t("public repo: no Spotify secret or token in the app", () => {
  const dir = path.join(__dirname, "..", "app");
  ["music.js", "music-logic.js", "config.js", "home.js", "luna.js"].forEach(f => {
    const s = fs.readFileSync(path.join(dir, f), "utf8");
    assert.ok(!/client_secret/i.test(s), f);
    assert.ok(!/\bBQ[A-Za-z0-9_-]{40,}/.test(s) && !/\bAQ[A-Za-z0-9_-]{40,}/.test(s), f + " holds what looks like a token");
  });
});

t("the shield blocks no Spotify host", () => {
  const hosts = fs.readFileSync(path.join(__dirname, "..", "app", "shield", "hosts.txt"), "utf8");
  ["accounts.spotify.com", "api.spotify.com", "i.scdn.co"].forEach(h => {
    hosts.split("\n").forEach(line => {
      const name = line.trim();
      if (!name || name[0] === "#") return;
      assert.ok(h !== name && !h.endsWith("." + name), h + " blocked by " + name);
    });
  });
});

console.log(n + " tests, 0 failed");

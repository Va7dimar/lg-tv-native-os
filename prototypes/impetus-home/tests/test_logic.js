// Host checks for app/logic.js. Run: node tests/test_logic.js
"use strict";
const assert = require("assert");
const L = require("../app/logic.js");

const cfg = {
  selfId: "org.va7dimar.home",
  order: ["netflix"],
  hide: ["hidden.by.owner"],
  labels: { "spotify-beehive": "Spotify" },
};
const apps = [
  { id: "youtube", title: "YouTube", visible: true },
  { id: "netflix", title: "Netflix", visible: true },
  { id: "spotify-beehive", title: "Spotify - Music and Podcasts", visible: true },
  { id: "rakuten", title: "Rakuten TV - Movies", visible: true },
  { id: "org.va7dimar.home", title: "Impetus", visible: true },
  { id: "hidden.by.owner", title: "X", visible: true },
  { id: "com.webos.app.browser", title: "Browser", visible: true, systemApp: true },
  { id: "invisible", title: "Y", visible: false },
  { id: "classhidden", title: "Z", visible: true, class: { hidden: true } },
  { id: "bad id; rm", title: "Evil", visible: true },
  { id: "com.webos.app.hdmi2", title: "HDMI2", visible: false, systemApp: true },
];
const ALL = { exec: true, picture: true, screenoff: true, volume: true, sleep: true };
const film = { id: "film", launch: "com.webos.app.hdmi2", pictureMode: "cinema",
  sunMode: { backlight: 30, colorTemperature: -20 } };
const music = { id: "music", launch: "spotify-beehive", screenOffAfterSeconds: 20 };
const wind = { id: "winddown", launch: "last", picture: { backlight: 25 }, volumeMax: 12, sleepMinutes: 60 };
const onUtc = new Date(2026, 10, 14).getTimezoneOffset() === 0;

let n = 0;
function t(name, fn) { fn(); n++; console.log("ok  " + name); }

t("pickApps: filter, order, label", () => {
  const got = L.pickApps(apps, cfg);
  assert.deepStrictEqual(got.map(a => a.id), ["netflix", "rakuten", "spotify-beehive", "youtube"]);
  assert.strictEqual(got[1].label, "Rakuten TV");
  assert.strictEqual(got[2].label, "Spotify");
});

t("clock, English date, duration", () => {
  const d = new Date(2026, 10, 14, 7, 5, 9);
  assert.strictEqual(L.formatClock(d), "07:05");
  assert.strictEqual(L.formatDate(d), "Saturday 14 November");
  assert.strictEqual(L.formatDuration(375), "6 h 15 min");
});

t("sun: Reykjavik 14 Nov 2026 rise ~09:54, set ~16:31 UTC (+-10 min)", () => {
  // Expected values from the closed-form hour angle (dec -18.3 deg, lat 64.15,
  // -0.833 deg): half-day 49.6 deg = 3 h 18 min around solar noon 13:13.
  // Iceland is UTC all year; the check runs only when the host is on UTC.
  const day = L.sunDay(new Date(2026, 10, 14, 12, 0));
  const mins = ms => new Date(ms).getUTCHours() * 60 + new Date(ms).getUTCMinutes();
  if (onUtc) {
    assert.ok(Math.abs(mins(day.rise) - (9 * 60 + 54)) <= 10, "rise " + mins(day.rise));
    assert.ok(Math.abs(mins(day.set) - (16 * 60 + 31)) <= 10, "set " + mins(day.set));
  }
  assert.ok(day.peakAlt > 5 && day.peakAlt < 12, "peak " + day.peakAlt);
  // Midsummer: the sun barely sets.
  const jun = L.sunDay(new Date(2026, 5, 21, 12, 0));
  assert.ok((jun.set - jun.rise) / 3600000 > 20, "june day");
});

t("nightWindow: starts at sunset by day, at once by night, ends at the next sunrise", () => {
  const noon = Date.UTC(2026, 10, 14, 12, 0), noonS = noon / 1000;
  const day = L.nightWindow(noon);
  assert.ok(day.start > noonS && day.start < noonS + 12 * 3600, "start " + day.start);
  assert.ok(day.end > day.start && day.end < noonS + 30 * 3600, "end " + day.end);
  if (onUtc) {
    assert.ok(Math.abs(day.start - Date.UTC(2026, 10, 14, 16, 31) / 1000) <= 600, "sunset");
    assert.ok(Math.abs(day.end - Date.UTC(2026, 10, 15, 9, 57) / 1000) <= 600, "next sunrise");
  }
  const evening = L.nightWindow(Date.UTC(2026, 10, 14, 20, 0));
  assert.strictEqual(evening.start, 0);
  assert.ok(Math.abs(evening.end - day.end) <= 60, "same sunrise");
  const early = L.nightWindow(Date.UTC(2026, 10, 14, 3, 0));
  assert.strictEqual(early.start, 0);
  assert.ok(early.end > Date.UTC(2026, 10, 14, 3, 0) / 1000 && early.end < day.start, "this morning's sunrise");
});

t("launchPayload: safe ids, no single quote in params", () => {
  assert.deepStrictEqual(L.launchPayload("netflix"), { id: "netflix" });
  assert.deepStrictEqual(L.launchPayload("y", { contentTarget: "a" }), { id: "y", params: { contentTarget: "a" } });
  assert.strictEqual(L.launchPayload("x'; reboot"), null);
  assert.strictEqual(L.launchPayload("y", { contentTarget: "it's" }), null);
});

t("parseLaunchParams: string, object, rubbish", () => {
  assert.deepStrictEqual(L.parseLaunchParams('{"notice":"sleep","until":1700}'), { notice: "sleep", until: 1700 });
  assert.deepStrictEqual(L.parseLaunchParams({ notice: "sleep" }), { notice: "sleep" });
  assert.deepStrictEqual(L.parseLaunchParams("{broken"), {});
  assert.deepStrictEqual(L.parseLaunchParams(""), {});
  assert.deepStrictEqual(L.parseLaunchParams(undefined), {});
  assert.deepStrictEqual(L.parseLaunchParams("7"), {});
});

t("ctlCommand: one fixed shape, every word checked", () => {
  const dir = "/media/developer/apps/usr/palm/applications/org.va7dimar.home";
  assert.strictEqual(L.ctlCommand(dir, ["scene", "on", "id=film", "night=backlight:30,colorTemperature:-20"]),
    "sh " + dir + "/bin/impetus-ctl scene on id=film night=backlight:30,colorTemperature:-20");
  for (const bad of ["a b", "x;reboot", "$(reboot)", "`reboot`", "a|b", "a&b", "it's", 'say"hi"', "a>b", "", "a\nb"]) {
    assert.strictEqual(L.ctlCommand(dir, ["state", bad]), null, JSON.stringify(bad));
  }
  assert.strictEqual(L.ctlCommand(dir, []), null);
  assert.strictEqual(L.ctlCommand("relative/dir", ["state"]), null);
  assert.strictEqual(L.ctlCommand("/tmp/../etc", ["state"]), null);
  assert.strictEqual(L.ctlCommand("/tmp/x y", ["state"]), null);
  assert.strictEqual(L.ctlCommand(undefined, ["state"]), null);
});

t("parseKv, parseSections, parseCaps", () => {
  assert.deepStrictEqual(L.parseKv("a=1\nb=two=2\nnoise\n c = 3 \n"), { a: "1", b: "two=2", c: "3" });
  assert.deepStrictEqual(L.parseSections("skipped\n@vitals\ntemp=47000\nuptime=5\n@talk\n@log\nline one\nline two"),
    { vitals: "temp=47000\nuptime=5", talk: "", log: "line one\nline two" });
  assert.deepStrictEqual(L.parseCaps("exec=1\npicture=0\nshield=1"), { exec: true, picture: false, shield: true });
  assert.deepStrictEqual(L.parseCaps(""), {});
});

t("sceneWords: the three scenes on a TV that can do everything", () => {
  const ctx = { caps: ALL, night: { start: 100, end: 200 }, fallback: "com.webos.app.hdmi2" };
  assert.deepStrictEqual(L.sceneWords(film, ctx), ["id=film", "launch=com.webos.app.hdmi2", "mode=cinema",
    "night=backlight:30,colorTemperature:-20", "nightstart=100", "end=200"]);
  assert.deepStrictEqual(L.sceneWords(music, ctx), ["id=music", "launch=spotify-beehive", "screenoff=20"]);
  assert.deepStrictEqual(L.sceneWords(wind, ctx), ["id=winddown", "launch=@last", "fallback=com.webos.app.hdmi2",
    "set=backlight:25", "volmax=12", "sleep=60"]);
  for (const s of [film, music, wind]) for (const w of L.sceneWords(s, ctx)) assert.ok(L.isSafeWord(w), w);
});

t("sceneWords: parts this TV cannot do are left out; nothing left means no scene", () => {
  const night = { start: 100, end: 200 };
  assert.deepStrictEqual(L.sceneWords(film, { caps: ALL, night: null }), ["id=film", "launch=com.webos.app.hdmi2", "mode=cinema"]);
  assert.strictEqual(L.sceneWords(film, { caps: { screenoff: true, volume: true, sleep: true }, night }), null);
  assert.strictEqual(L.sceneWords(music, { caps: { picture: true }, night }), null);
  assert.deepStrictEqual(L.sceneWords(wind, { caps: { sleep: true }, night }), ["id=winddown", "launch=@last", "sleep=60"]);
  assert.strictEqual(L.sceneWords(wind, { caps: {}, night }), null);
  assert.strictEqual(L.sceneWords(wind, undefined), null);
});

t("sceneWords: a malformed scene is refused whole", () => {
  const ctx = { caps: ALL, night: { start: 1, end: 2 } };
  assert.strictEqual(L.sceneWords({ id: "x y", pictureMode: "cinema" }, ctx), null);
  assert.strictEqual(L.sceneWords({ id: "x", launch: "a;b", pictureMode: "cinema" }, ctx), null);
  assert.strictEqual(L.sceneWords({ id: "x", pictureMode: "cin ema" }, ctx), null);
  assert.strictEqual(L.sceneWords({ id: "x", picture: { backlight: "30;reboot" } }, ctx), null);
  assert.strictEqual(L.sceneWords({ id: "x", sunMode: { backlight: "a b" } }, ctx), null);
  assert.strictEqual(L.sceneWords({ id: "x", sleepMinutes: 0 }, ctx), null);
  assert.strictEqual(L.sceneWords({ id: "x", sleepMinutes: 1.5 }, ctx), null);
  assert.strictEqual(L.sceneWords({ id: "x", volumeMax: 101 }, ctx), null);
  assert.strictEqual(L.sceneWords({ id: "x", screenOffAfterSeconds: 601 }, ctx), null);
  assert.strictEqual(L.sceneWords(null, ctx), null);
  // A key outside the known picture keys is never sent.
  assert.deepStrictEqual(L.sceneWords({ id: "x", picture: { backlight: 10, evil: "1" } }, ctx), ["id=x", "set=backlight:10"]);
});

t("sceneLine: what a latched key says", () => {
  const at = s => L.formatClock(new Date(s * 1000));
  assert.strictEqual(L.sceneLine({ scene: "film", end: "1794650000" }, "film"), "ON · UNTIL " + at(1794650000));
  assert.strictEqual(L.sceneLine({ scene: "winddown", sleep: "1794600000", end: "" }, "winddown"), "ON · SLEEPS " + at(1794600000));
  assert.strictEqual(L.sceneLine({ scene: "music", screenoff: "1794600020" }, "music"), "ON · SCREEN OFF " + at(1794600020));
  assert.strictEqual(L.sceneLine({ scene: "music", sleep: "", end: "", screenoff: "" }, "music"), "ON");
  assert.strictEqual(L.sceneLine({ scene: "film" }, "music"), null);
  assert.strictEqual(L.sceneLine({ scene: "" }, ""), null);
  assert.strictEqual(L.sceneLine(null, "film"), null);
});

t("shieldText, shieldLine, countdown", () => {
  assert.strictEqual(L.shieldText({ shield: "off" }), "OFF");
  assert.strictEqual(L.shieldText({}), "OFF");
  assert.strictEqual(L.shieldText({ shield: "on", hits: "1204" }), "1204");
  assert.strictEqual(L.shieldText({ shield: "on", hits: "" }), "ON");
  assert.strictEqual(L.shieldLine({ shield: "on", hits: "1204" }), "ON · 1204 BLOCKED");
  assert.strictEqual(L.shieldLine({ shield: "on" }), "ON");
  assert.strictEqual(L.shieldLine({ shield: "off", hits: "9" }), "OFF");
  assert.strictEqual(L.countdown(1075, 1000 * 1000), "1:15");
  assert.strictEqual(L.countdown(1120, 1000 * 1000), "2:00");
  assert.strictEqual(L.countdown(1005, 1000 * 1000), "0:05");
  assert.strictEqual(L.countdown(900, 1000 * 1000), "0:00");
});

t("parseStill and stillAge", () => {
  const jpg = "\xFF\xD8\xFF\xE0 picture\nbytes";
  assert.deepStrictEqual(L.parseStill("kind=live age=0\n" + jpg), { kind: "live", age: 0, body: jpg });
  assert.deepStrictEqual(L.parseStill("kind=last age=720\n" + jpg), { kind: "last", age: 720, body: jpg });
  assert.deepStrictEqual(L.parseStill("kind=none age=0\n"), { kind: "none", age: 0, body: "" });
  assert.deepStrictEqual(L.parseStill("kind=live age=0\nnot a picture"), { kind: "none", age: 0, body: "" });
  assert.deepStrictEqual(L.parseStill("error=word"), { kind: "none", age: 0, body: "" });
  assert.deepStrictEqual(L.parseStill(""), { kind: "none", age: 0, body: "" });
  assert.strictEqual(L.stillAge("live", 0), "LIVE");
  assert.strictEqual(L.stillAge("last", 720), "12 MIN AGO");
  assert.strictEqual(L.stillAge("last", 20), "1 MIN AGO");
  assert.strictEqual(L.stillAge("last", 7200), "2 H AGO");
});

t("parseNetstat: established, no loopback, program name", () => {
  const text = [
    "Active Internet connections (w/o servers)",
    "Proto Recv-Q Send-Q Local Address           Foreign Address         State       PID/Program name",
    "tcp        0      0 10.0.0.5:51234          142.250.74.46:443       ESTABLISHED 1234/WebAppMgr",
    "tcp        0      0 127.0.0.1:3000          127.0.0.1:41000         ESTABLISHED 99/node",
    "tcp        0      0 10.0.0.5:40000          52.1.2.3:443            TIME_WAIT   -",
    "tcp        0      0 ::ffff:10.0.0.5:5555    ::ffff:3.4.5.6:443      ESTABLISHED -",
  ].join("\n");
  assert.deepStrictEqual(L.parseNetstat(text), [
    { ip: "142.250.74.46", port: "443", prog: "WebAppMgr" },
    { ip: "3.4.5.6", port: "443", prog: "?" },
  ]);
});

t("parseNslookup: busybox and bind styles", () => {
  assert.strictEqual(L.parseNslookup("46.74.250.142.in-addr.arpa\tname = arn09s23-in-f14.1e100.net.\n", "x"), "arn09s23-in-f14.1e100.net");
  assert.strictEqual(L.parseNslookup("Server: 1.1.1.1\nAddress 1: 1.1.1.1 one.one.one.one\n\nName: 8.8.8.8\nAddress 1: 8.8.8.8 dns.google\n", "8.8.8.8"), "dns.google");
  assert.strictEqual(L.parseNslookup("** server can't find 1.2.3.4: NXDOMAIN", "1.2.3.4"), null);
});

t("ownerOf: by name suffix, else by address", () => {
  assert.strictEqual(L.ownerOf("eic.rdx2.lgtvsdp.com", "34.1.2.3"), "LG");
  assert.strictEqual(L.ownerOf("SNU.LGE.COM", "18.1.2.3"), "LG");
  assert.strictEqual(L.ownerOf("arn09s23-in-f14.1e100.net", "142.250.74.46"), "Google");
  assert.strictEqual(L.ownerOf("ichnaea.netflix.com"), "Netflix");
  assert.strictEqual(L.ownerOf("ec2-3-248-12-1.eu-west-1.compute.amazonaws.com"), "Amazon cloud");
  assert.strictEqual(L.ownerOf("notlge.com", "8.8.8.8"), "Unknown");
  assert.strictEqual(L.ownerOf(null, "192.168.1.20"), "Home network");
  assert.strictEqual(L.ownerOf(undefined, "172.20.1.1"), "Home network");
  assert.strictEqual(L.ownerOf(null, "172.32.1.1"), "Unknown");
  assert.strictEqual(L.ownerOf(null, "8.8.8.8"), "Unknown");
});

t("groupTalkers: by program and owner, most first", () => {
  const conns = [
    { ip: "1.1.1.1", port: "443", prog: "WebAppMgr" }, { ip: "1.1.1.2", port: "443", prog: "WebAppMgr" },
    { ip: "2.2.2.2", port: "443", prog: "rdxd" }, { ip: "1.1.1.1", port: "80", prog: "WebAppMgr" },
    { ip: "9.9.9.9", port: "443", prog: "WebAppMgr" },
  ];
  const hosts = { "1.1.1.1": "a.1e100.net", "1.1.1.2": "b.google.com", "2.2.2.2": "eic.rdx2.lgtvsdp.com", "9.9.9.9": null };
  assert.deepStrictEqual(L.groupTalkers(conns, hosts), { total: 5, rows: [
    { prog: "WebAppMgr", owner: "Google", count: 3 },
    { prog: "rdxd", owner: "LG", count: 1 },
    { prog: "WebAppMgr", owner: "Unknown", count: 1 },
  ] });
  assert.deepStrictEqual(L.groupTalkers([], {}), { total: 0, rows: [] });
  assert.deepStrictEqual(L.groupTalkers(undefined, undefined), { total: 0, rows: [] });
});

t("scrubLog: device ids never reach the screen", () => {
  const dirty = 'boot serial=ABC123XYZ nduid: "0123456789abcdef0123456789abcdef01234567" mac AA:BB:CC:DD:EE:FF ' +
    'uuid 123e4567-e89b-12d3-a456-426614174000 key 0f3c9a7be21d4c55aa01 at 192.168.1.50 and 10.0.0.5 via 8.8.8.8';
  const clean = L.scrubLog(dirty);
  for (const secret of ["ABC123XYZ", "0123456789abcdef", "AA:BB:CC", "123e4567", "0f3c9a7be21d4c55aa01", "192.168.1.50", "10.0.0.5"]) {
    assert.ok(clean.indexOf(secret) < 0, secret + " left in: " + clean);
  }
  assert.ok(clean.indexOf("8.8.8.8") >= 0, "a public address stays");
  assert.ok(clean.indexOf("192.168.x.x") >= 0 && clean.indexOf("10.x.x") >= 0, clean);
  assert.strictEqual(L.scrubLog('{"deviceId":"LGTV-1234","wifi_mac":"aabbccddeeff"}'), '{"deviceId":"[hidden]","wifi_mac":"[hidden]"}');
  assert.strictEqual(L.scrubLog("volume changed 14 -> 12"), "volume changed 14 -> 12");
});

t("shortLog and filterLog: newest lines, shortened, own polling left out", () => {
  assert.deepStrictEqual(L.shortLog('2026-11-14T21:02:41.120394Z [5521.100] user.info sam [] SAM APP_LAUNCH {"app_id":"netflix"}'),
    { t: "21:02:41", who: "sam", msg: '[] SAM APP_LAUNCH {"app_id":"netflix"}' });
  assert.deepStrictEqual(L.shortLog("Nov 14 21:03:10 LGwebOSTV connmand[412]: wlan0 lease renewed"),
    { t: "21:03:10", who: "connmand", msg: "wlan0 lease renewed" });
  assert.deepStrictEqual(L.shortLog("something else entirely"), { t: "", who: "", msg: "something else entirely" });
  const text = [
    "2026-11-14T21:02:41.120394Z [5521.100] user.info sam [] SAM APP_LAUNCH netflix",
    "",
    "2026-11-14T21:03:30.118742Z [5570.098] user.info luna-send [] poll",
    "2026-11-14T21:03:31.000000Z [5571.000] user.info sam [] launch org.va7dimar.home",
    "2026-11-14T21:03:40.004410Z [5579.984] user.err rdxd [] " + "x".repeat(200),
    "2026-11-14T21:03:41.004410Z [5580.984] user.info nyx [] mac AA:BB:CC:DD:EE:FF up",
  ].join("\n");
  const got = L.filterLog(text, 10);
  assert.deepStrictEqual(got.map(l => l.who), ["sam", "rdxd", "nyx"]);
  assert.strictEqual(got[0].msg, "SAM APP_LAUNCH netflix");
  assert.strictEqual(got[1].msg.length, 120);
  assert.strictEqual(got[2].msg, "mac [mac] up");
  assert.deepStrictEqual(L.filterLog(text, 1).map(l => l.who), ["nyx"]);
  assert.deepStrictEqual(L.filterLog("", 5), []);
});

t("formatUptime and parseVitals", () => {
  assert.strictEqual(L.formatUptime(59), "0 min");
  assert.strictEqual(L.formatUptime(3725), "1 h 2 min");
  assert.strictEqual(L.formatUptime("93784.2"), "1 d 2 h");
  assert.deepStrictEqual(L.parseVitals({ temp: "47000", uptime: "3725.5", memtotal: "1048576", memavail: "524288",
    diskused: "262144", disktotal: "1048576" }),
    { tempC: 47, uptime: "1 h 2 min", mem: { pct: 50, text: "0.5 / 1.0 GB" }, disk: { pct: 25, text: "0.3 / 1.0 GB" } });
  assert.deepStrictEqual(L.parseVitals({ temp: "52" }), { tempC: 52, uptime: null, mem: null, disk: null });
  assert.deepStrictEqual(L.parseVitals({ temp: "", memtotal: "", memavail: "5" }), { tempC: null, uptime: null, mem: null, disk: null });
  assert.deepStrictEqual(L.parseVitals(undefined), { tempC: null, uptime: null, mem: null, disk: null });
});

t("nearest: spatial focus picks the closest in direction", () => {
  const r = [
    { x: 0, y: 0, w: 700, h: 500 },     // 0 big focal
    { x: 0, y: 560, w: 220, h: 150 },   // 1 shortcut a
    { x: 240, y: 560, w: 220, h: 150 }, // 2 shortcut b
    { x: 750, y: 0, w: 300, h: 100 },   // 3 app top
    { x: 750, y: 600, w: 300, h: 100 }, // 4 app low
  ];
  assert.strictEqual(L.nearest(r, 0, "down"), 1);
  assert.strictEqual(L.nearest(r, 0, "right"), 3);
  assert.strictEqual(L.nearest(r, 2, "right"), 4);
  assert.strictEqual(L.nearest(r, 1, "up"), 0);
  assert.strictEqual(L.nearest(r, 0, "left"), 0);
});

t("isSafeId and isSafeWord reject shell characters", () => {
  assert.ok(L.isSafeId("com.webos.app.hdmi2"));
  assert.ok(!L.isSafeId("x'; reboot"));
  assert.ok(L.isSafeWord("night=backlight:30,colorTemperature:-20"));
  assert.ok(L.isSafeWord("launch=@last"));
  assert.ok(!L.isSafeWord("a b") && !L.isSafeWord("a;b") && !L.isSafeWord("$(x)") && !L.isSafeWord(7));
});

t("the shipped config: every scene yields safe words", () => {
  global.window = {};
  require("../app/config.js");
  const scenes = global.window.IMPETUS_CONFIG.scenes;
  assert.strictEqual(scenes.length, 3);
  for (const s of scenes) {
    const w = L.sceneWords(s, { caps: ALL, night: { start: 0, end: 1794650000 }, fallback: "com.webos.app.hdmi2" });
    assert.ok(w && w.length > 1, s.id);
    assert.ok(L.ctlCommand("/media/developer/apps/usr/palm/applications/org.va7dimar.home", ["scene", "on"].concat(w)), s.id);
  }
});

// ---------- Iceland: the quake list ----------
const fs = require("fs"), path = require("path");
const QUAKE_PAGE = fs.readFileSync(path.join(__dirname, "fixtures", "vedur-quakeinfo-2026-11-15.txt"), "utf8");
const QUAKE_NOW = Date.UTC(2026, 10, 15, 0, 20, 0);

t("quakes: the 15.11 page gives 75, newest first, read as UTC", () => {
  const q = L.parseQuakeInfo("<script>\n" + QUAKE_PAGE + "</script>", QUAKE_NOW);
  assert.strictEqual(q.length, 75);
  assert.strictEqual(q[0].t, Date.UTC(2026, 10, 15, 0, 4, 18));
  assert.strictEqual(q[0].lat, 63.91); assert.strictEqual(q[0].lon, -21.186);
  assert.strictEqual(q[0].m, 0.4); assert.strictEqual(q[0].dep, 5.5); assert.strictEqual(q[0].place, "Selfoss");
  for (let i = 1; i < q.length; i++) assert.ok(q[i - 1].t >= q[i].t);
  assert.ok(q.some(x => x.place === "Goðabunga"), "Icelandic letters survive");
});

t("quakes: older than 49 h and out-of-range entries are dropped", () => {
  const one = (t, lat, lon, s) => "{'t':new Date(" + t + "),'lat':'" + lat + "','lon':'" + lon + "','dep':'1.0','s':'" + s + "','q':'90.0','dR':'X'}";
  const text = "quakeInfo = [" + [
    one("2026,11-1,14,12,0,0", "63.9", "-22.1", "1.2"),   // kept
    one("2026,11-1,12,12,0,0", "63.9", "-22.1", "1.2"),   // 60 h old
    one("2026,11-1,14,12,0,0", "51.5", "-0.1", "1.2"),    // London
    one("2026,11-1,14,12,0,0", "63.9", "-22.1", "9.9"),   // magnitude out of range
    one("2026,11-1,14,12,0,0", "63.9", "-22.1", "abc"),   // not a number
    "{'t':'yesterday','lat':'63.9','lon':'-22.1','s':'1.0'}" // no date
  ].join(",") + "];";
  const q = L.parseQuakeInfo(text, QUAKE_NOW);
  assert.strictEqual(q.length, 1);
  assert.strictEqual(q[0].m, 1.2);
});

t("quakes: no array is null (feed down); an empty array is an empty list", () => {
  assert.strictEqual(L.parseQuakeInfo("<html>maintenance</html>", QUAKE_NOW), null);
  assert.strictEqual(L.parseQuakeInfo("", QUAKE_NOW), null);
  assert.strictEqual(L.parseQuakeInfo(null, QUAKE_NOW), null);
  assert.strictEqual(L.parseQuakeInfo("quakeInfo = [ ];", QUAKE_NOW).length, 0);
  assert.strictEqual(L.parseQuakeInfo("quakeInfo = [{'t':new Date(2026,11-1,14,1,2,3)", QUAKE_NOW), null);
});

t("quakes: nothing in the page is evaluated", () => {
  global.__pwned = false;
  const text = "quakeInfo = [{'t':new Date(2026,11-1,14,12,0,0),'lat':'63.9','lon':'-22.1','s':'1.0','dR':'');__pwned=true;('x'}];";
  const q = L.parseQuakeInfo(text, QUAKE_NOW);
  assert.strictEqual(global.__pwned, false);
  assert.ok(Array.isArray(q));
});

t("quakes: the helper's reply gives kind, age and the list", () => {
  const fresh = L.parseQuakeReply("kind=fresh age=0\n" + QUAKE_PAGE, QUAKE_NOW);
  assert.strictEqual(fresh.kind, "fresh"); assert.strictEqual(fresh.age, 0); assert.strictEqual(fresh.quakes.length, 75);
  const last = L.parseQuakeReply("kind=last age=300\n" + QUAKE_PAGE, QUAKE_NOW);
  assert.strictEqual(last.kind, "last"); assert.strictEqual(last.age, 300);
  for (const bad of ["kind=none age=0", "kind=none age=0\n", "", null, "error=iceland", "kind=fresh age=0",
    "kind=fresh age=0\n<html>maintenance</html>", "kind=freshest age=0\n" + QUAKE_PAGE]) {
    const r = L.parseQuakeReply(bad, QUAKE_NOW);
    assert.deepStrictEqual(r, { kind: "none", age: 0, quakes: null }, String(bad).slice(0, 40));
  }
  // Entries on the page but none readable: the page changed, so the feed is down.
  const changed = QUAKE_PAGE.replace(/new Date\(/g, "new Datum(");
  assert.deepStrictEqual(L.parseQuakeReply("kind=fresh age=0\n" + changed, QUAKE_NOW), { kind: "none", age: 0, quakes: null });
  // A quiet island: an empty list is still a good list.
  assert.deepStrictEqual(L.parseQuakeReply("kind=fresh age=0\nquakeInfo = [];", QUAKE_NOW).quakes, []);
});

t("quakes: the feed state keeps the last list and says since when it is down", () => {
  const NOW = QUAKE_NOW, A = [{ t: NOW - 60000 }], B = [{ t: NOW - 1000 }];
  const at = (ms) => L.formatClock(new Date(ms));
  assert.strictEqual(L.isleSource(null), "Icelandic Met Office · waiting for the list");
  // Nothing yet, and the helper has nothing: down, no time, no list.
  let st = L.isleStep(null, { kind: "none", age: 0, quakes: null }, NOW);
  assert.deepStrictEqual(st, { quakes: null, goodAt: null, down: true });
  assert.strictEqual(L.isleSource(st), "Icelandic Met Office · feed down");
  // A fresh list.
  st = L.isleStep(st, { kind: "fresh", age: 30, quakes: A }, NOW);
  assert.deepStrictEqual(st, { quakes: A, goodAt: NOW - 30000, down: false });
  assert.strictEqual(L.isleSource(st), "Icelandic Met Office · updated " + at(NOW - 30000));
  // The fetch fails: the list stays, the line says since when.
  const later = NOW + 120000;
  st = L.isleStep(st, { kind: "none", age: 0, quakes: null }, later);
  assert.deepStrictEqual(st, { quakes: A, goodAt: NOW - 30000, down: true });
  assert.strictEqual(L.isleSource(st), "Icelandic Met Office · feed down since " + at(NOW - 30000));
  // The helper's older copy never replaces a newer list the page holds.
  st = L.isleStep(st, { kind: "last", age: 600, quakes: B }, later);
  assert.deepStrictEqual(st, { quakes: A, goodAt: NOW - 30000, down: true });
  // A newer copy from the helper is shown, still as down.
  st = L.isleStep(st, { kind: "last", age: 10, quakes: B }, later);
  assert.deepStrictEqual(st, { quakes: B, goodAt: later - 10000, down: true });
  // Back up.
  st = L.isleStep(st, { kind: "fresh", age: 0, quakes: A }, later);
  assert.strictEqual(st.down, false);
  assert.strictEqual(L.isleSource(st), "Icelandic Met Office · updated " + at(later));
});

const FLIGHTS = fs.readFileSync(path.join(__dirname, "fixtures", "adsb-lol-2026-11-15.json"), "utf8");
const FLIGHT_NOW = 1794704979500;

t("flights: adsb.lol's answer gives the aircraft with their fix times", () => {
  const r = L.parseFlightReply("kind=fresh age=0\n" + FLIGHTS, FLIGHT_NOW);
  assert.strictEqual(r.kind, "fresh");
  assert.deepStrictEqual(r.flights.map(f => [f.id, f.call, f.track]), [["48ae25", "LOT2E", 269.38], ["471f41", "WZZ89J", 290.87]]);
  assert.strictEqual(r.flights[1].t, FLIGHT_NOW - 17762);
  const ac = (o) => "kind=fresh age=0\n" + JSON.stringify({ now: FLIGHT_NOW, ac: [Object.assign({ hex: "4cc2a1", lat: 64, lon: -22, track: 90, seen_pos: 1 }, o)] });
  assert.strictEqual(L.parseFlightReply(ac({}), FLIGHT_NOW).flights.length, 1);
  for (const bad of [{ alt_baro: "ground" }, { lat: null }, { track: undefined }, { lat: 55 }, { lon: 10 }, { seen_pos: 90 },
    { hex: "<img>" }]) {
    assert.strictEqual(L.parseFlightReply(ac(bad), FLIGHT_NOW).flights.length, 0, JSON.stringify(bad));
  }
  assert.strictEqual(L.parseFlightReply(ac({ flight: "<b>x</b>" }), FLIGHT_NOW).flights[0].call, "");
  for (const bad of ["kind=none age=0", "kind=fresh age=0\n{not json", "kind=fresh age=0\n{\"msg\":\"x\"}", "", null,
    "kind=fresh age=0"]) {
    assert.deepStrictEqual(L.parseFlightReply(bad, FLIGHT_NOW), { kind: "none", age: 0, flights: null }, String(bad));
  }
});

t("flights: trails keep ten fixes, add only newer ones and drop a plane gone for 3 min", () => {
  const fix = (id, t) => ({ id, call: "", lat: 64, lon: -20, track: 0, t });
  let tr = {};
  for (let i = 1; i <= 12; i++) tr = L.flightTrails(tr, [fix("a", i * 60000)], i * 60000);
  assert.strictEqual(tr.a.length, 10);
  assert.strictEqual(tr.a[0].t, 3 * 60000);
  const same = L.flightTrails(tr, [fix("a", 12 * 60000), fix("a", 5 * 60000)], 12 * 60000);
  assert.strictEqual(same.a.length, 10);
  assert.strictEqual(tr.a.length, 10, "the old trails are not changed");
  assert.deepStrictEqual(L.flightTrails(tr, [], 12 * 60000 + 180001), {});
});

t("flights: the feed state and its line", () => {
  const at = (ms) => L.formatClock(new Date(ms));
  const fresh = L.parseFlightReply("kind=fresh age=0\n" + FLIGHTS, FLIGHT_NOW);
  assert.strictEqual(L.flightSource(null), "Aircraft: adsb.lol (ODbL) · waiting");
  let st = L.flightStep(null, fresh, FLIGHT_NOW);
  assert.strictEqual(L.flightSource(st), "Aircraft: adsb.lol (ODbL) · 2 in the air · updated " + at(FLIGHT_NOW));
  st = L.flightStep(st, { kind: "none", age: 0, flights: null }, FLIGHT_NOW + 60000);
  assert.strictEqual(st.down, true);
  assert.strictEqual(Object.keys(st.trails).length, 2, "kept while under 3 min");
  assert.strictEqual(L.flightSource(st), "Aircraft: adsb.lol (ODbL) · feed down since " + at(FLIGHT_NOW));
  st = L.flightStep(st, { kind: "none", age: 0, flights: null }, FLIGHT_NOW + 240000);
  assert.deepStrictEqual(st.trails, {}, "no frozen planes");
  assert.strictEqual(L.flightSource(L.flightStep(null, { kind: "none", age: 0, flights: null }, FLIGHT_NOW)), "Aircraft: adsb.lol (ODbL) · feed down");
});

t("webcam: the helper's answer, read", () => {
  const jpg = "\xFF\xD8\xFF\xE0rest";
  assert.deepStrictEqual(L.parseWebcam("kind=fresh age=0\n" + jpg), { kind: "fresh", age: 0, body: jpg });
  assert.deepStrictEqual(L.parseWebcam("kind=last age=90\n" + jpg), { kind: "last", age: 90, body: jpg });
  assert.strictEqual(L.parseWebcam("kind=fresh age=0\n<html>error</html>").kind, "none", "not a JPG");
  assert.strictEqual(L.parseWebcam("kind=none age=0").kind, "none");
  assert.strictEqual(L.parseWebcam("").kind, "none");
  assert.strictEqual(L.parseWebcam("kind=live age=0\n" + jpg).kind, "none", "only fresh or last");
});

t("webcam: shown in daylight while the frame is young, with its credit", () => {
  const noon = Date.UTC(2026, 10, 15, 13, 0);      // sun about +7° at Gíghæð
  const night = Date.UTC(2026, 10, 15, 22, 0);
  const dusk = Date.UTC(2026, 10, 15, 17, 45);     // sun about -7°: the camera only shows grey noise
  assert.strictEqual(L.webcamShown("fresh", 0, noon), true);
  assert.strictEqual(L.webcamShown("last", 300, noon), true);
  assert.strictEqual(L.webcamShown("last", 301, noon), false, "older than 5 min");
  assert.strictEqual(L.webcamShown("none", 0, noon), false);
  assert.strictEqual(L.webcamShown("fresh", 0, night), false);
  assert.strictEqual(L.webcamShown("fresh", 0, dusk), false);
  const at = L.formatClock(new Date(noon - 90000));
  assert.strictEqual(L.webcamCredit(90, noon), "Road camera: Vegagerðin (IRCA), CC BY 4.0 · " + at);
});

t("shield: none of its names blocks a host the Iceland room needs", () => {
  const FEEDS = ["en.vedur.is", "vedur.is", "api.adsb.lol", "adsb.lol", "www.vegagerdin.is", "vegagerdin.is"];
  const names = fs.readFileSync(path.join(__dirname, "..", "app", "shield", "hosts.txt"), "utf8")
    .split(/\r?\n/).map(s => s.trim()).filter(s => s && s[0] !== "#");
  assert.strictEqual(names.length, 45);
  for (const host of FEEDS) {
    for (const name of names) {
      assert.ok(host !== name && !host.endsWith("." + name), name + " would block " + host);
    }
  }
});

t("nextBedtime: tonight's hour, still tonight's a while after, then tomorrow's", () => {
  const at = (h, m, day) => new Date(2026, 10, day || 14, h, m).getTime();
  assert.strictEqual(L.nextBedtime(at(20, 0), "22:30"), at(22, 30) / 1000);
  assert.strictEqual(L.nextBedtime(at(23, 59), "22:30"), at(22, 30) / 1000);     // TV turned on late
  assert.strictEqual(L.nextBedtime(at(1, 30, 15), "22:30"), at(22, 30, 15) / 1000); // past the window
  assert.strictEqual(L.nextBedtime(at(23, 0), "00:15"), at(0, 15, 15) / 1000);    // after midnight
  assert.strictEqual(L.nextBedtime(at(0, 20, 15), "00:15"), at(0, 15, 15) / 1000);
  for (const bad of ["24:00", "7:30", "22.30", "", null, "22:30;reboot"]) assert.strictEqual(L.nextBedtime(at(20, 0), bad), null);
});

t("bedtimeWords: safe helper words, defaults, off and malformed", () => {
  const now = new Date(2026, 10, 14, 20, 0).getTime();
  const w = L.bedtimeWords({ at: "22:30", scene: "winddown" }, now);
  assert.deepStrictEqual(w, ["bedtime", "set", "at=" + new Date(2026, 10, 14, 22, 30).getTime() / 1000, "step=10", "every=15", "floor=10"]);
  assert.ok(L.ctlCommand("/media/developer/apps/usr/palm/applications/org.va7dimar.home", w));
  assert.deepStrictEqual(L.bedtimeWords({ at: "23:00", stepBacklight: 5, everyMinutes: 10, floorBacklight: 0 }, now).slice(3),
    ["step=5", "every=10", "floor=0"]);
  assert.strictEqual(L.bedtimeWords(null, now), null);
  assert.strictEqual(L.bedtimeWords({ scene: "winddown" }, now), null);
  assert.strictEqual(L.bedtimeWords({ at: "22:30", stepBacklight: 0 }, now), null);
  assert.strictEqual(L.bedtimeWords({ at: "22:30", everyMinutes: "15" }, now), null);
  assert.strictEqual(L.bedtimeWords({ at: "22:30", floorBacklight: 101 }, now), null);
});

t("the shipped config: the bedtime nudge offers a scene that exists", () => {
  const c = global.window.IMPETUS_CONFIG;
  assert.ok(L.bedtimeWords(c.bedtime, Date.now()));
  assert.ok(c.scenes.some(s => s.id === c.bedtime.scene));
});

t("phoneBody: key lines and word lines, nothing unsafe", () => {
  assert.strictEqual(L.phoneBody({ op: "do", t: "ab12" }, ["scene", "off"]), "op=do\nt=ab12\nw=scene\nw=off\n");
  assert.strictEqual(L.phoneBody({ op: "hello", t: "" }, []), "op=hello\n");
  assert.strictEqual(L.phoneBody({ op: "do" }, ["a;reboot"]), null);
  assert.strictEqual(L.phoneBody({ op: "x\nw=restore" }, []), null);
  assert.strictEqual(L.phoneBody({ "o p": "do" }, []), null);
});

t("phoneName and pairCode", () => {
  assert.strictEqual(L.phoneName("Mozilla/5.0 (iPhone; CPU iPhone OS 18_0 like Mac OS X)"), "iPhone");
  assert.strictEqual(L.phoneName("Mozilla/5.0 (Linux; Android 15; Pixel 9)"), "Android");
  assert.strictEqual(L.phoneName(undefined), "Phone");
  assert.strictEqual(L.pairCode("123 456"), "123456");
  assert.strictEqual(L.pairCode(" 012345 "), "012345");
  assert.strictEqual(L.pairCode("12345"), null);
  assert.strictEqual(L.pairCode("12a456"), null);
});

t("parsePhones reads the list and the engine's paired lines", () => {
  const text = "phone=3fa91c iPhone 1763100000\npaired=b07e22 Android 1763142000\nphone=on\nphone=XYZ bad 1\npaired=abcdef a;b 1";
  assert.deepStrictEqual(L.parsePhones(text), [
    { id: "3fa91c", name: "iPhone", at: 1763100000 }, { id: "b07e22", name: "Android", at: 1763142000 }]);
  assert.deepStrictEqual(L.parsePhones(undefined), []);
});

t("pairedLine and phoneLine", () => {
  assert.strictEqual(L.pairedLine(new Date(2026, 10, 14, 12).getTime() / 1000), "PAIRED 14 NOV");
  assert.strictEqual(L.phoneLine({ phone: "off" }), "OFF");
  assert.strictEqual(L.phoneLine({ phone: "none" }), "OFF");
  assert.strictEqual(L.phoneLine({ phone: "on", phoneport: "8090", phoneaddr: "192.0.2.7" }), "ON · 192.0.2.7:8090");
  assert.strictEqual(L.phoneLine({ phone: "on", phoneport: "8090", phoneaddr: "" }), "ON · PORT 8090");
  assert.strictEqual(L.phoneLine({ phone: "on", phoneport: "x" }), "ON");
});

t("openWords: a safe id, params base64-coded and capped", () => {
  const b64 = (s) => Buffer.from(s).toString("base64");
  assert.deepStrictEqual(L.openWords("netflix"), ["open", "id=netflix"]);
  assert.deepStrictEqual(L.openWords("netflix", { a: 1 }, b64), ["open", "id=netflix", "params=" + b64('{"a":1}')]);
  assert.deepStrictEqual(L.openWords("netflix", { a: "x".repeat(600) }, b64), ["open", "id=netflix"]);
  assert.strictEqual(L.openWords("x; reboot"), null);
});

console.log(n + " tests, 0 failed");

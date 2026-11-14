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
const ALL = { picture: true, screenoff: true, volume: true, sleep: true };
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

console.log(n + " tests, 0 failed");

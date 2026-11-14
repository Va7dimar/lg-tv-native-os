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

let n = 0;
function t(name, fn) { fn(); n++; console.log("ok  " + name); }

t("pickApps: filter, order, label", () => {
  const got = L.pickApps(apps, cfg);
  assert.deepStrictEqual(got.map(a => a.id), ["netflix", "rakuten", "spotify-beehive", "youtube"]);
  assert.strictEqual(got[1].label, "Rakuten TV");
  assert.strictEqual(got[2].label, "Spotify");
});

t("clock, Icelandic date, duration", () => {
  const d = new Date(2026, 10, 14, 7, 5, 9);
  assert.strictEqual(L.formatClock(d), "07:05");
  assert.strictEqual(L.formatDate(d), "laugardagur 14. nóvember");
  assert.strictEqual(L.formatDuration(375), "6 klst. 15 mín.");
});

t("sun: Reykjavik 14 Nov 2026 rise ~09:54, set ~16:31 UTC (+-10 min)", () => {
  // Expected values from the closed-form hour angle (dec -18.3 deg, lat 64.15,
  // -0.833 deg): half-day 49.6 deg = 3 h 18 min around solar noon 13:13.
  // Iceland is UTC all year; the check runs only when the host is on UTC.
  const day = L.sunDay(new Date(2026, 10, 14, 12, 0));
  const mins = ms => new Date(ms).getUTCHours() * 60 + new Date(ms).getUTCMinutes();
  if (new Date(2026, 10, 14).getTimezoneOffset() === 0) {
    assert.ok(Math.abs(mins(day.rise) - (9 * 60 + 54)) <= 10, "rise " + mins(day.rise));
    assert.ok(Math.abs(mins(day.set) - (16 * 60 + 31)) <= 10, "set " + mins(day.set));
  }
  assert.ok(day.peakAlt > 5 && day.peakAlt < 12, "peak " + day.peakAlt);
  // Midsummer: the sun barely sets.
  const jun = L.sunDay(new Date(2026, 5, 21, 12, 0));
  assert.ok((jun.set - jun.rise) / 3600000 > 20, "june day");
});

t("launchPayload: safe ids, no single quote in params", () => {
  assert.deepStrictEqual(L.launchPayload("netflix"), { id: "netflix" });
  assert.deepStrictEqual(L.launchPayload("y", { contentTarget: "a" }), { id: "y", params: { contentTarget: "a" } });
  assert.strictEqual(L.launchPayload("x'; reboot"), null);
  assert.strictEqual(L.launchPayload("y", { contentTarget: "it's" }), null);
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

t("isSafeId rejects shell characters", () => {
  assert.ok(L.isSafeId("com.webos.app.hdmi2"));
  assert.ok(!L.isSafeId("x'; reboot"));
});

console.log(n + " tests, 0 failed");

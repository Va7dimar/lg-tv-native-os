// Room 4: Iceland (#26). The island at 1920x1080 and the last 48 hours of
// earthquakes as warm light, as in the approved mock. Three layers: the base
// (land, lens frame, ribbon axis, legend, credit) is drawn once; the quakes
// layer is redrawn from each list and each minute; the motion layer (HTML:
// the live dot, the ripple on the newest quake, the breathing of halos under
// 6 h) moves by CSS transform and opacity only. Rules: DESIGN.md "Room 4: Iceland".
// Chromium 79: ES5 only. No blend modes, no blur on anything that moves.
(function (root) {
  "use strict";
  var NS = "http://www.w3.org/2000/svg";
  var L = root.ImpetusLogic, MAP = root.ICELAND_MAP, PJ = MAP.projection;
  var LENS = { lon: MAP.lens.lon, lat: MAP.lens.lat, k: MAP.lens.k, r: MAP.lens.r, cx: 420, cy: 770 };
  var GLOWS = 400;              // halos drawn at most, half on the map and half in the lens (the newest); every quake keeps its core
  var BREATHE = 40;             // halos under 6 h that breathe (HTML, layer 3) at most; the rest stay still in the SVG
  var HOUR = 3600000, DAY = 24 * HOUR;
  var DAYS = ["SUN", "MON", "TUE", "WED", "THU", "FRI", "SAT"];
  var RIBBON = { x0: 600, x1: 1824, base: 1032 };

  // Volcanic zones: the mock's hand sketch, for orientation only.
  var ZONES = [
    [[-23.6, 63.55], [-22.7, 63.82], [-22.0, 63.92], [-21.3, 64.03], [-20.8, 64.4], [-20.2, 64.75]],
    [[-20.3, 63.42], [-19.7, 63.95], [-18.6, 64.25], [-17.5, 64.45], [-16.9, 64.75], [-16.75, 65.05], [-16.8, 65.7], [-17.2, 66.1], [-17.9, 66.5]]
  ];
  var PLACES = [["Reykjavík", -21.94, 64.146, "r"], ["Akureyri", -18.09, 65.68, "r"], ["Ísafjörður", -23.13, 66.07, "r"],
    ["Egilsstaðir", -14.4, 65.26, "l"], ["Vík", -19.0, 63.42, "r"]];
  var LENS_PLACES = [["Grindavík", -22.43, 63.84, 1], ["Reykjanestá", -22.70, 63.815, 0], ["Krýsuvík", -22.06, 63.89, 1],
    ["Keflavík", -22.56, 64.0, 1], ["Svartsengi", -22.43, 63.88, 0]];
  // Region rows on the map: the Met Office's place names, grouped, with where the label sits.
  var GROUPS = [
    ["Bárðarbunga", ["Bárðarbunga", "Kistufell", "Dyngjujökull"], -26, -22, "end"],
    ["Kverkfjöll", ["Kverkfjöll"], 26, 6, "start"],
    ["Torfajökull · Hekla", ["Álftavatn", "Vatnafjöll", "Hrafntinnusker", "Torfajökull", "Hekla"], 16, 34, "start"],
    ["Mýrdalsjökull", ["Hábunga", "Goðabunga", "Austmannsbunga", "Mýrdalsjökull"], 24, 22, "start"],
    ["Borgarfjörður", ["Borgarnes", "Hvalfjörður"], -22, -18, "end"],
    ["Hengill", ["Hestfjall", "Hengill", "Ölkelduháls", "Hveragerði"], 18, -26, "start"]
  ];

  function P(lon, lat) { return [PJ.x0 + (lon - PJ.lon0) * PJ.s * PJ.c, PJ.y0 + (PJ.lat0 - lat) * PJ.s]; }
  var LC = P(LENS.lon, LENS.lat);
  function LP(lon, lat) { var p = P(lon, lat); return [LENS.cx + (p[0] - LC[0]) * LENS.k, LENS.cy + (p[1] - LC[1]) * LENS.k]; }
  function inLens(q) { return q.lon < -21.35 && q.lat < 64.25; }

  function el(tag, attrs, parent, text) {
    var e = document.createElementNS(NS, tag);
    for (var k in attrs) if (attrs.hasOwnProperty(k)) e.setAttribute(k, attrs[k]);
    if (text !== undefined && text !== null) e.textContent = text;
    if (parent) parent.appendChild(e);
    return e;
  }
  function f1(v) { return v.toFixed(1); }
  function line(pts) { return "M" + pts.map(function (p) { return f1(p[0]) + " " + f1(p[1]); }).join("L"); }

  // Colour by age: white-hot when fresh, amber after six hours, ember at two days.
  var HEAT = [[0, [255, 246, 228]], [6, [255, 214, 150]], [18, [255, 160, 76]], [48, [214, 74, 40]]];
  function heat(h) {
    for (var i = 1; i < HEAT.length; i++) {
      if (h <= HEAT[i][0]) {
        var a = HEAT[i - 1], b = HEAT[i], t = Math.max(0, (h - a[0]) / (b[0] - a[0]));
        return [0, 1, 2].map(function (j) { return Math.round(a[1][j] + (b[1][j] - a[1][j]) * t); });
      }
    }
    return HEAT[HEAT.length - 1][1];
  }
  function rgb(c, a) { return "rgba(" + c[0] + "," + c[1] + "," + c[2] + "," + (a === undefined ? 1 : a.toFixed(3)) + ")"; }
  function coreR(m) { return 2.8 + 3.2 * Math.pow(Math.max(m, 0.1), 1.2); }
  function alpha(h) { return Math.max(0.16, 1 - Math.pow(Math.max(h, 0) / 48, 0.7) * 0.84); }
  function pad2(n) { return (n < 10 ? "0" : "") + n; }
  function utcHm(ms) { var d = new Date(ms); return pad2(d.getUTCHours()) + ":" + pad2(d.getUTCMinutes()); }
  function ago(h) { return h < 1 ? Math.max(0, Math.round(h * 60)) + " min ago" : Math.round(h) + " h ago"; }

  // ---------- Layer 1: drawn once ----------
  function defs(svg) {
    var d = el("defs", {}, svg), g;
    g = el("radialGradient", { id: "ice-room", cx: "22%", cy: "16%", r: "75%" }, d);
    el("stop", { offset: 0, "stop-color": "#E6EAF1", "stop-opacity": 0.09 }, g);
    el("stop", { offset: 0.7, "stop-color": "#E6EAF1", "stop-opacity": 0 }, g);
    g = el("linearGradient", { id: "ice-land", x1: 0, y1: 0, x2: 0, y2: 1 }, d);
    el("stop", { offset: 0, "stop-color": "#14181C" }, g);
    el("stop", { offset: 1, "stop-color": "#0B0D10" }, g);
    g = el("filter", { id: "ice-soft", x: "-20%", y: "-20%", width: "140%", height: "140%" }, d);
    el("feGaussianBlur", { stdDeviation: 14 }, g);
    return d;
  }

  function drawBase(svg) {
    defs(svg);
    el("rect", { x: 0, y: 0, width: 1920, height: 1080, fill: "#000" }, svg);
    el("rect", { x: 0, y: 0, width: 1920, height: 1080, fill: "url(#ice-room)" }, svg);

    // The shelf: the coast echoed outward like depth lines.
    var shelf = el("g", { fill: "none", stroke: "#E6EAF1", "stroke-linejoin": "round" }, svg);
    [[90, 0.012], [54, 0.018], [28, 0.026], [12, 0.04]].forEach(function (w) {
      el("path", { d: MAP.coast, "stroke-width": w[0], "stroke-opacity": w[1] }, shelf);
    });
    el("path", { d: MAP.coast, fill: "url(#ice-land)", stroke: "#3A3F46", "stroke-width": 1.3, "stroke-linejoin": "round" }, svg);
    el("path", { d: MAP.glac, fill: "#E6EAF1", "fill-opacity": 0.055, stroke: "#E6EAF1", "stroke-opacity": 0.16, "stroke-width": 1 }, svg);

    // The seam, where the plates part (static, so its blur is drawn once).
    var seam = el("g", { fill: "none", "stroke-linecap": "round", "stroke-linejoin": "round" }, svg);
    ZONES.forEach(function (z) {
      var d = line(z.map(function (p) { return P(p[0], p[1]); }));
      el("path", { d: d, stroke: "#FFB25C", "stroke-opacity": 0.07, "stroke-width": 46, filter: "url(#ice-soft)" }, seam);
      el("path", { d: d, stroke: "#FFB25C", "stroke-opacity": 0.22, "stroke-width": 1, "stroke-dasharray": "2 7" }, seam);
    });
    var sp = P(-17.15, 65.25);
    el("text", { x: sp[0] + 18, y: sp[1], "class": "lbl", "font-size": 13, fill: "#8E6A48" }, svg, "WHERE THE PLATES PART");

    PLACES.forEach(function (p) {
      var xy = P(p[1], p[2]), right = p[3] === "r";
      el("circle", { cx: f1(xy[0]), cy: f1(xy[1]), r: 2.2, fill: "#6E7580" }, svg);
      el("text", { x: f1(right ? xy[0] + 9 : xy[0] - 9), y: f1(xy[1] + 5), "class": "place", "font-size": 15,
        "text-anchor": right ? "start" : "end" }, svg, p[0]);
    });

    // The Reykjanes lens: its frame and map; its quakes go in layer 2.
    var mr = LENS.r / LENS.k, dx = LC[0] - LENS.cx, dy = LC[1] - LENS.cy;
    var dist = Math.sqrt(dx * dx + dy * dy), ang = Math.atan2(dy, dx), off = Math.asin((LENS.r - mr) / dist);
    el("circle", { cx: f1(LC[0]), cy: f1(LC[1]), r: f1(mr), fill: "none", stroke: "#E6EAF1", "stroke-opacity": 0.28,
      "stroke-width": 1, "stroke-dasharray": "3 5" }, svg);
    [1, -1].forEach(function (sg) {
      var a = ang + sg * (Math.PI / 2 - off);
      el("line", { x1: f1(LENS.cx + LENS.r * Math.cos(a)), y1: f1(LENS.cy + LENS.r * Math.sin(a)),
        x2: f1(LC[0] + mr * Math.cos(a)), y2: f1(LC[1] + mr * Math.sin(a)), stroke: "#E6EAF1", "stroke-opacity": 0.12, "stroke-width": 1 }, svg);
    });
    el("circle", { cx: LENS.cx, cy: LENS.cy, r: LENS.r + 10, fill: "none", stroke: "#E6EAF1", "stroke-opacity": 0.05, "stroke-width": 18 }, svg);
    el("circle", { cx: LENS.cx, cy: LENS.cy, r: LENS.r, fill: "#030405" }, svg);
    var clip = el("clipPath", { id: "ice-lens" }, svg.querySelector("defs"));
    el("circle", { cx: LENS.cx, cy: LENS.cy, r: LENS.r }, clip);
    var lens = el("g", { "clip-path": "url(#ice-lens)" }, svg);
    var tf = "translate(" + LENS.cx + " " + LENS.cy + ") scale(" + LENS.k + ") translate(" + f1(-LC[0]) + " " + f1(-LC[1]) + ")";
    el("path", { d: MAP.coastFine, transform: tf, fill: "url(#ice-land)", stroke: "#4A5058", "stroke-width": (1.2 / LENS.k).toFixed(2),
      "stroke-linejoin": "round" }, lens);
    el("path", { d: line(ZONES[0].map(function (p) { return P(p[0], p[1]); })), transform: tf, fill: "none", stroke: "#FFB25C",
      "stroke-opacity": 0.08, "stroke-width": f1(30 / LENS.k), filter: "url(#ice-soft)" }, lens);
    var lo, la, a1, a2;
    for (lo = -23; lo <= -21.5; lo += 0.5) {
      a1 = LP(lo, 63.6); a2 = LP(lo, 64.2);
      el("line", { x1: f1(a1[0]), y1: f1(a1[1]), x2: f1(a2[0]), y2: f1(a2[1]), stroke: "#E6EAF1", "stroke-opacity": 0.04 }, lens);
    }
    for (la = 63.7; la <= 64.11; la += 0.1) {
      a1 = LP(-23.2, la); a2 = LP(-21.4, la);
      el("line", { x1: f1(a1[0]), y1: f1(a1[1]), x2: f1(a2[0]), y2: f1(a2[1]), stroke: "#E6EAF1", "stroke-opacity": 0.04 }, lens);
    }
    LENS_PLACES.forEach(function (p) {
      var xy = LP(p[1], p[2]);
      if (p[3]) el("circle", { cx: f1(xy[0]), cy: f1(xy[1]), r: 2.4, fill: "#6E7580" }, lens);
      el("text", { x: f1(xy[0] + 8), y: f1(xy[1] - 8), "class": "place", "font-size": 15 }, lens, p[0]);
    });
    el("text", { x: LENS.cx - LENS.r + 6, y: LENS.cy - LENS.r - 34, "class": "lbl", "font-size": 17 }, svg, "REYKJANES");

    // Left column, the ribbon's axis, the legend and the map credit.
    var X = 112;
    el("text", { x: X + 24, y: 135, "class": "lbl", "font-size": 18 }, svg, "ICELAND · NOW");
    el("text", { x: X, y: 334, "class": "read", "font-size": 28, fill: "#C9CED6" }, svg, "earthquakes in the last 48 hours");

    var R = RIBBON;
    el("line", { x1: R.x0, y1: R.base, x2: R.x1, y2: R.base, stroke: "#34383E", "stroke-width": 1 }, svg);
    el("text", { x: R.x1, y: R.base + 26, "class": "read", "font-size": 14, "text-anchor": "end" }, svg, "now");
    el("text", { x: R.x0, y: R.base + 26, "class": "read", "font-size": 14 }, svg, "48 h ago");
    el("text", { x: X, y: R.base + 2, "class": "lbl", "font-size": 13 }, svg, "LAST 48 HOURS");
    el("text", { x: X, y: R.base + 24, "class": "read", "font-size": 14, fill: "#6E7580" }, svg, "taller = stronger");
    el("text", { x: R.x1 - 60, y: R.base + 26, "class": "read", "font-size": 13, "text-anchor": "end", fill: "#4E545C" }, svg,
      "Coast: Landmælingar Íslands via geoBoundaries, CC BY 4.0 · Glaciers: Natural Earth");

    var gx = 1824 - 330;
    el("text", { x: gx - 16, y: 60, "class": "read", "font-size": 14, "text-anchor": "end", fill: "#6E7580" }, svg, "magnitude");
    [0.5, 1.5, 2.5].forEach(function (m) {
      var r = coreR(m);
      el("circle", { cx: f1(gx), cy: 55, r: f1(r), fill: rgb([255, 214, 150]) }, svg);
      el("text", { x: f1(gx + r + 6), y: 60, "class": "num", "font-size": 14, fill: "#8E959F" }, svg, m.toFixed(1));
      gx += r * 2 + 44;
    });
    el("text", { x: f1(gx + 6), y: 60, "class": "read", "font-size": 14, fill: "#6E7580" }, svg, "fresh");
    gx += 50;
    [0, 12, 24, 36, 47].forEach(function (h, i) {
      el("rect", { x: f1(gx + i * 14), y: 50, width: 14, height: 8, fill: rgb(heat(h), alpha(h)) }, svg);
    });
    el("text", { x: f1(gx + 76), y: 60, "class": "read", "font-size": 14, fill: "#6E7580" }, svg, "2 days");
  }

  // ---------- Layer 2: from each list ----------
  // m: the motion layer's box for these quakes ({box, ox, oy}); the halo of
  // one of the newest BREATHE/2 under 6 h goes there to breathe, else into the SVG.
  function drawQuakes(parent, list, now, proj, scale, glows, m) {
    var g = el("g", {}, parent);
    // Oldest first so the fresh ones sit on top; only the newest `glows` get a halo.
    for (var i = list.length - 1; i >= 0; i--) {
      var q = list[i], h = (now - q.t) / HOUR, c = heat(h), a = alpha(h), r = coreR(q.m) * scale, xy = proj(q.lon, q.lat);
      var x = f1(xy[0]), y = f1(xy[1]);
      if (i < glows && h < 6 && i < BREATHE / 2) breathe(m, xy[0], xy[1], r * 9, heat(3), a * 0.95);
      else if (i < glows) el("circle", { cx: x, cy: y, r: f1(r * 9), fill: "url(#ice-glow" + Math.min(7, Math.floor(Math.max(h, 0) / 6)) + ")",
        opacity: (a * 0.95).toFixed(3) }, g);
      el("circle", { cx: x, cy: y, r: f1(r), fill: rgb(c, a) }, g);
      el("circle", { cx: x, cy: y, r: f1(r * 0.45), fill: rgb([255, 252, 245], a * 0.9) }, g);
    }
  }

  function glowDefs(svg) {
    var d = el("defs", {}, svg);
    for (var b = 0; b < 8; b++) {
      var c = heat(b * 6 + 3), g = el("radialGradient", { id: "ice-glow" + b }, d);
      [[0, 0.9], [0.16, 0.45], [0.45, 0.1], [1, 0]].forEach(function (s) {
        el("stop", { offset: s[0], "stop-color": "rgb(" + c.join(",") + ")", "stop-opacity": s[1] }, g);
      });
    }
    var clip = el("clipPath", { id: "ice-lens2" }, d);
    el("circle", { cx: LENS.cx, cy: LENS.cy, r: LENS.r }, clip);
  }

  function drawRibbon(svg, list, now) {
    var R = RIBBON, from = now - 48 * HOUR;
    function X(t) { return R.x1 - (now - t) / (48 * HOUR) * (R.x1 - R.x0); }
    var d = new Date(now), mid = Date.UTC(d.getUTCFullYear(), d.getUTCMonth(), d.getUTCDate());
    for (var s = mid; s > from - DAY; s -= DAY) {
      if (s > from && s < now) el("line", { x1: f1(X(s)), y1: R.base - 46, x2: f1(X(s)), y2: R.base + 6, stroke: "#34383E", "stroke-dasharray": "2 4" }, svg);
      var a = Math.max(s, from), b = Math.min(s + DAY, now), sd = new Date(s);
      if (b - a > 3 * HOUR) el("text", { x: f1(X(a) + 8), y: R.base - 36, "class": "read", "font-size": 13, fill: "#6E7580" }, svg,
        DAYS[sd.getUTCDay()] + " " + sd.getUTCDate());
    }
    list.forEach(function (q) {
      var h = (now - q.t) / HOUR;
      if (h > 48 || h < 0) return;
      var x = f1(X(q.t)), len = 6 + Math.max(q.m, 0) * 16;
      el("line", { x1: x, y1: R.base, x2: x, y2: f1(R.base - len), stroke: rgb(heat(h), alpha(h)), "stroke-width": 2, "stroke-linecap": "round" }, svg);
    });
  }

  function drawLabels(svg, list) {
    GROUPS.forEach(function (gr) {
      var qs = list.filter(function (q) { return gr[1].indexOf(q.place) >= 0 && !inLens(q); });
      if (!qs.length) return;
      var lon = 0, lat = 0, max = -9;
      qs.forEach(function (q) { lon += q.lon; lat += q.lat; max = Math.max(max, q.m); });
      var xy = P(lon / qs.length, lat / qs.length), x = f1(xy[0] + gr[2]), y = xy[1] + gr[3];
      el("text", { x: x, y: f1(y), "class": "read", "font-size": 17, "text-anchor": gr[4], fill: "#B8BEC7" }, svg, gr[0]);
      el("text", { x: x, y: f1(y + 20), "class": "num", "font-size": 14, "text-anchor": gr[4], fill: "#8E959F" }, svg,
        qs.length + " · max M" + max.toFixed(1));
    });
  }

  function drawHead(svg, list, now) {
    var X = 112;
    el("text", { x: X - 8, y: 286, "class": "mono", "font-size": 180 }, svg, list ? String(list.length) : "–");
    if (!list || !list.length) return;
    var newest = list[0], strongest = list[0];
    list.forEach(function (q) { if (q.m > strongest.m) strongest = q; });
    [["STRONGEST", strongest, strongest.place + " · " + ago((now - strongest.t) / HOUR)],
     ["NEWEST", newest, newest.place + " · " + utcHm(newest.t) + " · " + ago((now - newest.t) / HOUR)]].forEach(function (row, i) {
      var y = 404 + i * 46;
      el("text", { x: X, y: y, "class": "lbl", "font-size": 14 }, svg, row[0]);
      el("text", { x: X + 128, y: y + 1, "class": "num", "font-size": 22 }, svg, "M" + row[1].m.toFixed(1));
      el("text", { x: X + 196, y: y + 1, "class": "read", "font-size": 20 }, svg, row[2]);
    });
  }

  // ---------- Layer 3: motion (HTML, placed once per draw, moved by CSS only) ----------
  function div(cls, x, y, size, parent) {
    var d = document.createElement("div");
    d.className = cls;
    d.style.left = f1(x - size / 2) + "px"; d.style.top = f1(y - size / 2) + "px";
    d.style.width = d.style.height = f1(size) + "px";
    parent.appendChild(d);
    return d;
  }

  // A halo that breathes: the outer box holds its age's opacity, the inner one breathes.
  function breathe(m, x, y, r, c, a) {
    var o = div("halo", x - m.ox, y - m.oy, r * 2, m.box), s = "rgba(" + c.join(",") + ",";
    o.style.opacity = a.toFixed(3);
    var i = document.createElement("div");
    i.className = "breathe";
    i.style.backgroundImage = "radial-gradient(circle closest-side, " + s + "0.9) 0%, " + s + "0.45) 16%, " + s + "0.1) 45%, " + s + "0) 100%)";
    o.appendChild(i);
  }

  function ripple(m, x, y, r) {
    ["r1", "r2", "r3"].forEach(function (c) { div("ripple " + c, x - m.ox, y - m.oy, r * 2, m.box); });
  }

  var base = null, layer = null, motion = null, planes = null;

  function build(baseSvg, quakeSvg, motionBox, flightSvg) {
    base = baseSvg; layer = quakeSvg; motion = motionBox; planes = flightSvg;
    drawBase(base);
  }

  // ---------- Aircraft (own SVG on top, redrawn from each flight reply) ----------
  // Cool and small beside the warm quakes: a trail of the last fixes and an
  // arrow on the newest, pointing along the track. Only over the map's side
  // of the screen (the left column keeps its text); not in the lens.
  function drawFlights(st, now) {
    if (!planes) return;
    while (planes.firstChild) planes.removeChild(planes.firstChild);
    var clip = el("clipPath", { id: "ice-sky" }, el("defs", {}, planes));
    el("rect", { x: 580, y: 130, width: 1340, height: 856 }, clip);   // under the source lines, above the ribbon
    var g = el("g", { "clip-path": "url(#ice-sky)" }, planes), trails = (st && st.trails) || {};
    for (var id in trails) {
      if (!Object.prototype.hasOwnProperty.call(trails, id)) continue;
      var tr = trails[id], pts = [];
      for (var i = 0; i < tr.length; i++) { var p = P(tr[i].lon, tr[i].lat); pts.push(f1(p[0]) + "," + f1(p[1])); }
      if (pts.length > 1) el("polyline", { points: pts.join(" "), fill: "none", stroke: "#7F9BB8", "stroke-width": 1.5,
        "stroke-opacity": 0.4, "stroke-linecap": "round", "stroke-linejoin": "round" }, g);
      var last = tr[tr.length - 1], xy = P(last.lon, last.lat);
      el("path", { d: "M0,-9 L5.5,6 L0,3 L-5.5,6 Z", fill: "#CFE0F2", "fill-opacity": 0.85,
        transform: "translate(" + f1(xy[0]) + "," + f1(xy[1]) + ") rotate(" + Math.round(last.track) + ")" }, g);
    }
    el("text", { x: 1824, y: 116, "class": "read", "font-size": 15, "text-anchor": "end", fill: st && st.down ? "#8E959F" : "#6E7580" }, planes,
      L.flightSource(st));
  }

  // st: the feed state from L.isleStep ({ quakes, goodAt, down }), or null
  // before the first reply. Redraws layers 2 and 3; the base stays.
  function draw(st, now) {
    if (!layer) return;
    while (layer.firstChild) layer.removeChild(layer.firstChild);
    while (motion.firstChild) motion.removeChild(motion.firstChild);
    glowDefs(layer);
    var list = (st && st.quakes) || [], down = !!(st && st.down);
    var mMap = { box: motion, ox: 0, oy: 0 };
    var lensBox = div("lensclip", LENS.cx, LENS.cy, LENS.r * 2, motion);
    var mLens = { box: lensBox, ox: LENS.cx - LENS.r, oy: LENS.cy - LENS.r };
    div(down ? "dot down" : "dot live", 118, 128, 12, motion);
    drawQuakes(layer, list, now, P, 1, GLOWS / 2, mMap);
    drawLabels(layer, list);
    var lensList = list.filter(inLens), lens = el("g", { "clip-path": "url(#ice-lens2)" }, layer);
    drawQuakes(lens, lensList, now, LP, 1.55, GLOWS / 2, mLens);
    var newest = list[0];
    if (newest && now - newest.t < 48 * HOUR) {
      var xy = P(newest.lon, newest.lat);
      ripple(mMap, xy[0], xy[1], 9);
      if (inLens(newest)) { xy = LP(newest.lon, newest.lat); ripple(mLens, xy[0], xy[1], 12); }
    }
    el("circle", { cx: LENS.cx, cy: LENS.cy, r: LENS.r, fill: "none", stroke: "#4A5058", "stroke-width": 1.2 }, layer);
    el("text", { x: LENS.cx - LENS.r + 6, y: LENS.cy - LENS.r - 10, "class": "read", "font-size": 17 }, layer,
      lensList.length + " of " + list.length + " quakes · drawn " + LENS.k + "× larger");
    drawHead(layer, st && st.quakes, now);
    drawRibbon(layer, list, now);
    el("text", { x: 1824, y: 92, "class": "read", "font-size": 15, "text-anchor": "end", fill: down ? "#8E959F" : "#6E7580" }, layer,
      L.isleSource(st));
  }

  root.ImpetusIceland = { build: build, draw: draw, drawFlights: drawFlights, heat: heat, project: P };
})(window);

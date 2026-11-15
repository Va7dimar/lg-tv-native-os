// The overhead room (issue #23): the sky over home as a chart seen from
// below, with the ISS, the newest Starlink trains and the planes passing now,
// and the ISS's next visible pass. Its door in the control room carries the
// note when a pass can be seen within 12 hours. Rules: DESIGN.md, "Overhead".
// Every feed goes through the helper (`sky ...`); a feed that fails leaves a
// quiet "feed down" in the source line, never a box or a spinner, and
// nothing here holds up the other rooms. Chromium 79: ES5 only.
(function () {
  "use strict";
  var K = window.ImpetusSky, L = window.ImpetusLogic, CFG = window.IMPETUS_CONFIG || {};
  var $ = function (id) { return document.getElementById(id); };
  var NS = "http://www.w3.org/2000/svg";
  var CX = 1330, CY = 540, R = 440;              // the dome on the 1920x1080 frame
  var MOVE_EVERY = 2000;                        // positions, while the room is open
  var PLANES_EVERY = 30000;                     // the planes feed, while the room is open
  var ORBITS_EVERY = 10 * 60000, ORBITS_SOON = 2 * 60000;
  var PASS_EVERY = 30 * 60000, PASS_HOURS = 48;
  var PLANES_STALE = 3 * 60000;                 // a plane not heard from for this long is dropped
  var PLANE_ROWS = 3, PLANE_MARKS = 12;

  var ctl = null, open = false;
  var place = null;                             // the TV's home position, null = the placeholder
  var iss = null, issL1 = "", sats = [], orbitsFeed = null, orbitsTimer = null;
  var pass = null, passAt = 0, passWhere = "";
  var planes = [], planesSt = { goodAt: 0, down: false }, planesBusy = false;
  var moveTimer = null, planesTimer = null;

  function noop() {}
  function home() { return place || (CFG.sky && CFG.sky.place) || K.PLACEHOLDER; }
  function whereKey() { var p = home(); return p.lat + "," + p.lon; }

  // ---------- asking the helper ----------

  function askPlace() {
    return ctl(["sky", "place"]).then(function (text) {
      place = K.readPlace(L.parseKv(text));
    }, noop);
  }

  // The helper answers from its copy at once and fetches in the background
  // when that copy is old; an answer that is not fresh is asked again soon.
  function askOrbits() {
    clearTimeout(orbitsTimer);
    return ctl(["sky", "orbits"]).then(function (text) {
      var s = L.parseSections(text);
      var fi = K.parseFeed(s.iss), ft = K.parseFeed(s.trains);
      orbitsFeed = fi;
      var list = K.withOrbits(K.parseTle(fi.body));
      if (list.length && list[0].l1 !== issL1) { iss = list[0]; issL1 = iss.l1; pass = null; }
      if (ft.kind !== "none") sats = K.withOrbits(K.parseTle(ft.body));
      return fi.kind === "fresh" && ft.kind === "fresh";
    }, function () { return false; }).then(function (fresh) {
      orbitsTimer = setTimeout(askOrbits, fresh ? ORBITS_EVERY : ORBITS_SOON);
      notePass();
      if (open) draw();
    });
  }

  function askPlanes() {
    if (planesBusy) return;
    planesBusy = true;
    ctl(["sky", "planes", "at=" + K.placeAt(home())]).then(function (text) {
      var f = K.parseFeed(text), list = f.kind === "none" ? null : K.parsePlanes(f.body, home());
      if (list) { planes = list; planesSt.goodAt = Date.now() - f.age * 1000; }
      planesSt.down = !list || f.kind !== "fresh";
    }, function () { planesSt.down = true; }).then(function () {
      planesBusy = false;
      if (Date.now() - planesSt.goodAt > PLANES_STALE) planes = [];
      if (open) draw();
    });
  }

  // ---------- the next visible pass, and the door's note ----------

  function notePass() {
    var now = Date.now();
    if (iss && (!pass || passWhere !== whereKey() || now - passAt > PASS_EVERY ||
        (pass.visible && pass.visible.end < now))) {
      pass = K.nextVisible(iss.rec, home(), now, PASS_HOURS);
      passAt = now;
      passWhere = whereKey();
    }
    var note = K.passNote(pass, now);
    $("skynote").textContent = note || "";
    $("skydoor").classList.toggle("noted", !!note);
  }

  // ---------- drawing ----------

  function svg(tag, attrs, parent) {
    var e = document.createElementNS(NS, tag);
    for (var k in attrs) if (attrs.hasOwnProperty(k)) e.setAttribute(k, attrs[k]);
    if (parent) parent.appendChild(e);
    return e;
  }

  // n children of one kind in a group, made once and reused.
  function pool(g, n, tag, cls) {
    while (g.childNodes.length < n) svg(tag, { "class": cls }, g);
    for (var i = 0; i < g.childNodes.length; i++) g.childNodes[i].style.display = i < n ? "" : "none";
    return g.childNodes;
  }

  function xy(az, el) { return K.domeXY(az, el, CX, CY, R); }

  function line(points) {
    var d = "";
    points.forEach(function (q) { var p = xy(q.az, q.el); d += (d ? " L" : "M") + p.x.toFixed(1) + " " + p.y.toFixed(1); });
    return d;
  }

  function text(id, s) { $(id).textContent = s || ""; }

  function drawIss(now, p) {
    var at = iss && K.look(iss.rec, now, p), dot = $("issdot"), glow = $("issglow");
    var paths = pool($("passpath"), 3, "path", "");
    paths[0].setAttribute("class", "whole"); paths[1].setAttribute("class", "seen"); paths[2].setAttribute("class", "travelled");
    var showPass = null;
    if (!at) {
      text("issnow", iss ? "NO POSITION" : "NO ORBIT YET");
      text("isswhere", "");
      dot.style.display = glow.style.display = "none";
    } else if (at.el > 0) {
      var xyNow = xy(at.az, at.el);
      text("issnow", "UP NOW · " + Math.round(at.el) + "° HIGH · " + K.compass(at.az));
      text("isswhere", L.formatClock(new Date(now)) + " · " + Math.round(at.km).toLocaleString("en-US") + " km away · " +
        (at.sunlit ? "in sunlight" : "in the earth's shadow"));
      dot.setAttribute("cx", xyNow.x); dot.setAttribute("cy", xyNow.y);
      glow.setAttribute("cx", xyNow.x); glow.setAttribute("cy", xyNow.y);
      dot.style.display = glow.style.display = "";
      glow.style.opacity = at.sunlit ? 1 : 0.35;
      // The pass in progress: its whole path, and the part already travelled.
      var cur = K.passes(iss.rec, p, now - 20 * 60000, 2 / 3, 15).filter(function (q) { return q.rise <= now && q.set >= now; })[0];
      if (cur) {
        showPass = cur;
        paths[2].setAttribute("d", line(cur.path.filter(function (q) { return q.t <= now; }).concat([{ az: at.az, el: at.el }])));
      }
    } else {
      text("issnow", "BELOW THE HORIZON");
      text("isswhere", "over " + Math.abs(at.lat).toFixed(1) + "° " + (at.lat < 0 ? "S" : "N") + " " +
        Math.abs(at.lon).toFixed(1) + "° " + (at.lon < 0 ? "W" : "E") + " · " + Math.round(at.alt) + " km up");
      dot.style.display = glow.style.display = "none";
      showPass = pass;
    }
    paths[2].style.display = at && at.el > 0 && showPass ? "" : "none";
    // The pass on the chart: its whole path faint, the part that can be seen in green.
    var v = showPass && showPass.visible;
    paths[0].setAttribute("d", showPass ? line(showPass.path) : "");
    paths[1].setAttribute("d", v ? line(showPass.path.filter(function (q) { return q.t >= v.start && q.t <= v.end; })) : "");
    var mark = $("passmark"), label = $("passmarklabel");
    if (v && !(at && at.el > 0)) {
      var first = showPass.path.filter(function (q) { return q.t >= v.start; })[0], m = xy(first.az, first.el);
      mark.setAttribute("cx", m.x); mark.setAttribute("cy", m.y);
      label.setAttribute("x", m.x + (m.x > CX ? 16 : -16)); label.setAttribute("y", m.y - 14);
      label.setAttribute("text-anchor", m.x > CX ? "start" : "end");
      label.textContent = L.formatClock(new Date(v.start));
      mark.style.display = label.style.display = "";
    } else {
      mark.style.display = label.style.display = "none";
    }
  }

  function drawPass(now) {
    var v = pass && pass.visible;
    if (v && now >= v.start && now <= v.end) {
      text("passtime", "NOW"); text("passday", "");
      text("passline", K.passLine(v));
    } else if (v) {
      text("passtime", L.formatClock(new Date(v.start)));
      text("passday", K.passDay(v.start, now));
      text("passline", K.passLine(v));
    } else {
      text("passtime", ""); text("passday", "");
      text("passline", iss ? "None in the next 2 days. From up here the ISS keeps low in the south." : "");
    }
  }

  function drawSats(now, p) {
    var up = [];
    sats.forEach(function (s) {
      var at = K.look(s.rec, now, p);
      if (at && at.el > 0) { at.launch = s.launch; at.num = s.num; up.push(at); }
    });
    var dots = pool($("satdots"), up.length, "circle", "sat");
    up.forEach(function (q, i) {
      var m = xy(q.az, q.el);
      dots[i].setAttribute("cx", m.x.toFixed(1)); dots[i].setAttribute("cy", m.y.toFixed(1));
      dots[i].setAttribute("r", q.sunlit ? 3 : 2.2);
      dots[i].setAttribute("class", q.sunlit ? "sat lit" : "sat");
    });
    var runs = K.trains(up), lines = pool($("trainlines"), runs.length, "path", "train");
    runs.forEach(function (run, i) { lines[i].setAttribute("d", line(run)); });
    var lit = up.filter(function (q) { return q.sunlit; }).length;
    text("trainline", sats.length ? up.length + " above the horizon · " + lit + " in sunlight" : "No elements yet.");
  }

  function drawPlanes(p) {
    var marks = pool($("planemarks"), Math.min(planes.length, PLANE_MARKS), "g", "plane");
    planes.slice(0, PLANE_MARKS).forEach(function (q, i) {
      var g = marks[i];
      if (!g.firstChild) {
        svg("path", { d: "M0 -11 L7 8 L0 4 L-7 8 Z" }, g);
        svg("text", { x: 14, y: 5 }, g);
      }
      var m = xy(q.az, q.el);
      // East is to the left on this chart, so a heading turns the other way.
      var turn = q.track === null ? 0 : -q.track;
      g.firstChild.setAttribute("transform", "rotate(" + turn.toFixed(0) + ")");
      g.setAttribute("transform", "translate(" + m.x.toFixed(1) + " " + m.y.toFixed(1) + ")");
      g.lastChild.textContent = i < PLANE_ROWS ? q.call : "";
    });
    var ol = $("planelist");
    ol.innerHTML = "";
    if (!planes.length) {
      var none = document.createElement("li");
      none.className = "none";
      none.textContent = planesSt.goodAt ? "None within 100 km." : "";
      ol.appendChild(none);
    }
    planes.slice(0, PLANE_ROWS).forEach(function (q) {
      var li = document.createElement("li"), c = document.createElement("span"), d = document.createElement("span");
      c.className = "call"; c.textContent = q.call;
      d.className = "n"; d.textContent = K.planeLine(q);
      li.appendChild(c); li.appendChild(d);
      ol.appendChild(li);
    });
    text("planecount", planes.length > PLANE_ROWS ? planes.length + " within 100 km" : "");
  }

  function draw() {
    var now = Date.now(), p = home();
    notePass();
    text("skyfrom", place ? "FROM HOME" : "FROM CENTRAL REYKJAVÍK · SET HOME ON THE PHONE");
    drawIss(now, p);
    drawPass(now);
    drawSats(now, p);
    drawPlanes(p);
    text("orbitsline", K.orbitsLine(orbitsFeed));
    text("planesline", K.planesLine(planesSt));
  }

  // ---------- the room ----------

  function enter() {
    open = true;
    draw();
    // The phone may have set a new home since: asked again on every visit.
    askPlace().then(function () { draw(); askPlanes(); askOrbits(); });
    clearInterval(moveTimer); clearInterval(planesTimer);
    moveTimer = setInterval(draw, MOVE_EVERY);
    planesTimer = setInterval(askPlanes, PLANES_EVERY);
  }

  function leave() {
    open = false;
    clearInterval(moveTimer); clearInterval(planesTimer);
  }

  // From home.js once the helper answered the probe: elements for the
  // door's note, kept fresh in the background.
  function start(ctlFn) {
    ctl = ctlFn;
    askPlace().then(askOrbits);
    setInterval(notePass, 60000);
  }

  window.ImpetusOverhead = { start: start, enter: enter, leave: leave };
})();

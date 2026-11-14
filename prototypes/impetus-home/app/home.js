// Impetus Home controller: the living room, the control room and the turn
// between them. Rules: DESIGN.md. Chromium 79: ES5 only.
(function () {
  "use strict";
  var L = window.ImpetusLogic, LUNA = window.ImpetusLuna, CFG = window.IMPETUS_CONFIG;
  var $ = function (id) { return document.getElementById(id); };
  var SVGNS = "http://www.w3.org/2000/svg";

  var HORIZON = 691, ARC_RISE = 330, X0 = -140, X1 = 2060;
  var KEY = { LEFT: 37, UP: 38, RIGHT: 39, DOWN: 40, OK: 13, BACK: 461, BACKSPACE: 8, ESC: 27 };

  var isOpen = false, focusIdx = 0, focusables = [], idleTimer = null, connTimer = null;
  var seen = {}, hosts = {}, resolving = {};

  // ---------- Fit: lay out at 1920x1080, scale with zoom (never transform) ----------
  function fit() {
    var z = Math.min(window.innerWidth / 1920, window.innerHeight / 1080);
    document.body.style.zoom = z;
  }

  // ---------- Room 1: the living room ----------
  function pathFor(day, from, to) {
    var span = day.set - day.rise, d = "";
    for (var t = from; t <= to + 1; t += 5 * 60000) {
      var tt = Math.min(t, to);
      var x = X0 + (tt - day.rise) / span * (X1 - X0);
      var y = HORIZON - (L.sunAltitude(tt) + 0.833) / (day.peakAlt + 0.833) * ARC_RISE;
      d += (d ? " L" : "M") + x.toFixed(1) + " " + y.toFixed(1);
      if (tt === to) break;
    }
    return d;
  }

  function hm(ms) { return L.formatClock(new Date(ms)); }

  function drawLiving() {
    var now = new Date(), t = now.getTime();
    $("clock").textContent = L.formatClock(now);
    $("date").textContent = L.formatDate(now);

    var day = L.sunDay(now);
    var sun = $("sun"), glow = $("glow");
    if (day.rise === null || day.set === null) {
      $("arc").setAttribute("d", ""); $("travelled").setAttribute("d", "");
      sun.style.display = "none"; glow.style.display = "none";
      $("sunline").textContent = "";
      return;
    }
    $("arc").setAttribute("d", pathFor(day, day.rise, day.set));
    var x, y;
    if (t >= day.rise && t <= day.set) {
      $("travelled").setAttribute("d", pathFor(day, day.rise, t));
      x = X0 + (t - day.rise) / (day.set - day.rise) * (X1 - X0);
      y = HORIZON - (L.sunAltitude(t) + 0.833) / (day.peakAlt + 0.833) * ARC_RISE;
      sun.style.display = ""; glow.style.opacity = 1;
    } else {
      // Night: the point sinks under the line, a dim glow spills over it
      // on the side where the sun went down or will come up.
      $("travelled").setAttribute("d", t > day.set ? pathFor(day, day.rise, day.set) : "");
      x = t > day.set ? 1700 : 220;
      y = HORIZON + 12;
      sun.style.display = "none"; glow.style.opacity = 0.7;
    }
    sun.setAttribute("cx", x); sun.setAttribute("cy", y);
    glow.setAttribute("cx", x); glow.setAttribute("cy", y);
    glow.style.display = "";

    var sl = $("sunline");
    sl.innerHTML = "";
    function word(s) { sl.appendChild(document.createTextNode(s)); }
    function num(s) { var e = document.createElement("span"); e.className = "n"; e.textContent = s; sl.appendChild(e); }
    function sep() { var e = document.createElement("span"); e.className = "sep"; e.textContent = "·"; sl.appendChild(e); }
    var mins = (day.set - day.rise) / 60000;
    word("sólarupprás "); num(hm(day.rise)); sep();
    word("sólsetur "); num(hm(day.set)); sep();
    num(String(Math.floor(Math.round(mins) / 60))); word(" klst. ");
    num(String(Math.round(mins) % 60)); word(" mín.");
  }

  // ---------- Room 2: the control room ----------
  function key(cls, text, onPress) {
    var b = document.createElement("button");
    b.className = "key " + cls;
    b.setAttribute("data-focus", "");
    if (text) b.textContent = text;
    b._press = onPress;
    return b;
  }

  function renderShortcuts() {
    var box = $("shortcuts");
    box.innerHTML = "";
    (CFG.shortcuts || []).slice(0, 3).forEach(function (s) {
      var b = key("shortcut", s.label, function () { return LUNA.launch(s.id, s.params); });
      var p = document.createElement("span");
      p.className = "place"; p.textContent = s.place || "";
      b.appendChild(p);
      box.appendChild(b);
    });
  }

  function renderApps(apps) {
    var box = $("apps");
    box.innerHTML = "";
    var list = L.pickApps(apps, CFG).slice(0, 12);
    for (var c = 0; c < 2; c++) {
      var col = document.createElement("div");
      col.className = "appcol";
      list.slice(c * 6, c * 6 + 6).forEach(function (a) {
        col.appendChild(key("appbar", a.label.toUpperCase(), function () { return LUNA.launch(a.id); }));
      });
      box.appendChild(col);
    }
    var extra = L.pickApps(apps, CFG).length - list.length;
    var note = $("note");
    note.hidden = extra <= 0;
    note.textContent = extra > 0 ? extra + " fleiri: raðaðu í config.js" : "";
  }

  function collect() {
    focusables = Array.prototype.slice.call(document.querySelectorAll("#control [data-focus]"));
    $("appletv")._press = function () { return LUNA.launch(CFG.appleTv.id); };
  }

  function paintFocus() {
    focusables.forEach(function (el, i) { el.classList.toggle("focused", i === focusIdx); });
  }

  function moveFocus(dir) {
    var rects = focusables.map(function (el) {
      var r = el.getBoundingClientRect();
      return { x: r.left, y: r.top, w: r.width, h: r.height };
    });
    focusIdx = L.nearest(rects, focusIdx, dir);
    paintFocus();
  }

  function press() {
    var el = focusables[focusIdx];
    if (!el || !el._press) return;
    el.classList.add("pressed");
    setTimeout(function () { el.classList.remove("pressed"); }, 140);
    el._press().catch(function (e) { console.log("launch failed", e && (e.errorText || e.message || e)); });
  }

  // ---------- Connections (read only, only while the room is open) ----------
  function refreshConnections() {
    LUNA.connections().then(function (list) {
      var now = Date.now(), live = {};
      list.forEach(function (c) {
        var k = c.prog + "|" + c.ip + "|" + c.port;
        live[k] = true;
        if (!seen[k]) seen[k] = { at: now, c: c, fresh: true };
        if (hosts[c.ip] === undefined && !resolving[c.ip]) {
          resolving[c.ip] = true;
          LUNA.hostOf(c.ip).then(function (h) { hosts[c.ip] = h; }, function () { hosts[c.ip] = null; })
            .then(function () { delete resolving[c.ip]; if (isOpen) drawConnections(); });
        }
      });
      Object.keys(seen).forEach(function (k) { if (!live[k]) delete seen[k]; });
      $("conncount").textContent = String(list.length);
      drawConnections();
    }, function () {
      $("conncount").textContent = "–";
    });
  }

  function drawConnections() {
      var newest = Object.keys(seen).map(function (k) { return seen[k]; })
        .sort(function (a, b) { return b.at - a.at; }).slice(0, 5);
      var ol = $("connlist");
      ol.innerHTML = "";
      newest.forEach(function (s) {
        var li = document.createElement("li");
        var host = hosts[s.c.ip] || s.c.ip;
        li.innerHTML = "";
        var p = document.createElement("span"); p.className = "prog"; p.textContent = s.c.prog;
        var a = document.createElement("span"); a.className = "arrow"; a.textContent = " → ";
        li.appendChild(p); li.appendChild(a); li.appendChild(document.createTextNode(host));
        if (s.fresh) {
          li.className = "fresh";
          s.fresh = false;
          setTimeout(function () { li.className = ""; }, 60);
        }
        ol.appendChild(li);
      });
  }

  // ---------- The turn ----------
  function bumpIdle() {
    clearTimeout(idleTimer);
    idleTimer = setTimeout(function () { setOpen(false); }, (CFG.idleSeconds || 60) * 1000);
  }

  function setOpen(open, instant) {
    if (open === isOpen && !instant) return;
    isOpen = open;
    document.body.classList.toggle("instant", !!instant);
    document.body.classList.toggle("open", open);
    $("control").setAttribute("aria-hidden", open ? "false" : "true");
    clearInterval(connTimer); clearTimeout(idleTimer);
    if (open) {
      focusIdx = 0; paintFocus(); bumpIdle();
      refreshConnections();
      connTimer = setInterval(refreshConnections, (CFG.connectionsEverySeconds || 5) * 1000);
    } else {
      drawLiving();
    }
  }

  function onKey(e) {
    var k = e.keyCode;
    e.preventDefault();
    if (!isOpen) { setOpen(true); return; } // the opening key does nothing else
    bumpIdle();
    if (k === KEY.BACK || k === KEY.BACKSPACE || k === KEY.ESC) setOpen(false);
    else if (k === KEY.LEFT) moveFocus("left");
    else if (k === KEY.RIGHT) moveFocus("right");
    else if (k === KEY.UP) moveFocus("up");
    else if (k === KEY.DOWN) moveFocus("down");
    else if (k === KEY.OK) press();
  }

  // ---------- Start ----------
  fit();
  window.addEventListener("resize", fit);
  document.addEventListener("keydown", onKey);
  // Back from an app (relaunch, or the page shown again): land on the living room.
  document.addEventListener("webOSRelaunch", function () { setOpen(false, true); });
  document.addEventListener("visibilitychange", function () { if (!document.hidden) setOpen(false, true); });

  drawLiving();
  setInterval(function () { if (!isOpen) drawLiving(); }, 60000);
  renderShortcuts();
  LUNA.listApps().then(renderApps, function () {
    $("note").hidden = false; $("note").textContent = "Forritalisti náðist ekki.";
  }).then(function () { collect(); paintFocus(); });
  collect();
})();

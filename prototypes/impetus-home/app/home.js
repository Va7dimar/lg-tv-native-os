// Impetus Home controller: the living room, the control room, the engine
// room, the sleep notice and the turns between them. Rules: DESIGN.md.
// Chromium 79: ES5 only.
(function () {
  "use strict";
  var L = window.ImpetusLogic, LUNA = window.ImpetusLuna, CFG = window.IMPETUS_CONFIG;
  var $ = function (id) { return document.getElementById(id); };

  var HORIZON = 691, ARC_RISE = 330, X0 = -140, X1 = 2060;
  var KEY = { LEFT: 37, UP: 38, RIGHT: 39, DOWN: 40, OK: 13, BACK: 461, BACKSPACE: 8, ESC: 27 };
  var NOTICE_SECONDS = 120;   // the keeper brings the notice up this long before standby
  var TALK_ROWS = 9, LOG_LINES = 14;

  var room = "living";        // living | control | engine | notice
  var focusIdx = 0, focusables = [];
  var idleTimer = null, stateTimer = null, stillTimer = null, engineTimer = null, noticeTimer = null;
  var caps = {}, state = {}, sceneKeys = [];
  var stillBusy = false, liveDead = false;
  var conns = [], hosts = {}, resolving = {};
  var noticeUntil = 0, dismissed = 0, cancelling = false;

  function every(seconds, fallback) { return (seconds || fallback) * 1000; }
  function noop() {}

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
    function num(s) { sl.appendChild(span("n", s)); }
    function sep() { sl.appendChild(span("sep", "·")); }
    var mins = Math.round((day.set - day.rise) / 60000);
    word("sunrise "); num(hm(day.rise)); sep();
    word("sunset "); num(hm(day.set)); sep();
    num(String(Math.floor(mins / 60))); word(" h ");
    num(String(mins % 60)); word(" min");
  }

  // ---------- Building blocks ----------
  function span(cls, text) {
    var e = document.createElement("span");
    e.className = cls;
    e.textContent = text || "";
    return e;
  }

  function key(cls, onPress) {
    var b = document.createElement("button");
    b.className = "key " + cls;
    b.setAttribute("data-focus", "");
    b._press = onPress;
    return b;
  }

  // ---------- Room 2: the control room ----------
  function renderShortcuts() {
    var box = $("shortcuts");
    box.innerHTML = "";
    (CFG.shortcuts || []).slice(0, 3).forEach(function (s) {
      var b = key("shortcut", function () { return LUNA.launch(s.id, s.params); });
      b.appendChild(span("name", s.label));
      b.appendChild(span("place", s.place));
      box.appendChild(b);
    });
  }

  function renderApps(apps) {
    var box = $("apps");
    box.innerHTML = "";
    var all = L.pickApps(apps, CFG), list = all.slice(0, 12);
    for (var c = 0; c < 2; c++) {
      var col = document.createElement("section");
      col.className = "appcol";
      list.slice(c * 6, c * 6 + 6).forEach(function (a) {
        var b = key("appbar", function () { return LUNA.launch(a.id); });
        b.textContent = a.label.toUpperCase();
        col.appendChild(b);
      });
      box.appendChild(col);
    }
    var extra = all.length - list.length;
    $("note").hidden = extra <= 0;
    $("note").textContent = extra > 0 ? extra + " more: order them in config.js" : "";
  }

  function sceneCtx() {
    return { caps: caps, night: L.nightWindow(Date.now()), fallback: CFG.appleTv.id };
  }

  // A scene is drawn only when this TV can do at least one of its parts.
  function renderScenes() {
    var box = $("scenes");
    box.innerHTML = "";
    sceneKeys = [];
    (CFG.scenes || []).forEach(function (scene) {
      if (sceneKeys.length >= 3 || !L.sceneWords(scene, sceneCtx())) return;
      var b = key("scene", function () { return pressScene(scene); });
      var st = span("state", "");
      b.appendChild(span("name", scene.label || scene.id.toUpperCase()));
      b.appendChild(span("does", scene.does));
      b.appendChild(st);
      box.appendChild(b);
      sceneKeys.push({ scene: scene, el: b, state: st });
    });
    $("sceneslabel").hidden = sceneKeys.length === 0;
  }

  // A latched key turns its scene off; any other starts its scene (the
  // helper ends the one that was on first).
  function pressScene(scene) {
    if (state.scene === scene.id) {
      return LUNA.ctl(["scene", "off"]).then(function () {
        state.scene = "";
        paintState();
        return refreshState();
      });
    }
    var words = L.sceneWords(scene, sceneCtx());
    if (!words) return Promise.reject(new Error("scene not available"));
    return LUNA.ctl(["scene", "on"].concat(words)).then(function (out) {
      if (L.parseKv(out).ok !== "1") throw new Error("scene refused: " + out);
      state.scene = scene.id; state.sleep = ""; state.end = ""; state.screenoff = "";
      paintState();
      setTimeout(refreshState, 2000);
    });
  }

  function paintState() {
    sceneKeys.forEach(function (k) {
      var line = L.sceneLine(state, k.scene.id);
      k.el.classList.toggle("latched", line !== null);
      k.state.textContent = line || "";
    });
    $("shieldcount").textContent = L.shieldText(state);
    $("shield").classList.toggle("latched", state.shield === "on");
    $("shieldstate").textContent = L.shieldLine(state);
    $("shielddoes").textContent = "Blocks LG's own ads, tracking and content recognition" +
      (Number(state.hosts) > 0 ? ": " + state.hosts + " hosts." : ".");
  }

  function refreshState() {
    if (!caps.exec) return Promise.resolve();
    return LUNA.ctl(["state"]).then(function (text) {
      state = L.parseKv(text);
      paintState();
      checkNotice();
    }, noop);
  }

  // ---------- The APPLE TV still ----------
  function isDark(img) {
    try {
      var c = document.createElement("canvas");
      c.width = 32; c.height = 18;
      var g = c.getContext("2d");
      g.drawImage(img, 0, 0, 32, 18);
      var d = g.getImageData(0, 0, 32, 18).data, sum = 0;
      for (var i = 0; i < d.length; i += 4) sum += d[i] + d[i + 1] + d[i + 2];
      return sum / (d.length / 4 * 3) < 8;
    } catch (e) { return false; }
  }

  function showStill(s) {
    var img = $("still");
    if (!s) {
      img.hidden = true;
      $("appletv").classList.remove("has-still");
      $("stillage").textContent = "";
      return;
    }
    img.src = s.src;
    img.hidden = false;
    $("appletv").classList.add("has-still");
    $("stillage").textContent = L.stillAge(s.kind, s.age);
  }

  // A live capture first; when it is black (nothing on the video plane while
  // Impetus is in front) the helper is asked for the last still it kept.
  function refreshStill() {
    if (!caps.capture || stillBusy || room !== "control") return;
    stillBusy = true;
    var again = false;
    LUNA.still(liveDead).then(function (s) {
      if (!s || s.kind === "none" || !s.src) { showStill(null); return; }
      return new Promise(function (resolve) {
        var probe = new Image();
        probe.onload = function () {
          if (s.kind === "live" && isDark(probe)) { liveDead = true; again = true; }
          else showStill(s);
          resolve();
        };
        probe.onerror = function () { showStill(null); resolve(); };
        probe.src = s.src;
      });
    }).then(noop, noop).then(function () {
      stillBusy = false;
      if (again) refreshStill();
    });
  }

  // ---------- Room 3: the engine room ----------
  function drawVitals(v) {
    $("temp").textContent = v.tempC === null ? "–" : String(v.tempC);
    $("uptime").textContent = v.uptime || "–";
    $("memtext").textContent = v.mem ? v.mem.text : "–";
    $("membar").style.width = (v.mem ? v.mem.pct : 0) + "%";
    $("disktext").textContent = v.disk ? v.disk.text : "–";
    $("diskbar").style.width = (v.disk ? v.disk.pct : 0) + "%";
  }

  function drawTalkers() {
    var g = L.groupTalkers(conns, hosts), ol = $("talklist");
    $("talktotal").textContent = String(g.total);
    ol.innerHTML = "";
    var max = g.rows.length ? g.rows[0].count : 1;
    g.rows.slice(0, TALK_ROWS).forEach(function (r) {
      var li = document.createElement("li"), bar = span("bar", ""), who = span("who", "");
      bar.style.width = Math.max(2, Math.round(r.count / max * 100)) + "%";
      who.appendChild(document.createTextNode(r.prog));
      who.appendChild(span("arrow", " → "));
      who.appendChild(span("owner", r.owner));
      li.appendChild(bar); li.appendChild(who); li.appendChild(span("num", String(r.count)));
      ol.appendChild(li);
    });
  }

  function drawLog(lines) {
    var ol = $("loglist");
    ol.innerHTML = "";
    lines.slice().reverse().forEach(function (l) {
      var li = document.createElement("li");
      if (l.t) li.appendChild(document.createTextNode(l.t + " "));
      if (l.who) li.appendChild(span("who", l.who + " "));
      li.appendChild(document.createTextNode(l.msg));
      ol.appendChild(li);
    });
  }

  // Names for the far ends, a few new ones per refresh so the TV is not
  // flooded with lookups.
  function resolveHosts() {
    var budget = 4;
    conns.forEach(function (c) {
      if (budget <= 0 || hosts[c.ip] !== undefined || resolving[c.ip]) return;
      budget--;
      resolving[c.ip] = true;
      LUNA.hostOf(c.ip).then(function (h) { hosts[c.ip] = h; }, function () { hosts[c.ip] = null; })
        .then(function () { delete resolving[c.ip]; if (room === "engine") drawTalkers(); });
    });
  }

  function refreshEngine() {
    if (room !== "engine") return Promise.resolve();
    return LUNA.ctl(["engine"]).then(function (text) {
      var s = L.parseSections(text);
      drawVitals(L.parseVitals(L.parseKv(s.vitals)));
      state = L.parseKv(s.state);
      paintState();
      conns = L.parseNetstat(s.talk);
      resolveHosts();
      drawTalkers();
      drawLog(L.filterLog(s.log, LOG_LINES));
    }, noop);
  }

  function pressShield() {
    return LUNA.ctl(["shield", state.shield === "on" ? "off" : "on"]).then(function (out) {
      var kv = L.parseKv(out);
      if (kv.error) console.log("shield:", kv.error);
      return refreshEngine();
    });
  }

  // ---------- The sleep notice ----------
  function showNotice(until) {
    noticeUntil = until;
    setRoom("notice", true);
  }

  function drawNotice() {
    $("countdown").textContent = L.countdown(noticeUntil, Date.now());
    // Standby did not come (or the TV just woke up): back to the living room.
    if (Date.now() / 1000 > noticeUntil + 15) setRoom("living", true);
  }

  // Any key: drop the timer and go back to what was on.
  function cancelNotice() {
    if (cancelling) return;
    cancelling = true;
    dismissed = noticeUntil;
    LUNA.ctl(["sleep", "cancel"]).then(function (text) {
      var prev = L.parseKv(text).prev;
      setRoom("living", true);
      if (L.isSafeId(prev)) return LUNA.launch(prev);
    }).then(noop, noop).then(function () {
      cancelling = false;
      if (room === "notice") setRoom("living", true);
    });
  }

  // The keeper opens Impetus with {notice, until}; if those params are lost
  // on the way, the timer itself says a standby is near.
  function checkNotice() {
    var until = Number(state.sleep);
    if (room === "notice" || !(until > 0) || until === dismissed) return;
    var left = until - Date.now() / 1000;
    if (left > 0 && left <= NOTICE_SECONDS) showNotice(until);
  }

  // ---------- Focus ----------
  function collect() {
    var keep = focusables[focusIdx];
    var sel = room === "engine" ? "#engine [data-focus]" : "#control [data-focus]";
    focusables = Array.prototype.slice.call(document.querySelectorAll(sel))
      .filter(function (el) { return !el.hidden; });
    var i = focusables.indexOf(keep);
    focusIdx = i >= 0 ? i : 0;
  }

  function paintFocus() {
    var old = document.querySelectorAll(".focused");
    for (var i = 0; i < old.length; i++) old[i].classList.remove("focused");
    if ((room === "control" || room === "engine") && focusables[focusIdx]) {
      focusables[focusIdx].classList.add("focused");
    }
  }

  function moveFocus(dir) {
    if (!focusables.length) return;
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
    var p = el._press();
    if (p && p.then) p.then(noop, function (e) { console.log("press failed", e && (e.errorText || e.message || e)); });
  }

  // ---------- The turns ----------
  function bumpIdle() {
    clearTimeout(idleTimer);
    idleTimer = setTimeout(function () { setRoom("living"); }, every(CFG.idleSeconds, 60));
  }

  function setRoom(next, instant) {
    if (next === room && !instant) return;
    var prev = room, b = document.body.classList;
    room = next;
    b.toggle("instant", !!instant);
    b.toggle("open", next === "control");
    b.toggle("deep", next === "engine");
    b.toggle("notice", next === "notice");
    ["control", "engine", "notice"].forEach(function (id) {
      $(id).setAttribute("aria-hidden", next === id ? "false" : "true");
    });
    clearInterval(stateTimer); clearInterval(stillTimer); clearInterval(engineTimer);
    clearInterval(noticeTimer); clearTimeout(idleTimer);
    collect();
    if (next === "control") {
      // Arriving from the living room lands on APPLE TV; coming back out of
      // the engine room lands on its door.
      focusIdx = prev === "engine" ? Math.max(0, focusables.indexOf($("door"))) : 0;
      liveDead = false;
      refreshState(); refreshStill();
      stateTimer = setInterval(refreshState, every(CFG.stateEverySeconds, 5));
      stillTimer = setInterval(refreshStill, every(CFG.stillEverySeconds, 3));
      bumpIdle();
    } else if (next === "engine") {
      focusIdx = 0;
      refreshEngine();
      engineTimer = setInterval(refreshEngine, every(CFG.engineEverySeconds, 5));
      bumpIdle();
    } else if (next === "notice") {
      drawNotice();
      noticeTimer = setInterval(drawNotice, 500);
    } else {
      drawLiving();
    }
    paintFocus();
  }

  function onKey(e) {
    var k = e.keyCode;
    e.preventDefault();
    if (room === "notice") { cancelNotice(); return; }
    if (room === "living") { setRoom("control"); return; } // the opening key does nothing else
    bumpIdle();
    if (k === KEY.BACK || k === KEY.BACKSPACE || k === KEY.ESC) setRoom(room === "engine" ? "control" : "living");
    else if (k === KEY.LEFT) moveFocus("left");
    else if (k === KEY.RIGHT) moveFocus("right");
    else if (k === KEY.UP) moveFocus("up");
    else if (k === KEY.DOWN) moveFocus("down");
    else if (k === KEY.OK) press();
  }

  // Shown again (first launch, relaunch, back from an app): the sleep notice
  // when the keeper asked for it, else the living room.
  function arrive(raw) {
    var p = L.parseLaunchParams(raw), until = Number(p.until);
    if (p.notice === "sleep" && until > Date.now() / 1000 && until !== dismissed) { showNotice(until); return; }
    if (room !== "notice") setRoom("living", true);
    refreshState();
  }

  function launchParams() {
    // PC preview: ?notice=sleep shows the notice, ?room=control|engine opens a room.
    var q = location.search || "";
    if (/[?&]notice=sleep/.test(q)) return { notice: "sleep", until: Math.round(Date.now() / 1000) + NOTICE_SECONDS };
    return window.PalmSystem ? window.PalmSystem.launchParams : null;
  }

  // ---------- Start ----------
  fit();
  window.addEventListener("resize", fit);
  document.addEventListener("keydown", onKey);
  document.addEventListener("webOSRelaunch", function (e) { arrive(e && e.detail); });
  document.addEventListener("visibilitychange", function () { if (!document.hidden) arrive(launchParams()); });

  $("appletv")._press = function () { return LUNA.launch(CFG.appleTv.id); };
  $("door")._press = function () { setRoom("engine"); };
  $("shield")._press = pressShield;

  drawLiving();
  setInterval(function () { if (room === "living") drawLiving(); }, 60000);
  renderShortcuts();
  paintState();
  LUNA.listApps().then(renderApps, function () {
    $("note").hidden = false; $("note").textContent = "The app list is not available.";
  }).then(function () { collect(); paintFocus(); });

  // Self-test: ask the helper what works on this TV and draw only that.
  LUNA.ctl(["probe"]).then(L.parseCaps, function () { return {}; }).then(function (c) {
    caps = c;
    renderScenes();
    $("door").hidden = !caps.exec;
    $("shieldline").hidden = !caps.shield;
    $("shield").hidden = !caps.shield;
    collect(); paintFocus();
    if (caps.exec) LUNA.ctl(["start", "target=" + CFG.appleTv.id]).then(noop, noop);
    arrive(launchParams());
    var m = /[?&]room=(control|engine)/.exec(location.search || "");
    if (m) setRoom(m[1], true);
  });
})();

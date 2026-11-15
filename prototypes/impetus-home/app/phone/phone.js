// Impetus phone remote (issue #21): the page the TV serves to a phone on the
// home network. It pairs with the code on the TV screen, keeps the token in
// this phone's storage, and runs what the remote runs: the Apple TV, a scene
// on or off, the shield, an app, standby. Every request goes to
// cgi-bin/api (bin/impetus-phone), which checks the token and each word.
// Calm failures: a quiet line in the corner, never a box or a spinner.
// On a PC preview, window.MOCK_API stands in for the TV.
(function () {
  "use strict";

  var L = window.ImpetusLogic;
  var CFG = window.IMPETUS_CONFIG || {};
  var $ = function (id) { return document.getElementById(id); };
  var STORE = "impetus.phone.token";
  var STATE_EVERY = 5000, RETRY_EVERY = 10000, ARM_FOR = 4000;

  var token = "", memToken = "";
  var caps = {}, state = {}, sceneKeys = [];
  var stateTimer = null, quietTimer = null, armTimer = null;

  function noop() {}

  // ---------- the token ----------
  function loadToken() {
    try { return window.localStorage.getItem(STORE) || ""; } catch (e) { return memToken; }
  }
  function saveToken(t) {
    memToken = t;
    try { if (t) window.localStorage.setItem(STORE, t); else window.localStorage.removeItem(STORE); } catch (e) { /* memory only */ }
  }

  // ---------- the quiet line ----------
  function quiet(text, forMs) {
    clearTimeout(quietTimer);
    $("quiet").textContent = text || "";
    if (text && forMs) quietTimer = setTimeout(function () { $("quiet").textContent = ""; }, forMs);
  }

  // ---------- requests ----------
  function post(fields, words) {
    if (window.MOCK_API) return Promise.resolve(window.MOCK_API(fields, words || []));
    var body = L.phoneBody(fields, words);
    if (body === null) return Promise.reject(new Error("unsafe word"));
    return fetch("cgi-bin/api", { method: "POST", headers: { "Content-Type": "text/plain" },
      body: body, cache: "no-store" }).then(function (r) {
      if (!r.ok) throw new Error("http " + r.status);
      return r.text();
    });
  }

  // A request that needs the token. A revoked phone hears paired=0 and goes
  // back to the pairing screen.
  function authed(fields, words) {
    fields.t = token;
    return post(fields, words).then(function (text) {
      if (/^paired=0\s*$/.test(text)) { unpaired(); throw new Error("unpaired"); }
      quiet("");
      return text;
    }, function (e) { quiet("TV NOT ANSWERING"); throw e; });
  }

  function helper(words) {
    return authed({ op: "do" }, words).then(function (text) {
      var kv = L.parseKv(text);
      if (kv.ok !== "1") throw new Error(kv.error || "refused");
      return kv;
    });
  }

  // ---------- pressing ----------
  function key(cls, onPress) {
    var b = document.createElement("button");
    b.type = "button";
    b.className = "key " + cls;
    b.addEventListener("click", function () { press(b, onPress); });
    return b;
  }

  function span(cls, text) {
    var s = document.createElement("span");
    s.className = cls;
    s.textContent = text;
    return s;
  }

  function press(el, fn) {
    el.classList.add("pressed");
    setTimeout(function () { el.classList.remove("pressed"); }, 140);
    var p = fn();
    if (p && p.then) p.then(noop, function (e) {
      if (e && e.message === "unpaired") return;
      if ($("quiet").textContent !== "TV NOT ANSWERING") quiet("NOT DONE", 4000);
    });
  }

  // ---------- pairing ----------
  function showPair(line) {
    clearInterval(stateTimer);
    $("remote").hidden = true;
    $("pair").hidden = false;
    $("codeform").hidden = true;
    $("ask").hidden = false;
    $("pairline").textContent = line || "";
  }

  function unpaired() {
    saveToken("");
    token = "";
    showPair("This phone is no longer paired. Ask the TV for a new code.");
  }

  function askCode() {
    return post({ op: "pair" }).then(function (text) {
      var kv = L.parseKv(text);
      if (kv.error === "full") { $("pairline").textContent = "Eight phones are paired already. Revoke one in the engine room."; return; }
      if (kv.ok !== "1") throw new Error(kv.error || "refused");
      quiet("");
      $("ask").hidden = true;
      $("codeform").hidden = false;
      $("pairline").textContent = "The code is good for " + Math.max(1, Math.round(Number(kv.life || 120) / 60)) + " min.";
      $("code").focus();
    }, function (e) { quiet("TV NOT ANSWERING"); throw e; });
  }

  function sendCode(ev) {
    ev.preventDefault();
    var code = L.pairCode($("code").value);
    if (!code) { $("pairline").textContent = "Six digits, as on the TV."; return; }
    press($("send"), function () {
      return post({ op: "confirm", code: code, n: L.phoneName(navigator.userAgent) }).then(function (text) {
        var kv = L.parseKv(text);
        $("code").value = "";
        if (kv.token) { saveToken(kv.token); token = kv.token; hello(); return; }
        if (kv.error === "code") {
          $("pairline").textContent = "Not that code. " + kv.left + (kv.left === "1" ? " try" : " tries") + " left.";
        } else if (kv.error === "expired") {
          showPair("That code has run out. Ask for a new one.");
        } else if (kv.error === "full") {
          showPair("Eight phones are paired already. Revoke one in the engine room.");
        } else {
          throw new Error(kv.error || "refused");
        }
      }, function (e) { quiet("TV NOT ANSWERING"); throw e; });
    });
  }

  // ---------- the remote ----------
  function sceneCtx() {
    return { caps: caps, night: L.nightWindow(Date.now()), fallback: CFG.appleTv && CFG.appleTv.id };
  }

  function renderScenes() {
    var box = $("scenes");
    box.innerHTML = "";
    sceneKeys = [];
    (CFG.scenes || []).forEach(function (scene) {
      if (sceneKeys.length >= 3 || !L.sceneWords(scene, sceneCtx())) return;
      var b = key("scene", function () { return pressScene(scene); });
      var st = span("state", "");
      b.appendChild(span("name", scene.label || scene.id.toUpperCase()));
      b.appendChild(span("does", scene.does || ""));
      b.appendChild(st);
      box.appendChild(b);
      sceneKeys.push({ scene: scene, el: b, state: st });
    });
    $("sceneslabel").hidden = sceneKeys.length === 0;
  }

  // As on the TV: a latched key turns its scene off, any other starts its
  // scene (the helper ends the one that was on first).
  function pressScene(scene) {
    if (state.scene === scene.id) {
      return helper(["scene", "off"]).then(function () { state.scene = ""; paint(); setTimeout(refresh, 1500); });
    }
    var words = L.sceneWords(scene, sceneCtx());
    if (!words) return Promise.reject(new Error("scene not available"));
    return helper(["scene", "on"].concat(words)).then(function () {
      state.scene = scene.id; state.sleep = ""; state.end = ""; state.screenoff = "";
      paint();
      setTimeout(refresh, 2000);
    });
  }

  function pressShield() {
    return helper(["shield", state.shield === "on" ? "off" : "on"]).then(refresh);
  }

  function open(id, params) {
    var w = L.openWords(id, params, window.btoa ? function (s) { return window.btoa(s); } : null);
    if (!w) return Promise.reject(new Error("bad app id"));
    return helper(w);
  }

  // Standby takes two presses: the first arms the key for a few seconds.
  function pressStandby() {
    var b = $("standby");
    if (!b.classList.contains("armed")) {
      b.classList.add("armed");
      b.firstChild.textContent = "PRESS AGAIN FOR STANDBY";
      clearTimeout(armTimer);
      armTimer = setTimeout(disarm, ARM_FOR);
      return null;
    }
    disarm();
    return helper(["standby"]);
  }
  function disarm() {
    clearTimeout(armTimer);
    $("standby").classList.remove("armed");
    $("standby").firstChild.textContent = "STANDBY";
  }

  function renderShortcuts() {
    var box = $("shortcuts");
    box.innerHTML = "";
    (CFG.shortcuts || []).slice(0, 4).forEach(function (s) {
      if (!L.isSafeId(s.id)) return;
      var b = key("shortcut", function () { return open(s.id, s.params); });
      b.appendChild(span("name", s.label || s.id));
      if (s.place) b.appendChild(span("does", s.place));
      box.appendChild(b);
    });
    $("shortcutslabel").hidden = !box.firstChild;
  }

  function renderApps(list) {
    var box = $("apps");
    box.innerHTML = "";
    list.forEach(function (a) {
      var b = key("app", function () { return open(a.id); });
      b.appendChild(span("name", a.label.toUpperCase()));
      box.appendChild(b);
    });
    $("appslabel").hidden = list.length === 0;
  }

  function loadApps() {
    return authed({ op: "apps" }).then(function (text) {
      var res = JSON.parse(text || "{}");
      renderApps(L.pickApps(res.apps || [], CFG));
    }).then(noop, function () { renderApps([]); });
  }

  function paint() {
    sceneKeys.forEach(function (k) {
      var line = L.sceneLine(state, k.scene.id);
      k.el.classList.toggle("latched", line !== null);
      k.state.textContent = line || "";
    });
    $("shield").classList.toggle("latched", state.shield === "on");
    $("shieldstate").textContent = L.shieldLine(state);
  }

  function refresh() {
    if (!token || document.hidden) return Promise.resolve();
    return authed({ op: "state" }).then(function (text) { state = L.parseKv(text); paint(); }, noop);
  }

  function showRemote() {
    $("pair").hidden = true;
    $("remote").hidden = false;
    renderScenes();
    renderShortcuts();
    $("shield").hidden = $("shieldlabel").hidden = !caps.shield;
    paint();
    loadApps();
    clearInterval(stateTimer);
    stateTimer = setInterval(refresh, STATE_EVERY);
  }

  // The first word with the TV: is this phone still paired, what can the TV
  // do, what is on. No answer: a quiet line, and a later try.
  function hello() {
    if (!token) { showPair(); return; }
    authed({ op: "hello" }).then(function (text) {
      var s = L.parseSections(text);
      caps = L.parseCaps(s.caps);
      state = L.parseKv(s.state);
      showRemote();
    }, function (e) {
      if (e && e.message === "unpaired") return;
      setTimeout(hello, RETRY_EVERY);
    });
  }

  // ---------- start ----------
  $("ask").addEventListener("click", function () { press($("ask"), askCode); });
  $("again").addEventListener("click", function () { askCode().then(noop, noop); });
  $("codeform").addEventListener("submit", sendCode);
  $("appletv").addEventListener("click", function () {
    press($("appletv"), function () { return open(CFG.appleTv && CFG.appleTv.id); });
  });
  $("shield").addEventListener("click", function () { press($("shield"), pressShield); });
  $("standby").addEventListener("click", function () { press($("standby"), pressStandby); });
  document.addEventListener("visibilitychange", function () { if (!document.hidden) refresh(); });

  token = loadToken();
  hello();
})();

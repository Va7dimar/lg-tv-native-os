// Luna bus calls from the web app. A direct call is tried first; if the
// app's role is denied (listApps is, on this TV), the same luna-send runs
// through Homebrew Channel's root exec service. Everything that changes the
// TV goes through the helper (bin/impetus-ctl), one verb at a time.
// On a PC preview, window.MOCK_APPS, MOCK_CTL, MOCK_STILL and MOCK_HOSTS
// stand in for the TV.
(function (root) {
  "use strict";

  var L = root.ImpetusLogic;
  var SAM = "luna://com.webos.service.applicationmanager/";
  var EXEC = "luna://org.webosbrew.hbchannel.service/exec";
  var IP = /^[0-9A-Fa-f.:]+$/;
  var pending = []; // keep bridges alive until they answer

  function call(uri, params) {
    return new Promise(function (resolve, reject) {
      if (typeof PalmServiceBridge === "undefined") {
        reject(new Error("no PalmServiceBridge"));
        return;
      }
      var bridge = new PalmServiceBridge();
      pending.push(bridge);
      bridge.onservicecallback = function (msg) {
        pending.splice(pending.indexOf(bridge), 1);
        var res;
        try { res = JSON.parse(msg); } catch (e) { reject(e); return; }
        if (res.returnValue === false) reject(res); else resolve(res);
      };
      bridge.call(uri, JSON.stringify(params || {}));
    });
  }

  // Root shell. Only three shapes ever reach it, each built here from fixed
  // text and checked values: a luna-send for the app list, one nslookup, and
  // the helper line from ImpetusLogic.ctlCommand.
  function execRaw(command) { return call(EXEC, { command: command }); }
  function exec(command) {
    return execRaw(command).then(function (res) { return res.stdoutString || ""; });
  }

  function rootLuna(method, payload) {
    var cmd = "luna-send -n 1 " + SAM + method + " '" + JSON.stringify(payload) + "'";
    return exec(cmd).then(function (text) {
      var out = JSON.parse(text || "{}");
      if (out.returnValue === false) throw out;
      return out;
    });
  }

  function viaEither(method, payload) {
    return call(SAM + method, payload).catch(function () {
      return rootLuna(method, payload);
    });
  }

  function listApps() {
    if (root.MOCK_APPS) return Promise.resolve(root.MOCK_APPS);
    return viaEither("listApps", {}).then(function (res) { return res.apps || []; });
  }

  function launch(id, params) {
    var p = L.launchPayload(id, params);
    if (!p) return Promise.reject(new Error("bad launch payload"));
    if (root.MOCK_APPS) { console.log("launch", JSON.stringify(p)); return Promise.resolve({}); }
    return viaEither("launch", p);
  }

  // ---- The helper ----

  // The app's own folder, read from the page's address; config.js is the
  // fallback (a PC preview never gets here: MOCK_CTL answers first).
  function appDir() {
    var m = /^(\/[A-Za-z0-9._\/-]+\/usr\/palm\/applications\/[A-Za-z0-9._-]+)\/[^\/]*$/.exec(location.pathname || "");
    return m ? m[1] : (root.IMPETUS_CONFIG && root.IMPETUS_CONFIG.appDir);
  }

  function ctlRaw(words) {
    var cmd = L.ctlCommand(appDir(), words);
    if (!cmd) return Promise.reject(new Error("bad helper words"));
    return execRaw(cmd);
  }

  // One helper verb; resolves with its text answer.
  function ctl(words) {
    if (root.MOCK_CTL) {
      return new Promise(function (resolve) { resolve(root.MOCK_CTL(words) || ""); });
    }
    return ctlRaw(words).then(function (res) { return res.stdoutString || ""; });
  }

  // The APPLE TV still -> {kind: "live"|"last"|"none", age, src}. The JPG
  // comes back as bytes behind one header line.
  function still(nolive) {
    if (root.MOCK_STILL) return Promise.resolve(root.MOCK_STILL(nolive));
    return ctlRaw(nolive ? ["still", "nolive"] : ["still"]).then(function (res) {
      var s = L.parseStill(res.stdoutBytes ? atob(res.stdoutBytes) : "");
      if (s.kind === "none" || !s.body) return { kind: "none", age: 0, src: null };
      return { kind: s.kind, age: s.age, src: "data:image/jpeg;base64," + btoa(s.body) };
    });
  }

  function hostOf(ip) {
    if (!IP.test(ip)) return Promise.resolve(null);
    if (root.MOCK_HOSTS) return Promise.resolve(root.MOCK_HOSTS[ip] || null);
    return exec("nslookup " + ip + " 2>/dev/null").then(function (text) {
      return L.parseNslookup(text, ip);
    });
  }

  root.ImpetusLuna = { call: call, listApps: listApps, launch: launch,
    ctl: ctl, still: still, hostOf: hostOf };
})(this);

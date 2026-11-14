// Luna bus calls from the web app. A direct call is tried first; if the
// app's role is denied (listApps is, on this TV), the same luna-send runs
// through Homebrew Channel's root exec service. On a PC preview,
// window.MOCK_APPS and window.MOCK_NETSTAT stand in for the TV.
(function (root) {
  "use strict";

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

  // Root shell; command is built here from fixed strings and checked values only.
  function exec(command) {
    return call(EXEC, { command: command }).then(function (res) { return res.stdoutString || ""; });
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
    var p = root.ImpetusLogic.launchPayload(id, params);
    if (!p) return Promise.reject(new Error("bad launch payload"));
    if (root.MOCK_APPS) { console.log("launch", JSON.stringify(p)); return Promise.resolve({}); }
    return viaEither("launch", p);
  }

  function connections() {
    if (root.MOCK_NETSTAT) return Promise.resolve(root.ImpetusLogic.parseNetstat(root.MOCK_NETSTAT()));
    return exec("netstat -tnp 2>/dev/null").then(root.ImpetusLogic.parseNetstat);
  }

  function hostOf(ip) {
    if (!IP.test(ip)) return Promise.resolve(null);
    if (root.MOCK_HOSTS) return Promise.resolve(root.MOCK_HOSTS[ip] || null);
    return exec("nslookup " + ip + " 2>/dev/null").then(function (text) {
      return root.ImpetusLogic.parseNslookup(text, ip);
    });
  }

  root.ImpetusLuna = { call: call, listApps: listApps, launch: launch,
    connections: connections, hostOf: hostOf };
})(this);

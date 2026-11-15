// phone-serve.js: the phone remote's web server where the TV's busybox has
// no httpd (issue #21). The same contract as busybox httpd, nothing more:
//   node phone-serve.js <port> <www dir>
// GET serves a file from <www dir> (one folder deep at most); POST
// /cgi-bin/api runs <www dir>/cgi-bin/api as CGI. Callers from outside the
// home network get 403. impetus-ctl starts and stops it.
// Plain ES5: the TV's node is old.
"use strict";

var http = require("http");
var fs = require("fs");
var path = require("path");
var spawn = require("child_process").spawn;

var port = Number(process.argv[2]);
var root = process.argv[3];
// The shell that runs the CGI door; a test may point it elsewhere.
var SHELL = process.env.IMPETUS_CGI_SHELL || "sh";
var BODY_MAX = 4096;
var CGI_WAIT = 40000; // a standby may try three power calls of 10 s each
var TYPES = { ".html": "text/html; charset=utf-8", ".js": "application/javascript; charset=utf-8",
  ".css": "text/css; charset=utf-8", ".woff2": "font/woff2" };

function homeNet(addr) {
  var a = String(addr || "").replace(/^::ffff:/, "");
  return /^(10\.|192\.168\.|172\.(1[6-9]|2\d|3[01])\.|127\.)/.test(a) || a === "::1";
}

function end(res, code) { res.writeHead(code, { "Content-Type": "text/plain" }); res.end(); }

function serveFile(req, res) {
  var p = req.url.split("?")[0];
  if (p === "/") p = "/index.html";
  if (!/^\/([A-Za-z0-9_-]+\/)?[A-Za-z0-9_-]+\.[a-z0-9]+$/.test(p) || p.indexOf("/cgi-bin/") === 0) return end(res, 404);
  fs.readFile(path.join(root, p), function (err, data) {
    if (err) return end(res, 404);
    res.writeHead(200, { "Content-Type": TYPES[path.extname(p)] || "application/octet-stream",
      "Cache-Control": "no-cache" });
    res.end(data);
  });
}

// CGI output: header lines, a blank line, the body.
function splitCgi(buf) {
  var text = buf.toString("latin1");
  var cut = text.indexOf("\r\n\r\n"), skip = 4;
  if (cut < 0) { cut = text.indexOf("\n\n"); skip = 2; }
  if (cut < 0) return { headers: { "Content-Type": "text/plain" }, body: buf };
  var headers = {};
  text.slice(0, cut).split(/\r?\n/).forEach(function (line) {
    var i = line.indexOf(":");
    if (i > 0) headers[line.slice(0, i).trim()] = line.slice(i + 1).trim();
  });
  return { headers: headers, body: buf.slice(Buffer.byteLength(text.slice(0, cut + skip), "latin1")) };
}

function runCgi(req, res) {
  var chunks = [], size = 0, over = false;
  req.on("data", function (c) {
    size += c.length;
    if (size > BODY_MAX) over = true; else chunks.push(c);
  });
  req.on("end", function () {
    if (over) return end(res, 413);
    var body = Buffer.concat(chunks);
    var env = {};
    Object.keys(process.env).forEach(function (k) { env[k] = process.env[k]; });
    env.GATEWAY_INTERFACE = "CGI/1.1";
    env.REQUEST_METHOD = req.method;
    env.CONTENT_LENGTH = String(body.length);
    env.CONTENT_TYPE = req.headers["content-type"] || "";
    env.REMOTE_ADDR = String(req.socket.remoteAddress || "").replace(/^::ffff:/, "");
    env.HTTP_USER_AGENT = req.headers["user-agent"] || "";
    var child = spawn(SHELL, [path.join(root, "cgi-bin", "api")], { env: env });
    var out = [];
    var timer = setTimeout(function () { child.kill(); }, CGI_WAIT);
    child.stdout.on("data", function (c) { out.push(c); });
    child.stderr.on("data", function () {});
    child.on("error", function () { clearTimeout(timer); end(res, 502); });
    child.on("close", function () {
      clearTimeout(timer);
      if (res.headersSent) return;
      var r = splitCgi(Buffer.concat(out));
      res.writeHead(200, r.headers);
      res.end(r.body);
    });
    child.stdin.on("error", function () {});
    child.stdin.end(body);
  });
}

var server = http.createServer(function (req, res) {
  if (!homeNet(req.socket.remoteAddress)) return end(res, 403);
  if (req.method === "POST" && req.url.split("?")[0] === "/cgi-bin/api") return runCgi(req, res);
  if (req.method === "GET" || req.method === "HEAD") return serveFile(req, res);
  end(res, 405);
});
server.on("error", function () { process.exit(1); }); // the port is taken: impetus-ctl tries the next
server.listen(port);

// Counts calls to the shield's dead address. This TV's kernel has no
// firewall module, so the count comes from a listener: every blocked name
// resolves to the sink address, and each connection that arrives is one
// blocked call. It answers nothing and closes at once.
//
// Usage: node shield-count.js <count file> <ipv4 sink> [ipv6 sink]
// Old node on the TV: no arrow functions, no const.
var net = require("net");
var fs = require("fs");

var file = process.argv[2];
var sinks = process.argv.slice(3);
var count = 0, dirty = true;

if (!file || !sinks.length) process.exit(2);

function hit(socket) {
  count++;
  dirty = true;
  socket.on("error", function () {});
  socket.destroy();
}

sinks.forEach(function (addr) {
  [80, 443].forEach(function (port) {
    var server = net.createServer(hit);
    server.on("error", function () {}); // a port in use is skipped, not fatal
    server.listen(port, addr);
  });
});

setInterval(function () {
  if (!dirty) return;
  dirty = false;
  try { fs.writeFileSync(file, String(count) + "\n"); } catch (e) { /* /tmp gone: keep counting */ }
}, 1000);

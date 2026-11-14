// Tiny static server for previewing Impetus Home on a PC.
//   node preview/serve.js        then open http://localhost:8765/preview/dev.html
// Serves this prototype's folder only, on this machine only.
const http = require("http"), fs = require("fs"), path = require("path");
const root = path.resolve(__dirname, "..");
const port = Number(process.env.PORT) || 8765;
const types = { ".html": "text/html; charset=utf-8", ".js": "text/javascript", ".css": "text/css",
  ".woff2": "font/woff2", ".png": "image/png" };
http.createServer((req, res) => {
  const p = path.join(root, decodeURIComponent(req.url.split("?")[0]));
  if (p !== root && !p.startsWith(root + path.sep)) { res.writeHead(403); return res.end(); }
  fs.readFile(p, (err, data) => {
    if (err) { res.writeHead(404); return res.end(); }
    res.writeHead(200, { "Content-Type": types[path.extname(p)] || "application/octet-stream" });
    res.end(data);
  });
}).listen(port, "127.0.0.1", () => console.log("http://localhost:" + port + "/preview/dev.html"));

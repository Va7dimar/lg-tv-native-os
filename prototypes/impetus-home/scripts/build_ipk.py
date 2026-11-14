#!/usr/bin/env python3
"""Build the Impetus Home web-app IPK from app/. No LG SDK.

Same ar/tar layout as prototypes/wayland-hello/scripts/build_ipk.py (ares-cli
package.js order, plain 16-byte ar names, fixed timestamps), so the same
app/ files always give the same IPK bytes.

Usage: build_ipk.py [out.ipk]
"""

from __future__ import annotations

import gzip
import hashlib
import io
import json
import os
import sys
import tarfile

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
APP_DIR = os.path.join(ROOT, "app")


def _pad(text, width):
    return (str(text) + (" " * width))[:width]


def _ar_header(name, size, mtime):
    return (_pad(name, 16) + _pad(int(mtime), 12) + "0     " + "0     "
            + "100644  " + _pad(int(size), 10) + "`\n").encode("ascii")


def _tar_gzip(members, mtime):
    raw = io.BytesIO()
    with tarfile.open(fileobj=raw, mode="w", format=tarfile.USTAR_FORMAT) as tar:
        dirs = set()
        for arcname, _data in members:
            parent = os.path.dirname(arcname)
            while parent:
                dirs.add(parent)
                parent = os.path.dirname(parent)
        for directory in sorted(dirs):
            info = tarfile.TarInfo(directory)
            info.type = tarfile.DIRTYPE
            info.mode = 0o755
            info.mtime = mtime
            tar.addfile(info)
        for arcname, data in members:
            info = tarfile.TarInfo(arcname)
            info.size = len(data)
            info.mode = 0o644
            info.mtime = mtime
            tar.addfile(info, io.BytesIO(data))
    out = io.BytesIO()
    with gzip.GzipFile(filename="", mode="wb", fileobj=out, mtime=mtime) as gz:
        gz.write(raw.getvalue())
    return out.getvalue()


def build_ipk(out_path, mtime=0):
    with open(os.path.join(APP_DIR, "appinfo.json"), "r", encoding="utf-8") as fh:
        info = json.load(fh)
    app_id, version = info["id"], info["version"]
    prefix = "usr/palm/applications/" + app_id
    members = []
    for base, _dirs, files in os.walk(APP_DIR):
        for name in files:
            path = os.path.join(base, name)
            rel = os.path.relpath(path, APP_DIR).replace(os.sep, "/")
            with open(path, "rb") as fh:
                data = fh.read()
            if name.endswith((".js", ".css", ".html", ".json")):
                data = data.replace(b"\r\n", b"\n")
            members.append((prefix + "/" + rel, data))
    members.sort(key=lambda m: m[0])
    size_kb = max(1, (sum(len(d) for _n, d in members) + 1023) // 1024)
    control = "\n".join([
        "Package: " + app_id, "Version: " + version, "Section: misc",
        "Priority: optional", "Architecture: all", "Installed-Size: %d" % size_kb,
        "Maintainer: N/A <nobody@example.com>", "Description: Impetus Home",
        "webOS-Package-Format-Version: 2", "webOS-Packager-Version: impetus-home-" + version, "",
    ]).encode("utf-8")
    parts = [("debian-binary", b"2.0\n"),
             ("control.tar.gz", _tar_gzip([("control", control)], mtime)),
             ("data.tar.gz", _tar_gzip(members, mtime))]
    blob = bytearray(b"!<arch>\n")
    for name, data in parts:
        blob += _ar_header(name, len(data), mtime) + data
        if len(data) % 2:
            blob += b"\n"
    os.makedirs(os.path.dirname(os.path.abspath(out_path)), exist_ok=True)
    with open(out_path, "wb") as fh:
        fh.write(blob)
    return hashlib.sha256(blob).hexdigest()


def _version():
    with open(os.path.join(APP_DIR, "appinfo.json"), encoding="utf-8") as fh:
        return json.load(fh)["version"]


def main(argv):
    out = argv[1] if len(argv) > 1 else os.path.join(ROOT, "build", "org.va7dimar.home_%s_all.ipk" % _version())
    print("%s  %s" % (build_ipk(out), out))
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))

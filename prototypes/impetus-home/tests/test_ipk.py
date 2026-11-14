#!/usr/bin/env python3
"""Host check: the IPK is ar + tar.gz with appinfo for a web app, built twice to the same bytes."""

import gzip
import io
import json
import os
import sys
import tarfile
import tempfile

sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "scripts"))
import build_ipk  # noqa: E402


def ar_members(blob):
    assert blob[:8] == b"!<arch>\n"
    pos, out = 8, {}
    while pos < len(blob):
        name = blob[pos:pos + 16].decode().strip()
        size = int(blob[pos + 48:pos + 58].decode().strip())
        out[name] = blob[pos + 60:pos + 60 + size]
        pos += 60 + size + (size % 2)
    return out


def main():
    with tempfile.TemporaryDirectory() as tmp:
        a, b = os.path.join(tmp, "a.ipk"), os.path.join(tmp, "b.ipk")
        assert build_ipk.build_ipk(a) == build_ipk.build_ipk(b), "not reproducible"
        with open(a, "rb") as fh:
            parts = ar_members(fh.read())
    assert list(parts) == ["debian-binary", "control.tar.gz", "data.tar.gz"], list(parts)
    data = tarfile.open(fileobj=io.BytesIO(gzip.decompress(parts["data.tar.gz"])))
    names = data.getnames()
    prefix = "usr/palm/applications/org.va7dimar.home/"
    for need in ("appinfo.json", "index.html", "home.js", "fonts/Syncopate-Bold.woff2", "fonts/LICENSE-Syncopate.txt", "icon.png"):
        assert prefix + need in names, need
    info = json.load(data.extractfile(prefix + "appinfo.json"))
    assert info["id"] == "org.va7dimar.home" and info["type"] == "web" and info["title"] == "Impetus"
    print("test_ipk: 1 test, 0 failed")


if __name__ == "__main__":
    main()

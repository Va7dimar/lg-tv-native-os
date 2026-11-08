#!/usr/bin/env python3
"""Download the openlgtv buildroot-nc4 2026.08-webos SDK and check its digest.

Fail closed. The GitHub release asset digest, the digest pinned in this file,
and the SHA256 of the downloaded bytes must all be identical. A mismatch stops
the script before extract. There is no bypass flag. Unknown arguments are
rejected. The toolchain is written under build-cache/ and is not for commit.

Usage: python3 -I scripts/fetch_openlgtv_sdk.py
"""
import hashlib
import json
import os
import platform
import sys
import tarfile
import urllib.request

TAG = "2026.08-webos"
API = "https://api.github.com/repos/openlgtv/buildroot-nc4/releases/tags/" + TAG
# GitHub asset digest field for this tag. Update only together with a fresh API read.
PINNED = {
    "x86_64": (
        "arm-webos-linux-gnueabi_sdk-buildroot-x86_64.tar.gz",
        "2230a6351e5cce6fcb9d4fdcb4697335f223995401ef969c81744aaeb14c5344",
    ),
    "aarch64": (
        "arm-webos-linux-gnueabi_sdk-buildroot-aarch64.tar.gz",
        "3a9330f3789f8008ece7c8a48f58c3a71d0307a9a1f81896db938b785524c3ce",
    ),
}
ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
CACHE = os.path.join(ROOT, "build-cache")
DL = os.path.join(CACHE, "downloads")
DEST = os.path.join(CACHE, "openlgtv-sdk")
UA = {"User-Agent": "wayland-hello-sdk-fetch/0.2", "Accept": "application/vnd.github+json"}


def die(msg):
    sys.exit("error: " + msg)


def main():
    if len(sys.argv) != 1:
        die("this script takes no arguments and has no bypass")
    machine = platform.machine()
    if machine not in PINNED:
        die("no pinned SDK asset for host machine %s" % machine)
    name, pinned = PINNED[machine]
    req = urllib.request.Request(API, headers=UA)
    with urllib.request.urlopen(req, timeout=60) as r:
        rel = json.load(r)
    digest = None
    url = None
    for asset in rel.get("assets") or []:
        if asset.get("name") == name:
            digest = asset.get("digest") or ""
            url = asset.get("browser_download_url")
            break
    if not digest or not url:
        die("release %s has no asset %s" % (TAG, name))
    if not digest.startswith("sha256:"):
        die("GitHub digest for %s is not sha256: %r" % (name, digest))
    remote = digest.split(":", 1)[1].lower()
    if remote != pinned:
        die("GitHub digest %s does not match pinned %s; not downloading" % (remote, pinned))
    os.makedirs(DL, exist_ok=True)
    dest = os.path.join(DL, name)
    if os.path.exists(dest):
        h = hashlib.sha256()
        with open(dest, "rb") as f:
            for chunk in iter(lambda: f.read(1024 * 1024), b""):
                h.update(chunk)
        if h.hexdigest() != pinned:
            die("existing %s hash mismatch; refusing to use or replace it automatically" % dest)
    else:
        tmp = dest + ".part"
        req = urllib.request.Request(url, headers={"User-Agent": UA["User-Agent"]})
        with urllib.request.urlopen(req, timeout=120) as r, open(tmp, "wb") as f:
            while True:
                chunk = r.read(1024 * 1024)
                if not chunk:
                    break
                f.write(chunk)
        h = hashlib.sha256()
        with open(tmp, "rb") as f:
            for chunk in iter(lambda: f.read(1024 * 1024), b""):
                h.update(chunk)
        if h.hexdigest() != pinned:
            os.unlink(tmp)
            die("download hash mismatch; deleted partial file")
        os.rename(tmp, dest)
    marker = os.path.join(DEST, ".extracted-sha256")
    if os.path.exists(marker) and open(marker).read().strip() == pinned:
        print("sdk already extracted for %s" % pinned)
        return
    os.makedirs(DEST, exist_ok=True)

    def member_ok(member, dest_path):
        # The SDK ships symlinks whose targets are the build machine's prefix.
        # relocate-sdk.sh rewrites those. Reject only names that escape the tree.
        parts = member.name.split("/")
        if member.name.startswith("/") or ".." in parts:
            raise tarfile.OutsideDestinationError(member, dest_path)
        return member

    with tarfile.open(dest, "r:gz") as tar:
        tar.extractall(DEST, filter=member_ok)
    with open(marker, "w") as f:
        f.write(pinned + "\n")
    print("verified sha256 %s" % pinned)
    print("extracted under %s" % DEST)


if __name__ == "__main__":
    main()

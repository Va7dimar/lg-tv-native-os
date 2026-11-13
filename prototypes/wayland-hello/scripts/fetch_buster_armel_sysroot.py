#!/usr/bin/env python3
"""Fetch a glibc 2.28 Debian buster armel sysroot from archive.debian.org.

Chain of trust (recorded to build-cache/sysroot-manifest.json):
  InRelease/Release(.gpg) --gpgv(debian archive keyring)--> SHA256 of
  main/binary-armel/Packages.xz --> SHA256 of each .deb --> extracted with a
  pure-python ar reader + tarfile(filter="data") into build-cache/sysroot.
No maintainer scripts are run; nothing is installed system-wide.
FAIL CLOSED: if gpgv or a keyring is unavailable, or the Release signature
does not verify, the script STOPS. There is no bypass flag; an unverified
Release is never used. Unknown arguments are rejected.

Usage: python3 -I scripts/fetch_buster_armel_sysroot.py
"""
import hashlib, io, json, lzma, os, subprocess, sys, tarfile, urllib.request

MIRROR = "https://archive.debian.org/debian"
SUITE = "buster"
ARCH = "armel"
PKGS = ["libc6", "libc6-dev", "linux-libc-dev"]
ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
CACHE = os.path.join(ROOT, "build-cache")
DL = os.path.join(CACHE, "downloads")
SYSROOT = os.path.join(CACHE, "sysroot")
KEYRINGS = ["/usr/share/keyrings/debian-archive-keyring.gpg",
            "/usr/share/keyrings/debian-archive-removed-keys.gpg"]
UA = {"User-Agent": "wayland-hello-sysroot-fetch/0.1"}


def get(url, dest):
    if not os.path.exists(dest):
        req = urllib.request.Request(url, headers=UA)
        with urllib.request.urlopen(req, timeout=60) as r, open(dest + ".part", "wb") as f:
            f.write(r.read())
        os.rename(dest + ".part", dest)
    with open(dest, "rb") as f:
        return f.read()


def sha256(b):
    return hashlib.sha256(b).hexdigest()


def verify_release(manifest):
    rel = get(f"{MIRROR}/dists/{SUITE}/Release", os.path.join(DL, "Release"))
    get(f"{MIRROR}/dists/{SUITE}/Release.gpg", os.path.join(DL, "Release.gpg"))
    manifest["release_sha256"] = sha256(rel)
    ok = False
    for kr in KEYRINGS:
        if os.path.exists(kr):
            try:
                p = subprocess.run(["gpgv", "--keyring", kr, os.path.join(DL, "Release.gpg"),
                                    os.path.join(DL, "Release")], capture_output=True, text=True, timeout=60)
            except (OSError, subprocess.TimeoutExpired) as e:
                manifest.setdefault("gpgv", []).append({"keyring": kr, "error": repr(e)})
                continue
            manifest.setdefault("gpgv", []).append({"keyring": kr, "rc": p.returncode, "stderr": p.stderr[-800:]})
            if p.returncode == 0:
                ok = True; break
    manifest["release_signature_verified"] = ok
    if not ok:
        # Fail closed. No bypass exists; nothing derived from this Release is used.
        sys.exit("Release signature NOT verified (no gpgv/keyring or bad signature); stopping. "
                 "No sysroot was extracted.")
    return rel.decode()


def packages_index(release_text, manifest):
    rel_path = f"main/binary-{ARCH}/Packages.xz"
    want = None; in_sha = False
    for line in release_text.splitlines():
        if line.startswith("SHA256:"):
            in_sha = True; continue
        if in_sha and line.startswith(" "):
            h, size, path = line.split()
            if path == rel_path:
                want = h
        elif in_sha:
            in_sha = False
    if not want:
        sys.exit("Packages.xz not listed in Release")
    data = get(f"{MIRROR}/dists/{SUITE}/{rel_path}", os.path.join(DL, "Packages-armel.xz"))
    if sha256(data) != want:
        sys.exit("Packages.xz hash mismatch")
    manifest["packages_xz_sha256"] = want
    return lzma.decompress(data).decode()


def parse_stanzas(text):
    cur = {}
    for line in text.splitlines():
        if not line:
            if cur:
                yield cur
            cur = {}
        elif not line.startswith(" ") and ":" in line:
            k, v = line.split(":", 1); cur[k] = v.strip()
    if cur:
        yield cur


def ar_members(blob):
    assert blob[:8] == b"!<arch>\n", "not an ar archive"
    off = 8
    while off + 60 <= len(blob):
        hdr = blob[off:off + 60]
        name = hdr[:16].decode().strip().rstrip("/")
        size = int(hdr[48:58].decode().strip())
        yield name, blob[off + 60: off + 60 + size]
        off += 60 + size + (size & 1)


def extract_deb(blob, dest):
    for name, data in ar_members(blob):
        if name.startswith("data.tar"):
            mode = "r:xz" if name.endswith(".xz") else "r:gz" if name.endswith(".gz") else "r:"
            def relink(member, path):
                # Debian -dev symlinks are absolute (e.g. libdl.so -> /lib/arm-linux-gnueabi/libdl.so.2);
                # rewrite them relative so they resolve inside the sysroot, then apply the
                # strict "data" filter (which rejects absolute/out-of-tree links).
                if member.issym() and member.linkname.startswith("/"):
                    here = os.path.dirname("/" + member.name.lstrip("./"))
                    member = member.replace(linkname=os.path.relpath(member.linkname, here), deep=False)
                return tarfile.data_filter(member, path)
            with tarfile.open(fileobj=io.BytesIO(data), mode=mode) as t:
                t.extractall(dest, filter=relink)
            return
    raise RuntimeError("no data.tar in deb")


def main():
    if len(sys.argv) > 1:
        sys.exit("usage: python3 -I scripts/fetch_buster_armel_sysroot.py (no options; "
                 "signature verification cannot be bypassed)")
    os.makedirs(DL, exist_ok=True); os.makedirs(SYSROOT, exist_ok=True)
    manifest = {"mirror": MIRROR, "suite": SUITE, "arch": ARCH, "packages": []}
    rel = verify_release(manifest)
    idx = {s["Package"]: s for s in parse_stanzas(packages_index(rel, manifest)) if s.get("Package") in PKGS}
    for p in PKGS:
        s = idx[p]
        url = f"{MIRROR}/{s['Filename']}"
        blob = get(url, os.path.join(DL, os.path.basename(s["Filename"])))
        h = sha256(blob)
        if h != s["SHA256"]:
            sys.exit(f"hash mismatch for {p}")
        extract_deb(blob, SYSROOT)
        manifest["packages"].append({"package": p, "version": s["Version"], "url": url, "sha256": h, "size": len(blob)})
        print(f"ok {p} {s['Version']} {h}")
    # libc.so / libdl.so linker scripts and symlinks use absolute paths; with --sysroot ld
    # re-roots them because the scripts live inside the sysroot.
    with open(os.path.join(CACHE, "sysroot-manifest.json"), "w") as f:
        json.dump(manifest, f, indent=2)
    print("manifest:", os.path.join(CACHE, "sysroot-manifest.json"))


if __name__ == "__main__":
    main()

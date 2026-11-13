#!/usr/bin/env python3
"""Build a webOS native IPK with tar and an ar archive. No LG SDK.

The member order and paths follow ares-cli (webos-tools) lib/package.js:

  ar -q <ipk> debian-binary control.tar.gz data.tar.gz
  debian-binary is the four bytes "2.0\\n"
  control fields are the createControlFile() list, including
  webOS-Package-Format-Version: 2
  data.tar.gz is rooted at usr/palm/applications/<app id>/

Timestamps, owners, and gzip headers are fixed so the same binary and
packaging files always produce the same IPK bytes. ares itself stamps the
archive with the current time; this script keeps the layout and drops the
clock.
"""

from __future__ import annotations

import argparse
import gzip
import io
import json
import os
import sys
import tarfile

APP_ID = "org.va7dimar.waylandhello"
VERSION = "0.9.0"
ARCH = "arm"
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PACKAGING = os.path.join(ROOT, "packaging")
APP_PREFIX = "usr/palm/applications/" + APP_ID


def _pad(text, width):
    return (str(text) + (" " * width))[:width]


def _ar_header(name, size, mtime):
    # Plain 16-byte space-padded names. GNU ar appends '/' and this TV's
    # installer rejected that with "ipk verified failed" (errorCode -5).
    # ares package.js arFileHeader is the same width: 16 name, 12 mtime,
    # uid/gid "0     ", mode "100644  ", 10 size, then backtick newline.
    return (
        _pad(name, 16)
        + _pad(int(mtime), 12)
        + "0     "
        + "0     "
        + "100644  "
        + _pad(int(size), 10)
        + "`\n"
    ).encode("ascii")


def _tar_gzip(members, mtime):
    """members: list of (arcname, data, mode). Directories are implied."""
    raw = io.BytesIO()
    with tarfile.open(fileobj=raw, mode="w", format=tarfile.USTAR_FORMAT) as tar:
        dirs = []
        seen = set()
        for arcname, _data, _mode in members:
            parent = os.path.dirname(arcname)
            while parent and parent not in seen:
                dirs.append(parent)
                seen.add(parent)
                parent = os.path.dirname(parent)
        for directory in sorted(dirs):
            info = tarfile.TarInfo(directory)
            info.type = tarfile.DIRTYPE
            info.mode = 0o755
            info.mtime = mtime
            info.uid = 0
            info.gid = 0
            info.uname = ""
            info.gname = ""
            tar.addfile(info)
        for arcname, data, mode in members:
            info = tarfile.TarInfo(arcname)
            info.size = len(data)
            info.mode = mode
            info.mtime = mtime
            info.uid = 0
            info.gid = 0
            info.uname = ""
            info.gname = ""
            tar.addfile(info, io.BytesIO(data))
    out = io.BytesIO()
    with gzip.GzipFile(filename="", mode="wb", fileobj=out, mtime=mtime) as gz:
        gz.write(raw.getvalue())
    return out.getvalue()


def _control(installed_size):
    lines = [
        "Package: " + APP_ID,
        "Version: " + VERSION,
        "Section: misc",
        "Priority: optional",
        "Architecture: " + ARCH,
        "Installed-Size: " + str(installed_size),
        "Maintainer: N/A <nobody@example.com>",
        "Description: wayland-hello native probe",
        "webOS-Package-Format-Version: 2",
        "webOS-Packager-Version: wayland-hello-" + VERSION,
        "",
    ]
    return "\n".join(lines).encode("utf-8")


def render_appinfo(lifecycle="omit", default_window_type="card"):
    """lifecycle is omit, 1, or 2. omit leaves nativeLifeCycleInterfaceVersion out."""
    if lifecycle not in ("omit", "1", "2", 1, 2, None):
        raise SystemExit("lifecycle must be omit, 1, or 2")
    if lifecycle in (1, 2):
        lifecycle = str(lifecycle)
    if not default_window_type or not default_window_type.isalnum() or len(default_window_type) > 32:
        raise SystemExit("defaultWindowType must be a short token such as card or overlay")
    path = os.path.join(PACKAGING, "appinfo.json")
    with open(path, "r", encoding="utf-8") as fh:
        info = json.load(fh)
    info["defaultWindowType"] = default_window_type
    info["noSplashOnLaunch"] = True
    info.pop("nativeLifeCycleInterfaceVersion", None)
    if lifecycle in ("1", "2"):
        info["nativeLifeCycleInterfaceVersion"] = int(lifecycle)
    return (json.dumps(info, indent=2) + "\n").encode("utf-8")


def build_ipk(binary_path, out_path, mtime=0, lifecycle="omit", default_window_type=None, heartbeat_ms=0, menu=False):
    if not os.path.isfile(binary_path):
        raise SystemExit("binary not found: %s" % binary_path)
    if default_window_type is None:
        # Lifecycle-2 persist experiment uses overlay so Home's CARD does not
        # cover the surface. Plain packages stay card (the 30 s SAM-launch path).
        default_window_type = "overlay" if str(lifecycle) == "2" else "card"
    files = {
        "appinfo.json": (render_appinfo(lifecycle, default_window_type), 0o644),
        "icon.png": (None, 0o644),
        "wayland-hello-launch.sh": (None, 0o755),
    }
    members = []
    payload = 0
    for name, (data, mode) in files.items():
        if data is None:
            with open(os.path.join(PACKAGING, name), "rb") as fh:
                data = fh.read()
        payload += len(data)
        members.append((APP_PREFIX + "/" + name, data, mode))
    with open(binary_path, "rb") as fh:
        binary = fh.read()
    payload += len(binary)
    members.append((APP_PREFIX + "/wayland-hello", binary, 0o755))
    if heartbeat_ms:
        hb = ("%d\n" % int(heartbeat_ms)).encode("ascii")
        payload += len(hb)
        members.append((APP_PREFIX + "/heartbeat-ms", hb, 0o644))
    if menu:
        # SAM launches the ELF (appinfo main). A sidecar next to the ELF
        # selects --menu; rewriting launch.sh cannot, because it is not main.
        payload += 2
        members.append((APP_PREFIX + "/menu", b"1\n", 0o644))
    members.sort(key=lambda item: item[0])
    installed = max(1, (payload + 1023) // 1024)
    control_gz = _tar_gzip([("control", _control(installed), 0o644)], mtime)
    data_gz = _tar_gzip(members, mtime)
    debian = b"2.0\n"
    parts = [
        ("debian-binary", debian),
        ("control.tar.gz", control_gz),
        ("data.tar.gz", data_gz),
    ]
    blob = bytearray(b"!<arch>\n")
    for name, data in parts:
        blob += _ar_header(name, len(data), mtime)
        blob += data
        if len(data) % 2:
            blob += b"\n"
    os.makedirs(os.path.dirname(os.path.abspath(out_path)), exist_ok=True)
    with open(out_path, "wb") as fh:
        fh.write(blob)
    return out_path


def main(argv):
    parser = argparse.ArgumentParser(description="Build the wayland-hello native IPK")
    parser.add_argument("--binary", required=True, help="ELF to place at wayland-hello")
    parser.add_argument(
        "--out",
        default=os.path.join(ROOT, "build", "ipk", APP_ID + "_" + VERSION + "_" + ARCH + ".ipk"),
    )
    parser.add_argument(
        "--lifecycle",
        choices=("omit", "1", "2"),
        default="omit",
        help="nativeLifeCycleInterfaceVersion; omit leaves the field out (v1)",
    )
    parser.add_argument(
        "--default-window-type",
        default=None,
        help="appinfo.json defaultWindowType (card, or overlay when --lifecycle 2)",
    )
    parser.add_argument(
        "--heartbeat-ms",
        type=int,
        default=0,
        help="write heartbeat-ms next to the ELF; the client reads it on SAM launch (0 omits it)",
    )
    parser.add_argument(
        "--menu",
        action="store_true",
        help="package a menu sidecar so SAM launch selects --menu instead of --demo",
    )
    args = parser.parse_args(argv)
    if args.heartbeat_ms and not 100 <= args.heartbeat_ms <= 60000:
        raise SystemExit("--heartbeat-ms must be 0 or 100..60000")
    path = build_ipk(
        args.binary,
        args.out,
        lifecycle=args.lifecycle,
        default_window_type=args.default_window_type,
        heartbeat_ms=args.heartbeat_ms,
        menu=args.menu,
    )
    print(path)
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))

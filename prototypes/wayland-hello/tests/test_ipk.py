#!/usr/bin/env python3
"""IPK layout checks. Builds a package around a stub binary. No TV, no LG SDK."""

import io
import json
import os
import shutil
import subprocess
import sys
import tarfile
import tempfile

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
sys.path.insert(0, os.path.join(ROOT, "scripts"))

from build_ipk import APP_ID, VERSION, build_ipk  # noqa: E402

failed = 0


def check(name, cond, detail=""):
    global failed
    if cond:
        print("ok  ", name)
    else:
        failed += 1
        print("FAIL", name, detail)


def parse_ar(blob):
    check("ar magic", blob.startswith(b"!<arch>\n"), blob[:16])
    off = 8
    members = []
    while off < len(blob):
        header = blob[off:off + 60]
        check("ar header length", len(header) == 60, str(len(header)))
        if len(header) != 60:
            break
        name = header[0:16].decode("ascii").strip()
        size = int(header[48:58].decode("ascii").strip())
        magic = header[58:60]
        check("ar header magic " + name, magic == b"`\n", repr(magic))
        start = off + 60
        data = blob[start:start + size]
        check("ar member size " + name, len(data) == size, str(len(data)))
        members.append((name, data))
        off = start + size
        if size % 2:
            off += 1
    return members


class Archive(object):
    def __init__(self, gz_bytes):
        self._tar = tarfile.open(fileobj=io.BytesIO(gz_bytes), mode="r:gz")

    def names(self):
        return [m.name for m in self._tar.getmembers()]

    def files(self):
        return sorted(m.name for m in self._tar.getmembers() if m.isfile())

    def read(self, name):
        return self._tar.extractfile(name).read()

    def member(self, name):
        return self._tar.getmember(name)


def main():
    stub = b"\x7fELF-wayland-hello-stub\n"
    tmp = tempfile.mkdtemp(prefix="wh-ipk-")
    try:
        binary = os.path.join(tmp, "wayland-hello")
        with open(binary, "wb") as fh:
            fh.write(stub)
        out_a = os.path.join(tmp, "a.ipk")
        out_b = os.path.join(tmp, "b.ipk")
        build_ipk(binary, out_a)
        build_ipk(binary, out_b)
        with open(out_a, "rb") as fh:
            blob = fh.read()
        with open(out_b, "rb") as fh:
            again = fh.read()
        check("ipk is reproducible", blob == again, "%d vs %d" % (len(blob), len(again)))

        members = parse_ar(blob)
        names = [name for name, _data in members]
        check("ar member order", names == ["debian-binary", "control.tar.gz", "data.tar.gz"], str(names))
        raw_names = []
        scan = 8
        while scan + 60 <= len(blob):
            raw_names.append(blob[scan:scan + 16])
            size = int(blob[scan + 48:scan + 58].decode("ascii").strip())
            scan += 60 + size + (size % 2)
        check("ar names are space-padded and have no GNU slash",
              raw_names == [b"debian-binary   ", b"control.tar.gz  ", b"data.tar.gz     "],
              repr(raw_names))
        by_name = dict(members)
        check("debian-binary is 2.0", by_name.get("debian-binary") == b"2.0\n", repr(by_name.get("debian-binary")))

        control_tar = Archive(by_name["control.tar.gz"])
        check("control archive has control", control_tar.names() == ["control"], str(control_tar.names()))
        control = control_tar.read("control").decode("utf-8")
        for line in (
            "Package: " + APP_ID,
            "Version: " + VERSION,
            "Architecture: arm",
            "webOS-Package-Format-Version: 2",
            "Section: misc",
            "Priority: optional",
        ):
            check("control has " + line, line in control, control)

        data_tar = Archive(by_name["data.tar.gz"])
        prefix = "usr/palm/applications/" + APP_ID + "/"
        expect = sorted([
            prefix + "appinfo.json",
            prefix + "icon.png",
            prefix + "wayland-hello",
            prefix + "wayland-hello-launch.sh",
        ])
        check("data paths", data_tar.files() == expect, str(data_tar.files()))
        check("ipk does not ship sysbus members",
              not any("sysbus" in name for name in data_tar.files()), str(data_tar.files()))
        info = json.loads(data_tar.read(prefix + "appinfo.json").decode("utf-8"))
        check("appinfo id", info.get("id") == APP_ID, str(info))
        check("appinfo type native", info.get("type") == "native", str(info))
        check("appinfo main is the ELF", info.get("main") == "wayland-hello", str(info))
        check("appinfo icon", info.get("icon") == "icon.png", str(info))
        check("default window type is card", info.get("defaultWindowType") == "card", str(info))
        check("no splash on launch", info.get("noSplashOnLaunch") is True, str(info))
        check("lifecycle field omitted", "nativeLifeCycleInterfaceVersion" not in info, str(info))
        check("requiredPermissions is application.operation",
              info.get("requiredPermissions") == ["application.operation"], str(info))
        icon = data_tar.read(prefix + "icon.png")
        check("icon is a png", icon.startswith(b"\x89PNG\r\n\x1a\n"), repr(icon[:8]))
        packed = data_tar.read(prefix + "wayland-hello")
        check("binary bytes are unchanged", packed == stub, "%d" % len(packed))
        launch = data_tar.read(prefix + "wayland-hello-launch.sh").decode("utf-8")
        launch_info = data_tar.member(prefix + "wayland-hello-launch.sh")
        bin_info = data_tar.member(prefix + "wayland-hello")
        check("launcher is executable", launch_info.mode & 0o111 == 0o111, oct(launch_info.mode))
        check("binary is executable", bin_info.mode & 0o111 == 0o111, oct(bin_info.mode))
        for needle in (
            "Not SAM's main",
            "/tmp/wh6.log",
            "----- environment -----",
            'exec "$APP_DIR/wayland-hello"',
        ):
            check("launcher contains " + needle, needle in launch, "")
        for needle in ("ls-control", "scan-services", "scan-volatile-dirs", "__EXE_NAME__"):
            check("launcher does not call " + needle, needle not in launch, "")
        script = os.path.join(tmp, "launch.sh")
        with open(script, "w", encoding="utf-8") as fh:
            fh.write(launch)
        syntax = subprocess.run(["sh", "-n", script], capture_output=True, text=True)
        check("launcher passes sh -n", syntax.returncode == 0, syntax.stderr)

        app = os.path.join(tmp, "app")
        os.mkdir(app)
        for name in ("appinfo.json", "wayland-hello-launch.sh"):
            shutil.copy(os.path.join(ROOT, "packaging", name), os.path.join(app, name))
        stub_bin = os.path.join(app, "wayland-hello")
        with open(stub_bin, "w", encoding="utf-8") as fh:
            fh.write("#!/bin/sh\nprintf '%s\\n' \"$*\" > /tmp/wh6-args.$$\n")
        os.chmod(stub_bin, 0o755)
        os.chmod(os.path.join(app, "wayland-hello-launch.sh"), 0o755)
        log = "/tmp/wh6.log"
        if os.path.exists(log):
            os.remove(log)
        env = os.environ.copy()
        env["APPID"] = "org.va7dimar.fromenv"
        env.pop("APP_ID", None)
        payload = '{"event":"launch","appId":"org.va7dimar.fromjson","interfaceVersion":2,"interfaceMethod":"registerApp"}'
        run = subprocess.run(
            ["sh", os.path.join(app, "wayland-hello-launch.sh"), payload],
            cwd=app, env=env, capture_output=True, text=True,
        )
        check("launcher exits 0", run.returncode == 0, run.stderr)
        with open(log, encoding="utf-8", errors="replace") as fh:
            logged = fh.read()
        check("log dumps env", "----- environment -----" in logged and "APPID=org.va7dimar.fromenv" in logged
              and payload in logged, logged[-800:])
        check("launcher does not install ls2",
              "----- ls2 -----" not in logged and "ls2: root=" not in logged
              and "ls-control" not in logged, logged)
        arg_files = [n for n in os.listdir("/tmp") if n.startswith("wh6-args.")]
        check("client was exec'd", len(arg_files) == 1, str(arg_files))
        if arg_files:
            with open(os.path.join("/tmp", arg_files[0]), encoding="utf-8") as fh:
                args = fh.read()
            os.remove(os.path.join("/tmp", arg_files[0]))
            check("exec keeps the SAM json argv", args.strip() == payload, args)
            check("launcher does not invent client flags",
                  "--demo" not in args and "--luna-register" not in args
                  and "--webos-shell" not in args and "--menu" not in args, args)
        if os.path.exists(log):
            os.remove(log)

        env["WAYLAND_HELLO_LS2_ROOT"] = os.path.join(tmp, "luna-dev")
        os.makedirs(env["WAYLAND_HELLO_LS2_ROOT"])
        run = subprocess.run(
            ["sh", os.path.join(app, "wayland-hello-launch.sh"), payload],
            cwd=app, env=env, capture_output=True, text=True,
        )
        check("launcher ignores a writable luna root", run.returncode == 0, run.stderr)
        check("no role files under the luna root",
              os.listdir(env["WAYLAND_HELLO_LS2_ROOT"]) == [], env["WAYLAND_HELLO_LS2_ROOT"])
        for name in os.listdir("/tmp"):
            if name.startswith("wh6-args."):
                os.remove(os.path.join("/tmp", name))
        if os.path.exists(log):
            os.remove(log)

        out_v2 = os.path.join(tmp, "v2.ipk")
        build_ipk(binary, out_v2, lifecycle="2")
        with open(out_v2, "rb") as fh:
            v2_members = dict(parse_ar(fh.read()))
        v2_data = Archive(v2_members["data.tar.gz"])
        v2_info = json.loads(v2_data.read(prefix + "appinfo.json").decode("utf-8"))
        v2_files = v2_data.files()
        check("lifecycle 2 ipk has no sysbus members",
              not any("sysbus" in name for name in v2_files), str(v2_files))
        check("lifecycle 2 main stays the ELF", v2_info.get("main") == "wayland-hello", str(v2_info))
        check("lifecycle 2 is written", v2_info.get("nativeLifeCycleInterfaceVersion") == 2, str(v2_info))
        check("lifecycle 2 defaults to overlay", v2_info.get("defaultWindowType") == "overlay", str(v2_info))
        check("splash stays off when flags change", v2_info.get("noSplashOnLaunch") is True, str(v2_info))
        check("lifecycle 2 keeps requiredPermissions",
              v2_info.get("requiredPermissions") == ["application.operation"], str(v2_info))

        out_hb = os.path.join(tmp, "hb.ipk")
        build_ipk(binary, out_hb, lifecycle="2", heartbeat_ms=1000)
        with open(out_hb, "rb") as fh:
            hb_members = dict(parse_ar(fh.read()))
        hb_data = Archive(hb_members["data.tar.gz"])
        check("heartbeat sidecar is packaged next to the ELF",
              hb_data.read(prefix + "heartbeat-ms") == b"1000\n", "")

        out_menu = os.path.join(tmp, "menu.ipk")
        build_ipk(binary, out_menu, menu=True)
        with open(out_menu, "rb") as fh:
            menu_members = dict(parse_ar(fh.read()))
        menu_data = Archive(menu_members["data.tar.gz"])
        check("menu IPK ships a sidecar next to the ELF",
              menu_data.read(prefix + "menu") == b"1\n", "")
        check("default IPK does not ship a menu sidecar",
              prefix + "menu" not in data_tar.files(), str(data_tar.files()))
        menu_launch = menu_data.read(prefix + "wayland-hello-launch.sh").decode("utf-8")
        check("menu IPK launcher still execs the ELF with argv",
              'exec "$APP_DIR/wayland-hello"' in menu_launch and "--menu" not in menu_launch,
              menu_launch[-400:])

        out_pa = os.path.join(tmp, "photo-a.ipk")
        build_ipk(binary, out_pa, photo_frame="A")
        with open(out_pa, "rb") as fh:
            pa_members = dict(parse_ar(fh.read()))
        pa_data = Archive(pa_members["data.tar.gz"])
        pa_info = json.loads(pa_data.read(prefix + "appinfo.json").decode("utf-8"))
        check("photo-frame A sidecar is packaged next to the ELF",
              pa_data.read(prefix + "photo-frame") == b"A\n", "")
        check("photo-frame A main stays the ELF", pa_info.get("main") == "wayland-hello", str(pa_info))
        check("photo-frame A is lifecycle 2", pa_info.get("nativeLifeCycleInterfaceVersion") == 2, str(pa_info))
        check("photo-frame A defaultWindowType is card", pa_info.get("defaultWindowType") == "card", str(pa_info))
        check("photo-frame A has no sysbus members",
              not any("sysbus" in name for name in pa_data.files()), str(pa_data.files()))
        check("default IPK does not ship a photo-frame sidecar",
              prefix + "photo-frame" not in data_tar.files(), str(data_tar.files()))

        out_pb = os.path.join(tmp, "photo-b.ipk")
        build_ipk(binary, out_pb, photo_frame="B")
        with open(out_pb, "rb") as fh:
            pb_members = dict(parse_ar(fh.read()))
        pb_data = Archive(pb_members["data.tar.gz"])
        pb_info = json.loads(pb_data.read(prefix + "appinfo.json").decode("utf-8"))
        check("photo-frame B sidecar is packaged next to the ELF",
              pb_data.read(prefix + "photo-frame") == b"B\n", "")
        check("photo-frame B main stays the ELF", pb_info.get("main") == "wayland-hello", str(pb_info))
        check("photo-frame B is lifecycle 2", pb_info.get("nativeLifeCycleInterfaceVersion") == 2, str(pb_info))
        check("photo-frame B defaultWindowType is overlay", pb_info.get("defaultWindowType") == "overlay", str(pb_info))

        if shutil.which("ar") and shutil.which("tar"):
            listing = subprocess.run(["ar", "t", out_a], capture_output=True, text=True)
            check("system ar lists the three members",
                  listing.returncode == 0 and listing.stdout.split() == names,
                  listing.stdout + listing.stderr)
    finally:
        shutil.rmtree(tmp)
    print("%d failed" % failed)
    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(main())

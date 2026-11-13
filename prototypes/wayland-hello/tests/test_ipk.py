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
        info = json.loads(data_tar.read(prefix + "appinfo.json").decode("utf-8"))
        check("appinfo id", info.get("id") == APP_ID, str(info))
        check("appinfo type native", info.get("type") == "native", str(info))
        check("appinfo main is the launcher", info.get("main") == "wayland-hello-launch.sh", str(info))
        check("appinfo icon", info.get("icon") == "icon.png", str(info))
        check("default window type is card", info.get("defaultWindowType") == "card", str(info))
        check("no splash on launch", info.get("noSplashOnLaunch") is True, str(info))
        check("lifecycle field omitted", "nativeLifeCycleInterfaceVersion" not in info, str(info))
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
            "--demo",
            '--app-id "$APPID_VALUE"',
            "/tmp/wh6.log",
            "----- environment -----",
        ):
            check("launcher contains " + needle, needle in launch, "")
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
        env.pop("XDG_RUNTIME_DIR", None)
        env.pop("WAYLAND_DISPLAY", None)
        payload = '{"event":"launch","appId":"org.va7dimar.fromjson","parameters":{}}'
        run = subprocess.run(
            ["sh", os.path.join(app, "wayland-hello-launch.sh"), payload],
            cwd=app, env=env, capture_output=True, text=True,
        )
        check("launcher exits 0", run.returncode == 0, run.stderr)
        with open(log, encoding="utf-8", errors="replace") as fh:
            logged = fh.read()
        check("log dumps env", "----- environment -----" in logged and "APPID=org.va7dimar.fromenv" in logged
              and "XDG_RUNTIME_DIR=/tmp/xdg" in logged and "WAYLAND_DISPLAY=wayland-0" in logged, logged[-600:])
        check("APPID wins over argv appId",
              "app_id=org.va7dimar.fromenv" in logged and "app_id_source=APPID" in logged
              and payload in logged, logged[:800])
        arg_files = [n for n in os.listdir("/tmp") if n.startswith("wh6-args.")]
        check("client was exec'd", len(arg_files) == 1, str(arg_files))
        if arg_files:
            with open(os.path.join("/tmp", arg_files[0]), encoding="utf-8") as fh:
                args = fh.read()
            os.remove(os.path.join("/tmp", arg_files[0]))
            check("exec args",
                  args.strip() == "--demo --app-id org.va7dimar.fromenv",
                  args)
            check("launcher does not pass webos-shell", "--webos-shell" not in args, args)
            check("default launcher does not register", "--luna-register" not in args, args)
        if os.path.exists(log):
            os.remove(log)

        env.pop("APPID", None)
        run = subprocess.run(
            ["sh", os.path.join(app, "wayland-hello-launch.sh"),
             '{"event":"launch","appId":"org.va7dimar.fromjson","parameters":{}}'],
            cwd=app, env=env, capture_output=True, text=True,
        )
        check("json appId used when APPID is unset", run.returncode == 0, run.stderr)
        with open(log, encoding="utf-8", errors="replace") as fh:
            logged = fh.read()
        check("argv1.appId is the source",
              "app_id=org.va7dimar.fromjson" in logged and "app_id_source=argv1.appId" in logged, logged[:500])
        for name in os.listdir("/tmp"):
            if name.startswith("wh6-args."):
                os.remove(os.path.join("/tmp", name))
        if os.path.exists(log):
            os.remove(log)

        env["XDG_RUNTIME_DIR"] = "/tmp/keep-xdg"
        env["WAYLAND_DISPLAY"] = "wayland-9"
        run = subprocess.run(
            ["sh", os.path.join(app, "wayland-hello-launch.sh"), '{"event":"launch","parameters":{}}'],
            cwd=app, env=env, capture_output=True, text=True,
        )
        check("launcher falls back to appinfo id", run.returncode == 0, run.stderr)
        with open(log, encoding="utf-8", errors="replace") as fh:
            logged = fh.read()
        check("appinfo id when argv has no appId",
              "app_id=org.va7dimar.waylandhello" in logged and "app_id_source=appinfo.json" in logged, logged[:500])
        check("preset wayland env is kept",
              "XDG_RUNTIME_DIR=/tmp/keep-xdg" in logged and "WAYLAND_DISPLAY=wayland-9" in logged, logged[-500:])
        for name in os.listdir("/tmp"):
            if name.startswith("wh6-args."):
                os.remove(os.path.join("/tmp", name))
        if os.path.exists(log):
            os.remove(log)

        out_v2 = os.path.join(tmp, "v2.ipk")
        build_ipk(binary, out_v2, lifecycle="2", default_window_type="overlay")
        with open(out_v2, "rb") as fh:
            v2_members = dict(parse_ar(fh.read()))
        v2_info = json.loads(Archive(v2_members["data.tar.gz"]).read(prefix + "appinfo.json").decode("utf-8"))
        with open(os.path.join(app, "appinfo.json"), "w", encoding="utf-8") as fh:
            json.dump(v2_info, fh)
        with open(os.path.join(app, "heartbeat-ms"), "w", encoding="utf-8") as fh:
            fh.write("1000\n")
        run = subprocess.run(
            ["sh", os.path.join(app, "wayland-hello-launch.sh")],
            cwd=app, env=env, capture_output=True, text=True,
        )
        check("lifecycle 2 launcher exits 0", run.returncode == 0, run.stderr)
        arg_files = [n for n in os.listdir("/tmp") if n.startswith("wh6-args.")]
        check("lifecycle 2 launcher passes luna and heartbeat", len(arg_files) == 1, str(arg_files))
        if arg_files:
            with open(os.path.join("/tmp", arg_files[0]), encoding="utf-8") as fh:
                args = fh.read().strip()
            os.remove(os.path.join("/tmp", arg_files[0]))
            check("lifecycle 2 exec args",
                  args == "--demo --luna-register --heartbeat-ms 1000 --app-id org.va7dimar.waylandhello",
                  args)
        if os.path.exists(log):
            os.remove(log)

        check("lifecycle 2 is written", v2_info.get("nativeLifeCycleInterfaceVersion") == 2, str(v2_info))
        check("window type flag is written", v2_info.get("defaultWindowType") == "overlay", str(v2_info))
        check("splash stays off when flags change", v2_info.get("noSplashOnLaunch") is True, str(v2_info))

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

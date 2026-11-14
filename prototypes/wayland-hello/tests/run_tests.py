#!/usr/bin/env python3
"""OFF-TV smoke tests for wayland-hello. Usage: run_tests.py PATH_TO_HOST_BINARY

One or two checks per mode: option parsing, the mock-compositor protocol path,
input, webOS shell, luna registration, the menu, EGL fallback and linkage.
Never touches a real compositor: XDG_RUNTIME_DIR/WAYLAND_DISPLAY are always
forced to the temp mock socket. Edge cases were trimmed on purpose; add a check
when a bug shows up on the TV, not for every branch.
"""
import json, os, shutil, subprocess, sys, tempfile, time

BIN = os.path.abspath(sys.argv[1])
HERE = os.path.dirname(os.path.abspath(__file__))
MOCK = os.path.join(HERE, "mock_compositor.py")
LAUNCH = ('{"event":"launch","appId":"org.va7dimar.waylandhello",'
          '"interfaceVersion":2,"interfaceMethod":"registerApp"}')
results = []


def check(name, cond, detail=""):
    results.append((name, bool(cond), detail))
    print(("PASS " if cond else "FAIL ") + name + ("" if cond else "  :: " + detail))


def run(args, env_extra=None, timeout=40):
    env = {"PATH": os.environ.get("PATH", "/usr/bin:/bin"), "WAYLAND_HELLO_LOG": "-"}
    env.update(env_extra or {})
    t0 = time.monotonic()
    p = subprocess.run([BIN] + args, env=env, capture_output=True, text=True, timeout=timeout)
    return p.returncode, p.stdout, p.stderr, time.monotonic() - t0


def with_mock(mock_args, client_args, timeout=40, env_extra=None):
    d = tempfile.mkdtemp(prefix="wlh-test-")
    sock, log = os.path.join(d, "wayland-mock"), os.path.join(d, "log.jsonl")
    m = subprocess.Popen([sys.executable, "-I", MOCK, sock, log] + mock_args)
    for _ in range(100):
        if os.path.exists(sock):
            break
        time.sleep(0.05)
    try:
        env = {"XDG_RUNTIME_DIR": d, "WAYLAND_DISPLAY": "wayland-mock"}
        env.update(env_extra or {})
        r = run(client_args, env, timeout)
    finally:
        try:
            m.wait(timeout=3)
        except subprocess.TimeoutExpired:
            m.kill(); m.wait()
    with open(log) as f:
        events = [json.loads(l) for l in f if l.strip()]
    return r, events


def reqs(events):
    return [(e.get("iface"), e.get("req")) for e in events if "req" in e]


def last_pixels(events):
    pix = [e for e in events if e.get("event") == "pixels"]
    return pix[-1] if pix else {}


def build_so(src_text, dest):
    src = dest + ".c"
    with open(src, "w") as f:
        f.write(src_text)
    p = subprocess.run(["gcc", "-shared", "-fPIC", "-o", dest, src], capture_output=True, text=True, timeout=30)
    if p.returncode != 0:
        raise RuntimeError(p.stderr)


def webos_fixture():
    """Build a fake libwayland-webos-client with the OSE opcode layout."""
    hdr = ("struct wl_message { const char *name; const char *signature; const void *types; };\n"
           "struct wl_interface { const char *name; int version; int method_count;"
           " const struct wl_message *methods; int event_count; const struct wl_message *events; };\n")
    shell = [("get_system_pip", ""), ("get_shell_surface", "no")]
    surface = [("set_location_hint", "u"), ("set_state", "u"), ("set_property", "ss"), ("set_key_mask", "u")]
    events = [("state_changed", "u"), ("position_changed", "ii"), ("close", ""),
              ("exposed", "a"), ("state_about_to_change", "u")]

    def arr(name, items):
        return "static const struct wl_message %s[] = {%s};\n" % (
            name, "".join('{"%s", "%s", 0},' % it for it in items))

    src = hdr + arr("shell_m", shell) + arr("surf_m", surface) + arr("surf_e", events) + (
        'const struct wl_interface wl_webos_shell_interface = {"wl_webos_shell", 1, %d, shell_m, 0, 0};\n'
        'const struct wl_interface wl_webos_shell_surface_interface = '
        '{"wl_webos_shell_surface", 1, %d, surf_m, %d, surf_e};\n') % (len(shell), len(surface), len(events))
    d = tempfile.mkdtemp(prefix="wlh-so-")
    build_so(src, os.path.join(d, "libwayland-webos-client.so.1"))
    return d


def luna_fixture():
    d = tempfile.mkdtemp(prefix="wlh-luna-")
    so = os.path.join(d, "libluna-service2.so.3")
    built = subprocess.run(["gcc", "-shared", "-fPIC", "-std=c99", "-o", so, os.path.join(HERE, "luna_fixture.c")],
                           capture_output=True, text=True)
    check("luna fixture builds", built.returncode == 0, built.stderr)
    if built.returncode != 0:
        return None
    os.symlink("libluna-service2.so.3", os.path.join(d, "libglib-2.0.so.0"))
    return d


def parser_tests():
    rc, out, _, _ = run(["--parse-only"])
    check("defaults", rc == 0 and "runtime_dir=/tmp/xdg" in out and "display=wayland-0" in out
          and "duration_s=10" in out and "size=640x360" in out, out)
    for bad in (["--duration", "0"], ["--size", "4000x10"], ["--display", "../x"], ["--bogus"]):
        rc, _, _, _ = run(["--parse-only"] + bad)
        check("reject %s" % " ".join(bad), rc == 2, "rc=%d" % rc)
    rc, out, _, _ = run(["--version"])
    check("version 0.9", rc == 0 and "0.9-prototype" in out, out)
    rc, out, err, _ = run([LAUNCH, "--parse-only"])
    check("sam lifecycle-2 json selects overlay, luna and 90s cap",
          rc == 0 and "sam_lifecycle2=1" in out and "luna_register=1" in out
          and "window_type=_WEBOS_WINDOW_TYPE_OVERLAY" in out and "duration_s=90" in out, out + err)
    side = tempfile.mkdtemp(prefix="wlh-menu-side-")
    try:
        bin2 = os.path.join(side, "wayland-hello")
        shutil.copy(BIN, bin2)
        with open(os.path.join(side, "menu"), "w", encoding="ascii") as fh:
            fh.write("1\n")
        p = subprocess.run([bin2, LAUNCH, "--parse-only"], env={"PATH": os.environ.get("PATH", "/usr/bin:/bin")},
                           capture_output=True, text=True, timeout=40)
        check("menu sidecar selects menu on a sam launch",
              p.returncode == 0 and "menu=1" in p.stdout and "demo=0" in p.stdout, p.stdout + p.stderr)
    finally:
        shutil.rmtree(side)


def mock_tests():
    (rc, out, err, dt), ev = with_mock([], ["--dry-run", "--duration", "5"])
    check("dry-run lists globals and binds nothing",
          rc == 0 and "interface=wl_shell" in out and ("wl_registry", "bind") not in reqs(ev), out)

    (rc, out, err, dt), ev = with_mock(["--configure", "5000x3000"], ["--duration", "2"])
    r = reqs(ev)
    check("surface mode draws and exits on its deadline", rc == 0 and 1.5 < dt < 4.5, "rc=%d dt=%.2f %s" % (rc, dt, err[-300:]))
    check("surface mode sends the core requests",
          all(q in r for q in [("wl_shell_surface", "set_fullscreen"), ("wl_shm_pool", "create_buffer"),
                               ("wl_surface", "attach"), ("wl_surface", "commit")]), str(r))
    bufs = [e["args"] for e in ev if e.get("req") == "create_buffer"]
    check("oversized configure clamped to 1920x1080", any(b[2] == 1920 and b[3] == 1080 for b in bufs), str(bufs))

    (rc, out, err, dt), ev = with_mock(["--no-shell"], ["--duration", "5"])
    check("no wl_shell fails closed rc=5", rc == 5, "rc=%d %s" % (rc, err))
    (rc, out, err, dt), ev = with_mock(["--stall"], ["--dry-run", "--duration", "2"])
    check("stalled compositor still exits", rc != 0 and dt < 5.5, "rc=%d dt=%.2f" % (rc, dt))


def input_tests():
    (rc, out, err, dt), ev = with_mock(["--seats", "1", "--input-script", "p105"], ["--input", "--duration", "2"])
    px = last_pixels(ev)
    check("arrow moves the square",
          rc == 0 and "keycode raw=105 state=pressed" in out and "input: model square x=60" in err
          and px.get("80,120") == 0xff00ff00, err[-400:])
    (rc, out, err, dt), ev = with_mock(["--seats", "1", "--input-script", "p158"], ["--input", "--duration", "6"])
    check("BACK exits", rc == 0 and dt < 4.0 and "exiting (back-key)" in err, "rc=%d dt=%.2f" % (rc, dt))
    (rc, out, err, dt), ev = with_mock([], ["--input", "--duration", "3"])
    check("no wl_seat fails closed rc=8", rc == 8, "rc=%d %s" % (rc, err))
    (rc, out, err, dt), ev = with_mock(["--seats", "1", "--input-script", "p105", "--no-release"],
                                       ["--demo", "--duration", "2"])
    check("demo paints into a spare buffer when none are released",
          rc == 0 and "buf: spare gen=2" in err and last_pixels(ev).get("80,120") == 0xff00ff00, err[-500:])


def webos_tests(ose):
    (rc, out, err, dt), ev = with_mock(["--webos"], ["--webos-shell", "--duration", "2"],
                                       env_extra={"WAYLAND_HELLO_LIB_DIR": ose})
    seq = [(e.get("req"), e.get("args")) for e in ev if e.get("iface") == "wl_webos_shell_surface"]
    check("webos shell sets appId then fullscreen state 3",
          rc == 0 and ("op2", ["appId", "wayland-hello-prototype"]) in seq and ("op1", [3]) in seq, str(seq))
    (rc, out, err, dt), ev = with_mock(["--webos"], ["--webos-shell", "--window-type", "_WEBOS_WINDOW_TYPE_OVERLAY", "--duration", "2"],
                                       env_extra={"WAYLAND_HELLO_LIB_DIR": ose})
    seq = [(e.get("req"), e.get("args")) for e in ev if e.get("iface") == "wl_webos_shell_surface"]
    check("overlay window type is sent", rc == 0 and ("op2", ["_WEBOS_WINDOW_TYPE", "_WEBOS_WINDOW_TYPE_OVERLAY"]) in seq, str(seq))
    (rc, out, err, dt), ev = with_mock(["--webos"], ["--webos-shell", "--duration", "2"],
                                       env_extra={"WAYLAND_HELLO_LIB_DIR": tempfile.mkdtemp()})
    check("missing webos library fails closed rc=9", rc == 9 and "Failing closed" in err, err[-300:])


def luna_tests(ose):
    fix = luna_fixture()
    if not fix:
        return
    (rc, out, err, dt), ev = with_mock([], ["--luna-register", "--duration", "2"],
                                       env_extra={"WAYLAND_HELLO_LIB_DIR": fix})
    check("luna registers and exits on close",
          rc == 0 and "luna: event=registered" in err and "exiting (luna-close)" in err, err[-600:])
    (rc, out, err, dt), ev = with_mock([], ["--luna-register", "--duration", "4"],
                                       env_extra={"WAYLAND_HELLO_LIB_DIR": fix, "WAYLAND_HELLO_LUNA_SCRIPT": "reject"})
    check("rejected registerApp fails closed before a surface",
          rc == 10 and not any(e.get("req") == "bind" for e in ev), "rc=%d %s" % (rc, err[-400:]))

    os.symlink(os.path.join(ose, "libwayland-webos-client.so.1"), os.path.join(fix, "libwayland-webos-client.so.1"))
    (rc, out, err, dt), ev = with_mock(["--webos", "--seats", "1", "--input-script", "L"], [LAUNCH, "--duration", "6"],
                                       env_extra={"WAYLAND_HELLO_LIB_DIR": fix, "WAYLAND_HELLO_LUNA_SCRIPT": "relaunch-only"})
    check("sam lifecycle-2 overlay stays up past keyboard leave",
          rc == 0 and dt > 5.0 and "persist: restore-foreground event=relaunch" in err
          and "keyboard leave" in err and "exiting (deadline)" in err, "rc=%d dt=%.2f %s" % (rc, dt, err[-600:]))

    logf = os.path.join(tempfile.mkdtemp(prefix="wlh-wh6-"), "wh6.log")
    with open(logf, "w", encoding="utf-8") as fh:
        fh.write("luna: no registerApp reply after 2000ms\ninfo: exiting (deadline)\n"
                 "summary: commits=1 luna_replies=0 luna_polls=4\n"
                 "persist: alive t=5000 enter=1 leave=0 restores=1 luna_replies=2\n")
    p = subprocess.run([sys.executable, "-I", os.path.join(os.path.dirname(HERE), "scripts", "classify_wh6_log.py"), logf],
                       capture_output=True, text=True)
    check("wh6 log classifier runs", p.returncode == 0 and "replies=0" in p.stdout and "persist=yes" in p.stdout,
          p.stdout + p.stderr)


FOCUS, UNFOCUS = 0xffd4a017, 0xff2a3a55


def menu_tests():
    (rc, out, err, dt), ev = with_mock(["--seats", "1"], ["--menu", "--duration", "2"])
    px = last_pixels(ev)
    check("menu starts on Demo", rc == 0 and px.get("50,147") == FOCUS and px.get("243,147") == UNFOCUS, str(px))
    (rc, out, err, dt), ev = with_mock(["--seats", "1", "--input-script", "p106"], ["--menu", "--duration", "2"])
    check("RIGHT moves focus to About", rc == 0 and last_pixels(ev).get("243,147") == FOCUS, err[-400:])
    (rc, out, err, dt), ev = with_mock(["--seats", "1", "--input-script", "p105,p352"], ["--menu", "--duration", "6"])
    check("OK on Exit exits", rc == 0 and dt < 4.0 and "exiting (menu-exit)" in err, "rc=%d dt=%.2f" % (rc, dt))


def egl_tests():
    (rc, out, err, dt), ev = with_mock([], ["--egl", "--duration", "2"], env_extra={"WAYLAND_HELLO_LIB_DIR": tempfile.mkdtemp()})
    check("missing EGL falls back to shm",
          rc == 0 and "falling back to shm" in err and any(e.get("req") == "create_buffer" for e in ev), err[-400:])


def linkage_tests():
    blob = open(BIN, "rb").read()
    check("binary opens no /dev/input, /dev/fb or /dev/dri", not any(s in blob for s in (b"/dev/input", b"/dev/fb", b"/dev/dri")))
    p = subprocess.run(["readelf", "-d", BIN], capture_output=True, text=True)
    needed = [l.split("[", 1)[1].split("]", 1)[0] for l in p.stdout.splitlines() if "(NEEDED)" in l and "[" in l]
    check("NEEDED is libc/libdl/librt only", needed and set(needed) <= {"libc.so.6", "libdl.so.2", "librt.so.1"}, str(needed))


if __name__ == "__main__":
    parser_tests()
    mock_tests()
    input_tests()
    ose = webos_fixture()
    webos_tests(ose)
    luna_tests(ose)
    menu_tests()
    egl_tests()
    linkage_tests()
    n_fail = sum(1 for _, ok, _ in results if not ok)
    print("\n%d tests, %d failed" % (len(results), n_fail))
    sys.exit(1 if n_fail else 0)

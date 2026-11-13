#!/usr/bin/env python3
"""OFF-TV tests for wayland-hello. Usage: run_tests.py PATH_TO_HOST_BINARY

Runs (1) option-parser tests via --parse-only, (2) mock-compositor protocol
tests over a private socket in a temp dir. Never touches a real compositor:
XDG_RUNTIME_DIR/WAYLAND_DISPLAY are always forced to the temp mock socket.
"""
import json, os, subprocess, sys, tempfile, time

BIN = os.path.abspath(sys.argv[1])
HERE = os.path.dirname(os.path.abspath(__file__))
MOCK = os.path.join(HERE, "mock_compositor.py")
results = []


def check(name, cond, detail=""):
    results.append((name, bool(cond), detail))
    print(("PASS " if cond else "FAIL ") + name + ("" if cond else "  :: " + detail))


def run(args, env_extra=None, timeout=40):
    env = {"PATH": os.environ.get("PATH", "/usr/bin:/bin")}
    env.update(env_extra or {})
    t0 = time.monotonic()
    p = subprocess.run([BIN] + args, env=env, capture_output=True, text=True, timeout=timeout)
    return p.returncode, p.stdout, p.stderr, time.monotonic() - t0


def parser_tests():
    rc, out, _, _ = run(["--parse-only"])
    check("defaults runtime_dir=/tmp/xdg", rc == 0 and "runtime_dir=/tmp/xdg" in out, out)
    check("defaults display=wayland-0", "display=wayland-0" in out, out)
    check("defaults duration=10", "duration_s=10" in out, out)
    check("defaults fullscreen=1 size=640x360", "fullscreen=1" in out and "size=640x360" in out, out)
    rc, out, _, _ = run(["--parse-only"], {"XDG_RUNTIME_DIR": "/run/x", "WAYLAND_DISPLAY": "w1"})
    check("env overrides", "runtime_dir=/run/x" in out and "display=w1" in out, out)
    rc, out, _, _ = run(["--parse-only", "--runtime-dir", "/a", "--display", "b"], {"XDG_RUNTIME_DIR": "/run/x"})
    check("cli overrides env", "runtime_dir=/a" in out and "display=b" in out, out)
    for bad in (["--duration", "0"], ["--duration", "31"], ["--duration", "abc"], ["--duration"],
                ["--size", "4000x10"], ["--size", "0x10"], ["--size", "10"], ["--color", "zzzzzz"],
                ["--display", "../x"], ["--runtime-dir", "rel"], ["--bogus"]):
        rc, _, _, _ = run(["--parse-only"] + bad)
        check("reject %s" % " ".join(bad), rc == 2, "rc=%d" % rc)
    rc, _, _, _ = run(["--parse-only"], {"WAYLAND_DISPLAY": "a/b"})
    check("reject env WAYLAND_DISPLAY with slash", rc == 2, "rc=%d" % rc)
    rc, out, _, _ = run(["--parse-only", "--duration", "30", "--size", "1920x1080", "--max-size", "800x600"])
    check("size clamped to max-size", rc == 0 and "size=800x600" in out and "duration_s=30" in out, out)
    rc, out, _, _ = run(["--help"])
    check("--help exit 0", rc == 0 and "--dry-run" in out and "--input" in out and "--webos-shell" in out and "--egl" in out, out)
    rc, out, _, _ = run(["--parse-only", "--input", "--webos-shell", "--egl", "--app-id", "wayland-hello-prototype"])
    check("v2 flags parse", rc == 0 and "input=1" in out and "webos_shell=1" in out and "egl=1" in out
          and "app_id=wayland-hello-prototype" in out, out)
    rc, out, _, _ = run(["--version"])
    check("version 0.7", rc == 0 and "0.7-prototype" in out, out)
    rc, _, err, _ = run(["--parse-only", "--window-type", "_WEBOS_WINDOW_TYPE_OVERLAY"])
    check("window-type requires webos shell", rc == 2, "rc=%d %s" % (rc, err))
    rc, _, err, _ = run(["--parse-only", "--webos-shell", "--window-type", "OVERLAY"])
    check("window-type must be the webOS token", rc == 2, "rc=%d %s" % (rc, err))
    rc, out, _, _ = run(["--parse-only", "--webos-shell", "--window-type", "_WEBOS_WINDOW_TYPE_OVERLAY", "--app-id", "wayland-hello-prototype"])
    check("window-type parses", rc == 0 and "window_type=_WEBOS_WINDOW_TYPE_OVERLAY" in out and "app_id=wayland-hello-prototype" in out, out)
    rc, out, _, _ = run(["--parse-only", "--webos-shell"])
    check("webos default window type is CARD", rc == 0 and "window_type=_WEBOS_WINDOW_TYPE_CARD" in out, out)
    rc, out, err, _ = run(["--parse-only", "--demo"])
    check("demo is plain wl_shell input with a 120s cap",
          rc == 0 and "demo=1" in out and "input=1" in out and "webos_shell=0" in out and "duration_s=120" in out, out)
    rc, out, _, _ = run(["--parse-only", "--demo", "--duration", "45"])
    check("demo duration can exceed 30", rc == 0 and "duration_s=45" in out, out)
    rc, _, err, _ = run(["--parse-only", "--demo", "--webos-shell"])
    check("demo rejects webos-shell", rc == 2 and "plain wl_shell" in err, err)
    rc, out, err, _ = run(["--parse-only", "--luna-register", "--heartbeat-ms", "500"])
    check("luna and heartbeat parse", rc == 0 and "luna_register=1" in out and "heartbeat_ms=500" in out, out + err)
    rc, _, err, _ = run(["--parse-only", "--heartbeat-ms", "50"])
    check("reject heartbeat below 100", rc == 2 and "100..60000" in err, err)
    rc, _, err, _ = run(["--parse-only", "--duration", "45"])
    check("reject duration 45 without demo", rc == 2 and "1..30" in err, err)
    rc, _, err, _ = run(["--parse-only", "--webos-key-mask"])
    check("key mask requires webos shell", rc == 2, "rc=%d %s" % (rc, err))
    rc, out, _, _ = run(["--parse-only", "--webos-shell", "--webos-key-mask", "--exit-on-leave"])
    check("v3 flags parse", rc == 0 and "webos_key_mask=1" in out and "exit_on_leave=1" in out, out)
    for bad in ("", "has space", "../x", "a/b", "A" * 65):
        rc, _, _, _ = run(["--parse-only", "--app-id", bad])
        check("reject app-id %r" % bad, rc == 2, "rc=%d" % rc)


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
        if env_extra:
            env.update(env_extra)
        r = run(client_args, env, timeout)
    finally:
        try:
            m.wait(timeout=3)
        except subprocess.TimeoutExpired:
            m.kill(); m.wait()
    with open(log) as f:
        events = [json.loads(l) for l in f if l.strip()]
    leftovers = [x for x in os.listdir(d) if x.startswith("wayland-hello-")]
    return r, events, leftovers


def reqs(events):
    return [(e.get("iface"), e.get("req")) for e in events if "req" in e]


def mock_tests():
    (rc, out, err, dt), ev, _ = with_mock([], ["--dry-run", "--duration", "5"])
    r = reqs(ev)
    check("dry-run exit 0", rc == 0, err)
    check("dry-run prints globals", "interface=wl_shell" in out and "interface=wl_compositor" in out, out)
    check("dry-run prints unconfirmed global verbatim", "zz_test_interface_unconfirmed" in out, out)
    check("dry-run creates no surface/bind", not any(q in r for q in [("wl_compositor", "create_surface"), ("wl_registry", "bind")]), str(r))

    (rc, out, err, dt), ev, _ = with_mock(["--no-shell"], ["--duration", "5"])
    r = reqs(ev)
    check("no wl_shell -> fail closed rc=5", rc == 5, "rc=%d %s" % (rc, err))
    check("no wl_shell -> no surface created", ("wl_compositor", "create_surface") not in r, str(r))

    (rc, out, err, dt), ev, _ = with_mock(["--stall"], ["--dry-run", "--duration", "2"])
    check("stalled compositor -> bounded exit", rc != 0 and dt < 5.5, "rc=%d dt=%.2f %s" % (rc, dt, err))

    (rc, out, err, dt), ev, left = with_mock(["--configure", "5000x3000"], ["--duration", "2"])
    r = reqs(ev)
    check("surface mode rc=0", rc == 0, "rc=%d %s" % (rc, err))
    check("surface mode duration bounded ~2s", 1.5 < dt < 4.5, "dt=%.2f" % dt)
    for q in [("wl_registry", "bind"), ("wl_compositor", "create_surface"), ("wl_shell", "get_shell_surface"),
              ("wl_shell_surface", "set_fullscreen"), ("wl_shm", "create_pool"), ("wl_shm_pool", "create_buffer"),
              ("wl_surface", "attach"), ("wl_surface", "commit"), ("wl_shell_surface", "pong")]:
        check("surface mode sent %s.%s" % q, q in r, str(r))
    binds = [e["args"] for e in ev if e.get("req") == "bind"]
    check("all binds at version 1", binds and all(b[2] == 1 for b in binds), str(binds))
    # mock_compositor logs wl_shm_pool.create_buffer (sig "niiiiu") as
    # [new_id, offset, width, height, stride, format]
    bufs = [e["args"] for e in ev if e.get("req") == "create_buffer"]
    check("configure 5000x3000 clamped to 1920x1080",
          any(b[2] == 1920 and b[3] == 1080 and b[4] == 1920 * 4 for b in bufs), str(bufs))
    check("first buffer default 640x360",
          bufs and bufs[0][1] == 0 and bufs[0][2] == 640 and bufs[0][3] == 360 and bufs[0][4] == 640 * 4
          and bufs[0][5] == 1, str(bufs))
    pools = [e for e in ev if e.get("event") == "pool_fd"]
    check("pool fd size matches declared", pools and all(p["size"] == p["declared"] for p in pools), str(pools))
    check("no shm temp files left", not left, str(left))
    check("disconnect observed", any(e.get("event") == "disconnect" for e in ev), "")
    check("stderr lines carry monotonic timestamps", any(line.startswith("t=") and line[2:3].isdigit() for line in err.splitlines()), err[:200])
    check("countdown arms on commit-queued", "countdown-armed trigger=commit-queued" in err, err)
    names = [e.get("req") for e in ev]
    check("frame request precedes commit", "frame" in names and "commit" in names and names.index("frame") < names.index("commit"), str(names))
    check("one pending frame callback", names.count("frame") == 1, str(names))
    check("missing frame callback is not a failed present", rc == 0 and "frame: request queued" in err
          and "frame: pending callback destroyed during cleanup" in err
          and "summary: commits=" in err and "frame_done=0" in err and "frame_pending=1" in err, err[-500:])
    check("shell ping is logged and ponged", "shell: ping serial=" in err and "shell: pong serial=" in err, err)
    check("wl_shell title and class carry the app id",
          any(e.get("req") == "set_title" and e.get("args") == ["wayland-hello-prototype"] for e in ev)
          and any(e.get("req") == "set_class" and e.get("args") == ["wayland-hello-prototype"] for e in ev), str(reqs(ev)))
    check("configure logs raw and clamped size", "raw=5000x3000" in err and "clamped=1920x1080" in err, err)

    rc, out, err, dt = run(["--dry-run", "--duration", "2"],
                           {"XDG_RUNTIME_DIR": tempfile.mkdtemp(), "WAYLAND_DISPLAY": "none"})
    check("no socket -> rc=3", rc == 3, "rc=%d %s" % (rc, err))


def build_so(src_text, dest):
    src = dest + ".c"
    with open(src, "w") as f:
        f.write(src_text)
    p = subprocess.run(["gcc", "-shared", "-fPIC", "-o", dest, src], capture_output=True, text=True, timeout=30)
    if p.returncode != 0:
        raise RuntimeError(p.stderr)


WEBOS_HDR = r'''
struct wl_message { const char *name; const char *signature; const void *types; };
struct wl_interface {
  const char *name; int version;
  int method_count; const struct wl_message *methods;
  int event_count; const struct wl_message *events;
};
'''


def webos_src(shell, surface):
    events = [("state_changed", "u"), ("position_changed", "ii"), ("close", ""),
              ("exposed", "a"), ("state_about_to_change", "u")]

    def arr(name, items):
        lines = ["static const struct wl_message %s[] = {" % name]
        for n, s in items:
            lines.append('  {"%s", "%s", 0},' % (n, s))
        if not items:
            lines.append('  {"unused", "", 0},')
        lines.append("};")
        return "\n".join(lines)

    return WEBOS_HDR + arr("shell_m", shell) + "\n" + arr("surf_m", surface) + "\n" + arr("surf_e", events) + """
const struct wl_interface wl_webos_shell_interface = {"wl_webos_shell", 1, %d, shell_m, 0, 0};
const struct wl_interface wl_webos_shell_surface_interface = {"wl_webos_shell_surface", 1, %d, surf_m, %d, surf_e};
""" % (max(1, len(shell)), len(surface), len(events))


def input_tests():
    (rc, out, err, dt), ev, _ = with_mock(["--seats", "2", "--input-script", "p105,p30"], ["--input", "--duration", "2"])
    check("input mode rc=0", rc == 0, "rc=%d %s" % (rc, err[-400:]))
    check("raw keycodes on stdout", "keycode raw=105 state=pressed seat=0" in out and "keycode raw=30 state=pressed seat=0" in out, out)
    check("keycode log names the evdev assumption", "keycode-log assumption=wl_keyboard_key_is_evdev" in out, out)
    check("arrow moves square", "input: model square x=60 y=100 size=40" in err, err)
    check("other key recolors", "input: model color ff0000" in err, err)
    pix = [e for e in ev if e.get("event") == "pixels"]
    check("pixels show moved green square and red background",
          pix and pix[-1].get("16,16") == 0xffff0000 and pix[-1].get("80,120") == 0xff00ff00
          and pix[-1].get("120,120") == 0xffff0000, str(pix))
    check("two keyboards bound", sum(1 for e in ev if e.get("req") == "get_keyboard") == 2, str(reqs(ev)))
    check("keymap xkb_v1 logged twice", err.count("format=1 (xkb_v1)") == 2, err)
    check("keymap prefix logged", "xkb_keymap" in err, err)
    check("pointer motion logged", "input: pointer motion" in err and "x=10.000" in err and "y=5.000" in err, err)
    check("modifiers logged", "depressed=0x1" in err, err)
    check("wl_seat only, no evdev open mentioned as a path", "no evdev device open" in err, err)

    (rc, out, err, dt), ev, _ = with_mock(["--seats", "1", "--input-script", "p158"], ["--input", "--duration", "6"])
    check("BACK exits cleanly", rc == 0 and dt < 4.0, "rc=%d dt=%.2f %s" % (rc, dt, err[-300:]))
    check("BACK raw code on stdout", "keycode raw=158 state=pressed seat=0" in out, out)
    check("BACK assumed evdev 158 xkb 166", "assumed_evdev=KEY_BACK" in err and "xkb_keycode=166" in err and "exiting (back-key)" in err, err)

    (rc, out, err, dt), ev, _ = with_mock(["--seats", "1", "--input-script", "p1"], ["--input", "--duration", "6"])
    check("Escape exits", rc == 0 and dt < 4.0 and "exiting (escape)" in err and "keycode raw=1 state=pressed" in out,
          "rc=%d dt=%.2f" % (rc, dt))

    (rc, out, err, dt), ev, _ = with_mock(["--seats", "1", "--input-script", "p174"], ["--input", "--duration", "6"])
    check("EXIT exits", rc == 0 and dt < 4.0 and "exiting (exit-key)" in err and "keycode raw=174 state=pressed" in out
          and "xkb_keycode=182" in err, "rc=%d dt=%.2f" % (rc, dt))

    (rc, out, err, dt), ev, _ = with_mock(["--seats", "1", "--input-script", "p461"], ["--input", "--duration", "2"])
    check("unknown 461 does not exit early", rc == 0 and dt > 1.5, "rc=%d dt=%.2f" % (rc, dt))
    check("unknown 461 raw on stdout", "keycode raw=461 state=pressed seat=0" in out and "assumed_evdev=unknown" in err, out + err)

    (rc, out, err, dt), ev, _ = with_mock(["--seats", "1", "--input-script", "L"], ["--input", "--exit-on-leave", "--duration", "6"])
    check("exit-on-leave after keyboard leave", rc == 0 and dt < 4.0 and "exiting (keyboard-leave)" in err
          and "input: keyboard leave" in err and "input: keyboard enter" in err, "rc=%d dt=%.2f %s" % (rc, dt, err[-400:]))

    (rc, out, err, dt), ev, _ = with_mock(["--seats", "1", "--input-script", "L"], ["--input", "--duration", "2"])
    check("leave without the flag waits for the deadline", rc == 0 and dt > 1.5 and "keyboard leave" in err
          and "exiting (deadline)" in err, "rc=%d dt=%.2f" % (rc, dt))

    (rc, out, err, dt), ev, _ = with_mock([], ["--input", "--duration", "3"])
    check("no wl_seat fails closed rc=8", rc == 8, "rc=%d %s" % (rc, err))
    check("no seat means no surface", ("wl_compositor", "create_surface") not in reqs(ev), str(reqs(ev)))

    (rc, out, err, dt), ev, _ = with_mock(["--seats", "1", "--webos"], ["--dry-run", "--input", "--webos-shell", "--egl", "--duration", "3"])
    check("dry-run still binds nothing", rc == 0 and not any(e.get("req") == "bind" for e in ev), str(reqs(ev)))
    check("dry-run lists seat and webos shell", "interface=wl_seat" in out and "interface=wl_webos_shell" in out, out)

    (rc, out, err, dt), ev, _ = with_mock(["--stall"], ["--input", "--egl", "--webos-shell", "--duration", "2"])
    check("flags do not disable the deadline", rc != 0 and dt < 5.5, "rc=%d dt=%.2f" % (rc, dt))


def webos_tests():
    ose = webos_src(
        [("get_system_pip", ""), ("get_shell_surface", "no")],
        [("set_location_hint", "u"), ("set_state", "u"), ("set_property", "ss"), ("set_key_mask", "u")])
    shifted = webos_src(
        [("get_shell_surface", "no")],
        [("set_location_hint", "u"), ("set_state", "u"), ("set_property", "ss"), ("set_key_mask", "u")])
    bad = webos_src(
        [("get_shell_surface", "u")],
        [("set_state", "u"), ("set_property", "ss")])
    nokey = webos_src(
        [("get_system_pip", ""), ("get_shell_surface", "no")],
        [("set_location_hint", "u"), ("set_state", "u"), ("set_property", "ss")])
    d_ose, d_shift, d_bad, d_nokey, d_empty = [tempfile.mkdtemp(prefix="wlh-so-") for _ in range(5)]
    build_so(ose, os.path.join(d_ose, "libwayland-webos-client.so.1"))
    build_so(shifted, os.path.join(d_shift, "libwayland-webos-client.so.1"))
    build_so(bad, os.path.join(d_bad, "libwayland-webos-client.so.1"))
    build_so(nokey, os.path.join(d_nokey, "libwayland-webos-client.so.1"))

    def ops(ev):
        return [(e.get("iface"), e.get("req"), e.get("args")) for e in ev if str(e.get("iface", "")).startswith("wl_webos")]

    (rc, out, err, dt), ev, _ = with_mock(["--webos"], ["--webos-shell", "--duration", "2"],
                                          env_extra={"WAYLAND_HELLO_LIB_DIR": d_ose})
    found = ops(ev)
    check("webos OSE fixture rc=0", rc == 0, err[-500:])
    check("get_shell_surface uses runtime opcode 1",
          any(i == "wl_webos_shell" and r == "op1" for i, r, a in found) and "get_shell_surface=1" in err, str(found))
    check("set_state fullscreen value 3", any(r == "op1" and a == [3] for i, r, a in found if i.endswith("surface")), str(found))
    check("appId property sent", any(r == "op2" and a == ["appId", "wayland-hello-prototype"] for i, r, a in found), str(found))
    seq = [(e.get("req"), e.get("args")) for e in ev if e.get("iface") == "wl_webos_shell_surface"]
    state_at = next(i for i, (r, a) in enumerate(seq) if r == "op1")
    prop_at = [i for i, (r, a) in enumerate(seq) if r == "op2"]
    check("properties precede set_state", prop_at and max(prop_at) < state_at, str(seq))
    check("displayAffinity 0 is sent before state",
          any(r == "op2" and a == ["displayAffinity", "0"] for r, a in seq[:state_at]), str(seq))
    check("default webos window type is CARD",
          any(r == "op2" and a == ["_WEBOS_WINDOW_TYPE", "_WEBOS_WINDOW_TYPE_CARD"] for r, a in seq[:state_at]), str(seq))
    check("key mask not sent unless opted in", not any(r == "op3" for i, r, a in found), str(found))
    check("webos events logged with values",
          "webos: event state_changed value=3" in err and "webos: event position_changed x=10 y=20" in err
          and "webos: event exposed" in err and "webos: event state_about_to_change value=2" in err, err[-800:])
    check("wl_shell not bound in webos mode", not any(e.get("req") == "bind" and e.get("args", [None, None])[1] == "wl_shell" for e in ev), str(reqs(ev)))

    (rc, out, err, dt), ev, _ = with_mock(["--webos"], ["--webos-shell", "--no-fullscreen", "--duration", "2"],
                                          env_extra={"WAYLAND_HELLO_LIB_DIR": d_ose})
    found = ops(ev)
    check("no-fullscreen sends OSE state 0", any(r == "op1" and a == [0] for i, r, a in found if i.endswith("surface")), str(found))

    (rc, out, err, dt), ev, _ = with_mock(["--webos"], ["--webos-shell", "--duration", "2"],
                                          env_extra={"WAYLAND_HELLO_LIB_DIR": d_shift})
    found = ops(ev)
    check("shifted fixture uses opcode 0", rc == 0 and any(i == "wl_webos_shell" and r == "op0" for i, r, a in found)
          and "get_shell_surface=0" in err, "rc=%d %s %s" % (rc, found, err[-400:]))

    (rc, out, err, dt), ev, _ = with_mock(["--webos"], ["--webos-shell", "--duration", "2"],
                                          env_extra={"WAYLAND_HELLO_LIB_DIR": d_bad})
    check("bad signature fails closed", rc == 9 and not any(str(e.get("iface", "")).startswith("wl_webos") and e.get("req") != "bind" for e in ev),
          "rc=%d %s" % (rc, err[-400:]))
    check("bad signature sends no webos request", not any(e.get("iface") == "wl_webos_shell" for e in ev), str(reqs(ev)))

    (rc, out, err, dt), ev, _ = with_mock(["--webos"], ["--webos-shell", "--duration", "2"],
                                          env_extra={"WAYLAND_HELLO_LIB_DIR": d_empty})
    check("missing webos library fails closed", rc == 9 and "libwayland-webos-client.so.1" in err and "Failing closed" in err, err[-500:])
    check("missing library sends no bind", not any(e.get("req") == "bind" for e in ev), str(reqs(ev)))

    (rc, out, err, dt), ev, _ = with_mock(["--webos"], ["--webos-shell", "--webos-key-mask", "--duration", "2"],
                                          env_extra={"WAYLAND_HELLO_LIB_DIR": d_ose})
    found = ops(ev)
    check("opt-in key mask sends OSE back|exit", rc == 0 and any(r == "op3" and a == [0xFFFFFFFE] for i, r, a in found), str(found) + err[-300:])

    (rc, out, err, dt), ev, _ = with_mock(["--webos"], ["--webos-shell", "--window-type", "_WEBOS_WINDOW_TYPE_OVERLAY", "--duration", "2"],
                                          env_extra={"WAYLAND_HELLO_LIB_DIR": d_ose})
    seq = [(e.get("req"), e.get("args")) for e in ev if e.get("iface") == "wl_webos_shell_surface"]
    check("overlay window type is a set_property before set_state",
          rc == 0 and any(r == "op2" and a == ["_WEBOS_WINDOW_TYPE", "_WEBOS_WINDOW_TYPE_OVERLAY"] for r, a in seq)
          and "webos: set_property opcode=2 name=_WEBOS_WINDOW_TYPE value=_WEBOS_WINDOW_TYPE_OVERLAY" in err
          and "webos: set_state opcode=1 value=3" in err, str(seq) + err[-500:])

    (rc, out, err, dt), ev, _ = with_mock(["--webos"], ["--webos-shell", "--webos-key-mask", "--duration", "2"],
                                          env_extra={"WAYLAND_HELLO_LIB_DIR": d_nokey})
    check("opt-in key mask fails closed when set_key_mask is absent", rc == 9 and not any(e.get("req") == "bind" for e in ev),
          "rc=%d %s" % (rc, err[-400:]))

    (rc, out, err, dt), ev, _ = with_mock([], ["--webos-shell", "--duration", "2"])
    check("absent wl_webos_shell fails closed", rc == 9 and "not advertised" in err, err[-300:])

    xml_tests()


def xml_tests():
    import xml.etree.ElementTree as ET
    path = os.path.join(os.path.dirname(HERE), "third_party", "webos-wayland-extensions", "protocol", "webos-shell.xml")
    root = ET.parse(path).getroot()
    surf = next(i for i in root.findall("interface") if i.get("name") == "wl_webos_shell_surface")
    reqs_xml = [r for r in list(surf) if r.tag == "request"]
    names = [r.get("name") for r in reqs_xml]
    check("vendored XML has set_key_mask", "set_key_mask" in names, str(names))
    mask = next(r for r in reqs_xml if r.get("name") == "set_key_mask")
    args = mask.findall("arg")
    check("set_key_mask takes one uint", len(args) == 1 and args[0].get("type") == "uint", str([(a.get("name"), a.get("type")) for a in args]))
    enum = next(e for e in surf.findall("enum") if e.get("name") == "webos_key")
    bits = {en.get("name"): int(en.get("value"), 0) for en in enum.findall("entry")}
    check("OSE key bits back exit default", bits.get("back") == 2 and bits.get("exit") == 4 and bits.get("default") == 0xFFFFFFF8, str(bits))
    state = next(e for e in surf.findall("enum") if e.get("name") == "state")
    states = {en.get("name"): int(en.get("value"), 0) for en in state.findall("entry")}
    check("OSE fullscreen state is 3", states.get("fullscreen") == 3 and states.get("default") == 0, str(states))


def telemetry_tests():
    (rc, out, err, dt), ev, _ = with_mock(["--frame-done"], ["--duration", "2"])
    check("frame done keeps server timestamp separate", rc == 0 and "server_ts=123456" in err
          and "local_ms=" in err and "not subtracted from local time" in err
          and "not a visibility proof" in err and "frame: callback proxy destroyed" in err, err[-700:])
    check("frame done does not rearm the countdown", err.count("countdown-armed") == 1, err)

    (rc, out, err, dt), ev, _ = with_mock(["--seats", "1", "--input-script", "p105", "--no-release"],
                                          ["--input", "--duration", "2"])
    pix = [e for e in ev if e.get("event") == "pixels"]
    check("busy redraw is deferred", rc == 0 and "redraw: deferred" in err and "input: model square" in err, err[-700:])
    check("deferred redraw does not write busy memory",
          pix and pix[-1].get("120,120") == 0xff00ff00 and pix[-1].get("80,120") != 0xff00ff00, str(pix))

    (rc, out, err, dt), ev, _ = with_mock(["--seats", "1", "--input-script", "p105", "--no-release"],
                                          ["--demo", "--duration", "2"])
    pix = [e for e in ev if e.get("event") == "pixels"]
    check("demo allocates a second buffer when none are released",
          rc == 0 and "buf: spare gen=2" in err and "redraw: queued gen=2" in err
          and "releases=0" in err and "redraw: deferred" not in err, err[-900:])
    check("demo paints the moved square into the spare buffer",
          pix and pix[-1].get("80,120") == 0xff00ff00 and pix[-1].get("120,120") != 0xff00ff00, str(pix))
    (rc, out, err, dt), ev, _ = with_mock(["--seats", "1", "--input-script", "p158"],
                                          ["--demo", "--duration", "6"])
    check("demo exits on BACK", rc == 0 and dt < 4.0 and "exiting (back-key)" in err, "rc=%d dt=%.2f" % (rc, dt))
    (rc, out, err, dt), ev, _ = with_mock(["--seats", "1", "--input-script", "p174"],
                                          ["--demo", "--duration", "6"])
    check("demo exits on EXIT", rc == 0 and dt < 4.0 and "exiting (exit-key)" in err, "rc=%d dt=%.2f" % (rc, dt))

    (rc, out, err, dt), ev, _ = with_mock([], ["--luna-register", "--duration", "2"],
                                          env_extra={"WAYLAND_HELLO_LIB_DIR": "/tmp/wayland-hello-no-luna"})
    check("missing luna library fails closed", rc == 10 and "libluna-service2.so.3" in err and "Failing closed" in err, err[-500:])
    check("missing luna sends no bind", not any(e.get("req") == "bind" for e in ev), str(ev)[:400])

    fix = tempfile.mkdtemp(prefix="wlh-luna-")
    so = os.path.join(fix, "libluna-service2.so.3")
    built = subprocess.run(["gcc", "-shared", "-fPIC", "-std=c99", "-o", so,
                            os.path.join(HERE, "luna_fixture.c")],
                           capture_output=True, text=True)
    check("luna fixture builds", built.returncode == 0, built.stderr)
    if built.returncode == 0:
        os.symlink("libluna-service2.so.3", os.path.join(fix, "libglib-2.0.so.0"))
        (rc, out, err, dt), ev, _ = with_mock([], ["--luna-register", "--duration", "2"],
                                              env_extra={"WAYLAND_HELLO_LIB_DIR": fix, "LS2_NAME": "org.va7dimar.waylandhello-3"})
        check("luna register uses LS2_NAME and exits on close",
              rc == 0 and "luna: register name=org.va7dimar.waylandhello-3 source=LS2_NAME" in err
              and "luna: LSCall luna://com.webos.service.applicationmanager/registerApp {\"subscribe\":true}" in err
              and "luna: event=registered" in err and "luna: event=relaunch" in err
              and "luna: event=close" in err and "exiting (luna-close)" in err
              and "fixture: iterate ctx=null block=0" in err
              and err.find("fixture: LSUnregister") > err.find("luna: event=close"), err[-1500:])

        def luna_case(name, script, args, timeout=40):
            env = {"WAYLAND_HELLO_LIB_DIR": fix}
            if script:
                env["WAYLAND_HELLO_LUNA_SCRIPT"] = script
            return with_mock([], args, timeout=timeout, env_extra=env)

        (rc, out, err, dt), ev, _ = luna_case("reject", "reject", ["--luna-register", "--duration", "4"])
        check("rejected registerApp fails closed before a surface",
              rc == 10 and "luna: reply rejected" in err and "returnValue\":false" in err
              and "exiting (luna-reject)" in err
              and not any(e.get("req") == "bind" for e in ev), "rc=%d %s" % (rc, err[-500:]))

        (rc, out, err, dt), ev, _ = luna_case("regfail", "register-fail", ["--luna-register", "--duration", "4"])
        check("LSRegister failure logs the luna error",
              rc == 10 and "luna: LSRegister failed code=1 message=register refused" in err
              and not any(e.get("req") == "bind" for e in ev), "rc=%d %s" % (rc, err[-400:]))

        (rc, out, err, dt), ev, _ = luna_case("attachfail", "attach-fail", ["--luna-register", "--duration", "4"])
        check("LSGmainAttach failure logs the luna error",
              rc == 10 and "luna: LSGmainAttach failed code=2 message=attach refused" in err
              and "fixture: LSUnregister" in err
              and not any(e.get("req") == "bind" for e in ev), "rc=%d %s" % (rc, err[-400:]))

        (rc, out, err, dt), ev, _ = luna_case("callfail", "call-fail", ["--luna-register", "--duration", "4"])
        check("LSCall failure logs the luna error and still unregisters",
              rc == 10 and "luna: LSCall failed code=3 message=call refused" in err
              and err.find("fixture: LSUnregister") > err.find("luna: LSCall failed")
              and not any(e.get("req") == "bind" for e in ev), "rc=%d %s" % (rc, err[-400:]))

        (rc, out, err, dt), ev, _ = luna_case("nested", "nested-close", ["--luna-register", "--duration", "4"])
        check("top-level close wins over a nested event",
              rc == 0 and "exiting (luna-close)" in err and "event=relaunch" not in err, err[-500:])

        (rc, out, err, dt), ev, _ = luna_case("relaunch", "relaunch-only", ["--luna-register", "--duration", "2"])
        polls = 0
        for line in err.splitlines():
            if "luna_polls=" in line:
                polls = int(line.split("luna_polls=")[1].split()[0])
        check("relaunch does not exit and polling continues",
              rc == 0 and dt > 1.2 and "luna: event=relaunch" in err and "luna-close" not in err
              and "exiting (deadline)" in err and polls >= 5 and "fixture: LSUnregister" in err,
              "rc=%d dt=%.2f polls=%d %s" % (rc, dt, polls, err[-400:]))

        (rc, out, err, dt), ev, _ = luna_case("late", "close-late", ["--luna-register", "--duration", "8"], timeout=20)
        check("close during the poll loop exits before the safety cap",
              rc == 0 and dt < 6.0 and "exiting (luna-close)" in err, "rc=%d dt=%.2f" % (rc, dt))

        (rc, out, err, dt), ev, _ = luna_case("silent", "silent", ["--luna-register", "--duration", "6"], timeout=15)
        check("silent bus fails closed",
              rc == 10 and "exiting (luna-reject)" in err and "luna: no registerApp reply after" in err
              and "luna_replies=0" in err and 1.2 < dt < 3.5
              and err.find("fixture: LSUnregister") > err.find("no registerApp reply after"),
              "rc=%d dt=%.2f %s" % (rc, dt, err[-500:]))

        (rc, out, err, dt), ev, _ = luna_case("nesta", "nest-close-inside", ["--luna-register", "--duration", "2"])
        check("nested event=close does not end a top-level relaunch",
              rc == 0 and dt > 1.2 and "luna: event=relaunch" in err and "luna-close" not in err,
              "rc=%d dt=%.2f %s" % (rc, dt, err[-400:]))
        (rc, out, err, dt), ev, _ = luna_case("nestb", "nest-close-outside", ["--luna-register", "--duration", "2"])
        check("top-level relaunch wins when nested close comes first",
              rc == 0 and dt > 1.2 and "luna: event=relaunch" in err and "luna-close" not in err,
              "rc=%d dt=%.2f %s" % (rc, dt, err[-400:]))
        (rc, out, err, dt), ev, _ = luna_case("nestrv", "nest-true-then-false", ["--luna-register", "--duration", "4"])
        check("top-level returnValue false is not masked by a nested true",
              rc == 10 and "exiting (luna-reject)" in err and not any(e.get("req") == "bind" for e in ev),
              "rc=%d %s" % (rc, err[-400:]))
        (rc, out, err, dt), ev, _ = luna_case("nestrv2", "nest-false-then-true", ["--luna-register", "--duration", "2"])
        check("nested returnValue false does not mask a top-level registered",
              rc == 0 and dt > 1.2 and "luna: event=registered" in err and "luna-reject" not in err,
              "rc=%d dt=%.2f %s" % (rc, dt, err[-400:]))

        (rc, out, err, dt), ev, _ = with_mock(
            ["--stall"], ["--luna-register", "--duration", "3"], timeout=10,
            env_extra={"WAYLAND_HELLO_LIB_DIR": fix, "WAYLAND_HELLO_LUNA_SCRIPT": "close-startup"})
        check("stalled startup roundtrip aborts on luna close",
              rc == 0 and dt < 0.8 and "exiting (luna-close)" in err
              and "roundtrip deadline exceeded" not in err,
              "rc=%d dt=%.2f %s" % (rc, dt, err[-400:]))

        (rc, out, err, dt), ev, _ = luna_case("late", "late-reject", ["--luna-register", "--duration", "6"], timeout=20)
        check("mid-run reject exits as luna-reject",
              rc == 10 and "exiting (luna-reject)" in err and "exiting (deadline)" not in err
              and "commit-queued" in err, "rc=%d dt=%.2f %s" % (rc, dt, err[-400:]))

        (rc, out, err, dt), ev, _ = luna_case("hub", "hub", ["--luna-register", "--duration", "4"])
        check("hub error fails closed",
              rc == 10 and "exiting (luna-reject)" in err and "Unknown method" in err
              and not any(e.get("req") == "bind" for e in ev), "rc=%d %s" % (rc, err[-400:]))

        (rc, out, err, dt), ev, _ = luna_case("dryreject", "reject-roundtrip",
                                              ["--dry-run", "--luna-register", "--duration", "4"])
        check("dry-run does not return 0 after a reject",
              rc == 10 and "exiting (luna-reject)" in err and "dry-run: no surfaces created" not in out,
              "rc=%d out=%s err=%s" % (rc, out[-200:], err[-400:]))

        (rc, out, err, dt), ev, _ = luna_case("closestart", "close-startup", ["--luna-register", "--duration", "4"])
        check("close during startup does not commit a surface",
              rc == 0 and "exiting (luna-close)" in err
              and not any(e.get("req") in ("commit", "create_surface") for e in ev),
              "rc=%d %s" % (rc, err[-400:]))

        (rc, out, err, dt), ev, _ = with_mock([], ["--luna-register", "--duration", "2"],
                                              env_extra={"WAYLAND_HELLO_LIB_DIR": fix, "LS2_NAME": "bad name"})
        check("unusable LS2_NAME falls back to the app id",
              rc == 0 and "source=app-id" in err and "not a usable service name" in err, err[-500:])

        partial = tempfile.mkdtemp(prefix="wlh-luna-partial-")
        partial_so = os.path.join(partial, "libluna-service2.so.3")
        partial_build = subprocess.run(
            ["gcc", "-shared", "-fPIC", "-std=c99", "-DLUNA_OMIT_ATTACH", "-o", partial_so,
             os.path.join(HERE, "luna_fixture.c")],
            capture_output=True, text=True)
        check("partial luna fixture builds", partial_build.returncode == 0, partial_build.stderr)
        if partial_build.returncode == 0:
            os.symlink("libluna-service2.so.3", os.path.join(partial, "libglib-2.0.so.0"))
            (rc, out, err, dt), ev, _ = with_mock([], ["--luna-register", "--duration", "2"],
                                                  env_extra={"WAYLAND_HELLO_LIB_DIR": partial})
            check("missing LSGmainAttach fails closed",
                  rc == 10 and "missing symbol LSGmainAttach" in err
                  and not any(e.get("req") == "bind" for e in ev), "rc=%d %s" % (rc, err[-400:]))

    sample = (
        "luna: LSCall luna://com.webos.service.applicationmanager/registerApp {\"subscribe\":true}\n"
        "luna: no registerApp reply after 2000ms\n"
        "info: exiting (deadline)\n"
        "summary: commits=1 luna_replies=0 luna_polls=4\n"
    )
    logf = os.path.join(tempfile.mkdtemp(prefix="wlh-wh6-"), "wh6.log")
    with open(logf, "w", encoding="utf-8") as fh:
        fh.write(sample)
    classified = subprocess.run(
        ["python3", "-I", os.path.join(os.path.dirname(HERE), "scripts", "classify_wh6_log.py"), logf],
        capture_output=True, text=True)
    check("wh6 classifier names a silent bus",
          classified.returncode == 0 and classified.stdout == "replies=0\nreply=none\nexit=deadline\nmarker=yes\n",
          classified.stdout + classified.stderr)

    (rc, out, err, dt), ev, _ = with_mock([], ["--heartbeat-ms", "400", "--duration", "2"])
    check("heartbeat ticks while idle", rc == 0 and "heartbeat: tick n=2" in err, err[-500:])

    (rc, out, err, dt), ev, _ = with_mock(["--configure", "800x600", "--no-release"], ["--duration", "2"])
    check("resize logs generations and busy destruction",
          rc == 0 and "resize: apply old_gen=1" in err and "busy=1" in err
          and "destroy-before-release gen=1" in err and "buf: create gen=2" in err
          and "resize: applied new_gen=2" in err, err[-900:])

    (rc, out, err, dt), ev, _ = with_mock([], ["--duration", "2"])
    check("no configure still exits on the countdown", rc == 0 and 1.5 < dt < 4.5
          and "countdown-armed trigger=commit-queued" in err, "rc=%d dt=%.2f" % (rc, dt))

    (rc, out, err, dt), ev, _ = with_mock(["--seats", "1", "--input-script", "p105,p105,p105"],
                                          ["--input", "--duration", "2"])
    check("repeated input stays bounded and rate-limits model logs",
          rc == 0 and "model_repeats_suppressed=" in err and "model_repeats_suppressed=0" not in err, err[-400:])

    (rc, out, err, dt), ev, _ = with_mock(["--seats", "1", "--input-script", "L"],
                                          ["--input", "--exit-on-leave", "--duration", "6"])
    check("leave names the surface", "keyboard leave seat=0 surface=ours" in err and "keyboard enter seat=0 surface=ours" in err, err[-500:])


def egl_tests():
    empty = tempfile.mkdtemp(prefix="wlh-egl-")
    (rc, out, err, dt), ev, _ = with_mock([], ["--egl", "--duration", "2"], env_extra={"WAYLAND_HELLO_LIB_DIR": empty})
    check("missing egl libs fall back to shm", rc == 0 and "libwayland-egl.so.1" in err and "falling back to shm" in err, err[-500:])
    check("shm buffer still created", any(e.get("req") == "create_buffer" for e in ev), str(reqs(ev)))
    stub = "int wayland_hello_egl_stub;\n"
    build_so(stub, os.path.join(empty, "libwayland-egl.so.1"))
    (rc, out, err, dt), ev, _ = with_mock(["--seats", "1", "--input-script", "p105"], ["--egl", "--input", "--duration", "2"],
                                          env_extra={"WAYLAND_HELLO_LIB_DIR": empty})
    check("missing egl symbol is logged and shm input still works",
          rc == 0 and "missing symbol wl_egl_window_create" in err and "falling back to shm" in err
          and "keycode raw=105 state=pressed" in out and "input: model square x=60" in err, err[-500:])


def linkage_tests():
    blob = open(BIN, "rb").read()
    for s in (b"/dev/input", b"/dev/fb", b"/dev/dri"):
        check("binary has no %s" % s.decode(), s not in blob)
    p = subprocess.run(["readelf", "-d", BIN], capture_output=True, text=True)
    needed = []
    for line in p.stdout.splitlines():
        if "(NEEDED)" in line and "[" in line:
            needed.append(line.split("[", 1)[1].split("]", 1)[0])
    check("host NEEDED is libc/libdl/librt only", needed and set(needed) <= {"libc.so.6", "libdl.so.2", "librt.so.1"}, str(needed))
    t = subprocess.run(["objdump", "-T", BIN], capture_output=True, text=True)
    symbols = t.stdout
    check("no link-time wl/egl/gl symbols",
          " wl_" not in symbols and " egl" not in symbols.lower() and " gl" not in symbols.lower())


if __name__ == "__main__":
    parser_tests()
    mock_tests()
    input_tests()
    webos_tests()
    telemetry_tests()
    egl_tests()
    linkage_tests()
    n_fail = sum(1 for _, ok, _ in results if not ok)
    print("\n%d tests, %d failed" % (len(results), n_fail))
    sys.exit(1 if n_fail else 0)

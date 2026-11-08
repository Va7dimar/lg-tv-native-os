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
    check("--help exit 0", rc == 0 and "--dry-run" in out, out)


def with_mock(mock_args, client_args, timeout=40):
    d = tempfile.mkdtemp(prefix="wlh-test-")
    sock, log = os.path.join(d, "wayland-mock"), os.path.join(d, "log.jsonl")
    m = subprocess.Popen([sys.executable, "-I", MOCK, sock, log] + mock_args)
    for _ in range(100):
        if os.path.exists(sock):
            break
        time.sleep(0.05)
    try:
        r = run(client_args, {"XDG_RUNTIME_DIR": d, "WAYLAND_DISPLAY": "wayland-mock"}, timeout)
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

    rc, out, err, dt = run(["--dry-run", "--duration", "2"],
                           {"XDG_RUNTIME_DIR": tempfile.mkdtemp(), "WAYLAND_DISPLAY": "none"})
    check("no socket -> rc=3", rc == 3, "rc=%d %s" % (rc, err))


if __name__ == "__main__":
    parser_tests()
    mock_tests()
    n_fail = sum(1 for _, ok, _ in results if not ok)
    print("\n%d tests, %d failed" % (len(results), n_fail))
    sys.exit(1 if n_fail else 0)

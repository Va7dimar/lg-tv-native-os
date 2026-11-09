#!/usr/bin/env python3
"""Minimal Wayland wire-protocol mock server for OFF-TV tests of wayland-hello.

Not a compositor: it parses requests generically, logs them as JSON lines,
answers wl_display.sync, advertises a configurable global list, and can send
wl_shell_surface.configure / ping. Modes:
  normal     answer everything
  stall      accept connection, never answer (tests deadlines)
Usage: mock_compositor.py SOCKET_PATH LOGFILE [--no-shell] [--stall]
       [--configure WxH] [--once]
"""
import json, mmap, os, socket, struct, sys, array, tempfile

# request signatures we care about: (interface, opcode) -> (name, sig)
# sig chars: u/i uint/int, s string, o object, n new_id(typed), N new_id(untyped bind: s,u,n), h fd, ? nullable prefix
REQ = {
    ("wl_display", 0): ("sync", "n", "wl_callback"),
    ("wl_display", 1): ("get_registry", "n", "wl_registry"),
    ("wl_registry", 0): ("bind", "uN", None),
    ("wl_compositor", 0): ("create_surface", "n", "wl_surface"),
    ("wl_compositor", 1): ("create_region", "n", "wl_region"),
    ("wl_shm", 0): ("create_pool", "nhi", "wl_shm_pool"),
    ("wl_shm_pool", 0): ("create_buffer", "niiiiu", "wl_buffer"),
    ("wl_shm_pool", 1): ("destroy", "", None),
    ("wl_shm_pool", 2): ("resize", "i", None),
    ("wl_buffer", 0): ("destroy", "", None),
    ("wl_surface", 0): ("destroy", "", None),
    ("wl_surface", 1): ("attach", "?oii", None),
    ("wl_surface", 2): ("damage", "iiii", None),
    ("wl_surface", 3): ("frame", "n", "wl_callback"),
    ("wl_surface", 6): ("commit", "", None),
    ("wl_shell", 0): ("get_shell_surface", "no", "wl_shell_surface"),
    ("wl_shell_surface", 0): ("pong", "u", None),
    ("wl_shell_surface", 3): ("set_toplevel", "", None),
    ("wl_shell_surface", 5): ("set_fullscreen", "uu?o", None),
    ("wl_shell_surface", 8): ("set_title", "s", None),
    ("wl_shell_surface", 9): ("set_class", "s", None),
    ("wl_seat", 0): ("get_pointer", "n", "wl_pointer"),
    ("wl_seat", 1): ("get_keyboard", "n", "wl_keyboard"),
    ("wl_seat", 2): ("get_touch", "n", "wl_touch"),
}


def pack_str(s):
    b = s.encode() + b"\0"
    pad = (4 - len(b) % 4) % 4
    return struct.pack("<I", len(b)) + b + b"\0" * pad


def msg(obj, op, payload=b""):
    return struct.pack("<II", obj, ((8 + len(payload)) << 16) | op) + payload


class Client:
    def __init__(self, conn, log, args):
        self.c, self.log, self.args = conn, log, args
        self.objs = {1: "wl_display"}
        self.buf = b""
        self.fds = []
        self.globals = [(1, "wl_compositor", 3), (2, "wl_shm", 1), (3, "wl_output", 2)]
        if not args.get("no_shell"):
            self.globals.append((4, "wl_shell", 1))
        self.globals.append((5, "zz_test_interface_unconfirmed", 1))
        for i in range(args.get("seats") or 0):
            self.globals.append((10 + i, "wl_seat", 3))
        if args.get("webos"):
            self.globals.append((30, "wl_webos_shell", 1))
        self.script = args.get("script") or []
        self.keyboards = []
        self.surface_id = 0
        self.buffer_id = 0
        self.mem = None
        self.last_buf = None
        self.did_input = False
        self.frame_cb = 0
        self.keymap = b'xkb_keymap {\n\txkb_keycodes "(evdev)";\n};\n'

    def send(self, data):
        try:
            self.c.sendall(data)
        except (BrokenPipeError, ConnectionResetError, OSError):
            return

    def emit(self, **kw):
        self.log.write(json.dumps(kw) + "\n"); self.log.flush()

    def recv(self):
        fds = array.array("i")
        data, anc, _, _ = self.c.recvmsg(65536, socket.CMSG_SPACE(16 * fds.itemsize))
        for lvl, typ, d in anc:
            if lvl == socket.SOL_SOCKET and typ == socket.SCM_RIGHTS:
                fds.frombytes(d[: len(d) - (len(d) % fds.itemsize)])
        self.fds.extend(fds)
        return data

    def parse_args(self, sig, p):
        out, off, nullable = [], 0, False
        for ch in sig:
            if ch == "?":
                nullable = True; continue
            if ch in "uion":
                v = struct.unpack_from("<I" if ch != "i" else "<i", p, off)[0]; off += 4
                out.append(v)
            elif ch == "s":
                ln = struct.unpack_from("<I", p, off)[0]; off += 4
                out.append(p[off:off + ln - 1].decode(errors="replace")); off += (ln + 3) & ~3
            elif ch == "h":
                out.append(self.fds.pop(0) if self.fds else -1)
            elif ch == "N":
                ln = struct.unpack_from("<I", p, off)[0]; off += 4
                iface = p[off:off + ln - 1].decode(); off += (ln + 3) & ~3
                ver, nid = struct.unpack_from("<II", p, off); off += 8
                out += [iface, ver, nid]
            nullable = False
        return out

    def send_fds(self, data, fds):
        self.c.sendmsg([data], [(socket.SOL_SOCKET, socket.SCM_RIGHTS, array.array("i", fds).tobytes())])

    def send_keymap(self, kid):
        f = tempfile.NamedTemporaryFile(prefix="wlh-keymap-", delete=False)
        f.write(self.keymap)
        f.close()
        fd = os.open(f.name, os.O_RDONLY)
        os.unlink(f.name)
        payload = struct.pack("<II", 1, len(self.keymap))
        self.send_fds(msg(kid, 0, payload), [fd])
        os.close(fd)
        self.send(msg(kid, 4, struct.pack("<IIIII", 7, 1, 0, 0, 0)))

    def on_commit(self):
        if self.args.get("frame_done") and self.frame_cb:
            self.send(msg(self.frame_cb, 0, struct.pack("<I", 123456)))
            self.frame_cb = 0
        if self.buffer_id and not self.args.get("no_release"):
            self.send(msg(self.buffer_id, 0, b""))  # wl_buffer.release
        if self.did_input:
            return
        self.did_input = True
        if not self.surface_id:
            return
        for kid in self.keyboards:
            self.send(msg(kid, 1, struct.pack("<III", 7, self.surface_id, 0)))  # enter, empty keys
        serial = 1
        for kind, code in self.script:
            if not self.keyboards:
                self.emit(event="script_dropped")
                return
            if kind == "L":
                self.send(msg(self.keyboards[0], 2, struct.pack("<II", serial, self.surface_id)))
            else:
                state = 1 if kind == "p" else 0
                self.send(msg(self.keyboards[0], 3, struct.pack("<IIII", serial, 1, code, state)))
            serial += 1

    def sample_pixels(self):
        if not self.mem or not self.last_buf:
            return
        pts = {}
        w, h, stride, off = self.last_buf
        for x, y in ((16, 16), (80, 120), (120, 120), (160, 120),
                     (50, 147), (243, 147), (436, 147), (320, 45)):
            if 0 <= x < w and 0 <= y < h:
                o = off + y * stride + x * 4
                if 0 <= o <= len(self.mem) - 4:
                    pts["%d,%d" % (x, y)] = struct.unpack_from("<I", self.mem, o)[0]
        if pts:
            self.emit(event="pixels", **pts)

    def handle_webos_shell(self, obj, op, payload):
        if len(payload) >= 8:
            nid, surf = struct.unpack_from("<II", payload)
            self.objs[nid] = "wl_webos_shell_surface"
            self.emit(iface="wl_webos_shell", obj=obj, req="op%d" % op, args=[nid, surf])
            self.send(msg(nid, 0, struct.pack("<I", 3)))
            self.send(msg(nid, 1, struct.pack("<ii", 10, 20)))
            body = struct.pack("<iiiii", 0, 0, 100, 50, -1)
            self.send(msg(nid, 3, struct.pack("<I", len(body)) + body))
            self.send(msg(nid, 4, struct.pack("<I", 2)))
        else:
            self.emit(iface="wl_webos_shell", obj=obj, req="op%d" % op, args=[len(payload)])

    def handle_webos_surface(self, obj, op, payload):
        if len(payload) == 4:
            self.emit(iface="wl_webos_shell_surface", obj=obj, req="op%d" % op, args=[struct.unpack("<I", payload)[0]])
        elif len(payload) > 4:
            self.emit(iface="wl_webos_shell_surface", obj=obj, req="op%d" % op, args=self.parse_args("ss", payload))
        else:
            self.emit(iface="wl_webos_shell_surface", obj=obj, req="op%d" % op, args=[])

    def handle(self, obj, op, payload):
        iface = self.objs.get(obj, "?")
        if iface == "wl_webos_shell":
            self.handle_webos_shell(obj, op, payload)
            return
        if iface == "wl_webos_shell_surface":
            self.handle_webos_surface(obj, op, payload)
            return
        name, sig, newtype = REQ.get((iface, op), ("op%d" % op, "", None))
        args = self.parse_args(sig, payload) if sig else []
        self.emit(iface=iface, obj=obj, req=name, args=[a for a in args])
        for a in args:
            pass
        if (iface, name) == ("wl_registry", "bind"):
            gname, biface, ver, nid = args
            self.objs[nid] = biface
            if biface == "wl_shm":
                self.send(msg(nid, 0, struct.pack("<I", 0)) + msg(nid, 0, struct.pack("<I", 1)))
            elif biface == "wl_seat":
                self.send(msg(nid, 0, struct.pack("<I", 3)))
                self.send(msg(nid, 1, pack_str("seat-%d" % nid)))
            return
        if newtype is not None:
            self.objs[args[0]] = newtype
            if newtype == "wl_surface":
                self.surface_id = args[0]
            elif newtype == "wl_keyboard":
                self.keyboards.append(args[0])
                self.send_keymap(args[0])
            elif newtype == "wl_pointer":
                self.send(msg(args[0], 2, struct.pack("<Iii", 10, 2560, 1280)))
            elif newtype == "wl_callback" and iface == "wl_surface" and name == "frame":
                self.frame_cb = args[0]
        if self.args.get("stall"):
            return
        if (iface, name) == ("wl_display", "sync"):
            self.send(msg(args[0], 0, struct.pack("<I", 1)) + msg(1, 1, struct.pack("<I", args[0])))
            self.objs.pop(args[0], None)
        elif (iface, name) == ("wl_display", "get_registry"):
            out = b""
            for gname, gi, gv in self.globals:
                out += msg(args[0], 0, struct.pack("<I", gname) + pack_str(gi) + struct.pack("<I", gv))
            self.send(out)
        elif (iface, name) == ("wl_shm", "create_pool"):
            fd = args[1]
            if fd >= 0:
                st = os.fstat(fd)
                self.emit(event="pool_fd", size=st.st_size, declared=args[2])
                if self.mem is not None:
                    self.mem.close()
                self.mem = mmap.mmap(fd, st.st_size, mmap.MAP_SHARED, mmap.PROT_READ)
                os.close(fd)
        elif (iface, name) == ("wl_shm_pool", "create_buffer"):
            self.buffer_id = args[0]
            self.last_buf = (args[2], args[3], args[4], args[1])
        elif (iface, name) == ("wl_surface", "commit"):
            self.on_commit()
        elif (iface, name) == ("wl_shell_surface", "set_fullscreen"):
            ss = obj
            self.send(msg(ss, 0, struct.pack("<I", 77)))  # ping
            cfg = self.args.get("configure")
            if cfg:
                w, h = cfg
                self.send(msg(ss, 1, struct.pack("<Iii", 0, w, h)))

    def run(self):
        while True:
            try:
                data = self.recv()
            except OSError:
                return
            if not data:
                self.sample_pixels()
                self.emit(event="disconnect"); return
            self.buf += data
            while len(self.buf) >= 8:
                obj, so = struct.unpack_from("<II", self.buf)
                size, op = so >> 16, so & 0xFFFF
                if size < 8 or len(self.buf) < size:
                    break
                payload = self.buf[8:size]; self.buf = self.buf[size:]
                self.handle(obj, op, payload)


def main():
    a = sys.argv[1:]
    path, logp = a[0], a[1]
    args = {"no_shell": "--no-shell" in a, "stall": "--stall" in a, "webos": "--webos" in a,
            "frame_done": "--frame-done" in a, "no_release": "--no-release" in a}
    if "--seats" in a:
        args["seats"] = int(a[a.index("--seats") + 1])
    if "--input-script" in a:
        script = []
        for part in a[a.index("--input-script") + 1].split(","):
            if part in ("L", "l"):
                script.append(("L", 0))
            elif part and part[0] in "pr":
                script.append((part[0], int(part[1:])))
        args["script"] = script
    if "--configure" in a:
        w, h = a[a.index("--configure") + 1].split("x"); args["configure"] = (int(w), int(h))
    try:
        os.unlink(path)
    except FileNotFoundError:
        pass
    s = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
    s.bind(path); s.listen(1)
    with open(logp, "w") as log:
        log.write(json.dumps({"event": "listening"}) + "\n"); log.flush()
        conn, _ = s.accept()
        Client(conn, log, args).run()


if __name__ == "__main__":
    main()

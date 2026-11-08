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
import json, os, socket, struct, sys, array

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

    def send(self, data):
        self.c.sendall(data)

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

    def handle(self, obj, op, payload):
        iface = self.objs.get(obj, "?")
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
            return
        if newtype is not None:
            self.objs[args[0]] = newtype
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
                os.close(fd)
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
    args = {"no_shell": "--no-shell" in a, "stall": "--stall" in a}
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

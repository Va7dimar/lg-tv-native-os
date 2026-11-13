#!/usr/bin/env python3
"""Classify a wayland-hello log (for example /tmp/wh6.log). Host-only.

Prints replies, reply, exit, marker, persist, restore, overlay. Does not
decide whether the TV kept the surface.
"""

from __future__ import annotations

import sys


def classify(text):
    replies = None
    for line in text.splitlines():
        if "summary:" not in line:
            continue
        key = "luna_replies="
        if key in line:
            replies = int(line.split(key, 1)[1].split()[0])
    if "exiting (luna-reject)" in text:
        how = "luna-reject"
    elif "exiting (luna-close)" in text:
        how = "luna-close"
    elif "exiting (deadline)" in text:
        how = "deadline"
    else:
        how = "other"
    seen = "seen" if replies else "none"
    marker = "yes" if "no registerApp reply after" in text else "no"
    persist = "yes" if "persist: alive" in text else "no"
    restore = "yes" if "persist: restore-foreground" in text else "no"
    overlay = "yes" if "_WEBOS_WINDOW_TYPE_OVERLAY" in text else "no"
    return replies, seen, how, marker, persist, restore, overlay


def main(argv):
    path = argv[1] if len(argv) > 1 else "-"
    if path == "-":
        text = sys.stdin.read()
    else:
        with open(path, "r", encoding="utf-8", errors="replace") as fh:
            text = fh.read()
    replies, seen, how, marker, persist, restore, overlay = classify(text)
    print("replies=%s" % ("-" if replies is None else replies))
    print("reply=%s" % seen)
    print("exit=%s" % how)
    print("marker=%s" % marker)
    print("persist=%s" % persist)
    print("restore=%s" % restore)
    print("overlay=%s" % overlay)
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))

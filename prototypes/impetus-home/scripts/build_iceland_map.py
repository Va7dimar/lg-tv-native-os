#!/usr/bin/env python3
"""Build app/iceland/map.js: Iceland's coast and glaciers as SVG paths at 1920x1080.

The Iceland room (#26) draws these paths; nothing is projected on the TV.

Sources, pinned by commit and checked by SHA-256 (a changed file stops the build):
  coast        geoBoundaries ISL ADM0, CC BY 4.0, Landmaelingar Islands (Lysigagnagatt)
  coast, lens  the same, at full detail, cut to the Reykjanes lens
  glaciers     Natural Earth 10 m glaciated areas, public domain

Projection (the approved mock's): equirectangular, cos 64.9 deg,
  x = 600 + (lon + 24.6) * 250 * cos(64.9 deg),  y = 120 + (66.6 - lat) * 250.
Simplified with Ramer-Douglas-Peucker at 0.45 px; the lens at 0.45 px of its own
3.1x scale. One decimal per number. The same inputs always give the same bytes.

Usage: build_iceland_map.py [--cache DIR] [--out FILE]
Standard library only. Downloads go to the cache (default build/map-src/), never into git.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import math
import os
import sys
import urllib.request

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

SOURCES = {
    "coast": {
        "url": "https://github.com/wmgeolab/geoBoundaries/raw/9469f09/releaseData/gbOpen/ISL/ADM0/"
               "geoBoundaries-ISL-ADM0_simplified.geojson",
        "sha256": "59c86c957e9f6f147f4adfca45ece4ea946990dcbdf8884f9edb6e715242205b",
    },
    "coastFull": {
        "url": "https://github.com/wmgeolab/geoBoundaries/raw/9469f09/releaseData/gbOpen/ISL/ADM0/"
               "geoBoundaries-ISL-ADM0.geojson",
        "sha256": "c07af9c63ebc92680c780471ccadaf1eea8f3527156053132004e794c5467e3c",
    },
    "glaciers": {
        "url": "https://raw.githubusercontent.com/nvkelso/natural-earth-vector/"
               "ca96624a56bd078437bca8184e78163e5039ad19/geojson/ne_10m_glaciated_areas.geojson",
        "sha256": "04fd2303d5f0ece2cf482af19d06731d745db9690501d7b0a2a4b7fe23a7726f",
    },
}

X0, Y0, S = 600.0, 120.0, 250.0
LON0, LAT0 = -24.6, 66.6
C = math.cos(math.radians(64.9))
TOL = 0.45
MIN_RING = 1.5                   # px: a smaller island is not drawn
LENS = {"lon": -22.3, "lat": 63.88, "k": 3.1, "r": 208.0}
ICELAND = (-25.5, 62.8, -12.5, 66.8)   # lon/lat box for the glaciers


def project(lon, lat):
    return (X0 + (lon - LON0) * S * C, Y0 + (LAT0 - lat) * S)


def fetch(name, cache):
    src = SOURCES[name]
    path = os.path.join(cache, os.path.basename(src["url"]))
    if not os.path.exists(path):
        os.makedirs(cache, exist_ok=True)
        print("download", src["url"], file=sys.stderr)
        with urllib.request.urlopen(src["url"], timeout=120) as resp:
            data = resp.read()
        with open(path + ".part", "wb") as fh:
            fh.write(data)
        os.replace(path + ".part", path)
    with open(path, "rb") as fh:
        data = fh.read()
    digest = hashlib.sha256(data).hexdigest()
    if digest != src["sha256"]:
        raise SystemExit("%s: SHA-256 %s, expected %s; delete %s to fetch again" % (name, digest, src["sha256"], path))
    return json.loads(data.decode("utf-8")), len(data)


def polygons(geojson):
    for feature in geojson["features"]:
        geom = feature["geometry"]
        if geom["type"] == "Polygon":
            yield geom["coordinates"]
        elif geom["type"] == "MultiPolygon":
            for poly in geom["coordinates"]:
                yield poly


def rdp(points, tol):
    """Ramer-Douglas-Peucker on an open line, iterative."""
    if len(points) < 3:
        return list(points)
    keep = [False] * len(points)
    keep[0] = keep[-1] = True
    stack = [(0, len(points) - 1)]
    while stack:
        a, b = stack.pop()
        ax, ay = points[a]
        bx, by = points[b]
        dx, dy = bx - ax, by - ay
        norm = math.hypot(dx, dy)
        best, idx = -1.0, -1
        for i in range(a + 1, b):
            px, py = points[i]
            d = abs(dy * px - dx * py + bx * ay - by * ax) / norm if norm else math.hypot(px - ax, py - ay)
            if d > best:
                best, idx = d, i
        if idx > 0 and best > tol:
            keep[idx] = True
            stack.append((a, idx))
            stack.append((idx, b))
    return [p for p, k in zip(points, keep) if k]


def simplify_ring(ring, tol):
    """A closed ring: split at its farthest point so both halves keep their ends."""
    pts = ring[:-1] if len(ring) > 1 and ring[0] == ring[-1] else list(ring)
    if len(pts) < 4:
        return pts
    far = max(range(len(pts)), key=lambda i: (pts[i][0] - pts[0][0]) ** 2 + (pts[i][1] - pts[0][1]) ** 2)
    half1 = rdp(pts[:far + 1], tol)
    half2 = rdp(pts[far:] + [pts[0]], tol)
    return half1[:-1] + half2[:-1]


def clip(ring, x0, y0, x1, y1):
    """Sutherland-Hodgman: a ring cut to a rectangle (still a closed shape)."""
    def cut(points, inside, cross):
        out = []
        for i, cur in enumerate(points):
            prev = points[i - 1]
            if inside(cur):
                if not inside(prev):
                    out.append(cross(prev, cur))
                out.append(cur)
            elif inside(prev):
                out.append(cross(prev, cur))
        return out

    def at_x(x):
        return lambda p, q: (x, p[1] + (q[1] - p[1]) * (x - p[0]) / (q[0] - p[0]))

    def at_y(y):
        return lambda p, q: (p[0] + (q[0] - p[0]) * (y - p[1]) / (q[1] - p[1]), y)

    pts = list(ring)
    for inside, cross in ((lambda p: p[0] >= x0, at_x(x0)), (lambda p: p[0] <= x1, at_x(x1)),
                          (lambda p: p[1] >= y0, at_y(y0)), (lambda p: p[1] <= y1, at_y(y1))):
        if not pts:
            break
        pts = cut(pts, inside, cross)
    return pts


def big_enough(pts, min_px):
    xs = [p[0] for p in pts]
    ys = [p[1] for p in pts]
    return max(xs) - min(xs) >= min_px or max(ys) - min(ys) >= min_px


def path_of(rings):
    parts = []
    for pts in rings:
        parts.append("M" + "L".join("%.1f %.1f" % (x, y) for x, y in pts) + "Z")
    return "".join(parts)


def rings_of(geojson, tol, keep=None, box=None, min_px=MIN_RING):
    rings = []
    for poly in polygons(geojson):
        for ring in poly:
            if keep and not keep(ring):
                continue
            pts = [project(c[0], c[1]) for c in ring]
            if box:
                pts = clip(pts, *box)
                if len(pts) < 3:
                    continue
            pts = simplify_ring(pts, tol)
            if len(pts) >= 3 and big_enough(pts, min_px):
                rings.append(pts)
    return rings


def build(cache, out):
    coast, n_coast = fetch("coast", cache)
    full, n_full = fetch("coastFull", cache)
    glac, n_glac = fetch("glaciers", cache)

    def in_iceland(ring):
        lon, lat = ring[0][0], ring[0][1]
        return ICELAND[0] < lon < ICELAND[2] and ICELAND[1] < lat < ICELAND[3]

    cx, cy = project(LENS["lon"], LENS["lat"])
    reach = LENS["r"] / LENS["k"] + 6           # the lens shows this many base px around its centre
    lens_box = (cx - reach, cy - reach, cx + reach, cy + reach)

    data = {
        "coast": path_of(rings_of(coast, TOL)),
        "glac": path_of(rings_of(glac, TOL, keep=in_iceland)),
        "coastFine": path_of(rings_of(full, TOL / LENS["k"], box=lens_box, min_px=MIN_RING / LENS["k"])),
        "lens": {"lon": LENS["lon"], "lat": LENS["lat"], "k": LENS["k"], "r": LENS["r"]},
        "projection": {"x0": X0, "y0": Y0, "lon0": LON0, "lat0": LAT0, "s": S, "c": round(C, 9)},
    }
    head = [
        "// Generated by scripts/build_iceland_map.py; do not edit by hand.",
        "// Iceland at 1920x1080 for the Iceland room (#26). Sources, by SHA-256:",
    ]
    for name, size in (("coast", n_coast), ("coastFull", n_full), ("glaciers", n_glac)):
        head.append("//   %s %s (%d bytes, sha256 %s)" % (name, SOURCES[name]["url"], size, SOURCES[name]["sha256"]))
    head.append("// Coast: geoBoundaries, CC BY 4.0, Landmaelingar Islands. Glaciers: Natural Earth, public domain.")
    body = "window.ICELAND_MAP = " + json.dumps(data, sort_keys=True, separators=(",", ":")) + ";\n"
    text = "\n".join(head) + "\n" + body
    os.makedirs(os.path.dirname(out), exist_ok=True)
    with open(out, "w", encoding="ascii", newline="\n") as fh:
        fh.write(text)
    return data


def main():
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--cache", default=os.path.join(ROOT, "build", "map-src"))
    ap.add_argument("--out", default=os.path.join(ROOT, "app", "iceland", "map.js"))
    args = ap.parse_args()
    data = build(args.cache, args.out)
    for key in ("coast", "glac", "coastFine"):
        print("%-9s %6d bytes" % (key, len(data[key])))
    print("wrote", args.out)


if __name__ == "__main__":
    main()

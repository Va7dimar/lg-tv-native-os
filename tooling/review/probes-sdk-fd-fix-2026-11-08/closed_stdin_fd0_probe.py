"""Synthetic closed-stdin fd0 alias probe. No sdk-candidates assets."""
from __future__ import annotations
import gzip, hashlib, io, json, lzma, os, subprocess, sys, tarfile, tempfile
from pathlib import Path

def tar_bytes():
    out = io.BytesIO()
    with tarfile.open(fileobj=out, mode="w") as tf:
        ti = tarfile.TarInfo("a"); ti.size = 5
        tf.addfile(ti, io.BytesIO(b"hello"))
    return out.getvalue()

def main():
    sys.path.insert(0, "/workspace/lg-tv/tooling")
    import sdk_inventory_phase as sdk
    root = Path(tempfile.mkdtemp(prefix="fd0-"))
    base = root / "workspace" / "lg-tv" / "sdk-candidates" / "20191125"
    assets = base / "assets"
    assets.mkdir(parents=True)
    outd = base / "inspection-metadata-PENDING-REVIEW"
    specs = []
    files = (
        ("sdk", "xz", "starfish-sdk-x86_64-ca9v1-toolchain-5.0.0-20191125.sh"),
        ("native", "gz", "native_sysroot_dependencies.tar.gz"),
        ("target", "gz", "target_sysroot_dependencies.tar.gz"),
    )
    for label, codec, name in files:
        packed = lzma.compress(tar_bytes()) if codec == "xz" else gzip.compress(tar_bytes(), mtime=0)
        prefix = b"synthetic\nMARKER:\n" if codec == "xz" else b""
        data = prefix + packed
        path = assets / name
        path.write_bytes(data)
        marker = prefix[-8:] if prefix else b""
        specs.append({
            "label": label, "path": str(path), "size": len(data),
            "sha256": hashlib.sha256(data).hexdigest(), "codec": codec,
            "offset": len(prefix), "marker_hex": marker.hex(),
        })
    child = Path(__file__).with_name("closed_stdin_fd0_child.py")
    proc = subprocess.run(
        [sys.executable, "-I", "-B", str(child), json.dumps({"specs": specs, "output": str(outd)})],
        capture_output=True, text=True, timeout=60,
    )
    audit_path = outd / "fd012-audit.json"
    audit = json.loads(audit_path.read_text()) if audit_path.exists() else None
    payload = {
        "rc": proc.returncode,
        "stdout": proc.stdout,
        "stderr": proc.stderr[:2000],
        "audit": audit,
        "synthetic_base": str(base),
        "note": "synthetic tree mirroring production path depth; no real sdk-candidates assets",
    }
    print(json.dumps(payload, indent=2))
    dest = Path("/workspace/lg-tv/tooling/review/probes-sdk-fd-fix-2026-11-08/probe-closed-stdin-fd0.json")
    dest.write_text(json.dumps(payload, indent=2) + "\n")

if __name__ == "__main__":
    main()

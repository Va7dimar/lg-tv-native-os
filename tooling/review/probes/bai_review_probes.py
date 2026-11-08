"""Throwaway synthetic probes. Never opens catalog archives."""
from __future__ import annotations
import gzip, io, json, os, stat, sys, tarfile, tempfile, traceback
from pathlib import Path

TOOL = Path("/workspace/lg-tv/tooling")
sys.path.insert(0, str(TOOL))
import bounded_archive_inventory as bai

OUT = Path("/workspace/lg-tv/tooling/review/probes")
results = []

def rec(name, **kwargs):
    results.append({"name": name, **kwargs})
    print("PROBE", name, {k: v for k, v in kwargs.items() if k != "detail"})

def write_targz(path: Path, files: dict[str, bytes]) -> Path:
    with tarfile.open(path, "w:gz") as tf:
        for name, data in files.items():
            info = tarfile.TarInfo(name)
            info.size = len(data)
            info.type = tarfile.REGTYPE
            tf.addfile(info, io.BytesIO(data))
    return path

# --- Probe 1: cross-archive ceilings (members / expanded / pathname) ---
try:
    root = Path(tempfile.mkdtemp(prefix="probe-xa-"))
    a1 = write_targz(root / "a1.tar.gz", {"a.txt": b"AAAA", "b.txt": b"BBBB"})
    a2 = write_targz(root / "a2.tar.gz", {"c.txt": b"CCCC", "d.txt": b"DDDD"})
    out = root / "out"
    out.mkdir()
    # 3 members total across archives, 2 per archive. If global, max_members=3
    # should go partial after first extra. If per-archive, each archive has only 2
    # and overall would be ok.
    res = bai.inventory_archives(
        [a1, a2],
        out,
        limits=bai.Limits(min_free_disk_bytes=1, max_members=3),
    )
    payload = json.loads((out / "inventory.json").read_text())
    rec(
        "cross_archive_max_members",
        ok=res.ok,
        status=res.status,
        member_counts=[a.get("member_count") for a in payload["archives"]],
        errors=payload.get("errors"),
        interpretation="FAIL_SPEC_GLOBAL if ok=True (ceilings reset per archive); PASS_GLOBAL if partial",
        detail={"doc_status": payload["status"], "archives": [{"filename": a["filename"], "status": a["status"], "n": a["member_count"]} for a in payload["archives"]]},
    )
except Exception as e:
    rec("cross_archive_max_members", error=str(e), tb=traceback.format_exc())

try:
    root = Path(tempfile.mkdtemp(prefix="probe-xe-"))
    # each file 40 bytes, 2 files per archive = 80 logical each
    a1 = write_targz(root / "a1.tar.gz", {"a.bin": b"A" * 40, "b.bin": b"B" * 40})
    a2 = write_targz(root / "a2.tar.gz", {"c.bin": b"C" * 40, "d.bin": b"D" * 40})
    out = root / "out"
    out.mkdir()
    # global 100 would fail on archive2 if accumulated (80+40>100)
    # per-archive 100 would accept both (80<=100)
    res = bai.inventory_archives(
        [a1, a2],
        out,
        limits=bai.Limits(min_free_disk_bytes=1, max_expanded_bytes=100),
    )
    payload = json.loads((out / "inventory.json").read_text())
    rec(
        "cross_archive_max_expanded",
        ok=res.ok,
        status=res.status,
        expanded=[a.get("expanded_bytes") for a in payload["archives"]],
        errors=payload.get("errors"),
        interpretation="FAIL_SPEC_GLOBAL if ok=True; PASS_GLOBAL if partial",
    )
except Exception as e:
    rec("cross_archive_max_expanded", error=str(e), tb=traceback.format_exc())

# --- Probe 2: continue after limit on first archive ---
try:
    root = Path(tempfile.mkdtemp(prefix="probe-cont-"))
    a1 = write_targz(root / "a1.tar.gz", {f"f{i}.txt": b"n" for i in range(5)})
    a2 = write_targz(root / "a2.tar.gz", {"later.txt": b"later-payload"})
    out = root / "out"
    out.mkdir()
    res = bai.inventory_archives(
        [a1, a2],
        out,
        limits=bai.Limits(min_free_disk_bytes=1, max_members=3),
        select=("later.txt",),
    )
    payload = json.loads((out / "inventory.json").read_text())
    selected_exists = (out / "selected" / "later.txt").exists()
    rec(
        "continues_after_limit_and_may_select_from_later_archive",
        ok=res.ok,
        status=res.status,
        archive_statuses=[a.get("status") for a in payload["archives"]],
        archive2_members=[m["canonical_name"] for m in payload["archives"][1]["members"]] if len(payload["archives"])>1 else [],
        selected_later_exists=selected_exists,
        errors=payload.get("errors"),
    )
except Exception as e:
    rec("continues_after_limit_and_may_select_from_later_archive", error=str(e), tb=traceback.format_exc())

# --- Probe 3: absolute-named symlink decision overwrite ---
try:
    root = Path(tempfile.mkdtemp(prefix="probe-abslink-"))
    archive = root / "abslink.tar.gz"
    with tarfile.open(archive, "w:gz") as tf:
        link = tarfile.TarInfo("/abs/link")
        link.type = tarfile.SYMTYPE
        link.linkname = "relative-target"
        tf.addfile(link)
        ok = tarfile.TarInfo("ok.txt")
        data = b"ok"
        ok.size = len(data)
        tf.addfile(ok, io.BytesIO(data))
    out = root / "out"
    out.mkdir()
    res = bai.inventory_archives([archive], out, limits=bai.Limits(min_free_disk_bytes=1))
    payload = json.loads((out / "inventory.json").read_text())
    members = payload["archives"][0]["members"]
    rec(
        "absolute_symlink_member_decision",
        ok=res.ok,
        status=res.status,
        members=[{"raw": m["raw_name"], "canon": m["canonical_name"], "decision": m["decision"], "reasons": m["reasons"], "type": m["type"]} for m in members],
    )
except Exception as e:
    rec("absolute_symlink_member_decision", error=str(e), tb=traceback.format_exc())

# --- Probe 4: do PAX/GNU metadata members surface? ---
try:
    root = Path(tempfile.mkdtemp(prefix="probe-paxsurf-"))
    long_name = "deep/" + ("n" * 140) + ".txt"
    archive = write_targz(root / "long.tar.gz", {long_name: b"long-ok"})
    # also inspect raw next() kinds
    kinds = []
    with tarfile.open(archive, "r:gz") as tf:
        while True:
            info = tf.next()
            if info is None:
                break
            kinds.append({"name": info.name, "type": info.type, "type_repr": repr(info.type), "size": info.size, "pax": dict(info.pax_headers or {})})
    out = root / "out"
    out.mkdir()
    res = bai.inventory_archives([archive], out, limits=bai.Limits(min_free_disk_bytes=1))
    payload = json.loads((out / "inventory.json").read_text())
    rec(
        "gnu_longname_surface_as_metadata",
        tarfile_next_members=kinds,
        inventory_types=[m["type"] for m in payload["archives"][0]["members"]],
        pathname_bytes=payload["archives"][0]["pathname_bytes"],
        name_len=len(long_name),
    )
except Exception as e:
    rec("gnu_longname_surface_as_metadata", error=str(e), tb=traceback.format_exc())

# --- Probe 5: large PAX header allocated inside next() before tool loop can reject ---
# Use a moderately large but safe PAX comment (~2 MiB) and tiny pathname budget.
try:
    root = Path(tempfile.mkdtemp(prefix="probe-paxalloc-"))
    pax_value = "Z" * (2 * 1024 * 1024)
    record = f" comment={pax_value}\n"
    # length prefix includes itself; compute correctly in bytes
    # We'll let tarfile write a pax header via pax_headers on TarInfo
    archive = root / "paxbig.tar.gz"
    with tarfile.open(archive, "w:gz", format=tarfile.PAX_FORMAT) as tf:
        info = tarfile.TarInfo("small.txt")
        data = b"hi"
        info.size = len(data)
        info.pax_headers = {"comment": pax_value}
        tf.addfile(info, io.BytesIO(data))
    # What does next() return and how big are pax_headers?
    with tarfile.open(archive, "r:gz") as tf:
        info = tf.next()
        pax_comment_len = len((info.pax_headers or {}).get("comment", ""))
        surfaced_type = info.type
        surfaced_name = info.name
    out = root / "out"
    out.mkdir()
    res = bai.inventory_archives(
        [archive],
        out,
        limits=bai.Limits(min_free_disk_bytes=1, max_pathname_bytes=100),
    )
    payload = json.loads((out / "inventory.json").read_text())
    rec(
        "pax_payload_vs_pathname_budget",
        writer_pax_comment_len=len(pax_value),
        reader_pax_comment_len=pax_comment_len,
        surfaced_type=repr(surfaced_type),
        surfaced_name=surfaced_name,
        ok=res.ok,
        status=res.status,
        pathname_bytes=payload["archives"][0].get("pathname_bytes") if payload.get("archives") else None,
        errors=payload.get("errors"),
        member_count=payload["archives"][0].get("member_count") if payload.get("archives") else None,
        note="stdlib next() already loaded pax comment before inventory applied max_pathname_bytes=100",
    )
except Exception as e:
    rec("pax_payload_vs_pathname_budget", error=str(e), tb=traceback.format_exc())

# --- Probe 6: sparse helper vs parser-surfaced sparse ---
try:
    info = tarfile.TarInfo("sparse.bin")
    info.type = tarfile.REGTYPE
    info.size = 10  # stored/data size style
    info.sparse = [(0, 4), (9996, 4)]
    helper = bai.logical_member_size(info)

    # What does tarfile persist/read back if we set .sparse?
    root = Path(tempfile.mkdtemp(prefix="probe-sparse-"))
    raw = root / "sparse.tar.gz"
    with tarfile.open(raw, "w:gz") as tf:
        written = tarfile.TarInfo("sparse.bin")
        written.type = tarfile.REGTYPE
        written.size = 10
        written.sparse = [(0, 4), (9996, 4)]
        tf.addfile(written, io.BytesIO(b"0123456789"))
    readback = []
    with tarfile.open(raw, "r:gz") as tf:
        while True:
            inf = tf.next()
            if inf is None:
                break
            readback.append({
                "name": inf.name,
                "type": repr(inf.type),
                "size": inf.size,
                "sparse": inf.sparse,
                "logical_helper": bai.logical_member_size(inf),
            })
    out = root / "out"
    out.mkdir()
    res = bai.inventory_archives(
        [raw],
        out,
        limits=bai.Limits(min_free_disk_bytes=1, max_expanded_bytes=100),
    )
    payload = json.loads((out / "inventory.json").read_text())
    rec(
        "sparse_parser_vs_helper",
        helper_on_synthetic_size10_extent10000=helper,
        readback=readback,
        ok=res.ok,
        status=res.status,
        expanded=payload["archives"][0].get("expanded_bytes") if payload.get("archives") else None,
        errors=payload.get("errors"),
        note="implementation test used size=10000 so it cannot distinguish sparse-extent accounting from size-field accounting",
    )
except Exception as e:
    rec("sparse_parser_vs_helper", error=str(e), tb=traceback.format_exc())

# --- Probe 7: output_dir/selected as symlink escape ---
try:
    root = Path(tempfile.mkdtemp(prefix="probe-outlink-"))
    outside = root / "outside"
    outside.mkdir()
    archive = write_targz(root / "a.tar.gz", {"docs/note.txt": b"plain text only\n"})
    out = root / "out"
    out.mkdir()
    selected = out / "selected"
    selected.symlink_to(outside)
    res = bai.inventory_archives(
        [archive],
        out,
        limits=bai.Limits(min_free_disk_bytes=1),
        select=("docs/note.txt",),
    )
    leaked = list(outside.rglob("*"))
    rec(
        "output_selected_symlink_escape",
        ok=res.ok,
        status=res.status,
        errors=res.document.get("errors") if res.document else None,
        leaked_outside=[str(p) for p in leaked],
        dest_inside_out=(out / "selected" / "docs" / "note.txt").exists(),
    )
except Exception as e:
    rec("output_selected_symlink_escape", error=str(e), tb=traceback.format_exc())

# --- Probe 8: r:gz caches members ---
try:
    root = Path(tempfile.mkdtemp(prefix="probe-cache-"))
    archive = write_targz(root / "a.tar.gz", {f"f{i}.txt": b"x" for i in range(20)})
    with tarfile.open(archive, "r:gz") as tf:
        n = 0
        while tf.next() is not None:
            n += 1
        cached = len(tf.members)
    with tarfile.open(archive, "r|gz") as tf:
        n2 = 0
        while tf.next() is not None:
            n2 += 1
        cached_stream = len(tf.members)
    rec("r_gz_caches_members", counted=n, cached_r_gz=cached, counted_stream=n2, cached_r_pipe_gz=cached_stream)
except Exception as e:
    rec("r_gz_caches_members", error=str(e), tb=traceback.format_exc())

# --- Probe 9: min_free_disk floor ---
try:
    lim = bai.Limits(min_free_disk_bytes=1)
    rec("min_free_disk_can_be_lowered_below_10giB", allowed=True, value=lim.min_free_disk_bytes)
except Exception as e:
    rec("min_free_disk_can_be_lowered_below_10giB", allowed=False, error=str(e))

# --- Probe 10: unused leftover / selected hash on oversize lying size ---
# logical size small, actual... extractfile is bounded by header size, so cannot lie larger
# instead confirm decision overwrite already done.

# --- Probe 11: open selected parent symlink to outside after selected/ exists as real dir ---
try:
    root = Path(tempfile.mkdtemp(prefix="probe-parentlink-"))
    outside = root / "outside"
    outside.mkdir()
    archive = write_targz(root / "a.tar.gz", {"docs/note.txt": b"plain\n"})
    out = root / "out"
    out.mkdir()
    (out / "selected").mkdir()
    (out / "selected" / "docs").symlink_to(outside)
    res = bai.inventory_archives(
        [archive],
        out,
        limits=bai.Limits(min_free_disk_bytes=1),
        select=("docs/note.txt",),
    )
    leaked = list(outside.rglob("*"))
    rec(
        "selected_intermediate_symlink_escape",
        ok=res.ok,
        status=res.status,
        errors=res.document.get("errors") if res.document else None,
        leaked_outside=[str(p) for p in leaked],
        archive_error=res.document.get("archives", [{}])[0].get("error") if res.document else None,
    )
except Exception as e:
    rec("selected_intermediate_symlink_escape", error=str(e), tb=traceback.format_exc())

# write report
out_json = OUT / "probe-results.json"
out_md = OUT / "probe-results.md"
out_json.write_text(json.dumps(results, indent=2) + "\n", encoding="utf-8")
lines = ["# Targeted synthetic probe results", "", "No catalog archives were opened.", ""]
for item in results:
    lines.append(f"## {item['name']}")
    lines.append("")
    lines.append("```json")
    lines.append(json.dumps(item, indent=2))
    lines.append("```")
    lines.append("")
out_md.write_text("\n".join(lines), encoding="utf-8")
print("WROTE", out_json)
print("WROTE", out_md)

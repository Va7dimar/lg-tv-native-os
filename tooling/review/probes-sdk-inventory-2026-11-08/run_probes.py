"""Independent synthetic counterexamples for SDK metadata inventory review.
Never open, hash, or parse production SDK assets under sdk-candidates/.
"""
from __future__ import annotations

import dataclasses
import gzip
import hashlib
import inspect
import io
import json
import lzma
import os
from pathlib import Path
import sys
import tarfile
import tempfile
import time
import traceback
from unittest import mock

TOOLS = Path("/workspace/lg-tv/tooling")
sys.path.insert(0, str(TOOLS))
import sdk_inventory_phase as sdk
import isolate_sdk_inventory as isolate

OUT = Path("/workspace/lg-tv/tooling/review/probes-sdk-inventory-2026-11-08")
RESULTS = []


def record(name, passed, detail):
    RESULTS.append({"name": name, "passed": bool(passed), "detail": detail})
    print(f"[{'PASS' if passed else 'FAIL'}] {name}: {detail if not isinstance(detail, (dict, list)) else json.dumps(detail)[:400]}")


def tar_bytes(entries=None, fmt=tarfile.PAX_FORMAT):
    out = io.BytesIO()
    with tarfile.open(fileobj=out, mode="w", format=fmt) as tf:
        for entry in entries or [("a", b"hello")]:
            if isinstance(entry, tarfile.TarInfo):
                tf.addfile(entry, io.BytesIO(b"x" * entry.size) if entry.isreg() else None)
            else:
                name, data = entry
                ti = tarfile.TarInfo(name)
                ti.size = len(data)
                tf.addfile(ti, io.BytesIO(data))
    return out.getvalue()


def make_specs(root, tar=None, transforms=None, serial=[0]):
    tar = tar if tar is not None else tar_bytes()
    result = []
    for i, codec in enumerate(("xz", "gz", "gz")):
        packed = lzma.compress(tar) if codec == "xz" else gzip.compress(tar, mtime=0)
        if transforms and i in transforms:
            packed = transforms[i](packed)
        prefix = b"synthetic\nMARKER:\n" if i == 0 else b""
        data = prefix + packed
        serial[0] += 1
        path = root / f"fixture-{serial[0]}"
        path.write_bytes(data)
        result.append(sdk.InputSpec(
            ("sdk", "native", "target")[i], str(path), len(data),
            hashlib.sha256(data).hexdigest(), codec, len(prefix),
            b"MARKER:\n" if i == 0 else b"",
        ))
    return result


def run_phase(root, serial, specs=None, **limits):
    serial[0] += 1
    out = root / f"out-{serial[0]}"
    result = sdk.inventory(specs or make_specs(root), out, sdk.Limits(**limits))
    manifest = json.loads((out / "manifest.json").read_text())
    return manifest, out, result


def main():
    tmp = tempfile.TemporaryDirectory(prefix="sdk-indep-probe-")
    root = Path(tmp.name)
    serial = [0]
    try:
        _run(root, serial)
    except Exception:
        record("probe_harness", False, traceback.format_exc())
    finally:
        tmp.cleanup()
    (OUT / "probe-results.json").write_text(json.dumps(RESULTS, indent=2) + "\n")
    failed = [r for r in RESULTS if not r["passed"]]
    print(f"\n{len(RESULTS)} probes, {len(failed)} failed")
    return 0 if not failed else 1


def _run(root, serial):
    # 1. Happy path: three streams, selected 0, independent counters
    specs = make_specs(root)
    doc, out, _ = run_phase(root, serial, specs)
    rows = [json.loads(x) for x in (out / "members.jsonl").read_text().splitlines()] if (out / "members.jsonl").exists() else []
    record("happy_three_streams_metadata_only",
           doc["ok"] and doc["totals"]["selected_bytes"] == 0
           and doc["totals"]["logical_regular_bytes"] == 15
           and doc["totals"]["decoded_bytes"] == 3 * len(tar_bytes())
           and doc["totals"]["decoded_bytes"] != doc["totals"]["logical_regular_bytes"]
           and doc["controls"]["extraction_implemented"] is False
           and doc["controls"]["noexec"] is False
           and doc["full_hash_bytes"] == sum(s.size for s in specs)
           and all(a["integrity_eof"] and a["tar_eof"] for a in doc["inputs"])
           and all(r["selected"] is False for r in rows),
           {"ok": doc["ok"], "totals": doc["totals"], "extraction": doc["controls"]["extraction_implemented"],
            "n_rows": len(rows)})

    # 2. Pins before any parse
    specs = make_specs(root)
    specs[2] = dataclasses.replace(specs[2], sha256="0" * 64)
    with mock.patch.object(sdk, "parse_archive", side_effect=AssertionError("must not parse")) as parser:
        doc, _, _ = run_phase(root, serial, specs)
    record("all_pins_before_any_parser",
           (not doc["ok"]) and parser.call_count == 0 and doc["totals"]["decoded_bytes"] == 0
           and "pin" in doc["error"],
           {"ok": doc["ok"], "error": doc["error"], "parser_calls": parser.call_count})

    # 3. Marker / magic
    specs = make_specs(root)
    data = bytearray(Path(specs[0].path).read_bytes())
    data[specs[0].offset - 2] ^= 1  # corrupt MARKER
    Path(specs[0].path).write_bytes(data)
    specs[0] = dataclasses.replace(specs[0], sha256=hashlib.sha256(data).hexdigest())
    doc, _, _ = run_phase(root, serial, specs)
    record("marker_mismatch_no_decode",
           (not doc["ok"]) and doc["totals"]["decoded_bytes"] == 0 and "marker" in doc["error"],
           doc["error"])

    # 4. Concat / trailing both codecs
    concat_ok = True
    concat_detail = {}
    for index, kind, transform in (
        (0, "xz_concat", lambda b: b + b),
        (0, "xz_junk", lambda b: b + b"junk"),
        (0, "xz_zero_tail", lambda b: b + b"\0"),
        (1, "gz_concat", lambda b: b + b),
        (1, "gz_junk", lambda b: b + b"junk"),
        (1, "gz_zero_tail", lambda b: b + b"\0"),
        (0, "xz_trunc", lambda b: b[:-4]),
        (1, "gz_trunc", lambda b: b[:-4]),
    ):
        doc, _, _ = run_phase(root, serial, make_specs(root, transforms={index: transform}))
        good = (not doc["ok"]) and len(doc["inputs"]) <= index + 1
        concat_detail[kind] = {"ok": doc["ok"], "error": doc["error"], "n_inputs": len(doc["inputs"])}
        if not good:
            concat_ok = False
    record("concat_trailing_trunc_both_codecs", concat_ok, concat_detail)

    # 5. Nonzero decoded tar tail vs extra zero padding
    base = tar_bytes()
    doc_bad, _, _ = run_phase(root, serial, make_specs(root, base + b"x"))
    doc_pad, _, _ = run_phase(root, serial, make_specs(root, base + b"\0" * 1024))
    doc_short, _, _ = run_phase(root, serial, make_specs(root, base[:1024]))  # only first? may be incomplete
    record("nonzero_tail_rejected_zero_padding_ok",
           (not doc_bad["ok"]) and doc_pad["ok"] and (not doc_short["ok"]),
           {"nonzero": doc_bad["error"], "padding_ok": doc_pad["ok"], "short": doc_short["error"]})

    # 6. Invalid later header not treated as EOF
    raw = tar_bytes()
    bad = raw[:1024] + b"not a tar header".ljust(512, b"x") + raw[1536:]
    doc, _, _ = run_phase(root, serial, make_specs(root, bad))
    record("invalid_later_header_not_masked_as_eof",
           (not doc["ok"]) and "invalid tar header" in (doc["error"] or ""),
           doc["error"])

    # 7. LZMA memory limit
    specs = make_specs(root, transforms={0: lambda _: lzma.compress(
        tar_bytes(), filters=[{"id": lzma.FILTER_LZMA2, "dict_size": 8 << 20}])})
    doc, _, _ = run_phase(root, serial, specs, lzma_memlimit=1 << 20)
    record("lzma_memlimit_fails_closed",
           (not doc["ok"]) and "Memory" in (doc["error"] or ""),
           doc["error"])

    # 8. Bounded reads
    spec = make_specs(root)[0]
    fd, _ = sdk.open_regular(spec.path)
    try:
        obs = dict(compressed_bytes_read=0, compressed_bytes_consumed=None,
                   decoded_bytes=0, max_decoder_chunk=0, integrity_eof=False)
        budget = sdk.Budget(sdk.Limits(), time.monotonic() + 120)
        reader = sdk.DecodedReader(fd, spec, budget, obs)
        unbounded = False
        try:
            reader.read(-1)
        except sdk.InventoryError:
            unbounded = True
        first = reader.read(1)
        charged = budget.totals["decoded_bytes"]
        record("unbounded_read_forbidden_and_decode_charged_including_lookahead",
               unbounded and first == tar_bytes()[:1] and charged > 1,
               {"unbounded_rejected": unbounded, "charged": charged, "tell": reader.tell(),
                "max_chunk": obs["max_decoder_chunk"]})
    finally:
        os.close(fd)

    # 9. Shared independent caps
    cap_ok = True
    cap_detail = {}
    for kwargs, counter in (({"members": 2}, "members"),
                            ({"logical_bytes": 14}, "logical_regular_bytes"),
                            ({"decoded_bytes": 2 * len(tar_bytes())}, "decoded_bytes")):
        doc, _, _ = run_phase(root, serial, make_specs(root), **kwargs)
        good = (not doc["ok"]) and "limit" in doc["error"] and doc["totals"][counter] > list(kwargs.values())[0]
        cap_detail[counter] = {"error": doc["error"], "total": doc["totals"][counter]}
        if not good:
            cap_ok = False
    doc_exact, _, _ = run_phase(root, serial, make_specs(root),
                                logical_bytes=15, decoded_bytes=3 * len(tar_bytes()))
    cap_ok = cap_ok and doc_exact["ok"]
    cap_detail["exact_caps_ok"] = doc_exact["ok"]
    record("shared_independent_logical_and_decoded_caps", cap_ok, cap_detail)

    # 10. First stream fail skips remaining
    doc, _, _ = run_phase(root, serial, make_specs(root, transforms={0: lambda b: b[:-1]}))
    record("first_failure_skips_remaining_after_all_pins",
           (not doc["ok"]) and all(p["verified"] for p in doc["pin_verifications"])
           and doc["skipped_inputs"] == ["native", "target"],
           {"error": doc["error"], "skipped": doc["skipped_inputs"],
            "verified": [p["verified"] for p in doc["pin_verifications"]]})

    # 11. Unsafe paths / escape symlink
    sy = tarfile.TarInfo("dir/sym")
    sy.type = tarfile.SYMTYPE
    sy.linkname = "../../escape"
    doc, _, _ = run_phase(root, serial, make_specs(root, tar_bytes([sy])))
    record("unsafe_symlink_escape_fails",
           (not doc["ok"]) and "unsafe" in (doc["error"] or ""),
           doc["error"])

    # 12. Production pins / CLI
    pins = sdk.PRODUCTION_SPECS
    pin_ok = (
        pins[0].offset == 10820 and pins[0].marker == b"MARKER:\n" and pins[0].codec == "xz"
        and pins[0].size == 166821312
        and pins[0].sha256 == "3029c64809fe93e6fe6bfb72ac9de6ec556452a0790feb0f9b23abed409e669b"
        and pins[1].codec == "gz" and pins[1].size == 8017931
        and pins[2].codec == "gz" and pins[2].size == 323786694
        and sum(s.size for s in pins) == 498625937
    )
    cli_ok = True
    cli_detail = {}
    base = []
    for s in pins:
        base += ["--" + s.label, s.path]
    base += ["--output-dir", str(root / "never-created")]
    for flag in ("--select", "--max-members", "--offset", "--expected-hash", "--test-spec", "--synthetic-fixture-mode"):
        try:
            sdk.production_arguments(base + [flag, "1"])
            cli_ok = False
            cli_detail[flag] = "accepted"
        except SystemExit:
            cli_detail[flag] = "rejected"
        except Exception as e:
            cli_detail[flag] = type(e).__name__
    try:
        wrong = list(base)
        wrong[1] = str(root / "wrong")
        sdk.production_arguments(wrong)
        cli_ok = False
        cli_detail["wrong_path"] = "accepted"
    except sdk.InventoryError as e:
        cli_detail["wrong_path"] = str(e)
    record("production_pins_and_closed_cli", pin_ok and cli_ok and not (root / "never-created").exists(),
           {"pins_ok": pin_ok, "cli": cli_detail})

    # 13. Limits cannot be raised
    try:
        sdk.Limits(members=200001)
        raised = True
    except ValueError:
        raised = False
    record("limits_cannot_be_raised", not raised, {"raised": raised})

    # 14. Hook API on this interpreter
    sig = str(inspect.signature(tarfile.TarInfo._frombuf))
    record("cpython_313_hook_api_matches",
           hasattr(tarfile.TarInfo, "_frombuf") and hasattr(tarfile.TarInfo, "_proc_member")
           and "dircheck" in sig,
           {"version": sys.version, "frombuf": sig})

    # 15. Isolation command shape
    specs = make_specs(root)
    cmd = isolate.build_command(specs, "/proc/self/fd/99", ["/usr/bin/python3", "-I", "/tool/probe.py"], 117)
    joined = " ".join(cmd)
    record("isolation_command_shape",
           cmd[0].endswith("timeout") and "--unshare-all" in cmd and "--as=1073741824" in cmd
           and "--share-net" not in cmd and "/home" not in joined and "/root" not in joined
           and "/cursor" not in joined and "117" in cmd
           and all(cmd.count(s.path) == 1 for s in specs)
           and str(root) not in joined,
           cmd)

    # 16. Atomic no overwrite
    out = root / "publication"
    fd = sdk.fresh_output(out)
    try:
        sdk.atomic_json(fd, "manifest.json", {"ok": False})
        overwrite = False
        try:
            sdk.atomic_json(fd, "manifest.json", {"ok": True})
            overwrite = True
        except FileExistsError:
            pass
        kept = json.loads((out / "manifest.json").read_text())
        record("atomic_manifest_never_overwrites",
               (not overwrite) and kept.get("ok") is False,
               kept)
    finally:
        os.close(fd)

    # 17. Freshness: existing / dangling rejected
    p = root / "existing-out"
    p.mkdir()
    fresh_ok = True
    try:
        sdk.inventory(make_specs(root), p)
        fresh_ok = False
        detail = "existing accepted"
    except OSError as e:
        detail = str(e)
    dangling = root / "dangling-out"
    dangling.symlink_to(root / "absent")
    try:
        sdk.inventory(make_specs(root), dangling)
        fresh_ok = False
        detail = "dangling accepted"
    except OSError as e:
        detail = {"existing": detail, "dangling": str(e)}
    record("fresh_output_rejects_existing_and_dangling", fresh_ok, detail)

    # 18. Mutation after pin
    specs = make_specs(root)
    original = sdk.parse_archive

    def mutate(*args, **kwargs):
        with open(specs[0].path, "ab") as f:
            f.write(b"!")
        return original(*args, **kwargs)

    with mock.patch.object(sdk, "parse_archive", side_effect=mutate):
        doc, _, _ = run_phase(root, serial, specs)
    record("mutation_after_pin_detected",
           (not doc["ok"]) and "mutat" in doc["error"],
           doc["error"])

    # 19. Deadline covers pins
    with mock.patch.object(sdk.time, "monotonic", side_effect=[0, 121, 122, 123, 124, 125]):
        doc, _, _ = run_phase(root, serial, make_specs(root))
    record("deadline_covers_pins",
           (not doc["ok"]) and "deadline" in doc["error"],
           doc["error"])

    # 20. Integrity corruption after logical tar eof
    def damage_xz(b):
        pos = -12
        return b[:pos] + bytes([b[pos] ^ 1]) + b[pos + 1:]
    doc, _, _ = run_phase(root, serial, make_specs(root, transforms={0: damage_xz}))
    record("integrity_after_tar_eof_detected",
           (not doc["ok"]) and doc["inputs"] and not doc["inputs"][-1]["integrity_eof"],
           {"error": doc["error"], "integrity_eof": doc["inputs"][-1]["integrity_eof"] if doc["inputs"] else None})

    # 21. Nested flag without expansion
    inner = tar_bytes([("secret.txt", b"secret")])
    nested = tar_bytes([("README/nested.tar.gz", inner), ("a", b"hello")])
    doc, out, _ = run_phase(root, serial, make_specs(root, nested))
    text = (out / "members.jsonl").read_text() if (out / "members.jsonl").exists() else ""
    record("nested_archive_flagged_not_expanded",
           doc["ok"] and "secret.txt" not in text and '"nested_archive":true' in text.replace(" ", ""),
           {"ok": doc["ok"], "has_secret": "secret.txt" in text, "snippet": text[:300]})

    # 22. Worker main disabled
    import subprocess
    proc = subprocess.run([sys.executable, "-I", "-B", str(TOOLS / "sdk_inventory_phase.py")],
                          stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    record("direct_worker_invocation_disabled",
           proc.returncode == 2 and b"isolate_sdk_inventory.py" in proc.stderr,
           {"rc": proc.returncode, "stderr": proc.stderr.decode()[:200]})


if __name__ == "__main__":
    raise SystemExit(main())

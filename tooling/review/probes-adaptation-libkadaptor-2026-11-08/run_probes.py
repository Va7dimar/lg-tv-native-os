"""Independent synthetic counterexamples for adaptation/libkadaptor review.
Never touch catalog archives or production output directories.
"""
from __future__ import annotations

import hashlib
import io
import json
import os
from pathlib import Path
import sys
import tarfile
import tempfile
import traceback
from unittest import mock

TOOLS = Path("/workspace/lg-tv/tooling")
sys.path.insert(0, str(TOOLS))
import adaptation_libkadaptor_phase as ap
import isolate_adaptation_phase as iso

PIN = "soc/libkadaptor-1.0.0-908.3.tar.gz"
OUT = Path("/workspace/lg-tv/tooling/review/probes-adaptation-libkadaptor-2026-11-08")
RESULTS = []


def sha(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def archive(entries):
    buf = io.BytesIO()
    with tarfile.open(fileobj=buf, mode="w:gz") as tf:
        for name, payload in entries:
            info = name if isinstance(name, tarfile.TarInfo) else tarfile.TarInfo(name)
            if info.isreg():
                info.size = len(payload)
                tf.addfile(info, io.BytesIO(payload))
            else:
                tf.addfile(info)
    return buf.getvalue()


def record(name, passed, detail):
    RESULTS.append({"name": name, "passed": bool(passed), "detail": detail})
    mark = "PASS" if passed else "FAIL"
    print(f"[{mark}] {name}: {detail}")


def run():
    tmp = tempfile.TemporaryDirectory(prefix="adaptation-indep-probe-")
    root = Path(tmp.name)
    try:
        _run(root)
    except Exception:
        record("probe_harness", False, traceback.format_exc())
    finally:
        tmp.cleanup()
    (OUT / "probe-results.json").write_text(json.dumps(RESULTS, indent=2) + "\n")
    failed = [r for r in RESULTS if not r["passed"]]
    print(f"\n{len(RESULTS)} probes, {len(failed)} failed")
    return 0 if not failed else 1


def _run(root: Path):
    inner = archive([
        ("README.md", b"hardware notes\n"),
        ("build/config", b"OPTION=y\n"),
        ("LICENSE", b"license\n"),
        ("include/hal/device.hpp", b"int open_device();\n"),
        ("blob.bin", b"raw\0binary"),
        ("README/nested.tar.gz", archive([("secret.txt", b"secret")])),
    ])
    outer_path = root / "synthetic-outer.tar.gz"
    outer_bytes = archive([(PIN, inner), ("soc/kernel.tar.gz", b"k\0notcopied")])
    outer_path.write_bytes(outer_bytes)

    def spec(**changes):
        values = dict(
            outer_bytes=outer_path.stat().st_size,
            outer_sha256=sha(outer_path.read_bytes()),
            target_size=len(inner),
            target_sha256=sha(inner),
        )
        values.update(changes)
        return ap.PhaseSpec.for_tests(**values)

    def limits(**changes):
        return ap.PhaseLimits.for_tests(min_free_disk_bytes=1, **changes)

    # 1. Happy path + unallowlisted not copied + nested not expanded
    out = root / "out-happy"
    out.mkdir()
    result = ap.run_adaptation_phase(outer_path, out, spec=spec(), limits=limits())
    staged = list((out / "staged").iterdir()) if (out / "staged").exists() else []
    secrets = list(out.rglob("secret.txt"))
    kernel = [p for p in staged if "kernel" in p.name]
    selected_readme = (out / "selected" / Path(PIN).name / "README.md").is_file()
    record(
        "happy_copy_select_no_nested_no_other_packages",
        result.ok and len(staged) == 1 and staged[0].name == Path(PIN).name
        and not kernel and not secrets and selected_readme
        and result.document["copied"][0]["verified_before_inner"],
        {
            "ok": result.ok,
            "errors": result.document["errors"],
            "staged": [p.name for p in staged],
            "secrets": [str(p) for p in secrets],
            "copied": result.document.get("copied"),
            "selected_readme": selected_readme,
            "nested_flags": [
                m.get("nested_archive_not_expanded")
                for inner_doc in result.document.get("inners", [])
                for m in inner_doc.get("members", [])
                if m.get("canonical_name") == "README/nested.tar.gz"
            ],
        },
    )

    # 2. Hash verified before parse
    with mock.patch.object(ap.bai, "open_untrusted_tar_gz", side_effect=AssertionError("parsed")) as parser:
        out = root / "out-bad-hash"
        out.mkdir()
        result = ap.run_adaptation_phase(
            outer_path, out, spec=spec(outer_sha256="0" * 64), limits=limits()
        )
        record(
            "outer_hash_before_parse",
            (not result.ok) and parser.call_count == 0
            and any("hash" in e.lower() for e in result.document["errors"]),
            {"ok": result.ok, "errors": result.document["errors"], "parser_calls": parser.call_count},
        )

    # 3. Size verified before parse
    with mock.patch.object(ap.bai, "open_untrusted_tar_gz", side_effect=AssertionError("parsed")) as parser:
        out = root / "out-bad-size"
        out.mkdir()
        result = ap.run_adaptation_phase(
            outer_path, out, spec=spec(outer_bytes=1), limits=limits()
        )
        record(
            "outer_size_before_parse",
            (not result.ok) and parser.call_count == 0
            and any("size" in e.lower() for e in result.document["errors"]),
            {"ok": result.ok, "errors": result.document["errors"], "parser_calls": parser.call_count},
        )

    # 4. Staged rehash before inner
    original_open = ap.bai.open_regular_nofollow

    def tamper(path):
        p = Path(path)
        if p.parent.name == "staged":
            p.write_bytes(b"x" * len(inner))
        return original_open(path)

    out = root / "out-rehash"
    out.mkdir()
    with mock.patch.object(ap.bai, "open_regular_nofollow", side_effect=tamper), \
         mock.patch.object(ap.bai, "open_untrusted_tar_gz", wraps=ap.bai.open_untrusted_tar_gz) as parser:
        result = ap.run_adaptation_phase(outer_path, out, spec=spec(), limits=limits())
        record(
            "staged_rehash_before_inner",
            (not result.ok) and parser.call_count == 1
            and any("staged" in e.lower() and "hash" in e.lower() for e in result.document["errors"]),
            {"ok": result.ok, "errors": result.document["errors"], "parser_calls": parser.call_count},
        )

    # 5. Production pins immutable
    try:
        ap.PhaseSpec(outer_bytes=1, synthetic=False)
        pin_ok = False
        pin_detail = "PhaseSpec accepted mutated production pins"
    except ap.PhaseError as exc:
        pin_ok = "cannot be changed" in str(exc)
        pin_detail = str(exc)
    prod = ap.PhaseSpec()
    pin_values_ok = (
        prod.outer_bytes == 511945894
        and prod.outer_sha256 == "95894dd81e2bb32fd1ced1eb119698f2e1464e6b9b5b5879ea51528d7d5e8832"
        and prod.target_size == 123840909
        and prod.target_sha256 == "46e7e652bc8f6fc9a57ade3baca9b1300a9e8c1bdc4bcde3cb7675116184bf25"
        and ap.TARGET_MEMBER == PIN
        and prod.target_size < 134217728
    )
    record("production_pins_immutable_and_fit_binary_cap", pin_ok and pin_values_ok, {
        "mutation_error": pin_detail,
        "target_size": prod.target_size,
        "binary_cap": 134217728,
        "outer_bytes": prod.outer_bytes,
        "outer_compressed_cap": 536870912,
        "admitted": prod.outer_bytes + prod.target_size,
        "admitted_cap": 1073741824,
    })

    # 6. Synthetic cannot retarget member
    spec_path = root / "bad-spec.json"
    spec_path.write_text(json.dumps(dict(
        outer_bytes=1, outer_sha256="a" * 64, target_size=1, target_sha256="b" * 64,
        member="soc/kernel.tar.gz",
    )))
    try:
        ap.load_synthetic_spec(spec_path)
        record("synthetic_cannot_retarget_member", False, "load_synthetic_spec accepted kernel retarget")
    except ap.PhaseError as exc:
        record("synthetic_cannot_retarget_member", "cannot change" in str(exc), str(exc))

    extra_key = root / "extra-spec.json"
    extra_key.write_text(json.dumps(dict(
        outer_bytes=1, outer_sha256="a" * 64, target_size=1, target_sha256="b" * 64,
        extra="nope",
    )))
    try:
        ap.load_synthetic_spec(extra_key)
        record("synthetic_rejects_unknown_keys", False, "accepted unknown key")
    except ap.PhaseError as exc:
        record("synthetic_rejects_unknown_keys", True, str(exc))

    # 7. Production CLI cannot swap pins / raise floors
    cli_flags = (
        "--expected-outer-sha256", "--expected-outer-bytes", "--test-target",
        "--allow-test-spec", "--min-free-disk-bytes", "--wall-seconds",
        "--address-space-bytes",
    )
    cli_ok = True
    cli_detail = {}
    for flag in cli_flags:
        with mock.patch("sys.stderr", io.StringIO()):
            rc = ap.main(["--outer", "synthetic", "--output-dir", "synthetic", flag, "1"])
        cli_detail[flag] = rc
        if rc == 0:
            cli_ok = False
    record("production_cli_rejects_retarget_and_ceiling_flags", cli_ok, cli_detail)

    # isolate CLI shares the same parser
    iso_ok = True
    iso_detail = {}
    for flag in cli_flags:
        with mock.patch("sys.stderr", io.StringIO()):
            rc = iso.main(["--outer", str(outer_path), "--output-dir", str(root / "iso-cli"), flag, "1"])
        iso_detail[flag] = rc
        if rc == 0:
            iso_ok = False
    record("isolate_cli_rejects_retarget_and_ceiling_flags", iso_ok, iso_detail)

    # 8. Ceilings cannot be raised
    raised = {}
    ok_raise = True
    for key, value in ap.CEILINGS.items():
        try:
            ap.PhaseLimits.for_tests(**{key: value + 1})
            raised[key] = "accepted raise"
            ok_raise = False
        except ap.PhaseLimitError:
            raised[key] = "rejected"
    try:
        ap.PhaseLimits(min_free_disk_bytes=1)
        raised["disk_without_test_flag"] = "accepted below floor"
        ok_raise = False
    except ap.PhaseLimitError:
        raised["disk_without_test_flag"] = "rejected"
    try:
        iso.build_isolation_command(outer_path, root / "out-happy", wall_seconds=121)
        raised["isolate_wall"] = "accepted raise"
        ok_raise = False
    except ap.PhaseLimitError:
        raised["isolate_wall"] = "rejected"
    record("ceilings_cannot_be_raised", ok_raise, raised)

    # 9. Collision marks failed AND overwrites previous index
    out = root / "out-collision"
    out.mkdir()
    old = '{"ok": true, "status": "ok", "kept": "previous-success-index"}'
    (out / "phase.json").write_text(old)
    result = ap.run_adaptation_phase(outer_path, out, spec=spec(), limits=limits())
    new_text = (out / "phase.json").read_text()
    overwritten = old not in new_text and "previous-success-index" not in new_text
    collision = any("collision" in e.lower() for e in result.document["errors"])
    record(
        "index_collision_marks_failed_then_overwrites_old_index",
        (not result.ok) and collision and overwritten and result.status == "failed",
        {
            "ok": result.ok,
            "status": result.status,
            "errors": result.document["errors"],
            "overwritten": overwritten,
            "new_ok": json.loads(new_text).get("ok"),
            "new_errors": json.loads(new_text).get("errors"),
        },
    )
    (OUT / "probe-collision-overwritten-phase.json").write_text(new_text)

    # 10. Shared member budget across outer+inner
    out = root / "out-members"
    out.mkdir()
    result = ap.run_adaptation_phase(outer_path, out, spec=spec(), limits=limits(max_members=1))
    record(
        "shared_member_budget_stops_phase",
        (not result.ok) and any("member" in e.lower() for e in result.document["errors"]),
        {"ok": result.ok, "status": result.status, "errors": result.document["errors"]},
    )

    # 11. Unclaimed payload discarded in bounded chunks
    sizes = []

    class Reader:
        def __init__(self, src):
            self.src = src

        def __enter__(self):
            return self

        def __exit__(self, *args):
            self.src.close()

        def read(self, size=-1):
            sizes.append(size)
            if size < 0 or size > 1024 * 1024:
                raise AssertionError(f"unbounded archive payload read: {size}")
            return self.src.read(size)

        def close(self):
            self.src.close()

    original = ap.bai.open_untrusted_tar_gz

    def open_tar(handle):
        tf = original(handle)
        extract = tf.extractfile
        tf.extractfile = lambda member: Reader(extract(member))
        return tf

    fat = root / "fat-outer.tar.gz"
    fat.write_bytes(archive([("unclaimed.bin", b"x" * 3_000_000), (PIN, inner)]))
    out = root / "out-chunks"
    out.mkdir()
    fat_spec = ap.PhaseSpec.for_tests(
        outer_bytes=fat.stat().st_size,
        outer_sha256=sha(fat.read_bytes()),
        target_size=len(inner),
        target_sha256=sha(inner),
    )
    with mock.patch.object(ap.bai, "open_untrusted_tar_gz", side_effect=open_tar):
        result = ap.run_adaptation_phase(fat, out, spec=fat_spec, limits=limits())
    record(
        "unclaimed_payload_chunked_1mib",
        result.ok and sizes and max(sizes) <= 1024 * 1024,
        {"ok": result.ok, "errors": result.document["errors"], "max_read": max(sizes) if sizes else None, "n_reads": len(sizes)},
    )

    # 12. Isolation command shape
    out = root / "out-iso-shape"
    out.mkdir()
    cmd = iso.build_isolation_command(outer_path, out)
    joined = " ".join(cmd)
    shape_ok = (
        cmd[:4] == ["timeout", "--kill-after=5s", "120", "prlimit"]
        and "--as=1073741824" in cmd
        and "--unshare-all" in cmd
        and "--clearenv" in cmd
        and "--share-net" not in cmd
        and "/home" not in joined
        and "/root" not in joined
        and "/cursor" not in joined
        and "--synthetic-fixture-mode" not in cmd
        and "adaptation_libkadaptor_phase.py" in joined
        and "targeted_core_two_phase.py" not in joined
    )
    record("isolation_command_pins_and_no_home_net", shape_ok, cmd)

    # 13. Launcher rejects symlink outer
    link = root / "link.tar.gz"
    link.symlink_to(outer_path)
    try:
        iso.build_isolation_command(link, out)
        record("launcher_rejects_symlink_outer", False, "accepted symlink outer")
    except Exception as exc:
        record("launcher_rejects_symlink_outer", "symlink" in str(exc).lower() or "nofollow" in str(exc).lower() or type(exc).__name__ == "InputError", f"{type(exc).__name__}: {exc}")

    # 14. Selected directory symlink containment
    out = root / "out-escape"
    out.mkdir()
    (out / "selected").symlink_to(root / "outside-selected")
    result = ap.run_adaptation_phase(outer_path, out, spec=spec(), limits=limits())
    record(
        "selected_symlink_contained",
        (not result.ok)
        and not (root / "outside-selected").exists()
        and any("escape" in e.lower() or "symlink" in e.lower() for e in result.document["errors"]),
        {"ok": result.ok, "errors": result.document["errors"], "outside_exists": (root / "outside-selected").exists()},
    )

    # 15. Production filename required when not synthetic
    out = root / "out-name"
    out.mkdir()
    result = ap.run_adaptation_phase(outer_path, out, spec=ap.PhaseSpec(), limits=limits())
    record(
        "production_requires_pinned_outer_filename",
        (not result.ok) and any("name" in e.lower() for e in result.document["errors"]),
        {"ok": result.ok, "errors": result.document["errors"], "used_name": outer_path.name},
    )

    # 16. charge uses '>' so exact cap is allowed (not a must-fix; document)
    sess_limits = limits(max_members=2)
    # just note the operator
    import inspect
    src = inspect.getsource(ap._Phase.charge)
    record(
        "charge_allows_exact_cap_via_greater_than",
        "self.totals[key] + amount > getattr(self.limits, ceiling)" in src,
        src,
    )

    # 17. noexec residual documented
    out = root / "out-controls"
    out.mkdir()
    result = ap.run_adaptation_phase(outer_path, out, spec=spec(), limits=limits())
    controls = result.document["controls"]
    record(
        "honest_residuals_documented",
        result.ok
        and controls["noexec_output_demonstrated"] is False
        and controls["outer_decoded_regular_files_only"] is True
        and "observation" in controls["disk_reserve_check"]
        and "prlimit" in controls["allocation_backstop"],
        controls,
    )


if __name__ == "__main__":
    raise SystemExit(run())

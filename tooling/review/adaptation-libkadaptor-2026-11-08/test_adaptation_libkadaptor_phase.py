"""Synthetic-only adaptation tests; never access catalog archives."""
from __future__ import annotations

import dataclasses
import gzip
import hashlib
import io
import json
import os
from pathlib import Path
import subprocess
import sys
import tarfile
import tempfile
import unittest
from unittest import mock

TOOLS = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(TOOLS))
import adaptation_libkadaptor_phase as ap
import isolate_adaptation_phase as iso

PIN = "soc/libkadaptor-1.0.0-908.3.tar.gz"


def sha(data):
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


def sparse_archive(origsize=10000):
    def octal(value, width):
        return (oct(value)[2:].rjust(width - 1, "0") + "\0").encode()
    header = bytearray(512)
    header[:11] = b"sparse.bin\0"
    for start, width, value in ((100, 8, 420), (108, 8, 0), (116, 8, 0),
                                (124, 12, 8), (136, 12, 0), (386, 12, 0),
                                (398, 12, 4), (410, 12, origsize - 4),
                                (422, 12, 4), (483, 12, origsize)):
        header[start:start + width] = octal(value, width)
    header[156:157] = tarfile.GNUTYPE_SPARSE
    header[257:263] = b"ustar "
    header[263:265] = b" \0"
    header[148:156] = b"        "
    header[148:156] = f"{sum(header):06o}\0 ".encode()
    return gzip.compress(bytes(header) + b"DATAEND!" + bytes(504 + 1024))


class PhaseTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory(prefix="adaptation-synthetic-")
        self.addCleanup(self.tmp.cleanup)
        self.root = Path(self.tmp.name)
        self.out = self.root / "out"
        self.out.mkdir()
        self.inner = archive([
            ("README.md", b"hardware notes\n"),
            ("build/config", b"OPTION=y\n"),
            ("LICENSE", b"license\n"),
            ("manifest.txt", b"files\n"),
            ("include/hal/device.hpp", b"int open_device();\n"),
            ("other/device_api.h", b"int device_api();\n"),
            ("README.bin", b"bad\0text"),
            ("blob.bin", b"raw\0binary"),
            ("README/nested.tar.gz", archive([("secret.txt", b"secret")])),
        ])
        self.outer = self.root / "synthetic-outer.tar.gz"
        self.make_outer()

    def make_outer(self, entries=None):
        self.outer.write_bytes(archive(entries if entries is not None else [(PIN, self.inner)]))
        return self.outer

    def spec(self, **changes):
        values = dict(outer_bytes=self.outer.stat().st_size,
                      outer_sha256=sha(self.outer.read_bytes()),
                      target_size=len(self.inner), target_sha256=sha(self.inner))
        values.update(changes)
        return ap.PhaseSpec.for_tests(**values)

    def limits(self, **changes):
        return ap.PhaseLimits.for_tests(min_free_disk_bytes=1, **changes)

    def run_phase(self, **kwargs):
        kwargs.setdefault("spec", self.spec())
        kwargs.setdefault("limits", self.limits())
        return ap.run_adaptation_phase(self.outer, self.out, **kwargs)

    def failed(self, result, reason=None):
        self.assertFalse(result.ok)
        self.assertIn(result.status, {"failed", "partial"})
        doc = json.loads((self.out / "phase.json").read_text())
        self.assertFalse(doc["ok"])
        if reason:
            self.assertIn(reason, " ".join(doc["errors"]).lower())
        return doc

    def test_exact_copy_and_nul_free_evidence(self):
        result = self.run_phase()
        self.assertTrue(result.ok, result.document)
        staged = self.out / "staged" / Path(PIN).name
        self.assertEqual(staged.read_bytes(), self.inner)
        self.assertIn(b"\0", self.inner)
        self.assertEqual(staged.stat().st_mode & 0o777, 0o644)
        selected = self.out / "selected" / Path(PIN).name
        for path in ("README.md", "build/config", "LICENSE", "manifest.txt",
                     "include/hal/device.hpp", "other/device_api.h"):
            self.assertTrue((selected / path).is_file(), path)
            self.assertEqual((selected / path).stat().st_mode & 0o777, 0o644)
        self.assertFalse((selected / "README.bin").exists())
        self.assertFalse((selected / "blob.bin").exists())
        self.assertTrue(result.document["copied"][0]["verified_before_inner"])

    def test_unallowlisted_packages_are_not_copied(self):
        self.make_outer([(PIN, self.inner), ("soc/kernel.tar.gz", b"k\0"),
                         ("soc/bootcode.tar.gz", b"b"), ("soc/chromium.tar.gz", b"c"),
                         ("soc/other.tar.gz", b"other")])
        result = self.run_phase()
        self.assertTrue(result.ok)
        self.assertEqual([p.name for p in (self.out / "staged").iterdir()], [Path(PIN).name])
        self.assertEqual([r["member"] for r in result.document["copied"]], [PIN])

    def test_nested_inner_archive_metadata_only(self):
        result = self.run_phase()
        self.assertTrue(result.ok)
        self.assertFalse(list(self.out.rglob("secret.txt")))
        nested = [m for m in result.document["inners"][0]["members"]
                  if m["canonical_name"] == "README/nested.tar.gz"]
        self.assertEqual(len(nested), 1)
        self.assertTrue(nested[0]["nested_archive_not_expanded"])
        self.assertFalse(nested[0]["selected"])

    def test_outer_hash_verified_before_tar_parser(self):
        with mock.patch.object(ap.bai, "open_untrusted_tar_gz", side_effect=AssertionError("parsed")) as parser:
            self.failed(self.run_phase(spec=self.spec(outer_sha256="0" * 64)), "outer hash")
            parser.assert_not_called()

    def test_outer_size_verified_before_tar_parser(self):
        with mock.patch.object(ap.bai, "open_untrusted_tar_gz") as parser:
            self.failed(self.run_phase(spec=self.spec(outer_bytes=1)), "outer size")
            parser.assert_not_called()

    def test_wrong_target_hash(self):
        self.failed(self.run_phase(spec=self.spec(target_sha256="0" * 64)), "hash")
        self.assertFalse((self.out / "selected").exists())

    def test_wrong_target_size(self):
        self.failed(self.run_phase(spec=self.spec(target_size=len(self.inner) + 1)), "size")

    def test_missing_target(self):
        self.make_outer([("soc/other.tar.gz", b"other")])
        self.failed(self.run_phase(), "missing")

    def test_target_path_must_be_exact_raw_name(self):
        self.make_outer([("soc/./" + Path(PIN).name, self.inner)])
        self.failed(self.run_phase(), "exact")

    def test_target_types_rejected(self):
        for kind in (tarfile.SYMTYPE, tarfile.LNKTYPE, tarfile.DIRTYPE, tarfile.FIFOTYPE):
            with self.subTest(kind=kind):
                out = self.root / ("out-" + kind.decode())
                info = tarfile.TarInfo(PIN)
                info.type, info.linkname = kind, "safe"
                self.make_outer([(info, b"")])
                result = ap.run_adaptation_phase(self.outer, out, spec=self.spec(), limits=self.limits())
                self.assertFalse(result.ok)
                self.assertEqual(result.status, "failed")

    def test_duplicate_outer_member(self):
        self.make_outer([(PIN, self.inner), ("soc/./" + Path(PIN).name, self.inner)])
        self.failed(self.run_phase(), "duplicate")

    def test_duplicate_inner_member(self):
        self.inner = archive([("README", b"one"), ("./README", b"two")])
        self.make_outer()
        self.failed(self.run_phase(), "duplicate")

    def test_outer_traversal(self):
        self.make_outer([(PIN, self.inner), ("../escape", b"x")])
        self.failed(self.run_phase(), "parent_escape")

    def test_inner_absolute_path(self):
        self.inner = archive([("/absolute", b"x")])
        self.make_outer()
        self.failed(self.run_phase(), "absolute_path")

    def test_unsafe_inner_link(self):
        info = tarfile.TarInfo("link")
        info.type, info.linkname = tarfile.SYMTYPE, "../../outside"
        self.inner = archive([(info, b"")])
        self.make_outer()
        self.failed(self.run_phase(), "unsafe_link")

    def test_safe_links_recorded_never_followed(self):
        info = tarfile.TarInfo("link")
        info.type, info.linkname = tarfile.SYMTYPE, "README"
        self.inner = archive([("README", b"text"), (info, b"")])
        self.make_outer()
        result = self.run_phase()
        self.assertTrue(result.ok)
        self.assertFalse(list(self.out.rglob("link")))

    def test_shared_member_budget(self):
        self.failed(self.run_phase(limits=self.limits(max_members=1)), "members")

    def test_shared_pathname_budget(self):
        self.failed(self.run_phase(limits=self.limits(max_pathname_bytes=len(PIN))), "pathname")

    def test_outer_decoded_budget(self):
        self.make_outer([(PIN, self.inner), ("extra", b"x")])
        self.failed(self.run_phase(limits=self.limits(max_outer_decoded_bytes=len(self.inner))), "outer_decoded")

    def test_outer_decoded_counts_regular_payload_only(self):
        directory = tarfile.TarInfo("dir")
        directory.type, directory.size = tarfile.DIRTYPE, 900000
        info = tarfile.TarInfo(PIN)
        info.pax_headers = {"comment": "metadata" * 500}
        self.make_outer([(directory, b""), (info, self.inner)])
        result = self.run_phase(limits=self.limits(max_outer_decoded_bytes=len(self.inner)))
        self.assertTrue(result.ok, result.document)
        self.assertEqual(result.document["totals"]["outer_decoded_bytes"], len(self.inner))

    def test_phase_expanded_double_charges_binary_copy(self):
        self.failed(self.run_phase(limits=self.limits(max_phase_expanded_bytes=2 * len(self.inner) - 1)), "expanded")

    def test_phase_expanded_charges_selected_copies(self):
        self.inner = archive([("README", b"a" * 30)])
        self.make_outer()
        self.failed(self.run_phase(limits=self.limits(max_phase_expanded_bytes=2 * len(self.inner) + 59)), "expanded")

    def test_binary_each_budget(self):
        self.failed(self.run_phase(limits=self.limits(max_binary_each_bytes=len(self.inner) - 1)), "binary")

    def test_binary_combined_budget(self):
        self.failed(self.run_phase(limits=self.limits(max_binary_combined_bytes=len(self.inner) - 1)), "binary")

    def test_admitted_compressed_budget(self):
        self.failed(self.run_phase(limits=self.limits(max_admitted_compressed_bytes=self.outer.stat().st_size + len(self.inner) - 1)), "admitted")

    def test_outer_compressed_budget(self):
        self.failed(self.run_phase(limits=self.limits(max_outer_compressed_bytes=self.outer.stat().st_size - 1)), "outer_compressed")

    def test_selected_combined_budget(self):
        self.failed(self.run_phase(limits=self.limits(max_selected_combined_bytes=3)), "selected_combined")

    def test_selected_each_budget(self):
        self.failed(self.run_phase(limits=self.limits(max_selected_text_member_bytes=3)), "selected_text")

    def test_sparse_logical_size_charged(self):
        self.inner = sparse_archive()
        self.make_outer()
        self.failed(self.run_phase(limits=self.limits(max_phase_expanded_bytes=2 * len(self.inner) + 9999)), "expanded")

    def test_global_deadline_shared_through_inner(self):
        now = [0.0]
        original = ap.bai.open_untrusted_tar_gz
        calls = []
        def parser(handle):
            calls.append(now[0])
            if len(calls) == 1:
                now[0] = 0.75
            else:
                now[0] = 1.25
            return original(handle)
        with mock.patch.object(ap.bai, "open_untrusted_tar_gz", side_effect=parser):
            self.failed(self.run_phase(limits=self.limits(wall_seconds=1), clock=lambda: now[0]), "wall")
        self.assertEqual(len(calls), 2)

    def test_disk_failure_before_outer_open(self):
        with mock.patch.object(ap.shutil, "disk_usage", return_value=type("Usage", (), {"free": 0})()), \
             mock.patch.object(ap.bai, "open_regular_nofollow") as opener:
            self.failed(self.run_phase(), "disk")
            opener.assert_not_called()

    def test_disk_rechecked_before_staged_write(self):
        counts = [0]
        def usage(path):
            counts[0] += 1
            return type("Usage", (), {"free": 10**12 if counts[0] == 1 else 0})()
        with mock.patch.object(ap.shutil, "disk_usage", side_effect=usage):
            self.failed(self.run_phase(), "disk")
        self.assertFalse(list(self.out.rglob("*.tar.gz")))

    def test_existing_phase_json_fails_honestly(self):
        (self.out / "phase.json").write_text('{"ok": true}')
        self.failed(self.run_phase(), "collision")

    def test_existing_phase_markdown_fails_honestly(self):
        (self.out / "phase.md").write_text("old")
        self.failed(self.run_phase(), "collision")

    def test_index_symlink_escape_uses_failed_fallback(self):
        outside = self.root / "outside.json"
        outside.write_text("unchanged")
        (self.out / "phase.json").symlink_to(outside)
        result = self.run_phase()
        self.assertFalse(result.ok)
        self.assertEqual(result.status, "failed")
        self.assertEqual(outside.read_text(), "unchanged")
        fallback = json.loads((self.out / "phase-failed.json").read_text())
        self.assertFalse(fallback["ok"])

    def test_markdown_directory_collision(self):
        (self.out / "phase.md").mkdir()
        self.failed(self.run_phase(), "collision")

    def test_selected_file_collision_preserves_existing_file(self):
        existing = self.out / "selected" / Path(PIN).name / "README.md"
        existing.parent.mkdir(parents=True)
        existing.write_bytes(b"existing")
        self.failed(self.run_phase())
        self.assertEqual(existing.read_bytes(), b"existing")

    def test_staged_collision_fails(self):
        (self.out / "staged").mkdir()
        (self.out / "staged" / Path(PIN).name).write_bytes(b"old")
        self.failed(self.run_phase(), "collision")

    def test_selected_write_escape_fails(self):
        (self.out / "selected").symlink_to(self.root / "outside")
        self.failed(self.run_phase(), "escape")
        self.assertFalse((self.root / "outside").exists())

    def test_write_oserror_is_failed_index(self):
        with mock.patch.object(ap.bai, "_write_selected_file", side_effect=OSError("synthetic write failure")):
            self.failed(self.run_phase(), "synthetic write failure")

    def test_staged_rehash_before_inner(self):
        original = ap.bai.open_regular_nofollow
        def open_file(path):
            if Path(path).parent.name == "staged":
                Path(path).write_bytes(b"x" * len(self.inner))
            return original(path)
        with mock.patch.object(ap.bai, "open_regular_nofollow", side_effect=open_file), \
             mock.patch.object(ap.bai, "open_untrusted_tar_gz", wraps=ap.bai.open_untrusted_tar_gz) as parser:
            self.failed(self.run_phase(), "staged hash")
            self.assertEqual(parser.call_count, 1)

    def test_symlink_outer_rejected(self):
        link = self.root / "link.tar.gz"
        link.symlink_to(self.outer)
        result = ap.run_adaptation_phase(link, self.out, spec=self.spec(), limits=self.limits())
        self.failed(result, "symlink")

    def test_streaming_reads_are_bounded(self):
        original = ap.bai.open_untrusted_tar_gz
        sizes = []
        class Reader:
            def __init__(self, src): self.src = src
            def __enter__(self): return self
            def __exit__(self, *args): self.src.close()
            def read(self, size=-1):
                sizes.append(size)
                if size < 0 or size > 1024 * 1024:
                    raise AssertionError("unbounded archive payload read")
                return self.src.read(size)
            def close(self): self.src.close()
        def open_tar(handle):
            tf = original(handle)
            extract = tf.extractfile
            tf.extractfile = lambda member: Reader(extract(member))
            return tf
        self.make_outer([("unclaimed.bin", b"x" * 3000000), (PIN, self.inner)])
        with mock.patch.object(ap.bai, "open_untrusted_tar_gz", side_effect=open_tar):
            result = self.run_phase()
        self.assertTrue(result.ok, result.document)
        self.assertTrue(sizes)
        self.assertLessEqual(max(sizes), 1024 * 1024)

    def test_controls_documented(self):
        result = self.run_phase()
        self.assertTrue(result.ok)
        controls = result.document["controls"]
        self.assertFalse(controls["noexec_output_demonstrated"])
        for key in ("isolation_required_for_untrusted_inputs",
                    "parser_allocates_extended_headers_before_semantic_limits",
                    "outer_decoded_regular_files_only"):
            self.assertTrue(controls[key], key)
        self.assertIn("prlimit", controls["allocation_backstop"])
        self.assertIn("observation", controls["disk_reserve_check"])
        self.assertTrue(result.document["disk_observations"])


class ContractTests(unittest.TestCase):
    def test_production_pins(self):
        self.assertEqual(ap.TARGET_MEMBER, PIN)
        spec = ap.PhaseSpec()
        self.assertEqual(spec.outer_bytes, 511945894)
        self.assertEqual(spec.outer_sha256, "95894dd81e2bb32fd1ced1eb119698f2e1464e6b9b5b5879ea51528d7d5e8832")
        self.assertEqual(spec.target_size, 123840909)
        self.assertEqual(spec.target_sha256, "46e7e652bc8f6fc9a57ade3baca9b1300a9e8c1bdc4bcde3cb7675116184bf25")

    def test_limits_cannot_be_raised(self):
        expected = dict(wall_seconds=120, address_space_bytes=1073741824,
                        max_members=200000, max_pathname_bytes=100000000,
                        max_phase_expanded_bytes=4294967296,
                        max_outer_compressed_bytes=536870912, max_outer_decoded_bytes=671088640,
                        max_binary_each_bytes=134217728, max_binary_combined_bytes=134217728,
                        max_admitted_compressed_bytes=1073741824,
                        max_selected_text_member_bytes=16777216, max_selected_combined_bytes=67108864)
        limits = ap.PhaseLimits()
        for key, value in expected.items():
            with self.subTest(key=key):
                self.assertEqual(getattr(limits, key), value)
                with self.assertRaises(ap.PhaseLimitError):
                    ap.PhaseLimits.for_tests(**{key: value + 1})
        with self.assertRaises(ap.PhaseLimitError):
            ap.PhaseLimits(min_free_disk_bytes=1)
        self.assertEqual(limits.min_free_disk_bytes, 10737418240)

    def test_production_cli_cannot_swap_pins_or_disk_floor(self):
        for flag in ("--expected-outer-sha256", "--expected-outer-bytes", "--test-target",
                     "--allow-test-spec", "--min-free-disk-bytes", "--wall-seconds"):
            with self.subTest(flag=flag), mock.patch("sys.stderr", io.StringIO()):
                self.assertNotEqual(ap.main(["--outer", "synthetic", "--output-dir", "synthetic", flag, "1"]), 0)

    def test_evidence_names(self):
        for name in ("README.txt", "Makefile", ".config", "foo_defconfig", "Kconfig",
                     "include/device.h", "hardware/device.hpp", "api/x.h", "adaptor/x.h",
                     "kadaptor/x.hpp", "some_api.h"):
            self.assertTrue(ap.is_evidence_plaintext_name(name), name)
        for name in ("scripts/run.sh", "unrelated/private.h", "blob.bin", "README/a.tar.gz"):
            self.assertFalse(ap.is_evidence_plaintext_name(name), name)

    def test_synthetic_spec_cannot_change_member_path(self):
        with tempfile.TemporaryDirectory(prefix="adaptation-spec-") as tmp:
            path = Path(tmp) / "spec.json"
            path.write_text(json.dumps(dict(outer_bytes=1, outer_sha256="a" * 64,
                                            target_size=1, target_sha256="b" * 64,
                                            member="soc/kernel.tar.gz")))
            with self.assertRaises(ap.PhaseError):
                ap.load_synthetic_spec(path)

    def test_invalid_spec_cli_records_failed_index(self):
        with tempfile.TemporaryDirectory(prefix="adaptation-invalid-spec-") as tmp:
            root = Path(tmp)
            spec = root / "spec.json"
            spec.write_text('{"member": "soc/kernel.tar.gz"}')
            out = root / "out"
            with mock.patch("sys.stderr", io.StringIO()):
                rc = ap.main(["--outer", str(root / "synthetic.tar.gz"),
                              "--output-dir", str(out), "--synthetic-fixture-mode", str(spec)])
            self.assertNotEqual(rc, 0)
            self.assertTrue((out / "phase.json").is_file())
            self.assertFalse(json.loads((out / "phase.json").read_text())["ok"])


class IsolationTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory(prefix="adaptation-isolation-synthetic-")
        self.addCleanup(self.tmp.cleanup)
        self.root = Path(self.tmp.name)
        self.outer = self.root / "synthetic-outer.tar.gz"
        self.outer.write_bytes(b"synthetic")
        self.out = self.root / "out"
        self.out.mkdir()

    def test_isolation_command_shape(self):
        cmd = iso.build_isolation_command(self.outer, self.out)
        self.assertEqual(cmd[:4], ["timeout", "--kill-after=5s", "120", "prlimit"])
        for flag in ("--as=1073741824", "--cpu=120", "--core=0", "--nofile=64",
                     "--unshare-all", "--die-with-parent", "--new-session", "--clearenv"):
            self.assertIn(flag, cmd)
        for bad in ("--share-net", "/home", "/root", "/cursor"):
            self.assertNotIn(bad, cmd)
        self.assertIn("PYTHONPATH", cmd)
        self.assertIn("/tool", cmd)
        self.assertNotIn("targeted_core_two_phase.py", " ".join(cmd))
        ro = [(cmd[i + 1], cmd[i + 2]) for i, value in enumerate(cmd) if value == "--ro-bind"]
        self.assertEqual(len(ro), 4)
        self.assertIn(("/usr", "/usr"), ro)
        self.assertIn((str(TOOLS / "adaptation_libkadaptor_phase.py"), "/tool/adaptation_libkadaptor_phase.py"), ro)
        self.assertIn((str(TOOLS / "bounded_archive_inventory.py"), "/tool/bounded_archive_inventory.py"), ro)
        self.assertEqual([cmd[i+1:i+3] for i, v in enumerate(cmd) if v == "--bind"], [[str(self.out), "/output"]])
        for target in ("/bin", "/lib", "/lib64"):
            self.assertIn(target, cmd)
        self.assertNotIn("--synthetic-fixture-mode", cmd)

    def test_launcher_rejects_symlink_outer(self):
        link = self.root / "link.tar.gz"
        link.symlink_to(self.outer)
        with self.assertRaises(ap.bai.InputError):
            iso.build_isolation_command(link, self.out)

    def test_launcher_input_error_records_failed_index(self):
        link = self.root / "link.tar.gz"
        link.symlink_to(self.outer)
        with mock.patch("sys.stderr", io.StringIO()):
            rc = iso.main(["--outer", str(link), "--output-dir", str(self.out)])
        self.assertNotEqual(rc, 0)
        self.assertTrue((self.out / "phase.json").is_file())
        self.assertFalse(json.loads((self.out / "phase.json").read_text())["ok"])

    def test_isolation_integration_synthetic_mode_only(self):
        inner = archive([("README", b"isolation evidence\n"), ("include/hal/x.h", b"int x();")])
        self.outer.write_bytes(archive([(PIN, inner)]))
        spec = self.root / "spec.json"
        spec.write_text(json.dumps(dict(outer_bytes=self.outer.stat().st_size,
                                        outer_sha256=sha(self.outer.read_bytes()),
                                        target_size=len(inner), target_sha256=sha(inner))))
        rc = iso.main(["--outer", str(self.outer), "--output-dir", str(self.out),
                       "--synthetic-fixture-mode", str(spec)])
        self.assertEqual(rc, 0)
        doc = json.loads((self.out / "phase.json").read_text())
        self.assertTrue(doc["ok"])
        self.assertFalse(doc["controls"]["noexec_output_demonstrated"])
        for key in ("home_box_visible", "root_ssh_visible", "cursor_visible"):
            self.assertFalse(doc["isolation_observation"][key])
        launch = json.loads((self.out / "launcher-result.json").read_text())
        self.assertFalse(launch["noexec_output_demonstrated"])
        self.assertFalse(launch["share_net"])
        self.assertNotEqual(launch["host_net_ns"], launch["sandbox_net_ns"])
        self.assertIn("--synthetic-fixture-mode", launch["command"])
        self.assertEqual(launch["command"].count("--ro-bind"), 5)


if __name__ == "__main__":
    unittest.main()

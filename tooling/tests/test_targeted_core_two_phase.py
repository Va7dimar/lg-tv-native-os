"""Synthetic tests for the CORE TWO targeted inner phase. No LG catalog inputs."""
from __future__ import annotations

import gzip
import hashlib
import io
import json
import os
import sys
import tarfile
import tempfile
import unittest
from pathlib import Path

TOOL_DIR = Path(__file__).resolve().parents[1]
if str(TOOL_DIR) not in sys.path:
    sys.path.insert(0, str(TOOL_DIR))

import targeted_core_two_phase as tcp  # noqa: E402


CATALOG_FILENAMES = (
    "webOS 6.0 KLP_1.0_1.tar.gz",
    "webOS 6.0 KLP_1.0_2.tar.gz",
    "webOS 6.0 KLP_1.0_3.tar.gz",
)


def _sha256(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def _inner_targz(files: dict[str, bytes]) -> bytes:
    buf = io.BytesIO()
    with tarfile.open(fileobj=buf, mode="w:gz") as tf:
        for name, data in files.items():
            info = tarfile.TarInfo(name)
            info.size = len(data)
            info.mode = 0o644
            info.type = tarfile.REGTYPE
            tf.addfile(info, io.BytesIO(data))
    return buf.getvalue()


def _outer_targz(path: Path, members: dict[str, bytes]) -> Path:
    with tarfile.open(path, "w:gz") as tf:
        for name, data in members.items():
            info = tarfile.TarInfo(name)
            info.size = len(data)
            info.mode = 0o644
            info.type = tarfile.REGTYPE
            tf.addfile(info, io.BytesIO(data))
    return path


def _write_gnu_sparse_member_bytes(name: str = "sparse.bin", origsize: int = 10_000) -> bytes:
    def octal(val: int, width: int) -> bytes:
        return (oct(val)[2:].rjust(width - 1, "0") + "\0").encode("ascii")

    header = bytearray(512)
    encoded = name.encode("ascii") + b"\0"
    header[0 : len(encoded)] = encoded
    header[100:108] = octal(0o644, 8)
    header[108:116] = octal(0, 8)
    header[116:124] = octal(0, 8)
    header[124:136] = octal(8, 12)
    header[136:148] = octal(0, 12)
    header[156:157] = tarfile.GNUTYPE_SPARSE
    header[257:263] = b"ustar "
    header[263:265] = b" \0"
    header[386:398] = octal(0, 12)
    header[398:410] = octal(4, 12)
    header[410:422] = octal(origsize - 4, 12)
    header[422:434] = octal(4, 12)
    header[482] = 0
    header[483:495] = octal(origsize, 12)
    header[148:156] = b"        "
    chk = sum(header)
    header[148:156] = f"{chk:06o}\0 ".encode("ascii")
    payload = b"DATAEND!" + bytes(512 - 8)
    raw = bytes(header) + payload + bytes(1024)
    out = io.BytesIO()
    with gzip.GzipFile(fileobj=out, mode="wb") as handle:
        handle.write(raw)
    return out.getvalue()


class AllowlistPinTests(unittest.TestCase):
    def test_core_two_pins_exact_targets_and_excludes_libkadaptor(self):
        names = [target.member for target in tcp.CORE_TWO_TARGETS]
        self.assertEqual(
            names,
            [
                "soc/kernel-1.0.0-711..4.tar.gz",
                "soc/bootcode-1.0.0-1099.7.tar.gz",
            ],
        )
        self.assertEqual(tcp.KERNEL_BYTES, 170350960)
        self.assertEqual(tcp.BOOTCODE_BYTES, 12014324)
        self.assertEqual(
            tcp.KERNEL_SHA256,
            "110f08578519954be3113108ca461d4190d387c3cbb6e50d648274c9dcaf9962",
        )
        self.assertEqual(
            tcp.BOOTCODE_SHA256,
            "b88f252cf9ae4f4535e015959916cd87067f0e6cf551ef0f189cdc2f4365e23e",
        )
        self.assertEqual(tcp.OUTER_BYTES, 511945894)
        self.assertTrue(all("libkadaptor" not in name for name in names))

    def test_phase_limits_cannot_be_raised(self):
        with self.assertRaises(tcp.PhaseLimitError):
            tcp.PhaseLimits(max_binary_each_bytes=209715200 + 1)
        with self.assertRaises(tcp.PhaseLimitError):
            tcp.PhaseLimits(wall_seconds=121)
        with self.assertRaises(tcp.PhaseLimitError):
            tcp.PhaseLimits(max_phase_expanded_bytes=4294967296 + 1)


class EvidenceNameTests(unittest.TestCase):
    def test_evidence_names_accepted(self):
        for name in (
            "README",
            "README.md",
            "LICENSE",
            "COPYING",
            "manifest.txt",
            "build/config",
            "board/platform.h",
            "arch/arm/configs/foo_defconfig",
            ".config",
            "Kconfig",
        ):
            self.assertTrue(tcp.is_evidence_plaintext_name(name), name)

    def test_non_evidence_names_rejected(self):
        for name in ("vmlinux.bin", "image.img", "scripts/doit.sh", "soc/extra.tar.gz"):
            self.assertFalse(tcp.is_evidence_plaintext_name(name), name)


class PhaseBehaviorTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory(prefix="core2-")
        self.root = Path(self.tmp.name)
        self.out = self.root / "out"
        self.out.mkdir()
        self.fx = self.root / "fx"
        self.fx.mkdir()
        self.kernel_payload = _inner_targz(
            {
                "README": b"kernel board documentation\n",
                "arch/arm/configs/foo_defconfig": b"CONFIG_FOO=y\n",
                "nested/extra.tar.gz": _inner_targz({"secret.txt": b"nope"}),
                "blob.bin": b"elf\x00binary",
            }
        )
        self.boot_payload = _inner_targz(
            {
                "README.md": b"bootcode license and build notes\n",
                "LICENSE": b"license text\n",
            }
        )
        self.kernel_sha = _sha256(self.kernel_payload)
        self.boot_sha = _sha256(self.boot_payload)

    def tearDown(self):
        self.tmp.cleanup()

    def _spec(self, **overrides):
        extras = overrides.pop("extra_targets", ())
        targets = overrides.pop(
            "targets",
            (
                tcp.TargetSpec(tcp.KERNEL_MEMBER, len(self.kernel_payload), self.kernel_sha),
                tcp.TargetSpec(tcp.BOOTCODE_MEMBER, len(self.boot_payload), self.boot_sha),
            ),
        )
        return tcp.PhaseSpec.for_tests(
            outer_name="outer.tar.gz",
            outer_bytes=overrides.pop("outer_bytes", None),
            outer_sha256=overrides.pop("outer_sha256", None),
            targets=targets + tuple(extras),
            **overrides,
        )

    def _limits(self, **kwargs):
        kwargs.setdefault("min_free_disk_bytes", 1)
        return tcp.PhaseLimits.for_tests(**kwargs)

    def _outer(self, extra: dict[str, bytes] | None = None, include_targets: bool = True) -> Path:
        members = {}
        if include_targets:
            members[tcp.KERNEL_MEMBER] = self.kernel_payload
            members[tcp.BOOTCODE_MEMBER] = self.boot_payload
        if extra:
            members.update(extra)
        path = self.fx / "outer.tar.gz"
        return _outer_targz(path, members)

    def _run(self, outer: Path, **kwargs):
        limits = kwargs.pop("limits", self._limits())
        spec = kwargs.pop("spec", None)
        if spec is None:
            data = outer.read_bytes()
            spec = self._spec(outer_bytes=len(data), outer_sha256=_sha256(data))
        return tcp.run_core_two_phase(outer, self.out, spec=spec, limits=limits, **kwargs)

    def test_exact_copy_selects_evidence_allows_nul_in_binary_only(self):
        outer = self._outer()
        result = self._run(outer)
        self.assertTrue(result.ok)
        self.assertEqual(result.status, "ok")
        staged_k = self.out / "staged" / Path(tcp.KERNEL_MEMBER).name
        staged_b = self.out / "staged" / Path(tcp.BOOTCODE_MEMBER).name
        self.assertEqual(staged_k.read_bytes(), self.kernel_payload)
        self.assertEqual(staged_b.read_bytes(), self.boot_payload)
        self.assertEqual(os.stat(staged_k).st_mode & 0o111, 0)
        readme = self.out / "selected" / Path(tcp.KERNEL_MEMBER).name / "README"
        self.assertTrue(readme.is_file())
        self.assertEqual(readme.read_bytes(), b"kernel board documentation\n")
        self.assertFalse(any(self.out.rglob("blob.bin")))
        self.assertFalse(any(self.out.rglob("secret.txt")))
        payload = json.loads((self.out / "phase.json").read_text(encoding="utf-8"))
        self.assertTrue(payload["ok"])
        self.assertFalse(payload["controls"]["noexec_output_demonstrated"])
        self.assertTrue(payload["controls"]["isolation_required_for_untrusted_inputs"])

    def test_unallowlisted_libkadaptor_is_not_copied(self):
        extra = {tcp.LIBKADAPTOR_MEMBER: b"adaptor\x00payload"}
        outer = self._outer(extra=extra)
        result = self._run(outer)
        self.assertTrue(result.ok)
        self.assertFalse((self.out / "staged" / Path(tcp.LIBKADAPTOR_MEMBER).name).exists())
        copied = [item["member"] for item in result.document.get("copied", [])]
        self.assertNotIn(tcp.LIBKADAPTOR_MEMBER, copied)

    def test_oversize_binary_rejected(self):
        outer = self._outer()
        result = self._run(outer, limits=self._limits(max_binary_each_bytes=10))
        self.assertFalse(result.ok)
        self.assertNotEqual(result.status, "ok")
        payload = json.loads((self.out / "phase.json").read_text(encoding="utf-8"))
        self.assertFalse(payload["ok"])

    def test_wrong_hash_rejected(self):
        outer = self._outer()
        data = outer.read_bytes()
        spec = self._spec(outer_bytes=len(data), outer_sha256=_sha256(data))
        bad_targets = (
            tcp.TargetSpec(tcp.KERNEL_MEMBER, len(self.kernel_payload), "0" * 64),
            tcp.TargetSpec(tcp.BOOTCODE_MEMBER, len(self.boot_payload), self.boot_sha),
        )
        spec = tcp.PhaseSpec.for_tests(
            outer_name="outer.tar.gz",
            outer_bytes=len(data),
            outer_sha256=_sha256(data),
            targets=bad_targets,
        )
        result = self._run(outer, spec=spec)
        self.assertFalse(result.ok)
        self.assertIn("hash", " ".join(result.document.get("errors", [])).lower())

    def test_wrong_size_rejected(self):
        outer = self._outer()
        data = outer.read_bytes()
        spec = tcp.PhaseSpec.for_tests(
            outer_name="outer.tar.gz",
            outer_bytes=len(data),
            outer_sha256=_sha256(data),
            targets=(
                tcp.TargetSpec(tcp.KERNEL_MEMBER, len(self.kernel_payload) + 5, self.kernel_sha),
                tcp.TargetSpec(tcp.BOOTCODE_MEMBER, len(self.boot_payload), self.boot_sha),
            ),
        )
        result = self._run(outer, spec=spec)
        self.assertFalse(result.ok)
        self.assertIn("size", " ".join(result.document.get("errors", [])).lower())

    def test_missing_target_rejected(self):
        path = _outer_targz(self.fx / "outer.tar.gz", {tcp.KERNEL_MEMBER: self.kernel_payload})
        data = path.read_bytes()
        spec = self._spec(outer_bytes=len(data), outer_sha256=_sha256(data))
        result = self._run(path, spec=spec)
        self.assertFalse(result.ok)
        self.assertIn("missing", " ".join(result.document.get("errors", [])).lower())

    def test_symlink_target_rejected(self):
        path = self.fx / "outer.tar.gz"
        with tarfile.open(path, "w:gz") as tf:
            link = tarfile.TarInfo(tcp.KERNEL_MEMBER)
            link.type = tarfile.SYMTYPE
            link.linkname = "elsewhere.tar.gz"
            tf.addfile(link)
            info = tarfile.TarInfo(tcp.BOOTCODE_MEMBER)
            info.size = len(self.boot_payload)
            tf.addfile(info, io.BytesIO(self.boot_payload))
        data = path.read_bytes()
        spec = self._spec(outer_bytes=len(data), outer_sha256=_sha256(data))
        result = self._run(path, spec=spec)
        self.assertFalse(result.ok)

    def test_duplicate_target_rejected(self):
        path = self.fx / "outer.tar.gz"
        with tarfile.open(path, "w:gz") as tf:
            for name, payload in (
                (tcp.KERNEL_MEMBER, self.kernel_payload),
                (tcp.KERNEL_MEMBER, self.kernel_payload),
                (tcp.BOOTCODE_MEMBER, self.boot_payload),
            ):
                info = tarfile.TarInfo(name)
                info.size = len(payload)
                tf.addfile(info, io.BytesIO(payload))
        data = path.read_bytes()
        result = self._run(path, spec=self._spec(outer_bytes=len(data), outer_sha256=_sha256(data)))
        self.assertFalse(result.ok)
        self.assertIn("duplicate", " ".join(result.document.get("errors", [])).lower())

    def test_absolute_and_parent_paths_fail_closed(self):
        extra = {"../escape.txt": b"x", "/abs/file": b"y"}
        # tarfile may rewrite names; craft raw members via TarInfo
        path = self.fx / "outer.tar.gz"
        with tarfile.open(path, "w:gz") as tf:
            for name, payload in (
                (tcp.KERNEL_MEMBER, self.kernel_payload),
                (tcp.BOOTCODE_MEMBER, self.boot_payload),
                ("../escape.txt", b"x"),
            ):
                info = tarfile.TarInfo(name)
                info.size = len(payload)
                tf.addfile(info, io.BytesIO(payload))
        data = path.read_bytes()
        result = self._run(path, spec=self._spec(outer_bytes=len(data), outer_sha256=_sha256(data)))
        self.assertFalse(result.ok)

    def test_inner_nested_archive_not_expanded(self):
        outer = self._outer()
        result = self._run(outer)
        self.assertTrue(result.ok)
        self.assertFalse(any(self.out.rglob("secret.txt")))
        inners = result.document.get("inners", [])
        nested_flags = [
            member.get("nested_archive_not_expanded")
            for archive in inners
            for member in archive.get("members", [])
            if member.get("canonical_name") == "nested/extra.tar.gz"
        ]
        self.assertTrue(nested_flags)
        self.assertTrue(all(nested_flags))

    def test_combined_binary_budget(self):
        outer = self._outer()
        total = len(self.kernel_payload) + len(self.boot_payload)
        result = self._run(outer, limits=self._limits(max_binary_combined_bytes=total - 1))
        self.assertFalse(result.ok)
        self.assertIn("binary", " ".join(result.document.get("errors", [])).lower())

    def test_outer_decoded_budget_is_shared(self):
        padding = b"Z" * 200
        extra = {"padding.bin": padding}
        outer = self._outer(extra=extra)
        # decoded stream includes both packages plus padding logical sizes
        result = self._run(outer, limits=self._limits(max_outer_decoded_bytes=50))
        self.assertFalse(result.ok)
        self.assertIn("outer_decoded", " ".join(result.document.get("errors", [])))

    def test_member_budget_does_not_reset_for_inner(self):
        outer = self._outer()
        # outer has 2 targets; inners have additional members. Cap of 2 should
        # stop before completing inner inventories.
        result = self._run(outer, limits=self._limits(max_members=2))
        self.assertFalse(result.ok)
        self.assertEqual(result.status, "partial")
        self.assertLessEqual(result.document.get("totals", {}).get("member_count", 99), 2)

    def test_wrong_outer_hash_never_reads_members(self):
        outer = self._outer()
        spec = self._spec(outer_bytes=outer.stat().st_size, outer_sha256="ab" * 32)
        result = self._run(outer, spec=spec)
        self.assertFalse(result.ok)
        self.assertFalse((self.out / "staged").exists() or any((self.out / "staged").glob("*") if (self.out / "staged").exists() else []))
        self.assertIn("outer", " ".join(result.document.get("errors", [])).lower())

    def test_global_deadline_does_not_reset(self):
        outer = self._outer()
        ticks = {"n": 0}

        def clock():
            ticks["n"] += 1
            # After initial setup/hash, jump past a 120s-equivalent short wall.
            return 0.0 if ticks["n"] < 3 else 10_000.0

        result = self._run(outer, limits=self._limits(wall_seconds=1), clock=clock)
        self.assertFalse(result.ok)
        self.assertIn(result.status, {"partial", "failed"})
        errors = " ".join(result.document.get("errors", [])).lower()
        self.assertTrue("wall" in errors or "deadline" in errors or "timeout" in errors)

    def test_disk_reserve_failure(self):
        outer = self._outer()
        orig = tcp.bai.shutil.disk_usage if hasattr(tcp, "bai") else None

        class Usage:
            free = 100

        # Patch whichever disk helper the module exposes.
        import targeted_core_two_phase as mod

        if hasattr(mod, "shutil"):
            saved = mod.shutil.disk_usage
            mod.shutil.disk_usage = lambda path: Usage()
            try:
                result = self._run(outer, limits=self._limits(min_free_disk_bytes=10_000))
            finally:
                mod.shutil.disk_usage = saved
        else:
            result = self._run(outer, limits=self._limits(min_free_disk_bytes=10_000))
        self.assertFalse(result.ok)
        payload = json.loads((self.out / "phase.json").read_text(encoding="utf-8"))
        self.assertFalse(payload["ok"])
        self.assertIn("disk", " ".join(payload.get("errors", [])).lower())

    def test_tests_do_not_point_at_catalog_archives(self):
        for name in CATALOG_FILENAMES:
            self.assertFalse((self.fx / name).exists())



    def test_sparse_inner_logical_size_counts_toward_phase_expanded(self):
        kernel = _write_gnu_sparse_member_bytes()
        boot = self.boot_payload
        path = _outer_targz(
            self.fx / "outer.tar.gz",
            {tcp.KERNEL_MEMBER: kernel, tcp.BOOTCODE_MEMBER: boot},
        )
        data = path.read_bytes()
        spec = tcp.PhaseSpec.for_tests(
            outer_name="outer.tar.gz",
            outer_bytes=len(data),
            outer_sha256=_sha256(data),
            targets=(
                tcp.TargetSpec(tcp.KERNEL_MEMBER, len(kernel), _sha256(kernel)),
                tcp.TargetSpec(tcp.BOOTCODE_MEMBER, len(boot), _sha256(boot)),
            ),
        )
        result = tcp.run_core_two_phase(
            path, self.out, spec=spec, limits=self._limits(max_phase_expanded_bytes=500)
        )
        self.assertFalse(result.ok)
        joined = " ".join(result.document.get("errors", []))
        self.assertTrue("expanded" in joined or "max_phase_expanded" in joined)

class IsolationTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory(prefix="core2-iso-")
        self.root = Path(self.tmp.name)
        sys.path.insert(0, str(TOOL_DIR))
        import isolate_targeted_phase as iso

        self.iso = iso

    def tearDown(self):
        self.tmp.cleanup()

    def test_isolation_command_is_narrow(self):
        outer = self.root / "outer.tar.gz"
        outer.write_bytes(b"x")
        out = self.root / "out"
        out.mkdir()
        cmd = self.iso.build_isolation_command(
            outer,
            out,
            wall_seconds=120,
            address_space_bytes=1073741824,
        )
        text = " ".join(cmd)
        self.assertEqual(cmd[0], "timeout")
        self.assertIn("prlimit", cmd)
        self.assertIn("--as=1073741824", cmd)
        self.assertIn("--unshare-all", cmd)
        self.assertNotIn("--share-net", cmd)
        self.assertNotIn("/home/box", cmd)
        self.assertIn("targeted_core_two_phase.py", text)

    def test_isolation_integration(self):
        kernel = _inner_targz({"README": b"iso kernel\n"})
        boot = _inner_targz({"LICENSE": b"iso boot\n"})
        outer = _outer_targz(
            self.root / "outer.tar.gz",
            {tcp.KERNEL_MEMBER: kernel, tcp.BOOTCODE_MEMBER: boot},
        )
        out = self.root / "iso-out"
        out.mkdir()
        rc = self.iso.main(
            [
                "--outer",
                str(outer),
                "--output-dir",
                str(out),
                "--expected-outer-bytes",
                str(outer.stat().st_size),
                "--expected-outer-sha256",
                _sha256(outer.read_bytes()),
                "--test-target",
                f"{tcp.KERNEL_MEMBER}:{len(kernel)}:{_sha256(kernel)}",
                "--test-target",
                f"{tcp.BOOTCODE_MEMBER}:{len(boot)}:{_sha256(boot)}",
                "--allow-test-spec",
            ]
        )
        self.assertEqual(rc, 0)
        payload = json.loads((out / "phase.json").read_text(encoding="utf-8"))
        self.assertTrue(payload["ok"])
        self.assertFalse(payload["controls"]["noexec_output_demonstrated"])
        launcher = json.loads((out / "launcher-result.json").read_text(encoding="utf-8"))
        self.assertFalse(launcher.get("noexec_output_demonstrated", True))
        if payload.get("isolation_observation"):
            self.assertFalse(payload["isolation_observation"].get("home_box_visible", True))


if __name__ == "__main__":
    unittest.main()

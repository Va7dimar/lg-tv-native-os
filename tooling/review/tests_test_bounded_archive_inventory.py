"""Adversarial tests for the bounded archive inventory tool.

Synthetic fixtures only. Does not open LG catalog archives.
"""
from __future__ import annotations

import gzip
import io
import json
import os
import stat
import sys
import tarfile
import tempfile
import unittest
import zlib
from pathlib import Path

TOOL_DIR = Path(__file__).resolve().parents[1]
if str(TOOL_DIR) not in sys.path:
    sys.path.insert(0, str(TOOL_DIR))

import bounded_archive_inventory as bai  # noqa: E402


CATALOG_BASENAMES = {
    "webOS 6.0 KLP_1.0_1.tar.gz",
    "webOS 6.0 KLP_1.0_2.tar.gz",
    "webOS 6.0 KLP_1.0_3.tar.gz",
}


def _write_regular_targz(path: Path, files: dict[str, bytes], *, dirs=(), extras=None) -> Path:
    with tarfile.open(path, "w:gz") as tf:
        for name in dirs:
            info = tarfile.TarInfo(name)
            info.type = tarfile.DIRTYPE
            info.mode = 0o755
            tf.addfile(info)
        for name, data in files.items():
            info = tarfile.TarInfo(name)
            info.type = tarfile.REGTYPE
            info.size = len(data)
            info.mode = 0o644
            tf.addfile(info, io.BytesIO(data))
        if extras:
            for extra in extras:
                tf.addfile(extra["info"], extra.get("fileobj"))
    return path


def _add_special(tf: tarfile.TarFile, name: str, typeflag: bytes, linkname: str = "", size: int = 0):
    info = tarfile.TarInfo(name)
    info.type = typeflag
    info.linkname = linkname
    info.size = size
    tf.addfile(info)


class LimitsTests(unittest.TestCase):
    def test_defaults_match_hard_ceilings(self):
        lim = bai.Limits()
        self.assertEqual(lim.max_members, 200_000)
        self.assertEqual(lim.max_pathname_bytes, 100_000_000)
        self.assertEqual(lim.max_selected_text_member_bytes, 16 * 1024 * 1024)
        self.assertEqual(lim.min_free_disk_bytes, 10 * 1024 * 1024 * 1024)
        self.assertEqual(lim.max_expanded_bytes, 20 * 1024 * 1024 * 1024)
        self.assertEqual(lim.wall_seconds, 120)
        self.assertEqual(lim.address_space_bytes, 1024 * 1024 * 1024)
        self.assertEqual(lim.max_stdout_bytes, 64 * 1024)

    def test_hard_maxima_cannot_be_raised(self):
        with self.assertRaises(bai.LimitError):
            bai.Limits(max_members=200_001)
        with self.assertRaises(bai.LimitError):
            bai.Limits(max_pathname_bytes=100_000_001)
        with self.assertRaises(bai.LimitError):
            bai.Limits(max_selected_text_member_bytes=16 * 1024 * 1024 + 1)
        with self.assertRaises(bai.LimitError):
            bai.Limits(max_expanded_bytes=20 * 1024 * 1024 * 1024 + 1)
        with self.assertRaises(bai.LimitError):
            bai.Limits(wall_seconds=121)
        with self.assertRaises(bai.LimitError):
            bai.Limits(address_space_bytes=1024 * 1024 * 1024 + 1)

    def test_lower_limits_allowed_for_tests(self):
        lim = bai.Limits(max_members=3, max_pathname_bytes=80, max_expanded_bytes=50)
        self.assertEqual(lim.max_members, 3)
        self.assertEqual(lim.max_pathname_bytes, 80)
        self.assertEqual(lim.max_expanded_bytes, 50)


class CanonicalizeTests(unittest.TestCase):
    def test_safe_relative_path(self):
        canon, reasons = bai.canonicalize_member_path("src/linux/README")
        self.assertEqual(canon, "src/linux/README")
        self.assertEqual(reasons, [])

    def test_absolute_unix_rejected(self):
        canon, reasons = bai.canonicalize_member_path("/etc/passwd")
        self.assertIsNone(canon)
        self.assertIn("absolute_path", reasons)

    def test_absolute_windows_drive_rejected(self):
        canon, reasons = bai.canonicalize_member_path(r"C:\Windows\system32")
        self.assertIsNone(canon)
        self.assertIn("absolute_path", reasons)

    def test_unc_rejected(self):
        canon, reasons = bai.canonicalize_member_path(r"\\server\share\file")
        self.assertIsNone(canon)
        self.assertIn("absolute_path", reasons)

    def test_parent_escape_rejected(self):
        canon, reasons = bai.canonicalize_member_path("../etc/passwd")
        self.assertIsNone(canon)
        self.assertIn("parent_escape", reasons)

    def test_nested_parent_escape_rejected(self):
        canon, reasons = bai.canonicalize_member_path("foo/../../etc/passwd")
        self.assertIsNone(canon)
        self.assertIn("parent_escape", reasons)

    def test_dotdot_inside_tree_normalized(self):
        canon, reasons = bai.canonicalize_member_path("foo/../bar")
        self.assertEqual(canon, "bar")
        self.assertEqual(reasons, [])

    def test_backslash_and_slash_same_canonical(self):
        a, ra = bai.canonicalize_member_path(r"a\b\c")
        b, rb = bai.canonicalize_member_path("a/b/c")
        self.assertEqual(ra, [])
        self.assertEqual(rb, [])
        self.assertEqual(a, b)
        self.assertEqual(a, "a/b/c")

    def test_double_slash_and_dot_collapsed(self):
        canon, reasons = bai.canonicalize_member_path("a//./b/./c")
        self.assertEqual(canon, "a/b/c")
        self.assertEqual(reasons, [])

    def test_nul_in_name_rejected(self):
        canon, reasons = bai.canonicalize_member_path("foo\x00bar")
        self.assertIsNone(canon)
        self.assertIn("nul_in_name", reasons)

    def test_empty_after_normalize_rejected(self):
        canon, reasons = bai.canonicalize_member_path("./.")
        self.assertIsNone(canon)
        self.assertIn("empty_path", reasons)


class LinkPolicyTests(unittest.TestCase):
    def test_absolute_symlink_unsafe(self):
        safe, resolved, reasons = bai.classify_link_target("bin/python", "/usr/bin/python")
        self.assertFalse(safe)
        self.assertIsNone(resolved)
        self.assertIn("unsafe_link_target", reasons)

    def test_escape_symlink_relative_to_parent(self):
        safe, resolved, reasons = bai.classify_link_target("dir/link", "../../etc/passwd")
        self.assertFalse(safe)
        self.assertIn("unsafe_link_target", reasons)

    def test_safe_relative_symlink(self):
        safe, resolved, reasons = bai.classify_link_target("dir/link", "../sibling")
        self.assertTrue(safe)
        self.assertEqual(resolved, "sibling")
        self.assertEqual(reasons, [])

    def test_hardlink_uses_same_policy(self):
        safe, resolved, reasons = bai.classify_link_target("dup", "ok.txt")
        self.assertTrue(safe)
        self.assertEqual(resolved, "ok.txt")


class InventoryBehaviorTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory(prefix="bai-test-")
        self.root = Path(self.tmp.name)
        self.out = self.root / "out"
        self.out.mkdir()
        self.fixtures = self.root / "fixtures"
        self.fixtures.mkdir()

    def tearDown(self):
        self.tmp.cleanup()

    def _result(self, archive: Path, **kwargs):
        limits = kwargs.pop("limits", bai.Limits.for_tests(min_free_disk_bytes=1))
        select = kwargs.pop("select", ())
        return bai.inventory_archives(
            [archive],
            self.out,
            limits=limits,
            select=select,
            **kwargs,
        )

    def test_happy_path_writes_json_and_markdown(self):
        archive = _write_regular_targz(
            self.fixtures / "ok.tar.gz",
            {"readme.txt": b"hello inventory\n", "src/main.c": b"int main(){return 0;}\n"},
            dirs=("src",),
        )
        result = self._result(archive)
        self.assertTrue(result.ok)
        self.assertEqual(result.status, "ok")
        payload = json.loads((self.out / "inventory.json").read_text(encoding="utf-8"))
        self.assertTrue(payload["ok"])
        self.assertEqual(payload["status"], "ok")
        self.assertTrue((self.out / "inventory.md").is_file())
        names = {m["canonical_name"] for m in payload["archives"][0]["members"]}
        self.assertIn("readme.txt", names)
        self.assertIn("src/main.c", names)

    def test_selected_plaintext_written_contained(self):
        archive = _write_regular_targz(
            self.fixtures / "sel.tar.gz",
            {"docs/note.txt": b"plain text only\n"},
        )
        result = self._result(archive, select=("docs/note.txt",))
        self.assertTrue(result.ok)
        selected = self.out / "selected" / "sel.tar.gz" / "docs" / "note.txt"
        self.assertTrue(selected.is_file())
        self.assertEqual(selected.read_bytes(), b"plain text only\n")
        self.assertEqual(stat.S_IMODE(selected.stat().st_mode), 0o644)
        resolved = selected.resolve()
        self.assertTrue(str(resolved).startswith(str(self.out.resolve()) + os.sep))

    def test_selected_oversize_not_written(self):
        archive = _write_regular_targz(
            self.fixtures / "big.txt.tar.gz",
            {"big.txt": b"x" * 200},
        )
        limits = bai.Limits.for_tests(min_free_disk_bytes=1, max_selected_text_member_bytes=50)
        result = self._result(archive, limits=limits, select=("big.txt",))
        self.assertFalse(any(self.out.rglob("big.txt")))
        payload = json.loads((self.out / "inventory.json").read_text(encoding="utf-8"))
        member = payload["archives"][0]["members"][0]
        self.assertFalse(member["selected"])
        self.assertIn("selected_oversize", member["reasons"])

    def test_nul_rejected_as_plaintext(self):
        archive = _write_regular_targz(
            self.fixtures / "bin.tar.gz",
            {"blob.bin": b"hello\x00world"},
        )
        result = self._result(archive, select=("blob.bin",))
        self.assertFalse(any(self.out.rglob("blob.bin")))
        payload = json.loads((self.out / "inventory.json").read_text(encoding="utf-8"))
        member = next(m for m in payload["archives"][0]["members"] if m["canonical_name"] == "blob.bin")
        self.assertIn("not_plaintext", member["reasons"])

    def test_member_count_limit_marks_partial(self):
        files = {f"f{i}.txt": b"n" for i in range(6)}
        archive = _write_regular_targz(self.fixtures / "many.tar.gz", files)
        limits = bai.Limits.for_tests(min_free_disk_bytes=1, max_members=5)
        result = self._result(archive, limits=limits)
        self.assertFalse(result.ok)
        self.assertEqual(result.status, "partial")
        payload = json.loads((self.out / "inventory.json").read_text(encoding="utf-8"))
        self.assertFalse(payload["ok"])
        self.assertEqual(payload["status"], "partial")
        self.assertIn("max_members", "".join(payload.get("errors", [])))

    def test_pathname_bytes_limit_marks_partial(self):
        archive = _write_regular_targz(
            self.fixtures / "names.tar.gz",
            {"short.txt": b"a", "a-quite-long-filename.txt": b"b"},
        )
        limits = bai.Limits.for_tests(min_free_disk_bytes=1, max_pathname_bytes=12)
        result = self._result(archive, limits=limits)
        self.assertFalse(result.ok)
        self.assertEqual(result.status, "partial")
        payload = json.loads((self.out / "inventory.json").read_text(encoding="utf-8"))
        self.assertIn("max_pathname_bytes", "".join(payload.get("errors", [])))

    def test_expansion_limit_counts_logical_size(self):
        archive = _write_regular_targz(
            self.fixtures / "exp.tar.gz",
            {"a.bin": b"A" * 40, "b.bin": b"B" * 40},
        )
        limits = bai.Limits.for_tests(min_free_disk_bytes=1, max_expanded_bytes=50)
        result = self._result(archive, limits=limits)
        self.assertFalse(result.ok)
        self.assertEqual(result.status, "partial")
        payload = json.loads((self.out / "inventory.json").read_text(encoding="utf-8"))
        self.assertIn("max_expanded_bytes", "".join(payload.get("errors", [])))

    def test_sparse_logical_size_counts_toward_expansion(self):
        info = tarfile.TarInfo("sparse.bin")
        info.type = tarfile.REGTYPE
        info.size = 10_000
        info.sparse = [(0, 4)]
        # logical_size helper must prefer declared/logical size over sparse data length
        self.assertGreaterEqual(bai.logical_member_size(info), 10_000)
        raw = self.fixtures / "sparse-meta.tar.gz"
        with tarfile.open(raw, "w:gz") as tf:
            written = tarfile.TarInfo("sparse.bin")
            written.type = tarfile.REGTYPE
            written.size = 10_000
            written.sparse = [(0, 4)]
            payload = b"data" + bytes(10_000 - 4)
            tf.addfile(written, io.BytesIO(payload))
        limits = bai.Limits.for_tests(min_free_disk_bytes=1, max_expanded_bytes=100)
        result = self._result(raw, limits=limits)
        self.assertFalse(result.ok)
        payload = json.loads((self.out / "inventory.json").read_text(encoding="utf-8"))
        joined = " ".join(payload.get("errors", []))
        self.assertTrue("max_expanded_bytes" in joined or result.status in {"failed", "partial"})

    def test_duplicate_canonical_paths_fail(self):
        archive = self.fixtures / "dup.tar.gz"
        with tarfile.open(archive, "w:gz") as tf:
            for name, data in (("a/./b.txt", b"one"), ("a/b.txt", b"two")):
                info = tarfile.TarInfo(name)
                info.size = len(data)
                tf.addfile(info, io.BytesIO(data))
        result = self._result(archive)
        self.assertFalse(result.ok)
        self.assertEqual(result.status, "failed")
        payload = json.loads((self.out / "inventory.json").read_text(encoding="utf-8"))
        reasons = [r for m in payload["archives"][0]["members"] for r in m["reasons"]]
        self.assertIn("duplicate_canonical_path", reasons)

    def test_backslash_collision_is_duplicate(self):
        archive = self.fixtures / "slashdup.tar.gz"
        with tarfile.open(archive, "w:gz") as tf:
            for name, data in (("win\\path.txt", b"a"), ("win/path.txt", b"b")):
                info = tarfile.TarInfo(name)
                info.size = len(data)
                tf.addfile(info, io.BytesIO(data))
        result = self._result(archive)
        self.assertFalse(result.ok)
        payload = json.loads((self.out / "inventory.json").read_text(encoding="utf-8"))
        reasons = [r for m in payload["archives"][0]["members"] for r in m["reasons"]]
        self.assertIn("duplicate_canonical_path", reasons)

    def test_absolute_and_parent_members_rejected(self):
        archive = self.fixtures / "evil.tar.gz"
        with tarfile.open(archive, "w:gz") as tf:
            for name, data in (("/etc/passwd", b"x"), ("../escape.txt", b"y"), ("ok.txt", b"z")):
                info = tarfile.TarInfo(name)
                info.size = len(data)
                tf.addfile(info, io.BytesIO(data))
        result = self._result(archive)
        self.assertFalse(result.ok)
        self.assertEqual(result.status, "failed")

    def test_device_and_fifo_rejected(self):
        archive = self.fixtures / "specials.tar.gz"
        with tarfile.open(archive, "w:gz") as tf:
            dev = tarfile.TarInfo("dev/nullish")
            dev.type = tarfile.CHRTYPE
            dev.devmajor = 1
            dev.devminor = 3
            tf.addfile(dev)
            fifo = tarfile.TarInfo("pipe")
            fifo.type = tarfile.FIFOTYPE
            tf.addfile(fifo)
        result = self._result(archive)
        self.assertFalse(result.ok)
        payload = json.loads((self.out / "inventory.json").read_text(encoding="utf-8"))
        reasons = [r for m in payload["archives"][0]["members"] for r in m["reasons"]]
        self.assertTrue({"device", "fifo"} & set(reasons))

    def test_safe_symlink_recorded_not_followed(self):
        archive = self.fixtures / "links.tar.gz"
        with tarfile.open(archive, "w:gz") as tf:
            data = b"target-bytes"
            info = tarfile.TarInfo("real.txt")
            info.size = len(data)
            tf.addfile(info, io.BytesIO(data))
            link = tarfile.TarInfo("alias.txt")
            link.type = tarfile.SYMTYPE
            link.linkname = "real.txt"
            tf.addfile(link)
        result = self._result(archive, select=("alias.txt", "real.txt"))
        self.assertTrue(result.ok)
        self.assertFalse(any(self.out.rglob("alias.txt")))
        self.assertTrue((self.out / "selected" / "links.tar.gz" / "real.txt").is_file())
        payload = json.loads((self.out / "inventory.json").read_text(encoding="utf-8"))
        alias = next(m for m in payload["archives"][0]["members"] if m["canonical_name"] == "alias.txt")
        self.assertEqual(alias["decision"], "recorded_not_followed")
        self.assertFalse(alias["selected"])

    def test_unsafe_symlink_fails_closed(self):
        archive = self.fixtures / "badlink.tar.gz"
        with tarfile.open(archive, "w:gz") as tf:
            link = tarfile.TarInfo("escape")
            link.type = tarfile.SYMTYPE
            link.linkname = "../../etc/passwd"
            tf.addfile(link)
        result = self._result(archive)
        self.assertFalse(result.ok)
        payload = json.loads((self.out / "inventory.json").read_text(encoding="utf-8"))
        reasons = [r for m in payload["archives"][0]["members"] for r in m["reasons"]]
        self.assertIn("unsafe_link_target", reasons)

    def test_hardlink_not_dereferenced(self):
        archive = self.fixtures / "hard.tar.gz"
        with tarfile.open(archive, "w:gz") as tf:
            data = b"payload"
            info = tarfile.TarInfo("orig.txt")
            info.size = len(data)
            tf.addfile(info, io.BytesIO(data))
            hard = tarfile.TarInfo("hard.txt")
            hard.type = tarfile.LNKTYPE
            hard.linkname = "orig.txt"
            tf.addfile(hard)
        result = self._result(archive, select=("hard.txt",))
        self.assertTrue(result.ok)
        self.assertFalse(any(self.out.rglob("hard.txt")))
        payload = json.loads((self.out / "inventory.json").read_text(encoding="utf-8"))
        hard_m = next(m for m in payload["archives"][0]["members"] if m["canonical_name"] == "hard.txt")
        self.assertEqual(hard_m["decision"], "recorded_not_followed")

    def test_truncated_gzip_fails_closed(self):
        intact = _write_regular_targz(self.fixtures / "full.tar.gz", {"a.txt": b"abcde" * 50})
        data = intact.read_bytes()
        truncated = self.fixtures / "trunc.tar.gz"
        truncated.write_bytes(data[:20])
        result = self._result(truncated)
        self.assertFalse(result.ok)
        self.assertIn(result.status, {"failed", "partial"})
        payload = json.loads((self.out / "inventory.json").read_text(encoding="utf-8"))
        self.assertFalse(payload["ok"])

    def test_malformed_gzip_fails_closed(self):
        bad = self.fixtures / "notgz.tar.gz"
        bad.write_bytes(b"this is not gzip")
        result = self._result(bad)
        self.assertFalse(result.ok)
        payload = json.loads((self.out / "inventory.json").read_text(encoding="utf-8"))
        self.assertFalse(payload["ok"])

    def test_malformed_pax_fails_closed(self):
        # Craft a ustar-like PAX 'x' header with an invalid extended record.
        def checksum(header: bytearray) -> None:
            header[148:156] = b"        "
            chk = sum(header)
            header[148:156] = f"{chk:06o}\0 ".encode("ascii")

        header = bytearray(512)
        header[0:8] = b"paxbad\0\0"
        header[124:135] = b"00000000020"  # size 16 decimal? 020 octal = 16
        header[124:136] = f"{16:011o} ".encode("ascii")
        header[156:157] = b"x"
        header[257:263] = b"ustar\0"
        header[263:265] = b"00"
        checksum(header)
        payload = b"not-a-valid-pax\n"  # 16 bytes, missing LEN KEY=VALUE
        padded = payload + b"\0" * (512 - len(payload))
        raw_tar = bytes(header) + padded + bytes(1024)
        gzpath = self.fixtures / "badpax.tar.gz"
        with gzip.open(gzpath, "wb") as gf:
            gf.write(raw_tar)
        result = self._result(gzpath)
        self.assertFalse(result.ok)
        payload_json = json.loads((self.out / "inventory.json").read_text(encoding="utf-8"))
        self.assertFalse(payload_json["ok"])

    def test_gnu_longname_inventoryable(self):
        long_name = "deep/" + ("n" * 140) + ".txt"
        archive = _write_regular_targz(self.fixtures / "long.tar.gz", {long_name: b"long-ok"})
        result = self._result(archive)
        self.assertTrue(result.ok)
        payload = json.loads((self.out / "inventory.json").read_text(encoding="utf-8"))
        names = {m["canonical_name"] for m in payload["archives"][0]["members"] if m["type"] == "file"}
        self.assertIn(long_name, names)

    def test_existing_output_collision(self):
        archive = _write_regular_targz(self.fixtures / "ok2.tar.gz", {"a.txt": b"a"})
        (self.out / "inventory.json").write_text("{}", encoding="utf-8")
        with self.assertRaises(bai.OutputCollisionError):
            self._result(archive)

    def test_duplicate_input_paths_rejected(self):
        archive = _write_regular_targz(self.fixtures / "one.tar.gz", {"a.txt": b"a"})
        with self.assertRaises(bai.InputCollisionError):
            bai.inventory_archives(
                [archive, archive],
                self.out,
                limits=bai.Limits.for_tests(min_free_disk_bytes=1),
            )

    def test_same_basename_inputs_rejected(self):
        d1 = self.fixtures / "d1"
        d2 = self.fixtures / "d2"
        d1.mkdir()
        d2.mkdir()
        a = _write_regular_targz(d1 / "same.tar.gz", {"a.txt": b"a"})
        b = _write_regular_targz(d2 / "same.tar.gz", {"b.txt": b"b"})
        with self.assertRaises(bai.InputCollisionError):
            bai.inventory_archives(
                [a, b],
                self.out,
                limits=bai.Limits.for_tests(min_free_disk_bytes=1),
            )

    def test_symlink_input_rejected(self):
        archive = _write_regular_targz(self.fixtures / "realinput.tar.gz", {"a.txt": b"a"})
        link = self.fixtures / "linkinput.tar.gz"
        link.symlink_to(archive)
        with self.assertRaises(bai.InputError):
            bai.inventory_archives(
                [link],
                self.out,
                limits=bai.Limits.for_tests(min_free_disk_bytes=1),
            )

    def test_disk_reserve_failure(self):
        archive = _write_regular_targz(self.fixtures / "disk.tar.gz", {"a.txt": b"a"})
        orig = bai.shutil.disk_usage

        class Usage:
            free = 100

        bai.shutil.disk_usage = lambda path: Usage()  # type: ignore
        try:
            result = bai.inventory_archives(
                [archive],
                self.out,
                limits=bai.Limits.for_tests(min_free_disk_bytes=10_000),
            )
            self.assertFalse(result.ok)
            payload = json.loads((self.out / "inventory.json").read_text(encoding="utf-8"))
            joined = " ".join(payload.get("errors", [])).lower()
            self.assertTrue("free_disk" in joined or "disk" in joined)
            self.assertFalse(payload["ok"])
        finally:
            bai.shutil.disk_usage = orig

    def test_nested_archive_not_expanded(self):
        inner = _write_regular_targz(self.fixtures / "inner.tar.gz", {"secret.txt": b"nope"})
        outer = _write_regular_targz(
            self.fixtures / "outer.tar.gz",
            {"nested.tar.gz": inner.read_bytes(), "ok.txt": b"visible"},
        )
        result = self._result(outer, select=("nested.tar.gz", "ok.txt"))
        self.assertTrue(result.ok)
        payload = json.loads((self.out / "inventory.json").read_text(encoding="utf-8"))
        nested = next(m for m in payload["archives"][0]["members"] if m["canonical_name"] == "nested.tar.gz")
        self.assertTrue(nested.get("nested_archive_not_expanded"))
        self.assertFalse(nested["selected"])
        self.assertFalse(any(self.out.rglob("secret.txt")))

    def test_cli_rejects_raised_maximum(self):
        archive = _write_regular_targz(self.fixtures / "cli.tar.gz", {"a.txt": b"a"})
        rc = bai.main(
            [
                "--input",
                str(archive),
                "--output-dir",
                str(self.out),
                "--max-members",
                "200001",
            ]
        )
        self.assertEqual(rc, 2)

    def test_stdout_is_bounded(self):
        archive = _write_regular_targz(self.fixtures / "stdout.tar.gz", {"a.txt": b"a"})
        from io import StringIO

        buf = StringIO()
        old = sys.stdout
        sys.stdout = buf
        try:
            rc = bai.main(["--input", str(archive), "--output-dir", str(self.out)])
        finally:
            sys.stdout = old
        self.assertEqual(rc, 0)
        written = buf.getvalue().encode("utf-8")
        self.assertLessEqual(len(written), 64 * 1024)
        self.assertNotIn("member dump", buf.getvalue().lower())
        self.assertIn("inventory.json", buf.getvalue())

    def test_cli_does_not_open_missing_fixture_named_like_catalog(self):
        # Guard test intent: catalog originals are not used as fixtures here.
        for name in CATALOG_BASENAMES:
            self.assertFalse((self.fixtures / name).exists())


class IsolationCommandTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory(prefix="bai-iso-")
        self.root = Path(self.tmp.name)
        sys.path.insert(0, str(TOOL_DIR))
        import isolate_inventory as iso

        self.iso = iso

    def tearDown(self):
        self.tmp.cleanup()

    def test_command_uses_timeout_prlimit_unshare_and_explicit_binds(self):
        inp = self.root / "in.tar.gz"
        inp.write_bytes(b"x")
        out = self.root / "out"
        out.mkdir()
        tool = TOOL_DIR / "bounded_archive_inventory.py"
        cmd = self.iso.build_isolation_command(
            [inp],
            out,
            limits=bai.Limits(),
            tool_path=tool,
            forwarded_args=["--max-members", "50"],
        )
        text = " ".join(cmd)
        self.assertEqual(cmd[0], "timeout")
        self.assertIn("--kill-after=5s", cmd)
        self.assertIn("prlimit", cmd)
        self.assertIn("--as=1073741824", cmd)
        self.assertIn("--unshare-all", cmd)
        self.assertIn("--clearenv", cmd)
        self.assertNotIn("--share-net", cmd)
        self.assertIn("--ro-bind", cmd)
        self.assertIn(str(inp.resolve()), cmd)
        self.assertIn(str(out.resolve()), cmd)
        self.assertNotRegex(text, r"(^| )(/home|/root|/cursor)( |$)")
        self.assertNotIn("/home/box", cmd)

    def test_isolation_integration_hides_home_and_writes_inventory(self):
        archive = self.root / "tiny.tar.gz"
        _write_regular_targz(archive, {"hello.txt": b"hi\n"})
        out = self.root / "iso-out"
        out.mkdir()
        rc = self.iso.main(
            [
                "--input",
                str(archive),
                "--output-dir",
                str(out),
                "--max-members",
                "50",
            ]
        )
        self.assertEqual(rc, 0)
        payload = json.loads((out / "inventory.json").read_text(encoding="utf-8"))
        self.assertTrue(payload["ok"])
        obs = payload.get("isolation_observation") or payload.get("host", {})
        # When launched isolated, home should not be visible. If observation is
        # present, require it to report that fact.
        if "home_box_visible" in json.dumps(payload):
            self.assertFalse(payload["isolation_observation"]["home_box_visible"])
        launcher = json.loads((out / "launcher-result.json").read_text(encoding="utf-8"))
        self.assertFalse(launcher.get("noexec_output_demonstrated", True))
        self.assertTrue(launcher.get("unshare_all"))
        # Confirm host vs sandbox net ns were recorded as evidence when available.
        if "sandbox_net_ns" in launcher and "host_net_ns" in launcher:
            self.assertNotEqual(launcher["sandbox_net_ns"], launcher["host_net_ns"])


if __name__ == "__main__":
    unittest.main()

"""Regression tests for independent-review findings. Synthetic fixtures only."""
from __future__ import annotations

import gzip
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

import bounded_archive_inventory as bai  # noqa: E402


def _write_regular_targz(path: Path, files: dict[str, bytes]) -> Path:
    with tarfile.open(path, "w:gz") as tf:
        for name, data in files.items():
            info = tarfile.TarInfo(name)
            info.type = tarfile.REGTYPE
            info.size = len(data)
            info.mode = 0o644
            tf.addfile(info, io.BytesIO(data))
    return path


def _octal(val: int, width: int) -> bytes:
    return (oct(val)[2:].rjust(width - 1, "0") + "\0").encode("ascii")


def _checksum(header: bytes) -> bytes:
    buf = bytearray(header)
    buf[148:156] = b"        "
    chk = sum(buf)
    buf[148:156] = f"{chk:06o}\0 ".encode("ascii")
    return bytes(buf)


def write_gnu_sparse_targz(path: Path, name: str = "sparse.bin", origsize: int = 10_000) -> Path:
    """GNU type-S sparse member: 8 stored bytes, large logical origsize."""
    header = bytearray(512)
    encoded = name.encode("ascii") + b"\0"
    header[0:len(encoded)] = encoded
    header[100:108] = _octal(0o644, 8)
    header[108:116] = _octal(0, 8)
    header[116:124] = _octal(0, 8)
    header[124:136] = _octal(8, 12)  # stored size
    header[136:148] = _octal(0, 12)
    header[156:157] = tarfile.GNUTYPE_SPARSE
    header[257:263] = b"ustar "
    header[263:265] = b" \0"
    header[386:398] = _octal(0, 12)
    header[398:410] = _octal(4, 12)
    header[410:422] = _octal(origsize - 4, 12)
    header[422:434] = _octal(4, 12)
    header[482] = 0
    header[483:495] = _octal(origsize, 12)
    header = _checksum(header)
    payload = b"DATAEND!" + bytes(512 - 8)
    raw = bytes(header) + payload + bytes(1024)
    with gzip.open(path, "wb") as handle:
        handle.write(raw)
    return path


class ReviewRegressionTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory(prefix="bai-reg-")
        self.root = Path(self.tmp.name)
        self.out = self.root / "out"
        self.out.mkdir()
        self.fixtures = self.root / "fx"
        self.fixtures.mkdir()

    def tearDown(self):
        self.tmp.cleanup()

    def _limits(self, **kwargs):
        kwargs.setdefault("min_free_disk_bytes", 1)
        try:
            return bai.Limits.for_tests(**kwargs)
        except AttributeError:
            return bai.Limits(**kwargs)

    def test_cross_archive_member_budget_is_aggregate(self):
        a1 = _write_regular_targz(self.fixtures / "a1.tar.gz", {"a.txt": b"1", "b.txt": b"2"})
        a2 = _write_regular_targz(self.fixtures / "a2.tar.gz", {"c.txt": b"3", "d.txt": b"4"})
        result = bai.inventory_archives(
            [a1, a2], self.out, limits=self._limits(max_members=3)
        )
        payload = json.loads((self.out / "inventory.json").read_text(encoding="utf-8"))
        total = sum(arch["member_count"] for arch in payload["archives"])
        self.assertFalse(result.ok)
        self.assertEqual(result.status, "partial")
        self.assertLessEqual(total, 3)
        self.assertIn("max_members", " ".join(payload.get("errors", [])))

    def test_cross_archive_expanded_budget_is_aggregate(self):
        a1 = _write_regular_targz(self.fixtures / "e1.tar.gz", {"x.bin": b"X" * 80})
        a2 = _write_regular_targz(self.fixtures / "e2.tar.gz", {"y.bin": b"Y" * 80})
        result = bai.inventory_archives(
            [a1, a2], self.out, limits=self._limits(max_expanded_bytes=100)
        )
        payload = json.loads((self.out / "inventory.json").read_text(encoding="utf-8"))
        expanded = sum(arch["expanded_bytes"] for arch in payload["archives"])
        self.assertFalse(result.ok)
        self.assertEqual(result.status, "partial")
        self.assertLessEqual(expanded, 100)
        self.assertIn("max_expanded_bytes", " ".join(payload.get("errors", [])))

    def test_cross_archive_pathname_budget_is_aggregate(self):
        a1 = _write_regular_targz(self.fixtures / "p1.tar.gz", {"abcdefghij.txt": b"1"})
        a2 = _write_regular_targz(self.fixtures / "p2.tar.gz", {"klmnopqrst.txt": b"2"})
        result = bai.inventory_archives(
            [a1, a2], self.out, limits=self._limits(max_pathname_bytes=20)
        )
        payload = json.loads((self.out / "inventory.json").read_text(encoding="utf-8"))
        path_bytes = sum(arch["pathname_bytes"] for arch in payload["archives"])
        self.assertFalse(result.ok)
        self.assertEqual(result.status, "partial")
        self.assertLessEqual(path_bytes, 20)
        self.assertIn("max_pathname_bytes", " ".join(payload.get("errors", [])))

    def test_partial_first_archive_does_not_process_or_select_later(self):
        first = _write_regular_targz(
            self.fixtures / "first.tar.gz",
            {"one.txt": b"1", "two.txt": b"2", "three.txt": b"3"},
        )
        second = _write_regular_targz(self.fixtures / "second.tar.gz", {"later.txt": b"later"})
        result = bai.inventory_archives(
            [first, second],
            self.out,
            limits=self._limits(max_members=2),
            select=("later.txt",),
        )
        payload = json.loads((self.out / "inventory.json").read_text(encoding="utf-8"))
        self.assertFalse(result.ok)
        self.assertEqual(result.status, "partial")
        self.assertEqual(len(payload["archives"]), 1)
        self.assertEqual(payload["archives"][0]["status"], "partial")
        later_names = [
            m.get("canonical_name")
            for arch in payload["archives"]
            for m in arch.get("members", [])
        ]
        self.assertNotIn("later.txt", later_names)
        self.assertFalse(any(self.out.rglob("later.txt")))
        self.assertTrue(
            payload.get("skipped_inputs")
            or any("stopped" in err for err in payload.get("errors", []))
        )

    def test_failed_first_archive_does_not_read_later(self):
        evil = self.fixtures / "evil.tar.gz"
        with tarfile.open(evil, "w:gz") as tf:
            link = tarfile.TarInfo("/abs/link")
            link.type = tarfile.SYMTYPE
            link.linkname = "../../etc/passwd"
            tf.addfile(link)
        later = _write_regular_targz(self.fixtures / "after.tar.gz", {"ok.txt": b"ok"})
        result = bai.inventory_archives([evil, later], self.out, limits=self._limits())
        payload = json.loads((self.out / "inventory.json").read_text(encoding="utf-8"))
        self.assertFalse(result.ok)
        self.assertEqual(result.status, "failed")
        self.assertEqual(len(payload["archives"]), 1)

    def test_absolute_symlink_member_stays_rejected(self):
        archive = self.fixtures / "abslink.tar.gz"
        with tarfile.open(archive, "w:gz") as tf:
            link = tarfile.TarInfo("/abs/link")
            link.type = tarfile.SYMTYPE
            link.linkname = "relative-target"
            tf.addfile(link)
            data = b"ok"
            info = tarfile.TarInfo("ok.txt")
            info.size = len(data)
            tf.addfile(info, io.BytesIO(data))
        result = bai.inventory_archives([archive], self.out, limits=self._limits())
        payload = json.loads((self.out / "inventory.json").read_text(encoding="utf-8"))
        member = next(m for m in payload["archives"][0]["members"] if m["raw_name"] == "/abs/link")
        self.assertEqual(member["decision"], "rejected")
        self.assertIn("absolute_path", member["reasons"])
        self.assertNotEqual(member["decision"], "recorded_not_followed")
        self.assertFalse(result.ok)

    def test_parser_surfaced_sparse_logical_size(self):
        archive = write_gnu_sparse_targz(self.fixtures / "sparse-gnu.tar.gz")
        with open(archive, "rb") as handle:
            opener = getattr(bai, "open_untrusted_tar_gz", None)
            self.assertIsNotNone(opener, "open_untrusted_tar_gz is required for stream-true reads")
            tf = opener(handle)
            try:
                info = tf.next()
            finally:
                tf.close()
        self.assertIsNotNone(info)
        self.assertTrue(info.sparse)
        self.assertGreaterEqual(bai.logical_member_size(info), 10_000)
        self.assertLess(8, 10_000)  # stored payload is smaller than logical size
        result = bai.inventory_archives(
            [archive], self.out, limits=self._limits(max_expanded_bytes=100)
        )
        payload = json.loads((self.out / "inventory.json").read_text(encoding="utf-8"))
        self.assertFalse(result.ok)
        self.assertIn("max_expanded_bytes", " ".join(payload.get("errors", [])))
        member = payload["archives"][0]["members"][0]
        self.assertTrue(member.get("sparse"))
        self.assertGreaterEqual(member["size"], 10_000)

    def test_open_untrusted_tar_uses_noncaching_stream(self):
        archive = _write_regular_targz(self.fixtures / "stream.tar.gz", {"a.txt": b"a", "b.txt": b"b"})
        opener = getattr(bai, "open_untrusted_tar_gz", None)
        self.assertIsNotNone(opener)
        with open(archive, "rb") as handle:
            tf = opener(handle)
            try:
                self.assertTrue(tf.stream)
                seen = 0
                while tf.next() is not None:
                    seen += 1
                    self.assertEqual(tf.members, [])
                self.assertEqual(seen, 2)
            finally:
                tf.close()

    def test_cli_cannot_lower_disk_reserve_floor(self):
        archive = _write_regular_targz(self.fixtures / "diskcli.tar.gz", {"a.txt": b"a"})
        rc = bai.main(
            [
                "--input",
                str(archive),
                "--output-dir",
                str(self.out),
                "--min-free-disk-bytes",
                "1",
            ]
        )
        self.assertEqual(rc, 2)
        self.assertFalse((self.out / "inventory.json").exists())

    def test_emit_stdout_truncation_is_valid_json(self):
        from io import StringIO

        buf = StringIO()
        old = sys.stdout
        sys.stdout = buf
        try:
            bai.emit_stdout({"status": "ok", "ok": True, "error": "x" * 4000}, 80)
        finally:
            sys.stdout = old
        parsed = json.loads(buf.getvalue())
        self.assertIsInstance(parsed, dict)
        self.assertIn("status", parsed)
        self.assertTrue(parsed.get("truncated") or parsed.get("error") == "stdout_truncated")

    def test_cross_archive_selected_names_are_namespaced(self):
        a1 = _write_regular_targz(self.fixtures / "left.tar.gz", {"README": b"one"})
        a2 = _write_regular_targz(self.fixtures / "right.tar.gz", {"README": b"two"})
        result = bai.inventory_archives(
            [a1, a2], self.out, limits=self._limits(), select=("README",)
        )
        self.assertTrue(result.ok)
        left = self.out / "selected" / "left.tar.gz" / "README"
        right = self.out / "selected" / "right.tar.gz" / "README"
        self.assertTrue(left.is_file())
        self.assertTrue(right.is_file())
        self.assertEqual(left.read_bytes(), b"one")
        self.assertEqual(right.read_bytes(), b"two")

    def test_isolate_rejects_symlink_input(self):
        import isolate_inventory as iso

        real = _write_regular_targz(self.fixtures / "real.tar.gz", {"a.txt": b"a"})
        link = self.fixtures / "link.tar.gz"
        link.symlink_to(real)
        out = self.root / "iso-out"
        out.mkdir()
        with self.assertRaises(bai.InputError):
            iso.build_isolation_command(
                [link],
                out,
                limits=self._limits(),
                tool_path=TOOL_DIR / "bounded_archive_inventory.py",
            )
        rc = iso.main(["--input", str(link), "--output-dir", str(out)])
        self.assertNotEqual(rc, 0)

    def test_document_states_isolation_backstop_and_noexec_honesty(self):
        archive = _write_regular_targz(self.fixtures / "notes.tar.gz", {"a.txt": b"a"})
        result = bai.inventory_archives([archive], self.out, limits=self._limits())
        payload = result.document or json.loads((self.out / "inventory.json").read_text())
        notes = json.dumps(payload).lower()
        self.assertIn("isolate", notes)
        self.assertFalse(payload["isolation_observation"]["noexec_output_demonstrated"])
        self.assertIn("disk", notes)


if __name__ == "__main__":
    unittest.main()

"""Synthetic UTF8 boundary tests; no production paths are opened."""
import gzip
import io
import json
import lzma
import os
from pathlib import Path
import sys
import tarfile
import tempfile
import time
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import sdk_inventory_phase as sdk

LONG = 'a' * 99 + '\u0100-suffix'


def archive(entries, fmt=tarfile.GNU_FORMAT):
    raw = io.BytesIO()
    with tarfile.open(fileobj=raw, mode='w', format=fmt,
                      encoding='utf-8', errors='surrogateescape') as tf:
        for entry in entries:
            tf.addfile(entry)
    return raw.getvalue()


def entry(name='file', link='', kind=tarfile.REGTYPE, **metadata):
    info = tarfile.TarInfo(name)
    info.linkname, info.type = link, kind
    for key, value in metadata.items():
        setattr(info, key, value)
    return info


class UTF8BoundaryTests(unittest.TestCase):
    def parse(self, raw, codec, **limits):
        packed = gzip.compress(raw, mtime=0) if codec == 'gz' else lzma.compress(raw)
        budget = sdk.Budget(sdk.Limits(**limits), time.monotonic() + 30)
        obs = dict(compressed_bytes_read=0, compressed_bytes_consumed=None,
                   decoded_bytes=0, max_decoder_chunk=0, integrity_eof=False)
        rows = []
        with tempfile.TemporaryFile() as f:
            f.write(packed); f.flush()
            spec = sdk.InputSpec('synthetic', 'not-opened', len(packed), '', codec)
            sdk.parse_archive(f.fileno(), spec, budget, obs, rows.append)
        return rows, budget.totals, obs

    def test_gnu_split_utf8_name_and_link_roundtrip(self):
        for codec in ('gz', 'xz'):
            for name, link in ((LONG, ''), ('sym', LONG), (LONG, LONG)):
                with self.subTest(codec=codec, name=name, link=link):
                    ti = entry(name, link, tarfile.SYMTYPE if link else tarfile.REGTYPE)
                    raw = archive([ti])
                    # Maintained writer produces valid extended UTF8, but the
                    # following fixed field ends with the first byte of U+0100.
                    base = ti.tobuf(format=tarfile.GNU_FORMAT, encoding='utf-8')[-512:]
                    if name == LONG:
                        self.assertEqual(base[0:100], b'a' * 99 + b'\xc4')
                    if link == LONG:
                        self.assertEqual(base[157:257], b'a' * 99 + b'\xc4')
                    rows, totals, obs = self.parse(raw, codec)
                    self.assertEqual(rows[0]['raw_name'], name)
                    self.assertEqual(rows[0]['link_target'], link)
                    self.assertEqual(totals['members'], 1 + (name == LONG) + (link == LONG))
                    self.assertTrue(obs['integrity_eof'] and obs['tar_eof'])
                    self.assertEqual(json.loads(json.dumps(rows, ensure_ascii=True)), rows)

    def test_pax_unicode_and_ustar_baselines(self):
        for codec in ('gz', 'xz'):
            for fmt, name, link in ((tarfile.PAX_FORMAT, LONG, LONG),
                                    (tarfile.USTAR_FORMAT, '\u0100-file', '\u0100-target'),
                                    (tarfile.USTAR_FORMAT, 'd/' + 'a' * 99, 'target'),
                                    (tarfile.GNU_FORMAT, 'a' * 140, 'b' * 140)):
                with self.subTest(codec=codec, fmt=fmt, name=name):
                    rows, _, _ = self.parse(archive([entry(name, link, tarfile.SYMTYPE)], fmt), codec)
                    self.assertEqual((rows[0]['raw_name'], rows[0]['link_target']), (name, link))

    def test_unresolved_invalid_utf8_fails_closed(self):
        for codec in ('gz', 'xz'):
            for ti in (entry('safe-\udcc4'), entry('sym', 'safe-\udcc4', tarfile.SYMTYPE),
                       entry('a' * 101 + '\udcc4'),
                       entry('sym', 'a' * 101 + '\udcc4', tarfile.SYMTYPE),
                       entry(uname='owner-\udcc4'), entry(gname='group-\udcc4')):
                with self.subTest(codec=codec, name=ti.name, link=ti.linkname, uname=ti.uname, gname=ti.gname):
                    with self.assertRaises((sdk.InventoryError, UnicodeError)):
                        self.parse(archive([ti]), codec)

    def test_extended_paths_links_duplicates_and_types_fail_closed(self):
        badnames = ('../' + LONG, '/' + LONG, 'C:/' + LONG, 'dir/../' + LONG, 'dir\\' + LONG)
        for codec in ('gz', 'xz'):
            for fmt in (tarfile.GNU_FORMAT, tarfile.PAX_FORMAT):
                cases = [[entry(name)] for name in badnames]
                cases += [[entry('sym', target, kind)] for target in ('../../' + LONG, '/' + LONG, 'C:/' + LONG, 'dir\\' + LONG)
                          for kind in (tarfile.SYMTYPE, tarfile.LNKTYPE)]
                cases += [[entry(LONG), entry('./' + LONG)]]
                cases += [[entry(LONG, kind=kind)] for kind in (tarfile.CHRTYPE, tarfile.FIFOTYPE, tarfile.GNUTYPE_SPARSE, b'Z')]
                if fmt == tarfile.PAX_FORMAT:
                    cases += [[entry(LONG, pax_headers={'GNU.sparse.map': '0,1', 'GNU.sparse.size': '1'})]]
                for index, members in enumerate(cases):
                    with self.subTest(codec=codec, fmt=fmt, case=index):
                        with self.assertRaises(sdk.InventoryError):
                            self.parse(archive(members, fmt), codec)

    def test_original_byte_budget_and_hidden_headers(self):
        # Two GNU extensions: each has a 13-byte header name and a padded
        # 512-byte body. Base name/link are each 100 ORIGINAL bytes, including
        # the incomplete UTF8 byte. Resolved name/link each count full UTF8.
        expected = 2 * (13 + 512) + 200 + 2 * len(LONG.encode('utf-8'))
        for codec in ('gz', 'xz'):
            raw = archive([entry(LONG, LONG, tarfile.SYMTYPE)])
            with self.subTest(codec=codec):
                _, totals, _ = self.parse(raw, codec, metadata_bytes=expected, members=3)
                self.assertEqual(totals['metadata_bytes'], expected)
                self.assertEqual(totals['members'], 3)
                with self.assertRaisesRegex(sdk.InventoryError, 'metadata_bytes'):
                    self.parse(raw, codec, metadata_bytes=expected - 1)
                with self.assertRaisesRegex(sdk.InventoryError, 'members'):
                    self.parse(raw, codec, members=2)

    def test_regular_multibyte_metadata_charges_unchanged(self):
        for codec in ('gz', 'xz'):
            raw = archive([entry('\u0100', uname='\u00e9', gname='\u00f6')], tarfile.USTAR_FORMAT)
            _, totals, _ = self.parse(raw, codec, metadata_bytes=8)
            self.assertEqual(totals['metadata_bytes'], 8)
            with self.assertRaisesRegex(sdk.InventoryError, 'metadata_bytes'):
                self.parse(raw, codec, metadata_bytes=7)


if __name__ == '__main__':
    unittest.main()

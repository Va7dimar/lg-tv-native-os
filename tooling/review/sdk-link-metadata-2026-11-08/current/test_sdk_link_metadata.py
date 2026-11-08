"""Synthetic metadata policy tests; no production inputs or link targets opened."""
import builtins
import json
import os
from pathlib import Path
import tarfile
from unittest import mock

from test_sdk_inventory_phase import InventoryTests, tar_bytes


def link(name, target, kind=tarfile.SYMTYPE):
    ti = tarfile.TarInfo(name)
    ti.type, ti.linkname = kind, target
    return ti


class LinkMetadataTests(InventoryTests):
    # Reuse fixture helpers, not inherited tests.
    def test_absolute_and_escaping_symlinks_are_nonextractable_metadata(self):
        import sdk_inventory_phase as sdk
        sentinel = self.root / 'sentinel'
        sentinel.write_text('SYNTHETIC NEVER READ')
        entries = [link('dir/abs', str(sentinel)), link('dir/escape', '../../sentinel'),
                   link('dir/safe', '../file')]
        specs = self.specs(tar_bytes(entries))
        original_open, original_pread = os.open, os.pread
        def guarded_open(path, *args, **kwargs):
            if os.fspath(path) == str(sentinel):
                raise AssertionError('target opened')
            return original_open(path, *args, **kwargs)
        def guarded_pread(fd, *args):
            if os.fstat(fd).st_ino == sentinel.stat().st_ino:
                raise AssertionError('target read')
            return original_pread(fd, *args)
        with mock.patch.object(os, 'open', side_effect=guarded_open), mock.patch.object(os, 'pread', side_effect=guarded_pread), mock.patch.object(builtins, 'open', side_effect=AssertionError('unexpected file read')), mock.patch.object(Path, 'resolve', side_effect=AssertionError('target resolved')):
            doc, out = self.run_phase(specs)
        self.assertTrue(doc['ok'], doc)
        rows = [json.loads(s) for s in (out / 'members.jsonl').read_text().splitlines()]
        self.assertEqual([r['link_target_classification'] for r in rows[:3]], ['absolute', 'out_of_tree', 'relative'])
        for row in rows:
            self.assertFalse(row['selected'])
            self.assertFalse(row['extractable'])
        self.assertEqual(rows[2]['decision'], 'recorded_not_followed')
        self.assertEqual(rows[0]['decision'], 'recorded_not_followed_nonextractable')
        self.assertEqual(doc['totals']['selected_bytes'], 0)
        self.assertFalse(doc['controls']['extraction_implemented'])
        # Strict helper remains the nonreuse guard for unsafe target policies.
        for target in ('/abs', '../../escape'):
            with self.assertRaises(sdk.InventoryError): sdk.link_safe('dir/sym', target, False)

    def test_rejected_hardlink_diagnostic_and_later_inputs_skipped(self):
        for target in ('/abs', '../../escape'):
            doc, out = self.run_phase(self.specs(tar_bytes([link('bad', target, tarfile.LNKTYPE)])))
            self.assertFalse(doc['ok'])
            self.assertEqual(doc['status'], 'partial')
            self.assertEqual(doc['skipped_inputs'], ['native', 'target'])
            self.assertEqual((out / 'members.jsonl').read_text(), '')
            records = doc.get('rejected_links', [])
            self.assertEqual(len(records), 1, doc)
            row = records[0]
            self.assertEqual(row['type'], 'hardlink')
            self.assertEqual(row['name']['value'], 'bad')
            self.assertEqual(row['target']['value'], target)
            self.assertIn('unsafe link', row['failed_rule'])

    def test_long_unicode_control_diagnostic_is_bounded_json(self):
        name = '../' + '\u0100\n\t"<>&' * 1000
        target = '/' + '\u00e9\r\n' * 1000
        doc, out = self.run_phase(self.specs(tar_bytes([link(name, target, tarfile.LNKTYPE)])))
        self.assertFalse(doc['ok'])
        records = doc.get('rejected_links', [])
        self.assertEqual(len(records), 1, doc)
        for key, original in (('name', name), ('target', target)):
            field = records[0][key]
            self.assertEqual(field['original_bytes'], len(original.encode('utf-8')))
            self.assertTrue(field['truncated'])
            self.assertLessEqual(len(json.dumps(field['value'], ensure_ascii=True)) - 2, 512)
        self.assertLess(len(json.dumps(records, ensure_ascii=True)), 2000)
        self.assertLess(len(doc['error']), 200)
        self.assertEqual(json.loads((out / 'manifest.json').read_text()), doc)

    def test_full_names_and_targets_charge_budget_before_rejection(self):
        name, target = '\x01' * 90, '/' + '\x02' * 90
        doc, _ = self.run_phase(self.specs(tar_bytes([link(name, target, tarfile.LNKTYPE)], tarfile.USTAR_FORMAT)), metadata_bytes=350)
        self.assertFalse(doc['ok'])
        self.assertIn('metadata_bytes', doc['error'])
        self.assertEqual(doc['totals']['metadata_bytes'], 362)
        self.assertEqual(doc['status'], 'partial')
        self.assertEqual(doc['skipped_inputs'], ['native', 'target'])
        self.assertEqual(len(doc.get('rejected_links', [])), 1)
        self.assertTrue(doc['rejected_links'][0]['name']['truncated'])
        self.assertTrue(doc['rejected_links'][0]['target']['truncated'])

    def test_malformed_targets_and_unsafe_members_still_fail_closed(self):
        for ti in [link('sym', ''), link('sym', 'C:/bad'), link('sym', 'dir\\bad'),
                   link('../sym', '/abs'), link('/sym', '/abs'), link('C:/sym', '/abs'),
                   link('dir\\sym', '/abs'), link('sym', 'bad-\udcc4')]:
            doc, _ = self.run_phase(self.specs(tar_bytes([ti], tarfile.GNU_FORMAT)))
            self.assertFalse(doc['ok'], repr(ti))
            self.assertEqual(len(doc.get('rejected_links', [])), 1, doc)
            self.assertTrue(doc['rejected_links'][0]['failed_rule'])
        for entries in ([link('same', '/abs'), link('./same', '/abs')],
                        [link('hard', '/abs', tarfile.LNKTYPE)],
                        [link('hard', '../../escape', tarfile.LNKTYPE)]):
            doc, _ = self.run_phase(self.specs(tar_bytes(entries)))
            self.assertFalse(doc['ok'])

    def test_rejected_retention_is_bounded_even_if_collector_reused(self):
        import sdk_inventory_phase as sdk
        import time
        budget = sdk.Budget(sdk.Limits(), time.monotonic() + 30)
        reject = getattr(budget, 'reject_link', None)
        self.assertTrue(callable(reject), 'bounded rejected-link collector missing')
        for _ in range(100): reject(link('name', '/target'), sdk.InventoryError('unsafe link target'))
        self.assertLessEqual(len(budget.rejected_links), 4)
        self.assertGreater(len(budget.rejected_links), 0)


# Keep only these new tests; inherited fixture methods remain available.
for _name in tuple(vars(InventoryTests)):
    if _name.startswith('test_'):
        setattr(LinkMetadataTests, _name, None)
del InventoryTests

"""Synthetic-only exact selected plaintext tests. Never read SDK source assets."""
import dataclasses
import hashlib
import json
import os
from pathlib import Path
import subprocess
import sys
import tarfile
import unittest
from unittest import mock

sys.path.insert(0, str(Path(__file__).resolve().parent))
import test_sdk_inventory_phase as fixtures

sdk, isolate = fixtures.sdk, fixtures.isolate


class TextSelectorTests(unittest.TestCase):
    def setUp(self):
        self.fixture = fixtures.InventoryTests('test_success_shared_three_streams')
        self.fixture.setUp()
        self.addCleanup(self.fixture.doCleanups)
        self.root = self.fixture.root

    def selector(self, label='sdk', path='a', size=5):
        return sdk.TextSelector(label, path, size)

    def run_selected(self, selectors, specs=None, cap=64 * 1024**2, **kwargs):
        self.fixture.serial += 1
        out = self.root / f'selected-{self.fixture.serial}'
        doc = sdk.inventory(specs or self.fixture.specs(), out, selectors=selectors,
                            selected_total_bytes=cap, **kwargs)
        self.assertEqual(doc, json.loads((out / 'manifest.json').read_text()))
        rows = [json.loads(x) for x in (out / 'members.jsonl').read_text().splitlines()] if (out / 'members.jsonl').exists() else []
        return doc, out, rows

    def assert_failed(self, result, error=None):
        doc, out, rows = result
        self.assertFalse(doc['ok'], doc)
        self.assertIn(doc['status'], ('failed', 'partial'))
        self.assertFalse(json.loads((out / 'manifest.json').read_text())['ok'])
        if error:
            self.assertIn(error, doc['error'])
        return doc, out, rows

    def test_exact_regular_multiple_inputs_hash_and_original_bytes(self):
        text = 'hello é\tworld\r\n'.encode()
        specs = self.fixture.specs(fixtures.tar_bytes([('dir/text', text), ('unselected', b'NO EMIT\x00\xff')]))
        selectors = [self.selector(label, 'dir/text', len(text)) for label in ('sdk', 'target')]
        doc, out, rows = self.run_selected(selectors, specs, cap=2 * len(text))
        self.assertTrue(doc['ok'], doc)
        self.assertEqual(doc['mode'], 'SELECTEDTEXT')
        self.assertEqual(doc['totals']['selected_bytes'], 2 * len(text))
        selected = [r for r in rows if r['selected']]
        self.assertEqual([r['input'] for r in selected], ['sdk', 'target'])
        for r in selected:
            self.assertEqual(r['raw_name'], 'dir/text')
            self.assertEqual(r['size'], len(text))
            self.assertEqual(r['content_sha256'], hashlib.sha256(text).hexdigest())
            data_path = r['output_data_path']
            self.assertEqual(Path(data_path).name, data_path)
            self.assertEqual((out / data_path).read_bytes(), text)
            self.assertEqual((out / data_path).stat().st_mode & 0o777, 0o600)
        self.assertEqual(len({r['output_data_path'] for r in selected}), 2)
        self.assertEqual(len(list(out.iterdir())), 4)
        self.assertTrue(all(a['integrity_eof'] and a['tar_eof'] for a in doc['inputs']))
        self.assertEqual(doc['full_hash_bytes'], sum(s.size for s in specs))

    def test_default_metadata_only_emits_no_content(self):
        doc, out = self.fixture.run_phase(self.fixture.specs(fixtures.tar_bytes([('a', b'\x00\xff')])) )
        self.assertTrue(doc['ok'])
        self.assertEqual(doc['mode'], 'METADATAONLY')
        self.assertEqual(doc['totals']['selected_bytes'], 0)
        self.assertEqual(sorted(p.name for p in out.iterdir()), ['manifest.json', 'members.jsonl'])

    def test_size_mismatch_both_directions(self):
        for size in (4, 6):
            with self.subTest(size=size):
                doc, out, _ = self.assert_failed(self.run_selected([self.selector(size=size)]), 'selected size mismatch')
                self.assertEqual(doc['status'], 'partial')
                self.assertEqual(list(out.glob('selected-*.txt')), [])

    def test_missing_checked_after_all_streams(self):
        doc, _, _ = self.assert_failed(self.run_selected([self.selector(path='missing')]), 'missing selected')
        self.assertEqual(len(doc['inputs']), 3)
        self.assertTrue(all(x['integrity_eof'] and x['tar_eof'] for x in doc['inputs']))

    def test_one_missing_among_multiple_prevents_success(self):
        doc, _, rows = self.assert_failed(self.run_selected([self.selector(), self.selector('target', 'missing')]))
        self.assertEqual(sum(r['selected'] for r in rows), 1)
        self.assertEqual(doc['status'], 'partial')

    def test_duplicate_selectors_even_different_sizes(self):
        for size in (5, 6):
            with self.subTest(size=size):
                self.assert_failed(self.run_selected([self.selector(), self.selector(size=size)]), 'duplicate selector')

    def test_unknown_input_and_bad_sizes_rejected_before_parser(self):
        cases = [self.selector('other')]
        cases += [self.selector(size=size) for size in (-1, 16 * 1024**2 + 1, 2**100, True, 1.0, '5')]
        for selector in cases:
            with self.subTest(selector=selector), mock.patch.object(sdk, 'parse_archive', side_effect=AssertionError('parser reached')):
                doc, _, _ = self.assert_failed(self.run_selected([selector]))
                self.assertEqual(doc['inputs'], [])
                self.assertNotIn('parser reached', doc['error'])

    def test_literal_paths_reject_globs_aliases_traversal_controls(self):
        for path in ('', '.', './a', 'a/', 'a//b', 'a/./b', '../a', 'a/../b', '/a',
                     'C:/a', 'C:a', 'a\\b', 'a*', 'a?', 'a[0]', 'a]', 'a\x00', 'a\n', 'a\u200b'):
            with self.subTest(path=path):
                doc, _, _ = self.assert_failed(self.run_selected([self.selector(path=path)]))
                self.assertEqual(doc['inputs'], [])

    def test_canonical_member_alias_is_not_selected(self):
        for path in ('./a', 'x/../a', 'd//a', 'd/./a', 'a/'):
            requested = 'd/a' if path.startswith('d') else 'a'
            with self.subTest(path=path):
                specs = self.fixture.specs(fixtures.tar_bytes([(path, b'hello')]))
                self.assert_failed(self.run_selected([self.selector(path=requested)], specs))

    def test_selected_links_directories_and_special_members_fail_never_follow(self):
        sentinel = self.root / 'SENTINEL'
        sentinel.write_text('synthetic NEVER OPEN')
        for kind in (tarfile.SYMTYPE, tarfile.LNKTYPE, tarfile.DIRTYPE, tarfile.FIFOTYPE,
                     tarfile.CHRTYPE, tarfile.BLKTYPE, tarfile.GNUTYPE_SPARSE):
            with self.subTest(kind=kind):
                ti = tarfile.TarInfo('chosen'); ti.type = kind
                ti.linkname = str(sentinel) if kind == tarfile.SYMTYPE else 'a'
                specs = self.fixture.specs(fixtures.tar_bytes([('a', b'hello'), ti]))
                original = os.open
                def guard(path, *args, **kwargs):
                    if os.fspath(path) == str(sentinel):
                        raise AssertionError('link target opened')
                    return original(path, *args, **kwargs)
                with mock.patch.object(os, 'open', side_effect=guard):
                    doc, out, _ = self.assert_failed(self.run_selected([self.selector(path='chosen', size=0)], specs))
                self.assertNotIn('link target opened', doc['error'])
                self.assertEqual(list(out.glob('selected-*.txt')), [])

    def test_plaintext_rejects_nul_utf8_controls_binary(self):
        bad = [b'a\x00b', b'\xff', b'\xc0\xaf', b'\xed\xa0\x80', b'\x7fELF', b'\x89PNG\r\n\x1a\n']
        bad += [chr(c).encode() for c in list(range(0, 9)) + [11, 12] + list(range(14, 32)) + list(range(127, 160))]
        bad += [c.encode() for c in ('\u200b', '\u202e', '\ufeff', '\u2028', '\u2029', '\ue000', '\u0378')]
        for data in bad:
            with self.subTest(data=data):
                specs = self.fixture.specs(fixtures.tar_bytes([('a', data)]))
                doc, out, _ = self.assert_failed(self.run_selected([self.selector(size=len(data))], specs))
                self.assertEqual(list(out.glob('selected-*.txt')), [])
                self.assertEqual(doc['totals']['selected_bytes'], 0)

    def test_shared_cap_exact_and_one_byte_over_across_inputs(self):
        selectors = [self.selector(label) for label in ('sdk', 'native', 'target')]
        doc, _, _ = self.run_selected(selectors, cap=15)
        self.assertTrue(doc['ok'], doc)
        self.assertEqual(doc['totals']['selected_bytes'], 15)
        self.assert_failed(self.run_selected(selectors, cap=14), 'selected total')
        for cap in (-1, 64 * 1024**2 + 1, 2**100, True, 1.0):
            with self.subTest(cap=cap):
                self.assert_failed(self.run_selected(selectors, cap=cap))

    def test_hard_member_limit_exact_and_oversize(self):
        size = 16 * 1024**2
        specs = self.fixture.specs(fixtures.tar_bytes([('a', b'x' * size)]))
        doc, out, rows = self.run_selected([self.selector(size=size)], specs, cap=size)
        self.assertTrue(doc['ok'], doc)
        selected = next(r for r in rows if r['selected'])
        self.assertEqual((out / selected['output_data_path']).stat().st_size, size)
        self.assert_failed(self.run_selected([self.selector(size=size + 1)], specs, cap=size + 1))

    def test_hard_total_limit_64mib_boundary(self):
        # Config-only synthetic evidence: all four selectors fit the immutable
        # hard total; one more byte fails before parsing. No huge archive needed.
        size = 16 * 1024**2
        selectors = [self.selector('sdk', f'a{i}', size) for i in range(4)]
        doc, _, _ = self.assert_failed(self.run_selected(selectors, cap=64 * 1024**2), 'missing selected')
        self.assertEqual(len(doc['inputs']), 3)
        self.assert_failed(self.run_selected(selectors + [self.selector('target', 'extra', 1)]), 'selected total')

    def test_empty_selected_regular_text(self):
        specs = self.fixture.specs(fixtures.tar_bytes([('a', b'')]))
        doc, out, rows = self.run_selected([self.selector(size=0)], specs, cap=0)
        self.assertTrue(doc['ok'], doc)
        row = next(r for r in rows if r['selected'])
        self.assertEqual((out / row['output_data_path']).read_bytes(), b'')
        self.assertEqual(row['content_sha256'], hashlib.sha256(b'').hexdigest())

    def test_unselected_absolute_symlink_remains_metadata(self):
        ti = tarfile.TarInfo('sym'); ti.type = tarfile.SYMTYPE; ti.linkname = '/never/open'
        specs = self.fixture.specs(fixtures.tar_bytes([('a', b'hello'), ti]))
        doc, _, rows = self.run_selected([self.selector()], specs, cap=5)
        self.assertTrue(doc['ok'], doc)
        links = [r for r in rows if r['type'] == 'symlink']
        self.assertTrue(all(r['link_target_classification'] == 'absolute' and not r['selected'] for r in links))

    def test_output_fresh_symlink_and_existing_data_refusal(self):
        selectors = [self.selector()]; specs = self.fixture.specs()
        for kind in ('existing', 'leaf', 'ancestor'):
            out = self.root / kind
            if kind == 'existing': out.mkdir()
            elif kind == 'leaf': out.symlink_to(self.root / 'absent')
            else:
                out.symlink_to(self.root, target_is_directory=True); out = out / 'new'
            with self.subTest(kind=kind), self.assertRaises(OSError):
                sdk.inventory(specs, out, selectors=selectors, selected_total_bytes=5)
        # A supplied output descriptor is launcher-only. Even if polluted, data
        # creation must never overwrite or follow an existing generated name.
        out = self.root / 'data-symlink'; out.mkdir()
        target = self.root / 'target'; target.write_bytes(b'sentinel')
        (out / 'selected-000001.txt').symlink_to(target)
        fd = sdk.directory_fd(out)
        try:
            doc = sdk.inventory(specs, out, output_fd=fd, selectors=selectors, selected_total_bytes=5)
        finally:
            os.close(fd)
        self.assertFalse(doc['ok'], doc)
        self.assertEqual(target.read_bytes(), b'sentinel')

    def test_all_pins_precede_selected_content_reads(self):
        specs = self.fixture.specs()
        specs[2] = dataclasses.replace(specs[2], sha256='0' * 64)
        with mock.patch.object(sdk, 'parse_archive', side_effect=AssertionError('must not parse')):
            doc, out, _ = self.assert_failed(self.run_selected([self.selector()], specs))
        self.assertIn('pin', doc['error'])
        self.assertEqual(doc['totals']['selected_bytes'], 0)
        self.assertEqual(list(out.glob('selected-*.txt')), [])

    def test_selected_content_never_skips_eof_corruption_or_shared_caps(self):
        selectors = [self.selector()]
        for index in (0, 1, 2):
            for transform in (lambda b: b[:-1], lambda b: b + b'junk', lambda b: b + b,
                              lambda b: b[:-8] + bytes([b[-8] ^ 1]) + b[-7:]):
                with self.subTest(index=index, transform=transform):
                    self.assert_failed(self.run_selected(selectors, self.fixture.specs(transforms={index: transform})))
        raw = fixtures.tar_bytes()
        for raw in (raw[:1024], raw[:1536] + b'BAD' + raw[1539:]):
            self.assert_failed(self.run_selected(selectors, self.fixture.specs(raw)))
        for limits in (sdk.Limits(members=2), sdk.Limits(decoded_bytes=20480),
                       sdk.Limits(metadata_bytes=2), sdk.Limits(logical_bytes=14)):
            self.assert_failed(self.run_selected(selectors, limits=limits))

    def test_no_nested_expansion(self):
        specs = self.fixture.specs(fixtures.tar_bytes([('outer.tar', fixtures.tar_bytes([('a', b'hello')]))]))
        self.assert_failed(self.run_selected([self.selector()], specs), 'missing selected')
        self.assert_failed(self.run_selected([self.selector(path='outer.tar', size=10240)], specs))

    def test_cli_literal_configuration_and_no_pin_overrides(self):
        base = sum((['--' + s.label, s.path] for s in sdk.PRODUCTION_SPECS), [])
        base += ['--output-dir', str(self.root / 'never-opened')]
        args = sdk.production_arguments(base + ['--select-text', 'sdk', 'a', '5',
                                                '--select-text', 'target', 'a', '5',
                                                '--selected-total-bytes', '10'])
        self.assertEqual(args.selectors, [self.selector(), self.selector('target')])
        self.assertEqual(args.selected_total_bytes, 10)
        for extra in (['--select-text', 'sdk', 'a', '5'], ['--selected-total-bytes', '5'],
                      ['--select-text', 'sdk', './a', '5', '--selected-total-bytes', '5'],
                      ['--select-text', 'sdk', 'a', '-1', '--selected-total-bytes', '5'],
                      ['--select-text', 'sdk', 'a', '05', '--selected-total-bytes', '5'],
                      ['--select-text', 'sdk', 'a', str(2**100), '--selected-total-bytes', '5']):
            with self.subTest(extra=extra), self.assertRaises((sdk.InventoryError, SystemExit)):
                sdk.production_arguments(base + extra)
        self.assertFalse((self.root / 'never-opened').exists())

    def test_launcher_forwards_literal_selection_and_keeps_devnull(self):
        specs = self.fixture.specs(); out = self.root / 'launcher'
        captured = {}
        original = isolate._bootstrap
        def bootstrap(*args, **kwargs):
            captured['code'] = original(*args, **kwargs)
            return captured['code']
        def fail(*args, **kwargs):
            self.assertIs(kwargs['stdin'], subprocess.DEVNULL)
            self.assertIn('--unshare-all', args[0])
            self.assertIn('--nofile=64', args[0])
            raise OSError('synthetic startup failure')
        with mock.patch.object(isolate, '_bootstrap', side_effect=bootstrap), mock.patch.object(isolate.subprocess, 'run', side_effect=fail):
            result = isolate.launch(specs, out, selectors=[self.selector()], selected_total_bytes=5)
        self.assertFalse(result['ok'])
        self.assertIn('synthetic startup failure', result['error'])
        self.assertIn('TextSelector', captured['code'])
        self.assertIn('selected_total_bytes=5', captured['code'])
        self.assertEqual(json.loads((out / 'manifest.json').read_text())['mode'], 'SELECTEDTEXT')

    def test_synthetic_selected_sandbox(self):
        specs = self.fixture.specs(); out = self.root / 'sandbox'
        result = isolate.launch(specs, out, synthetic_probe=True,
                                selectors=[self.selector('target')], selected_total_bytes=5)
        if result.get('sandbox_unavailable'):
            self.assertFalse(result['ok'])
            self.skipTest('unchanged nested sandbox unavailable: ' + str(result['error']))
        self.assertTrue(result['ok'], result)
        doc = json.loads((out / 'manifest.json').read_text())
        self.assertEqual(doc['totals']['selected_bytes'], 5)
        rows = [json.loads(x) for x in (out / 'members.jsonl').read_text().splitlines()]
        row = next(r for r in rows if r['selected'])
        self.assertEqual((out / row['output_data_path']).read_bytes(), b'hello')
        self.assertEqual(row['content_sha256'], hashlib.sha256(b'hello').hexdigest())
        probe = json.loads((out / 'isolation-probe.json').read_text())
        self.assertTrue(probe['home_hidden'] and probe['input_readonly'] and probe['network_unavailable'])


if __name__ == '__main__':
    unittest.main()

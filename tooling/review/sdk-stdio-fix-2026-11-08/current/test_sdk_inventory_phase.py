"""Synthetic-only SDK contract tests. Never opens production input paths."""
import dataclasses
import gzip
import hashlib
import io
import json
import lzma
import os
from pathlib import Path
import subprocess
import sys
import tarfile
import tempfile
import time
import unittest
from unittest import mock

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import sdk_inventory_phase as sdk
import isolate_sdk_inventory as isolate


def tar_bytes(entries=None, fmt=tarfile.PAX_FORMAT):
    out = io.BytesIO()
    with tarfile.open(fileobj=out, mode='w', format=fmt) as tf:
        for entry in entries or [('a', b'hello')]:
            if isinstance(entry, tarfile.TarInfo):
                tf.addfile(entry, io.BytesIO(b'x' * entry.size) if entry.isreg() else None)
            else:
                name, data = entry
                ti = tarfile.TarInfo(name)
                ti.size = len(data)
                tf.addfile(ti, io.BytesIO(data))
    return out.getvalue()


class InventoryTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory(prefix='sdk-synthetic-')
        self.root = Path(self.tmp.name)
        self.addCleanup(self.tmp.cleanup)
        self.serial = 0

    def specs(self, tar=None, transforms=None):
        tar = tar if tar is not None else tar_bytes()
        result = []
        for i, codec in enumerate(('xz', 'gz', 'gz')):
            packed = lzma.compress(tar) if codec == 'xz' else gzip.compress(tar, mtime=0)
            if transforms and i in transforms:
                packed = transforms[i](packed)
            prefix = b'synthetic\nMARKER:\n' if i == 0 else b''
            data = prefix + packed
            self.serial += 1
            path = self.root / f'fixture-{self.serial}'
            path.write_bytes(data)
            result.append(sdk.InputSpec(('sdk', 'native', 'target')[i], str(path),
                         len(data), hashlib.sha256(data).hexdigest(), codec,
                         len(prefix), b'MARKER:\n' if i == 0 else b''))
        return result

    def run_phase(self, specs=None, **limits):
        self.serial += 1
        out = self.root / f'out-{self.serial}'
        result = sdk.inventory(specs or self.specs(), out, sdk.Limits(**limits))
        manifest = json.loads((out / 'manifest.json').read_text())
        self.assertEqual(result, manifest)
        self.assertEqual(manifest['ok'], manifest['status'] == 'ok')
        return manifest, out

    def test_success_shared_three_streams(self):
        specs = self.specs()
        doc, out = self.run_phase(specs)
        self.assertTrue(doc['ok'], doc)
        self.assertEqual(doc['totals']['members'], 3)
        self.assertEqual(doc['totals']['logical_regular_bytes'], 15)
        self.assertEqual(doc['totals']['decoded_bytes'], 3 * len(tar_bytes()))
        self.assertEqual(doc['totals']['selected_bytes'], 0)
        self.assertEqual(doc['full_hash_bytes'], sum(s.size for s in specs))
        self.assertTrue(all(a['integrity_eof'] and a['tar_eof'] for a in doc['inputs']))
        rows = [json.loads(x) for x in (out / 'members.jsonl').read_text().splitlines()]
        self.assertEqual([r['raw_name'] for r in rows], ['a'] * 3)
        self.assertEqual(sorted(p.name for p in out.iterdir()), ['manifest.json', 'members.jsonl'])

    def test_all_pins_precede_any_parser(self):
        specs = self.specs()
        specs[2] = dataclasses.replace(specs[2], sha256='0' * 64)
        with mock.patch.object(sdk, 'parse_archive', side_effect=AssertionError('must not parse')):
            doc, _ = self.run_phase(specs)
        self.assertFalse(doc['ok'])
        self.assertIn('pin', doc['error'])
        self.assertEqual(doc['totals']['decoded_bytes'], 0)

    def test_size_nofollow_offset_marker_signature(self):
        for case in ('size', 'symlink', 'ancestor', 'offset', 'marker', 'signature'):
            with self.subTest(case=case):
                specs = self.specs()
                s = specs[0]
                if case == 'size':
                    specs[0] = dataclasses.replace(s, size=s.size + 1)
                elif case in ('symlink', 'ancestor'):
                    link = self.root / f'link-{self.serial}'
                    link.symlink_to(s.path if case == 'symlink' else self.root,
                                    target_is_directory=case == 'ancestor')
                    specs[0] = dataclasses.replace(s, path=str(link if case == 'symlink' else link / Path(s.path).name))
                elif case == 'offset':
                    specs[0] = dataclasses.replace(s, offset=s.offset + 1)
                else:
                    data = bytearray(Path(s.path).read_bytes())
                    data[s.offset - 2 if case == 'marker' else s.offset] ^= 1
                    Path(s.path).write_bytes(data)
                    specs[0] = dataclasses.replace(s, sha256=hashlib.sha256(data).hexdigest())
                doc, _ = self.run_phase(specs)
                self.assertFalse(doc['ok'], case)
                self.assertEqual(doc['totals']['decoded_bytes'], 0)

    def test_mutation_detected_and_stable_descriptor(self):
        specs = self.specs()
        original = sdk.parse_archive
        def mutate(*args, **kwargs):
            with open(specs[0].path, 'ab') as f:
                f.write(b'!')
            return original(*args, **kwargs)
        with mock.patch.object(sdk, 'parse_archive', side_effect=mutate):
            doc, _ = self.run_phase(specs)
        self.assertFalse(doc['ok'])
        self.assertIn('mutat', doc['error'])

    def test_compression_failures_both_codecs(self):
        transforms = {
            'truncated': lambda b: b[:-4],
            'corrupt': lambda b: b[:-6] + bytes([b[-6] ^ 0x80]) + b[-5:],
            'concat': lambda b: b + b,
            'zero_tail': lambda b: b + b'\0',
            'junk_tail': lambda b: b + b'junk',
        }
        for index in (0, 1):
            for kind, transform in transforms.items():
                with self.subTest(index=index, kind=kind):
                    doc, _ = self.run_phase(self.specs(transforms={index: transform}))
                    self.assertFalse(doc['ok'])
                    self.assertLessEqual(len(doc['inputs']), index + 1)

    def test_tail_and_missing_tar_eof(self):
        base = tar_bytes()
        for data in (base + b'x', base[:1024] + b'X' * 512,
                     base[:1024], base[:1536], base[:1024] + b'\0' * 511):
            with self.subTest(length=len(data)):
                doc, _ = self.run_phase(self.specs(data))
                self.assertFalse(doc['ok'])
        # Nonzero data in decoder read-ahead beyond the FIRST tar zero header.
        doc, _ = self.run_phase(self.specs(base[:1536] + b'BAD' + base[1539:]))
        self.assertFalse(doc['ok'])
        doc, _ = self.run_phase(self.specs(base + b'\0' * 1024))
        self.assertTrue(doc['ok'])

    def test_shared_limits_are_independent(self):
        for kwargs, counter in (({'members': 2}, 'members'),
                                ({'metadata_bytes': 2}, 'metadata_bytes'),
                                ({'logical_bytes': 14}, 'logical_regular_bytes'),
                                ({'decoded_bytes': 2 * len(tar_bytes())}, 'decoded_bytes')):
            with self.subTest(kwargs=kwargs):
                doc, _ = self.run_phase(self.specs(), **kwargs)
                self.assertFalse(doc['ok'])
                self.assertIn('limit', doc['error'])
                self.assertGreater(doc['totals'][counter], list(kwargs.values())[0])
        doc, _ = self.run_phase(self.specs(), logical_bytes=15, decoded_bytes=3 * len(tar_bytes()))
        self.assertTrue(doc['ok'])

    def test_deadline_covers_pins(self):
        with mock.patch.object(sdk.time, 'monotonic', side_effect=[0, 121, 122, 123, 124, 125]):
            doc, _ = self.run_phase(self.specs())
        self.assertFalse(doc['ok'])
        self.assertIn('deadline', doc['error'])

    def test_unsafe_duplicate_devices_sparse(self):
        cases = [[('../x', b'')], [('/abs', b'')], [('C:/x', b'')],
                 [('x/../y', b'')], [('a', b''), ('./a', b'')]]
        for kind in (tarfile.CHRTYPE, tarfile.FIFOTYPE, tarfile.GNUTYPE_SPARSE, b'Z'):
            ti = tarfile.TarInfo('bad'); ti.type = kind
            cases.append([ti])
        ti = tarfile.TarInfo('sparse'); ti.pax_headers = {'GNU.sparse.map': '0,1', 'GNU.sparse.size': '1'}
        cases.append([ti])
        for entries in cases:
            with self.subTest(entries=str(entries)):
                doc, _ = self.run_phase(self.specs(tar_bytes(entries)))
                self.assertFalse(doc['ok'])

    def test_links_pax_gnu_longnames_metadata_only(self):
        sy = tarfile.TarInfo('dir/sym'); sy.type = tarfile.SYMTYPE; sy.linkname = 'file'
        hard = tarfile.TarInfo('hard'); hard.type = tarfile.LNKTYPE; hard.linkname = 'dir/file'
        pax = tarfile.TarInfo('p' * 180); pax.pax_headers = {'comment': 'benign-é'}
        for fmt in (tarfile.PAX_FORMAT, tarfile.GNU_FORMAT):
            doc, out = self.run_phase(self.specs(tar_bytes([('dir/file', b''), sy, hard, pax], fmt)))
            self.assertTrue(doc['ok'], doc)
            rows = [json.loads(x) for x in (out / 'members.jsonl').read_text().splitlines()]
            links = [r for r in rows if r['link_target']]
            self.assertEqual(len(links), 6)
            self.assertTrue(all(r['decision'] == 'recorded_not_followed' for r in links))
            self.assertGreater(doc['totals']['metadata_bytes'], sum(len(r['raw_name']) for r in rows))
        sy.linkname = '../../escape'
        doc, _ = self.run_phase(self.specs(tar_bytes([sy])))
        self.assertFalse(doc['ok'])

    def test_lzma_memory_limit_and_bounded_decoder(self):
        specs = self.specs(transforms={0: lambda _: lzma.compress(tar_bytes(),
                           filters=[{'id': lzma.FILTER_LZMA2, 'dict_size': 8 << 20}])})
        doc, _ = self.run_phase(specs, lzma_memlimit=1 << 20)
        self.assertFalse(doc['ok'])
        self.assertIn('Memory', doc['error'])
        doc, _ = self.run_phase(self.specs(tar_bytes([('large', b'A' * (2 << 20))])))
        self.assertTrue(doc['ok'])
        self.assertTrue(all(a['max_decoder_chunk'] <= sdk.CHUNK for a in doc['inputs']))

    def test_output_freshness_symlinks_atomic_false(self):
        specs = self.specs()
        for kind in ('existing', 'dangling', 'ancestor'):
            p = self.root / f'bad-{kind}'
            if kind == 'existing': p.mkdir()
            elif kind == 'dangling': p.symlink_to(self.root / 'absent')
            else:
                p.symlink_to(self.root, target_is_directory=True)
                p = p / 'fresh'
            with self.assertRaises(OSError): sdk.inventory(specs, p)
        doc, out = self.run_phase(self.specs(transforms={0: lambda b: b[:-1]}))
        self.assertFalse(doc['ok'])
        self.assertFalse(any(p.name.startswith('.') for p in out.iterdir()))
        self.assertTrue((out / 'members.jsonl').exists())

    def test_closed_production_parser(self):
        for module in (sdk, isolate):
            with self.assertRaises(SystemExit):
                module.argument_parser().parse_args(['--test-spec', 'bad'])
        self.assertEqual(sum(s.size for s in sdk.PRODUCTION_SPECS), 498625937)
        self.assertEqual(sdk.PRODUCTION_SPECS[0].offset, 10820)

    def test_wrapper_failure_has_atomic_false_manifest(self):
        specs = self.specs()
        out = self.root / 'launcher-failure'
        with mock.patch.object(isolate.subprocess, 'run', side_effect=OSError('synthetic startup failure')):
            doc = isolate.launch(specs, out)
        self.assertFalse(doc['ok'])
        self.assertFalse(json.loads((out / 'manifest.json').read_text())['ok'])
        self.assertFalse(json.loads((out / 'launcher-result.json').read_text())['ok'])

    def test_wrapper_command_exact_binds_and_limits(self):
        specs = self.specs()
        cmd = isolate.build_command(specs, '/proc/self/fd/99', ['/usr/bin/python3', '-I', '/tool/probe.py'], 117)
        self.assertIn('--unshare-all', cmd)
        self.assertIn('--as=1073741824', cmd)
        self.assertIn('117', cmd)
        for spec in specs: self.assertEqual(cmd.count(spec.path), 1)
        self.assertNotIn(str(self.root), cmd)
        self.assertNotIn('/home', cmd)


    def test_failed_phase_reports_verified_and_skipped_inputs(self):
        specs = self.specs(transforms={0: lambda b: b[:-1]})
        doc, _ = self.run_phase(specs)
        self.assertFalse(doc['ok'])
        self.assertEqual(len(doc['pin_verifications']), 3)
        self.assertTrue(all(p['verified'] for p in doc['pin_verifications']))
        self.assertEqual(doc['skipped_inputs'], ['native', 'target'])
        self.assertEqual([p['bytes_hashed'] for p in doc['pin_verifications']], [s.size for s in specs])

    def test_isolated_python_cli_rejects_synthetic_paths_before_any_input_open(self):
        out = self.root / 'cli-never-created'
        cmd = [sys.executable, '-I', '-B', str(Path(isolate.__file__).absolute()),
               '--sdk', str(self.root / 'not-sdk'), '--native', str(self.root / 'not-native'),
               '--target', str(self.root / 'not-target'), '--output-dir', str(out)]
        result = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        self.assertEqual(result.returncode, 2, result.stderr.decode())
        self.assertFalse(json.loads(result.stdout)['ok'])
        self.assertFalse(out.exists())

    def test_closed_cli_rejects_overrides_and_wrong_paths(self):
        base = []
        for s in sdk.PRODUCTION_SPECS:
            base += ['--' + s.label, s.path]
        base += ['--output-dir', str(self.root / 'never-created')]
        for flag in ('--select', '--max-members', '--offset', '--expected-hash', '--test-spec'):
            with self.subTest(flag=flag), self.assertRaises(SystemExit):
                sdk.production_arguments(base + [flag, '1'])
        base[1] = str(self.root / 'wrong')
        with self.assertRaises(sdk.InventoryError):
            sdk.production_arguments(base)
        self.assertFalse((self.root / 'never-created').exists())

    def test_global_pax_and_hidden_extensions_are_counted(self):
        raw = io.BytesIO()
        with tarfile.open(fileobj=raw, mode='w', format=tarfile.PAX_FORMAT,
                          pax_headers={'comment': 'global-é'}) as tf:
            member = tarfile.TarInfo('long-' + 'x' * 160)
            tf.addfile(member)
        doc, _ = self.run_phase(self.specs(raw.getvalue()))
        self.assertTrue(doc['ok'], doc)
        # global header + local long-name PAX header + regular per archive.
        self.assertEqual(doc['totals']['members'], 9)
        doc, _ = self.run_phase(self.specs(raw.getvalue()), members=8)
        self.assertFalse(doc['ok'])
        self.assertEqual(doc['totals']['members'], 9)
        doc, _ = self.run_phase(self.specs(raw.getvalue()), metadata_bytes=500)
        self.assertFalse(doc['ok'])

    def test_invalid_later_tar_header_is_not_tolerated(self):
        raw = tar_bytes()
        bad = raw[:1024] + b'not a tar header'.ljust(512, b'x') + raw[1536:]
        doc, _ = self.run_phase(self.specs(bad))
        self.assertFalse(doc['ok'])
        self.assertIn('invalid tar header', doc['error'])

    def test_integrity_corruption_after_logical_tar_eof_is_detected(self):
        for index in (0, 1):
            def damage(b):
                pos = -12 if index == 0 else -8
                return b[:pos] + bytes([b[pos] ^ 1]) + b[pos+1:]
            doc, _ = self.run_phase(self.specs(transforms={index: damage}))
            self.assertFalse(doc['ok'])
            self.assertFalse(doc['inputs'][-1]['integrity_eof'])

    def test_descriptor_replacement_does_not_substitute_unpinned_input(self):
        specs = self.specs()
        original = sdk.parse_archive
        def replace(*args, **kwargs):
            path = Path(specs[0].path)
            replacement = path.with_suffix('.replacement')
            replacement.write_bytes(b'not the verified descriptor')
            replacement.replace(path)
            return original(*args, **kwargs)
        with mock.patch.object(sdk, 'parse_archive', side_effect=replace):
            doc, out = self.run_phase(specs)
        self.assertFalse(doc['ok'])
        self.assertIn('mutation', doc['error'])
        self.assertIn('"raw_name":"a"', (out / 'members.jsonl').read_text())

    def test_no_unbounded_reader_calls_and_drain_deadline(self):
        spec = self.specs()[0]
        fd, _ = sdk.open_regular(spec.path)
        self.addCleanup(os.close, fd)
        obs = dict(compressed_bytes_read=0, compressed_bytes_consumed=None,
                   decoded_bytes=0, max_decoder_chunk=0, integrity_eof=False)
        budget = sdk.Budget(sdk.Limits(), time.monotonic() + 120)
        reader = sdk.DecodedReader(fd, spec, budget, obs)
        with self.assertRaises(sdk.InventoryError): reader.read(-1)
        self.assertEqual(reader.read(1), tar_bytes()[:1])
        self.assertGreater(budget.totals['decoded_bytes'], reader.tell())
        budget.deadline = time.monotonic() - 1
        with self.assertRaisesRegex(sdk.InventoryError, 'deadline'):
            reader.read(65536)

    def test_worker_limit_claim_is_truthful_outside_sandbox(self):
        doc, _ = self.run_phase(self.specs())
        self.assertIsNone(doc['controls']['enforced_address_space_bytes'])
        self.assertEqual(doc['controls']['required_launcher_address_space_bytes'], 1024**3)

    def test_launcher_timeout_keeps_partial_and_false(self):
        specs = self.specs()
        out = self.root / 'timed-out'
        with mock.patch.object(isolate.subprocess, 'run',
                               side_effect=subprocess.TimeoutExpired('synthetic', 120)):
            doc = isolate.launch(specs, out)
        self.assertFalse(doc['ok'])
        self.assertIn('TimeoutExpired', doc['error'])
        self.assertFalse(json.loads((out / 'manifest.json').read_text())['ok'])

    def test_output_publication_never_overwrites(self):
        out = self.root / 'publication'
        fd = sdk.fresh_output(out)
        try:
            sdk.atomic_json(fd, 'manifest.json', {'ok': False})
            with self.assertRaises(FileExistsError):
                sdk.atomic_json(fd, 'manifest.json', {'ok': True})
            self.assertFalse(json.loads((out / 'manifest.json').read_text())['ok'])
            self.assertFalse((out / '.manifest.json.pending').exists())
        finally:
            os.close(fd)

    def test_synthetic_full_path_isolation(self):
        specs = self.specs()
        out = self.root / 'isolated'
        # API-only synthetic specs; production CLI offers no alternate pins.
        doc = isolate.launch(specs, out, synthetic_probe=True)
        evidence = json.loads((out / 'launcher-result.json').read_text())
        if evidence.get('sandbox_unavailable'):
            self.assertFalse(doc['ok'])
            self.skipTest('isolation runtime blocked: ' + evidence['error'])
        self.assertTrue(doc['ok'], evidence)
        probe = json.loads((out / 'isolation-probe.json').read_text())
        self.assertTrue(probe['home_hidden'])
        self.assertTrue(probe['input_readonly'])
        self.assertNotEqual(probe['net_ns'], os.readlink('/proc/self/ns/net'))
        self.assertTrue(probe['network_unavailable'])


if __name__ == '__main__':
    unittest.main()

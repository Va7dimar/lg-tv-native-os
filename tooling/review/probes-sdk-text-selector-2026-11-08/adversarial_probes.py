"""Independent synthetic probes for selected-plaintext. No SDK assets opened."""
import gzip, hashlib, io, json, lzma, os, shlex, sys, tarfile, tempfile, traceback
from pathlib import Path
from unittest import mock

ROOT = Path('/workspace/lg-tv/tooling')
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / 'tests'))
import sdk_inventory_phase as sdk
from test_sdk_inventory_phase import InventoryTests, tar_bytes

results = []

def rec(name, passed, detail):
    results.append({'name': name, 'passed': bool(passed), 'detail': detail})
    print(('PASS' if passed else 'FAIL'), name)

COMMAND = Path('/workspace/lg-tv/tooling/review/sdk-text-selector-2026-11-08/exact-command.txt')
SELECTORS = [
    ('sdk', 'version-ca9v1-starfishmllib32-linux-gnueabi', 125),
    ('sdk', 'environment-setup-ca9v1-starfishmllib32-linux-gnueabi', 4321),
    ('sdk', 'site-config-ca9v1-starfishmllib32-linux-gnueabi', 13611),
    ('sdk', 'sysroots/ca9v1-starfishmllib32-linux-gnueabi/usr/include/linux/version.h', 97),
    ('target', 'usr/include/linux/version.h', 97),
    ('sdk', 'sysroots/ca9v1-starfishmllib32-linux-gnueabi/usr/include/features.h', 15721),
    ('target', 'usr/include/features.h', 15721),
    ('sdk', 'sysroots/x86_64-starfishsdk-linux/usr/lib/arm-starfish-linux-gnueabi/gcc/arm-starfish-linux-gnueabi/8.2.0/include-fixed/README', 750),
    ('target', 'sysroot-providers/lib32-linux-libc-headers', 24),
    ('target', 'sysroot-providers/lib32-glibc', 11),
]

helper = InventoryTests('run_phase')
helper.setUp()

def make_specs(sdk_entries, native_entries, target_entries):
    tars = [tar_bytes(sdk_entries), tar_bytes(native_entries), tar_bytes(target_entries)]
    result = []
    for i, (tar, codec) in enumerate(zip(tars, ('xz', 'gz', 'gz'))):
        packed = lzma.compress(tar) if codec == 'xz' else gzip.compress(tar, mtime=0)
        prefix = b'synthetic\nMARKER:\n' if i == 0 else b''
        data = prefix + packed
        helper.serial += 1
        path = helper.root / f'probe-{helper.serial}'
        path.write_bytes(data)
        result.append(sdk.InputSpec(('sdk', 'native', 'target')[i], str(path),
                                    len(data), hashlib.sha256(data).hexdigest(), codec,
                                    len(prefix), b'MARKER:\n' if i == 0 else b''))
    return result

try:
    # 1. Ten indexed files, exact sizes, 50478 shared bound
    try:
        assert len(SELECTORS) == 10
        assert sum(s[2] for s in SELECTORS) == 50478
        payloads = {}
        sdk_entries, target_entries = [], []
        for i, (inp, path, size) in enumerate(SELECTORS):
            data = (f'{i}:' + 'A' * (size - len(f'{i}:'))).encode()
            assert len(data) == size and data.decode('utf-8').isprintable()
            payloads[(inp, path)] = data
            (sdk_entries if inp == 'sdk' else target_entries).append((path, data))
        specs = make_specs(sdk_entries, [('unselected-native', b'native-not-selected\n')], target_entries)
        selectors = [sdk.TextSelector(*row) for row in SELECTORS]
        helper.serial += 1
        out = helper.root / f'sel-{helper.serial}'
        doc = sdk.inventory(specs, out, selectors=selectors, selected_total_bytes=50478)
        assert doc['ok'], doc
        assert doc['mode'] == 'SELECTEDTEXT'
        assert doc['totals']['selected_bytes'] == 50478
        rows = [json.loads(x) for x in (out / 'members.jsonl').read_text().splitlines()]
        selected = [r for r in rows if r['selected']]
        assert len(selected) == 10
        names = []
        for r in selected:
            key = (r['input'], r['canonical_name'])
            data = payloads[key]
            assert r['size'] == len(data)
            assert r['raw_name'] == r['canonical_name'] == key[1]
            assert r['output_data_path'].startswith('selected-') and r['output_data_path'].endswith('.txt')
            assert '/' not in r['output_data_path']
            written = (out / r['output_data_path']).read_bytes()
            assert written == data
            assert hashlib.sha256(written).hexdigest() == r['content_sha256']
            assert (out / r['output_data_path']).stat().st_mode & 0o777 == 0o600
            names.append(r['output_data_path'])
        assert names == [f'selected-{i:06d}.txt' for i in range(1, 11)]
        assert not (helper.root / 'unselected-native').exists()
        rec('ten_files_50478_exact_bound', True, {'selected_bytes': 50478, 'files': names})
    except Exception:
        rec('ten_files_50478_exact_bound', False, traceback.format_exc())

    # 2. One byte under shared bound fails closed before success
    try:
        selectors = [sdk.TextSelector(*row) for row in SELECTORS]
        helper.serial += 1
        out = helper.root / f'sel-{helper.serial}'
        # reconstruct specs? previous specs still valid (synthetic files persist)
        doc = sdk.inventory(specs, out, selectors=selectors, selected_total_bytes=50477)
        assert not doc['ok'] and 'selected total' in doc['error']
        rec('shared_bound_one_byte_under_fails', True, doc['error'][:120])
    except Exception:
        rec('shared_bound_one_byte_under_fails', False, traceback.format_exc())

    # 3. Literal/noncanonical selectors rejected, no inputs opened (inputs empty)
    try:
        n = 0
        for path in ('', '.', './a', 'a/', 'a//b', 'a/./b', '../a', 'a/../b', '/a',
                     'C:/a', 'a\\b', 'a*', 'a?', 'a[0]', 'a\n', 'foo*bar'):
            helper.serial += 1
            out = helper.root / f'sel-{helper.serial}'
            doc = sdk.inventory(helper.specs(), out, selectors=[sdk.TextSelector('sdk', path, 1)], selected_total_bytes=1)
            assert not doc['ok'], path
            assert doc['inputs'] == [], path
            n += 1
        rec('literal_selectors_rejected', True, n)
    except Exception:
        rec('literal_selectors_rejected', False, traceback.format_exc())

    # 4. NUL/binary rejected; no selected-*.txt written
    try:
        details = []
        for data in (b'a\x00b', b'\xff', b'\x7fELF', b'\x89PNG\r\n\x1a\n'):
            specs2 = helper.specs(tar_bytes([('a', data)]))
            helper.serial += 1
            out = helper.root / f'sel-{helper.serial}'
            doc = sdk.inventory(specs2, out, selectors=[sdk.TextSelector('sdk', 'a', len(data))],
                                selected_total_bytes=len(data))
            assert not doc['ok']
            assert list(out.glob('selected-*.txt')) == []
            details.append(doc['error'].split(':')[0])
        rec('nul_binary_rejected_no_write', True, details)
    except Exception:
        rec('nul_binary_rejected_no_write', False, traceback.format_exc())

    # 5. Selected symlink never follows sentinel; no data file
    try:
        sentinel = helper.root / 'SENTINEL'
        sentinel.write_text('NEVER OPEN')
        ti = tarfile.TarInfo('chosen'); ti.type = tarfile.SYMTYPE; ti.linkname = str(sentinel)
        specs2 = helper.specs(tar_bytes([('a', b'hello'), ti]))
        original = os.open
        def guard(path, *args, **kwargs):
            if os.fspath(path) == str(sentinel):
                raise AssertionError('link target opened')
            return original(path, *args, **kwargs)
        helper.serial += 1
        out = helper.root / f'sel-{helper.serial}'
        with mock.patch.object(os, 'open', side_effect=guard):
            doc = sdk.inventory(specs2, out, selectors=[sdk.TextSelector('sdk', 'chosen', 0)],
                                selected_total_bytes=0)
        assert not doc['ok']
        assert 'link target opened' not in (doc.get('error') or '')
        assert list(out.glob('selected-*.txt')) == []
        rec('selected_symlink_never_followed', True, doc['error'][:160])
    except Exception:
        rec('selected_symlink_never_followed', False, traceback.format_exc())

    # 6. Output write safety: generated name, exclusive create
    try:
        helper.serial += 1
        out = helper.root / f'sel-{helper.serial}'
        # First success writes selected-000001.txt
        specs2 = helper.specs(tar_bytes([('a', b'hello')]))
        doc = sdk.inventory(specs2, out, selectors=[sdk.TextSelector('sdk', 'a', 5)], selected_total_bytes=5)
        assert doc['ok']
        first = out / 'selected-000001.txt'
        assert first.read_bytes() == b'hello'
        try:
            sdk.inventory(specs2, out, selectors=[sdk.TextSelector('sdk', 'a', 5)], selected_total_bytes=5)
            raise AssertionError('existing output dir should fail freshness')
        except OSError as e:
            reuse = type(e).__name__
        # Polluted generated name as symlink must not be followed/overwritten
        polluted = helper.root / 'polluted'; polluted.mkdir()
        sentinel = helper.root / 'sent-out'; sentinel.write_bytes(b'sentinel')
        (polluted / 'selected-000001.txt').symlink_to(sentinel)
        fd = sdk.directory_fd(polluted)
        try:
            doc3 = sdk.inventory(specs2, polluted, output_fd=fd, selectors=[sdk.TextSelector('sdk', 'a', 5)], selected_total_bytes=5)
        finally:
            os.close(fd)
        assert not doc3['ok']
        assert sentinel.read_bytes() == b'sentinel'
        rec('output_generated_name_and_freshness', True, {'reuse': reuse, 'polluted_ok': doc3['ok']})
    except Exception:
        rec('output_generated_name_and_freshness', False, traceback.format_exc())

    # 7. Proposed command: parse only, do not open SDK paths or launch
    try:
        raw = COMMAND.read_text()
        assert hashlib.sha256(raw.encode()).hexdigest() == '4856e812ece17229f0872f22ae66921bca78c80fb97fe9ae465c5dd3749963d7'
        # strip comments and reconstruct argv
        line = ' '.join(ln.rstrip('\\').strip() for ln in raw.splitlines() if not ln.startswith('#') and ln.strip())
        argv = shlex.split(line)
        assert argv[0] == '/usr/bin/python3' and '-I' in argv and '-B' in argv
        script = argv[argv.index('-B') + 1]
        assert script.endswith('isolate_sdk_inventory.py')
        args = argv[argv.index(script) + 1:]
        parsed = sdk.production_arguments(args)
        assert parsed.output_dir.endswith('inspection-selected-text-PENDING-REVIEW')
        assert 'inspection-metadata' not in parsed.output_dir
        assert parsed.selected_total_bytes == 50478
        assert len(parsed.selectors) == 10
        rows = [(s.input, s.path, s.size) for s in parsed.selectors]
        assert rows == SELECTORS
        mapped = sdk.validate_selectors(parsed.selectors, parsed.selected_total_bytes)
        assert len(mapped) == 10
        assert all(sdk.canonical(p) == p for _, p, _ in SELECTORS)
        rec('literal_command_parse_no_open', True, {
            'output_dir': parsed.output_dir,
            'n': len(parsed.selectors),
            'total': parsed.selected_total_bytes,
            'sdk': sum(1 for s in parsed.selectors if s.input == 'sdk'),
            'target': sum(1 for s in parsed.selectors if s.input == 'target'),
            'native': sum(1 for s in parsed.selectors if s.input == 'native'),
        })
    except Exception:
        rec('literal_command_parse_no_open', False, traceback.format_exc())

    # 8. Launcher isolation literals preserved
    try:
        src = Path('/workspace/lg-tv/tooling/isolate_sdk_inventory.py').read_text()
        assert 'stdin=subprocess.DEVNULL' in src
        assert 'def _normalize_stdio' in src
        assert 'inherited descriptor survived cleanup' in src
        assert 'pass_fds=' in src
        assert 'TextSelector' in src
        rec('launcher_fd_stdio_literals_kept', True, 'ok')
    except Exception:
        rec('launcher_fd_stdio_literals_kept', False, traceback.format_exc())

    # 9. Hashes and prior reviews
    try:
        def sha(p):
            return hashlib.sha256(Path(p).read_bytes()).hexdigest()
        checks = {
            'reader': sha('/workspace/lg-tv/tooling/sdk_inventory_phase.py') == '77922ceb9757797055a42feeebc7e1da702bbca3c0f677fb87a00f58f3b048cf',
            'launcher': sha('/workspace/lg-tv/tooling/isolate_sdk_inventory.py') == 'c4befa0c75267bb99e804076eda54d400edeb651151d61ea5112a4e3fd09387a',
            'tests': sha('/workspace/lg-tv/tooling/tests/test_sdk_text_selector.py') == '537c33d6b8783b44e906abe5c3e071ffae4b3f4c60ed8cc5e0c6dc7a2860355b',
            'command': sha(str(COMMAND)) == '4856e812ece17229f0872f22ae66921bca78c80fb97fe9ae465c5dd3749963d7',
            'link_review': sha('/workspace/lg-tv/tooling/review/sdk-link-metadata-independent-review.md') == '95b21beea2373b03af8eeee2cfd3f716df8efa4c95e82f13b99559c6a05818d5',
            'utf8_review': sha('/workspace/lg-tv/tooling/review/sdk-utf8-fix-independent-review.md') == '13ba1ab83e232c67b69c4984b6145014631603199af2db6e958024b15beb1ebc',
            'stdio_review': sha('/workspace/lg-tv/tooling/review/sdk-stdio-fix-independent-review.md') == '8ff151080819e2f6814dbeeb88f2bbc7551ba59c0dbe491234e73842adc011dd',
            'fd_review': sha('/workspace/lg-tv/tooling/review/sdk-fd-fix-independent-review.md') == '2acda00ef7d41373f5ad2fcb9173c9f18a04cfd42f932d69809219c990e7312b',
            'v1_review': sha('/workspace/lg-tv/tooling/review/sdk-inventory-independent-review.md') == '57ac2f23882d603db7304a4ea7dd95c2579fa6f2c8e213535f20aefb67d5edb4',
            'before_reader': sha('/workspace/lg-tv/tooling/review/sdk-text-selector-2026-11-08/before/sdk_inventory_phase.py') == 'cecbb2ac06755100d414852b91dccf8527b05321b34a96da3e0eda86b59c16c1',
            'before_launcher': sha('/workspace/lg-tv/tooling/review/sdk-text-selector-2026-11-08/before/isolate_sdk_inventory.py') == '2a6638e3439748a6dc4fb7237a03c3d05521685746df5315683c861acab9ca52',
            'existing_phase_tests': sha('/workspace/lg-tv/tooling/tests/test_sdk_inventory_phase.py') == '03962a2ca74afbe1446afd9ee87ba9dd6bf6d6cacbc7c24f11f68e93407b5749',
            'existing_link_tests': sha('/workspace/lg-tv/tooling/tests/test_sdk_link_metadata.py') == '1c31fd5d2af306f54c050cc39b62077fb6c1f12ee2e6db536c54d27f79d8ee26',
        }
        rec('hashes_and_prior_reviews', all(checks.values()), checks)
    except Exception:
        rec('hashes_and_prior_reviews', False, traceback.format_exc())

    # 10. Source: generated output names; extractfile only after isreg; no member path writes
    try:
        src = Path('/workspace/lg-tv/tooling/sdk_inventory_phase.py').read_text()
        assert "name = f'selected-{len(found) + 1:06d}.txt'" in src
        assert 'O_EXCL' in src and 'O_NOFOLLOW' in src
        i_reg = src.index("if not member.isreg():")
        i_read = src.index('data = selected_plaintext(tf, member)')
        assert i_reg < i_read
        rec('write_and_read_order_safe', True, 'ok')
    except Exception:
        rec('write_and_read_order_safe', False, traceback.format_exc())

finally:
    helper.tearDown()

outp = Path('/workspace/lg-tv/tooling/review/probes-sdk-text-selector-2026-11-08/probe-results.json')
outp.write_text(json.dumps(results, indent=2))
failed = [r for r in results if not r['passed']]
print('SUMMARY', f'{len(results)-len(failed)}/{len(results)} passed')
if failed:
    for r in failed:
        print('----', r['name'])
        print(str(r['detail'])[:2500])
    raise SystemExit(1)

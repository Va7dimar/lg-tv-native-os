"""Independent synthetic probes for link-metadata policy. No SDK paths."""
import builtins, hashlib, io, json, os, sys, tarfile, tempfile, traceback
from pathlib import Path
from unittest import mock

ROOT = Path('/workspace/lg-tv/tooling')
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT/'tests'))
import sdk_inventory_phase as sdk
from test_sdk_inventory_phase import InventoryTests, tar_bytes

results = []

def rec(name, passed, detail):
    results.append({'name': name, 'passed': bool(passed), 'detail': detail})
    print(('PASS' if passed else 'FAIL'), name)

def link(name, target, kind=tarfile.SYMTYPE):
    ti = tarfile.TarInfo(name)
    ti.type, ti.linkname = kind, target
    return ti

helper = InventoryTests('run_phase')
helper.setUp()

try:
    # 1. Absolute + escaping symlink recorded, sentinel never opened/read/resolved
    try:
        sentinel = helper.root / 'sentinel'
        sentinel.write_text('SYNTHETIC NEVER READ')
        entries = [link('dir/abs', str(sentinel)), link('dir/escape', '../../sentinel'),
                   link('dir/safe', '../file'), link('rel', 'file')]
        specs = helper.specs(tar_bytes(entries))
        orig_open, orig_pread = os.open, os.pread
        def guarded_open(path, *args, **kwargs):
            if os.fspath(path) == str(sentinel):
                raise AssertionError('target opened')
            return orig_open(path, *args, **kwargs)
        def guarded_pread(fd, *args):
            if os.fstat(fd).st_ino == sentinel.stat().st_ino:
                raise AssertionError('target read')
            return orig_pread(fd, *args)
        with mock.patch.object(os, 'open', side_effect=guarded_open), \
             mock.patch.object(os, 'pread', side_effect=guarded_pread), \
             mock.patch.object(builtins, 'open', side_effect=AssertionError('unexpected file read')), \
             mock.patch.object(Path, 'resolve', side_effect=AssertionError('target resolved')):
            doc, out = helper.run_phase(specs)
        assert doc['ok'], doc
        rows = [json.loads(s) for s in (out / 'members.jsonl').read_text().splitlines()]
        classes = [r['link_target_classification'] for r in rows[:4]]
        assert classes == ['absolute', 'out_of_tree', 'relative', 'relative'], classes
        assert rows[0]['decision'] == 'recorded_not_followed_nonextractable'
        assert rows[1]['decision'] == 'recorded_not_followed_nonextractable'
        assert rows[2]['decision'] == 'recorded_not_followed'
        assert all(not r['extractable'] and not r['selected'] for r in rows)
        assert doc['totals']['selected_bytes'] == 0
        assert doc['controls']['extraction_implemented'] is False
        assert not any(hasattr(sdk, n) and callable(getattr(sdk, n))
                       for n in ('extract', 'extract_member', 'extractall'))
        rec('symlink_metadata_no_follow', True, {'classes': classes, 'n': len(rows)})
    except Exception:
        rec('symlink_metadata_no_follow', False, traceback.format_exc())

    # 2. Hardlink absolute/escape fail-closed, later inputs skipped, no member rows
    try:
        details = []
        for target, expect_class in (('/abs', 'absolute'), ('../../escape', 'out_of_tree')):
            doc, out = helper.run_phase(helper.specs(tar_bytes([link('bad', target, tarfile.LNKTYPE)])))
            assert not doc['ok'] and doc['status'] == 'partial'
            assert doc['skipped_inputs'] == ['native', 'target']
            assert (out / 'members.jsonl').read_text() == ''
            recs = doc['rejected_links']
            assert len(recs) == 1
            assert recs[0]['type'] == 'hardlink'
            assert recs[0]['target']['value'] == target
            assert recs[0]['target_classification'] == expect_class
            details.append(expect_class)
        rec('hardlink_fail_closed_skips_later', True, details)
    except Exception:
        rec('hardlink_fail_closed_skips_later', False, traceback.format_exc())

    # 3. Member traversal / absolute / drive / backslash / duplicates still fail
    try:
        n = 0
        for ti in [link('../sym', '/abs'), link('/sym', '/abs'), link('C:/sym', '/abs'),
                   link('dir\\sym', '/abs'), link('sym', ''), link('sym', 'C:/bad'),
                   link('sym', 'dir\\bad')]:
            doc, _ = helper.run_phase(helper.specs(tar_bytes([ti], tarfile.GNU_FORMAT)))
            assert not doc['ok'], repr((ti.name, ti.linkname, doc))
            n += 1
        doc, _ = helper.run_phase(helper.specs(tar_bytes([link('same', '/abs'), link('./same', '../x')])))
        assert not doc['ok']
        rec('unsafe_names_and_malformed_targets_fail_closed', True, {'n': n + 1})
    except Exception:
        rec('unsafe_names_and_malformed_targets_fail_closed', False, traceback.format_exc())

    # 4. Diagnostics bounded / escaped; error does not contain full name/target
    try:
        name = '../' + '\u0100\n\t"<>&' * 1000
        target = '/' + '\u00e9\r\n' * 1000
        doc, out = helper.run_phase(helper.specs(tar_bytes([link(name, target, tarfile.LNKTYPE)])))
        assert not doc['ok']
        recs = doc['rejected_links']
        assert len(recs) == 1
        for key, original in (('name', name), ('target', target)):
            field = recs[0][key]
            assert field['original_bytes'] == len(original.encode('utf-8'))
            assert field['truncated'] is True
            assert len(json.dumps(field['value'], ensure_ascii=True)) - 2 <= 512
        assert len(json.dumps(recs, ensure_ascii=True)) < 2000
        assert name not in doc['error'] and target not in doc['error']
        assert len(doc['error']) < 200
        rec('diagnostics_bounded_and_not_in_error', True, {
            'name_orig': recs[0]['name']['original_bytes'],
            'target_orig': recs[0]['target']['original_bytes'],
            'error_len': len(doc['error']),
        })
    except Exception:
        rec('diagnostics_bounded_and_not_in_error', False, traceback.format_exc())

    # 5. Full strings charge before rejection; truncated diagnostics unused for caps
    try:
        name, target = '\x01' * 90, '/' + '\x02' * 90
        doc, _ = helper.run_phase(helper.specs(tar_bytes([link(name, target, tarfile.LNKTYPE)], tarfile.USTAR_FORMAT)), metadata_bytes=350)
        assert not doc['ok']
        assert 'metadata_bytes' in doc['error']
        assert doc['totals']['metadata_bytes'] == 362
        assert doc['skipped_inputs'] == ['native', 'target']
        assert doc['rejected_links'][0]['name']['truncated']
        rec('full_charge_before_reject_not_truncated_diag', True, 362)
    except Exception:
        rec('full_charge_before_reject_not_truncated_diag', False, traceback.format_exc())

    # 6. Retention cap 4
    try:
        budget = sdk.Budget(sdk.Limits(), __import__('time').monotonic() + 30)
        for _ in range(100):
            budget.reject_link(link('name', '/target'), sdk.InventoryError('unsafe link target'))
        assert len(budget.rejected_links) == 4
        rec('rejected_links_capped_at_4', True, 4)
    except Exception:
        rec('rejected_links_capped_at_4', False, traceback.format_exc())

    # 7. link_safe remains strict nonreuse guard
    try:
        for target in ('/abs', '../../escape'):
            try:
                sdk.link_safe('dir/sym', target, False)
            except sdk.InventoryError:
                pass
            else:
                raise AssertionError('link_safe accepted ' + target)
        sdk.link_safe('dir/sym', '../file', False)  # relative in-tree should pass
        rec('link_safe_still_rejects_unsafe', True, 'ok')
    except Exception:
        rec('link_safe_still_rejects_unsafe', False, traceback.format_exc())

    # 8. Invalid UTF8 symlink target still fail-closed; diagnostic doesn't crash
    try:
        doc, _ = helper.run_phase(helper.specs(tar_bytes([link('sym', 'bad-\udcc4')], tarfile.GNU_FORMAT)))
        assert not doc['ok']
        assert doc['rejected_links']
        rec('invalid_utf8_symlink_target_fail_closed', True, doc['rejected_links'][0]['failed_rule'])
    except Exception:
        rec('invalid_utf8_symlink_target_fail_closed', False, traceback.format_exc())

    # 9. GNU long absolute symlink still recorded (UTF8-boundary class)
    try:
        LONG = 'a' * 99 + '\u0100-suffix'
        raw = tar_bytes([link('sym', '/' + LONG)])
        # use InventoryTests helper with gz default
        doc, out = helper.run_phase(helper.specs(raw))
        assert doc['ok'], doc
        rows = [json.loads(s) for s in (out / 'members.jsonl').read_text().splitlines()]
        assert rows[0]['link_target'] == '/' + LONG
        assert rows[0]['link_target_classification'] == 'absolute'
        assert rows[0]['decision'] == 'recorded_not_followed_nonextractable'
        rec('gnu_long_absolute_symlink_recorded', True, rows[0]['link_target'][:20])
    except Exception:
        rec('gnu_long_absolute_symlink_recorded', False, traceback.format_exc())

    # 10. Assertion-change mapping matches preserved RED suite (9 fails)
    try:
        log = Path('/workspace/lg-tv/tooling/review/sdk-link-metadata-2026-11-08/logs/full-SDK-before-assertion-updates.log').read_text()
        fails = [ln for ln in log.splitlines() if ln.startswith('FAIL:')]
        assert len(fails) == 9, fails
        assert sum('test_links_pax_gnu_longnames_metadata_only' in ln for ln in fails) == 1
        assert sum('test_extended_paths_links_duplicates_and_types_fail_closed' in ln for ln in fails) == 8
        rec('assertion_updates_match_preserved_nine_failures', True, len(fails))
    except Exception:
        rec('assertion_updates_match_preserved_nine_failures', False, traceback.format_exc())

    # 11. Hashes / prior reviews / launcher unchanged
    try:
        def sha(p):
            return hashlib.sha256(Path(p).read_bytes()).hexdigest()
        checks = {
            'reader': sha('/workspace/lg-tv/tooling/sdk_inventory_phase.py') == 'cecbb2ac06755100d414852b91dccf8527b05321b34a96da3e0eda86b59c16c1',
            'launcher': sha('/workspace/lg-tv/tooling/isolate_sdk_inventory.py') == '2a6638e3439748a6dc4fb7237a03c3d05521685746df5315683c861acab9ca52',
            'link_tests': sha('/workspace/lg-tv/tooling/tests/test_sdk_link_metadata.py') == '1c31fd5d2af306f54c050cc39b62077fb6c1f12ee2e6db536c54d27f79d8ee26',
            'phase_tests': sha('/workspace/lg-tv/tooling/tests/test_sdk_inventory_phase.py') == '03962a2ca74afbe1446afd9ee87ba9dd6bf6d6cacbc7c24f11f68e93407b5749',
            'utf8_tests': sha('/workspace/lg-tv/tooling/tests/test_sdk_utf8_boundary.py') == '6278c8353a118a695e5512a1968eeae8c5eb49536dd5335b0091db23703f655e',
            'fd_tests': sha('/workspace/lg-tv/tooling/tests/test_sdk_fd_boundary.py') == 'f0b0e69c9b69b4e2122494b0104a791b108009b15b20dfc7a26d2d951126bd10',
            'stdio_tests': sha('/workspace/lg-tv/tooling/tests/test_sdk_stdio_boundary.py') == '15fe10e33a5c49c3fa879c0e5dda2b56e9f15d77caabcdd3de25f3c253ddf065',
            'review_utf8': sha('/workspace/lg-tv/tooling/review/sdk-utf8-fix-independent-review.md') == '13ba1ab83e232c67b69c4984b6145014631603199af2db6e958024b15beb1ebc',
            'review_stdio': sha('/workspace/lg-tv/tooling/review/sdk-stdio-fix-independent-review.md') == '8ff151080819e2f6814dbeeb88f2bbc7551ba59c0dbe491234e73842adc011dd',
            'review_fd': sha('/workspace/lg-tv/tooling/review/sdk-fd-fix-independent-review.md') == '2acda00ef7d41373f5ad2fcb9173c9f18a04cfd42f932d69809219c990e7312b',
            'review_v1': sha('/workspace/lg-tv/tooling/review/sdk-inventory-independent-review.md') == '57ac2f23882d603db7304a4ea7dd95c2579fa6f2c8e213535f20aefb67d5edb4',
            'before_reader': sha('/workspace/lg-tv/tooling/review/sdk-link-metadata-2026-11-08/before/sdk_inventory_phase.py') == 'e70f683abf7597f16d54f15c1f7e86d10be873dda9b0c6f95d881000c7047ba4',
        }
        rec('hashes_and_prior_reviews', all(checks.values()), checks)
    except Exception:
        rec('hashes_and_prior_reviews', False, traceback.format_exc())

    # 12. Source: no extract API; classification lexical; emit extractable False
    try:
        src = Path('/workspace/lg-tv/tooling/sdk_inventory_phase.py').read_text()
        assert 'extractfile' not in src and '.extract(' not in src
        assert 'readlink' not in src and 'realpath' not in src
        assert "classification = link_classification(name, member.linkname, member.islnk())" in src
        assert 'extractable=False' in src
        rec('no_extractor_or_resolve_in_source', True, 'ok')
    except Exception:
        rec('no_extractor_or_resolve_in_source', False, traceback.format_exc())

finally:
    helper.tearDown()

out = Path('/workspace/lg-tv/tooling/review/probes-sdk-link-metadata-2026-11-08/probe-results.json')
out.write_text(json.dumps(results, indent=2))
failed = [r for r in results if not r['passed']]
print('SUMMARY', f'{len(results)-len(failed)}/{len(results)} passed')
if failed:
    for r in failed:
        print('----', r['name'])
        print(r['detail'][:2000])
    raise SystemExit(1)

"""Independent synthetic UTF-8 adversarial probes. No production SDK paths."""
import gzip, io, json, lzma, os, sys, tarfile, tempfile, time, traceback
from pathlib import Path

ROOT = Path('/workspace/lg-tv/tooling')
sys.path.insert(0, str(ROOT))
import sdk_inventory_phase as sdk

LONG = 'a' * 99 + '\u0100-suffix'
OUT = Path('/workspace/lg-tv/tooling/review/probes-sdk-utf8-fix-2026-11-08')


def archive(entries, fmt=tarfile.GNU_FORMAT):
    raw = io.BytesIO()
    with tarfile.open(fileobj=raw, mode='w', format=fmt,
                      encoding='utf-8', errors='surrogateescape') as tf:
        for e in entries:
            tf.addfile(e)
    return raw.getvalue()


def entry(name='file', link='', kind=tarfile.REGTYPE, **metadata):
    info = tarfile.TarInfo(name)
    info.linkname, info.type = link, kind
    for k, v in metadata.items():
        setattr(info, k, v)
    return info


def parse(raw, codec='gz', **limits):
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


def expect_fail(raw, codec='gz', types=(sdk.InventoryError, UnicodeError)):
    try:
        rows, totals, obs = parse(raw, codec)
    except types as e:
        return type(e).__name__, str(e)[:200]
    raise AssertionError(f'expected fail, got {len(rows)} rows: {rows[:1]}')


results = []

def rec(name, passed, detail):
    results.append({'name': name, 'passed': bool(passed), 'detail': detail})
    print(('PASS' if passed else 'FAIL'), name, detail if not passed or isinstance(detail, (str, int, dict)) else '')


# 1. GNU split name/link/both x gz/xz + 0xc4 assertion + no surrogates in output
try:
    detail = {}
    for codec in ('gz', 'xz'):
        for name, link in ((LONG, ''), ('sym', LONG), (LONG, LONG)):
            ti = entry(name, link, tarfile.SYMTYPE if link else tarfile.REGTYPE)
            raw = archive([ti])
            base = ti.tobuf(format=tarfile.GNU_FORMAT, encoding='utf-8')[-512:]
            if name == LONG:
                assert base[0:100] == b'a' * 99 + b'\xc4', base[0:100]
            if link == LONG:
                assert base[157:257] == b'a' * 99 + b'\xc4'
            rows, totals, obs = parse(raw, codec)
            assert rows[0]['raw_name'] == name
            assert rows[0]['link_target'] == link
            dumped = json.dumps(rows)
            assert not any(0xD800 <= ord(ch) <= 0xDFFF for r in rows for ch in (r['raw_name']+r['link_target']+r['canonical_name']))
            assert obs['integrity_eof'] and obs['tar_eof']
            detail[f'{codec}:{name[:8]}:{link[:8]}'] = {
                'members': totals['members'], 'ok': True
            }
    rec('gnu_split_roundtrip_both_codecs', True, detail)
except Exception as e:
    rec('gnu_split_roundtrip_both_codecs', False, traceback.format_exc())


# 2. Unresolved invalid UTF-8 must fail closed (no rows)
try:
    cases = []
    for codec in ('gz', 'xz'):
        items = [
            entry('safe-\udcc4'),
            entry('sym', 'safe-\udcc4', tarfile.SYMTYPE),
            entry('a' * 101 + '\udcc4'),
            entry('sym', 'a' * 101 + '\udcc4', tarfile.SYMTYPE),
            entry(uname='owner-\udcc4'),
            entry(gname='group-\udcc4'),
        ]
        for ti in items:
            et, msg = expect_fail(archive([ti]), codec)
            cases.append({'codec': codec, 'err': et})
    rec('unresolved_invalid_utf8_fails_closed', True, {'n': len(cases), 'errors': sorted(set(c['err'] for c in cases))})
except Exception as e:
    rec('unresolved_invalid_utf8_fails_closed', False, traceback.format_exc())


# 3. Traversal / absolute / escape / dup / types still reject for GNU+PAX x codecs
try:
    n = 0
    badnames = ('../' + LONG, '/' + LONG, 'C:/' + LONG, 'dir/../' + LONG, 'dir\\' + LONG)
    for codec in ('gz', 'xz'):
        for fmt in (tarfile.GNU_FORMAT, tarfile.PAX_FORMAT):
            members_list = [[entry(name)] for name in badnames]
            members_list += [[entry('sym', target, kind)]
                             for target in ('../../' + LONG, '/' + LONG, 'C:/' + LONG, 'dir\\' + LONG)
                             for kind in (tarfile.SYMTYPE, tarfile.LNKTYPE)]
            members_list += [[entry(LONG), entry('./' + LONG)]]
            members_list += [[entry(LONG, kind=kind)] for kind in (tarfile.CHRTYPE, tarfile.FIFOTYPE, tarfile.GNUTYPE_SPARSE, b'Z')]
            if fmt == tarfile.PAX_FORMAT:
                members_list += [[entry(LONG, pax_headers={'GNU.sparse.map': '0,1', 'GNU.sparse.size': '1'})]]
            for members in members_list:
                et, msg = expect_fail(archive(members, fmt), codec, types=(sdk.InventoryError,))
                assert et == 'InventoryError'
                n += 1
    rec('extended_unsafe_still_inventoryerror', True, {'n': n})
except Exception as e:
    rec('extended_unsafe_still_inventoryerror', False, traceback.format_exc())


# 4. Policy applies to FINAL substituted name: discarded raw field looking like ../ + 0xc4
#    but GNU longname is safe -> must ACCEPT
try:
    # Craft via maintained writer with safe long name; the fixed field will be
    # first 100 bytes of LONG which is 99*'a'+0xc4, not a traversal.
    # Independently craft a member whose *raw* 100-byte name is '../' padded
    # with junk, replaced by GNU longname 'safe-final'.
    # Easier path: write LONG (safe relative) — already accepted.
    # Stronger: manually build GNU longname + header whose name field is b'../'+b'x'*96 + b'\xc4'
    def gnu_long_and_base(final_name, raw_name_bytes):
        assert len(raw_name_bytes) == 100
        bio = io.BytesIO()
        with tarfile.open(fileobj=bio, mode='w', format=tarfile.GNU_FORMAT, encoding='utf-8') as tf:
            tf.addfile(entry(final_name))
        data = bytearray(bio.getvalue())
        # Find the last 512-byte header before EOF blocks (two zero blocks)
        # Structure: longname hdr + padded body + file hdr + two EOF
        # Patch file header name field (offset of last non-zero 512 block)
        # Compute: walk headers.
        off = 0
        last_file_hdr = None
        while off + 512 <= len(data):
            block = data[off:off+512]
            if block == b'\0' * 512:
                break
            typ = bytes(block[156:157])
            last_file_hdr = off
            size = int(block[124:136].split(b'\0')[0] or b'0', 8)
            off += 512 + ((size + 511) // 512 * 512)
        data[last_file_hdr:last_file_hdr+100] = raw_name_bytes
        # Fix checksum
        hdr = bytearray(data[last_file_hdr:last_file_hdr+512])
        hdr[148:156] = b'        '
        chksum = sum(hdr) & 0o777777
        hdr[148:156] = (f'{chksum:06o}\0 ').encode('ascii')
        data[last_file_hdr:last_file_hdr+512] = hdr
        return bytes(data)

    raw = gnu_long_and_base('s' * 120, b'../' + b'x' * 96 + b'\xc4')
    rows, totals, obs = parse(raw, 'gz')
    assert rows[0]['raw_name'] == 's' * 120
    assert rows[0]['canonical_name'] == 's' * 120
    rec('policy_uses_final_not_discarded_raw_traversal_bytes', True, {'len': len(rows[0]['raw_name'])})
except Exception as e:
    rec('policy_uses_final_not_discarded_raw_traversal_bytes', False, traceback.format_exc())


# 5. GNU longname substitutes a traversal path -> still reject
try:
    et, msg = expect_fail(archive([entry('../' + LONG)]), 'gz', types=(sdk.InventoryError,))
    rec('final_gnu_traversal_rejected', True, {'err': et, 'msg': msg})
except Exception as e:
    rec('final_gnu_traversal_rejected', False, traceback.format_exc())


# 6. Patch raw ustar uname to invalid UTF-8 while PAX uname is valid.
#    Charging of raw owners is strict and happens before _apply_pax_info.
try:
    bio = io.BytesIO()
    with tarfile.open(fileobj=bio, mode='w', format=tarfile.PAX_FORMAT, encoding='utf-8') as tf:
        tf.addfile(entry('ok.txt', pax_headers={'uname': 'validowner'}, uname='validowner'))
    data = bytearray(bio.getvalue())
    off = 0
    file_hdr = None
    while off + 512 <= len(data):
        block = data[off:off+512]
        if block == b'\0' * 512:
            break
        typ = bytes(block[156:157])
        file_hdr = off
        size = int(block[124:136].split(b'\0')[0] or b'0', 8)
        off += 512 + ((size + 511) // 512 * 512)
    hdr = bytearray(data[file_hdr:file_hdr+512])
    hdr[265:297] = b'\xc4' + b'\0' * 31
    hdr[148:156] = b'        '
    chksum = sum(hdr) & 0o777777
    hdr[148:156] = (f'{chksum:06o}\0 ').encode('ascii')
    data[file_hdr:file_hdr+512] = hdr
    et, msg = expect_fail(bytes(data), 'gz')
    rec('raw_invalid_uname_rejected_despite_pax', True, {'err': et, 'msg': msg, 'file_hdr': file_hdr})
except Exception as e:
    rec('raw_invalid_uname_rejected_despite_pax', False, traceback.format_exc())

# 6b. Raw invalid NAME + PAX valid path should ACCEPT (intended name substitution)
try:
    bio = io.BytesIO()
    with tarfile.open(fileobj=bio, mode='w', format=tarfile.PAX_FORMAT, encoding='utf-8') as tf:
        tf.addfile(entry('good-final.txt', pax_headers={'path': 'good-final.txt'}))
    data = bytearray(bio.getvalue())
    off = 0
    file_hdr = None
    while off + 512 <= len(data):
        block = data[off:off+512]
        if block == b'\0' * 512:
            break
        file_hdr = off
        size = int(block[124:136].split(b'\0')[0] or b'0', 8)
        off += 512 + ((size + 511) // 512 * 512)
    hdr = bytearray(data[file_hdr:file_hdr+512])
    hdr[0:100] = b'a' * 99 + b'\xc4'
    hdr[148:156] = b'        '
    chksum = sum(hdr) & 0o777777
    hdr[148:156] = (f'{chksum:06o}\0 ').encode('ascii')
    data[file_hdr:file_hdr+512] = hdr
    rows, _, _ = parse(bytes(data), 'gz')
    assert rows[0]['raw_name'] == 'good-final.txt'
    rec('pax_valid_path_replaces_truncated_raw_name', True, rows[0]['raw_name'])
except Exception as e:
    rec('pax_valid_path_replaces_truncated_raw_name', False, traceback.format_exc())


# 7. USTAR prefix with isolated invalid byte should fail closed (joined into name)
try:
    # Write a simple ustar file and patch prefix field with 0xc4 and checksum
    bio = io.BytesIO()
    with tarfile.open(fileobj=bio, mode='w', format=tarfile.USTAR_FORMAT, encoding='utf-8') as tf:
        tf.addfile(entry('plain.txt'))
    data = bytearray(bio.getvalue())
    hdr = bytearray(data[0:512])
    # prefix at 345:500 — put a lone 0xc4
    hdr[345] = 0xc4
    hdr[148:156] = b'        '
    chksum = sum(hdr) & 0o777777
    hdr[148:156] = (f'{chksum:06o}\0 ').encode('ascii')
    data[0:512] = hdr
    et, msg = expect_fail(bytes(data), 'gz')
    rec('ustar_malformed_prefix_fails_closed', True, {'err': et, 'msg': msg})
except Exception as e:
    rec('ustar_malformed_prefix_fails_closed', False, traceback.format_exc())


# 8. Exact GNU metadata budget (name+link)
try:
    expected = 2 * (13 + 512) + 200 + 2 * len(LONG.encode('utf-8'))
    raw = archive([entry(LONG, LONG, tarfile.SYMTYPE)])
    _, totals, _ = parse(raw, 'gz', metadata_bytes=expected, members=3)
    assert totals['metadata_bytes'] == expected
    try:
        parse(raw, 'gz', metadata_bytes=expected - 1)
        raise AssertionError('expected metadata_bytes fail')
    except sdk.InventoryError as e:
        assert 'metadata_bytes' in str(e)
    rec('exact_gnu_metadata_budget', True, {'expected': expected, 'got': totals['metadata_bytes']})
except Exception as e:
    rec('exact_gnu_metadata_budget', False, traceback.format_exc())


# 9. Regular multibyte charges unchanged (name Ā=2, uname é=2, gname ö=2) => 8
#    After fix, uname/gname charged once in _proc_member; name charged raw+resolved.
#    For USTAR short name '\u0100' (2 bytes), raw==resolved so name charged twice? 
#    test says metadata_bytes=8.
#    name '\u0100' = 2 bytes charged in _proc_member + 2 in loop = 4; uname 2; gname 2 = 8.
try:
    raw = archive([entry('\u0100', uname='\u00e9', gname='\u00f6')], tarfile.USTAR_FORMAT)
    _, totals, _ = parse(raw, 'xz', metadata_bytes=8)
    assert totals['metadata_bytes'] == 8
    rec('regular_multibyte_charge', True, totals['metadata_bytes'])
except Exception as e:
    rec('regular_multibyte_charge', False, traceback.format_exc())


# 10. Successful emit never includes surrogate code points; JSON ascii-safe
try:
    rows, _, _ = parse(archive([entry(LONG, LONG, tarfile.SYMTYPE)]), 'gz')
    dumped = json.dumps(rows, ensure_ascii=True)
    assert json.loads(dumped) == rows
    rec('json_roundtrip_no_surrogates', True, rows[0]['raw_name'])
except Exception as e:
    rec('json_roundtrip_no_surrogates', False, traceback.format_exc())


# 11. nts() NUL-terminates names (pre-existing tar semantics, not a UTF8 regression).
#     canonical() still rejects an embedded NUL if one survived into the Unicode string.
try:
    rows, _, _ = parse(archive([entry('ok\x00hidden')]), 'gz')
    assert rows[0]['raw_name'] == 'ok'
    rec('nul_termination_is_preexisting_nts_semantics', True, rows[0]['raw_name'])
except Exception as e:
    rec('nul_termination_is_preexisting_nts_semantics', False, traceback.format_exc())


# 12. Hashes / launcher unchanged / prior reviews immutable
try:
    import hashlib
    def sha(p):
        return hashlib.sha256(Path(p).read_bytes()).hexdigest()
    checks = {
        'reader': sha('/workspace/lg-tv/tooling/sdk_inventory_phase.py') == 'e70f683abf7597f16d54f15c1f7e86d10be873dda9b0c6f95d881000c7047ba4',
        'launcher': sha('/workspace/lg-tv/tooling/isolate_sdk_inventory.py') == '2a6638e3439748a6dc4fb7237a03c3d05521685746df5315683c861acab9ca52',
        'utf8_tests': sha('/workspace/lg-tv/tooling/tests/test_sdk_utf8_boundary.py') == '746defc12bdcfa73f211eaad30ba8e349bb70eda8a40e9ed5bbb9ab12a4c3d58',
        'fd_tests': sha('/workspace/lg-tv/tooling/tests/test_sdk_fd_boundary.py') == 'f0b0e69c9b69b4e2122494b0104a791b108009b15b20dfc7a26d2d951126bd10',
        'stdio_tests': sha('/workspace/lg-tv/tooling/tests/test_sdk_stdio_boundary.py') == '15fe10e33a5c49c3fa879c0e5dda2b56e9f15d77caabcdd3de25f3c253ddf065',
        'orig_tests': sha('/workspace/lg-tv/tooling/tests/test_sdk_inventory_phase.py') == 'aaba6c1cc6fd799c02ea62d2a0a3b8103790af97bd6a4dea7a0c6496d48f0ba0',
        'review_v1': sha('/workspace/lg-tv/tooling/review/sdk-inventory-independent-review.md') == '57ac2f23882d603db7304a4ea7dd95c2579fa6f2c8e213535f20aefb67d5edb4',
        'review_fd': sha('/workspace/lg-tv/tooling/review/sdk-fd-fix-independent-review.md') == '2acda00ef7d41373f5ad2fcb9173c9f18a04cfd42f932d69809219c990e7312b',
        'review_stdio': sha('/workspace/lg-tv/tooling/review/sdk-stdio-fix-independent-review.md') == '8ff151080819e2f6814dbeeb88f2bbc7551ba59c0dbe491234e73842adc011dd',
        'before_reader': sha('/workspace/lg-tv/tooling/review/sdk-utf8-fix-2026-11-08/package/before/sdk_inventory_phase.py') == 'c04fe95faf8346741d18de8cdef4814beb520d47d079d7f1a702997ca026fd7f',
    }
    rec('hashes_and_prior_reviews', all(checks.values()), checks)
except Exception as e:
    rec('hashes_and_prior_reviews', False, traceback.format_exc())


# 13. Source-order: _frombuf hardcodes surrogateescape; final name/link charged strict; policies after
try:
    src = Path('/workspace/lg-tv/tooling/sdk_inventory_phase.py').read_text()
    i_from = src.index("return super()._frombuf(buf, encoding, 'surrogateescape', dircheck=dircheck)")
    i_raw = src.index("budget.text(self.name, self.linkname, errors='surrogateescape')")
    i_owners_raw = src.index("budget.text(self.uname, self.gname)")
    i_final_owners = src.index("member.uname.encode('utf-8', 'strict')")
    i_final_names = src.index("budget.text(member.name, member.linkname)")
    i_canon = src.index("name = canonical(member.name)")
    i_link = src.index("link_safe(name, member.linkname, member.islnk())")
    assert i_from < i_raw < i_final_owners < i_final_names < i_canon < i_link
    # TarFile still opened strict
    assert "encoding='utf-8', errors='strict')" in src
    rec('source_order_surrogate_then_strict_then_policy', True, 'ok')
except Exception as e:
    rec('source_order_surrogate_then_strict_then_policy', False, traceback.format_exc())


out = OUT / 'probe-results.json'
out.write_text(json.dumps(results, indent=2))
failed = [r for r in results if not r['passed']]
print('SUMMARY', f"{len(results)-len(failed)}/{len(results)} passed")
if failed:
    sys.exit(1)

"""Pinned inventory with optional exact plaintext selection via the launcher.

Default mode never emits/hashes member content. TarInfo hooks delegate parsing to
CPython tarfile; the hooks count extension headers and retain its zero boundary.
"""
from __future__ import annotations
import argparse
import hashlib
import json
import lzma
import os
import re
import resource
import stat
import sys
import tarfile
import time
import zlib
from dataclasses import asdict, dataclass

CHUNK = 65536
DISK_FLOOR = 10 * 1024**3
SELECTED_MEMBER_MAX = 16 * 1024**2
SELECTED_TOTAL_MAX = 64 * 1024**2


class InventoryError(Exception):
    pass


@dataclass(frozen=True)
class InputSpec:
    label: str
    path: str
    size: int
    sha256: str
    codec: str
    offset: int = 0
    marker: bytes = b''


@dataclass(frozen=True)
class TextSelector:
    input: str
    path: str
    size: int


def validate_selectors(selectors, selected_total_bytes):
    """Literal trusted configuration only; never normalize a requested path."""
    if type(selected_total_bytes) is not int or not 0 <= selected_total_bytes <= SELECTED_TOTAL_MAX:
        raise InventoryError('invalid selected total bound')
    result, total = {}, 0
    for selector in selectors:
        if not isinstance(selector, TextSelector):
            raise InventoryError('invalid selector')
        if selector.input not in ('sdk', 'native', 'target'):
            raise InventoryError('unknown selector input')
        path = selector.path
        if (not isinstance(path, str) or not path or path == '.' or
                any(c in path for c in '*?[]') or not path.isprintable() or
                canonical(path) != path):
            raise InventoryError('nonliteral/noncanonical selector path')
        if type(selector.size) is not int or not 0 <= selector.size <= SELECTED_MEMBER_MAX:
            raise InventoryError('invalid selected size')
        key = (selector.input, path)
        if key in result:
            raise InventoryError('duplicate selector')
        result[key] = selector
        total += selector.size
        if total > selected_total_bytes:
            raise InventoryError('selected total exceeds shared bound')
    return result


def selected_plaintext(tf, member):
    """Read only a validated regular member, never resolve a link or extract paths.

    Strict UTF8: printable Unicode plus TAB/LF/CR only. In particular NUL,
    C0/C1/DEL, format controls, and other nonprintable code points are rejected.
    """
    data = bytearray()
    with tf.extractfile(member) as source:
        while len(data) < member.size:
            chunk = source.read(min(CHUNK, member.size - len(data)))
            if not chunk:
                raise InventoryError('truncated selected payload')
            data.extend(chunk)
        if source.read(1):
            raise InventoryError('selected payload exceeds indexed size')
    try:
        text = data.decode('utf-8', 'strict')
    except UnicodeError as e:
        raise InventoryError('invalid UTF8 selected plaintext') from e
    if any(c not in '\t\n\r' and not c.isprintable() for c in text):
        raise InventoryError('nonplaintext selected content')
    return data


def write_selected(outfd, name, data):
    disk_check(outfd)
    fd = os.open(name, os.O_WRONLY | os.O_CREAT | os.O_EXCL | os.O_NOFOLLOW,
                 0o600, dir_fd=outfd)
    with os.fdopen(fd, 'wb') as dest:
        dest.write(data)
        dest.flush()
        os.fsync(dest.fileno())


_BASE = '/workspace/lg-tv/sdk-candidates/20191125/assets/'
PRODUCTION_SPECS = (
    InputSpec('sdk', _BASE + 'starfish-sdk-x86_64-ca9v1-toolchain-5.0.0-20191125.sh',
              166821312, '3029c64809fe93e6fe6bfb72ac9de6ec556452a0790feb0f9b23abed409e669b', 'xz', 10820, b'MARKER:\n'),
    InputSpec('native', _BASE + 'native_sysroot_dependencies.tar.gz',
              8017931, 'f97498cc24de8a617be8e842962e30299be034730981ac8da0e216548a92f48a', 'gz'),
    InputSpec('target', _BASE + 'target_sysroot_dependencies.tar.gz',
              323786694, 'b5bbe22da19a9fabea1f24cc1965e5a853e9d2935e9e5bdfcd81d7c83174f39b', 'gz'),
)


@dataclass(frozen=True)
class Limits:
    members: int = 200000
    metadata_bytes: int = 100000000
    logical_bytes: int = 4 * 1024**3
    decoded_bytes: int = 4 * 1024**3
    lzma_memlimit: int = 256 * 1024**2

    def __post_init__(self):
        hard = (200000, 100000000, 4 * 1024**3, 4 * 1024**3, 256 * 1024**2)
        for (name, value), maximum in zip(asdict(self).items(), hard):
            if type(value) is not int or not 0 < value <= maximum:
                raise ValueError('invalid limit: ' + name)


def check_deadline(deadline):
    if time.monotonic() >= deadline:
        raise InventoryError('deadline exceeded')


def signature(st):
    return (st.st_dev, st.st_ino, st.st_size, st.st_mtime_ns, st.st_ctime_ns, st.st_nlink)


def directory_fd(path):
    """Walk every component using directory descriptors, refusing symlinks."""
    path = os.fspath(path)
    if not os.path.isabs(path):
        path = os.path.join(os.getcwd(), path)
    parts = path.split('/')
    if '..' in parts:
        raise OSError('parent components forbidden')
    fd = os.open('/', os.O_RDONLY | os.O_DIRECTORY)
    try:
        for part in parts:
            if part in ('', '.'):
                continue
            new = os.open(part, os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW, dir_fd=fd)
            os.close(fd)
            fd = new
        return fd
    except BaseException:
        os.close(fd)
        raise


def open_regular(path):
    parent, leaf = os.path.split(os.path.abspath(os.fspath(path)))
    fdparent = directory_fd(parent)
    try:
        fd = os.open(leaf, os.O_RDONLY | os.O_NOFOLLOW | os.O_NONBLOCK, dir_fd=fdparent)
    finally:
        os.close(fdparent)
    st = os.fstat(fd)
    if not stat.S_ISREG(st.st_mode):
        os.close(fd)
        raise InventoryError('input not regular')
    return fd, signature(st)


def fresh_output(path):
    parent, leaf = os.path.split(os.path.abspath(os.fspath(path)))
    if not leaf or leaf in ('.', '..'):
        raise OSError('invalid output leaf')
    pfd = directory_fd(parent)
    try:
        os.mkdir(leaf, mode=0o700, dir_fd=pfd)
        fd = os.open(leaf, os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW, dir_fd=pfd)
        if os.fstat(fd).st_ino != os.stat(leaf, dir_fd=pfd, follow_symlinks=False).st_ino:
            os.close(fd)
            raise OSError('output creation race')
        return fd
    finally:
        os.close(pfd)


def disk_check(fd):
    info = os.fstatvfs(fd)
    free = info.f_bavail * info.f_frsize
    if free < DISK_FLOOR:
        raise InventoryError('observed free disk below 10GiB floor (not reserved)')
    return free


def atomic_json(fd, name, value):
    """Publish with link(2) for atomic visibility and no overwrite."""
    disk_check(fd)
    tmp = '.' + name + '.pending'
    raw = (json.dumps(value, ensure_ascii=True, sort_keys=True) + '\n').encode()
    out = os.open(tmp, os.O_WRONLY | os.O_CREAT | os.O_EXCL | os.O_NOFOLLOW, 0o600, dir_fd=fd)
    try:
        with os.fdopen(out, 'wb') as f:
            f.write(raw)
            f.flush()
            os.fsync(f.fileno())
        os.link(tmp, name, src_dir_fd=fd, dst_dir_fd=fd, follow_symlinks=False)
    finally:
        os.unlink(tmp, dir_fd=fd)
    os.fsync(fd)


def diagnostic_text(value):
    """Bound JSON-escaped text to 512 ASCII bytes, counting all original bytes.

    These are dictionary values for JSON serialization, not HTML or paths.
    Never use diagnostic/member strings as output filenames.
    """
    original_bytes = 0
    # Chunked accounting avoids another full-size copy of rejected metadata.
    for start in range(0, len(value), CHUNK):
        chunk = value[start:start + CHUNK]
        try:
            original_bytes += len(chunk.encode('utf-8', 'surrogateescape'))
        except UnicodeError:
            original_bytes += len(chunk.encode('utf-8', 'surrogatepass'))
    prefix, escaped_bytes = [], 0
    for char in value:
        width = len(json.dumps(char, ensure_ascii=True)) - 2
        if escaped_bytes + width > 512:
            break
        prefix.append(char)
        escaped_bytes += width
    truncated = len(prefix) < len(value)
    return dict(value=''.join(prefix), original_bytes=original_bytes, truncated=truncated)


class Budget:
    def __init__(self, limits, deadline):
        self.limits, self.deadline = limits, deadline
        self.rejected_links = []
        self.totals = dict(members=0, metadata_bytes=0, logical_regular_bytes=0,
                           decoded_bytes=0, selected_bytes=0)

    def reject_link(self, member, error):
        if not (member.issym() or member.islnk()) or len(self.rejected_links) >= 4:
            return
        rule = str(error)[:160] if isinstance(error, InventoryError) else type(error).__name__
        # Do not reparse/copy an unbounded target just to diagnose a failure.
        classification = ('invalid_utf8' if 'UTF8' in rule or isinstance(error, UnicodeError) else
                          'invalid' if rule.startswith('unsafe link target:') else
                          'absolute' if member.linkname.startswith('/') else
                          'out_of_tree' if rule == 'unsafe link escape' else 'not_evaluated')
        self.rejected_links.append(dict(name=diagnostic_text(member.name),
            target=diagnostic_text(member.linkname),
            type='symlink' if member.issym() else 'hardlink',
            target_classification=classification, failed_rule=rule))

    def add(self, key, amount):
        check_deadline(self.deadline)
        if amount < 0:
            raise InventoryError('negative size')
        self.totals[key] += amount
        bound = {'logical_regular_bytes': 'logical_bytes'}.get(key, key)
        if self.totals[key] > getattr(self.limits, bound):
            raise InventoryError('limit exceeded: ' + key)

    def text(self, *values, errors='strict'):
        try:
            self.add('metadata_bytes', sum(len(x.encode('utf-8', errors)) for x in values))
        except UnicodeError as e:
            raise InventoryError('invalid UTF8 metadata') from e


class DecodedReader:
    """Forward-only tar file adapter; every decoder-produced byte is charged.

    tarfile may request an entire PAX body; decoder calls remain <=CHUNK. Its
    allocations still rely on the launcher's AS/wall backstop.
    """
    def __init__(self, fd, spec, budget, observation):
        self.fd, self.spec, self.budget, self.obs = fd, spec, budget, observation
        self.rawpos = spec.offset
        self.pos = 0
        self.pending = b''
        self.buffer = b''
        self.done = False
        self.decoder = (lzma.LZMADecompressor(format=lzma.FORMAT_XZ,
                        memlimit=budget.limits.lzma_memlimit) if spec.codec == 'xz'
                        else zlib.decompressobj(16 + zlib.MAX_WBITS))

    def tell(self):
        return self.pos

    def produce(self):
        check_deadline(self.budget.deadline)
        if self.done:
            return b''
        if self.spec.codec == 'xz':
            need = self.decoder.needs_input
        else:
            need = not self.pending
        if need:
            data = os.pread(self.fd, min(CHUNK, self.spec.size - self.rawpos), self.rawpos)
            self.rawpos += len(data)
            self.obs['compressed_bytes_read'] += len(data)
            if not data:
                raise InventoryError('truncated compressed stream')
        else:
            data = self.pending if self.spec.codec == 'gz' else b''
        chunk = self.decoder.decompress(data, max_length=CHUNK)
        self.obs['decoded_bytes'] += len(chunk)
        self.obs['max_decoder_chunk'] = max(self.obs['max_decoder_chunk'], len(chunk))
        self.budget.add('decoded_bytes', len(chunk))
        self.pending = self.decoder.unconsumed_tail if self.spec.codec == 'gz' else b''
        if self.decoder.eof:
            unused = self.decoder.unused_data
            self.obs['compressed_bytes_consumed'] = self.rawpos - self.spec.offset - len(unused)
            if unused or self.rawpos != self.spec.size:
                raise InventoryError('compressed trailing/concatenated bytes')
            self.done = True
            self.obs['integrity_eof'] = True
        return chunk

    def read(self, size):
        if not isinstance(size, int) or size < 0:
            raise InventoryError('unbounded read forbidden')
        result = bytearray()
        while len(result) < size:
            check_deadline(self.budget.deadline)
            if not self.buffer:
                if self.done:
                    break
                self.buffer = self.produce()
                if not self.buffer:
                    continue
            n = min(size - len(result), len(self.buffer))
            result.extend(self.buffer[:n])
            self.buffer = self.buffer[n:]
            self.pos += n
        return bytes(result)

    def seek(self, offset, whence=0):
        if whence != 0 or offset < self.pos:
            raise InventoryError('backward/nonabsolute seek forbidden')
        while self.pos < offset:
            if not self.read(min(CHUNK, offset - self.pos)):
                raise InventoryError('truncated tar payload')
        return self.pos


def canonical(name):
    if not name or '\x00' in name or '\\' in name or name.startswith('/') or re.match(r'^[A-Za-z]:', name):
        raise InventoryError('unsafe path')
    parts = name.split('/')
    if '..' in parts:
        raise InventoryError('unsafe parent path')
    result = '/'.join(p for p in parts if p not in ('', '.'))
    # Conventional root directory headers may be recorded, never extracted.
    return result or '.'


def link_classification(member, target, hard=False):
    """Lexical metadata classification only; never resolve or open a target."""
    if not target:
        raise InventoryError('unsafe link target: empty')
    if '\x00' in target:
        raise InventoryError('unsafe link target: NUL')
    if '\\' in target:
        raise InventoryError('unsafe link target: backslash')
    if re.match(r'^[A-Za-z]:', target):
        raise InventoryError('unsafe link target: drive')
    if target.startswith('/'):
        return 'absolute'
    depth = 0 if hard else len(member.split('/')) - 1
    for part in target.split('/'):
        if part == '..':
            depth -= 1
            if depth < 0:
                return 'out_of_tree'
        elif part not in ('', '.'):
            depth += 1
    return 'relative'


def link_safe(member, target, hard):
    """Strict nonreuse guard: metadata permission MUST NOT authorize extraction.

    Any future extraction MUST reject absolute/out-of-tree targets; this reader
    implements no extractor. Only the metadata symlink branch may classify them.
    """
    classification = link_classification(member, target, hard)
    if classification == 'absolute':
        raise InventoryError('unsafe link target')
    if classification == 'out_of_tree':
        raise InventoryError('unsafe link escape')


def parse_archive(fd, spec, budget, observation, emit, select=None):
    reader = DecodedReader(fd, spec, budget, observation)
    boundary = [None]
    extensions = (tarfile.XHDTYPE, tarfile.XGLTYPE, tarfile.SOLARIS_XHDTYPE,
                  tarfile.GNUTYPE_LONGNAME, tarfile.GNUTYPE_LONGLINK)

    class ObservedInfo(tarfile.TarInfo):
        @classmethod
        def _frombuf(cls, buf, encoding, errors, *, dircheck=True):
            try:
                # GNU fixed fields may end mid-UTF8 before a valid longname/
                # longlink replaces them. Preserve bytes only at this boundary;
                # extension decoding and final resolved metadata remain strict.
                return super()._frombuf(buf, encoding, 'surrogateescape', dircheck=dircheck)
            except tarfile.EOFHeaderError:
                boundary[0] = reader.tell() - len(buf)
                raise
            except tarfile.HeaderError as e:
                # TarFile.next otherwise tolerates malformed later headers.
                raise InventoryError('invalid tar header: ' + str(e)) from e

        def _proc_member(self, tf):
            try:
                budget.add('members', 1)
                budget.text(self.name, self.linkname, errors='surrogateescape')
                budget.text(self.uname, self.gname)
                if self.size < 0:
                    raise InventoryError('negative tar size')
                if self.type == tarfile.GNUTYPE_SPARSE:
                    raise InventoryError('unsupported sparse member')
                if self.type in extensions:
                    # Charge padded extension bodies, even overwritten PAX keys.
                    budget.add('metadata_bytes', (self.size + 511) // 512 * 512)
                return super()._proc_member(tf)
            except (InventoryError, UnicodeError) as e:
                budget.reject_link(self, e)
                raise

    if not hasattr(tarfile.TarInfo, '_frombuf'):
        raise InventoryError('unsupported tarfile hook API; requires reviewed CPython 3.13')
    seen = set()
    with tarfile.open(fileobj=reader, mode='r:', tarinfo=ObservedInfo,
                      stream=True, encoding='utf-8', errors='strict') as tf:
        for member in tf:
            try:
                check_deadline(budget.deadline)
                # Validate final owners too, without charging their fixed fields
                # twice. PAX key/value accounting below charges substitutions.
                try:
                    member.uname.encode('utf-8', 'strict')
                    member.gname.encode('utf-8', 'strict')
                except UnicodeError as e:
                    raise InventoryError('invalid UTF8 metadata') from e
                budget.text(member.name, member.linkname)
                for key, value in member.pax_headers.items():
                    budget.text(key, value)
                if member.sparse is not None or any('sparse' in k.lower() for k in member.pax_headers):
                    raise InventoryError('unsupported sparse metadata')
                name = canonical(member.name)
                if name == '.' and not member.isdir():
                    raise InventoryError('unsafe empty member name')
                if name in seen:
                    raise InventoryError('duplicate canonical name')
                seen.add(name)
                classification = None
                if member.isreg():
                    kind = 'regular'
                    budget.add('logical_regular_bytes', member.size)
                elif member.isdir():
                    kind = 'directory'
                elif member.issym() or member.islnk():
                    kind = 'symlink' if member.issym() else 'hardlink'
                    if member.islnk():
                        link_safe(name, member.linkname, True)
                    classification = link_classification(name, member.linkname, member.islnk())
                else:
                    raise InventoryError('unsupported member type/device')
                if kind != 'regular' and member.size:
                    raise InventoryError('nonregular payload unsupported')
                record = dict(input=spec.label, raw_name=member.name, canonical_name=name,
                          type=kind, size=member.size, link_target=member.linkname,
                          pax_headers=member.pax_headers,
                          decision=('recorded_not_followed_nonextractable' if classification in ('absolute', 'out_of_tree') else
                                    'recorded_not_followed' if kind in ('symlink', 'hardlink') else 'recorded'),
                          link_target_classification=classification, extractable=False,
                          reasons=['metadata_only'] + ([classification + '_target'] if classification in ('absolute', 'out_of_tree') else []), selected=False,
                          nested_archive=name.lower().endswith(('.tar', '.gz', '.xz', '.zip', '.7z', '.bz2', '.tgz')))
                if select is not None:
                    select(tf, member, record)
                emit(record)
            except (InventoryError, UnicodeError) as e:
                budget.reject_link(member, e)
                raise
    if boundary[0] is None:
        raise InventoryError('missing tar zero EOF boundary')
    observation['tar_eof_offset'] = boundary[0]
    observation['compressed_counter_definition'] = 'Read counts include read-ahead; consumed is exact at compression EOF, otherwise unknown/null'
    trailing = 0
    while True:
        chunk = reader.read(CHUNK)
        if not chunk:
            break
        trailing += len(chunk)
        if any(chunk):
            raise InventoryError('nonzero decoded trailing tar data')
    # First zero block was consumed by the maintained parser; require second.
    if trailing < 512 or trailing % 512:
        raise InventoryError('incomplete tar EOF/padding')
    observation['tar_eof'] = True
    observation['decoded_zero_tail_bytes'] = trailing + 512
    if not reader.done:
        raise InventoryError('missing integrity EOF')


def inventory(specs, output_dir, limits=None, *, output_fd=None, deadline=None,
              selectors=(), selected_total_bytes=SELECTED_TOTAL_MAX):
    limits = limits or Limits()
    deadline = time.monotonic() + 120 if deadline is None else deadline
    budget = Budget(limits, deadline)
    outfd = fresh_output(output_dir) if output_fd is None else os.dup(output_fd)
    doc = dict(ok=False, status='failed', mode='SELECTEDTEXT' if selectors else 'METADATAONLY', inputs=[],
               totals=budget.totals, full_hash_bytes=0, error=None,
               members_jsonl='members.jsonl', limits=asdict(limits),
               pin_verifications=[], skipped_inputs=[], rejected_links=budget.rejected_links,
               controls=dict(noexec=False,
                   required_launcher_address_space_bytes=1024**3,
                   enforced_address_space_bytes=(None if resource.getrlimit(resource.RLIMIT_AS)[0] == resource.RLIM_INFINITY else resource.getrlimit(resource.RLIMIT_AS)[0]),
                   hard_rss_limit=False, disk_reserved=False, disk_floor_bytes=DISK_FLOOR,
                   selected_member_policy_bytes=16 * 1024**2,
                   selected_total_policy_bytes=64 * 1024**2,
                   extraction_implemented=False,
                   metadata_definition='Observed header strings + padded extension bodies + resolved name/link/PAX UTF8; conservative repeated charging',
                   raw_name_definition='Maintained parser decoded name before canonicalization, after PAX/GNU substitution',
                   allocation_backstop='Mandatory launcher AS/wall limits; tarfile extended-header allocations precede some semantic checks'))
    opened = []
    log = None
    try:
        requested = validate_selectors(selectors, selected_total_bytes)
        found = set()
        if requested:
            doc['selection'] = dict(selectors=[asdict(s) for s in requested.values()],
                                   shared_bound_bytes=selected_total_bytes,
                                   plaintext_policy='strict UTF8; printable Unicode plus TAB/LF/CR only')
        doc['observed_initial_free_bytes'] = disk_check(outfd)
        check_deadline(deadline)
        if len(specs) != 3 or [s.label for s in specs] != ['sdk', 'native', 'target']:
            raise InventoryError('exactly sdk/native/target required')
        for s in specs:
            verification = dict(label=s.label, path=s.path, expected_size=s.size,
                                expected_sha256=s.sha256, bytes_hashed=0, verified=False,
                                slice_start=s.offset, slice_end=s.size)
            doc['pin_verifications'].append(verification)
            check_deadline(deadline)
            if s.codec not in ('xz', 'gz') or not 0 <= s.offset < s.size:
                raise InventoryError('invalid slice/codec')
            fd, identity = open_regular(s.path)
            opened.append((fd, identity, s))
            if identity[2] != s.size:
                raise InventoryError('input size mismatch')
            h = hashlib.sha256()
            pos = 0
            while pos < s.size:
                check_deadline(deadline)
                chunk = os.pread(fd, min(CHUNK, s.size - pos), pos)
                if not chunk:
                    raise InventoryError('input truncated while hashing')
                h.update(chunk)
                pos += len(chunk)
                doc['full_hash_bytes'] += len(chunk)
                verification['bytes_hashed'] += len(chunk)
            if h.hexdigest() != s.sha256:
                raise InventoryError('input pin mismatch')
            if signature(os.fstat(fd)) != identity:
                raise InventoryError('input mutation during pin')
            if s.marker and (s.offset < len(s.marker) or os.pread(fd, len(s.marker), s.offset - len(s.marker)) != s.marker):
                raise InventoryError('slice marker mismatch')
            magic = b'\xfd7zXZ\x00' if s.codec == 'xz' else b'\x1f\x8b'
            if os.pread(fd, len(magic), s.offset) != magic:
                raise InventoryError('compression signature mismatch')
            verification['verified'] = True
            verification['descriptor_stat'] = dict(zip(('device', 'inode', 'size', 'mtime_ns', 'ctime_ns', 'link_count'), identity))
        # No decoder exists until every full pin, marker, signature is verified.
        logfd = os.open('members.jsonl', os.O_WRONLY | os.O_CREAT | os.O_EXCL | os.O_NOFOLLOW,
                        0o600, dir_fd=outfd)
        log = os.fdopen(logfd, 'w', encoding='utf-8')
        def emit(record):
            check_deadline(deadline)
            disk_check(outfd)
            log.write(json.dumps(record, ensure_ascii=True, separators=(',', ':')) + '\n')
            log.flush()
        def select(tf, member, record):
            key = (record['input'], record['canonical_name'])
            selector = requested.get(key)
            if selector is None:
                return
            if member.name != selector.path:
                raise InventoryError('selected member path alias')
            if not member.isreg():
                raise InventoryError('selected member not regular')
            if member.size != selector.size:
                raise InventoryError('selected size mismatch')
            if key in found:
                raise InventoryError('duplicate selected member')
            if budget.totals['selected_bytes'] + member.size > selected_total_bytes:
                raise InventoryError('selected total exceeds shared bound')
            data = selected_plaintext(tf, member)
            check_deadline(deadline)
            name = f'selected-{len(found) + 1:06d}.txt'
            write_selected(outfd, name, data)
            budget.totals['selected_bytes'] += len(data)
            found.add(key)
            record.update(selected=True, decision='selected_plaintext_data',
                          reasons=['exact_selector_size_and_plaintext_validated'],
                          content_sha256=hashlib.sha256(data).hexdigest(), output_data_path=name)
        for fd, identity, s in opened:
            if signature(os.fstat(fd)) != identity:
                raise InventoryError('input mutation before parsing')
            observation = dict(label=s.label, path=s.path, size=s.size, sha256=s.sha256,
                               slice_start=s.offset, slice_end=s.size,
                               compressed_bytes_read=0, compressed_bytes_consumed=None,
                               decoded_bytes=0, max_decoder_chunk=0,
                               tar_eof=False, integrity_eof=False)
            doc['inputs'].append(observation)
            parse_archive(fd, s, budget, observation, emit, select=select if requested else None)
            if signature(os.fstat(fd)) != identity:
                raise InventoryError('input mutation after parsing')
        for fd, identity, s in opened:
            if signature(os.fstat(fd)) != identity:
                raise InventoryError('input mutation at final check')
        if found != requested.keys():
            raise InventoryError('missing selected member(s): ' + str(len(requested.keys() - found)))
        check_deadline(deadline)
        doc.update(ok=True, status='ok')
    except (Exception, MemoryError) as e:
        doc.update(ok=False, status='partial' if doc['inputs'] else 'failed',
                   error=type(e).__name__ + ': ' + str(e)[:2000])
    finally:
        doc['skipped_inputs'] = [s.label for s in specs if s.label not in {a['label'] for a in doc['inputs']}]
        if log:
            log.close()
        for fd, _, _ in opened:
            os.close(fd)
        try:
            atomic_json(outfd, 'manifest.json', doc)
        finally:
            os.close(outfd)
    return doc


def argument_parser():
    parser = argparse.ArgumentParser(description='Pinned three-input inventory; default METADATAONLY')
    for label in ('sdk', 'native', 'target'):
        parser.add_argument('--' + label, required=True)
    parser.add_argument('--output-dir', required=True)
    parser.add_argument('--select-text', nargs=3, action='append', default=[],
                        metavar=('INPUT', 'EXACT_PATH', 'INDEXED_BYTES'))
    parser.add_argument('--selected-total-bytes')
    return parser


def production_arguments(argv=None):
    args = argument_parser().parse_args(argv)
    for spec in PRODUCTION_SPECS:
        if getattr(args, spec.label) != spec.path:
            raise InventoryError('production input path must equal immutable ' + spec.label + ' path')
    def literal_size(value):
        if not re.fullmatch(r'0|[1-9][0-9]{0,7}', value):
            raise InventoryError('invalid literal selected byte count')
        return int(value)
    if bool(args.select_text) != (args.selected_total_bytes is not None):
        raise InventoryError('selectors require explicit shared selected total, and vice versa')
    args.selectors = [TextSelector(label, path, literal_size(size)) for label, path, size in args.select_text]
    args.selected_total_bytes = (literal_size(args.selected_total_bytes)
                                 if args.selected_total_bytes is not None else SELECTED_TOTAL_MAX)
    validate_selectors(args.selectors, args.selected_total_bytes)
    return args


if __name__ == '__main__':
    print('Use isolate_sdk_inventory.py; direct production worker invocation is disabled.', file=sys.stderr)
    sys.exit(2)

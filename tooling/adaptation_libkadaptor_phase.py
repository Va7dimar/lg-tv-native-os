"""Narrow libkadaptor staging and one-level evidence inventory.

Use isolate_adaptation_phase.py for untrusted inputs. Extended tar headers can
allocate inside tarfile.next() before semantic checks; AS/wall isolation is the
allocation backstop. Archive contents are never executed.
"""
from __future__ import annotations

import argparse
from dataclasses import asdict, dataclass, field
import hashlib
import json
import os
from pathlib import Path
import re
import shutil
import stat
import sys
import tarfile
import time
import zlib

import bounded_archive_inventory as bai

OUTER_ARCHIVE_NAME = "webOS 6.0 KLP_1.0_2.tar.gz"
OUTER_BYTES = 511945894
OUTER_SHA256 = "95894dd81e2bb32fd1ced1eb119698f2e1464e6b9b5b5879ea51528d7d5e8832"
TARGET_MEMBER = "soc/libkadaptor-1.0.0-908.3.tar.gz"
TARGET_SIZE = 123840909
TARGET_SHA256 = "46e7e652bc8f6fc9a57ade3baca9b1300a9e8c1bdc4bcde3cb7675116184bf25"
CHUNK_BYTES = 1024 * 1024

# Independent phase ceilings: this phase does not inherit CORE TWO's binary caps.
CEILINGS = {
    "wall_seconds": 120,
    "address_space_bytes": 1073741824,
    "max_members": 200000,
    "max_pathname_bytes": 100000000,
    "max_phase_expanded_bytes": 4294967296,
    "max_outer_compressed_bytes": 536870912,
    "max_outer_decoded_bytes": 671088640,
    "max_binary_each_bytes": 134217728,
    "max_binary_combined_bytes": 134217728,
    "max_admitted_compressed_bytes": 1073741824,
    "max_selected_text_member_bytes": 16777216,
    "max_selected_combined_bytes": 67108864,
}


class PhaseError(Exception):
    """A failed policy, integrity, or output check."""


class PhaseLimitError(PhaseError):
    """Invalid limits or an exhausted shared budget."""


class PhasePartial(PhaseError):
    """The deadline or a shared semantic ceiling stopped the phase."""


@dataclass(frozen=True)
class PhaseLimits:
    wall_seconds: int = 120
    address_space_bytes: int = 1073741824
    max_members: int = 200000
    max_pathname_bytes: int = 100000000
    max_phase_expanded_bytes: int = 4294967296
    max_outer_compressed_bytes: int = 536870912
    max_outer_decoded_bytes: int = 671088640
    max_binary_each_bytes: int = 134217728
    max_binary_combined_bytes: int = 134217728
    max_admitted_compressed_bytes: int = 1073741824
    max_selected_text_member_bytes: int = 16777216
    max_selected_combined_bytes: int = 67108864
    min_free_disk_bytes: int = 10737418240
    _allow_lower_disk_reserve: bool = field(default=False, repr=False)

    def __post_init__(self):
        for name, ceiling in CEILINGS.items():
            value = getattr(self, name)
            if type(value) is not int or not 1 <= value <= ceiling:
                raise PhaseLimitError(f"{name} must be an integer in 1..{ceiling}")
        if type(self.min_free_disk_bytes) is not int or self.min_free_disk_bytes < 1:
            raise PhaseLimitError("min_free_disk_bytes must be a positive integer")
        if not self._allow_lower_disk_reserve and self.min_free_disk_bytes < bai.HARD_MIN_FREE_DISK_BYTES:
            raise PhaseLimitError("min_free_disk_bytes is below the 10GiB floor")

    @classmethod
    def for_tests(cls, **kwargs):
        return cls(_allow_lower_disk_reserve=True, **kwargs)


@dataclass(frozen=True)
class PhaseSpec:
    outer_bytes: int = OUTER_BYTES
    outer_sha256: str = OUTER_SHA256
    target_size: int = TARGET_SIZE
    target_sha256: str = TARGET_SHA256
    synthetic: bool = False

    def __post_init__(self):
        for name in ("outer_bytes", "target_size"):
            if type(getattr(self, name)) is not int or getattr(self, name) < 1:
                raise PhaseError(f"invalid {name}")
        for name in ("outer_sha256", "target_sha256"):
            if not isinstance(getattr(self, name), str) or not re.fullmatch(r"[0-9a-f]{64}", getattr(self, name)):
                raise PhaseError(f"invalid {name}")
        if not self.synthetic and (self.outer_bytes, self.outer_sha256, self.target_size, self.target_sha256) != (
            OUTER_BYTES, OUTER_SHA256, TARGET_SIZE, TARGET_SHA256
        ):
            raise PhaseError("production pins cannot be changed")

    @classmethod
    def for_tests(cls, **kwargs):
        return cls(synthetic=True, **kwargs)


@dataclass
class PhaseResult:
    ok: bool
    status: str
    document: dict


def load_synthetic_spec(path):
    """Explicit fixture pins only; unknown keys (including retargeting) fail closed."""
    fd, st = bai.open_regular_nofollow(Path(path))
    with os.fdopen(fd, "rb") as src:
        if st.st_size > 16384:
            raise PhaseError("synthetic spec is too large")
        raw = src.read(16385)
    try:
        data = json.loads(raw)
    except (ValueError, UnicodeError) as exc:
        raise PhaseError(f"invalid synthetic spec: {exc}") from exc
    required = {"outer_bytes", "outer_sha256", "target_size", "target_sha256"}
    if not isinstance(data, dict) or not required <= data.keys() or data.keys() - required - {"member"}:
        raise PhaseError("synthetic spec must contain only fixture sizes/hashes and optional pinned member")
    if data.pop("member", TARGET_MEMBER) != TARGET_MEMBER:
        raise PhaseError("synthetic spec cannot change the pinned member path")
    return PhaseSpec.for_tests(**data)


def is_evidence_plaintext_name(canonical):
    if not canonical or bai.is_nested_archive_name(canonical):
        return False
    parts = canonical.lower().split("/")
    base = parts[-1]
    header = base.endswith((".h", ".hpp"))
    if header and (set(parts[:-1]) & {"include", "api", "hardware", "adaptor", "hal", "kadaptor"}
                   or "api" in base):
        return True
    # Directory selectors cover build/config evidence; scripts are never executed.
    names = {"readme", "build", "config", "configs", "license", "licence", "copying",
             "manifest", "makefile", "cmakelists", "kconfig", "defconfig"}
    return any(part.lstrip(".").split(".", 1)[0] in names or
               part.endswith(("defconfig", "kconfig")) for part in parts)


def _document(limits, spec):
    public_limits = asdict(limits)
    public_limits.pop("_allow_lower_disk_reserve")
    return {
        "tool": "adaptation-libkadaptor-phase", "version": "1.0.0",
        "status": "failed", "ok": False, "synthetic_fixture_mode": spec.synthetic,
        "pins": {"outer_name": OUTER_ARCHIVE_NAME, "member": TARGET_MEMBER, **asdict(spec)},
        "limits": public_limits, "errors": [], "copied": [], "inners": [],
        "outer_members": [], "disk_observations": [],
        "totals": dict(member_count=0, pathname_bytes=0, expanded_bytes=0,
                       outer_decoded_bytes=0, binary_copy_bytes=0,
                       selected_text_bytes=0, admitted_compressed_bytes=0),
        "isolation_observation": bai.isolation_observation(),
        "controls": {
            "isolation_entrypoint": "isolate_adaptation_phase.py",
            "isolation_required_for_untrusted_inputs": True,
            "parser_allocates_extended_headers_before_semantic_limits": True,
            "allocation_backstop": "prlimit --as and timeout wall via isolate_adaptation_phase.py; tarfile.next() PAX/GNU allocations precede semantic checks",
            "disk_reserve_check": "free disk observation before phase and before writes; not a reservation",
            "in_process_wall_check": "single deadline for hash + copy + inner; never reset",
            "outer_decoded_regular_files_only": True,
            "noexec_output_demonstrated": False, "selected_file_mode": "0644",
            "selected_mode_is_not_noexec_mount": True,
            "tool_never_executes_archive_content": True, "inner_levels": 1,
        },
    }


class _Phase:
    """State of this one pinned package, with one deadline and shared counters."""
    def __init__(self, output, limits, spec, clock, doc):
        self.output, self.limits, self.spec = output, limits, spec
        self.clock, self.doc = clock, doc
        self.deadline = clock() + limits.wall_seconds
        self.totals = doc["totals"]

    def tick(self):
        if self.clock() >= self.deadline:
            raise PhasePartial("wall_seconds deadline exceeded")

    def disk(self, purpose):
        free = int(shutil.disk_usage(self.output).free)
        self.doc["disk_observations"].append({"purpose": purpose, "free_bytes": free})
        if free < self.limits.min_free_disk_bytes:
            raise PhaseError(f"disk free {free} below min_free_disk_bytes {self.limits.min_free_disk_bytes}")

    def charge(self, key, amount, ceiling):
        if amount < 0 or self.totals[key] + amount > getattr(self.limits, ceiling):
            raise PhasePartial(f"{ceiling} exceeded")
        self.totals[key] += amount

    def consume(self, src, *, writer=None, text=False):
        """Bounded chunks for both unclaimed data and the NUL-permitted binary."""
        total, digest, buffer = 0, hashlib.sha256(), bytearray() if text else None
        while True:
            self.tick()
            chunk = src.read(CHUNK_BYTES)
            self.tick()
            if not chunk:
                break
            total += len(chunk)
            digest.update(chunk)
            if writer is not None:
                self.charge("binary_copy_bytes", len(chunk), "max_binary_combined_bytes")
                self.charge("expanded_bytes", len(chunk), "max_phase_expanded_bytes")
                self.charge("admitted_compressed_bytes", len(chunk), "max_admitted_compressed_bytes")
                self.disk("staged payload write")
                writer.write(chunk)
            if text:
                if total > self.limits.max_selected_text_member_bytes:
                    raise PhasePartial("max_selected_text_member_bytes exceeded")
                buffer.extend(chunk)
        return total, digest.hexdigest(), buffer

    def verify(self, handle, size, expected_hash, label):
        self.tick()
        st = os.fstat(handle.fileno())
        if not stat.S_ISREG(st.st_mode) or st.st_size != size:
            raise PhaseError(f"{label} size mismatch")
        handle.seek(0)
        total, digest, _ = self.consume(handle)
        if total != size or os.fstat(handle.fileno()).st_size != size:
            raise PhaseError(f"{label} size mismatch")
        if digest != expected_hash:
            raise PhaseError(f"{label} hash mismatch")
        handle.seek(0)

    def members(self, handle, records, *, outer):
        """Forward-only policy pass; no extraction or implicit link following."""
        self.tick()
        with bai.open_untrusted_tar_gz(handle) as tf:
            seen = set()
            while True:
                self.tick()
                info = tf.next()
                self.tick()
                if info is None:
                    return
                kind = bai.member_kind(info)
                cost = bai.metadata_byte_cost(info.name or "", info)
                if kind == "metadata":
                    cost += bai.logical_member_size(info)
                self.charge("pathname_bytes", cost, "max_pathname_bytes")
                if kind == "metadata":
                    continue
                self.charge("member_count", 1, "max_members")
                canonical, reasons = bai.canonicalize_member_path(info.name)
                if reasons:
                    raise PhaseError("path policy:" + ",".join(reasons))
                if canonical in seen:
                    raise PhaseError("duplicate_canonical_path:" + canonical)
                seen.add(canonical)
                if kind in {"device", "fifo", "unsupported"}:
                    raise PhaseError("type policy:" + kind)
                if outer and canonical == TARGET_MEMBER:
                    if info.name != TARGET_MEMBER:
                        raise PhaseError("target requires exact raw member name")
                    if kind != "file":
                        raise PhaseError("target type mismatch")
                if kind in {"symlink", "hardlink"}:
                    safe, _, link_reasons = bai.classify_link_target(canonical, info.linkname)
                    if not safe:
                        raise PhaseError("link policy:" + ",".join(link_reasons))
                logical = bai.logical_member_size(info) if kind == "file" else 0
                if kind == "file":
                    if outer:
                        self.charge("outer_decoded_bytes", logical, "max_outer_decoded_bytes")
                    self.charge("expanded_bytes", logical, "max_phase_expanded_bytes")
                record = dict(raw_name=info.name, canonical_name=canonical, type=kind,
                              size=logical, selected=False, selected_output=None,
                              decision="recorded_not_followed" if kind in {"symlink", "hardlink"} else "accepted",
                              link_target=info.linkname or None, reasons=[],
                              sparse=bool(getattr(info, "sparse", None)),
                              nested_archive_not_expanded=bool(not outer and bai.is_nested_archive_name(canonical)))
                records.append(record)
                if kind != "file":
                    continue
                src = tf.extractfile(info)
                if src is None:
                    raise PhaseError("unreadable_member:" + canonical)
                with src:
                    yield info, record, src

    def stage(self, info, src):
        if info.size != self.spec.target_size or bai.logical_member_size(info) != self.spec.target_size:
            raise PhaseError("target size mismatch")
        size = self.spec.target_size
        for ceiling, total in (("max_binary_each_bytes", 0),
                               ("max_binary_combined_bytes", self.totals["binary_copy_bytes"]),
                               ("max_admitted_compressed_bytes", self.totals["admitted_compressed_bytes"]),
                               ("max_phase_expanded_bytes", self.totals["expanded_bytes"])):
            if size + total > getattr(self.limits, ceiling):
                raise PhasePartial(ceiling + " exceeded")
        self.disk("before staging")
        dest = bai.contained_path(self.output, "staged", Path(TARGET_MEMBER).name)
        dest.parent.mkdir(parents=True, exist_ok=True)
        if dest.exists() or dest.is_symlink():
            raise PhaseError("staged output collision")
        flags = os.O_CREAT | os.O_EXCL | os.O_WRONLY | os.O_NOFOLLOW
        created = False
        try:
            fd = os.open(dest, flags, 0o644)
            created = True
            with os.fdopen(fd, "wb") as writer:
                os.fchmod(writer.fileno(), 0o644)
                total, digest, _ = self.consume(src, writer=writer)
                writer.flush()
                os.fsync(writer.fileno())
            if total != size:
                raise PhaseError("target copied size mismatch")
            if digest != self.spec.target_sha256:
                raise PhaseError("target copied hash mismatch")
        except Exception:
            if created:
                dest.unlink(missing_ok=True)
            raise
        copied = dict(member=TARGET_MEMBER, path=str(dest.relative_to(self.output)),
                      bytes=total, sha256=digest, verified_before_inner=False)
        self.doc["copied"].append(copied)
        return dest

    def inner(self, staged):
        fd, _ = bai.open_regular_nofollow(staged)
        with os.fdopen(fd, "rb") as src:
            # Hash and parse through the same opened descriptor, with no reopen.
            self.verify(src, self.spec.target_size, self.spec.target_sha256, "staged")
            self.doc["copied"][0]["verified_before_inner"] = True
            inner = dict(filename=staged.name, status="failed", members=[])
            self.doc["inners"].append(inner)
            for info, record, payload in self.members(src, inner["members"], outer=False):
                want = not record["nested_archive_not_expanded"] and is_evidence_plaintext_name(record["canonical_name"])
                if want and record["size"] > self.limits.max_selected_text_member_bytes:
                    raise PhasePartial("max_selected_text_member_bytes exceeded")
                total, digest, data = self.consume(payload, text=want)
                if total != info.size:
                    raise PhaseError("inner member size mismatch")
                record["sha256"] = digest
                if not want:
                    continue
                if b"\0" in data:
                    record["reasons"].append("not_plaintext")
                    continue
                self.charge("selected_text_bytes", total, "max_selected_combined_bytes")
                self.charge("expanded_bytes", total, "max_phase_expanded_bytes")
                self.tick()
                self.disk("selected evidence write")
                record["selected_output"] = bai._write_selected_file(
                    self.output, staged.name, record["canonical_name"], data)
                record["selected"] = True
            inner["member_count"] = len(inner["members"])
            inner["status"] = "ok"


def _persist(output, doc, phase):
    """Best-effort bounded failure indices also report collisions/disk failures.

    An existing index is deliberately replaced by a failed index. Payload files
    are exclusive-created. If the primary index cannot be written, try a separate
    phase-failed.json inside the output. No write follows an escaping symlink.
    """
    try:
        phase.disk("before index writes")
        phase.tick()
    except (PhaseError, OSError) as exc:
        doc["errors"].append(str(exc))
        doc.update(status="failed", ok=False)
    def markdown():
        return ("# Hardware adaptation phase\n\n"
                f"Status: {doc['status']}\n\nOK: {doc['ok']}\n\n" +
                "\n".join(doc["errors"]) + "\n").encode()

    def target(name):
        path = bai.contained_path(output, name)
        if (output / name).is_symlink():
            raise PhaseError("index symlink collision:" + name)
        return path

    for name, encode in (
        ("phase.md", markdown),
        ("phase.json", lambda: (json.dumps(doc, indent=2) + "\n").encode()),
    ):
        try:
            bai.atomic_write_bytes(target(name), encode())
        except (OSError, PhaseError, bai.PathEscapeError) as exc:
            doc["errors"].append(f"index write {name}: {exc}")
            doc.update(status="failed", ok=False)
    if not doc["ok"]:
        # Re-sync JSON if a Markdown/JSON failure was discovered during persistence.
        try:
            bai.atomic_write_bytes(target("phase.md"), markdown())
        except (OSError, PhaseError, bai.PathEscapeError):
            pass
        for name in ("phase.json", "phase-failed.json"):
            try:
                bai.atomic_write_bytes(target(name), (json.dumps(doc, indent=2) + "\n").encode())
                break
            except (OSError, PhaseError, bai.PathEscapeError):
                continue


def record_failed_phase(output_dir, message):
    """Record CLI/launcher preflight failures when the explicit output permits it."""
    output = Path(output_dir).absolute()
    limits = PhaseLimits()
    doc = _document(limits, PhaseSpec())
    doc["errors"].append(message)
    try:
        if output.is_symlink():
            raise PhaseError("symlink output directory rejected")
        output.mkdir(parents=True, exist_ok=True)
        output = output.resolve()
        phase = _Phase(output, limits, PhaseSpec(), time.monotonic, doc)
        _persist(output, doc, phase)
    except (OSError, PhaseError, bai.PathEscapeError) as exc:
        doc["errors"].append(str(exc))
    return PhaseResult(False, "failed", doc)


def run_adaptation_phase(outer, output_dir, *, spec=None, limits=None, clock=time.monotonic):
    limits, spec = limits or PhaseLimits(), spec or PhaseSpec()
    output = Path(output_dir).absolute()
    doc = _document(limits, spec)
    phase = _Phase(output, limits, spec, clock, doc)
    try:
        if output.is_symlink():
            raise PhaseError("symlink output directory rejected")
        output.mkdir(parents=True, exist_ok=True)
        phase.output = output = output.resolve()
        phase.disk("before phase")
        phase.tick()
        for name in ("phase.json", "phase.md", "phase-failed.json"):
            path = bai.contained_path(output, name)
            if path.exists() or path.is_symlink():
                raise PhaseError("output collision:" + name)
        if not spec.synthetic and Path(outer).name != OUTER_ARCHIVE_NAME:
            raise PhaseError("production outer name mismatch")
        fd, _ = bai.open_regular_nofollow(Path(outer))
        with os.fdopen(fd, "rb") as handle:
            size = os.fstat(handle.fileno()).st_size
            if size > limits.max_outer_compressed_bytes:
                raise PhasePartial("max_outer_compressed_bytes exceeded")
            phase.charge("admitted_compressed_bytes", size, "max_admitted_compressed_bytes")
            phase.verify(handle, spec.outer_bytes, spec.outer_sha256, "outer")
            staged = None
            for info, record, src in phase.members(handle, doc["outer_members"], outer=True):
                if info.name == TARGET_MEMBER:
                    staged = phase.stage(info, src)
                else:
                    total, _, _ = phase.consume(src)
                    if total != info.size:
                        raise PhaseError("outer member size mismatch")
            if staged is None:
                raise PhaseError("missing pinned target")
        phase.inner(staged)
        phase.tick()
        doc.update(status="ok", ok=True)
    except PhasePartial as exc:
        doc["errors"].append(str(exc))
        doc.update(status="partial", ok=False)
    except (PhaseError, bai.InputError, bai.PathEscapeError, OSError,
            tarfile.TarError, EOFError, ValueError, OverflowError, RecursionError, zlib.error) as exc:
        doc["errors"].append(str(exc))
        doc.update(status="failed", ok=False)
    for inner in doc["inners"]:
        if inner["status"] != "ok":
            inner["status"] = doc["status"]
    # The output directory itself must be trustworthy before writing a failure index.
    if output.is_dir() and not output.is_symlink():
        _persist(output, doc, phase)
    return PhaseResult(doc["ok"], doc["status"], doc)


def build_arg_parser():
    parser = argparse.ArgumentParser(description="Pinned one-package hardware adaptation phase")
    parser.add_argument("--outer", required=True)
    parser.add_argument("--output-dir", required=True)
    parser.add_argument("--synthetic-fixture-mode", metavar="SPEC.json")
    return parser


def main(argv=None):
    try:
        args = build_arg_parser().parse_args(argv)
        spec = load_synthetic_spec(args.synthetic_fixture_mode) if args.synthetic_fixture_mode else PhaseSpec()
        result = run_adaptation_phase(args.outer, args.output_dir, spec=spec)
    except SystemExit as exc:
        return exc.code
    except (PhaseError, bai.InputError, OSError) as exc:
        record_failed_phase(args.output_dir, str(exc))
        print(str(exc), file=sys.stderr)
        return 2
    print(json.dumps({"ok": result.ok, "status": result.status,
                      "errors": result.document["errors"]})[:bai.HARD_MAX_STDOUT_BYTES])
    return 0 if result.ok else 1


if __name__ == "__main__":
    sys.exit(main())

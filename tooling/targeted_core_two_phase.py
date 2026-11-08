"""One isolated CORE TWO phase: copy kernel+bootcode binaries, then one inner inventory."""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import shutil
import sys
import tarfile
import time
import zlib
from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Callable, Iterable

import bounded_archive_inventory as bai

KERNEL_MEMBER = "soc/kernel-1.0.0-711..4.tar.gz"
KERNEL_BYTES = 170350960
KERNEL_SHA256 = "110f08578519954be3113108ca461d4190d387c3cbb6e50d648274c9dcaf9962"
BOOTCODE_MEMBER = "soc/bootcode-1.0.0-1099.7.tar.gz"
BOOTCODE_BYTES = 12014324
BOOTCODE_SHA256 = "b88f252cf9ae4f4535e015959916cd87067f0e6cf551ef0f189cdc2f4365e23e"
OUTER_ARCHIVE_NAME = "webOS 6.0 KLP_1.0_2.tar.gz"
OUTER_BYTES = 511945894
OUTER_SHA256 = "95894dd81e2bb32fd1ced1eb119698f2e1464e6b9b5b5879ea51528d7d5e8832"
LIBKADAPTOR_MEMBER = "soc/libkadaptor-1.0.0-908.3.tar.gz"

HARD_MAX_OUTER_COMPRESSED_BYTES = 536870912
HARD_MAX_BINARY_EACH_BYTES = 209715200
HARD_MAX_BINARY_COMBINED_BYTES = 335544320
HARD_MAX_ADMITTED_COMPRESSED_BYTES = 1073741824
HARD_MAX_OUTER_DECODED_BYTES = 671088640
HARD_MAX_PHASE_EXPANDED_BYTES = 4294967296
HARD_MAX_SELECTED_COMBINED_BYTES = 67108864

EVIDENCE_EXACT = {
    "readme",
    "license",
    "licence",
    "copying",
    "manifest",
    "config",
    "board",
    "build",
    "kconfig",
    "defconfig",
    "makefile",
}


@dataclass(frozen=True)
class TargetSpec:
    member: str
    size: int
    sha256: str


CORE_TWO_TARGETS = (
    TargetSpec(KERNEL_MEMBER, KERNEL_BYTES, KERNEL_SHA256),
    TargetSpec(BOOTCODE_MEMBER, BOOTCODE_BYTES, BOOTCODE_SHA256),
)


class PhaseLimitError(Exception):
    pass


class PhaseError(Exception):
    pass


@dataclass
class PhaseLimits:
    max_members: int = bai.HARD_MAX_MEMBERS
    max_pathname_bytes: int = bai.HARD_MAX_PATHNAME_BYTES
    max_selected_text_member_bytes: int = bai.HARD_MAX_SELECTED_TEXT_MEMBER_BYTES
    max_selected_combined_bytes: int = HARD_MAX_SELECTED_COMBINED_BYTES
    min_free_disk_bytes: int = bai.HARD_MIN_FREE_DISK_BYTES
    max_outer_compressed_bytes: int = HARD_MAX_OUTER_COMPRESSED_BYTES
    max_binary_each_bytes: int = HARD_MAX_BINARY_EACH_BYTES
    max_binary_combined_bytes: int = HARD_MAX_BINARY_COMBINED_BYTES
    max_admitted_compressed_bytes: int = HARD_MAX_ADMITTED_COMPRESSED_BYTES
    max_outer_decoded_bytes: int = HARD_MAX_OUTER_DECODED_BYTES
    max_phase_expanded_bytes: int = HARD_MAX_PHASE_EXPANDED_BYTES
    wall_seconds: int = bai.HARD_MAX_WALL_SECONDS
    address_space_bytes: int = bai.HARD_MAX_ADDRESS_SPACE_BYTES
    max_stdout_bytes: int = bai.HARD_MAX_STDOUT_BYTES
    _allow_lower_disk_reserve: bool = field(default=False, repr=False, compare=False)

    def __post_init__(self) -> None:
        maxima = {
            "max_members": bai.HARD_MAX_MEMBERS,
            "max_pathname_bytes": bai.HARD_MAX_PATHNAME_BYTES,
            "max_selected_text_member_bytes": bai.HARD_MAX_SELECTED_TEXT_MEMBER_BYTES,
            "max_selected_combined_bytes": HARD_MAX_SELECTED_COMBINED_BYTES,
            "max_outer_compressed_bytes": HARD_MAX_OUTER_COMPRESSED_BYTES,
            "max_binary_each_bytes": HARD_MAX_BINARY_EACH_BYTES,
            "max_binary_combined_bytes": HARD_MAX_BINARY_COMBINED_BYTES,
            "max_admitted_compressed_bytes": HARD_MAX_ADMITTED_COMPRESSED_BYTES,
            "max_outer_decoded_bytes": HARD_MAX_OUTER_DECODED_BYTES,
            "max_phase_expanded_bytes": HARD_MAX_PHASE_EXPANDED_BYTES,
            "wall_seconds": bai.HARD_MAX_WALL_SECONDS,
            "address_space_bytes": bai.HARD_MAX_ADDRESS_SPACE_BYTES,
            "max_stdout_bytes": bai.HARD_MAX_STDOUT_BYTES,
        }
        for name, hard in maxima.items():
            value = getattr(self, name)
            if not isinstance(value, int) or isinstance(value, bool) or value < 1:
                raise PhaseLimitError(f"{name} must be a positive integer")
            if value > hard:
                raise PhaseLimitError(f"{name} {value} exceeds hard maximum {hard}")
        if not isinstance(self.min_free_disk_bytes, int) or self.min_free_disk_bytes < 1:
            raise PhaseLimitError("min_free_disk_bytes must be a positive integer")
        if (
            self.min_free_disk_bytes < bai.HARD_MIN_FREE_DISK_BYTES
            and not self._allow_lower_disk_reserve
        ):
            raise PhaseLimitError(
                f"min_free_disk_bytes {self.min_free_disk_bytes} is below approved floor "
                f"{bai.HARD_MIN_FREE_DISK_BYTES}"
            )

    @classmethod
    def for_tests(cls, **kwargs) -> "PhaseLimits":
        kwargs["_allow_lower_disk_reserve"] = True
        return cls(**kwargs)


@dataclass
class PhaseSpec:
    outer_name: str = OUTER_ARCHIVE_NAME
    outer_bytes: int = OUTER_BYTES
    outer_sha256: str = OUTER_SHA256
    targets: tuple[TargetSpec, ...] = CORE_TWO_TARGETS
    allow_test_spec: bool = False

    @classmethod
    def core_two(cls) -> "PhaseSpec":
        return cls()

    @classmethod
    def for_tests(cls, **kwargs) -> "PhaseSpec":
        kwargs["allow_test_spec"] = True
        return cls(**kwargs)


@dataclass
class PhaseBudgets:
    members: int = 0
    pathname_bytes: int = 0
    expanded_bytes: int = 0
    selected_text_bytes: int = 0
    outer_decoded_bytes: int = 0
    binary_copy_bytes: int = 0
    admitted_compressed_bytes: int = 0


@dataclass
class PhaseResult:
    ok: bool
    status: str
    document: dict = field(default_factory=dict)


def is_evidence_plaintext_name(canonical: str) -> bool:
    if not canonical:
        return False
    parts = [part for part in canonical.replace("\\", "/").lower().split("/") if part]
    for part in parts:
        name = part.lstrip(".")
        stem = name.rsplit(".", 1)[0] if "." in name and not name.startswith(".") else name
        if "." in name and name.startswith("."):
            stem = name
        candidates = {part, name, stem}
        if "." in part:
            candidates.add(part.rsplit(".", 1)[0])
        for cand in candidates:
            if cand in EVIDENCE_EXACT:
                return True
            if cand.endswith("defconfig") or cand.endswith("kconfig"):
                return True
    return False


def _public_limits(limits: PhaseLimits) -> dict:
    data = asdict(limits)
    data.pop("_allow_lower_disk_reserve", None)
    return data


def _empty_document(limits: PhaseLimits) -> dict:
    return {
        "tool": "targeted-core-two-phase",
        "version": "1.0.0",
        "status": "failed",
        "ok": False,
        "generated_at": datetime.now(timezone.utc).astimezone().isoformat(),
        "limits": _public_limits(limits),
        "copied": [],
        "inners": [],
        "skipped_inputs": [],
        "errors": [],
        "totals": {
            "member_count": 0,
            "pathname_bytes": 0,
            "expanded_bytes": 0,
            "selected_text_bytes": 0,
            "outer_decoded_bytes": 0,
            "binary_copy_bytes": 0,
            "admitted_compressed_bytes": 0,
        },
        "isolation_observation": bai.isolation_observation(),
        "controls": {
            "isolation_entrypoint": "isolate_targeted_phase.py",
            "isolation_required_for_untrusted_inputs": True,
            "parser_allocates_extended_headers_before_semantic_limits": True,
            "allocation_backstop": (
                "prlimit address-space and timeout wall via isolate_targeted_phase.py; "
                "semantic caps do not contain tarfile.next() PAX/GNU allocations"
            ),
            "disk_reserve_check": (
                "observed free bytes before phase and before writes; not a filesystem reservation"
            ),
            "in_process_wall_check": (
                "single phase deadline covering hash, staging, and both inners; no per-package reset"
            ),
            "noexec_output_demonstrated": False,
            "selected_file_mode": "0644",
            "selected_mode_is_not_noexec_mount": True,
            "tool_never_executes_archive_content": True,
            "libkadaptor_in_scope": False,
            "chromium_rescan": False,
        },
    }


def _persist(output_dir: Path, document: dict) -> None:
    output_dir.mkdir(parents=True, exist_ok=True)
    lines = [
        "# CORE TWO targeted phase",
        "",
        f"- status: `{document['status']}`",
        f"- ok: `{document['ok']}`",
        f"- errors: {', '.join(document.get('errors', [])) or '(none)'}",
        f"- copied: {len(document.get('copied', []))}",
        f"- inners: {len(document.get('inners', []))}",
        "",
    ]
    bai.atomic_write_bytes(
        output_dir / "phase.json",
        (json.dumps(document, indent=2) + "\n").encode("utf-8"),
    )
    bai.atomic_write_bytes(output_dir / "phase.md", ("\n".join(lines) + "\n").encode("utf-8"))


def _sync_totals(document: dict, budgets: PhaseBudgets) -> None:
    document["totals"] = {
        "member_count": budgets.members,
        "pathname_bytes": budgets.pathname_bytes,
        "expanded_bytes": budgets.expanded_bytes,
        "selected_text_bytes": budgets.selected_text_bytes,
        "outer_decoded_bytes": budgets.outer_decoded_bytes,
        "binary_copy_bytes": budgets.binary_copy_bytes,
        "admitted_compressed_bytes": budgets.admitted_compressed_bytes,
    }


def _finish(output_dir: Path, document: dict, budgets: PhaseBudgets, status: str) -> PhaseResult:
    document["status"] = status
    document["ok"] = status == "ok"
    _sync_totals(document, budgets)
    _persist(output_dir, document)
    return PhaseResult(document["ok"], document["status"], document)


def _disk_free(path: Path) -> int:
    return int(shutil.disk_usage(path).free)


def _check_disk(path: Path, limits: PhaseLimits, errors: list[str]) -> bool:
    free = _disk_free(path)
    if free < limits.min_free_disk_bytes:
        errors.append(
            f"free_disk {free} is below min_free_disk_bytes {limits.min_free_disk_bytes}"
        )
        return False
    return True


def _timed_out(clock: Callable[[], float], deadline: float) -> bool:
    return clock() > deadline


def _hash_fd(fd: int, clock: Callable[[], float], deadline: float) -> tuple[str | None, str | None]:
    digest = hashlib.sha256()
    os.lseek(fd, 0, os.SEEK_SET)
    while True:
        if _timed_out(clock, deadline):
            return None, "wall_seconds exceeded"
        chunk = os.read(fd, 1024 * 1024)
        if not chunk:
            break
        digest.update(chunk)
    os.lseek(fd, 0, os.SEEK_SET)
    return digest.hexdigest(), None


def _hash_path(path: Path, clock: Callable[[], float], deadline: float) -> tuple[str | None, str | None]:
    fd, _st = bai.open_regular_nofollow(path)
    try:
        return _hash_fd(fd, clock, deadline)
    finally:
        os.close(fd)


def _write_staged(output_dir: Path, basename: str, data: bytes) -> Path:
    staged_root = bai.contained_path(output_dir, "staged")
    dest = bai.contained_path(staged_root, basename)
    dest.parent.mkdir(parents=True, exist_ok=True)
    flags = os.O_CREAT | os.O_EXCL | os.O_WRONLY
    fd = os.open(dest, flags, 0o644)
    with os.fdopen(fd, "wb") as handle:
        handle.write(data)
        handle.flush()
        os.fsync(handle.fileno())
    os.chmod(dest, 0o644)
    return dest


def _consume(src, hasher=None, clock=None, deadline=None) -> tuple[int, bytes, str | None]:
    chunks: list[bytes] = []
    total = 0
    while True:
        if clock is not None and deadline is not None and _timed_out(clock, deadline):
            return total, b"".join(chunks), "wall_seconds exceeded"
        piece = src.read(1024 * 1024)
        if not piece:
            break
        total += len(piece)
        chunks.append(piece)
        if hasher is not None:
            hasher.update(piece)
    return total, b"".join(chunks), None


def run_core_two_phase(
    outer,
    output_dir,
    spec: PhaseSpec | None = None,
    limits: PhaseLimits | None = None,
    clock: Callable[[], float] | None = None,
) -> PhaseResult:
    spec = spec or PhaseSpec.core_two()
    limits = limits or PhaseLimits()
    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    if (output_dir / "phase.json").exists() or (output_dir / "phase.md").exists():
        raise PhaseError(f"phase outputs already exist in {output_dir}")

    clock = clock or time.monotonic
    deadline = clock() + limits.wall_seconds
    budgets = PhaseBudgets()
    document = _empty_document(limits)
    target_by_name = {item.member: item for item in spec.targets}
    found: dict[str, dict] = {}

    if not _check_disk(output_dir, limits, document["errors"]):
        return _finish(output_dir, document, budgets, "failed")
    if _timed_out(clock, deadline):
        document["errors"].append("wall_seconds exceeded")
        return _finish(output_dir, document, budgets, "partial")

    outer = Path(outer)
    try:
        fd, st = bai.open_regular_nofollow(outer)
    except bai.InputError as exc:
        document["errors"].append(str(exc))
        return _finish(output_dir, document, budgets, "failed")

    try:
        if st.st_size != spec.outer_bytes:
            document["errors"].append(
                f"outer size {st.st_size} does not match expected {spec.outer_bytes}"
            )
            return _finish(output_dir, document, budgets, "failed")
        if st.st_size > limits.max_outer_compressed_bytes:
            document["errors"].append("max_outer_compressed_bytes exceeded")
            return _finish(output_dir, document, budgets, "failed")
        expected_copies = sum(item.size for item in spec.targets)
        budgets.admitted_compressed_bytes = st.st_size + expected_copies
        if budgets.admitted_compressed_bytes > limits.max_admitted_compressed_bytes:
            document["errors"].append("max_admitted_compressed_bytes exceeded")
            return _finish(output_dir, document, budgets, "failed")
        digest, wall = _hash_fd(fd, clock, deadline)
        if wall:
            document["errors"].append(wall)
            return _finish(output_dir, document, budgets, "partial")
        if digest != spec.outer_sha256:
            document["errors"].append("outer hash mismatch")
            return _finish(output_dir, document, budgets, "failed")

        fileobj = os.fdopen(os.dup(fd), "rb")
        try:
            tf = bai.open_untrusted_tar_gz(fileobj)
            try:
                seen: set[str] = set()
                while True:
                    if _timed_out(clock, deadline):
                        document["errors"].append("wall_seconds exceeded")
                        return _finish(output_dir, document, budgets, "partial")
                    if budgets.members >= limits.max_members:
                        document["errors"].append("max_members exceeded")
                        return _finish(output_dir, document, budgets, "partial")
                    try:
                        info = tf.next()
                    except (tarfile.TarError, OSError, EOFError, ValueError, zlib.error) as exc:
                        document["errors"].append(f"parse_error:{exc}")
                        return _finish(output_dir, document, budgets, "partial")
                    if info is None:
                        break
                    raw_name = info.name or ""
                    cost = bai.metadata_byte_cost(raw_name, info)
                    if budgets.pathname_bytes + cost > limits.max_pathname_bytes:
                        document["errors"].append("max_pathname_bytes exceeded")
                        return _finish(output_dir, document, budgets, "partial")
                    budgets.pathname_bytes += cost
                    kind = bai.member_kind(info)
                    if kind == "metadata":
                        continue
                    canonical, path_reasons = bai.canonicalize_member_path(raw_name)
                    if path_reasons:
                        document["errors"].append("policy:" + ",".join(path_reasons))
                        return _finish(output_dir, document, budgets, "failed")
                    if canonical in seen:
                        document["errors"].append("duplicate_canonical_path")
                        return _finish(output_dir, document, budgets, "failed")
                    seen.add(canonical)
                    if kind == "device":
                        document["errors"].append("device")
                        return _finish(output_dir, document, budgets, "failed")
                    if kind == "fifo":
                        document["errors"].append("fifo")
                        return _finish(output_dir, document, budgets, "failed")
                    if kind == "unsupported":
                        document["errors"].append("unsupported_type")
                        return _finish(output_dir, document, budgets, "failed")
                    if kind in {"symlink", "hardlink"}:
                        if canonical in target_by_name:
                            document["errors"].append(f"type mismatch for {canonical}")
                            return _finish(output_dir, document, budgets, "failed")
                        safe, _resolved, link_reasons = bai.classify_link_target(
                            canonical, info.linkname
                        )
                        if not safe:
                            document["errors"].append("policy:" + ",".join(link_reasons))
                            return _finish(output_dir, document, budgets, "failed")
                        budgets.members += 1
                        continue

                    logical = bai.logical_member_size(info) if kind == "file" else 0
                    if kind == "file":
                        if budgets.outer_decoded_bytes + logical > limits.max_outer_decoded_bytes:
                            document["errors"].append("outer_decoded budget exceeded")
                            return _finish(output_dir, document, budgets, "partial")
                        if budgets.expanded_bytes + logical > limits.max_phase_expanded_bytes:
                            document["errors"].append("max_phase_expanded_bytes exceeded")
                            return _finish(output_dir, document, budgets, "partial")
                        budgets.outer_decoded_bytes += logical
                        budgets.expanded_bytes += logical

                    budgets.members += 1
                    src = tf.extractfile(info) if kind == "file" else None
                    if kind != "file":
                        continue
                    if src is None:
                        document["errors"].append(f"unreadable_member:{raw_name}")
                        return _finish(output_dir, document, budgets, "partial")

                    hasher = hashlib.sha256()
                    if canonical in target_by_name:
                        target = target_by_name[canonical]
                        if canonical in found:
                            document["errors"].append(f"duplicate target {canonical}")
                            return _finish(output_dir, document, budgets, "failed")
                        if info.size != target.size or logical != target.size:
                            document["errors"].append(f"size mismatch for {canonical}")
                            return _finish(output_dir, document, budgets, "failed")
                        if logical > limits.max_binary_each_bytes:
                            document["errors"].append("max_binary_each_bytes exceeded")
                            return _finish(output_dir, document, budgets, "failed")
                        if budgets.binary_copy_bytes + logical > limits.max_binary_combined_bytes:
                            document["errors"].append("max_binary_combined_bytes exceeded")
                            return _finish(output_dir, document, budgets, "failed")
                        if budgets.expanded_bytes + logical > limits.max_phase_expanded_bytes:
                            document["errors"].append("max_phase_expanded_bytes exceeded")
                            return _finish(output_dir, document, budgets, "partial")
                        if not _check_disk(output_dir, limits, document["errors"]):
                            return _finish(output_dir, document, budgets, "failed")
                        total, payload, wall = _consume(src, hasher, clock, deadline)
                        if wall:
                            document["errors"].append(wall)
                            return _finish(output_dir, document, budgets, "partial")
                        digest = hasher.hexdigest()
                        if total != target.size or digest != target.sha256:
                            document["errors"].append(f"hash mismatch for {canonical}")
                            return _finish(output_dir, document, budgets, "failed")
                        staged = _write_staged(output_dir, Path(canonical).name, payload)
                        budgets.binary_copy_bytes += total
                        budgets.expanded_bytes += total
                        found[canonical] = {
                            "member": canonical,
                            "path": str(staged.relative_to(output_dir.resolve())),
                            "bytes": total,
                            "sha256": digest,
                            "verified_before_inner": False,
                        }
                    else:
                        _consume(src, None, clock, deadline)
            finally:
                tf.close()
        finally:
            fileobj.close()
    finally:
        os.close(fd)

    missing = [item.member for item in spec.targets if item.member not in found]
    if missing:
        document["errors"].append("missing targets: " + ", ".join(missing))
        return _finish(output_dir, document, budgets, "failed")
    document["copied"] = [found[item.member] for item in spec.targets]

    if not _check_disk(output_dir, limits, document["errors"]):
        return _finish(output_dir, document, budgets, "failed")

    for item in spec.targets:
        if _timed_out(clock, deadline):
            document["errors"].append("wall_seconds exceeded")
            document["skipped_inputs"].append(item.member)
            return _finish(output_dir, document, budgets, "partial")
        staged = output_dir / found[item.member]["path"]
        digest, wall = _hash_path(staged, clock, deadline)
        if wall:
            document["errors"].append(wall)
            return _finish(output_dir, document, budgets, "partial")
        if digest != item.sha256:
            document["errors"].append(f"staged hash mismatch before inner read: {item.member}")
            return _finish(output_dir, document, budgets, "failed")
        found[item.member]["verified_before_inner"] = True
        inner, errors, inner_status = _inventory_inner(
            staged, output_dir, limits, budgets, clock, deadline
        )
        document["inners"].append(inner)
        document["errors"].extend(errors)
        if inner_status != "ok":
            return _finish(output_dir, document, budgets, inner_status)

    document["copied"] = [found[item.member] for item in spec.targets]
    return _finish(output_dir, document, budgets, "ok")


def _inventory_inner(
    staged: Path,
    output_dir: Path,
    limits: PhaseLimits,
    budgets: PhaseBudgets,
    clock: Callable[[], float],
    deadline: float,
) -> tuple[dict, list[str], str]:
    errors: list[str] = []
    members: list[dict] = []
    archive = {
        "filename": staged.name,
        "status": "ok",
        "error": None,
        "member_count": 0,
        "members": members,
    }
    fd, _st = bai.open_regular_nofollow(staged)
    fileobj = os.fdopen(fd, "rb")
    try:
        tf = bai.open_untrusted_tar_gz(fileobj)
        try:
            seen: set[str] = set()
            while True:
                if _timed_out(clock, deadline):
                    errors.append("wall_seconds exceeded")
                    archive["status"] = "partial"
                    archive["error"] = "wall_seconds"
                    return archive, errors, "partial"
                if budgets.members >= limits.max_members:
                    errors.append("max_members exceeded")
                    archive["status"] = "partial"
                    archive["error"] = "max_members"
                    return archive, errors, "partial"
                try:
                    info = tf.next()
                except (tarfile.TarError, OSError, EOFError, ValueError, zlib.error) as exc:
                    errors.append(f"parse_error:{exc}")
                    archive["status"] = "partial"
                    archive["error"] = "parse_error"
                    return archive, errors, "partial"
                if info is None:
                    break
                raw_name = info.name or ""
                cost = bai.metadata_byte_cost(raw_name, info)
                if budgets.pathname_bytes + cost > limits.max_pathname_bytes:
                    errors.append("max_pathname_bytes exceeded")
                    archive["status"] = "partial"
                    return archive, errors, "partial"
                budgets.pathname_bytes += cost
                kind = bai.member_kind(info)
                if kind == "metadata":
                    continue
                canonical, path_reasons = bai.canonicalize_member_path(raw_name)
                reasons = list(path_reasons)
                decision = "accepted"
                if path_reasons:
                    decision = "rejected"
                    archive["status"] = "failed"
                    errors.append("policy:" + ",".join(path_reasons))
                    return archive, errors, "failed"
                if canonical in seen:
                    errors.append("duplicate_canonical_path")
                    return archive, errors, "failed"
                seen.add(canonical)
                if kind in {"device", "fifo", "unsupported"}:
                    errors.append(kind)
                    return archive, errors, "failed"
                if kind in {"symlink", "hardlink"}:
                    safe, _resolved, link_reasons = bai.classify_link_target(
                        canonical or "", info.linkname
                    )
                    if not safe:
                        errors.append("policy:" + ",".join(link_reasons))
                        return archive, errors, "failed"
                    decision = "recorded_not_followed"
                logical = bai.logical_member_size(info) if kind == "file" else 0
                nested = bool(canonical and bai.is_nested_archive_name(canonical))
                if kind == "file":
                    if budgets.expanded_bytes + logical > limits.max_phase_expanded_bytes:
                        errors.append("max_phase_expanded_bytes exceeded")
                        archive["status"] = "partial"
                        members.append(
                            {
                                "canonical_name": canonical,
                                "type": kind,
                                "size": logical,
                                "decision": decision,
                                "reasons": reasons + ["max_phase_expanded_bytes"],
                                "selected": False,
                                "sparse": bool(getattr(info, "sparse", None)),
                                "nested_archive_not_expanded": nested,
                            }
                        )
                        return archive, errors, "partial"
                    budgets.expanded_bytes += logical
                record = {
                    "canonical_name": canonical,
                    "raw_name": raw_name,
                    "type": kind,
                    "size": logical if kind == "file" else int(info.size or 0),
                    "decision": decision,
                    "reasons": reasons,
                    "selected": False,
                    "selected_output": None,
                    "sparse": bool(getattr(info, "sparse", None)),
                    "nested_archive_not_expanded": nested,
                }
                budgets.members += 1
                src = tf.extractfile(info) if kind == "file" else None
                if kind == "file" and src is not None:
                    want = (
                        decision == "accepted"
                        and not nested
                        and is_evidence_plaintext_name(canonical)
                    )
                    if want and logical > limits.max_selected_text_member_bytes:
                        want = False
                        record["reasons"].append("selected_oversize")
                    if want:
                        buf = src.read(limits.max_selected_text_member_bytes + 1)
                        extra, _rest, wall = _consume(src, None, clock, deadline)
                        if wall:
                            errors.append(wall)
                            return archive, errors, "partial"
                        if len(buf) > limits.max_selected_text_member_bytes:
                            record["reasons"].append("selected_oversize")
                        elif b"\x00" in buf:
                            record["reasons"].append("not_plaintext")
                        elif (
                            budgets.selected_text_bytes + len(buf)
                            > limits.max_selected_combined_bytes
                        ):
                            errors.append("max_selected_combined_bytes exceeded")
                            return archive, errors, "partial"
                        else:
                            if not _check_disk(output_dir, limits, errors):
                                return archive, errors, "failed"
                            if budgets.expanded_bytes + len(buf) > limits.max_phase_expanded_bytes:
                                errors.append("max_phase_expanded_bytes exceeded")
                                return archive, errors, "partial"
                            selected_output = bai._write_selected_file(
                                output_dir, staged.name, canonical, buf
                            )
                            record["selected"] = True
                            record["selected_output"] = selected_output
                            budgets.selected_text_bytes += len(buf)
                            budgets.expanded_bytes += len(buf)
                    else:
                        _consume(src, None, clock, deadline)
                members.append(record)
        finally:
            tf.close()
    finally:
        fileobj.close()
    archive["member_count"] = len(members)
    archive["members"] = members
    return archive, errors, archive["status"]


def build_arg_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="CORE TWO kernel/bootcode phase")
    parser.add_argument("--outer", required=True)
    parser.add_argument("--output-dir", required=True)
    parser.add_argument("--expected-outer-bytes", type=int, default=OUTER_BYTES)
    parser.add_argument("--expected-outer-sha256", default=OUTER_SHA256)
    parser.add_argument("--test-target", action="append", default=[])
    parser.add_argument("--allow-test-spec", action="store_true")
    parser.add_argument("--min-free-disk-bytes", type=int)
    parser.add_argument("--wall-seconds", type=int)
    return parser


def spec_from_args(args: argparse.Namespace) -> PhaseSpec:
    if args.allow_test_spec:
        targets = []
        for item in args.test_target:
            member, size_s, sha = item.split(":", 2)
            targets.append(TargetSpec(member, int(size_s), sha))
        if not targets:
            targets = list(CORE_TWO_TARGETS)
        return PhaseSpec.for_tests(
            outer_name=Path(args.outer).name,
            outer_bytes=args.expected_outer_bytes,
            outer_sha256=args.expected_outer_sha256,
            targets=tuple(targets),
        )
    return PhaseSpec(
        outer_name=OUTER_ARCHIVE_NAME,
        outer_bytes=args.expected_outer_bytes,
        outer_sha256=args.expected_outer_sha256,
        targets=CORE_TWO_TARGETS,
    )


def limits_from_args(args: argparse.Namespace) -> PhaseLimits:
    kwargs = {}
    if args.min_free_disk_bytes is not None:
        kwargs["min_free_disk_bytes"] = args.min_free_disk_bytes
    if args.wall_seconds is not None:
        kwargs["wall_seconds"] = args.wall_seconds
    return PhaseLimits(**kwargs)


def main(argv: list[str] | None = None) -> int:
    argv = list(sys.argv[1:] if argv is None else argv)
    parser = build_arg_parser()
    try:
        args = parser.parse_args(argv)
    except SystemExit as exc:
        return exc.code if isinstance(exc.code, int) else 2
    try:
        limits = limits_from_args(args)
        spec = spec_from_args(args)
        result = run_core_two_phase(args.outer, args.output_dir, spec=spec, limits=limits)
    except (PhaseLimitError, PhaseError, bai.InputError, bai.OutputCollisionError) as exc:
        bai.emit_stdout({"status": "failed", "ok": False, "error": str(exc)}, bai.HARD_MAX_STDOUT_BYTES)
        return 2
    bai.emit_stdout(
        {
            "status": result.status,
            "ok": result.ok,
            "phase": str(Path(args.output_dir) / "phase.json"),
        },
        limits.max_stdout_bytes,
    )
    return 0 if result.ok else 1


if __name__ == "__main__":
    sys.exit(main())

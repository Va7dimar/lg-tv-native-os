"""Bounded, fail-closed streaming inventory for untrusted tar.gz archives."""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import re
import shutil
import stat
import sys
import tarfile
import time
import zlib
from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import BinaryIO, Iterable

HARD_MAX_ADDRESS_SPACE_BYTES = 1073741824
HARD_MAX_WALL_SECONDS = 120
HARD_MAX_MEMBERS = 200_000
HARD_MAX_PATHNAME_BYTES = 100_000_000
HARD_MAX_SELECTED_TEXT_MEMBER_BYTES = 16 * 1024 * 1024
HARD_MIN_FREE_DISK_BYTES = 10 * 1024 * 1024 * 1024
HARD_MAX_EXPANDED_BYTES = 20 * 1024 * 1024 * 1024
HARD_MAX_STDOUT_BYTES = 64 * 1024

NESTED_ARCHIVE_SUFFIXES = (
    ".tar.gz",
    ".tar.bz2",
    ".tar.xz",
    ".tgz",
    ".tbz2",
    ".txz",
    ".tar",
    ".zip",
    ".7z",
    ".rar",
)

WINDOWS_DRIVE = re.compile(r"^[A-Za-z]:[/\\]")
METADATA_TYPES = {
    getattr(tarfile, "XHDTYPE", "x"),
    getattr(tarfile, "XGLTYPE", "g"),
    getattr(tarfile, "GNUTYPE_LONGNAME", "L"),
    getattr(tarfile, "GNUTYPE_LONGLINK", "K"),
}


class LimitError(Exception):
    pass


class OutputCollisionError(Exception):
    pass


class InputCollisionError(Exception):
    pass


class InputError(Exception):
    pass


class PathEscapeError(Exception):
    pass


@dataclass
class Limits:
    max_members: int = HARD_MAX_MEMBERS
    max_pathname_bytes: int = HARD_MAX_PATHNAME_BYTES
    max_selected_text_member_bytes: int = HARD_MAX_SELECTED_TEXT_MEMBER_BYTES
    min_free_disk_bytes: int = HARD_MIN_FREE_DISK_BYTES
    max_expanded_bytes: int = HARD_MAX_EXPANDED_BYTES
    wall_seconds: int = HARD_MAX_WALL_SECONDS
    address_space_bytes: int = HARD_MAX_ADDRESS_SPACE_BYTES
    max_stdout_bytes: int = HARD_MAX_STDOUT_BYTES

    _allow_lower_disk_reserve: bool = field(default=False, repr=False, compare=False)

    def __post_init__(self) -> None:
        maxima = {
            "max_members": HARD_MAX_MEMBERS,
            "max_pathname_bytes": HARD_MAX_PATHNAME_BYTES,
            "max_selected_text_member_bytes": HARD_MAX_SELECTED_TEXT_MEMBER_BYTES,
            "max_expanded_bytes": HARD_MAX_EXPANDED_BYTES,
            "wall_seconds": HARD_MAX_WALL_SECONDS,
            "address_space_bytes": HARD_MAX_ADDRESS_SPACE_BYTES,
            "max_stdout_bytes": HARD_MAX_STDOUT_BYTES,
        }
        for name, hard in maxima.items():
            value = getattr(self, name)
            if not isinstance(value, int) or isinstance(value, bool) or value < 1:
                raise LimitError(f"{name} must be a positive integer")
            if value > hard:
                raise LimitError(f"{name} {value} exceeds hard maximum {hard}")
        if not isinstance(self.min_free_disk_bytes, int) or self.min_free_disk_bytes < 1:
            raise LimitError("min_free_disk_bytes must be a positive integer")
        if (
            self.min_free_disk_bytes < HARD_MIN_FREE_DISK_BYTES
            and not self._allow_lower_disk_reserve
        ):
            raise LimitError(
                f"min_free_disk_bytes {self.min_free_disk_bytes} is below approved floor "
                f"{HARD_MIN_FREE_DISK_BYTES}"
            )

    @classmethod
    def for_tests(cls, **kwargs) -> "Limits":
        kwargs["_allow_lower_disk_reserve"] = True
        return cls(**kwargs)


def limits_public_dict(limits: Limits) -> dict:
    data = asdict(limits)
    data.pop("_allow_lower_disk_reserve", None)
    return data


@dataclass
class Budgets:
    members: int = 0
    pathname_bytes: int = 0
    expanded_bytes: int = 0
    selected_text_bytes: int = 0

    def exhausted(self, limits: Limits) -> str | None:
        if self.members >= limits.max_members:
            return "max_members"
        if self.pathname_bytes >= limits.max_pathname_bytes:
            return "max_pathname_bytes"
        if self.expanded_bytes >= limits.max_expanded_bytes:
            return "max_expanded_bytes"
        return None


def open_untrusted_tar_gz(fileobj: BinaryIO) -> tarfile.TarFile:
    """Open a gzip tar using CPython stream=True so TarInfo objects are not cached."""
    return tarfile.open(fileobj=fileobj, mode="r|gz", stream=True)


@dataclass
class InventoryResult:
    ok: bool
    status: str
    document: dict = field(default_factory=dict)


def canonicalize_member_path(name: str | None) -> tuple[str | None, list[str]]:
    if name is None:
        return None, ["missing_name"]
    if "\x00" in name:
        return None, ["nul_in_name"]
    if WINDOWS_DRIVE.match(name) or name.startswith("\\\\") or name.startswith("//"):
        return None, ["absolute_path"]
    unified = name.replace("\\", "/")
    if unified.startswith("/"):
        return None, ["absolute_path"]
    parts: list[str] = []
    for part in unified.split("/"):
        if part in ("", "."):
            continue
        if part == "..":
            if not parts:
                return None, ["parent_escape"]
            parts.pop()
            continue
        parts.append(part)
    if not parts:
        return None, ["empty_path"]
    return "/".join(parts), []


def classify_link_target(
    member_canonical: str, linkname: str | None
) -> tuple[bool, str | None, list[str]]:
    if not linkname:
        return False, None, ["unsafe_link_target", "empty_link_target"]
    if "\x00" in linkname:
        return False, None, ["unsafe_link_target", "nul_in_name"]
    if WINDOWS_DRIVE.match(linkname) or linkname.startswith("\\\\") or linkname.startswith("//"):
        return False, None, ["unsafe_link_target", "absolute_path"]
    unified = linkname.replace("\\", "/")
    if unified.startswith("/"):
        return False, None, ["unsafe_link_target", "absolute_path"]
    parent_parts = member_canonical.split("/")[:-1] if member_canonical else []
    parts = list(parent_parts)
    for part in unified.split("/"):
        if part in ("", "."):
            continue
        if part == "..":
            if not parts:
                return False, None, ["unsafe_link_target", "parent_escape"]
            parts.pop()
            continue
        parts.append(part)
    return True, "/".join(parts), []


def logical_member_size(info: tarfile.TarInfo) -> int:
    size = int(getattr(info, "size", 0) or 0)
    sparse = getattr(info, "sparse", None)
    if sparse:
        try:
            implied = 0
            for entry in sparse:
                offset, length = entry[0], entry[1]
                implied = max(implied, int(offset) + int(length))
            size = max(size, implied)
        except (TypeError, ValueError, IndexError):
            size = max(size, 0)
    return size


def _utf8_len(value: str | bytes | None) -> int:
    if value is None:
        return 0
    if isinstance(value, bytes):
        return len(value)
    return len(value.encode("utf-8", "surrogateescape"))


def metadata_byte_cost(raw_name: str, info: tarfile.TarInfo) -> int:
    cost = _utf8_len(raw_name) + _utf8_len(getattr(info, "linkname", "") or "")
    pax = getattr(info, "pax_headers", None) or {}
    for key, value in pax.items():
        cost += _utf8_len(str(key)) + _utf8_len(str(value))
    return cost


def is_nested_archive_name(canonical: str) -> bool:
    lower = canonical.lower()
    return any(lower.endswith(suffix) for suffix in NESTED_ARCHIVE_SUFFIXES)


def member_kind(info: tarfile.TarInfo) -> str:
    if info.type in METADATA_TYPES:
        return "metadata"
    if info.isdir():
        return "dir"
    if info.issym():
        return "symlink"
    if info.islnk():
        return "hardlink"
    if info.ischr() or info.isblk():
        return "device"
    if info.isfifo():
        return "fifo"
    if info.isfile() or info.isreg():
        return "file"
    return "unsupported"


def isolation_observation() -> dict:
    net_ns = None
    try:
        net_ns = os.readlink("/proc/self/ns/net")
    except OSError:
        net_ns = None
    return {
        "home_box_visible": os.path.exists("/home/box"),
        "root_ssh_visible": os.path.exists("/root/.ssh"),
        "cursor_visible": os.path.exists("/cursor"),
        "sandbox_net_ns": net_ns,
        "noexec_output_demonstrated": False,
    }


def contained_path(root: Path, *rel_parts: str) -> Path:
    root_resolved = root.resolve()
    candidate = root_resolved.joinpath(*rel_parts).resolve()
    root_s = str(root_resolved)
    cand_s = str(candidate)
    if cand_s != root_s and not cand_s.startswith(root_s + os.sep):
        raise PathEscapeError(f"path escapes output directory: {rel_parts!r}")
    return candidate


def atomic_write_bytes(path: Path, data: bytes) -> None:
    tmp = path.with_name(f".{path.name}.tmp.{os.getpid()}")
    flags = os.O_CREAT | os.O_EXCL | os.O_WRONLY
    fd = os.open(tmp, flags, 0o644)
    try:
        with os.fdopen(fd, "wb") as handle:
            handle.write(data)
            handle.flush()
            os.fsync(handle.fileno())
        os.replace(tmp, path)
    except Exception:
        try:
            os.unlink(tmp)
        except OSError:
            pass
        raise


def open_regular_nofollow(path: Path) -> tuple[int, os.stat_result]:
    try:
        st = os.lstat(path)
    except OSError as exc:
        raise InputError(f"cannot stat input {path}: {exc}") from exc
    if stat.S_ISLNK(st.st_mode):
        raise InputError(f"symlink input rejected: {path}")
    if not stat.S_ISREG(st.st_mode):
        raise InputError(f"input is not a regular file: {path}")
    flags = os.O_RDONLY
    if hasattr(os, "O_NOFOLLOW"):
        flags |= os.O_NOFOLLOW
    try:
        fd = os.open(path, flags)
    except OSError as exc:
        raise InputError(f"cannot open input {path}: {exc}") from exc
    return fd, st


def _validate_inputs(inputs: Iterable[Path]) -> list[Path]:
    resolved: list[Path] = []
    basenames: set[str] = set()
    seen: set[Path] = set()
    for raw in inputs:
        path = Path(raw)
        fd, _st = open_regular_nofollow(path)
        os.close(fd)
        real = path.resolve()
        if real in seen:
            raise InputCollisionError(f"duplicate input path: {real}")
        seen.add(real)
        name = path.name
        if name in basenames:
            raise InputCollisionError(f"duplicate input basename: {name}")
        basenames.add(name)
        resolved.append(path)
    if not resolved:
        raise InputError("no inputs provided")
    return resolved


def _free_disk_bytes(path: Path) -> int:
    return int(shutil.disk_usage(path).free)


def _markdown(document: dict) -> str:
    lines = [
        "# Bounded archive inventory",
        "",
        f"- status: `{document['status']}`",
        f"- ok: `{document['ok']}`",
        f"- generated_at: {document.get('generated_at', '')}",
        f"- errors: {', '.join(document.get('errors', [])) or '(none)'}",
        "",
    ]
    for archive in document.get("archives", []):
        lines.append(f"## {archive.get('filename', '(unknown)')}")
        lines.append("")
        lines.append(
            f"- archive_status: `{archive.get('status')}` members={archive.get('member_count')} "
            f"pathname_bytes={archive.get('pathname_bytes')} expanded_bytes={archive.get('expanded_bytes')} "
            f"selected_text_bytes={archive.get('selected_text_bytes')}"
        )
        if archive.get("error"):
            lines.append(f"- error: {archive['error']}")
        lines.append("")
        lines.append("| index | name | type | size | decision | reasons | selected |")
        lines.append("| --- | --- | --- | ---: | --- | --- | --- |")
        for member in archive.get("members", []):
            lines.append(
                "| {index} | {name} | {typ} | {size} | {decision} | {reasons} | {selected} |".format(
                    index=member.get("index"),
                    name=str(member.get("canonical_name") or member.get("raw_name") or "").replace("|", "\\|"),
                    typ=member.get("type"),
                    size=member.get("size"),
                    decision=member.get("decision"),
                    reasons=",".join(member.get("reasons") or []) or "-",
                    selected=member.get("selected"),
                )
            )
        lines.append("")
    return "\n".join(lines) + "\n"


def _write_selected_file(output_dir: Path, archive_label: str, canonical: str, data: bytes) -> str:
    label = Path(archive_label).name
    if label in ("", ".", ".."):
        label = "input"
    parts = [label] + [part for part in canonical.split("/") if part not in ("", ".")]
    if len(parts) < 2:
        raise PathEscapeError("empty selected path")
    selected_root = contained_path(output_dir, "selected")
    dest = contained_path(selected_root, *parts)
    dest.parent.mkdir(parents=True, exist_ok=True)
    flags = os.O_CREAT | os.O_EXCL | os.O_WRONLY
    fd = os.open(dest, flags, 0o644)
    with os.fdopen(fd, "wb") as handle:
        handle.write(data)
        handle.flush()
        os.fsync(handle.fileno())
    os.chmod(dest, 0o644)
    return str(dest.relative_to(output_dir.resolve()))


def _consume_payload(
    src: BinaryIO,
    hasher=None,
    deadline: float | None = None,
) -> tuple[int, str | None]:
    total = 0
    while True:
        if deadline is not None and time.monotonic() > deadline:
            return total, "wall_seconds"
        chunk = src.read(1024 * 1024)
        if not chunk:
            break
        total += len(chunk)
        if hasher is not None:
            hasher.update(chunk)
    return total, None


def _process_archive(
    path: Path,
    output_dir: Path,
    limits: Limits,
    select: set[str],
    deadline: float,
    hash_input: bool,
    budgets: Budgets,
) -> tuple[dict, list[str], str]:
    errors: list[str] = []
    members: list[dict] = []
    seen: set[str] = set()
    pathname_bytes = 0
    expanded_bytes = 0
    selected_text_bytes = 0
    archive_status = "ok"
    archive_error = None
    security_failed = False
    fd = None
    tf = None
    fileobj = None
    input_sha = None
    raw_stat = os.lstat(path)
    archive_label = path.name
    try:
        fd, _st = open_regular_nofollow(path)
        if hash_input:
            hasher = hashlib.sha256()
            tmpf = os.fdopen(os.dup(fd), "rb")
            try:
                while True:
                    chunk = tmpf.read(1024 * 1024)
                    if not chunk:
                        break
                    hasher.update(chunk)
                input_sha = hasher.hexdigest()
            finally:
                tmpf.close()
            os.lseek(fd, 0, os.SEEK_SET)
        fileobj = os.fdopen(fd, "rb")
        fd = None
        tf = open_untrusted_tar_gz(fileobj)
        index = 0
        while True:
            if time.monotonic() > deadline:
                errors.append("wall_seconds exceeded")
                archive_status = "partial"
                archive_error = "wall_seconds"
                break
            exhausted = budgets.exhausted(limits)
            if exhausted:
                errors.append(f"{exhausted} exceeded")
                archive_status = "partial"
                archive_error = exhausted
                break
            try:
                info = tf.next()
            except (tarfile.TarError, OSError, EOFError, ValueError, zlib.error) as exc:
                errors.append(f"parse_error:{exc}")
                archive_status = "partial" if members else "failed"
                archive_error = "parse_error"
                break
            if info is None:
                break

            raw_name = info.name or ""
            kind = member_kind(info)
            cost = metadata_byte_cost(raw_name, info)
            if kind == "metadata":
                cost += logical_member_size(info)
            if budgets.pathname_bytes + cost > limits.max_pathname_bytes:
                errors.append("max_pathname_bytes exceeded")
                archive_status = "partial"
                archive_error = "max_pathname_bytes"
                break
            pathname_bytes += cost
            budgets.pathname_bytes += cost

            if kind == "metadata":
                continue

            if budgets.members >= limits.max_members:
                errors.append("max_members exceeded")
                archive_status = "partial"
                archive_error = "max_members"
                break

            reasons: list[str] = []
            decision = "accepted"
            selected = False
            selected_output = None
            digest = None
            nested = False
            sparse = bool(getattr(info, "sparse", None))
            if not sparse and hasattr(info, "issparse"):
                try:
                    sparse = bool(info.issparse())
                except Exception:
                    sparse = False
            canonical, path_reasons = canonicalize_member_path(raw_name)
            if path_reasons:
                decision = "rejected"
                reasons.extend(path_reasons)
                security_failed = True
                canonical = canonical or None

            if canonical and canonical in seen:
                decision = "rejected"
                reasons.append("duplicate_canonical_path")
                security_failed = True
            elif canonical:
                seen.add(canonical)

            if kind == "device":
                decision = "rejected"
                reasons.append("device")
                security_failed = True
            elif kind == "fifo":
                decision = "rejected"
                reasons.append("fifo")
                security_failed = True
            elif kind == "unsupported":
                decision = "rejected"
                reasons.append("unsupported_type")
                security_failed = True
            elif kind in {"symlink", "hardlink"}:
                if decision != "rejected":
                    safe, resolved, link_reasons = classify_link_target(
                        canonical or "", info.linkname
                    )
                    if not safe:
                        decision = "rejected"
                        reasons.extend(link_reasons)
                        security_failed = True
                    else:
                        decision = "recorded_not_followed"
                else:
                    # Path already rejected (absolute/escape/etc). Do not
                    # relabel as recorded_not_followed even if the target
                    # string looks like a safe relative name.
                    pass

            logical = logical_member_size(info) if kind == "file" else 0
            if kind == "file":
                if budgets.expanded_bytes + logical > limits.max_expanded_bytes:
                    errors.append("max_expanded_bytes exceeded")
                    archive_status = "partial"
                    archive_error = "max_expanded_bytes"
                    members.append(
                        {
                            "index": index,
                            "raw_name": raw_name,
                            "canonical_name": canonical,
                            "type": kind,
                            "size": logical,
                            "link_target": info.linkname or None,
                            "decision": decision,
                            "reasons": reasons + ["max_expanded_bytes"],
                            "selected": False,
                            "selected_output": None,
                            "sha256": None,
                            "nested_archive_not_expanded": bool(
                                canonical and is_nested_archive_name(canonical)
                            ),
                            "sparse": bool(sparse),
                        }
                    )
                    break
                expanded_bytes += logical
                budgets.expanded_bytes += logical
                if canonical and is_nested_archive_name(canonical):
                    nested = True

            record = {
                "index": index,
                "raw_name": raw_name,
                "canonical_name": canonical,
                "type": kind,
                "size": logical if kind == "file" else int(info.size or 0),
                "link_target": info.linkname or None,
                "decision": decision,
                "reasons": reasons,
                "selected": False,
                "selected_output": None,
                "sha256": None,
                "nested_archive_not_expanded": nested,
                "sparse": bool(sparse),
            }

            if kind == "file":
                src = tf.extractfile(info)
                if src is None:
                    errors.append(f"unreadable_member:{raw_name}")
                    archive_status = "partial"
                    archive_error = "unreadable_member"
                    members.append(record)
                    budgets.members += 1
                    index += 1
                    break
                want = (
                    decision == "accepted"
                    and canonical in select
                    and not nested
                )
                if nested and canonical in select:
                    reasons.append("nested_archive_not_expanded")
                if want and logical > limits.max_selected_text_member_bytes:
                    want = False
                    reasons.append("selected_oversize")
                hasher = hashlib.sha256()
                read_total = 0
                if want:
                    buf = src.read(limits.max_selected_text_member_bytes + 1)
                    read_total += len(buf)
                    if len(buf) > limits.max_selected_text_member_bytes:
                        reasons.append("selected_oversize")
                        hasher.update(buf)
                        extra, wall = _consume_payload(src, hasher, deadline)
                        read_total += extra
                        digest = hasher.hexdigest()
                        if wall:
                            errors.append("wall_seconds exceeded")
                            archive_status = "partial"
                            archive_error = "wall_seconds"
                    elif b"\x00" in buf:
                        hasher.update(buf)
                        digest = hasher.hexdigest()
                        reasons.append("not_plaintext")
                    else:
                        hasher.update(buf)
                        digest = hasher.hexdigest()
                        try:
                            selected_output = _write_selected_file(
                                output_dir, archive_label, canonical, buf
                            )
                            selected = True
                            selected_text_bytes += len(buf)
                            budgets.selected_text_bytes += len(buf)
                        except (OSError, PathEscapeError) as exc:
                            errors.append(f"selected_write:{exc}")
                            archive_status = "failed"
                            archive_error = "selected_write"
                            security_failed = True
                else:
                    read_total, wall = _consume_payload(src, hasher, deadline)
                    digest = hasher.hexdigest()
                    if wall:
                        errors.append("wall_seconds exceeded")
                        archive_status = "partial"
                        archive_error = "wall_seconds"
                if read_total > logical:
                    extra = read_total - logical
                    if budgets.expanded_bytes + extra > limits.max_expanded_bytes:
                        errors.append("max_expanded_bytes exceeded")
                        archive_status = "partial"
                        archive_error = "max_expanded_bytes"
                    else:
                        expanded_bytes += extra
                        budgets.expanded_bytes += extra
                record["sha256"] = digest

            record["decision"] = decision
            record["reasons"] = reasons
            record["selected"] = selected
            record["selected_output"] = selected_output
            members.append(record)
            budgets.members += 1
            index += 1
            if archive_status in {"partial", "failed"} and archive_error in {
                "wall_seconds",
                "max_expanded_bytes",
                "selected_write",
            }:
                break
    except (tarfile.TarError, OSError, EOFError, ValueError) as exc:
        errors.append(f"parse_error:{exc}")
        archive_status = "partial" if members else "failed"
        archive_error = archive_error or "parse_error"
    finally:
        if tf is not None:
            try:
                tf.close()
            except Exception:
                pass
        if fileobj is not None:
            try:
                fileobj.close()
            except Exception:
                pass
        if fd is not None:
            try:
                os.close(fd)
            except OSError:
                pass

    if security_failed and archive_status == "ok":
        archive_status = "failed"
        archive_error = archive_error or "policy_rejected"

    return (
        {
            "filename": path.name,
            "path": str(path),
            "bytes": int(raw_stat.st_size),
            "sha256": input_sha,
            "status": archive_status,
            "error": archive_error,
            "member_count": len(members),
            "pathname_bytes": pathname_bytes,
            "expanded_bytes": expanded_bytes,
            "selected_text_bytes": selected_text_bytes,
            "members": members,
        },
        errors,
        archive_status,
    )


def _pax_records_valid(payload: bytes) -> bool:
    if not payload:
        return False
    text = payload.decode("utf-8", "replace")
    pos = 0
    length = len(text)
    valid_any = False
    while pos < length:
        if text[pos] == "\0":
            break
        space = text.find(" ", pos)
        if space < 0:
            return False
        try:
            rec_len = int(text[pos:space])
        except ValueError:
            return False
        if rec_len <= 0:
            return False
        record = text[pos : pos + rec_len]
        if len(record) < rec_len or "=" not in record:
            return False
        pos += rec_len
        valid_any = True
    return valid_any


def inventory_archives(
    inputs,
    output_dir,
    limits: Limits | None = None,
    select: Iterable[str] = (),
    hash_input: bool = False,
) -> InventoryResult:
    limits = limits or Limits()
    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    json_path = output_dir / "inventory.json"
    md_path = output_dir / "inventory.md"
    if json_path.exists() or md_path.exists():
        raise OutputCollisionError(f"output inventory already exists in {output_dir}")

    validated = _validate_inputs(Path(item) for item in inputs)
    free = _free_disk_bytes(output_dir)
    generated_at = datetime.now(timezone.utc).astimezone().isoformat()
    document = {
        "tool": "bounded-archive-inventory",
        "version": "1.1.0",
        "status": "ok",
        "ok": True,
        "generated_at": generated_at,
        "limits": limits_public_dict(limits),
        "host": {
            "python": sys.version.split()[0],
            "free_disk_bytes": free,
            "platform": sys.platform,
        },
        "isolation_observation": isolation_observation(),
        "controls": {
            "isolation_entrypoint": "isolate_inventory.py",
            "isolation_required_for_untrusted_inputs": True,
            "parser_allocates_extended_headers_before_semantic_limits": True,
            "allocation_backstop": (
                "prlimit address-space and timeout wall via isolate_inventory.py; "
                "semantic member/path/expansion caps do not contain tarfile.next() PAX/GNU allocations"
            ),
            "disk_reserve_check": (
                "observed free bytes once before work; not a filesystem reservation"
            ),
            "in_process_wall_check": (
                "checked between members and during payload reads; "
                "allocation inside tarfile.next() still relies on the process wall"
            ),
            "tarfile_stream": True,
            "noexec_output_demonstrated": False,
            "selected_file_mode": "0644",
            "selected_mode_is_not_noexec_mount": True,
            "tool_never_executes_archive_content": True,
            "selected_plaintext_is_untrusted_data": True,
        },
        "totals": {
            "member_count": 0,
            "pathname_bytes": 0,
            "expanded_bytes": 0,
            "selected_text_bytes": 0,
        },
        "skipped_inputs": [],
        "archives": [],
        "errors": [],
    }

    if free < limits.min_free_disk_bytes:
        document["status"] = "failed"
        document["ok"] = False
        document["errors"].append(
            f"free_disk {free} is below min_free_disk_bytes {limits.min_free_disk_bytes}"
        )
        _persist(output_dir, document)
        return InventoryResult(False, "failed", document)

    deadline = time.monotonic() + limits.wall_seconds
    select_set = set(select or ())
    overall = "ok"
    budgets = Budgets()
    remaining = list(validated)
    while remaining:
        if overall in {"partial", "failed"}:
            for path in remaining:
                document["skipped_inputs"].append(str(path))
            document["errors"].append("stopped_before_remaining_inputs")
            break
        exhausted = budgets.exhausted(limits)
        if exhausted:
            overall = "partial"
            document["errors"].append(f"{exhausted} exceeded")
            document["errors"].append("stopped_before_remaining_inputs")
            for path in remaining:
                document["skipped_inputs"].append(str(path))
            break
        path = remaining.pop(0)
        archive, errors, archive_status = _process_archive(
            path, output_dir, limits, select_set, deadline, hash_input, budgets
        )
        document["archives"].append(archive)
        document["errors"].extend(errors)
        if archive_status == "partial":
            overall = "partial"
        elif archive_status == "failed":
            overall = "failed"
    document["totals"] = {
        "member_count": budgets.members,
        "pathname_bytes": budgets.pathname_bytes,
        "expanded_bytes": budgets.expanded_bytes,
        "selected_text_bytes": budgets.selected_text_bytes,
    }
    if document["errors"] and overall == "ok":
        overall = "partial"

    document["status"] = overall
    document["ok"] = overall == "ok"
    _persist(output_dir, document)
    return InventoryResult(document["ok"], document["status"], document)


def _persist(output_dir: Path, document: dict) -> None:
    json_bytes = (json.dumps(document, indent=2, sort_keys=False) + "\n").encode("utf-8")
    md_bytes = _markdown(document).encode("utf-8")
    atomic_write_bytes(output_dir / "inventory.json", json_bytes)
    atomic_write_bytes(output_dir / "inventory.md", md_bytes)


def build_arg_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Bounded tar.gz inventory reader")
    parser.add_argument("--input", action="append", required=True, dest="inputs")
    parser.add_argument("--output-dir", required=True)
    parser.add_argument("--select", action="append", default=[])
    parser.add_argument("--max-members", type=int)
    parser.add_argument("--max-pathname-bytes", type=int)
    parser.add_argument("--max-selected-text-member-bytes", type=int)
    parser.add_argument("--max-expanded-bytes", type=int)
    parser.add_argument("--min-free-disk-bytes", type=int)
    parser.add_argument("--wall-seconds", type=int)
    parser.add_argument("--hash-input", action="store_true")
    return parser


def limits_from_args(args: argparse.Namespace) -> Limits:
    kwargs = {}
    mapping = {
        "max_members": args.max_members,
        "max_pathname_bytes": args.max_pathname_bytes,
        "max_selected_text_member_bytes": args.max_selected_text_member_bytes,
        "max_expanded_bytes": args.max_expanded_bytes,
        "min_free_disk_bytes": args.min_free_disk_bytes,
        "wall_seconds": args.wall_seconds,
    }
    for key, value in mapping.items():
        if value is not None:
            kwargs[key] = value
    return Limits(**kwargs)


def emit_stdout(payload: dict, limit: int) -> None:
    raw = (json.dumps(payload, separators=(",", ":")) + "\n").encode("utf-8")
    if len(raw) > limit:
        fallback = {
            "status": payload.get("status", "failed"),
            "ok": False,
            "truncated": True,
            "error": "stdout_truncated",
        }
        raw = (json.dumps(fallback, separators=(",", ":")) + "\n").encode("utf-8")
        if len(raw) > limit:
            raw = b'{"status":"failed","ok":false,"truncated":true,"error":"stdout_truncated"}\n'
    buf = getattr(sys.stdout, "buffer", None)
    if buf is not None:
        buf.write(raw)
        buf.flush()
    else:
        sys.stdout.write(raw.decode("utf-8"))
        sys.stdout.flush()


def main(argv: list[str] | None = None) -> int:
    argv = list(sys.argv[1:] if argv is None else argv)
    parser = build_arg_parser()
    try:
        args = parser.parse_args(argv)
    except SystemExit as exc:
        code = exc.code if isinstance(exc.code, int) else 2
        return code
    try:
        limits = limits_from_args(args)
    except LimitError as exc:
        emit_stdout({"status": "failed", "ok": False, "error": str(exc)}, HARD_MAX_STDOUT_BYTES)
        return 2
    try:
        result = inventory_archives(
            args.inputs,
            args.output_dir,
            limits=limits,
            select=args.select,
            hash_input=args.hash_input,
        )
    except (OutputCollisionError, InputCollisionError, InputError, LimitError) as exc:
        emit_stdout({"status": "failed", "ok": False, "error": str(exc)}, HARD_MAX_STDOUT_BYTES)
        return 2
    output_dir = Path(args.output_dir)
    emit_stdout(
        {
            "status": result.status,
            "ok": result.ok,
            "inventory": str(output_dir / "inventory.json"),
            "markdown": str(output_dir / "inventory.md"),
        },
        limits.max_stdout_bytes,
    )
    return 0 if result.ok else 1


if __name__ == "__main__":
    sys.exit(main())

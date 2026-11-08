# Bounded source-archive inventory tooling addendum

Date: 2026-11-08 (Atlantic/Reykjavik)
Parent plan: `tvs/lg-65nano756pr/docs/plans/2026-11-08-native-bootable-os.md` Task 2 / G2a lines 81-93
Approval basis: owner continue (t64), keep going (t65), full allowance (t66) after the E-tooling proposal in `tvs/lg-65nano756pr/handoff/e-tooling-proposal.md`
Status: implementable addendum for a box-only reader. This does **not** authorize TV/hardware/account actions, firmware, flashing, builds, downloaded-code execution, nested archive expansion, ceiling increases, package installation, network requests, or security-check bypass.

This tooling produces an inventory. It does **not** establish a compatible BSP, boot route, recovery path, or installable replacement OS.

## Goal

Ship a small, tested, streaming archive-inventory tool under `/workspace/lg-tv/tooling/` that can later (after independent review) index the three already-downloaded catalog `.tar.gz` originals read-only and optionally copy selected safe plaintext members.

This implementation session uses **synthetic adversarial fixtures only**. Do not parse the catalog archives before independent review.

Catalog originals (opaque-byte hashes from `tvs/lg-65nano756pr/evidence/catalog-manifest.json`; do not open in this session):

| Filename | Bytes | SHA256 |
|---|---|---|
| webOS 6.0 KLP_1.0_1.tar.gz | 3270734309 | 2bef84ebee68a860e9729ad5504ae6bf29b18b5fff9c12df0167e68613569970 |
| webOS 6.0 KLP_1.0_2.tar.gz | 511945894 | 95894dd81e2bb32fd1ced1eb119698f2e1464e6b9b5b5879ea51528d7d5e8832 |
| webOS 6.0 KLP_1.0_3.tar.gz | 1777722146 | f37ca9716820849e37b946bdd5d91d52b51c765a95dc0b309203470015b6fa1c |

## Hard ceilings (pinned defaults; maxima cannot be raised by flags)

These match current E1/Task 2 ceilings. CLI/API may **lower** maxima for efficient tests. Any attempt to set a maximum above the hard value is rejected (fail closed). Changing a hard constant requires a reviewed code change.

| Control | Hard default | Enforcement |
|---|---|---|
| Address space | 1 GiB (1073741824) | `prlimit --as` on isolated process; cannot be raised by flags |
| Wall time | 120 seconds | `timeout --kill-after=5s` plus in-process deadline; cannot be raised by flags |
| Members | 200000 | Streaming counter; exceed => stop, mark partial/failed |
| Total pathname + metadata bytes | 100000000 | Count every member name, link target, and PAX/GNU extended header key/value byte; exceed => stop, mark partial/failed |
| Selected text per member | 16 MiB (16777216) | Do not copy a member whose logical size exceeds this; stream-read at most limit+1 bytes and fail closed on overrun |
| Free disk reserve | >= 10 GiB (10737418240) | Recheck `shutil.disk_usage` on the output filesystem before work; fail if below |
| Aggregate expanded stream/data | 20 GiB (21474836480) | Add each regular member's **logical** size (sparse-aware) before/while skipping payload; exceed => stop, mark partial/failed |
| Nested archives | never expand | `.tar`, `.tar.gz`, `.tgz`, `.tar.bz2`, `.tar.xz`, `.zip`, `.7z`, `.rar` listed only as regular members if otherwise safe |
| Stdout/status | 64 KiB | Tool writes short status only; inventory goes to files |

`min_free_disk_bytes` is a minimum reserve. Tests may set a **higher** reserve to force a failure efficiently. Production CLI default is 10 GiB. Tests may lower other maxima.

Python `tarfile` streaming is a parser, not a sandbox. Extended headers, PAX, GNU long names, sparse metadata, and decompression allocations are untrusted input and count toward budgets.

## Outputs and fail-closed atomicity

Per invocation, write only under the explicit `--output-dir`:

- `inventory.json` — machine-readable result
- `inventory.md` — concise Markdown summary (status, counts, rejections, member table)
- optional `selected/<canonical-relative>` — plaintext copies of explicitly selected safe regular members
- launcher may also write `launcher-stdout.txt`, `launcher-stderr.txt`, `launcher-result.json`

Rules:

- No huge stdout (no member dump on stdout).
- Never write outside `--output-dir` after resolving and containment-checking paths.
- Never follow archive symlinks/hardlinks (no dereference, no extract-via-link).
- Never execute archive bytes, chmod extracted files executable, source scripts, or import archive content.
- Open inputs with `O_RDONLY|O_NOFOLLOW`; reject non-regular inputs (including input symlinks).
- If `inventory.json` / `inventory.md` already exist in the output dir, fail on output collision.
- Write JSON/Markdown to temp files in the output dir, `fsync`, then `os.replace`. A failed or stopped run still replaces with a document whose `status` is `failed` or `partial` and `ok` is `false`. Never leave a successful-looking index for a failed run.
- `status=ok` / `ok=true` only if every member was classified, no security/policy rejects occurred, no limit was exceeded, and parsing completed.
- Security/policy rejects (absolute paths, traversal, unsafe link targets, devices, FIFOs, sockets, unsupported types, duplicate canonical paths, output escape) => `status=failed`, `ok=false`.
- Resource/limit/truncated/malformed stops after some members were recorded => `status=partial`, `ok=false`.
- Truncated/malformed archives with no trustworthy complete parse => `failed` or `partial` as appropriate, never `ok`.

## Path, type, link, and collision policy

Canonicalization (used for admission, duplicates, and output placement):

1. Reject NUL in names or link targets.
2. Reject Windows drive paths (`X:\` / `X:/`) and UNC (`\\` or `//` server) as absolute.
3. Treat `\` and `/` as separators (cross-platform normalization).
4. Reject paths that are absolute after unification (leading `/`).
5. Collapse empty segments and `.`.
6. Resolve `..`; if it would escape the archive root, reject (`parent_escape`).
7. Reject names that normalize to empty (except a directory named `.` is not used as a writable selected path).
8. The canonical form is the POSIX-joined remaining segments (NFC not required for equality; `a/./b` and `a/b` collide; `a\b` and `a/b` collide).

Duplicates: if two members share a canonical name, reject the duplicate (and mark overall failed). Do not last-write-wins.

Input collisions: reject duplicate resolved input paths; reject two inputs that would map to the same output stem.

Output collisions: reject pre-existing inventory files; selected-file paths must `safe_join` under `output-dir/selected` and stay contained after resolve.

Types:

- Regular files: list; may select as plaintext if requested, logical size <= 16 MiB, and no NUL byte is observed.
- Directories: list only.
- Symlinks and hardlinks: **record, never dereference**. If the target is absolute or would escape the archive root when resolved relative to the member's parent directory, `rejected` / `unsafe_link_target` and overall failed. If the target stays inside the archive root, `recorded_not_followed` (not a security failure; still not followed and not extracted).
- Character/block devices, FIFOs, sockets, unknown/unsupported types: rejected, overall failed.
- Sparse regular files: count **logical** size toward the expanded budget; do not select if logical size exceeds the selected-text cap; do not materialize holes outside the cap.

Metadata: GNU long-name / long-link and PAX extended/global headers are untrusted. If the stdlib parser surfaces them as members, treat as metadata (do not extract as user files) and charge their names/payloads to the pathname/metadata budget. If the parser raises on malformed/truncated PAX or gzip, fail closed. Do not implement an ad-hoc second parser beyond wrapping `tarfile` and enforcing budgets/policy.

## Isolation launcher

`isolate_inventory.py` wraps the reader with existing tools only: GNU timeout 9.7, prlimit 2.41.5, bwrap 0.12.0, Python 3.13 stdlib `tarfile`. No new packages.

Demonstrated preflight (do not over-claim):

- Available: read-only namespace binds, cleared environment, separate network namespace via `--unshare-all`, `prlimit` AS/CPU, `timeout` wall kill.
- **noexec output/stage is NOT demonstrated** on this box: default tmpfs executes; remount `noexec` fails without superuser in the sandbox. Do not claim a non-exec mount. Compensating control: the tool never executes members and writes selected text with non-executable mode bits (`0o644`).

Launcher command shape:

- `timeout --kill-after=5s <wall> prlimit --as=<as> --cpu=<wall> --core=0 --nofile=64 -- bwrap --unshare-all --die-with-parent --new-session --clearenv ...`
- `--ro-bind /usr /usr` plus `/bin` `/lib` `/lib64` symlinks into `usr` (this host uses merged-usr).
- `--proc /proc --dev /dev --tmpfs /tmp`
- `--ro-bind` each explicit input file to `/input/<unique-name>`
- `--ro-bind` the inventory tool to `/tool/bounded_archive_inventory.py`
- `--bind` the explicit output directory to `/output`
- Do **not** bind `/home`, `/root`, `/cursor`, SSH/TV keys, or the rest of `/workspace`
- Empty environment except `PATH=/usr/bin:/bin`, `LANG=C`, `PYTHONDONTWRITEBYTECODE=1`
- Inner CLI uses only `/input/...` and `/output`

Resource-ceiling breach: stop and report via launcher result / non-zero exit. Do not retry with raised limits.

## Interfaces

```
python3 /workspace/lg-tv/tooling/bounded_archive_inventory.py \
  --input PATH [--input PATH ...] \
  --output-dir DIR \
  [--select CANONICAL_NAME ...] \
  [--max-members N] \
  [--max-pathname-bytes N] \
  [--max-selected-text-member-bytes N] \
  [--max-expanded-bytes N] \
  [--min-free-disk-bytes N] \
  [--wall-seconds N] \
  [--hash-input]

python3 /workspace/lg-tv/tooling/isolate_inventory.py \
  --input PATH [--input PATH ...] \
  --output-dir DIR \
  [same reader flags, forwarded]
```

Public Python API (tests import these):

- `HARD_MAX_*` constants
- `Limits` (defaults pinned; `__post_init__` / factory rejects maxima above hard caps)
- `canonicalize_member_path(name) -> (canonical|None, reasons)`
- `classify_link_target(member_canonical, linkname) -> (safe: bool, resolved_or_none, reasons)`
- `inventory_archives(inputs, output_dir, limits, select=()) -> InventoryResult`
- `build_isolation_command(inputs, output_dir, limits, tool_path, forwarded_args) -> list[str]`
- `main(argv) -> int`

## Test plan (TDD, synthetic fixtures only)

`python3 -m unittest discover -s /workspace/lg-tv/tooling/tests -v`

Tests create fixtures in temp directories. They must fail before production logic exists, then pass. Capture red/green artifacts under `tooling/artifacts/`.

Required cases:

- Path normalization / absolute / `..` / backslash / duplicates
- Symlink and hardlink safe-vs-escape; links recorded not dereferenced
- Devices, FIFOs, unsupported types
- Member-count, pathname-byte, expansion, selected-text oversize
- Malformed PAX, truncated/malformed gzip
- GNU long names counted and inventoryable when otherwise safe
- Sparse logical-size accounting
- Output containment and existing-output collision
- Input symlink / duplicate input / basename collision
- Hard maxima unraisable; lower test limits accepted
- Disk-reserve failure
- Partial/failed index marked `ok=false`
- Isolation command contents (unshare, ro inputs, no home/credentials, timeout/prlimit)
- Isolation integration with a tiny fixture where possible (home not visible, net ns differs, inventory written)
- Noexec honesty: do not assert a non-exec mount
- Bounded stdout
- Selected files mode not executable; plaintext NUL rejection

## Acceptance for this session

- Addendum written
- Tests written first; red artifact captured; implementation; green artifact captured
- Review copies of whole files plus a from-empty diff under `tooling/review/`
- `tooling/implementation-report.md` and `tooling/progress.md`
- No catalog archive parsed; no Page update; no BSP/boot claim

After independent review of material changes, a later worker may run the same reader against the three originals.


## Review-driven clarifications (2026-11-08, Atlantic/Reykjavik)

These notes correct implementation constraints. They do **not** weaken the pinned aggregate ceilings or replace the original Task 2/G2a plan.

- Member, pathname/metadata, and expanded-data ceilings are **invocation-level aggregates across all inputs**, not per-archive resets. A single run over the three catalog originals shares one 200000-member, 100000000 pathname-byte, and 20 GiB expanded budget.
- Exceeding a ceiling, or a parse/policy `failed`/`partial` result, **stops the run**. Later inputs are not opened, inventoried, or selected. The index is marked `partial` or `failed` with `ok=false`.
- `isolate_inventory.py` is the mandatory entrypoint for untrusted or catalog archives. CPython `tarfile.next()` reads PAX/GNU extended-header payloads before semantic budgets run. Process `prlimit` address-space (1 GiB) and `timeout` wall (120 s) are the allocation/time backstop, not the semantic caps.
- The tool uses `tarfile.open(..., mode="r|gz", stream=True)` so CPython does not cache `TarInfo` objects in `TarFile.members`.
- CLI `--min-free-disk-bytes` cannot go below the approved 10 GiB floor. Tests may use `Limits.for_tests(...)` to exercise the check. The disk check observes free space once before work; it is not a filesystem reservation.
- Selected plaintext is written to `selected/<input-basename>/...` so same-named members from different archives do not collide. Mode `0644` means the file is not marked executable by this tool; it is **not** a noexec mount. Output remains an ordinary writable filesystem. Selected text is untrusted data (NUL-free), never executed by this tool, and not treated as a script runner.
- In-process wall checks run between members and during payload reads. Time spent inside `tarfile.next()` (header/PAX allocation) still relies on the launcher process wall.
- Input symlinks are rejected by both the reader and the isolation launcher (`O_NOFOLLOW` / lstat), which do not follow a leaf symlink to bind a different file.

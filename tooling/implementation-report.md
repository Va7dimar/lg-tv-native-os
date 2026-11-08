# Bounded archive inventory — implementation report

Recorded: 2026-11-08 04:38 Atlantic/Reykjavik
Worker scope: box-only tooling under `/workspace/lg-tv/tooling/`. No repository, no package installs, no TV/hardware/account actions, no catalog-archive parsing, no Page update.

## What was implemented

A streaming, fail-closed inventory reader and an isolation launcher.

| Path | Role |
|---|---|
| `/workspace/lg-tv/docs/superpowers/plans/2026-11-08-bounded-source-inventory.md` | Implementable tooling addendum (written first) |
| `/workspace/lg-tv/tooling/bounded_archive_inventory.py` | Reader: stdlib `tarfile` wrapper, policy, limits, atomic JSON/Markdown, optional selected plaintext |
| `/workspace/lg-tv/tooling/isolate_inventory.py` | Launcher: `timeout` + `prlimit` + `bwrap --unshare-all` around the reader |
| `/workspace/lg-tv/tooling/tests/test_bounded_archive_inventory.py` | 48 unittest cases, synthetic adversarial fixtures only |
| `/workspace/lg-tv/tooling/README.md` | Repro commands |
| `/workspace/lg-tv/tooling/progress.md` | Resume notes |
| `/workspace/lg-tv/tooling/artifacts/` | Red/green logs and versions |
| `/workspace/lg-tv/tooling/review/` | Whole-file review copies and from-empty diff |

Public interface:

- `Limits` defaults pinned to current E1 ceilings. Any maximum above the hard cap raises `LimitError` (CLI exit 2). Tests may lower maxima.
- `canonicalize_member_path`, `classify_link_target`, `logical_member_size`, `inventory_archives`, `main`
- `isolate_inventory.build_isolation_command`, `isolate_inventory.main`
- CLI: `--input` (repeatable), `--output-dir`, `--select` (repeatable), lowerable limit flags, `--hash-input`

Hard defaults: 1 GiB address space, 120 s wall, 200000 members, 100000000 pathname/metadata bytes, 16 MiB selected-text member, >=10 GiB free-disk reserve, 20 GiB aggregate logical expanded data, 64 KiB stdout status, no nested expansion.

## Policy (consistent)

- Inputs opened with `O_RDONLY|O_NOFOLLOW`; symlink and non-regular inputs rejected.
- Duplicate resolved input paths and duplicate input basenames rejected (`InputCollisionError`).
- Existing `inventory.json` / `inventory.md` rejected (`OutputCollisionError`).
- Paths: reject NUL, Unix/Windows/UNC absolute names, and `..` escape after treating `\` and `/` as separators and collapsing `.` and empty segments. `foo/../bar` becomes `bar`. `a\b` and `a/b` collide.
- Duplicate canonical names: reject, overall `failed`.
- Symlinks and hardlinks: never dereferenced and never selected. Safe in-tree targets are `recorded_not_followed` (not a security failure). Absolute or escaping targets are `rejected` / `unsafe_link_target` and overall `failed`.
- Devices and FIFOs rejected (`device`, `fifo`). Unknown types rejected (`unsupported_type`).
- Nested archive suffixes are listed only; `nested_archive_not_expanded` is set and they are not selected or recursed.
- Regular payload is streamed and SHA-256 hashed while skipping. Selected copy happens only for accepted regular files, requested names, logical size <= cap, and no NUL (plaintext). Files are created `0600` then chmod'd to `0644` via `O_CREAT|O_EXCL`.
- Sparse members use logical size (`TarInfo.size` and sparse map extent) toward the expansion cap.
- PAX/GNU extended headers are untrusted metadata: counted toward the pathname/metadata budget; malformed gzip/tar/PAX fail closed.
- Limit breaches stop processing and write `status=partial`, `ok=false`. Policy rejects write `status=failed`, `ok=false`. `ok=true` only after a complete parse with no policy/limit/parse errors.
- JSON and Markdown are written via temp + `fsync` + `os.replace`.

## Isolation (evidenced, not over-claimed)

Pre-existing tools: Python 3.13.5, GNU tar 1.35 (not used as the reader), bubblewrap 0.12.0, prlimit from util-linux 2.41.5, timeout (GNU coreutils) 9.7.

Launcher command includes `timeout --kill-after=5s`, `prlimit --as=<limit> --cpu=<wall> --core=0 --nofile=64`, `bwrap --unshare-all --die-with-parent --new-session --clearenv`, read-only `/usr` plus merged-usr symlinks, `--proc`, `--dev`, `--tmpfs /tmp`, `--ro-bind` of each explicit input file to `/input/<name>`, `--ro-bind` of the reader to `/tool/bounded_archive_inventory.py`, and `--bind` of the explicit output directory to `/output`. It does not bind `/home`, `/root`, `/cursor`, or the rest of `/workspace`. `--share-net` is not added.

**noexec is not demonstrated and is not claimed.** On this box a bwrap tmpfs still executes scripts, and remounting the output bind `noexec` fails (`must be superuser to use mount`). Compensating controls: the reader never executes members and writes selected text with mode `0644`. `launcher-result.json` sets `noexec_output_demonstrated: false`.

Integration test `test_isolation_integration_hides_home_and_writes_inventory` ran the real launcher on a tiny synthetic archive: exit 0, inventory `ok`, `home_box_visible` false inside the sandbox observation, `unshare_all` true, and host vs sandbox net namespace inodes differed.

## TDD / verification

1. Addendum written before code.
2. Tests written before production behavior.
3. Red without modules: `python3 -m unittest discover -s /workspace/lg-tv/tooling/tests -v` → `ModuleNotFoundError` (see `artifacts/red-initial.txt`).
4. Intentional stubs returning wrong/empty behavior: `Ran 48 tests` `FAILED (failures=34, errors=10)` in 0.028s (`artifacts/red-after-stubs.txt`). Four tests passed accidentally on stub defaults (including the catalog-path guard and some assignment-only checks).
5. Production implementation.
6. After a stdout-buffer fix for captured `StringIO`, fresh run:

```
python3 -m unittest discover -s /workspace/lg-tv/tooling/tests -v
Ran 48 tests in 0.101s
OK
EXIT:0
```

Artifact: `tooling/artifacts/green-final.txt` (2026-11-08 04:38 Atlantic/Reykjavik).

The 48 tests cover: defaults and unraisable maxima; path normalization (absolute Unix/Windows/UNC, `..`, backslash collision, NUL, empty); link safe vs escape; devices/FIFOs; member-count, pathname-byte, expansion, sparse logical size; selected plaintext, oversize, NUL binary; duplicates; GNU long names; malformed PAX; truncated and malformed gzip; output collision; duplicate inputs and basename collision; symlink input; disk-reserve failure; nested archive non-expansion; CLI hard-max rejection; bounded stdout; isolation command contents; isolation integration.

Catalog originals (`webOS 6.0 KLP_1.0_{1,2,3}.tar.gz`) were not opened. Tests use only temp synthetic `.tar.gz` files.

## Versions

From `tooling/artifacts/versions.txt` (2026-11-08 04:38 Atlantic/Reykjavik / recorded as GMT, UTC+0):

- Python 3.13.5
- tar (GNU tar) 1.35
- bubblewrap 0.12.0
- prlimit from util-linux 2.41.5
- timeout (GNU coreutils) 9.7

No new packages were installed. GNU tar is present but inventory parsing uses the validated Python `tarfile` wrapper.

## Known risks and residual concerns

- Independent reviewer should inspect the reader before it is pointed at the three hashed catalog archives (5.56 GB total). This session did not do that.
- `tarfile` still performs decompression and header parsing inside the process. Isolation (1 GiB AS, 120 s wall, no network, narrow binds) plus semantic caps are the sandbox; a parser bug could still DoS or confuse classification. PAX validation is best-effort around what the stdlib surfaces or raises.
- Streaming mode used is `r:gz` on an `O_NOFOLLOW` file descriptor (forward-seekable gzip wrapper), not `r|gz`. Truncation/malformed gzip tests passed with this mode.
- Expansion accounting uses declared logical size. A lying size field plus extra unread data should be caught by `tarfile` when advancing; this should be re-checked on very large real archives.
- Selected-text aggregate size is counted (`selected_text_bytes`) and included in the per-member cap and expansion budget, but there is no separate selected-text total cap below the 20 GiB expansion ceiling.
- Free disk is checked once at start, not reserved by the filesystem.
- Address-space and wall-time process limits are enforced by the launcher (`prlimit`/`timeout`). In-process code also has a monotonic wall deadline. `prlimit --as` is not a perfect cgroup RSS guarantee.
- Isolation integration writes a one-line JSON status to stdout (visible after the unittest summary in `green-final.txt`). That status is small; inventories themselves go to files.
- `bwrap --dev /dev` is included so Python/stdlib have a normal device node set. It is a new isolated `/dev`, not a bind of host `/dev`... actually bwrap `--dev /dev` mounts a fresh minimal devtmpfs-like set. Still not a claim of a sealed device policy.
- Output directory itself is an ordinary writable ext4 bind (exec remains possible). Do not document it as noexec.
- Tooling success is an inventory capability only. It does not show board support, a boot route, recovery from an overwritten webOS, or a replacement OS.

## Review package

Whole files (not a git checkout) under `/workspace/lg-tv/tooling/review/`:

- `bounded_archive_inventory.py`
- `isolate_inventory.py`
- `tests_test_bounded_archive_inventory.py`
- `2026-11-08-bounded-source-inventory.md`
- `from-empty.diff` (unified diffs against `/dev/null`)
- `FILELIST.txt`

Parent should dispatch an independent reviewer on these material changes before any catalog-archive parse.


## Review-fix loop (2026-11-08 04:51 Atlantic/Reykjavik)

Independent review (`tooling/review/independent-review.md`) failed SPEC and quality. This section records the authorized box-only fix loop. Catalog/LG originals were still not parsed. This is a self-fix report, not a claim that independent review has passed.

### Regression tests first (red)

Command:

```
python3 -m unittest /workspace/lg-tv/tooling/tests/test_review_regressions.py -v
```

Artifact: `tooling/artifacts/red-review-regressions.txt`

Result: `Ran 13 tests in 0.035s` `FAILED (failures=12, errors=1)` `EXIT:1`

The 13 new tests encoded the review counterexamples before production changes: aggregate member/expanded/pathname budgets; stop-and-do-not-select later archives after partial or failed; absolute symlink member stays `rejected`; parser-surfaced GNU sparse logical size; `open_untrusted_tar_gz` stream=True without member cache; CLI disk-reserve floor; valid JSON stdout truncation; namespaced selected paths; isolate rejects symlink inputs; document isolation/noexec honesty.

### Production fix (coherent patch)

- Invocation-level `Budgets` accumulate members, pathname/metadata bytes, expanded logical (and extra decompressed) bytes, and selected-text bytes across all inputs. Remaining budget is enforced inside `_process_archive`.
- After `partial` or `failed`, remaining inputs are recorded in `skipped_inputs` and are not opened. An already-exhausted budget also skips later inputs without reading them.
- Link-target classification runs only when the member path itself was not already rejected, so `/abs/link` -> `relative-target` stays `decision=rejected` with `absolute_path`.
- GNU type-S sparse fixtures are parsed via the same opener; inventory records `sparse=true` and charges parser-surfaced logical size (`info.size` after `_proc_sparse` plus sparse map extents).
- Archives are opened with `tarfile.open(..., mode="r|gz", stream=True)` (`open_untrusted_tar_gz`) so CPython does not append to `TarFile.members`.
- `Limits.for_tests` may lower the disk reserve for synthetic tests. Production `Limits()` and CLI `--min-free-disk-bytes` cannot go below 10 GiB.
- Selected plaintext is written to `selected/<archive-basename>/...` with `O_CREAT|O_EXCL` and mode `0644`. `0644` is not a noexec mount; `noexec_output_demonstrated` remains false. The tool never executes archive content. Selected bytes are untrusted NUL-free data.
- Isolate launcher `lstat`+`O_NOFOLLOW` rejects leaf symlink inputs instead of `Path.resolve()`-following them into `--ro-bind`.
- `emit_stdout` truncation now emits a small valid JSON object (`truncated` / `stdout_truncated`) rather than sliced invalid JSON.
- Unused leftover hasher/drain path removed; hashing uses one hasher through selected and remainder reads.
- Inventory `controls` document the real guarantees: isolation required for untrusted inputs; PAX/GNU allocation happens inside `tarfile.next()` before semantic caps; AS/wall are the allocation backstop; disk check is a one-time observation, not a reservation; in-process wall is between members and during payload reads.

### Green after fix

Regression file:

```
python3 -m unittest /workspace/lg-tv/tooling/tests/test_review_regressions.py -v
Ran 13 tests in 0.027s
OK
EXIT:0
```

Artifact: `tooling/artifacts/green-review-regressions.txt`

Full suite, including isolation wrapper integration:

```
python3 -m unittest discover -s /workspace/lg-tv/tooling/tests -v
Ran 61 tests in 0.145s
OK
EXIT:0
```

Artifact: `tooling/artifacts/green-after-review-fixes.txt` (2026-11-08 04:51 Atlantic/Reykjavik)

Review probe counterexamples addressed by named tests: `test_cross_archive_member_budget_is_aggregate`, `test_cross_archive_expanded_budget_is_aggregate`, `test_partial_first_archive_does_not_process_or_select_later`, `test_absolute_symlink_member_stays_rejected`, `test_parser_surfaced_sparse_logical_size`.

### Remaining concerns (self-review only)

- Independent reviewer has not re-reviewed this patch. Do not treat this update as review-passed.
- Semantic caps still cannot contain `tarfile.next()` PAX/GNU allocations. Catalog parsing, if later approved, must use `isolate_inventory.py`.
- `prlimit --as` remains virtual address space, not RSS / cgroup `memory.max`.
- Disk reserve is still a single pre-work observation, not a quota.
- noexec output mount is still not demonstrated and is not claimed. Selected `0644` files can sit on an executable filesystem.
- In-process deadline cannot interrupt allocation inside `tarfile.next()`; the process wall is the backstop there.
- This tooling still does not establish a BSP, boot route, recovery path, or replacement OS.

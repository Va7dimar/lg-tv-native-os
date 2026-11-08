### Model and effort used
Claude Opus 5.5 (`claude-opus-5-5`). The harness ran me at a low reasoning-effort setting. This was a static read only.

**Coverage limits**
- **Contract file not read.** My Read of `docs/superpowers/plans/2026-11-08-adaptation-libkadaptor-phase.md` was denied because it is outside the allowed directory, and I did not work around that. I judged the code against your 14 requirements as written.
- **Hashes match.** reader `7884236467e1…42c2` and launcher `192dce045e47…e55b` match your expected values.
- **Also read:** the helpers the code calls in `bounded_archive_inventory.py` (lines 28–50 and 136–403).
- **Not verified:** my one runtime check, whether this Python's `tarfile` accepts `stream=True` (it ran no archive data), needed approval and did not run. I did not run the tests.

### Strengths
- **Outer size and hash checked before any tar parse.** `adaptation_libkadaptor_phase.py:457-463` opens without following symlinks, applies the 512 MiB compressed cap (460), charges the admitted budget (462), then `verify()` (235-246) checks size and SHA256. Only after that does `members()` call `open_untrusted_tar_gz` (251). The hash and the parse use the same descriptor. Tests: `test_outer_hash/size_verified_before_tar_parser`.
- **Exact target pin.**
  - Only `info.name == TARGET_MEMBER` is staged (466).
  - The canonical target must have exactly that raw name and must be a regular file (275-279).
  - Duplicate canonical paths are rejected (270), so a second copy cannot sneak in.
  - The destination name comes from a constant, and the file is created with `O_EXCL|O_NOFOLLOW` (315-322).
  - Size is checked before the copy (305), and size plus hash after it (329-332). A failed copy is deleted (333-336).
- **Staged file re-hashed before the single inner parse**, through the same descriptor (343-347). `verified_before_inner` is set only after that (347). `test_staged_rehash_before_inner` checks there is exactly one parser call.
- **Pins can't be changed.**
  - `PhaseSpec.__post_init__` rejects any change to the pins unless synthetic mode is on (109-112).
  - The CLI has only `--outer`, `--output-dir` and `--synthetic-fixture-mode` (494-498).
  - The synthetic spec file may contain only the four size/hash keys plus an optional `member`, which must equal the pinned name (137-141). Keys such as `synthetic` or a different target are rejected. `type(...) is int` rejects bools and floats (104).
  - Production checks the outer file name (455).
- **Bounded streaming.** `consume()` reads 1 MiB at a time and buffers only when `text=True` (212-233). Unclaimed outer members (469) and unselected inner members (354) are hashed and thrown away.
- **Shared budgets, one set of counters.** The phase keeps one deadline (194) and one `totals` dict for outer and inner.
  - **Expanded bytes (4 GiB)** charge four things: outer logical regular files (288), the staged copy per chunk (225), inner logical files (288), and selected copies (364).
  - **Outer decoded (640 MiB)** counts regular files only (286-287).
  - **Admitted compressed (1 GiB)** counts the outer file (462) plus the copied target per chunk (226).
  - **Binary (128 MiB each and combined)** is checked before the copy (308-313) and per chunk (224).
  - **Plaintext (16/64 MiB)** is checked at 352, 230 and 363.
  - **Members and pathname bytes** are charged at 266 and 263.
  - **Free disk** is observed at 449, 314, 227, 366 and 382.
  - With the production pins this fits: 511,945,894 + 123,840,909 = 635,786,803 bytes, under 1 GiB.
- **Ceilings can't be raised.** `CEILINGS` plus `__post_init__` (34-47, 79-87) enforce 1..ceiling. The 10 GiB disk floor can be lowered only through `for_tests`. The launcher sends its limits through `PhaseLimits` (`isolate_adaptation_phase.py:16`).
- **Isolation.** `timeout` + `prlimit --as/--cpu/--core=0/--nofile` + `bwrap --unshare-all --clearenv` (`isolate_adaptation_phase.py:25-28`).
  - Read-only binds: `/usr`, two tool files, and the outer file through a held `/proc/self/fd/N` (36-38, 84-89).
  - The only writable bind is the output directory.
  - No `/home`, `/root`, `/cursor` or `--share-net`.
- **Controls stated honestly** in the output (`adaptation_libkadaptor_phase.py:174-185`): `noexec_output_demonstrated: False`, the PAX/GNU allocation caveat, disk is "observation… not a reservation", and outer decoded counts regular files only.
- **No nested expansion** (inner is one level, 294, 351). Links are recorded and never followed (291). Nothing is executed.

### Issues

#### Critical
None found.

#### Important

**1. A crash or timeout leaves no failed index, and the external timeout beats the internal deadline.**
- **Where:** `adaptation_libkadaptor_phase.py:480-481` and `:194`; `isolate_adaptation_phase.py:25` and `:94-106`.
- **What:**
  - `MemoryError` (the expected result of hitting the `prlimit --as` limit inside `tarfile.next()`), `TypeError` and `KeyError` are not in the except list, so the child exits without writing `phase.json`.
  - The external `timeout 120` starts before interpreter startup, while the internal 120 s deadline starts at `_Phase.__init__`. The external one fires first, so the "partial" path is effectively unreachable under the launcher. The `prlimit --cpu=120` cap has the same problem.
  - When `phase.json` is missing, the launcher writes only `launcher-result.json`.
- **Why it matters:** this never produces `ok=true`, so requirement 8 holds. But the most likely failure modes leave no failed index.
- **Minimal fix:**
  - Set the internal deadline about 10 s below the external one (for example `wall_seconds - 10` for the in-process deadline).
  - Add `MemoryError` to the except list in `run_adaptation_phase`.
  - In the launcher, if `phase.json` is missing or the exit code is nonzero, call `ap.record_failed_phase(output, f"child exit {rc}")`.

**2. An index collision overwrites the old index, and the launcher has no freshness check of its own.**
- **Where:** `adaptation_libkadaptor_phase.py:451-454` → `_persist` (398-418, with `os.replace` in `atomic_write_bytes`); `isolate_adaptation_phase.py:112-113`.
- **What:**
  - **Known behaviour, confirmed:** on a collision the existing `phase.json` or `phase.md` is replaced by a failed index.
  - **Second path:** if the launcher fails after a successful child run (for example `_write_log` disk check at 60-62, or JSON decoding), `record_failed_phase` replaces the child's full `ok:true` document with a skeleton failed document. This is fail-safe, but the evidence is lost.
  - **Third path:** in a reused directory, if the child is killed before line 451, an old `ok:true` `phase.json` stays on disk while the exit code is nonzero.
- **Impact for the exact fresh command:** none, as long as `inspection-adaptation-PENDING-REVIEW` does not exist beforehand. For general use it is an important quality issue.
- **Minimal fix:**
  - Have the launcher refuse to start if `phase.json`, `phase.md`, `phase-failed.json` or `launcher-*.{txt,json}` exist (or require a missing or empty output directory).
  - On a collision, write to `phase-failed.json` only and never replace an existing index.
  - Have the launcher's post-run failures write `launcher-failed.json` instead of calling `record_failed_phase`.

**3. Broad selection plus a whole-phase stop on oversized candidates makes a false "partial" likely on the real tarball.**
- **Where:** `adaptation_libkadaptor_phase.py:152`, `:155-158`, `:352-353` and `:363`.
- **What:**
  - Any path with a directory component named `build`, `config` or `configs` is a selection candidate whatever its type. So are source files named `config.c` or `build.c`.
  - Any header whose basename contains the substring `api` is selected (for example `rapidjson.h`, `capi.h`).
  - A single candidate over 16 MiB (for example `…/build/libfoo.so`) raises `PhasePartial` for the whole phase. Candidates over 64 MiB combined do the same.
  - A 118 MiB compressed "libkadaptor" tarball probably contains prebuilt artefacts, which makes this plausible.
- **Why it matters:** this fails closed, so it is not unsafe. It is likely to waste the production run.
- **Minimal fix:** if your contract does not require a hard stop for oversized candidates, skip and record them instead (`reasons.append("oversize_not_selected")`, keep charging expanded bytes). Also limit directory selectors to text-like suffixes or extensionless files, and match `api` as a token (`_api`, `api_`, `api.h`) rather than a substring.

#### Minor
- **`partial` gets relabelled `failed`** (`adaptation_libkadaptor_phase.py:381-386`). After a deadline `PhasePartial`, the `phase.tick()` in `_persist` raises again, so the status becomes "failed" and the error appears twice. Fix: skip `tick()` in `_persist`, or don't downgrade `partial`.
- **Dead metadata branch** (`:261-265`). `tarfile.next()` handles `x/g/L/K` headers internally and never returns them. Their cost is already counted through `pax_headers` and the name and linkname. Fix: remove the branch or comment it as defensive.
- **Hardlink targets resolved against the wrong base** (`:281` → `bounded_archive_inventory.py:190`). Tar hardlink targets are relative to the archive root, but the code resolves them against the member's parent directory. Links are never followed, so only the classification and the recorded `link_target` can be wrong. Fix: use the archive root as the base for `hardlink`.
- **Disk observed per chunk** (`:227`). About 119 `disk_observations` entries for one copy. Fix: observe once before the copy and then every N MiB.
- **`record_failed_phase` always records production pins** (`:424-425`), even in synthetic mode.
- **Hard-coded limits in the launcher result** (`isolate_adaptation_phase.py:105`). `timeout_wall_seconds` and `prlimit_as_bytes` are fixed values rather than the limits actually used. Harmless while `main` uses the defaults.
- **Untrusted text in `phase.md`** (`:387-390`). Archive-derived canonical names inside errors go into the Markdown unescaped (Markdown/control-character injection, cosmetic).
- **Empty canonical paths fail the phase.** A `./` or `.` top entry produces `empty_path` and a whole-phase failure (fail-closed; can cause a false failure on some tarballs).
- **Unclaimed payloads are hashed** (`:222`) even though the digest is thrown away for outer non-targets. This costs CPU only.

### Residuals (honest limitations, not must-fixes)
- **noexec:** the output mount is not noexec, and the code says so (182-183). Selected files are written as 0644.
- **Memory limit:** `prlimit --as` limits virtual size, not resident memory. It is the only backstop for PAX/GNU allocations inside `tarfile.next()`, which the code acknowledges (3-5, 177-178).
- **Disk floor:** observed, not reserved. Space can drop between checks.
- **`outer_decoded`:** counts logical sizes of regular files only, not the full decompressed tar stream (headers, padding, PAX data).
- **Hash then parse window:** the same descriptor is used, but a host process with write access could still change the same file between hashing and parsing. Read-only binds only protect against the sandbox. The archive should be immutable on the host.
- **Leftovers on failure:** a staged copy or selected files written before a failure stay on disk when `ok=false`. Consumers must check `ok`.
- **Synthetic mode on the production CLI** skips the outer-name and hash pins, but only for the pinned member name, and the output records it.
- **Unverified Python dependency:** `stream=True` support in the host and sandbox `/usr/bin/python3` is not confirmed by me. On an older `tarfile` the `TypeError` would crash the child, with no `ok=true` and no index (see Important #1).

### SPEC: PASS
All 14 requirements are implemented as stated, against your restated contract (I could not read the plan file). Item 9's known overwrite behaviour is confirmed and recorded as Important #2.

### QUALITY: PASS
I'm passing it with conditions. No issue can produce `ok=true` wrongly, write outside the output directory, retarget the package, or raise a ceiling. The three Important items are about failure reporting and the risk of a false "partial", and should be fixed before the tool is reused more widely.

### Checkpoint for the exact planned command: YES, with conditions
1. `/workspace/lg-tv/source-catalog/inspection-adaptation-PENDING-REVIEW` must not exist before the run. This makes Important #2 irrelevant. I did not check this, because the path is outside my allowed directories.
2. Run it with no `--synthetic-fixture-mode`.
3. Count the run as successful only if the launcher exits 0 **and** `phase.json` exists with `ok:true`/`status:"ok"` **and** `copied[0].verified_before_inner == true`.
   - Treat any of these as failure: a missing `phase.json`, exit codes 124/137, `partial`, or `failed`.
4. No host process may write to the outer archive during the run.
5. First confirm that the synthetic suite passes on this host's `/usr/bin/python3`, which proves `tarfile` accepts `stream=True`.
6. Be prepared for a fail-closed "partial" caused by Important #3. That is a reason to adjust the selection rules, not to raise any ceiling.

### Did I execute anything against catalog archives?
No. I did not access, hash, list or parse anything under `source-catalog/archives/`, and ran no network commands. The only commands I ran hashed and line-counted the two tool files and listed definitions in `bounded_archive_inventory.py`. One harmless Python version check was blocked pending approval and did not run.

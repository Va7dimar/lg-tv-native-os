# Independent review: adaptation / libkadaptor phase tooling

Reviewed: 2026-11-08 06:35 Atlantic/Reykjavik (UTC+0)
Authority cited by parent: owner `t71u` (off-TV autonomy) and `t74u` (subscription-cost priority).
Scope: local non-repo data-processing tool only. No LG/catalog archive was read, hashed, or parsed. No TV actions, installs, production edits, Page writes, paid-API bypass, or permission bypass. Prior reviews and their probe trees were left immutable.

This review is technical criterion, not permission to inspect the original outer archive. Parent coordinates any real run.

Primary whole-code/spec analysis was requested from subscribed Claude Opus 5.5 HIGH. This document is the independent validation: contract + code + packaged artifacts + new synthetic probes, cross-checked against that Claude run (recorded honestly, including coverage limits).

## Package and hashes

Review package: `tooling/review/adaptation-libkadaptor-2026-11-08/`
Contract: `docs/superpowers/plans/2026-11-08-adaptation-libkadaptor-phase.md`

Verified SHA-256 of live production files (match the package copies and the claimed pins):

```
7884236467e1533de7e3ac1266c602845cee35f4acbda11612d7e01dd36842c2  tooling/adaptation_libkadaptor_phase.py
192dce045e47c30379e35e66584f6d21b584ecf6418a9729d1d334777730e55b  tooling/isolate_adaptation_phase.py
295f1972af7df84b7e5d3f43c7cf76d9eb6ef1e4f87ca35d0d1ed9fd44f4406f  tooling/tests/test_adaptation_libkadaptor_phase.py
ee7870b95a6603fae3c38d5a9908da559c598fd29a7b69ba7c2b9a369473ae2c  tooling/bounded_archive_inventory.py  (unchanged)
eb289faf86523479944275918a2777cf23c429d2b96dd1a8822a2ead2f371915  tooling/isolate_inventory.py          (unchanged)
4b030684120c6366ffcaefcd9181f7b6d695ba2cdc46148d3318fe40f65992ce  tooling/targeted_core_two_phase.py    (unchanged)
1cc90673cf34fc9e1fdb8ea535caa82b358ba4561169dec4e89c076fd4953ffb  tooling/isolate_targeted_phase.py     (unchanged)
```

Protected-file note in the package (`protected-files-unchanged.txt`) matches the live hashes above.

Method: contract + whole reader/launcher + tests + from-empty and vs-CORE-TWO diffs; existing red/green/independent-verify artifacts (not a blind full-suite rerun); 19 new targeted synthetic probes under `tooling/review/probes-adaptation-libkadaptor-2026-11-08/`. No production files were edited.

Test evidence (authoritative artifacts, not re-run here):

- `red-adaptation-phase.txt`: `Ran 49 tests` `FAILED (failures=51, errors=13)` — stub-era TDD, assertions of the form `missing adaptation behavior`.
- `green-adaptation-phase.txt` and `independent-verify-adaptation.txt`: `Ran 54 tests` `OK` (five tests were added after the 49-test red file; the current test module has 54 `test_` methods).
- `green-adaptation-full-suite.txt` and `independent-verify-full-suite.txt`: `Ran 139 tests` `OK` (54 new + 85 prior).

---

## Verdict

| Gate | Result |
|---|---|
| SPEC | **PASS** |
| QUALITY | **PASS** |
| Blocking / must-fix | **None** for the exact planned isolated invocation with a fresh output directory and unchanged caps |
| Checkpoint (one exact production invocation, caps unchanged) | **YES, it can truthfully pass**, under the conditions below. This is not itself permission to run. |

The phase implements the written adaptation contract: hash/size of the outer file before any tar parse; copy only `soc/libkadaptor-1.0.0-908.3.tar.gz` (123840909 / `46e7e652…`); re-hash the staged file before one inner inventory; production CLI and synthetic fixture mode cannot retarget another package; bounded 1 MiB chunk discard of unclaimed payloads; shared whole-phase ceilings; path/link/type/duplicate/sparse policy with PAX/GNU allocation acknowledged and isolate AS/wall as backstop; stop-all on fail/partial (never `ok=true`); fresh-output collision recorded as `failed`; symlink containment; no `/home` `/root` `/cursor` / `--share-net`; one inner level; no member execution; README/build/config/license/manifest plus conservative hardware-header selection; honest residuals.

Independent probes: **19/19 PASS**. See `tooling/review/probes-adaptation-libkadaptor-2026-11-08/probe-results.json`.

---

## Checkpoint conditions (exact planned command)

Command (from package `PROPOSED-INSPECTION-COMMAND.txt`; do not add `--synthetic-fixture-mode`):

```
python3 /workspace/lg-tv/tooling/isolate_adaptation_phase.py \
  --outer "/workspace/lg-tv/source-catalog/archives/webOS 6.0 KLP_1.0_2.tar.gz" \
  --output-dir /workspace/lg-tv/source-catalog/inspection-adaptation-PENDING-REVIEW
```

This checkpoint can pass if, and only if, all of the following hold:

1. Output directory is fresh. Observed at review time (2026-11-08 06:35 Atlantic/Reykjavik): `inspection-adaptation-PENDING-REVIEW` **does not exist**. A rerun against a directory that already contains `phase.json`, `phase.md`, or `phase-failed.json` will mark `failed` and overwrite the old index (Important #1). Do not reuse the directory.
2. Full production pins stay closed: no `--synthetic-fixture-mode`, no ceiling flags (the CLI rejects them).
3. Isolation wrapper is used (the planned command). Hard ceilings: wall 120 s; `prlimit --as=1073741824` (VSZ, not RSS); `--cpu=120`; `--core=0`; `--nofile=64`; members 200000; pathname 100000000; expanded 4 GiB; outer compressed 512 MiB; outer decoded regular-logical 640 MiB; binary 128 MiB each and combined; admitted compressed 1 GiB; selected text 16 MiB / 64 MiB; disk observation ≥ 10 GiB.
4. Count success only if the launcher exits 0 **and** `phase.json` exists as a regular file with `ok: true`, `status: "ok"`, and `copied[0].verified_before_inner == true`. Treat a missing index, `partial`, `failed`, or timeout/OOM exit (124/137) as unsuccessful. Do not infer success from leftover `staged/` or `selected/` files.
5. The host must not rewrite the outer archive during the run. Observed without opening or hashing: the planned outer path exists, is a regular file, and is not a symlink. Size/hash were not re-checked against the catalog file (forbidden in this review); the tool itself will verify `511945894` / `95894dd8…` before parse.
6. Runtime fail-closed is possible if inner members that match the broad `build`/`config`/… selectors exceed the 16 MiB selected-text cap (Important #2). That is not a reason to raise ceilings.
7. Disk at review time: about 108.76 GiB free on `/workspace/lg-tv` (observed, not reserved), above the 10 GiB floor.

Production pin arithmetic (from hardcoded constants, not from reading the archive): target 123840909 < 134217728 binary cap; outer 511945894 < 536870912 compressed cap; admitted 511945894 + 123840909 = 635786803 < 1073741824.

---

### Strengths

- Outer open uses `O_NOFOLLOW`. Size and SHA-256 are verified in `verify()` (`adaptation_libkadaptor_phase.py:235-246`, called at `:463`) **before** `members()` opens the tar parser (`:251`). Probe `outer_hash_before_parse` / `outer_size_before_parse`: wrong hash or size → `ok=false`, parser call count 0.
- Only `info.name == TARGET_MEMBER` is staged (`:466`). Canonical match still requires the exact raw name and a regular file (`:275-279`). Duplicate canonicals fail (`:270-272`). Unallowlisted `soc/kernel.tar.gz` was not copied (probe `happy_copy_select_no_nested_no_other_packages`).
- `stage()` pre-checks size against the pin and the 128 MiB / admitted / expanded caps, creates the destination with `O_CREAT|O_EXCL|O_WRONLY|O_NOFOLLOW`, hashes while copying, fsyncs, and unlinks on failure (`:304-336`).
- Staged file is re-hashed through the same `O_NOFOLLOW` descriptor before the single inner inventory (`:342-350`). Probe `staged_rehash_before_inner`: after tampering the staged bytes, errors `['staged hash mismatch']` and the parser was called once (outer only). `verified_before_inner` is set only after that re-hash.
- Production `PhaseSpec` rejects any pin mutation unless `synthetic=True` (`:109-112`). CLI exposes only `--outer`, `--output-dir`, `--synthetic-fixture-mode` (`:493-498`). Probes: production and isolate CLIs return nonzero for `--expected-outer-sha256`, `--allow-test-spec`, `--min-free-disk-bytes`, `--wall-seconds`, and similar (this removes the CORE TWO outer-pin CLI footgun). `load_synthetic_spec` allows only fixture sizes/hashes plus optional `member`, which must equal `TARGET_MEMBER`.
- `consume()` reads `CHUNK_BYTES` (1 MiB) and buffers only when `text=True`. Unclaimed outer members call `consume(src)` with no writer (`:469`). Probe `unclaimed_payload_chunked_1mib`: 3 MiB unclaimed file, max `read()` size 1048576, phase still `ok`.
- Shared `_Phase` deadline and `totals` cover hash + copy + inner. `charge()` uses `>` (exact cap is allowed; an improvement vs the earlier inventory `>=` labeling). Production `PhaseLimits` and `CEILINGS` match the contract table; `for_tests` cannot raise any ceiling; production construction cannot drop the 10 GiB disk floor. Probe `ceilings_cannot_be_raised` including `iso.build_isolation_command(..., wall_seconds=121)`.
- Charging matches the contract: outer decoded for regular files only (`:286-287`); expanded = outer logical + staged copy chunks + inner logical + selected copies; admitted = outer file size + copied target chunks; binary each/combined checked before and during the copy.
- Path/link/type/duplicate policy is applied to every member. Nested inner archives are flagged `nested_archive_not_expanded` and not selected (`:294`, `:351`). Probe: `secret.txt` was not materialized; nested flag true.
- Fail-closed: `ok=true` is set only after `inner()` returns (`:474-476`). `PhasePartial` / `PhaseError` / `PathEscapeError` / `OSError` / tar/zlib errors set `ok=false` (`:477-483`). Unlike CORE TWO, `PathEscapeError` is in the except list.
- Isolation (`isolate_adaptation_phase.py`): `timeout --kill-after=5s 120` + `prlimit --as=1073741824 --cpu=120 --core=0 --nofile=64` + `bwrap --unshare-all --clearenv` (no `--share-net`). RO binds: `/usr`, the two tool files, and the outer file. Writable bind: output only. Held `O_NOFOLLOW` fds replace `--ro-bind` sources with `/proc/self/fd/N` through bwrap setup. Leaf symlink outer rejected (probe). No `/home`, `/root`, or `/cursor` in the command.
- Controls document residuals honestly (`:174-185`): `noexec_output_demonstrated=false`, selected mode `0644` is not a noexec mount, disk is an observation not a reservation, outer decoded is regular-file logical sizes only, PAX/GNU allocations precede semantic checks.
- `record_failed_phase` and collision handling write a failed index rather than crashing (contract: “recorded as status=failed (not an uncaught crash)”).

---

### Issues

#### Critical (Must Fix)

None. No write escape in the probes, no member execution, no false `ok=true`, no package retarget, no ceiling raise, no catalog access by this review.

#### Important (Should Fix; not automatically deployment-unsafe for the exact fresh command)

1. **Output index collision marks `failed` and then overwrites the old index**
   - File: `adaptation_libkadaptor_phase.py:451-454` then `_persist` (`:374-379` documents this; `:398-418` writes via `atomic_write_bytes` / `os.replace`).
   - Probe `index_collision_marks_failed_then_overwrites_old_index`: pre-existing `phase.json` containing `{"ok": true, ..., "kept": "previous-success-index"}` became a failed document with `errors=['output collision:phase.json']`; the previous success text was gone. Artifact: `probes-adaptation-libkadaptor-2026-11-08/probe-collision-overwritten-phase.json`.
   - Related path: if the child writes a successful index and the launcher later fails (`_write_log` disk check or JSON issues), `isolate_adaptation_phase.py:112-113` calls `record_failed_phase`, which can replace that successful index with a skeleton failure document.
   - Impact on the exact planned command: none, as long as `inspection-adaptation-PENDING-REVIEW` is created fresh (it does not exist now). General reuse of an output directory loses the previous index. Payload files created with `O_EXCL` are not overwritten; only the index is replaced.
   - Minimal fix: on collision write only `phase-failed.json` and leave an existing `phase.json` untouched; have the launcher refuse to start if index/launcher logs already exist; write launcher post-run failures to `launcher-failed.json` instead of replacing `phase.json`.

2. **Broad name selectors plus a hard stop on oversized candidates can abort a real inner inventory fail-closed**
   - File: `adaptation_libkadaptor_phase.py:145-158`, `:351-353`.
   - Independent check: `is_evidence_plaintext_name("build/libfoo.so")` is True; `"config.c"` and `"src/config.c"` are True; `"rapidjson.h"` is True because `"api"` is a substring of the basename (`rapid` + `api` + …). `"unrelated/private.h"` and `"scripts/run.sh"` are False.
   - A matching candidate larger than 16 MiB raises `PhasePartial` for the whole phase (`:352-353`) before NUL filtering. Combined selected text over 64 MiB does the same. This never yields `ok=true`; it can waste the production run if `libkadaptor` contains large build/config artifacts.
   - The contract does ask for README/build/config/license/manifest plus conservative hardware headers, and it does require stop-on-partial. This is therefore not a SPEC miss; it is a quality risk of over-selecting then hard-stopping.
   - Minimal fix (if parent wants fewer false partials without raising caps): skip and record oversized or non-text candidates (`reasons.append("oversize_not_selected")` / `"not_plaintext"`) instead of aborting; tighten `"api"` to a token match; restrict directory selectors to text-like suffixes or extensionless names.

3. **Some hard failures leave no failed index; external 120 s timeout equals the internal deadline**
   - File: `adaptation_libkadaptor_phase.py:480-481` (no `MemoryError`); `isolate_adaptation_phase.py:25` and `:94-106`.
   - `MemoryError` from an in-process allocation spike, or the outer `timeout 120` / `prlimit --cpu=120` killing the child before `_persist`, leaves no `phase.json`. The launcher then writes only `launcher-result.json` / stdout/stderr. This never produces `ok=true`. The internal deadline starts later than the external timer, so a wall stop under isolate is more likely to be an external kill than a recorded `partial`.
   - `_persist` also calls `phase.tick()` and catches `PhaseError`, and `PhasePartial` subclasses `PhaseError`, so an already-expired deadline can relabel a `partial` document to `failed` (Minor below).
   - Minimal fix: catch `MemoryError` (and preferably `BaseException` for the index write path); set the in-process deadline several seconds below the isolate timeout; if `phase.json` is missing after a nonzero child exit, write a failed index from the launcher without clobbering a successful one.

#### Minor

- `_persist` (`:381-386`) can downgrade `status` from `partial` to `failed` when `tick()` re-raises after a wall `PhasePartial`, and can duplicate the error string. Tests accept either status.
- Per-chunk `disk()` during staging (`:227`) will append on the order of ~118 observations for the 118 MiB target copy.
- `record_failed_phase` always embeds production `PhaseSpec()` pins (`:424-425`), even for synthetic CLI preflight failures.
- Launcher result hard-codes `timeout_wall_seconds=120` and `prlimit_as_bytes=1073741824` (`isolate_adaptation_phase.py:105`) rather than the values actually used (harmless while `main` cannot change them).
- Dead `kind == "metadata"` branch in `members()` (`:261-265`): CPython `tarfile.next()` consumes `x/g/L/K` internally.
- Archive-derived text in `phase.md` is unescaped (`:387-390`).
- Unclaimed payloads are still SHA-256’d (`:222`) even though that digest is discarded for non-targets (CPU only).
- Hardlink target classification still uses the member’s parent directory in the unchanged metadata helper (links are never followed). Not a new adaptation-phase defect; noted because this phase calls that helper.
- First `open_regular_nofollow` in `build_isolation_command` is closed before `main` reopens and holds the fd (short TOCTOU window on a replace-with-another-regular-file). Binding uses the held fd afterward.

---

### Residuals (honest limitations; not must-fixes)

- `noexec_output_demonstrated` is false; selected/staged mode `0644` is not a noexec mount.
- Address-space cap is `prlimit --as` (VSZ, not RSS) and is the backstop for PAX/GNU allocations inside `tarfile.next()` before semantic checks.
- Disk floor is observed, not reserved; space can drop between checks.
- `outer_decoded` counts logical sizes of regular file members only, not headers, padding, or the full decompressed stream.
- Leftover staged or selected files may remain after `ok=false`; consumers must consult `phase.json`.
- `--synthetic-fixture-mode` on the production binaries skips the outer filename/hash pins but cannot change the pinned member name, and the output records `synthetic_fixture_mode`.
- Host-side mutation of the outer file between hash and parse is still possible in theory; the same descriptor is used, and isolate binds it read-only into the sandbox.

---

## Claude Opus 5.5 usage (honest)

Invocation (this reviewer, 2026-11-08 06:23–06:27 Atlantic/Reykjavik):

```
claude -p "$(cat .../claude-prompt.md)" --model claude-opus-5-5 --effort high --output-format json
```

- Signed in: `claude.ai`, subscription type `max`, Claude Code 2.1.317.
- `~/.claude/settings.json`: `model=claude-opus-5-5`, `effortLevel=high`.
- CLI JSON (`claude-raw.json`): `is_error=false`, `stop_reason=end_turn`, `num_turns=12`, `duration_api_ms=243561`, session `aa1c213d-fa39-43f3-9894-29b33f1e0483`.
- `modelUsage["claude-opus-5-5"]`: canonical `claude-opus-5-5`; thinkingTokens **16257**; outputTokens 23137; cacheReadInputTokens 533044; cacheCreationInputTokens 88763; costUSD 1.2795248 (list basis). No web search.
- The result text said the harness ran at a “low reasoning-effort setting.” That self-report contradicts `--effort high`, `effortLevel=high`, and 16257 thinking tokens; both are recorded in `probes-adaptation-libkadaptor-2026-11-08/claude-metadata.json`.
- Four permission denials inside Claude Code: hashing/line-counting the tools, **reading the contract file** (outside Claude’s allowed directory for that session), and a host Python `tarfile` `stream=True` check. Claude therefore judged the 14 restated requirements rather than the plan file itself, and said so. This independent review did read the contract.
- Claude did not access catalog archives. Claude SPEC: PASS; QUALITY: PASS; checkpoint YES with freshness and `phase.json` conditions. Independent review agrees, with the collision-overwrite and selection-breadth items recorded as Important rather than must-fix for the exact fresh command.

Saved: `claude-prompt.md`, `claude-raw.json`, `claude-result.md`, `claude-stderr.txt` (empty), `claude-metadata.json`, `claude-metadata-start.json`.

---

## What this review did not do

- Did not hash, open, or parse `webOS 6.0 KLP_1.0_2.tar.gz` or any other catalog archive.
- Did not run the planned isolate command or create `inspection-adaptation-PENDING-REVIEW`.
- Did not edit production tooling, CORE TWO, or the metadata reader.
- Did not write a Page.
- Did not rerun the 139-test suite; existing green and independent-verify artifacts were read, and 19 new synthetic probes were executed instead.

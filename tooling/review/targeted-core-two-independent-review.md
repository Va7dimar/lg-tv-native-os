# Independent review: CORE TWO targeted phase tooling

Reviewed: 2026-11-08 05:16 Atlantic/Reykjavik (UTC+0)
Authority cited by parent: owner `t68u` / `Continue` (phase implementation already done; this is the promised review before originals).
Scope: local non-repo data-processing tool only. No LG/catalog archive was read, hashed, or parsed. No TV actions, installs, production edits, or Page writes. Prior reviews and probes were left in place.

This review is **not** permission to inspect archive2. Parent coordinates any real run after a clean review.

## Package and hashes

Review package: `tooling/review/targeted-core-two-2026-11-08/`
Contract: `docs/superpowers/plans/2026-11-08-targeted-core-two-phase.md`
Implementation report: `tooling/targeted-core-two-implementation-report.md`

Verified SHA-256 (production `cmp`-matched the versioned copies):

```
4b030684120c6366ffcaefcd9181f7b6d695ba2cdc46148d3318fe40f65992ce  tooling/targeted_core_two_phase.py
1cc90673cf34fc9e1fdb8ea535caa82b358ba4561169dec4e89c076fd4953ffb  tooling/isolate_targeted_phase.py
ee7870b95a6603fae3c38d5a9908da559c598fd29a7b69ba7c2b9a369473ae2c  tooling/bounded_archive_inventory.py  (unchanged)
eb289faf86523479944275918a2777cf23c429d2b96dd1a8822a2ead2f371915  tooling/isolate_inventory.py          (unchanged)
b8642f161667db1fb5daffff6a54416e657f55606adde55351e27ca267625f9d  tooling/tests/test_targeted_core_two_phase.py
13c1485f2a043cdb328e819a4a10c754a4eed57818b4716458dbb8ce2a328d75  docs/superpowers/plans/2026-11-08-targeted-core-two-phase.md
2c94ef5f6c975ae20a421ea71e41d633bbce94531132141c8de9417e008b857b  tooling/targeted-core-two-implementation-report.md
```

Method: contract + implementation report + source/launcher + packaged tests; existing red/green artifacts (not blindly rerun); new targeted synthetic probes under `tooling/review/probes-targeted-core-two-2026-11-08/`.

Test evidence (authoritative artifacts, not re-run here):
- `artifacts/red-core-two-phase.txt`: `Ran 23 tests` `FAILED (failures=16, errors=3)` (assertion-level red on a stub; four pins/guards passed by accident). One sparse test was added after that red file (implementer disclosed this).
- `artifacts/green-core-two-phase.txt`: `Ran 24 tests in 0.142s` `OK`
- `artifacts/green-core-two-full-suite.txt`: `Ran 85 tests in 0.277s` `OK` (24 new + 48 metadata + 13 prior regressions = 85)

---

## Verdict

| Gate | Result |
|---|---|
| SPEC | **PASS** |
| QUALITY | **PASS** |
| Blocking / must-fix | **None** for the exact planned isolated invocation with unchanged caps |
| Checkpoint (one exact production invocation, caps unchanged) | **YES, it can truthfully pass** — this is not itself permission to run |

The phase implements the written CORE TWO contract: closed kernel+bootcode allowlist, pinned outer/payload size+hash checks, staged re-hash before any inner parse, shared budgets with no per-package reset, one inner level, fail-closed stop, isolation wrapper, and honest noexec/AS/PAX/disk residuals. Two Important items are real and should be fixed when convenient; they do not produce a false `ok`, do not leak writes, and do not affect the planned command if parent uses the proposed pins and a fresh output directory.

Independent review does not enlarge scope (no libkadaptor, no Chromium/all-three retry, no ceiling increases).

---

### Strengths

- Production allowlist is exactly `soc/kernel-1.0.0-711..4.tar.gz` (170350960 / `110f0857…`) and `soc/bootcode-1.0.0-1099.7.tar.gz` (12014324 / `b88f252c…`). `libkadaptor` is named only as an exclusion. Probe `pins_and_ceilings` and `happy_path_copy_select_accounting` (`libk_copied=false`).
- Outer file is opened with `O_NOFOLLOW`, size-checked, bounded by 512 MiB, hashed with deadline checks **before** `open_untrusted_tar_gz`. Wrong outer hash: `errors=['outer hash mismatch']`, no `staged/`, no inners (probe `wrong_outer_hash_no_stage`).
- Copied payloads are SHA-256’d during copy against the pinned target; staged files are re-hashed (`_hash_path`) and `verified_before_inner=true` **before** `_inventory_inner` (lines 539-554; probe confirmed).
- Path/link/type/duplicate policy is applied to every outer member (not just targets). Unsafe links, devices, FIFOs, unsupported types, absolute/`..` names, and duplicate canonicals fail the phase. A symlink *target* matching an allowlisted name is a type mismatch (test + code 451-454).
- Shared `PhaseBudgets` object is used for outer scan/copy and both inners. Probe `shared_member_budget_no_reset`: `max_members=2` (exactly the two outer files) yielded `partial` / `max_members exceeded` and **zero** inners. Probe happy path: `outer_decoded` equaled the sum of *all* regular logical sizes including unclaimed `padding.bin` and libkadaptor (693=693). Staged copies (478) were added again to `expanded` (double-charge). Selected plaintext (51) was also added to `expanded`. `admitted_compressed_bytes` equaled outer file size + the two expected copy sizes.
- Nested inner `nested/extra.tar.gz` was listed with `nested_archive_not_expanded=true`; `secret.txt` was not materialized. `blob.bin` (NUL) was not selected; README/LICENSE were.
- First inner policy failure stopped the phase before the second inner (`stop_after_first_inner_fail`: only `kernel-…` in `inners`, status `failed`). Both binaries had already been staged (copy phase completed); the second package was not parsed.
- One 120 s deadline is created once (`clock() + limits.wall_seconds`) and used for outer hash, member loops, consumes, staged re-hash, and both inners. No per-package reset. Launcher wraps the **entire** phase with `timeout --kill-after=5s 120` and `prlimit --as=1073741824 --cpu=120`.
- Isolation command: `bwrap --unshare-all`, no `--share-net`, no `/home` `/root` `/cursor`, RO tool + helper + outer, writable output only. Leaf symlink outer rejected (`isolate_rejects_symlink_outer`). `noexec_output_demonstrated` remains `false` in phase controls and launcher result.
- Hard ceilings match the contract table and cannot be raised (`PhaseLimits` / `cli_cannot_raise_wall`). `--test-target` is ignored unless `--allow-test-spec` (CLI then still uses production `CORE_TWO_TARGETS`; small fixtures size-mismatch rather than succeed).
- Disk floor 10 GiB on production `PhaseLimits`; `for_tests` may lower it. Checks run before the phase, before each staged write, and before selected writes.
- Writes `phase.json` / `phase.md` only (does not overwrite a prior `inventory.json`). `ok=true` only via the final `_finish(..., "ok")` after both targets copied, both staged hashes matched, and both inners returned `ok`.
- Selected caps: 16 MiB per member (metadata-reader helper) and 64 MiB combined (probe `selected_combined_cap` → `partial`).
- Metadata reader hash history was not rewritten.

---

### Issues

#### Critical (Must Fix)

None. No write escape, no member execution, no false `ok=true` on the probed attacks, no allowlist swap without the explicit test flag, no ceiling increase.

#### Important (Should Fix; not blocking the exact planned command)

1. **Production CLI can replace the outer size/hash pin without `--allow-test-spec`**
   - File: `targeted_core_two_phase.py:738-757` (`spec_from_args`)
   - Probe `cli_spec_without_allow_test_spec`: with `allow_test_spec=False` and dummy `--test-target`, **targets stayed** the production kernel+bootcode pair (good), but `outer_bytes=123` and `outer_sha256="cd"*32` were accepted as the expected outer pin.
   - Why it matters: the contract says tests may substitute sizes/hashes only via an explicit test helper and that production defaults stay pinned. The planned invocation restates the correct pins on the CLI, so that one command behaves correctly. A different invocation could point `--outer` at another file and pass matching `--expected-outer-*` without `--allow-test-spec`. Payload allowlist hashes would still have to match, so this is provenance of the *rest* of archive2 (other members decoded against the 640 MiB cap), not a silent allowlist swap.
   - Minimal fix: if not `args.allow_test_spec`, require `expected_outer_bytes == OUTER_BYTES` and `expected_outer_sha256` equal to `OUTER_SHA256` (hex, case-insensitive) and ignore/reject `--test-target`. Keep `--allow-test-spec` as the only substitution path.

2. **Symlink `output/staged` is contained but not fail-closed as a phase document**
   - File: `_write_staged` (`320-331`) via `bai.contained_path`; `run_core_two_phase` / `main` (`769-782`) do not catch `bai.PathEscapeError` or `OSError`.
   - Probe `symlink_staged_outdir`: planted `out/staged -> outside`; result `PathEscapeError: path escapes output directory: ('staged',)`; **no files leaked** into `outside`; `phase.json` was **not** written.
   - Why it matters: containment worked (no escape). The phase did not persist `ok=false` / `status=failed` the way selected-write errors do in the metadata reader. A reused output directory with a hostile `staged` symlink would crash instead of recording a failed index. The planned output dir is a new `inspection-core-two-PENDING-REVIEW` path.
   - Minimal fix: catch `PathEscapeError` and `OSError` around staged/selected writes, append an error, `_finish(..., "failed")`. Same for `O_EXCL` collisions on a leftover staged filename.

#### Minor

1. **`skipped_inputs` is incomplete.** After a first-inner failure the second package is not parsed (good) but `skipped_inputs` stays `[]` (only the pre-inner timeout path appends it, line 542).
2. **Skip-path `_consume` materializes the whole member** (`334-347` always `chunks.append` + `join`, including discarded non-targets). Peak RAM can approach the largest skipped regular member (outer_decoded remainder after the two copies can be up to ~488 MiB on the production 640 MiB cap) plus Python overhead, against a 1 GiB VSZ limit. Isolation AS is the backstop; stream-discarding unused payloads would reduce kill risk. Not a false-`ok` bug.
3. **Tar headers and end-of-archive zero blocks are not counted in `outer_decoded_bytes`.** The written contract asks for logical regular-member sizes; unclaimed *file* payloads *are* charged (probe). Header/padding/EOA bytes are not. That matches the contract table, not a full decompressed-tar-stream meter.
4. **Exact member-cap labeling** can still mark `partial` after completing exactly `max_members` members (`members >= max` at loop top), as in the prior metadata-reader residual. Fail-closed; production cap is 200000.
5. **Evidence names match any path component** in `EVIDENCE_EXACT` (so `board/anything` or `build/anything` NUL-free and under 16 MiB can be selected). This matches the unit tests (`board/platform.h`). ELF-like binaries under those dirs usually contain NUL and are rejected.
6. **`_consume` wall status on skip paths is ignored**; the next loop iteration still sees the global deadline and stops. Harmless.

---

### Known residuals (limitations, not automatically must-fix)

These match the contract and implementation report and remain true:

- **`noexec_output_demonstrated: false`.** Staged/selected mode `0644` is not a noexec mount; this tool never executes archive bytes. Output FS may still be executable.
- **`prlimit --as` is VSZ, not RSS / cgroup `memory.max`.**
- **CPython `tarfile.next()` allocates PAX/GNU extended headers before semantic caps.** The backstop is mandatory `isolate_targeted_phase.py` (1 GiB AS + 120 s wall) for any untrusted/catalog input.
- **Disk checks observe free space** before the phase and before writes; they do not reserve space.
- A later successful inner inventory still would not prove BSP compatibility, a boot route, recovery, or a replacement OS.
- Phase-expanded accounting double-charges copies as specified; a real archive2 run may still not fit unknown logical expansion inside 4 GiB / 640 MiB. Limits were not softened.

---

### Checkpoint: one exact production invocation

Planned command (from the package; **not executed** by this reviewer):

```
python3 /workspace/lg-tv/tooling/isolate_targeted_phase.py \
  --outer "/workspace/lg-tv/source-catalog/archives/webOS 6.0 KLP_1.0_2.tar.gz" \
  --output-dir /workspace/lg-tv/source-catalog/inspection-core-two-PENDING-REVIEW \
  --expected-outer-bytes 511945894 \
  --expected-outer-sha256 95894dd81e2bb32fd1ced1eb119698f2e1464e6b9b5b5879ea51528d7d5e8832
```

That command does not pass `--allow-test-spec`, does not raise caps, and restates the hardcoded outer pin. Under those conditions the tool will: verify the outer regular file’s size and SHA-256 before listing; copy only the two pinned members after payload size+hash match; re-hash staged files before each inner parse; inventory each staged package one level; select NUL-free evidence plaintext within 16 MiB / 64 MiB; share member/pathname/expanded/selected/wall budgets; stop the whole phase on failed/partial; and wrap the run in 1 GiB AS + 120 s timeout without home/net/credential binds.

**Checkpoint can truthfully pass** for that invocation. Parent must still explicitly hand off the real inspection. Do not treat this file as that handoff.

Strong guarantees: closed two-member allowlist; outer and payload hash/size pins (when CLI values match constants); no inner recursion; no libkadaptor copy; shared fail-closed budgets; containment on resolve (no leak in the planted-symlink probe); atomic `phase.json`/`phase.md` on normal completion and on handled errors.

Limitations that travel with a pass: see residuals above, plus Important #1–#2 if the CLI pins or output directory are not the planned ones.

---

### Probe artifacts

`tooling/review/probes-targeted-core-two-2026-11-08/probe-results.json` and `probe-results.md`. No catalog filenames were used as inputs.

Prior independent reviews remain at `tooling/review/independent-review.md` and `tooling/review/re-review-2026-11-08.md`.

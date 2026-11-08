# Independent re-review: SDK launcher stdio hardening

Reviewed: 2026-11-08 07:08 Atlantic/Reykjavik (UTC+0)
Authority cited by parent: ongoing owner off-TV technical re-review (no owner checkpoint; no policy/ceiling changes).
Scope: launcher stdio-hardening package `tooling/review/sdk-stdio-fix-2026-11-08/`, started from `10-HOST-VERIFICATION-ADDENDUM.md`. No SDK/candidate asset contents were read, hashed, or parsed. No production command, installer execution, TV action, or Page write.

Previous reviews remain immutable:
- `tooling/review/sdk-inventory-independent-review.md` SHA256 `57ac2f23882d603db7304a4ea7dd95c2579fa6f2c8e213535f20aefb67d5edb4` — V1 SPEC FAIL / QUALITY PASS for launcher `488e34d3…f7f0` (inherited-fd leak).
- `tooling/review/sdk-fd-fix-independent-review.md` SHA256 `2acda00ef7d41373f5ad2fcb9173c9f18a04cfd42f932d69809219c990e7312b` — FD≥3 SPEC PASS / QUALITY PASS for launcher `35b6dd2c…4771`, with Important closed-stdin fd-0 alias caveat.
- `tooling/review/adaptation-libkadaptor-independent-review.md` SHA256 `56846d707fd55b5bc1637daf591b61b0bc4ae49383c61c22bd7632b7b5296006` (unchanged).

This document reviews the new launcher hash only. It does not rewrite those verdicts.

Primary analysis: subscribed Claude Opus 5.5 HIGH. Independent probes and the full synthetic SDK test suite were run here; Claude permission denials were not worked around.

---

## Package and hashes

```
2a6638e3439748a6dc4fb7237a03c3d05521685746df5315683c861acab9ca52  tooling/isolate_sdk_inventory.py
c04fe95faf8346741d18de8cdef4814beb520d47d079d7f1a702997ca026fd7f  tooling/sdk_inventory_phase.py
aaba6c1cc6fd799c02ea62d2a0a3b8103790af97bd6a4dea7a0c6496d48f0ba0  tooling/tests/test_sdk_inventory_phase.py
f0b0e69c9b69b4e2122494b0104a791b108009b15b20dfc7a26d2d951126bd10  tooling/tests/test_sdk_fd_boundary.py
15fe10e33a5c49c3fa879c0e5dda2b56e9f15d77caabcdd3de25f3c253ddf065  tooling/tests/test_sdk_stdio_boundary.py
35b6dd2c2187df8e6e9a5774befa63f2217e89b62c3f149747815d1952084771  before/isolate_sdk_inventory.py (FD-fix baseline)
```

Live launcher, reader, and new stdio tests `cmp`-match `current/` snapshots and `05-CODE-SHA256SUMS.txt`. Reader is byte-identical to V1 (`c04fe95f…fd7f`); `04-sdk_inventory_phase.py.diff` is empty. Original 27-test module and FD-boundary tests are unchanged. Bootstrap `/proc/self/fd` cleanup is unchanged from the FD-fix launcher. Production delta is `import errno`, `_normalize_stdio()` (`isolate_sdk_inventory.py:104-117`), the call before `fresh_output` (`:123`), and `stdin=subprocess.DEVNULL` (`:152`).

Preserved RED (not relabelled): `02-HOST-FOCUSED-RED.txt` (7/7 FAIL before the change on the FD-fix launcher). Nested Codex `NETLINK_ROUTE` skips remain in nested logs and are not counted as passes. Host self-verification `09-HOST-GREEN.txt` (35/35 OK, 1.879s) is evidence, not this independent verdict.

---

## Verdict

| Gate | Result |
|---|---|
| SPEC | **PASS** (closed-stdio fd-0 alias from the FD-fix review is closed; inherited fds ≥ 3 remain closed) |
| QUALITY | **PASS** |
| Blocking must-fix | **None** |
| Important remaining | **None** for the reviewed stdio defect |

`_normalize_stdio()` fills any closed fd in 0–2 with `/dev/null` (only `EBADF` from `fstat` triggers replacement; other errors raise) before `fresh_output` / `open_regular`, so bind fds allocate at ≥ 3. The worker is spawned with `stdin=subprocess.DEVNULL`, so worker fd 0 is `/dev/null` even if the caller left stdin closed or pointed elsewhere. Intended launcher stdout/stderr log files on fds 1–2 are leftover by design, not an escape. The ≥ 3 `/proc` cleanup is unchanged and still fail-closed (`RuntimeError('inherited descriptor survived cleanup')` before reader import).

---

### Independent verification

Probes (synthetic only) under `tooling/review/probes-sdk-stdio-fix-2026-11-08/`:

- `all_seven_closed_stdio_masks`: masks 1–7 all `ok=true`, `exit=0`; worker audit `0=/dev/null`; fds 1/2 are `stdio-output/launcher-{stdout,stderr}.txt` (not input or output-dir paths). Saved `indep-seven-masks.json`.
- `production_depth_closed_stdin_no_fd0_alias` (mask 1): temp tree mirroring production path depth under `/tmp/.../workspace/lg-tv/sdk-candidates/20191125/...` (no real asset files). After `launch()`, worker fd 0 is `/dev/null`, not the synthetic assets path. Saved `indep-production-depth-mask1.json`.
- `production_depth_all_stdio_closed_mask7`: same depth tree, all of 0–2 closed first; fd 0 is `/dev/null`; fds 1/2 are the intended inspection-metadata log files.
- `normalize_before_allocation_and_devnull_stdin`: source-order check that `_normalize_stdio` runs before `fresh_output`/`open_regular` and that `subprocess.run` sets `stdin=DEVNULL`.
- `hashes_and_prior_reviews`: live hashes match claims; prior independent review files untouched.

Full synthetic suite rerun here: `python3 -B -m unittest discover -s tooling/tests -p 'test_sdk*.py' -v` → `Ran 35 tests in 1.745s` `OK` (`indep-full-suite.txt`, SUITE_EXIT 0). Includes all seven FD-boundary tests (normal/high inherited-fd closure and fail-closed incomplete/close/enumeration errors) plus `test_all_seven_closed_stdio_combinations`.

Host-green evidence agrees: `host-stdio-green/mask-1.json` … `mask-7.json` all `ok=true` with `audit[0]=/dev/null`; `host-fd-green/normal.json` passed fds `[3,4,5,6]` → `inherited=[]`, `parent_walk=[]`, `writable_reopens=[]`, `closed=[3,4,5,6]`; `high.json` passed `[256,257,5,6]` likewise closed (256/257 above sandbox `--nofile=64`). RED `red-evidence/mask-*.json` still show the pre-fix failures and were not modified.

No parent-directory escape via leftover host fds and no writable reopen of host inputs were observed on these synthetic launches.

---

### Strengths

- `_normalize_stdio` (`isolate_sdk_inventory.py:104-117`) replaces only `EBADF` slots; opens `/dev/null` `O_RDWR`; `dup2`/`close` if `open` does not return `n`; leaves already-open 0–2 alone.
- Call order (`:123` before `:124` / `:137`) prevents output-dir and input fds from landing on 0–2 where worker `dup2` or cleanup-skip would alias them. This is the FD-fix Important item.
- Worker `stdin=subprocess.DEVNULL` (`:152`) plus explicit stdout/stderr log handles (`:153-154`) make worker stdio independent of the caller's closed or redirected 0–2.
- Bootstrap cleanup (`:69-83`) unchanged; high fds 256/257 still close; fail-closed paths still stop before reader import.
- `test_sdk_stdio_boundary.py` drives a real `launch()` from a child that closes the selected mask, injects a pre-import fd 0–2 audit, and asserts fd 0 is `/dev/null` and that no stdio target equals an input or the output directory. Skip is tightened to `NETLINK_ROUTE` + `EPERM` (not a blanket bind-error skip).

---

### Issues

#### Critical

None.

#### Important

None.

#### Minor

- No unit test for a non-`EBADF` `fstat` error on fds 0–2 (coverage only; the raise path is straightforward).
- In a single-threaded launcher, `open("/dev/null")` should already return the closed slot, so the `dup2` branch is a race safety net.
- Stdio tests compare audit paths as exact strings against unresolved fixture paths; a symlink-backed temp root could weaken the negative alias check. This host uses `/tmp` real paths.
- Fds 1/2 are asserted only negatively (not an input/output-dir). Host and independent audits show they are the intended launcher log files.
- `launch()` leaves `/dev/null` in any previously closed caller slots 0–2. Harmless for the CLI; library callers should know. If the caller had closed stdout, `main()` summary JSON would go to `/dev/null`; `launcher-result.json` remains the record.
- If `/dev/null` cannot be opened, `launch` fails before creating the output directory / result file (fail-closed, no record).
- No concurrency guarantee against another thread in the launcher process closing fds during allocation (stated context is a single-threaded trusted launcher).

---

### Residuals (unchanged, outside this fix)

- XZ `CHECK_NONE` can still be labelled `integrity_eof`; full-file pin is unchanged.
- Absolute symlink targets still fail the whole phase.
- AS is VSZ not RSS; `noexec=false`; disk floor is observed not reserved; conservative metadata charging; 120 s / 200k / 100 MB / 4+4 GiB one-shot stop.
- Passing 35 synthetic tests is not an actual SDK inventory and does not prove SDK compatibility, TV identity, or boot/recovery. The production METADATAONLY command was not run.
- The V1 SPEC FAIL review remains the record for hash `488e34d3…f7f0`. The FD-fix review remains the record for hash `35b6dd2c…4771`, including its now-addressed caveat.

---

## Claude Opus 5.5 usage (honest)

Invocation 2026-11-08 07:05–07:07 Atlantic/Reykjavik, cwd `/workspace/lg-tv`:

`claude -p ... --model claude-opus-5-5 --effort high --output-format json`

Raw: `tooling/review/probes-sdk-stdio-fix-2026-11-08/claude-raw.json` (prompt `claude-prompt.md`).

- CLI JSON: `is_error=false`, `subtype=success`, `stop_reason=end_turn`, `num_turns=10`, `duration_api_ms=91557`, `duration_ms=91986`, session `c4e2e305-1858-4c81-8a54-bdeecc70fbb3`.
- `modelUsage["claude-opus-5-5"]`: canonicalModel `claude-opus-5-5`, provider `firstParty`; thinkingTokens **3493**; outputTokens 8036; inputTokens 18; cacheReadInputTokens 509873; cacheCreationInputTokens 66703; costUSD 0.7963906 list. No web search. `fast_mode_state=off`.
- Result prose said effort was “the session's default effort” and that the serving route could not be independently confirmed. The invocation used `--effort high`; the JSON has no separate effort field. Both the request and that self-report are recorded (same class of mismatch noted in the FD-fix review).
- Permission denials (not worked around): one Bash inspection of `09-HOST-GREEN.txt` / `host-stdio-green` / `host-fd-green` (`toolu_01JwiLcMxL2FMtzdogZSx81N`). Claude reported using `grep` on the same evidence instead. This review independently re-read those JSON files and reran the seven masks.
- Claude verdict: SPEC PASS, QUALITY PASS, no must-fix, hashes match, did not access `sdk-candidates` contents. Independent review agrees after reproducing all seven masks and the production-depth closed-stdin case.

---

## What this review did not do

- Did not open, hash, or parse real files under `/workspace/lg-tv/sdk-candidates/`.
- Did not execute the proposed production METADATAONLY command.
- Did not edit production tooling or rewrite prior independent reviews / original RED logs.
- Did not write a Page.
- Did not change isolation policy or resource ceilings.

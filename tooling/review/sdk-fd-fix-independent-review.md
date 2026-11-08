# Independent re-review: SDK launcher FD-containment fix

Reviewed: 2026-11-08 07:02 Atlantic/Reykjavik (UTC+0)
Authority cited by parent: owner `t71u` / `t74u` (already-authorized off-TV technical re-review; no owner checkpoint).
Scope: launcher-only FD fix. No SDK/candidate asset contents were read, hashed, or parsed. No production command, installer execution, TV action, or Page write.

The V1 independent review remains immutable:
`tooling/review/sdk-inventory-independent-review.md` SHA256 `57ac2f23882d603db7304a4ea7dd95c2579fa6f2c8e213535f20aefb67d5edb4` (unchanged).
That document stays SPEC FAIL / QUALITY PASS for launcher `488e34d3…f7f0`. This document reviews the new launcher hash only.

Primary analysis: subscribed Claude Opus 5.5 HIGH. Independent probes and the targeted synthetic suite were run here; Claude permission denials were not worked around.

Started from `tooling/review/sdk-fd-fix-2026-11-08/09-HOST-VERIFICATION-ADDENDUM.md`.

## Package and hashes

```
35b6dd2c2187df8e6e9a5774befa63f2217e89b62c3f149747815d1952084771  tooling/isolate_sdk_inventory.py
c04fe95faf8346741d18de8cdef4814beb520d47d079d7f1a702997ca026fd7f  tooling/sdk_inventory_phase.py
aaba6c1cc6fd799c02ea62d2a0a3b8103790af97bd6a4dea7a0c6496d48f0ba0  tooling/tests/test_sdk_inventory_phase.py
f0b0e69c9b69b4e2122494b0104a791b108009b15b20dfc7a26d2d951126bd10  tooling/tests/test_sdk_fd_boundary.py
488e34d3470403206c0974cc82cdd36f7a6078619aaabf0bda390e3ea040f7f0  v1/isolate_sdk_inventory.py (preserved)
```

Live files `cmp`-match `current/` snapshots. Reader is byte-identical to V1. Original 27-test module hash unchanged. All `SHA256SUMS-FIX.txt` entries OK. Production delta is the 20-line `_bootstrap` hunk in `05-launcher-vs-V1.diff` (`isolate_sdk_inventory.py:64-84`).

Preserved RED (not relabelled): `02-host-focused-RED.txt` (2/2 FAIL on V1: normal fds 3–6 and high 256/257 leaked; parent walk and writable reopen). Nested Codex `NETLINK_ROUTE` skips remain in logs 03–04. Host self-verification 08: 34/34 OK is not this independent verdict.

---

## Verdict

| Gate | Result |
|---|---|
| SPEC | **PASS** (V1 inherited-fd ≥ 3 leak, including fds above `nofile=64`, is closed) |
| QUALITY | **PASS** |
| Blocking must-fix | **None** for the reviewed V1 defect |
| Important remaining | Closed-stdin can alias a host input onto fd 0, which cleanup intentionally skips |

The advertised fix works: after bwrap bind setup, the trusted bootstrap enumerates `/proc/self/fd`, closes every descriptor ≥ 3 (no `closerange(3,64)` ceiling), re-enumerates, and raises `RuntimeError('inherited descriptor survived cleanup')` before importing the reader. Fresh `/output` and `/input/*` opens are then legitimate sandbox fds.

---

### Independent verification

Probes (synthetic only) under `tooling/review/probes-sdk-fd-fix-2026-11-08/`:

- `normal-fds`: passed fds `[3,4,5,6]` all EBADF after cleanup; `inherited=[]`; `parent_walk=[]`; `writable_reopens=[]`; `fresh_output_parent_marker=false`; `fresh_input_writable=[]`; path RO; home hidden; three-input synthetic manifest `ok=true`.
- `high-fds`: passed fds `[256,257,5,6]` likewise closed (256/257 above sandbox `--nofile=64`).
- `legitimate_synthetic_isolation_launch`: `isolate.launch(..., synthetic_probe=True)` `ok=true`; home hidden; input path readonly; distinct net ns; `selected_bytes=0`.
- `incomplete_cleanup_stops_before_reader`: sabotaged `os.close=lambda fd: None` → `RuntimeError: inherited descriptor survived cleanup`; `READER_REACHED` not printed.
- `hashes_match_claims` including the immutable V1 review hash.

Targeted suite rerun here: `python3 -B -m unittest discover -s tooling/tests -p 'test_sdk*.py' -v` → `Ran 34 tests in 0.863s` `OK` (`indep-full-suite.txt`). Matches host log 08.

Host-green-evidence `normal.json` / `high.json` agree with the independent normal/high probes. RED evidence `red-evidence/normal.json` and `high.json` still show the V1 leak and were not modified.

---

### Strengths

- Cleanup uses `/proc/self/fd` enumeration rather than `os.closerange(3, 64)`, so inherited fds above `prlimit --nofile=64` are closed (`isolate_sdk_inventory.py:68-81`). High-fd probe confirms 256/257 become EBADF.
- Only `EBADF` is tolerated; other close/fstat/listdir errors and survivors fail closed before `import sdk_inventory_phase`.
- Transient listdir directory fd is already closed when the snapshot is processed, so its number surfaces as EBADF (handled).
- Reader import and `directory_fd("/output")` happen after verification; later inventory descriptors are expected and do not restore host parent walk (`HOST_PARENT_SENTINEL` unreachable from a fresh `/output` fd).
- Sandbox path RO (`/input/sdk` O_WRONLY fails) and home/root hidden remain true on successful isolation.
- No parser, pin, CLI, ceiling, XZ-check, or symlink-policy change. `build_command` / `launch` / `main` bodies are unchanged aside from the bootstrap string.

---

### Issues

#### Critical

None.

#### Important (not a V1-regression fail; recommended before an actual METADATAONLY run)

**Closed stdin can place a host input on fd 0, which cleanup skips**

- Locations: `isolate_sdk_inventory.py:71` and `:77` (`if n<3: continue`); `launch` `:115-117` (`subprocess.run` without `stdin=`); lowest-fd allocation in `sdk_inventory_phase.directory_fd` / `open_regular`.
- Independent synthetic repro: `probes-sdk-fd-fix-2026-11-08/probe-closed-stdin-fd0.json` (temp tree mirroring production path depth: `.../workspace/lg-tv/sdk-candidates/20191125/assets/...`; no real asset files). Child closed fd 0 then called `launch()`. After bootstrap cleanup, worker fd 0 targeted the synthetic SDK input path and `/proc/self/fd/0` reopened `O_WRONLY` (`writable: true`). Parent walk via fd 0 failed only because that fd was a file, not a directory (`[Errno 20] Not a directory`).
- This is the V1 writable-reopen class on fd 0. It requires the launcher process to start with stdin closed (common in some automation; not the default interactive shell, where fd 0 is a tty). `</dev/null` *opens* fd 0 and avoids the hole; `0<&-` triggers it. Claude derived the same issue from code; their runtime probe was permission-denied and not worked around.
- Minimal hardening: `stdin=subprocess.DEVNULL` on the worker `subprocess.run`, and before `fresh_output`/`open_regular` ensure fds 0–2 are open (open `/dev/null` into any closed slot) or fail if a passed bind fd is `< 3`. Add a `launch()` regression with stdin closed. No parser/policy/ceiling change.

#### Minor

- Boundary tests drive `build_command` + `subprocess.run`, not `launch()`, so stdin handling on the real spawn path is untested.
- Inherited stdin/stdout/stderr (when they are a tty or orchestrator pipes) remain reachable; `--new-session` reduces TIOCSTI risk. This matches the original “keep 0–2” exception.
- `/proc/self/fd` is assumed genuine; a missing procfs fails closed. Asserting that 0/1/2 appear in the first listing would be cheap insurance.

---

### Residuals (unchanged, outside this fix)

- XZ `CHECK_NONE` can still be labelled `integrity_eof`; full-file pin is unchanged.
- Absolute symlink targets still fail the whole phase.
- AS is VSZ not RSS; `noexec=false`; disk floor is observed not reserved; conservative metadata charging; 120 s / 200k / 100 MB / 4+4 GiB one-shot stop.
- Passing 34 synthetic tests is not an actual SDK inventory and does not prove SDK compatibility, TV identity, or boot/recovery.
- The V1 SPEC FAIL review remains the record for hash `488e34d3…f7f0`.

---

## Claude Opus 5.5 usage (honest)

Invocation 2026-11-08 06:54–06:58 Atlantic/Reykjavik, cwd `/workspace/lg-tv`, default permissions:

`claude -p ... --model claude-opus-5-5 --effort high --output-format json`

- Signed in: `claude.ai`, subscription `max`, Claude Code 2.1.317.
- settings.json: `model=claude-opus-5-5`, `effortLevel=high`.
- CLI JSON: `is_error=false`, `num_turns=18`, `duration_api_ms=208466`, session `ceeb97b9-90ae-4bbf-8e4e-bbc14f80030d`.
- `claude-opus-5-5`: thinkingTokens **11831**; outputTokens 19555; cacheRead 787216; cacheCreate 81008; costUSD 1.1966952 list. No web search.
- Result prose said the harness did not name an effort level and that the reasoning budget was small. That contradicts `--effort high` and 11831 thinking tokens; both are recorded.
- Permission denials (not worked around): Bash cat of evidence files; a `/tmp` synthetic fd-0 probe; Write of that probe script. Claude therefore did not reproduce the fd-0 case; this review did, independently, with synthetic paths.
- Claude verdict: SPEC PASS (with stdin-open condition), QUALITY PASS, no blocking must-fix, recommended `stdin=DEVNULL` / refuse passed fds `< 3`. Independent review agrees after reproducing the edge case.
- Claude did not access `sdk-candidates` asset contents.

---

## What this review did not do

- Did not open, hash, or parse real files under `/workspace/lg-tv/sdk-candidates/`.
- Did not execute the proposed production METADATAONLY command.
- Did not edit production tooling or rewrite the V1 FAIL review / original RED logs.
- Did not write a Page.

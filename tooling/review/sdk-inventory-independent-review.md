# Independent review: SDK metadata-only inventory tooling

Reviewed: 2026-11-08 06:48 Atlantic/Reykjavik (UTC+0)
Authority cited by parent: owner `t71u` (off-TV autonomy) and `t74u` (subscription-cost priority).
Scope: local non-repo data-processing tool only. No SDK/candidate asset contents were read, hashed, or parsed. No installer/source execution, TV actions, production edits, or Page writes. Prior reviews remain immutable.

This review is technical criterion, not permission to run the planned METADATAONLY command. Parent coordinates any actual-run handoff.

Primary whole-code/spec analysis was requested from subscribed Claude Opus 5.5 HIGH. This document is the independent validation (contract + code + packaged artifacts + new synthetic probes), cross-checked against that Claude run. Denied Claude reads were not worked around; coverage gaps are recorded.

The orchestrator verification addendum was read first: host 27/27 PASS including synthetic bwrap isolation evidence (log 16), with earlier Codex nested-sandbox bwrap `NETLINK_ROUTE EPERM` failures preserved in logs 01–14 and not relabelled success.

## Package and hashes

Review package: `tooling/review/sdk-inventory-2026-11-08/`
Contract: `tooling/review/sdk-inventory-2026-11-08/sdk-static-inventory-contract.md`
Requirements: `tooling/review/sdk-inventory-2026-11-08/sdk-static-inventory-reader-requirements.md`

All 34 `SHA256SUMS.txt` entries verified OK against the package files. Live production files `cmp`-match the package copies:

```
c04fe95faf8346741d18de8cdef4814beb520d47d079d7f1a702997ca026fd7f  tooling/sdk_inventory_phase.py
488e34d3470403206c0974cc82cdd36f7a6078619aaabf0bda390e3ea040f7f0  tooling/isolate_sdk_inventory.py
aaba6c1cc6fd799c02ea62d2a0a3b8103790af97bd6a4dea7a0c6496d48f0ba0  tooling/tests/test_sdk_inventory_phase.py
ee7870b95a6603fae3c38d5a9908da559c598fd29a7b69ba7c2b9a369473ae2c  tooling/bounded_archive_inventory.py  (unchanged)
eb289faf86523479944275918a2777cf23c429d2b96dd1a8822a2ead2f371915  tooling/isolate_inventory.py          (unchanged)
4b030684120c6366ffcaefcd9181f7b6d695ba2cdc46148d3318fe40f65992ce  tooling/targeted_core_two_phase.py    (unchanged)
1cc90673cf34fc9e1fdb8ea535caa82b358ba4561169dec4e89c076fd4953ffb  tooling/isolate_targeted_phase.py     (unchanged)
7884236467e1533de7e3ac1266c602845cee35f4acbda11612d7e01dd36842c2  tooling/adaptation_libkadaptor_phase.py (unchanged)
192dce045e47c30379e35e66584f6d21b584ecf6418a9729d1d334777730e55b  tooling/isolate_adaptation_phase.py     (unchanged)
```

`protected-before.json` and `protected-after.json` are identical (metadata helper hashes unchanged).

Test evidence (artifacts read, suite not blindly rerun here):

- `01-red.txt` / `02-behavior-red.txt`: missing module then scaffold red (16 tests, failures/errors).
- Intermediate reds preserved: `04`, `07`, `08` (filename historically “green” but actually failed — implementer disclosed), `12` (`-I` import).
- `06-synthetic-isolation-evidence.txt`: Codex nested sandbox `bwrap: loopback: Failed to create NETLINK_ROUTE socket: Operation not permitted`; worker never started; manifests `ok=false`. Not relabelled success.
- `13-final-green.txt` / `14-final-green.txt`: 27 tests, 26 passed + 1 blocked skip in that sandbox.
- `15-orchestrator-targeted-verification.txt`: ordinary host runtime `Ran 27 tests in 0.506s` `OK`, exit 0, 0 skips.
- `16-host-synthetic-isolation-evidence.json`: synthetic three-input isolation `ok=true`; `home_hidden`, `input_readonly`, distinct net ns, loopback unavailable; totals `members=3`, `logical_regular_bytes=15`, `decoded_bytes=30720`, `selected_bytes=0`.
- `17-production-metadata-only-preflight.json`: lstat/statvfs only; proposed output absent; no asset rehash.
- `11-runtime-versions.txt`: Python 3.13.5, bwrap 0.12.0, prlimit 2.41.5, GNU timeout 9.7.

Independent synthetic probes: 22/22 PASS after correcting one false-positive substring check on the isolation command (parent directory is not itself an argv bind). Additional fd-leak probe: CONFIRMED (must-fix below). Artifacts under `tooling/review/probes-sdk-inventory-2026-11-08/`.

---

## Verdict

| Gate | Result |
|---|---|
| SPEC | **FAIL** (narrow: isolation containment / RO-input claims; pin/parse/budget/EOF items pass) |
| QUALITY | **PASS** (parser, pins, hooks, counters, fail-closed metadata path are careful) |
| Blocking / must-fix | **Yes** — inherited host file descriptors remain usable inside the worker |
| Checkpoint (exact planned METADATAONLY command) | **NO** for these hashes, until the must-fix is applied and re-probed |

Parser/pin/stream/hook behavior meets the written metadata contract. Isolation as actually launched does not: `pass_fds` leaves the host output-directory fd and the three input fds inherited into the sandbox worker, and those fds bypass the bind-mount RO/containment story. That is in scope because isolation exists to contain untrusted archive parsing.

---

## Must-fix (concrete repro)

**Inherited host fds leak through `pass_fds` into the bwrap worker**

- Location: `isolate_sdk_inventory.py:106-117` (`pass_fds=tuple([outfd] + input fds)`), `_bootstrap` at `:64-81` (never closes inherited fds), binds via `/proc/self/fd/N` at `:42-45` and `:106-107`.
- Independent probe: `probes-sdk-inventory-2026-11-08/probe-inherited-fds.json` (synthetic tempfile fixtures only; no `sdk-candidates` assets).
- Observed inside the worker:
  - fd 4 → host output directory (`.../out`)
  - fds 5–7 → host input files
  - `openat(fd4, "..")` listed the host parent (`in-0`, `in-1`, `in-2`, `out`)
  - `os.open("/proc/self/fd/{5,6,7}", O_WRONLY)` succeeded (`writable: true`)
- Why it matters: for the planned command the output directory’s parent is `sdk-candidates/20191125/`, which contains `assets/`. A worker that gained unexpected code execution (the reason untrusted inputs are sandboxed) could walk host directories via the inherited output dir fd, including toward `$HOME`, and could reopen the already-open asset fds writable, bypassing `--ro-bind`. The existing isolation probe only checks path existence (`/home`, `/input/sdk` O_WRONLY) and therefore overstates RO/hidden-home.
- The intended metadata worker never performs these operations; this is not a demonstrated write during a normal parse. It is still a contract miss for RO inputs and containment.
- Expected minimal fix: at the start of the bootstrap, before importing/using the tool, close inherited fds (for example `os.closerange(3, 64)`), then open `/output` freshly inside the sandbox; or switch to bwrap `--ro-bind-fd`/`--bind-fd` and ensure unused fds are not inherited. Extend the synthetic isolation probe to assert `/proc/self/fd` contains only stdin/stdout/stderr plus fds the worker itself opened, that `openat(..., "..")` on leftover dir fds is impossible, and that `/proc/self/fd/N` reopen-write of inputs fails.
- Expected outcome after fix: rerun this fd probe (no parent listing via inherited dir fd; no writable reopen); rerun the targeted 27-test host suite; re-hash.

---

## Checkpoint conditions (after the must-fix)

Exact unexecuted command (`proposed-metadataonly-command.txt`):

```
/usr/bin/python3 -I -B /workspace/lg-tv/tooling/isolate_sdk_inventory.py \
  --sdk /workspace/lg-tv/sdk-candidates/20191125/assets/starfish-sdk-x86_64-ca9v1-toolchain-5.0.0-20191125.sh \
  --native /workspace/lg-tv/sdk-candidates/20191125/assets/native_sysroot_dependencies.tar.gz \
  --target /workspace/lg-tv/sdk-candidates/20191125/assets/target_sysroot_dependencies.tar.gz \
  --output-dir /workspace/lg-tv/sdk-candidates/20191125/inspection-metadata-PENDING-REVIEW
```

After a reviewed fd-close delta, the command can pass a checkpoint if:

1. Output path remains absent (observed 2026-11-08 06:48 Atlantic/Reykjavik: does not exist and is not a dangling symlink). Do not reuse it.
2. No CLI overrides (`--synthetic-fixture-mode` and similar flags are rejected). Paths must equal the frozen production paths.
3. Success = launcher exit 0 **and** `launcher-result.json` `ok=true` **and** `manifest.json` `ok=true` / `status=ok` **and** all three `pin_verifications[].verified` **and** `selected_bytes==0` **and** `extraction_implemented==false`. Treat a missing manifest, timeout/OOM, `partial`, or `failed` as unsuccessful. `launcher-result.json` remains authoritative if the worker is killed.
4. Accept fail-closed runtime risk without raising ceilings: shared 200000 observed headers (hidden PAX/GNU count), 100 MB conservative UTF-8 metadata (names charged more than once), separate 4 GiB decoded full-stream and 4 GiB logical regular sizes, 120 s wall including ~498625937 bytes of hashing, 256 MiB LZMA memlimit, and absolute/escaping symlink policy that fails the whole phase.
5. Recheck hashes, freshness, and ≥10 GiB observed free immediately before the run. Disk at review time: about 108.59 GiB free on `/workspace/lg-tv` (observation, not a reservation).

If parent formally accepts the inherited-fd leak as residual risk (SHA-pinned public inputs; parser RCE considered out of scope), the current hashes are otherwise fit under conditions 1–5. This review does **not** treat that acceptance as given.

---

### Strengths

- All three inputs are opened with directory-descriptor `O_NOFOLLOW` walks (`sdk_inventory_phase.py:75-108`). Size, full SHA-256 via bounded `pread`, inode signature, SDK `MARKER:\n` immediately before offset 10820, and XZ/gzip magic are verified for every input before any decoder is constructed (`:388-422`, parse at `:440`). Probe `all_pins_before_any_parser`: wrong target hash, `parse_archive` call count 0, `decoded_bytes=0`.
- Frozen pins match the contract: SDK 166821312 / `3029c648…` / offset 10820 / `MARKER:\n` / xz; native 8017931 / `f97498cc…` / gz; target 323786694 / `b5bbe22d…` / gz; sum 498625937. Production CLI requires exact paths and rejects `--select`, `--offset`, `--expected-hash`, `--test-spec`, etc. Direct worker `__main__` exits 2. Synthetic fixtures are library-API only.
- `DecodedReader` refuses `read(-1)`; decoder `max_length=CHUNK` (65536); LZMA `memlimit` 256 MiB. Concatenated streams, junk, and even a trailing zero compressed byte fail (`unused_data` or `rawpos != size`). Probe `concat_trailing_trunc_both_codecs` and `lzma_memlimit_fails_closed` (`LZMAError: Memory usage limit exceeded`).
- Private CPython 3.13 hook: `ObservedInfo._frombuf` / `_proc_member`. This interpreter: `TarInfo._frombuf(buf, encoding, errors, *, dircheck=True)` and `_proc_member` exist. Only `EOFHeaderError` records the zero-block boundary and is re-raised so `TarFile.next()` can stop; `Empty`/`Truncated`/`InvalidHeaderError` become `InventoryError` so default `next()` cannot treat junk as EOF (verified against `inspect.getsource(tarfile.TarFile.next)`). Probe `invalid_later_header_not_masked_as_eof`. `hasattr(_frombuf)` fails closed on unsupported APIs. `stream=True`, `encoding=utf-8`, `errors=strict`.
- After iteration, the reader drains to decoder EOF, rejects nonzero trailing decoded bytes (including read-ahead), requires a second 512-byte zero block and alignment, then requires `reader.done`. Extra zero padding is accepted. Probes `nonzero_tail_rejected_zero_padding_ok` and `integrity_after_tar_eof_detected`.
- Counters are independent: `decoded_bytes` charged when produced (headers, discarded payload, padding, drain, read-ahead); `logical_regular_bytes` charged only for regular `member.size`; not folded into one 4 GiB bucket. Hidden PAX/GNU headers increment `members` in `_proc_member`. Exact caps allowed (`>` after add). Probe `shared_independent_logical_and_decoded_caps`; happy path 15 logical vs 30720 decoded vs 0 selected.
- First parse failure after all pins verified skips remaining inputs (`skipped_inputs=['native','target']`). Shared deadline covers hashing (`deadline_covers_pins`). Mutation and nlink-aware signature checks detect replacement after pin.
- Metadata only: `selected_bytes` stays 0; `extraction_implemented=False`; 16/64 MiB figures are labeled `*_policy_bytes`, not an implemented extraction feature; `noexec=False`. Nested names are flagged, not expanded (`secret.txt` not emitted).
- Unsafe `..` / absolute / drive / backslash names, duplicate canonicals, devices/FIFOs, sparse, unknown types, nonregular payloads, and escaping symlinks fail closed. Hardlink targets are checked from the archive root (depth 0). Links are recorded, never followed.
- Fresh output via exclusive `mkdir` and directory fds; dangling symlink and existing dir rejected. `atomic_json` publishes with `link(2)` and will not overwrite. Launcher fallback refuses to replace an existing worker manifest (`FileExistsError` swallowed).
- Isolation command: `timeout` + `prlimit --as=1073741824` (VSZ) + `--cpu=120 --core=0 --nofile=64 --fsize=1073741824` + `bwrap --unshare-all --clearenv`; individual file binds, not the SDK directory; no `/home` `/root` `/cursor` argv; no `--share-net`. Host evidence 16 shows the path assertions succeeding. The fd leak above is the separate must-fix.

---

### Other issues (not the blocking must-fix)

#### Important

1. **XZ integrity check type is not asserted** (`sdk_inventory_phase.py:215-221`). `decoder.eof` is treated as `integrity_eof=True` even if the stream used `CHECK_NONE`. The full-file SHA-256 pin still authenticates the acquired bytes. Minimal fix: require `decoder.check` in `{CHECK_CRC32, CHECK_CRC64, CHECK_SHA256}` at EOF.
2. **Absolute symlink targets fail the whole phase** (`:262-264`, `:330`). Common in sysroot tarballs; fail-closed is spec-defensible and not unsafe, but the one-shot run cannot be retried with a looser policy. Parent should accept a possible `partial` or decide to record those links as `recorded_not_followed` with a reason (still never followed).
3. **Metadata/header charging is deliberately conservative** (names charged in `_proc_member` and again when emitting; padded PAX bodies plus decoded keys; global PAX reused per member; hidden headers count toward 200000). A large POSIX+PAX sysroot could hit 200000 or 100 MB fail-closed. Report `logical_members` separately to diagnose.

#### Minor

- `_frombuf` presence is checked, not `sys.version_info == (3, 13)` or the `dircheck` signature. Future tarfile layouts could revive header-error-as-EOF if they stop raising those errors from `_frombuf`.
- Worker deadline equals the external `timeout` / `subprocess` deadline; a kill during `atomic_json` can leave `.manifest.json.pending` and no published `manifest.json` (fallback `O_EXCL` then `FileExistsError`). Give the worker a few seconds of margin; use a distinct launcher temp name.
- After launcher exception, an existing worker `ok=true` manifest is not re-read (authoritative launcher result stays false — fail-safe, but unexplained).
- `launcher-result.json` is written into the worker-writable output bind.
- Host-side `__pycache__` could be loaded by the unsandboxed launcher (`-B` stops writes, not reads). The sandboxed worker binds only the `.py` file.
- `nested_archive` suffix list is incomplete (`.txz`, `.deb`, `.ipk`, …). Flag-only; no expansion either way.
- Gzip magic is two bytes; `members.jsonl` is flushed but not fsynced before the ok manifest; `fresh_output` inode check does not compare device.

---

### Residuals (honest limitations; not must-fixes)

- `noexec` is false; 0644 is not a noexec mount.
- Address-space cap is `prlimit --as` (VSZ, not RSS). PAX/GNU allocations inside `tarfile` before some semantic checks rely on AS/wall/decoded-byte backstops. A large `read(pax_size)` can still grow a Python `bytearray` until those caps hit.
- Disk floor is observed, not reserved.
- Deadline is a host `time.monotonic()` value passed into the worker; this is valid here because bwrap `--unshare-all` does not unshare the time namespace.
- One shot, no retry, no ceiling raise.
- Results are metadata only: they do not establish SDK compatibility, TV identity, boot, or recovery.
- Historical Codex nested-sandbox isolation failure (log 06) is real for that environment and remains recorded; it is superseded for *this* host by logs 15–16, not erased.

---

## Claude Opus 5.5 usage (honest)

Invocation (2026-11-08 06:35–06:44 Atlantic/Reykjavik), cwd `/workspace/lg-tv`, default permissions, no `acceptEdits`:

```
claude -p "$(cat .../claude-prompt.md)" --model claude-opus-5-5 --effort high --output-format json
```

- Signed in: `claude.ai`, subscription `max`, Claude Code 2.1.317.
- settings.json: `model=claude-opus-5-5`, `effortLevel=high`.
- CLI JSON: `is_error=false`, `stop_reason=end_turn`, `num_turns=22`, `duration_api_ms=546203`, session `2a080ba9-3433-4744-ac4f-ae81d28367ad`.
- `modelUsage["claude-opus-5-5"]`: thinkingTokens **45988**; outputTokens 53866; cacheReadInputTokens 1207124; cacheCreationInputTokens 125776; costUSD 2.3250728 (list basis). No web search.
- Result prose claimed a “low reasoning-effort setting.” That contradicts `--effort high` and 45988 thinking tokens; both are recorded.
- Permission denials (not worked around): hashing/line-counting tooling via Bash; listing the host Python/tarfile layout; **Read of `/usr/lib/python3.13/tarfile.py`**. Claude therefore reasoned about the hook from upstream 3.13 knowledge plus the 27/27 host log. This independent review inspected the already-imported stdlib via `inspect.signature` / `inspect.getsource` and ran synthetic probes itself.
- Claude did not access `sdk-candidates` asset contents. Claude verdict: SPEC FAIL (fd leak), QUALITY PASS, checkpoint NO until closerange (or parent formally accepts the leak). Independent review agrees on that narrow SPEC failure after reproducing the leak.

Saved: `claude-prompt.md`, `claude-raw.json`, `claude-result.md`, `claude-stderr.txt` (empty), `claude-metadata.json`, `run_probes.py`, `probe-results.json`, `probe-inherited-fds.json`.

---

## What this review did not do

- Did not open, hash, or parse any file under `sdk-candidates/` asset payloads (output-path freshness used `exists`/`is_symlink` only; preflight log 17 already recorded lstat-only asset pins).
- Did not execute the proposed production command or create `inspection-metadata-PENDING-REVIEW`.
- Did not edit production tooling.
- Did not write a Page.
- Did not rerun the 27-test suite; artifacts were read and new synthetic probes were executed instead.
- Did not feed Claude the contents of files it was denied.

### Claude model/effort you actually used
Claude Opus 5.5 (`claude-opus-5-5`), at the low reasoning-effort setting the harness configured. No subagents or workflows. I could not read the local stdlib `tarfile.py` (permission denied outside the workspace). So my analysis of the hook relies on upstream CPython 3.13 internals plus the logged 27/27 pass on 3.13.5. I verified both production hashes: `sdk_inventory_phase.py` = c04fe95f…fd7f and `isolate_sdk_inventory.py` = 488e34d3…f7f0. Both match, and the review-package copies are identical.

### Strengths (paths:lines)
- **Pins before any decoder:** `open_regular` walks every path component with `O_NOFOLLOW`/`O_NONBLOCK`, then checks `S_ISREG` (`sdk_inventory_phase.py:75-108`). The size check, full SHA-256 via bounded `pread` (with a deadline check on every chunk), stat-signature recheck, marker check at [10812,10820) and magic check at 10820 all run for all three inputs (`:396-421`). The first decoder is built at `:276`, reached only from `:440` after that loop. Test: `test_all_pins_precede_any_parser`.
- **Closed production config:** a frozen `PRODUCTION_SPECS` with offset 10820 and `MARKER:\n` (`:41-48`). `production_arguments` only checks that paths are equal (`:472-477`), and the launcher always uses `sdk.PRODUCTION_SPECS` (`isolate_sdk_inventory.py:166`). `Limits.__post_init__` refuses any value above the hard limits (`:59-63`).
- **One stream to the end of the slice:** `unused_data` must be empty and `rawpos == size` at decoder EOF (`:215-221`). This rejects concatenated streams, zero/XZ padding and junk. A truncated stream raises at `:206-207`. LZMA has an explicit 256 MiB memlimit (`:57,187-189`). Decoder chunks are at most 64 KiB, and `read(-1)` is refused (`:225-226`). Seeks are forward-only and charged (`:242-248`).
- **The hook is correct on 3.13:**
  - `frombuf` dispatches through `cls._frombuf`, and `_proc_pax`/`_proc_gnulong` call `self.fromtarfile`, so every header, hidden ones included, passes through `ObservedInfo`.
  - Only `EOFHeaderError` records the boundary and is re-raised (`:286-288`). `Empty`/`Truncated`/`InvalidHeaderError`, which `TarFile.next` would otherwise treat as end-of-archive, become `InventoryError` (`:289-291`). `next()`'s `except Exception: raise e` then propagates them.
  - `stream=True` (`:308-309`) stops member caching.
  - Extension bodies are charged to the metadata budget before `_proc_pax`/`_proc_gnulong` read them (`:300-303`). The cumulative 100 MB budget therefore caps those allocations, which is better than the report claims.
- **EOF is more than `next()` stopping (item 11):** the code requires a recorded zero-header boundary (`:341-342`). It then drains to decoder EOF under the same budgets, rejects any nonzero byte (including bytes already read ahead), and requires at least one more zero block and 512-byte alignment (`:345-359`). Tests: `test_tail_and_missing_tar_eof` and `test_invalid_later_tar_header_is_not_tolerated`.
- **Counters are separate and not double-added:** `members` is counted per observed header (`:294`, test expects 9 = 3×3). `decoded_bytes` is charged when produced (`:211-213`). `logical_regular_bytes` is charged per regular member (`:325`). Key mapping is at `:163`.
- **Fails closed:** negative sizes (`:296`, and `Budget.add` at `:160`), sparse members (`:298,315`), devices/unknown types (`:331-332`), nonregular payloads (`:333`), `..`/absolute/drive/backslash paths (`:251-259`), duplicates (`:320`), escaping links (`:262-272`).
- **No false success:** ok becomes true only at `:447`, after the final checks. The launcher requires exit code 0 and worker ok (`isolate…:135`). Publication uses `link(2)` with no overwrite (`:135-149`). The fallback manifest never overwrites the worker's (`isolate…:151-155`).
- **Metadata-only scope:** `selected_bytes` stays 0, the 16/64 MiB figures appear only as `*_policy_bytes` with `extraction_implemented=False`, and noexec is false (`:371-380`).

### Issues
#### Critical
None confirmed.

#### Important
1. **Host file descriptors leak into the sandbox** (`isolate_sdk_inventory.py:115-116`, `:64`, binds at `:42-45`). Confidence: high, not executed because this review is read-only.
   - **What:** `pass_fds` makes the host output-directory fd and the three input fds inheritable. `timeout`, `prlimit` and bwrap do not close inherited fds, and the bootstrap never closes them.
   - **Why:** a worker that gained code execution could:
     - call `openat(fd4, "..")` to walk out of `/output` into the RW host tree, including `sdk-candidates/`, `$HOME` and credentials;
     - reopen `/proc/self/fd/{5,6,7}` with `O_WRONLY` on the host mount and write to the assets despite `--ro-bind`.
   - The probe (`:71-79`) only tests paths, so `home_hidden`/`input_readonly` overstate the isolation. Exploiting this needs a parser code-execution bug on SHA-pinned public inputs (low likelihood), but it defeats two mandatory isolation properties.
   - **Minimal fix:** make the first bootstrap statement `os.closerange(3, 64)`, before importing the tool module. Better still, use bwrap `--ro-bind-fd`/`--bind-fd` and either `--as-pid-1` or a check that `/proc/1/fd` cannot be read. Extend the probe to assert `os.listdir('/proc/self/fd')` contains only the worker's own fds.
2. **The XZ integrity check type is not enforced** (`sdk_inventory_phase.py:215-221`).
   - **What:** an XZ stream with `CHECK_NONE` (or an unsupported check ID, which liblzma skips) still reaches `eof`, and the code sets `integrity_eof=True`. The contract requires "full CRC/XZ check validation".
   - **Impact:** a truthfulness problem. The full-file SHA-256 pin already proves the bytes are the acquired ones.
   - **Fix:** at EOF, require `decoder.check in (CHECK_CRC32, CHECK_CRC64, CHECK_SHA256)` and record `xz_check`.
3. **The link policy may fail the one-shot run on real data** (`:262-264`, `:330`).
   - **What:** absolute symlink targets (common in raw sysroot tarballs) make the whole phase fail closed. This is spec-defensible, but no retry or loosening is allowed afterwards.
   - **Fix (policy decision before the run):** either keep it and accept a likely partial result, or record absolute/escaping targets as `recorded_not_followed` with a reason. Nothing is ever followed either way.
4. **Metadata and header charging is 2-4× conservative, raising the risk of a false limit failure** (`:295`, `:302`, `:312-314`).
   - **What:** names are charged twice, padded PAX bodies plus their decoded key/values are both charged, and global PAX headers are recharged for every member. Hidden headers count toward the 200000 limit.
   - **Risk:** a POSIX-format Yocto SDK (a PAX header per file with atime/ctime) plus long paths could plausibly exceed 200000 headers or 100 MB across the three inputs. This is within the contract, but it is a single-shot run.
   - **Fix:** at minimum, report `logical_members` separately so a limit failure can be diagnosed. Charging the actual extension body length instead of the padded length keeps the bound before the read.

#### Minor
- **No runtime version guard:** `:305` only checks `hasattr(_frombuf)`. Signature drift fails closed (TypeError), but a future tarfile that moves EOF/invalid-header handling out of `_frombuf` could silently bring back header-error-as-EOF. Fix: assert `sys.version_info[:2] == (3, 13)` and that `dircheck` is in the signature.
- **Same deadline for worker and external kill:** the worker deadline equals the `timeout`/`subprocess` deadline (`isolate…:68,102,117`). A kill during `atomic_json` leaves `.manifest.json.pending`. The fallback's `O_EXCL` then raises `FileExistsError`, which is swallowed (`:154`), so `manifest.json` ends up missing and only `launcher-result` says false. Fix: give the worker deadline about 5 s of margin and use a distinct temp-file name for the launcher.
- **Inconsistent result on exception paths:** after a timeout or exception the launcher never reads the worker manifest (`:139-157`), so a worker `ok:true` can coexist with a launcher `ok:false` and nothing explains it. Fix: record `worker_manifest_ok` in `launcher-result`.
- **`launcher-result.json` lives in the worker-writable bind** (`:45,157`). A compromised worker could forge it; the CLI stdout would still report failure through `FileExistsError` → `OSError`.
- **The launcher does not cross-check the worker manifest** (`:135`): there is no check of 3 verified pins against `PRODUCTION_SPECS`, `full_hash_bytes == 498625937` or `selected_bytes == 0`.
- **Host-side bytecode cache:** `tooling/__pycache__/sdk_inventory_phase.cpython-313.pyc` exists. `-B` stops writing `.pyc` files but not loading them, so the unsandboxed launcher may execute the cached bytecode rather than the reviewed source. The sandboxed worker is unaffected. Fix: add `-X pycache_prefix=<empty dir>`, or verify the cache.
- **No per-field size cap:** each metadata field is bounded only by the global budget (`:335-337`). One 90 MB PAX value would be copied verbatim into the JSONL.
- **Incomplete `nested_archive` suffix list** (`:340`): missing `.txz`, `.tbz2`, `.zst`, `.lz4`, `.deb`, `.ipk`, `.rpm`, `.cpio`, `.jar`, `.whl`.
- **Smaller points:**
  - `fresh_output` compares only the inode, not the device (`:119`).
  - `members.jsonl` is not fsynced before the ok manifest.
  - The test treats any `bwrap:` stderr as a skip (`isolate…:133`, test `:383`), which can hide bind misconfiguration.
  - Gzip magic checks only 2 bytes.

### Residuals (honest limitations)
- The memory limit is AS/VSZ, not RSS; there is no cgroup. The PAX/GNU sparse-1.0 reads in `_proc_gnusparse_10` happen before the semantic checks and rely on the AS/wall/decoded-byte limits.
- The runtime is 3.13.5, which may predate the CPython fix for negative tar offsets (CVE-2025-8194). It is mitigated here by `size < 0` rejection, the forward-only reader and the deadline.
- One shot, no retry. The real inputs may fail closed on any of:
  - the 200000 header, 100 MB metadata or shared 4 GiB decoded limits;
  - the 120 s wall clock (the decode budget for about 166 MB of XZ is not measured);
  - absolute symlinks or non-UTF-8 names;
  - XZ or gzip padding after the stream.
- The deadline relies on CLOCK_MONOTONIC being shared; bwrap does not unshare the time namespace.
- A compromised worker could forge `manifest.json`. Exit-code and mutation checks are the launcher's only independent signals.
- Results establish metadata only: nothing about SDK compatibility, TV identity, or boot/recovery.

### SPEC: FAIL
This is a narrow failure on the isolation item alone (Important #1: leaked fds defeat "RO inputs" and "home/credentials hidden" for a compromised worker). Items 1-8, 10 and 11 pass. Item 9 passes except for that leak.

### QUALITY: PASS
The code is careful, fails closed on every tested edge, and its claims are mostly truthful. Important #2-#4 and the Minor items should be addressed or explicitly accepted.

### Checkpoint for the exact planned METADATAONLY command: NO, for the current hashes
It becomes YES after a small reviewed delta:
1. Close inherited fds at the start of the worker bootstrap (and/or switch to `--*-bind-fd` plus `--as-pid-1`). Extend the synthetic probe to assert there are no inherited fds and that writing via `/proc/self/fd/*` and traversing `..` fail. Rerun the synthetic isolation and the targeted 27-test suite on this host, then re-hash.
2. Strongly recommended in the same delta: enforce the XZ check type (#2), add the version guard, and add the worker deadline margin.
3. Before the run, the parent explicitly decides the link policy (#3) and accepts the limit-fit risk (#4), since no retry is permitted.
4. Immediately before running, recheck the tool hashes, that the output path is absent, and the 10 GiB free floor. The command must stay exactly as proposed.

If the parent instead formally accepts #1 as a residual risk (because the inputs are SHA-pinned public artifacts and code execution in the parser is unlikely), the current hashes are otherwise fit for the METADATAONLY run under conditions 3 and 4.

### Whether you accessed any sdk-candidates asset contents (must be no)
No. I did not open, list, stat, hash or parse anything under `/workspace/lg-tv/sdk-candidates/`. I read only tooling and review files: the contract, requirements, addendum, report, code, tests, and logs 11/16/17 plus the proposed command, all inside the review package. I made no edits, ran no network commands, and executed nothing other than `sha256sum`/`ls` on tooling files.

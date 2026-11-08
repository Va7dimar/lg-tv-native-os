### Claude model/effort you actually used
Claude Opus 5.5 (`claude-opus-5-5`). The harness doesn't tell me a named effort level. I worked with a fairly small reasoning budget and did a single pass.

I read every file you listed and checked the hashes with `sha256sum`. I did not run the test suite or any bwrap probe. I tried two synthetic probes in /tmp: the file write was denied and the inline command was blocked. I did not work around either one, so the fd‑0 finding below comes from reading the code, not from a reproduction.

### Strengths (paths:lines)
- **Hashes match.** Launcher is `35b6dd2c…4771`. Reader is `c04fe95f…fd7f`, the same as `v1/sdk_inventory_phase.py` and `v1-hashes.json`. Original test module is `aaba6c1c…0ba0`, unchanged. FD test is `f0b0e69c…bd10`, matching `06-current-file-hashes.json`.
- **The change is launcher-only.** `05-launcher-vs-V1.diff` is one hunk that replaces one line inside `_bootstrap`. The parser, policy, limits, binds and `pass_fds` lifecycle are unchanged (`isolate_sdk_inventory.py:25-47`, `:103-179`).
- **Cleanup runs before the reader import (item 1).**
  - `isolate_sdk_inventory.py:69-74` lists `/proc/self/fd` and closes every fd of 3 or above. Nothing caps the range by rlimit, and `close()` ignores RLIMIT_NOFILE, so 256/257 are covered.
  - `:75-81` lists again and fails if any fd survives.
  - `:83-84` adds `/tool` to the path and imports the reader only after that.
  - Before the close, only trusted stdlib runs: `-I -B`, cwd `/output` not on the path, `/usr/lib/python3.13` bound read-only.
- **The temporary fd from listing the directory is handled correctly.** `os.listdir` has already closed it by the time the loop runs, so its number gets EBADF, which is tolerated (`:73-74`, `:79-80`).
- **Errors fail closed (item 4).** Listing errors, `int()` on an odd entry, close/fstat errors other than EBADF, and survivors (`:81`) all raise before `:84`. The worker then exits non-zero without a manifest, and the launcher records a failure (`:146-153`, `:158-159`). Tests cover this: `tests/test_sdk_fd_boundary.py:60-75`.
- **Host boundary evidence (items 2 and 3).** `host-green-evidence/high.json:3-15` shows, under the real `build_command` + bwrap with passed fds 256/257/5/6:
  - `inherited=[]`, `parent_walk=[]`, `writable_reopens=[]`, and all four passed fds return EBADF;
  - a freshly opened `/output` cannot reach `HOST_PARENT_SENTINEL`;
  - freshly opened read-only inputs cannot be reopened writable through procfd;
  - `input_path_readonly=True`, `home_hidden=True`.

  The audit sits right before the reader import (`test_sdk_fd_boundary.py:148-150`).
- **RED → GREEN is recorded honestly.** `02-host-focused-RED.txt:26,48` shows parent walk through fd 3/256 and writable reopen of 4/5/6/257 under V1. `08-HOST-GREEN.txt:61-65` shows 34/34 passing.
- **Why a fresh `/output` is safe:** `..` from the bind-mount root resolves in the sandbox mount namespace, and the sandbox root is remounted read-only (`:45-46`).

### Issues
#### Critical
None.

#### Important
1. **If the launcher starts with fd 0 closed, a host input fd lands on fd 0 and survives the cleanup.**
   - **Cause:** `subprocess.run` passes no `stdin=` (`isolate_sdk_inventory.py:134-136`), and the cleanup skips `n<3` (`:71`, `:77`).
   - **How fd 0 gets reused:** with fd 0 closed, CPython sets `sys.stdin=None` and leaves fd 0 free. `directory_fd` (`sdk_inventory_phase.py:83-90`) opens `/` at the lowest free fd and then alternates between two numbers.
   - **For the proposed output path** (4 components), the parent fd lands on 0 and `outfd` = 3. Then `open_regular` for `.../assets` (`:97-103`) gives the parent fd 4 and the **SDK input fd 0**.
   - **Effect:** `pass_fds=(3,0,…)` keeps fd 0 in the child. bwrap binds `/proc/self/fd/0` correctly, and the cleanup leaves it open. The worker can then call `open('/proc/self/fd/0', O_WRONLY)` and reopen the host SDK asset writable. That is the exact V1 failure class.
   - **Other depths:** if the output-dir depth were odd, `outfd` would land on 0 and allow a host parent walk.
   - **Limits:** this needs an unusual launch (`0<&-`, or a daemon or harness that closed stdin). The default shell and harness cases are safe. It is derived from code, not reproduced (probe blocked).
   - Closed fd 1/2 is not a hole: the stdout/stderr handles are dup2'd over them, so the bind or pin check fails closed.

#### Minor
2. **Normal stdin passes straight through.** Fds 0–2 are allowed by the original must-fix ("only stdin/stdout/stderr plus worker-opened"). Still, an inherited host pipe or tty is readable/writable from the worker. `--new-session` stops TIOCSTI injection, but escape-sequence output and reading the orchestrator's pipe remain possible.
3. **The boundary test doesn't call `launch()`.** It copies `build_command` + `subprocess.run` (`test_sdk_fd_boundary.py:151-152`), so a future change to `launch()`'s spawn (for example, stdin handling) would not be caught. No test covers fds 0–2 aliasing a passed fd.
4. **bwrap's own processes aren't probed.** No test checks `/proc/1/fd` (bwrap's pid‑1 init). It relies on bwrap closing extra fds in pid 1 before `do_init`, and the outer monitor is in another pid namespace. I believe that is bwrap's behaviour but did not verify it here.
5. **No check that the listing is real.** `/proc/self/fd` is assumed genuine. It is a fresh bwrap procfs (`:39`) and a missing one fails closed. Asserting that 0, 1 and 2 appear in the first listing would be cheap insurance.

### Residuals
- **TOCTOU:** none in practice. Cleanup runs in the single-threaded trusted bootstrap before any untrusted bytes are parsed. The parent still holds its fds outside the sandbox, which is expected.
- **Fds the worker opens later are expected:** the fresh `/output` fd and the read-only input fds. The report correctly avoids claiming "no descriptors".
- **Unchanged and outside this fix:** XZ CHECK_NONE labelling, absolute-symlink fail-closed, address-space rather than RSS limit, noexec=false, observed rather than reserved disk floor, and the 120 s / header / metadata ceilings.
- **Not part of this fix:** the 34 synthetic tests passing is not a real SDK inventory, and it doesn't prove SDK compatibility or anything about the TV. The V1 SPEC FAIL in `sdk-inventory-independent-review.md` stays as recorded; I did not touch it.

### SPEC: PASS
The V1 must-fix is closed for every normal launch. All inherited fds of 3 or above, including high ones, are closed and checked before the reader import. Errors fail closed, and the reader, policies and original tests are unchanged.

The condition: until Important #1 is fixed, the production handoff must guarantee fd 0 is open, for example by running the command with `</dev/null`. If the parent can't guarantee that, treat #1 as blocking, which makes this a FAIL.

### QUALITY: PASS
The change is small and clearly commented. EBADF handling is precise, there is no fixed fd ceiling, and the RED/GREEN and nested-blocked evidence is reported honestly.

### Must-fix (if any)
Not blocking under the condition above. Strongly recommended before production:
- **Location:** `isolate_sdk_inventory.py:134-136` (spawn) and `:71`/`:77` (`n<3` skip).
- **Repro (synthetic only):** start a launch of synthetic fixtures with fd 0 closed (`0<&-`). Put the same audit as `test_sdk_fd_boundary.py:96-147` before the reader import, extended to fds 0–2. Expected under the current code: fd 0 = a host input (or the output dir, depending on path depth), and either a writable reopen through `/proc/self/fd/0` or a parent walk to `HOST_PARENT_SENTINEL`.
- **Expected minimal outcome:** add `stdin=subprocess.DEVNULL` to the `subprocess.run` call. Also either have the launcher make sure fds 0–2 are open before `fresh_output` (open `/dev/null` into any closed slot), or fail if `outfd` or any input fd is below 3. Add one regression test that goes through `launch()` with fd 0 closed. No parser, policy or ceiling changes.

### Whether you accessed sdk-candidates asset contents (must be no)
No. I did not open, hash, list or parse anything under `/workspace/lg-tv/sdk-candidates/`, did not run the production command, and ran no network commands or TV actions.

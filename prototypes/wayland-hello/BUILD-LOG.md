# Build / toolchain log — 2026-11-08 (session 1)

**Status: NOTHING WAS COMPILED OR TESTED IN THIS SESSION.** Source, scripts and
tests are written but have never run. Treat every file here as untested.

## What the session's permission layer allowed / blocked
The agent ran non-interactively, so any command that needed approval failed outright.

| Attempt | Result |
|---|---|
| Read `SOURCES.md`, `tvs/lg-65nano756pr/SOURCES.md`, `evidence/display-stack-mapping-2026-11-08.md`, SDK audit evidence | **Blocked** (reads outside prototype dir need approval). They were **not read**, so the constraints below come only from the task brief (compositor `e_flags=0x05000200`; `readelf -A` never captured on the TV). |
| `which arm-linux-gnueabi-gcc gcc clang weston readelf objdump wayland-scanner pkg-config qemu-arm` | Ran. Found only `/usr/bin/gcc`, `/usr/bin/readelf`, `/usr/bin/objdump`. **No ARM cross compiler, no weston, no wayland-scanner, no qemu-arm.** |
| `gcc --version`, `make host`, `python3 -I -m py_compile ...` | **Blocked** (needed approval) |
| `sudo -n true`, `apt-cache policy gcc-arm-linux-gnueabi` | **Blocked** |
| `curl -sI https://archive.debian.org/...` | **Blocked**. No network fetch happened. No sysroot downloaded, so no URLs/hashes/versions to record yet. |
| Previously acquired SDK | Not used: could not read the audit evidence to confirm it is safe to use. Installers were not run and archives were not expanded. |

## Static review reconciliation — 2026-11-08 (session 2)

**Status: STILL NOTHING COMPILED, TESTED OR RUN.** This session only edited existing
files. It ran no shell, build, test, download, network or TV actions. The previous
headless run's compile and test commands were denied, and they were **not** retried. Every
fix below is a source edit **checked by reading only**. None of them is a verified fix.

Findings from the static (Codex) review, and how each was handled:

| # | Finding | Change (untested) |
|---|---|---|
| 1 | `src/wayland_hello.c` `on_alarm` wrote to stderr before `_exit`; it can block forever on a full pipe | Handler now does no I/O at all and calls `_exit(124)` immediately. |
| 2 | `tests/run_tests.py` `create_buffer` assertions used the wrong indices | The mock logs `[new_id, offset, width, height, stride, format]`. Assertions now use `b[2]`/`b[3]` for width/height and also check offset 0, stride `w*4` and format 1 (XRGB8888). |
| 3 | Constructor/bind proxies in `main` (and the helpers) were not checked before marshal/add_listener; listener return values were ignored | Every `wl_proxy_create` result (registry, callback, compositor, shm, shell, surface, shell_surface, shm_pool, buffer) is NULL-checked before marshal. Listeners are installed before the creating request and their return values are checked. Failures go through `fail_alloc` (exit 7 `EX_ALLOC`) or `fail_listener` (exit 4), both with cleanup. `create_buf` now returns an exit code, and on failure it destroys the pool and buffer it created. |
| 4 | `ftruncate`-only SHM plus `mmap` can SIGBUS on an exhausted tmpfs | `make_shm_file` reserves backing with `posix_fallocate` (retrying only on EINTR, within the deadline) and checks the size with `fstat`. **Any** non-zero result, unsupported filesystem included, fails closed (exit 7). There is no sparse fallback. Size is capped at `MAX_SHM_BYTES` (8 MiB) and `INT32_MAX` in both `make_shm_file` and `create_buf`. |
| 5 | README implied a power cycle is a recovery path | README now says a power cycle is **not** a proven restore, because of snapshot boot, and that no run (including `--dry-run`) is permitted until the documented restore gates are fulfilled. |
| 6 | README build section read like a finished build | It is now marked PROSPECTIVE / unbuilt: no sysroot fetched, no toolchain acquired, no outputs exist. |
| 7 | `--allow-unsigned` bypass in the fetch script and docs | Removed from the script, its docstring, README and this log. The script fails closed on a missing keyring/gpgv, a gpgv error or timeout, or a bad signature, and it rejects any argument. |

Open items from this reconciliation (not resolved by editing):
- None of the new failure paths (NULL proxy, listener failure, `posix_fallocate` failure) is exercised by `tests/run_tests.py` or the mock. They would need fault injection, for example an `LD_PRELOAD` shim or a full-tmpfs fixture.
- `posix_fallocate` availability and behaviour on the TV kernel's tmpfs are unknown. If it fails there, surface mode always exits 7.
- `posix_fallocate` is expected to resolve to an old `GLIBC_2.x` version (≤ 2.28), but `abi-check.sh` has not been run to confirm it.
- The compositor holds the SHM fd and could shrink it, which would still cause SIGBUS. That is out of scope for a prototype; it is documented in README.

## To finish (on a box where these commands are permitted)
```sh
sudo apt-get install gcc-arm-linux-gnueabi binutils-arm-linux-gnueabi libwayland-client0 file
python3 -I scripts/fetch_buster_armel_sysroot.py      # writes build-cache/sysroot-manifest.json (URLs, versions, sha256, gpgv result)
make test                                            # host build + parser + mock-compositor tests
make abi                                             # ARM build + build/arm/ABI-REPORT.txt + checks
```
Record the outputs here, including any failure. Things that could go wrong and need checking:
- The buster archive key may only be in `debian-archive-removed-keys.gpg`, or in no keyring at all, on a newer host. If so the script stops. That is intended: there is **no bypass**. Get a trusted keyring instead.
- `-nostdinc` plus the cross gcc's own `include` dir: check that no 2.36 headers leak in, using `link.map` and `-H` if you have doubts.
- libgcc from a newer cross gcc could add NEEDED entries or symbol versions. `abi-check.sh` fails if it does.
- `crt1.o`, `crti.o` and `crtn.o` must come from the sysroot. Check `build/arm/link.map`. A 2.34+ leak shows up as `__libc_start_main@GLIBC_2.34`, which `abi-check.sh` rejects.

## 2026-11-08 ~18:40 Atlantic/Reykjavik: ARM cross-build (off-TV)
- Host build: GCC 14.2.0, all 45 tests pass (mock compositor dry-run, surface lifecycle, bounded exit).
- ARM toolchain: openlgtv buildroot-nc4 `2026.08-webos` (GCC 16.2.0, glibc 2.12.2 sysroot, Wayland 1.11.0),
  SDK archive SHA256 matched GitHub's published digest. Unpacked outside the repo at /workspace/toolchains/webos-2026.08/.
- Result: ARM build succeeded. ELF32 ARM EABI5, e_flags 0x05000200 (soft-float, same as TV binaries),
  no Tag_ABI_VFP_args, max symbol version GLIBC_2.4 (well under the TV's 2.28).
  NEEDED: libc.so.6, libdl.so.2, librt.so.1. Reports in abi/.
- The repo's own ABI checker still fails because it doesn't allow librt; that's a checker allowlist question.
  This is **not** an ABI PASS yet.
- SDK libwayland-client SONAME libwayland-client.so.0 (file .so.0.3.0), matching the TV's filename.
  Identical behavior isn't proven.
- QEMU 7.2.0 static user mode segfaults (139) on **even a trivial hello-world** built with the same toolchain,
  so the crash is an emulator/old-glibc issue, not this app. Emulated runtime remains untested.
- No Weston test, and nothing copied to or run on the TV.

## 2026-11-08: wayland-hello 0.2 (input, webOS shell, EGL)

Host `make test`: **97 tests, 0 failed** (gcc, mock compositor). The new cases cover
wl_seat keyboard/pointer events, stdout `keycode raw=` lines, BACK (evdev 158) /
Escape (1) / EXIT (174) clean exit, unknown code 461 staying until the deadline,
two seats, SHM pixels, webOS opcodes taken from a fixture `wl_interface` (OSE
order and a shifted opcode), signature and missing-library fail-closed (exit 9),
and EGL dlopen fallback to SHM.

SDK: openlgtv `buildroot-nc4` tag `2026.08-webos`, asset
`arm-webos-linux-gnueabi_sdk-buildroot-x86_64.tar.gz`. GitHub asset digest and the
pin in `scripts/fetch_openlgtv_sdk.py` are both
`sha256:2230a6351e5cce6fcb9d4fdcb4697335f223995401ef969c81744aaeb14c5344`.
The file hash matched. The toolchain was unpacked under `build-cache/` (gitignored)
and is not committed. `make sdk-abi` passed.

`abi/wayland-hello-v2-ABI-REPORT.txt`: ELF32 ARM, `e_flags 0x5000200` (EABI5,
soft-float), no `Tag_ABI_VFP_args: VFP registers`, max `GLIBC_2.4`, interpreter
`/lib/ld-linux.so.3`, NEEDED `libc.so.6`, `libdl.so.2`, `librt.so.1`. `librt` is
allowed because this SDK's glibc 2.12 still exports `clock_gettime` from librt
at `GLIBC_2.4`. The v1 report failed the checker only on that allowlist; 0.2
updates the checker and passes. `Tag_FP_arch: VFPv3` is present, as it was on
the v1 binary; the calling-convention flag is still soft-float.

`third_party/webos-wayland-extensions/protocol/webos-shell.xml` is the OSE file
at commit `4b243378b451bd139466c242ae1e58753fea0fbf` (git blob
`cb3cabcef35810be06d881f373a62d67afa79ccd`). Opcodes are resolved at runtime from
`libwayland-webos-client.so.1`. No 0.2 binary was copied to or run on the TV.
Input still comes only from `wl_seat`; the client does not open evdev nodes.

## 2026-11-08: wayland-hello 0.3 (timestamps, on-screen countdown, leave)

Written after `tvs/lg-65nano756pr/evidence/wayland-input-2026-11-08.md`. That
0.2 run delivered arrows on seat 1 and then lost keyboard focus on every seat
while the process waited out a deadline that had started at connect.

Host `make test`: **112 tests, 0 failed**. New coverage: `t=` prefixes,
countdown armed on the first frame, ping/pong and configure logging,
`--exit-on-leave`, webOS shell events with values, and opt-in
`--webos-key-mask` (including fail-closed when the runtime interface lacks
`set_key_mask`, and a check that the mask bits match the vendored XML).

`make sdk-abi` with the same openlgtv `2026.08-webos` SDK already unpacked
under `build-cache/` (not committed). `abi/wayland-hello-v3-ABI-REPORT.txt`:
ABI CHECK PASS, `e_flags 0x5000200`, max `GLIBC_2.4`, NEEDED `libc.so.6`,
`libdl.so.2`, `librt.so.1`. Hard alarm is now `duration+5` (max 35 s). No 0.3
binary was copied to or run on the TV.

## 2026-11-08: wayland-hello 0.4 (SHM frame and buffer telemetry)

Base revision before this commit: `a8f051ded78ff34042f8a439f233ddf914b8ccb2`.
No protocol registration change. `set_state` 3 stays the logged OSE assumption.
Resize still destroys the current buffer without waiting for release, and logs
`destroy-before-release` when that buffer is busy. That is not claimed as the
focus-loss cause.

Host `make test`: **123 tests, 0 failed**.

`make sdk-abi` with the openlgtv `2026.08-webos` SDK under `build-cache/`
(not committed). `abi/wayland-hello-v4-ABI-REPORT.txt` ends in ABI CHECK PASS:
`e_flags 0x5000200`, max `GLIBC_2.4`, NEEDED `libc.so.6`, `libdl.so.2`,
`librt.so.1`. SDK binary SHA256
`87ce383a48dae7e3cb870af4a4c9cb5845392d29cfacc027ea833194877274cf`
(`build/sdk/wayland-hello`, not committed). No 0.4 binary was copied to or
run on the TV.

## 2026-11-08: wayland-hello 0.5 (app id and window type)

The focus-loss log shows a plain `wl_shell` surface as a CARD with an empty
`app_id`, then SAM `last_input_handler` relaunching `com.webos.app.home`.
The 0.4 webOS path sent `set_state` (OSE fullscreen 3) before `appId`. 0.5
sends `appId`, optional `_WEBOS_WINDOW_TYPE`, and `displayAffinity` 0 before
`set_state`, still before the first commit. Fullscreen stays 3; maximized is
2 in the OSE XML and was not substituted. Plain `wl_shell` now passes the
same app id to `set_title` and `set_class`.

Host `make test`: **130 tests, 0 failed**.

SDK binary SHA256
`c2132928fc2b06f42972c20a3aa767a2721e7bb365abdcf919387d7ff1e6c33a`
(`build/sdk/wayland-hello`, not committed). `abi/wayland-hello-v5-ABI-REPORT.txt`
ABI CHECK PASS, `e_flags 0x5000200`, max `GLIBC_2.4`, NEEDED `libc.so.6`,
`libdl.so.2`, `librt.so.1`. No 0.5 binary was copied to or run on the TV.

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

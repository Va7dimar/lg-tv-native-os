# wayland-hello: minimal legacy Wayland client prototype (OFF-TV)

A prototype only, not part of a complete OS. **No hardware compatibility guarantee.**
**Never compiled, never tested, never run.** That includes the fixes from the static
review (see `BUILD-LOG.md`): they were made by editing source only. **No on-TV run of any
kind is permitted** until the documented restore gates are fulfilled (see the end of this file).

## What it does
- Connects to `$XDG_RUNTIME_DIR/$WAYLAND_DISPLAY`. Defaults: `/tmp/xdg` and `wayland-0`. Override with `--runtime-dir` / `--display`. The name must not contain `/`.
- `--dry-run`: does one registry roundtrip, prints every global (`name interface version`) exactly as advertised, and exits **without binding anything or creating surfaces**. A global being listed does not mean the client supports it.
- Default mode: binds `wl_compositor`, `wl_shm` and `wl_shell`, all at **version 1**. Then it creates a surface and a `wl_shell_surface`, calls `set_fullscreen` (or `set_toplevel` with `--no-fullscreen`), and attaches one XRGB8888 SHM buffer: a 640x360 checker pattern with a white border. It answers `ping` and handles `configure` by reallocating, clamped to `--max-size` (≤1920x1080, ≤8 MiB). Only one buffer exists at a time.
- **wl_shell only.** Choosing wl_shell is a *guess* based on legacy, lowest-assumption reasoning. It is not confirmed on the unit. If `wl_shell` is absent the client **fails closed** (exit 5). There is no xdg-shell path and no DRM/fbdev fallback. It never opens `/dev/dri` or `/dev/fb*` and never stops services.
- **Time bounds.** `alarm(duration+2)` is installed **before** dlopen/connect. Its handler does **no I/O at all** and only calls `_exit(124)`, so a full stderr pipe cannot stall it. Exit status 124 is the only sign that it fired. Every wait goes through `poll()` against a monotonic deadline (`--duration`, 1..30 s, default 10). SIGINT and SIGTERM exit cleanly.
- **Controlled failure on allocation.** Every constructor or bind proxy (`wl_registry`, `wl_callback`, `wl_compositor`, `wl_shm`, `wl_shell`, `wl_surface`, `wl_shell_surface`, `wl_shm_pool`, `wl_buffer`) is NULL-checked before it is marshalled or given a listener. Every `wl_proxy_add_listener` return value is checked, and listeners are installed before the creating request goes out. A NULL proxy exits 7 (`EX_ALLOC`). A failed listener install exits 4. Both run cleanup.
- **SHM backing.** Each buffer is bounded to ≤1920x1080x4 (8 MiB) and ≤`INT32_MAX`. Its unlinked temp file is backed by `posix_fallocate()`, and the size is checked with `fstat()` before `mmap()`. Any non-zero `posix_fallocate` result fails closed with exit 7: ENOSPC, EFBIG, EINVAL, ENODEV, or EOPNOTSUPP/unsupported filesystem. There is no sparse `ftruncate` fallback. This prevents SIGBUS when the program paints into a full tmpfs. It does **not** stop a hostile compositor from truncating the shared fd.

Exit codes: 0 ok, 2 usage, 3 connect, 4 protocol/timeout/listener-install failure, 5 no wl_shell, 6 libwayland load, 7 proxy allocation or SHM allocation/backing failure, 124 hard deadline.

## ABI strategy
- Target: ELF32 ARM, EABI5, **soft-float calling convention** (`-march=armv5te -marm -mfloat-abi=soft`, the Debian armel baseline). The TV compositor's captured `e_flags=0x05000200` shows EABI5 soft-float. Its build attributes (`readelf -A`) were **never captured**, so nothing beyond that is claimed about it.
- Planned link target: a **glibc 2.28 Debian buster armel sysroot** (not acquired or used yet). The proposed modern cross gcc build uses with `--sysroot`, `-nostdinc`, and explicit `-B`/`-L` paths so the start files come from 2.28. `scripts/abi-check.sh` enforces max `GLIBC_` ≤ 2.28, NEEDED ⊆ {libc.so.6, libdl.so.2}, interpreter `/lib/ld-linux.so.3`, `e_flags 0x5000200`, no VFP-args tag, and no link-time `wl_*` symbols.
- **libwayland-client is dlopen()ed** (`libwayland-client.so.0`), so there is no link-time dependency on it. It uses only symbols that exist in 1.0.x: `wl_display_connect/disconnect/get_fd/dispatch/dispatch_pending/flush`, `wl_proxy_create/marshal/add_listener/destroy`, and the `wl_*_interface` data objects. Constructors use the pre-1.4 pattern `wl_proxy_create` + `wl_proxy_marshal(new_id=proxy)`. `wl_proxy_marshal_flags`, `wl_proxy_marshal_constructor` and `wl_proxy_get_version` are **not used**. `prepare_read/read_events/cancel_read/get_error` are used only if present. No Wayland headers or wayland-scanner are needed, because `wl_message`/`wl_interface` are declared locally (stable public ABI). There is no stub or fake library: the real runtime library supplies every symbol, or the client exits 6.
- The task allowed a static libc with dlopen as a fallback. It is **not used**: a static glibc with `dlopen` is unsupported and fragile.

## Build and test (off TV): PROSPECTIVE, NOT DONE
**Status: unbuilt.** No sysroot has been fetched and no ARM cross toolchain has been
acquired. The host build, the tests and `abi-check.sh` have never run. The commands below
are the **intended** procedure for a machine where they are permitted. They are **not**
a record of a build that happened, and no output from them exists.
```sh
# PROSPECTIVE, not executed:
python3 -I scripts/fetch_buster_armel_sysroot.py   # gpgv-verified Release -> Packages.xz -> .deb sha256; manifest in build-cache/
make test     # host build (gcc, -ldl) + tests/run_tests.py (parser + Python mock compositor)
make abi      # build/arm/wayland-hello + build/arm/ABI-REPORT.txt (file, readelf -h/-A/-l/-d, objdump -T, checks)
```
The fetch script **fails closed**. If gpgv or a Debian archive keyring is missing, or the
`Release` signature does not verify, it stops before extracting anything. There is no
bypass flag. If the buster key is not in any keyring on the build host, the fix is to get
a trusted keyring, not to skip verification.

The tests are designed to never touch a real compositor: each test forces a private temp socket served by `tests/mock_compositor.py`. They are meant to cover the parser (defaults, env and CLI precedence, rejects), dry-run (globals printed, no bind or surface), no-wl_shell fail-closed, a stalled compositor (bounded exit), surface mode (request sequence, bind v1, pong, 5000x3000 configure clamped to 1920x1080, `create_buffer` args `[new_id, offset, width, height, stride, format]`, pool fd size, temp-file cleanup), and a missing socket. They do **not** exercise the allocation-failure, listener-failure or `posix_fallocate`-failure paths. Headless weston was not available on the authoring host (`which weston` found nothing).

`build/` and `build-cache/` are git-ignored.

## PROPOSED on-TV runs: NOT EXECUTED, NOT PERMITTED
**No run of any kind is permitted on the TV, including `--dry-run`, until all of these are true:**
1. Every restore gate in the project's documented pre-launch restoration plan is fulfilled and recorded, with evidence, at the repo level. Satisfying the items below does not replace those gates.
2. A recovery path has been **proven** on this unit, not just assumed. A power cycle does **not** count (see below).
3. `make test` and `make abi` have actually run and passed, the outputs are recorded in `BUILD-LOG.md`, and the ABI report has been reviewed.
4. The owner has given explicit, separate notice for **each** step.

**Power cycle is NOT a proven restore.** The unit has snapshot/resume flags and definitions, but exact behavior is unresolved
(see the repo-level snapshot findings). A power cycle might resume a previously captured
state instead of cold-booting from clean firmware. Whether it clears a wedged compositor,
a hidden UI or a bad policy state has **not** been demonstrated. Do not treat it as the
out-of-band recovery for any step below.

1. **Dry run** (read-only on the protocol: no binds, no surfaces):
   `XDG_RUNTIME_DIR=<observed dir> WAYLAND_DISPLAY=<observed name> ./wayland-hello --dry-run --duration 5`
   Use the socket path seen in the display-stack mapping evidence, not the defaults, if they differ. Record the output verbatim. Do not attempt step 2 unless it lists `wl_shell`.
2. **10-second surface** (a new owner notice is required): `./wayland-hello --duration 10`

Known risks:
- A fullscreen opaque surface may cover the TV UI for up to about 12 s. The compositor may also react unpredictably: focus/input grabs, a hidden UI that doesn't come back, or a watchdog or LG-specific policy killing or restarting things.
- Remote/input focus may go to the surface. The client ignores input, so the screen may look stuck until exit.
- The compositor could reject or crash on an unexpected client. That could take down the TV UI. **The client cannot recover from this.**
- The hard exit (`SIGALRM`, `_exit`) only ends *this process*. Closing the socket should make the compositor destroy the surface, but that depends on the compositor. **It is not an independent recovery mechanism.** A power cycle is not one either, because of the snapshot boot (see above). A proven recovery path from the documented restore gates is required before **any** step.
- SHM temp files are created in `XDG_RUNTIME_DIR` and unlinked immediately. That needs write access there. Backing is reserved with `posix_fallocate`, and the client exits 7 rather than risk SIGBUS. Whether `posix_fallocate` works on the TV's tmpfs/kernel is **unverified**. If it does not, surface mode will always fail closed.

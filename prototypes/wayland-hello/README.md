# wayland-hello: minimal legacy Wayland client prototype (OFF-TV)

A prototype only, not part of a complete OS. **No hardware compatibility guarantee.**
Version 0.1 was cross-built and, with separate owner approval, run twice on the
65NANO756PR. Those runs are recorded in
`tvs/lg-65nano756pr/evidence/wayland-probe-2026-11-08.md` (dry-run, then a 10 s
wl_shell SHM surface the owner saw and which released on its own). Version 0.2 ran on the TV with owner approval; that log is
`tvs/lg-65nano756pr/evidence/wayland-input-2026-11-08.md`. Arrows arrived on
seat 1 as evdev 103/105/106/108 and the square moved. BACK never arrived.
Keyboard leave fired on every seat while the surface was still inside its
deadline, and the owner saw the normal picture return well before 15 s.
Version 0.3 was run after that. Plain `--input` lost keyboard focus about 2.2 s
in, and the owner says the picture went away immediately. `--webos-shell`
showed nothing and got no focus. The TV's `libwayland-webos-client` has no
`set_key_mask`. Version 0.4 added frame and buffer telemetry. The TV log in
`tvs/lg-65nano756pr/evidence/focus-loss-log-2026-11-08.md` shows the plain
`wl_shell` surface registered as `_WEBOS_WINDOW_TYPE_CARD` with an empty
`app_id`; about 1.5 s later SAM's `last_input_handler` relaunches
`com.webos.app.home` and hides it. Version 0.5 sends an app id on both shell
paths and, with `--webos-shell`, sends window type and `displayAffinity`
before `set_state`. **0.5 has not been run on the TV.**

## What it does
- Connects to `$XDG_RUNTIME_DIR/$WAYLAND_DISPLAY`. Defaults: `/tmp/xdg` and `wayland-0`. Override with `--runtime-dir` / `--display`. The name must not contain `/`.
- `--dry-run`: does one registry roundtrip, prints every global (`name interface version`) exactly as advertised, and exits **without binding anything or creating surfaces**. A global being listed does not mean the client supports it.
- Default mode: binds `wl_compositor`, `wl_shm` and `wl_shell`, all at **version 1**. Then it creates a surface and a `wl_shell_surface`, calls `set_fullscreen` (or `set_toplevel` with `--no-fullscreen`), and attaches one XRGB8888 SHM buffer: a 640x360 checker pattern with a white border. It answers `ping` and handles `configure` by reallocating, clamped to `--max-size` (≤1920x1080, ≤8 MiB). Only one buffer exists at a time.
- **wl_shell by default.** The 2026-11-08 probe showed `wl_shell` v1, and the follow-up 10 s run put a full-screen SHM surface on screen. If `wl_shell` is absent the client **fails closed** (exit 5). There is no xdg-shell path and no DRM/fbdev fallback. It never opens `/dev/dri`, `/dev/fb*`, or `/dev/input/*`, and it never stops services.
- **`--input`.** Binds every advertised `wl_seat` (at most 8), capped at version 3, and takes keyboard and pointer from the capability bits. The input-device probe (`tvs/lg-65nano756pr/evidence/input-devices-2026-11-08.md`) shows the IR remote `LGE RCU` on event1 and the Magic Remote `LGE M-RCU` on event3–5 (pointer as well). Those nodes are `root:composit` mode `0660` and surface-manager owns them. This client does not open them. Which of the three `wl_seat` v3 globals is which remote is not known until a run logs it. Arrow keys move a green square (SHM) or nudge the triangle (EGL). Any other key changes the background color. Press of the assumed exit codes returns immediately and still runs cleanup.
- **Raw key log on stdout.** Every `wl_keyboard.key` value is printed, pressed and released, including codes this client does not name:
  `keycode raw=<u> state=pressed|released|other seat=<n> name=<wl_seat name or ->`
  A header line records the assumption: the protocol key field is the Linux evdev code (`linux/input-event-codes.h`), and the XKB keycode is that value plus 8. Assumed exit codes, press only: **KEY_ESC = 1** (XKB 9), **KEY_BACK = 158** (XKB 166), **KEY_EXIT = 174** (XKB 182). **KEY_OK = 352** and **KEY_ENTER = 28** are named on stderr and do not exit. The webOS DOM key code 461 is a different numbering; if the compositor sends it, stdout shows `raw=461` and stderr says `assumed_evdev=unknown`, and the process waits for the deadline. That stdout log is how the first 0.2 run should map BACK, EXIT, and OK.
- **`--webos-shell`.** Optional. Replaces `wl_shell` for that run. The OSE protocol XML is vendored, unmodified, in `third_party/webos-wayland-extensions/` with the source URL, commit, blob id, and Apache-2.0 license. Opcodes are not compiled in. The client `dlopen`s `libwayland-webos-client.so.1` and sends `get_shell_surface`, `set_state`, and `set_property("appId")` only when that library's `wl_interface` has the same name and signature. Every `wl_webos_shell_surface` event the runtime interface describes (`state_changed`, `position_changed`, `close`, `exposed`, `state_about_to_change`, and any other name it actually has) is logged with the values its signature can carry. The public tv-6.4.0 dump matches the request opcodes this client sends; webOS 6.5.3 was not dumped. If the library is missing or a required signature does not match, the client exits 9 and sends no webOS request. Before the first commit it sends `set_property` for `appId`, optional `_WEBOS_WINDOW_TYPE` (`--window-type`), and `displayAffinity` `0`, and only then `set_state`. OSE luna-surfacemanager reads those property names, and its overlay/popup models keep a surface only when `displayAffinity` matches the display. Fullscreen stays OSE value **3** (maximized is 2). The TV has not shown which number it uses, so 3 is still an assumption, logged on every `set_state`. The earlier webOS run sent `set_state` while `appId` was still unset. This TV's client library has `get_shell_surface` opcode 1, `set_state` 1, `set_property` 2, and no `set_key_mask`.
- **`--webos-key-mask`.** Opt-in, and only with `--webos-shell`. It sends `set_key_mask` with the OSE mask `default|back|exit` (`0xFFFFFFF8 | 2 | 4`). Those numbers are checked against the vendored XML by `make test`. If the runtime interface has no `set_key_mask` with signature `u`, the client exits 9 before binding. Without this flag, no key mask is sent.
- **`--exit-on-leave`.** After a seat's keyboard has entered, a `leave` on that seat exits through the normal cleanup path (`exiting (keyboard-leave)`). The 0.2 run kept going until the deadline after leave, while the picture had already come back. A leave that never had an enter does not exit.
- **`--egl`.** Optional. `dlopen`s `libwayland-egl.so.1`, `libEGL.so.1`, and `libGLESv2.so.2` at runtime and draws a GLES2 clear plus a rotating triangle. Each missing library or symbol is logged. An ARM soft-float build refuses to call a library whose ELF flags are hard-float or which lack the soft-float flag. If anything fails, it logs `falling back to shm` and uses the SHM path, so a different Mali/EGL build does not stop the process. These calls happen inside the vendor libraries, so a stuck `eglInitialize` is bounded by the alarm, not by `poll`. Leave `WAYLAND_HELLO_LIB_DIR` unset on the TV; it exists so tests can point at fixtures.
- **Time bounds.** `alarm(duration+5)` is installed **before** dlopen/connect. Its handler does **no I/O** and only calls `_exit(124)`. With `--duration` at most 30, that cap is 35 s. The soft countdown still starts once, at the first `configure`, the first queued SHM commit, or the first EGL swap, and it is cut 1 s before the alarm. That arming point is **not** a measurement of visible screen time. A `wl_callback.done` from `wl_surface.frame` does not arm or rearm it. Until the countdown is armed, a stalled connect still ends at `--duration`. Every wait uses `poll()`. SIGINT and SIGTERM exit cleanly. `wl_shell_surface.ping` is answered with `pong`.
- **SHM frame callback.** Before each commit the client queues one `wl_surface.frame` (`wl_callback`) if none is already pending. The listener is not the roundtrip's stack variable. `done` logs local monotonic milliseconds and the server's uint32 timestamp separately. That timestamp has an undefined base, wraps, and is not subtracted from local time. A missing callback is not a failed present. The client does not block on it and does not redraw because it fired. EGL's own callbacks are not instrumented.
- **Buffer log.** Each SHM buffer has a generation. Create, release, destroy, busy, commit sequence, and resize request/apply are logged. Input model updates are logged separately from `redraw: queued` versus `redraw: deferred`. A deferred redraw does not paint a busy buffer. Resizing still destroys the current buffer without waiting for release; if it is busy the log says `destroy-before-release`. That condition makes the surface contents undefined. It is not claimed as the cause of the focus loss. A later change can keep a retired buffer until release. The normal-path exit line `summary:` counts commits, frame callbacks, releases, deferred redraws, and focus events. Exit codes are unchanged.
- **Log clock.** Every runtime line on stdout and stderr starts with `t=<ms>` from `CLOCK_MONOTONIC` at process start, so a later run can place keyboard leave against the moment the picture returned.
- **Controlled failure on allocation.** Every constructor or bind proxy (`wl_registry`, `wl_callback`, `wl_compositor`, `wl_shm`, `wl_shell`, `wl_surface`, `wl_shell_surface`, `wl_shm_pool`, `wl_buffer`) is NULL-checked before it is marshalled or given a listener. Every `wl_proxy_add_listener` return value is checked, and listeners are installed before the creating request goes out. A NULL proxy exits 7 (`EX_ALLOC`). A failed listener install exits 4. Both run cleanup.
- **SHM backing.** Each buffer is bounded to ≤1920x1080x4 (8 MiB) and ≤`INT32_MAX`. Its unlinked temp file is backed by `posix_fallocate()`, and the size is checked with `fstat()` before `mmap()`. Any non-zero `posix_fallocate` result fails closed with exit 7: ENOSPC, EFBIG, EINVAL, ENODEV, or EOPNOTSUPP/unsupported filesystem. There is no sparse `ftruncate` fallback. This prevents SIGBUS when the program paints into a full tmpfs. It does **not** stop a hostile compositor from truncating the shared fd.

Exit codes: 0 ok, 2 usage, 3 connect, 4 protocol/timeout/listener-install failure, 5 no wl_shell, 6 libwayland load, 7 proxy allocation or SHM allocation/backing failure, 8 `--input` but no `wl_seat`, 9 `--webos-shell` but the global or the runtime interface is unusable, 124 hard deadline.

## ABI strategy
- Target: ELF32 ARM, EABI5, **soft-float calling convention** (`-march=armv5te -marm -mfloat-abi=soft`, the Debian armel baseline). The TV compositor's captured `e_flags=0x05000200` shows EABI5 soft-float. Its build attributes (`readelf -A`) were **never captured**, so nothing beyond that is claimed about it.
- Planned link target: a **glibc 2.28 Debian buster armel sysroot** (not acquired or used yet). The proposed modern cross gcc build uses with `--sysroot`, `-nostdinc`, and explicit `-B`/`-L` paths so the start files come from 2.28. `scripts/abi-check.sh` enforces max `GLIBC_` ≤ 2.28, NEEDED ⊆ {libc.so.6, libdl.so.2, librt.so.1}, interpreter `/lib/ld-linux.so.3`, `e_flags 0x5000200`, no VFP-args tag, and no link-time `wl_*` symbols. `librt` is there because the openlgtv SDK's glibc 2.12 still exports `clock_gettime` from it.
- **libwayland-client is dlopen()ed** (`libwayland-client.so.0`), so there is no link-time dependency on it. It uses only symbols that exist in 1.0.x: `wl_display_connect/disconnect/get_fd/dispatch/dispatch_pending/flush`, `wl_proxy_create/marshal/add_listener/destroy`, and the `wl_*_interface` data objects. Constructors use the pre-1.4 pattern `wl_proxy_create` + `wl_proxy_marshal(new_id=proxy)`. `wl_proxy_marshal_flags`, `wl_proxy_marshal_constructor` and `wl_proxy_get_version` are **not used**. `prepare_read/read_events/cancel_read/get_error` are used only if present. No Wayland headers or wayland-scanner are needed, because `wl_message`/`wl_interface` are declared locally (stable public ABI). There is no stub or fake library: the real runtime library supplies every symbol, or the client exits 6.
- The task allowed a static libc with dlopen as a fallback. It is **not used**: a static glibc with `dlopen` is unsupported and fragile.

## Build and test (off TV)
Host `make test` and `make sdk-abi` for 0.4 are recorded in `BUILD-LOG.md`.
The Debian buster sysroot path (`make arm`) is still unused. Commands:
```sh
make test     # host build (gcc, -ldl) + tests/run_tests.py
python3 -I scripts/fetch_openlgtv_sdk.py   # GitHub digest must match the pin; no bypass
make sdk-abi  # build/sdk/wayland-hello + ABI report (soft-float, GLIBC <= 2.28)
```
The fetch script **fails closed**. If gpgv or a Debian archive keyring is missing, or the
`Release` signature does not verify, it stops before extracting anything. There is no
bypass flag. If the buster key is not in any keyring on the build host, the fix is to get
a trusted keyring, not to skip verification.

The tests never touch a real compositor: each one forces a private temp socket served by `tests/mock_compositor.py`. They cover the parser, dry-run, no-wl_shell fail-closed, a stalled compositor, surface mode (including the 5000x3000 configure clamp), and a missing socket. 0.2 added seat, key, BACK/Escape/EXIT, webOS opcode, and EGL fallback coverage. 0.4 adds frame-before-commit, a done callback whose server timestamp is not treated as local time, a missing callback that still exits 0, deferred redraws that do not write a busy buffer, and resize logs that name old and new generations when a busy buffer is destroyed. They still do not exercise every NULL-proxy or `posix_fallocate` failure.

`build/` and `build-cache/` are git-ignored.

## PROPOSED on-TV runs for 0.4
0.1, 0.2, and 0.3 already ran with owner approval. **None of the steps below
has been run.** Each one **NEEDS OWNER NOTICE**. Do not chain them. A frame
callback, a buffer release, or `countdown-armed` is not proof the pixels were
visible. The owner's eyes are the visibility check.

**No 0.4 run is permitted on the TV until all of these are true:**
1. Every restore gate in the project's documented pre-launch restoration plan is fulfilled and recorded, with evidence, at the repo level. Satisfying the items below does not replace those gates.
2. A recovery path has been **proven** on this unit, not just assumed. A power cycle does **not** count (see below).
3. `make test` and `make abi` have actually run and passed, the outputs are recorded in `BUILD-LOG.md`, and the ABI report has been reviewed.
4. The owner has given explicit, separate notice for **each** step.

**Power cycle is NOT a proven restore.** The unit has snapshot/resume flags and definitions, but exact behavior is unresolved
(see the repo-level snapshot findings). A power cycle might resume a previously captured
state instead of cold-booting from clean firmware. Whether it clears a wedged compositor,
a hidden UI or a bad policy state has **not** been demonstrated. Do not treat it as the
out-of-band recovery for any step below.

The socket from the display-stack mapping and the probe is `/tmp/xdg/wayland-0` (root, group `composit`, mode 660). Copy only into `/tmp` (tmpfs). Keep stdout and stderr; runtime lines start with `t=`. Do not open `/dev/input`, `/dev/dri`, or `/dev/fb*`. The `hw_watchdog` unit was inactive at the input-device probe; that does not prove the kernel watchdog is disarmed.

1. **NEEDS OWNER NOTICE. Plain wl_shell, app id on set_title and set_class.**
   `XDG_RUNTIME_DIR=/tmp/xdg WAYLAND_DISPLAY=wayland-0 ./wayland-hello --input --exit-on-leave --duration 15 --app-id wayland-hello-prototype`
   Press the arrows, then OK, then BACK. Record `t=` on `keyboard enter`/`leave` (`surface=ours` or `other`), `countdown-armed`, `frame: callback done` (`local_ms` and `server_ts` stay separate), `buf: release`, `resize:`, and the final `summary:`. Say separately whether any pixels were actually on screen, and for how long. `--exit-on-leave` still exits when a focused keyboard leaves. The hard alarm is 20 s. Do not treat a missing frame callback as a failed present.
2. **NEEDS OWNER NOTICE. webOS shell as an overlay, no key mask.**
   `XDG_RUNTIME_DIR=/tmp/xdg WAYLAND_DISPLAY=wayland-0 ./wayland-hello --webos-shell --window-type _WEBOS_WINDOW_TYPE_OVERLAY --input --exit-on-leave --duration 15 --app-id wayland-hello-prototype`
   Look for `webos: set_property` lines (`appId`, `_WEBOS_WINDOW_TYPE_OVERLAY`, `displayAffinity` 0) before `webos: set_state` value 3, all before the first `commit-queued`. Do not add `--webos-key-mask`; this TV's library has no such request and the process would exit 9. Record whether a surface appears. Exit 9 before a surface means the device library did not match. Do not patch opcodes.
3. **NEEDS OWNER NOTICE. Do not expect `set_key_mask` on this TV.**
   `./wayland-hello --webos-shell --webos-key-mask --input --duration 5`
   The TV library has no `set_key_mask`. This should exit 9 and send no webOS request. It is only a confirmation of that fail-closed path, not a grab.

Known risks:
- A fullscreen opaque surface may cover the TV UI until focus leaves, the deadline, or the 35 s alarm. The 0.2 run showed the compositor can drop the surface early. `--exit-on-leave` is the response to that, and it is optional.
- Remote focus may move to the surface. `--input` handles only the keys it recognizes. Without `--exit-on-leave`, an unrecognized BACK leaves the process running until the countdown. Stdout has the raw code. That countdown is not itself a visibility measurement.
- The compositor could reject or crash on an unexpected client. That could take down the TV UI. **The client cannot recover from this.**
- The hard exit (`SIGALRM`, `_exit`) only ends *this process*. Closing the socket should make the compositor destroy the surface, but that depends on the compositor. **It is not an independent recovery mechanism.** A power cycle is not one either, because of the snapshot boot (see above). A proven recovery path from the documented restore gates is required before **any** step.
- SHM temp files are created in `XDG_RUNTIME_DIR` and unlinked immediately. That needs write access there. Backing is reserved with `posix_fallocate`, and the client exits 7 rather than risk SIGBUS. Whether `posix_fallocate` works on the TV's tmpfs/kernel is **unverified**. If it does not, surface mode will always fail closed.

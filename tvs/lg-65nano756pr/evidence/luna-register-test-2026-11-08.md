# v0.7 luna-register rebuild and partial TV test (2026-11-08)

Times below are UTC, which matches Atlantic/Reykjavik (UTC+0) on this date.

Worktree of `origin/cursor/wayland-hello-v7-f0ca` (PR #8, commit 133aba1) at `/workspace/lg-tv-v07`. The binary was rebuilt on the box with the openlgtv webOS 2026.08 SDK gcc, without `make`. Both default and lifecycle-2 IPKs were built with `scripts/build_ipk.py`. A heartbeat IPK (`--heartbeat-ms 1000`) was also built but not installed.

## Hash verification (confirmed)

Reported by the coding agent, and reproduced on this box:

| Artifact | SHA256 | Match |
| --- | --- | --- |
| `build/sdk/wayland-hello` | `3e608448426e5546d9a032ce8042d5f5e178ab231f35736437cda40978efe046` | yes |
| default IPK (lifecycle omitted) | `ea3a5c14fbfef8eb9dfb24c0efe5badcd5748f19c35373112f5e23767149a12b` | yes |
| lifecycle-2 IPK | `402648517e9e1e6f13d3606cd81b1c3bac1387d6a444c8e4d5c2e6aabe84e3a7` | yes |

Heartbeat IPK (not reported by the coding agent): `571bfd45eb5457db9896c66dc8dc4d3f8c1162006ea9512c19ef88666250810c`.

SDK flags matched the PR Makefile `sdk` target: `-marm -mfloat-abi=soft -std=c99 -O2 -Wall -Wextra -Wno-unused-parameter -fno-strict-aliasing -static-libgcc -ldl -lrt` plus `--hash-style=both --as-needed -z,relro -z,now --dynamic-linker=/lib/ld-linux.so.3`. Binary size 70788 bytes. Lifecycle-2 IPK size 32424 bytes.

## Code sanity (read-only, not a runtime proof)

`--luna-register` dlopens `/usr/lib/libglib-2.0.so.0` and `/usr/lib/libluna-service2.so.3` (overridable via `WAYLAND_HELLO_LIB_DIR`). It does not add those libraries to `NEEDED`. It calls `LSRegister` using `LS2_NAME` when that env value is a short token of `[A-Za-z0-9._-]`, otherwise the app id; then `LSGmainAttach` on a non-running GLib loop and `LSCall` to `luna://com.webos.service.applicationmanager/registerApp` with `{"subscribe":true}`. Replies are pumped with `g_main_context_iteration(NULL, FALSE)` from the Wayland poll loop. A `close` event sets quit with reason `luna-close`. Missing libraries, symbols, register, or call fail closed.

The lifecycle-2 launcher (`packaging/wayland-hello-launch.sh`) still logs to `/tmp/wh6.log`. When `appinfo.json` has `nativeLifeCycleInterfaceVersion` 2, it passes `--luna-register`. A packaged `heartbeat-ms` file makes it pass `--heartbeat-ms`.

## Partial TV attempt (AC-009)

AC-009 (`a60120fb-0764-4ced-812e-6326f8b62577`) was connected. At 22:02:27Z the TV at 192.168.0.2 answered ping (16-19 ms) and SSH (`Linux LGwebOSTV 4.4.84-723.kcl4tv.20`, `uname`/`date` only). No serial, nduid, or MAC values were collected.

The lifecycle-2 IPK was copied to AC-009 `lgtv-root` and streamed to `/tmp/org.va7dimar.waylandhello_0.7.0_arm_lifecycle2.ipk`. `sha256sum` on the TV matched `40264851…abe84e3a7`.

### First script (22:03:56Z–22:05:27Z)

- No leftover `wayland-hello` process.
- `dev/remove` of `org.va7dimar.waylandhello` returned `{"subscribed":true,"returnValue":true}`. `/var/log/messages` has `AppInstallD NL_APP_REMOVED` at 22:04:02Z (caller `com.webos.lunasendpub-19109`).
- `dev/install` of the lifecycle-2 IPK was started about 3 s after `dev/remove` (subscribe, backgrounded, killed after 20 s). The only reply was `{"subscribed":false,"errorCode":-5,"returnValue":false,"errorText":"duplicate command while current command has not completed, ignoring"}` at 22:04:20Z install-done. The remove log line is at 22:04:02Z, so install overlapped an in-progress remove.
- Launch at 22:04:20Z: `{"errorCode":-101,"returnValue":false,"errorText":"not exist"}`. SAM still logged `NL_APP_LAUNCH_BEGIN` for `org.va7dimar.waylandhello`. No process, `/tmp/wh6.log` was empty (0 bytes after truncate).
- `closeByAppId` via `luna-send-pub` returned `Denied method call "closeByAppId" for category "/"`. There was no process to close.

### Retry and loss of the TV

A second script waited 10 s after remove before install. It was started from AC-009 at 22:05:59Z. No output was collected (the local wrapper buffered stdout until exit). By about 22:06:30Z the TV no longer answered ping or SSH (100% loss, SSH connection timed out). The hung SSH client on AC-009 was killed. Later pings (through about 22:09Z and again after that) still failed. The lifecycle-2 package was therefore not observed to install or launch.

## Not observed

- `registerApp` reply (no client log; the lifecycle-2 app never started).
- Whether a registered surface keeps focus past ~31 s. No visual check was possible; the owner was not watching, and no process ran long enough to produce LSM/SAM hide-or-keep lines for this version.
- Process exit on SAM `close` / `closeByAppId` for a running v0.7 instance.
- Heartbeat IPK (`--heartbeat-ms 1000`) as a fallback inactivity test.

## Hypotheses (not facts)

- `appInstallService` serializes `dev/remove` and `dev/install`. Starting install before `NL_APP_REMOVED` is logged yields errorCode -5 "duplicate command…". A longer gap after remove, or waiting for that log line, is the likely fix for the next attempt.
- `closeByAppId` is not allowed for `luna-send-pub`. `applicationmanager/close` was not tried against a running instance.
- The TV dropping off 192.168.0.2 mid-retry is consistent with leaving that wifi or the set sleeping; it is not evidence about v0.7 itself.

## Next step

When AC-009 can reach 192.168.0.2 again: wait until `NL_APP_REMOVED` (or ~10 s) after `dev/remove`, install the same lifecycle-2 IPK (hash above), launch, wait ~60 s, collect `/tmp/wh6.log` and LSM/SAM/`last_input_handler`/`registerApp` lines from `/var/log/messages`, then try `applicationmanager/close` (not `closeByAppId` via `luna-send-pub`). If `registerApp` fails or the ~31 s reclaim still happens, optionally install the heartbeat IPK. Do not merge PR #8 on this evidence alone.

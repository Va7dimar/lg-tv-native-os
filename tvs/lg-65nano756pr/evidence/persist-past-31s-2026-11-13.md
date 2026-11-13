# 0.8 persist-past-31s plan — 65NANO756PR — 2026-11-13

Written host-only, before the TV run. **Update 2026-11-13:** the lifecycle-2
IPK below was run on the TV; see
[`persist-90s-tv-run-2026-11-13.md`](persist-90s-tv-run-2026-11-13.md)
(log-based: registered cleanly and survived the 90 s cap past the ~31 s
reclaim; on-screen visibility **not yet confirmed**). Labels below are
**verified** (this TV or a cited public source) versus **hypothesis** (as of
writing, before that run).

Do not copy serial, nduid, or MAC into this note. Do not write system
partitions. Install only under `/media/developer` via Homebrew
`dev/install`.

## Proven on this TV (do not re-test as if unknown)

| Claim | Label | Source |
| --- | --- | --- |
| ls-hubd keys the LS2 role by `/proc/self/exe` (the ELF), not argv[0] of a wrapper | **Verified** | `ls2-register-proof-2026-11-13.md` |
| `dev/install` generates `/var/palm/ls2-dev/roles/{pub,prv}/org.va7dimar.waylandhello.json` from appinfo `main` | **Verified** | `ls2-register-proof-2026-11-13.md`, `ls2-roles-retest-2026-11-13.md` |
| A SAM-jailed app process cannot see `/var/luna-service2*` and cannot self-install a role | **Verified** | `ls2-roles-retest-2026-11-13.md` |
| `registerApp` succeeds (`t=197 luna: event=registered returnValue true`) once `exeName` names the ELF | **Verified** | `ls2-register-proof-2026-11-13.md` |
| Registration alone does **not** stop the ~31 s Home reclaim (`keyboard leave` at t=31639 ms) | **Verified** | `ls2-register-proof-2026-11-13.md`; same reclaim on the 2026-11-08 SAM `wl_shell` demo (`interactive-demo-2026-11-08.md`) |
| SAM `last_input_handler` relaunches `com.webos.app.home` | **Verified** | `focus-loss-log-2026-11-08.md` (`caller_app_id":"last_input_handler"`) |
| This TV advertises `wl_webos_shell` v1, `wl_webos_foreign` v1, `wl_webos_surface_group_compositor` v1, `wl_webos_input_manager` v1 | **Verified** | 2026-11-08 dry-run globals; `ls2-register-proof-2026-11-13.md` |
| SAM-launched `wl_shell` maps 1920x1080 and holds keyboard focus until that reclaim | **Verified** | `sam-launch-success-2026-11-08.md`, `ls2-register-proof-2026-11-13.md` |
| A non-SAM `--webos-shell` surface on this TV never mapped | **Verified** | 0.5 run in README / `focus-loss-log-2026-11-08.md` |

## What 0.8 changes (shippable)

A) appinfo `main` is `wayland-hello` (the ELF). `dev/install` should now
generate a role whose `exeName` already matches `/proc/self/exe`. The
wrapper is optional and does not write LS2 files. **Hypothesis until the
next install:** the generated role names the ELF without a root edit.

B) On a SAM lifecycle-2 launch document (`interfaceMethod":"registerApp"`),
the ELF selects `--luna-register`, `--webos-shell`,
`_WEBOS_WINDOW_TYPE_OVERLAY`, demo input, and a 90 s safety cap. It
handles `registerApp` events:

- `registered` — required ack of the subscription (**verified** on this TV
  once the role named the ELF).
- `relaunch` — re-assert fullscreen (`persist: restore-foreground`). No
  extra client ack: OSE `RunningApp::sendEvent` only `respond()`s on the
  subscription
  ([RunningApp.cpp](https://github.com/webosose/sam/blob/96161d3e50670fb21daccfb12a75c35fe406ce0e/src/base/RunningApp.cpp)).
  OSE nativeqt does `QWindow::showFullScreen()` on `relaunch`
  ([ServiceRequest.cpp](https://github.com/webosose/samples/blob/df5fd71410733d120315321e30909e08864f0155/native-apps/built-in/com.example.app.nativeqt/ServiceRequest.cpp)).
- `pause` — logged; surface stays mapped.
- `close` — clean exit.

`wl_webos_surface_group` / `wl_webos_foreign` / `wl_webos_input_manager`
are **not** used. Overlay + `appId` + `displayAffinity` + `set_state` 3 is
the LSM property path this client already speaks, and OSE
`OverlayWindowModel` keeps `_WEBOS_WINDOW_TYPE_OVERLAY` above CARD
([OverlayWindowModel.qml](https://github.com/webosose/luna-surfacemanager/blob/b2fef6f73232244f6f13102aa66d2d3f5942835e/base/qml/WebOSCompositorBase/models/OverlayWindowModel.qml)).
Surface groups are for foreign/video surfaces, not this SHM probe.

## Hypothesis that needs the TV

| Claim | Why it might work | Why it might fail |
| --- | --- | --- |
| SAM-launched `wl_webos_shell` maps, unlike the 0.5 non-SAM webOS path | 0.6 showed SAM launch is what LSM maps; this TV advertises `wl_webos_shell` v1 | LSM may still ignore webOS properties from a Homebrew native |
| Overlay keeps pixels above Home's CARD at ~31 s | OSE overlay model; stock `com.webos.app.factorywin` on this TV is overlay + lifecycle 2 | `last_input_handler` may unmap every non-Home surface regardless of type |
| `relaunch` restore keeps fullscreen if SAM re-foregrounds us | nativeqt `showFullScreen` | This TV may never send `relaunch` during the 31 s reclaim |
| 90 s cap is enough to observe past 31 s | Previous reclaim is ~31.6 s | SAM `close` or killing-timer may end us first |

OSE SAM starts a killing timer on transition states except `LAUNCHING`
(10 s) and `CLOSING` (1 s)
([RunningApp.cpp](https://github.com/webosose/sam/blob/96161d3e50670fb21daccfb12a75c35fe406ce0e/src/base/RunningApp.cpp)).
That is **not** the 31 s Home reclaim (verified as `last_input_handler`).
No public source was found that a heartbeat or `setForegroundApplication`
cancels `last_input_handler` for a native Homebrew app. Overlay + mapped
`appId` is the mechanism this build tests.

`registerApp` event names (`registered`, `relaunch`, `pause`, `close`) are
documented for lifecycle v2
([com.webos.service.applicationmanager](https://www.webosose.org/docs/reference/ls2-api/com-webos-service-applicationmanager/)).
This TV is Rockhopper 6.5.3, not OSE; the event set is **hypothesis**
beyond the `registered` payload already seen.

## Host hashes (0.8, this branch)

- SDK ELF SHA256 `ef27b70fcdca93f4a71e92c530d2fefd803d5c8f8a62f078919a45c30ff00f2b`
- default IPK SHA256 `1f774ab06df06fe5b31b712fa63fbb5c377f95e11e14c9afd5df06a3ac61d054`
- lifecycle-2 IPK SHA256 `e940723ab82be2cebcd1e02639abdcf1317afba960524ebe4dd2a8069fef39dc`

ABI CHECK PASS, `e_flags 0x5000200`, max `GLIBC_2.4`. None of the binaries
are committed. Do not install `888e96b0…` or `0452e5e3…`.

## On-TV steps (lifecycle-2 persist IPK)

Copy `org.va7dimar.waylandhello_0.8.0_arm-lifecycle2.ipk` to `/tmp` and
confirm SHA256 `e940723ab82be2cebcd1e02639abdcf1317afba960524ebe4dd2a8069fef39dc`.
`</dev/null` is required because `luna-send-pub` reads stdin
(`sam-launch-success-2026-11-08.md`).

```sh
luna-send-pub -n 1 luna://com.webos.appInstallService/dev/remove '{"id":"org.va7dimar.waylandhello","subscribe":true}' </dev/null
# wait until returnValue true / NL_APP_REMOVED; OSE docs:
# https://www.webosose.org/docs/reference/ls2-api/com-webos-appinstallservice/
luna-send-pub -n 1 luna://com.webos.appInstallService/dev/install '{"id":"org.va7dimar.waylandhello","ipkUrl":"/tmp/org.va7dimar.waylandhello_0.8.0_arm-lifecycle2.ipk","subscribe":true}' </dev/null
luna-send-pub -n 1 luna://com.webos.service.applicationmanager/launch '{"id":"org.va7dimar.waylandhello"}' </dev/null
```

Leave it until it ends itself (~90 s). Then:

```sh
grep -E 'luna: exe=|luna: event=registered|Invalid permissions|sam: lifecycle2=|_WEBOS_WINDOW_TYPE_OVERLAY|webos: set_state|persist: alive|persist: restore-foreground|keyboard leave|exiting' /tmp/wh6.log
```

Success past 31 s looks like:

- `luna: exe=.../wayland-hello` (not `.../wayland-hello-launch.sh`)
- `luna: event=registered` and no `-1027`
- `sam: lifecycle2=1` and `_WEBOS_WINDOW_TYPE_OVERLAY`
- at least one `persist: alive t=` with `t=` **> 31000**
- no `input: keyboard leave surface=ours` before that, **or** a leave
  followed by enter/restore and later alive ticks
- `exiting (deadline)` near 90 s (safety cap), not a 31 s death

Fail-closed: missing webOS shell/lib exits 9; luna permission/library
failure exits 10. Do not root-edit `/var` for this run — that is what 0.8
is supposed to make unnecessary.

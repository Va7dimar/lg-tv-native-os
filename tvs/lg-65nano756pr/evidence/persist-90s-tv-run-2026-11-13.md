# 0.8 lifecycle-2 overlay: 90 s TV run — 65NANO756PR — 2026-11-13

> **Log-based result. On-screen visibility is NOT yet confirmed.** Everything
> below comes from the app's own log (`/tmp/wh6.log`) and the luna/SAM
> responses captured during the run. Nobody looked at the screen during this
> run and there is no photo. Treat "survived 90 s" as "the process and its
> overlay surface stayed alive and kept focus-leave at zero", not as "a
> visible full-screen app was on the TV for 90 s".

Companion to the plan in
[`persist-past-31s-2026-11-13.md`](persist-past-31s-2026-11-13.md), which was
written before this run. No serial, nduid or MAC is recorded here. Nothing was
flashed and no system partition was written; the app was installed only
through Homebrew `dev/install`.

## Run

| Item | Value |
| --- | --- |
| When | 2026-11-13, about 20:00 Atlantic/Reykjavik |
| TV | LG 65NANO756PR at LAN `192.168.0.8`, webOS 6.5.3 |
| Build | PR #11 head `5148055`; lifecycle-2 IPK SHA256 `e940723ab82be2cebcd1e02639abdcf1317afba960524ebe4dd2a8069fef39dc` (SDK ELF `ef27b70f…`), box build hash-matched on the TV before install |
| Install | `appInstallService/dev/remove`, then `dev/install` from `/tmp` |
| Launch | `applicationmanager/launch` (SAM), app left to end itself at its 90 s safety cap |

## Results (log-based)

| Claim | Label | Evidence |
| --- | --- | --- |
| `dev/install` auto-generated a correct LS2 role from appinfo `main` = `wayland-hello` (the ELF); no hand-edited role | **Verified (log)** | `luna: exe=…/wayland-hello`; no root edit of `/var` |
| `registerApp` succeeded, no `-1027 Invalid permissions` | **Verified (log)** | `luna: event=registered` at `t=42` ms; no `Invalid permissions` line |
| Launched as lifecycle-2 with `_WEBOS_WINDOW_TYPE_OVERLAY` via `wl_webos_shell` | **Verified (log)** | `sam: lifecycle2=1`, `_WEBOS_WINDOW_TYPE_OVERLAY` property set |
| Survived the full 90 s safety cap, past the previous ~31.6 s `last_input_handler` Home reclaim | **Verified (log)** | `focus_leave=0` for the whole run; app ended at its own deadline, not at ~31 s |
| The overlay was actually visible on screen | **Unconfirmed** | No owner glance or photo yet |

## Caveats

- The app drew only a **640x360** buffer, not a 1920x1080 full-screen frame.
- **`focus_enter=0`**: the overlay never received keyboard focus. Overlay
  windows may be non-focusable on this TV, so remote input to the overlay is
  not established.
- Because `focus_leave=0` and `focus_enter=0` together, the absence of a
  focus-leave is weaker evidence than it looks: a surface that never had focus
  cannot lose it. The ~31 s reclaim did not kill the process, but whether Home
  covered the overlay visually is unknown.
- One run only.

## Next (needs the TV, owner decides)

1. Re-run with someone watching the screen (or a photo at ~10 s and ~45 s) to
   confirm visibility.
2. Consider a 1920x1080 overlay buffer for the visibility retest.
3. Investigate whether an overlay can take keyboard focus, or pair it with a
   focusable surface.

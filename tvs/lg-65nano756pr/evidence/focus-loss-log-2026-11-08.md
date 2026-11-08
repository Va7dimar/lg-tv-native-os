# Why the test surface disappears after ~1.6 s (TV log, 2026-11-08)

Source: read-only `grep` of `/var/log/messages` over SSH, around the second 0.4 `--input --exit-on-leave` run at ~21:19:49Z. Owner saw the picture "very briefly". No screen share was active.

## Confirmed log sequence (UTC)
```
21:19:49.675 surface-manager LSM NL_VSC {"app_id":"","visible":true,"window_type":"_WEBOS_WINDOW_TYPE_CARD"}
21:19:50.187 surface-manager LSM NL_VSC {"app_id":"com.webos.app.home","visible":false,"window_type":"_WEBOS_WINDOW_TYPE_CARD"}
21:19:51.198 sam SAM NL_APP_LAUNCH_BEGIN {"app_id":"com.webos.app.home","caller_app_id":"last_input_handler","mode":"last_input"}
21:19:51.239 surface-manager LSM NL_VSC {"app_id":"com.webos.app.home","visible":true,"window_type":"_WEBOS_WINDOW_TYPE_CARD"}
21:19:51.751 surface-manager LSM NL_VSC {"app_id":"","visible":false,"window_type":"_WEBOS_WINDOW_TYPE_CARD"}
```
- Our plain `wl_shell` surface is treated as a CARD window with an **empty app_id**.
- About 1.5 s after it becomes visible, SAM's `last_input_handler` relaunches `com.webos.app.home`, which hides our surface. That matches the client's `keyboard leave` at ~t=2113 ms.
- Also seen (unrelated noise): `preloadmanager` triggers `NL_APP_LAUNCH_BEGIN` for netflix/youtube every ~7 s; load average ~30 with mostly idle CPU (D-state kernel threads).

## Interpretation (hypothesis, strong)
The foreground surface isn't tied to any app SAM knows about. The system's last-input/home fallback then reclaims the screen. The timer, the buffer lifecycle and BACK handling are not the cause.

## Candidate next steps (not yet tested)
1. In `--webos-shell` mode, set a window type other than CARD (e.g. `_WEBOS_WINDOW_TYPE_OVERLAY` / popup) through `set_property`, so the home fallback doesn't treat it as a dead foreground app.
2. Run under an `appId` that SAM actually launched (e.g. start the binary from a minimal installed homebrew native app), so the card has a live owner.
3. Find out why the 0.3 `--webos-shell` run showed nothing at all (no NL_VSC line captured yet); check the `set_state` value.

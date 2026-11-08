# SAM-launched native app holds the screen (2026-11-08)

## Result (confirmed)
At 21:44:23Z, wayland-hello 0.5 (sha256 c2132928…) was packaged as a native IPK `org.va7dimar.waylandhello` and installed via `luna://com.webos.appInstallService/dev/install`. It was then launched via `luna-send-pub -n 1 luna://com.webos.service.applicationmanager/launch '{"id":"org.va7dimar.waylandhello"}'`. In plain `wl_shell` mode (`--input --duration 30`), the full-screen 1920x1080 checkerboard stayed visible for the full 30 s; the owner photographed it. Keyboard focus was entered on all 4 seats at t=585 ms and never left. Home returned only after the app exited (`last_input_handler`, at 21:44:55).

LSM log: app_id "" visible at 21:44:24.06, home hidden at 24.58, our surface hidden at 54.05 (our exit).

## What SAM provides
- argv[1] `{"@system_native_app":true,"nid":"org.va7dimar.waylandhello"}`
- `APPID=org.va7dimar.waylandhello`, `HOME=<app dir>`, `XDG_RUNTIME_DIR=/tmp/xdg`, `QT_WAYLAND_SHELL_INTEGRATION=webos`

## Other observations
- SAM-launched `--webos-shell` CARD mode (appId/type/affinity, then set_state 3) got a frame callback but no configure, no focus and no LSM visible line, so it was not shown.
- Packaging notes: GNU `ar` (names with a trailing `/`) failed with "ipk verified failed" (errorCode -5). An ar written with plain 16-char space-padded names was accepted.
- `luna-send-pub` inside a `sh -s` stdin script needs `</dev/null`, or it consumes the script.
- appinfo used: type native, main run.sh, noSplashOnLaunch, no lifecycle-version field.

## Takeaway
Being a SAM-launched app is what stops the home fallback; the plain wl_shell path works. Not yet tested: redraw (releases=0, deferred_redraws=9), remote key handling while owned, BACK/exit lifecycle, and EGL.

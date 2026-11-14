# Photo-frame mode C (webOS CARD + appId): TV run — 65NANO756PR — 2026-11-14

The native gate from the Native Home v1 plan, step 1. Mode C draws the same
full-screen test frame as modes A and B, in green, through `wl_webos_shell`
with `appId` set and window type `_WEBOS_WINDOW_TYPE_CARD`, the type OSE SAM
counts as a foreground app. The owner watched the screen with a phone and
pressed RIGHT once at about 20 s. No serial, nduid, MAC or IP is recorded.
Install was Homebrew `dev/install` only; the app was removed afterwards.

## Build

| Item | Value |
| --- | --- |
| Source | `native-home-v1` at `2bdcb1c` (0.10-prototype plus mode C) |
| ELF | SDK build, SHA256 `f329d027e0f4731759a93638c821c0e8e2f5771559944ec9fc7bc0533daff94b`, ABI check pass |
| IPK C | `build_ipk.py --photo-frame C`, SHA256 `5a77262b09db27e626802d5529943cfab57768d5b5d71ee1f83a4f5d69dd1a1f`, hash-matched on the TV |
| Launch | `applicationmanager/launch` (SAM, lifecycle 2), 07:26:33 UTC; app ended itself at its 120 s cap |

## Results

| Claim | Label | Evidence |
| --- | --- | --- |
| Mode C is never shown | **TV-validated** | Owner: nothing showed for the whole run |
| The window is set up as asked | **TV-validated (log)** | `set_property appId=org.va7dimar.waylandhello`, `_WEBOS_WINDOW_TYPE=_WEBOS_WINDOW_TYPE_CARD`, `set_state 3` before the first commit; buffer 1920×1080 |
| Registration with SAM works | **TV-validated (log)** | luna reply `{"event":"registered","returnValue":true}` at t=79 ms |
| The compositor sends nothing back | **TV-validated (log)** | no `state_changed`, `exposed`, `close` or keyboard event in 120 s; summary `kb_enter=0 last_key=0` |
| The RIGHT press did not reach the app | **TV-validated (log)** | `last_key=0` |
| Our app may not ask SAM for the foreground app | **TV-validated** | `getForegroundAppInfo` from the dev shell: `errorCode -1`, `Denied method call "getForegroundAppInfo" for category "/"` |

## Verdict: hybrid

`wl_webos_shell` windows do not map on this firmware, whether CARD (v0.5 on
2026-11-08, mode C today) or OVERLAY (mode B). Only plain `wl_shell`
fullscreen (mode A) reaches the screen, and SAM takes it back at about 31 s.
Per the owner's verdict rule, no more native runs. Impetus Home v1 is a webOS
web app that owns the foreground; the native renderer is for later.

Before the run the estimate was about 20 % that mode C would show at all, so
this result was expected.

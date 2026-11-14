# 0.10 photo-frame modes A and B: TV runs — 65NANO756PR — 2026-11-14

Two short runs of the 0.10 photo-frame build on the rooted TV, to see which
window path actually shows a full-screen picture. The owner watched the screen
and took a photo of each run. Photos are not committed (they show the room and
broadcast content); what they show is described below. No serial, nduid, MAC
or IP is recorded. Nothing was flashed; install was Homebrew `dev/install`
only, and the app was removed afterwards.

## Build

| Item | Value |
| --- | --- |
| Source | PR #1 branch at `ff365f3` (0.10-prototype) |
| ELF | SDK build, SHA256 `fd9d3eb8129e6364be80d69cb3b10a9301f629df2246071c60547a33ecd09078` (same ELF in both IPKs, hash-checked on the TV) |
| IPK A | `build_ipk.py --photo-frame A`, SHA256 `4c34cf5aa678ff6eefa65672ce710aeb020f5627e81c715edc59b1639b523cc2` |
| IPK B | `build_ipk.py --photo-frame B`, SHA256 `d837d1e334b7367e40e9826727218d4ee05b6c96518b26014cbb94ef882ae7a3` |
| Launch | `applicationmanager/launch` (SAM, lifecycle 2); app ends itself at its 120 s cap |

## Results

| Claim | Label | Evidence |
| --- | --- | --- |
| Mode A (`wl_shell` fullscreen) shows a 1920×1080 magenta frame with all four corner labels inside the visible area | **TV-validated** | Owner photo at T=15s: magenta, TL/TR/BL/BR boxes at the panel edges, text "MODE A FOCUSABLE FULLSCREEN / 1920X1080 / FOCUS ENTER=3 LEAVE=0" |
| Mode A gets keyboard focus on all three seats at about 0.6 s | **TV-validated** | log `keyboard enter seat=2/1/0` at t=580–647 ms; photo shows ENTER=3 |
| Mode A loses the screen to Home at about 31 s; the process keeps running hidden to the cap | **TV-validated** | owner saw magenta about 30 s, then Home; log `keyboard leave` ×3 at t≈31.7 s, ticks continue to s=119 |
| No remote key reached mode A | **TV-validated (log)** | summary `last_key=0` in both mode A runs |
| Mode B (`_WEBOS_WINDOW_TYPE_OVERLAY` via `wl_webos_shell`) is never shown | **TV-validated** | owner photo: TV picture with the system loading spinner, no magenta, for the whole run |
| Mode B: the compositor sends nothing back to the overlay surface | **TV-validated (log)** | after `set_property` appId / window type / `set_state 3`: no `state_changed`, `exposed`, `close` or keyboard events in 120 s; `kb_enter=0`; luna `registered` OK |

## What this means

- Mode A is the working path: a visible full-screen native app, but only for
  the ~31 s before SAM's last-input handler brings Home back
  (see [`last-input-30s-mechanisms-2026-11-09.md`](last-input-30s-mechanisms-2026-11-09.md)).
- Mode B's overlay surface is accepted and committed but never mapped, and SAM
  keeps its loading spinner up while it waits. This also settles the open
  question in [`persist-90s-tv-run-2026-11-13.md`](persist-90s-tv-run-2026-11-13.md):
  the 0.8 overlay that "survived 90 s" was most likely alive but invisible.
- Cosmetic: in mode A the `KEY=` line draws just below the black text panel.

# wayland-hello 0.2 `--input` runs on the TV (2026-11-08 ~19:18 Atlantic/Reykjavik)

The owner approved the run. Binary sha256 `e17de5a551556df66efdc5dc7bcfa51f6c3c843bae83ee1b72c26cc14a8fe99f` (SDK build of main 43a2c2a), run from `/tmp` as root, launched with `XDG_RUNTIME_DIR=/tmp/xdg WAYLAND_DISPLAY=wayland-0 ./wayland-hello2 --input --duration 15`. Both runs exited 0, ending with `info: exiting (deadline)`.

## Confirmed (from the log)
- Three `wl_seat` v3 globals (4, 17, 18) are bound. All three report caps=0x7 (pointer, keyboard, touch) and no seat name.
- Each seat sends an xkb_v1 keymap of 64099 bytes.
- The surface was committed at 640x360, and the compositor configured it to 1920x1080.
- Run 2: the IR/Magic Remote arrows arrived on **seat index 1 (global 17)** as standard evdev codes: UP=103, RIGHT=106, LEFT=105, DOWN=108 (XKB = code+8), each with press and release. The square moved on every press.
- No BACK (158), EXIT (174) or ESC (1) code was logged.
- Keyboard `leave` came on all seats after the last key. Each process then ran until its deadline.
- Owner report: the normal picture came back by itself, and it "was not 15 seconds" on screen.

## Open
- Whether BACK is consumed by the system (webOS normally reserves BACK/HOME for its own handling), or simply was not pressed.
- Why focus moved away early: the `keyboard leave` probably marks when the surface lost focus or was hidden. Check its timing against when the picture disappeared.
- The deadline is counted from connect, not from first frame/focus.

## Next
- v0.3: monotonic timestamps on every log line; start the deadline at the first configure; log keyboard enter and leave plus any surface or shell state changes with times; optional `--webos-shell` to test whether LG's shell keeps the surface in focus and delivers BACK.

## Correction appended 2026-11-08 (does not rewrite the capture above)

The bullets under "Confirmed" are the 0.2 log and the owner's words from that run. They stay as written.

Later client wording treated "the square moved" and a countdown armed at the first commit as if those were proof of how long pixels stayed on screen. They are not. A client-side model update, a queued commit, keyboard enter/leave, buffer release, and `wl_callback.done` each say only what they say. Visible pixels are a separate owner observation.

Owner report after the 0.3 build, not a line from the capture above: plain `--input` lost keyboard focus about 2.2 s in and the picture went away immediately. `--webos-shell` showed nothing and received no focus. The TV's `libwayland-webos-client` has no `set_key_mask`. No registration or opcode change is justified by that report. 0.4 only adds telemetry, including an explicit log when a resize destroys a buffer that has not been released.

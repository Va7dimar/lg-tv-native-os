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

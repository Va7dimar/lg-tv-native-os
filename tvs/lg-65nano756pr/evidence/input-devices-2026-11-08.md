# Input devices (read-only probe, 2026-11-08 ~19:05 Atlantic/Reykjavik)

Source: `/proc/bus/input/devices`, `ls -l /dev/input`, `/dev/watchdog*`, `systemctl is-active hw_watchdog` over SSH as root. Nothing was written.

## Confirmed
| Device name | Handlers |
|---|---|
| CHECK INPUT | kbd event0 |
| LGE RCU (IR remote) | kbd event1 |
| Bluetooth-audio-source | kbd event2 |
| LGE M-RCU - Builtin [0..2] (Magic Remote) | kbd mouseN jsN event3-5 |
| LGE TONE+ - Builtin [3] | kbd mouse3 js3 event6 |
| LGE Simple Premium | kbd mouse4 js4 event7 |
| IoT keypad | kbd event8 |

- `/dev/input/event*` are `root:composit 0660`; `mouse*`/`js*` are `root:input`.
- `/dev/watchdog` exists; `hw_watchdog` systemd unit reported `inactive` at probe time (exit 3).

## Implications (hypothesis)
- The normal route for app input is the compositor's `wl_seat` (surface-manager owns evdev). Reading evdev directly as root is possible but would compete with surface-manager; prefer `wl_seat` in wayland-hello v2.
- Watchdog behaviour is still untested; `inactive` unit does not prove no kernel/hardware watchdog is armed.

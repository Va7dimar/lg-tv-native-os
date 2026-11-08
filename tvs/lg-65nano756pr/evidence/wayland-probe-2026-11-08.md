# First on-TV run: wayland-hello --dry-run (2026-11-08 18:42 Atlantic/Reykjavik)

Owner approved ("Yes, run the probe now"). Binary copied to `/tmp/wayland-hello` (tmpfs, cleared on reboot)
via `scp -O` from AC-009. SHA256 on TV `be28a8fd...5581a` matched the box build (prototypes/wayland-hello/build/arm).
Command: `XDG_RUNTIME_DIR=/tmp/xdg WAYLAND_DISPLAY=wayland-0 ./wayland-hello --dry-run --duration 5` as root.
Result: exit 0 in under a second, no surfaces created, no services touched.

## Confirmed facts
- The webOS-toolchain ARM binary (soft-float, GLIBC_2.4 max) **loads and runs natively on the TV**: dynamic linking,
  libwayland-client and the ABI all work in practice.
- A root client can connect to the stock compositor socket `/tmp/xdg/wayland-0` (owner root, group `composit`, mode 660).
- The compositor advertises 18 globals:
  wl_compositor v3, wl_shm v1, mali_buffer_sharing v5, wl_seat v3 (x3), wl_webos_surface_group_compositor v1,
  wl_webos_foreign v1, wl_output v2, **wl_shell v1**, text_model_factory v1, input_method v1, input_panel v1,
  wl_webos_xinput_extension v1, wl_starfish_output v1, wl_starfish_pointer v1, **wl_webos_shell v1**,
  wl_webos_input_manager v1.
- `wl_shell` is present, so the prototype's provisional shell choice is available. `wl_webos_shell` is the
  native webOS shell extension the stock apps likely use (it's needed for full-screen/focus and remote keys).

## Not yet known
- Whether a plain wl_shell surface is actually shown, gets focus, or gets stacked above the stock UI
  (the compositor may require wl_webos_shell or an app id).
- Remote-control input delivery (wl_seat vs wl_webos_input_manager).
- Behavior across standby/snapshot.

## Next gate
10-second full-screen surface run (`./wayland-hello --duration 10`), needs a separate owner notice.

# Second on-TV run: 10-second full-screen surface (2026-11-08 18:47 Atlantic/Reykjavik)
Owner approved ("Yes, run the 10-second test now"). Same binary (SHA256 verified again).
Command: `XDG_RUNTIME_DIR=/tmp/xdg WAYLAND_DISPLAY=wayland-0 ./wayland-hello --duration 10`
Ran 18:47:28 to 18:47:38. Exit 0 by deadline, no leftover process.

## Confirmed
- The compositor accepted a plain **wl_shell** surface from a root client (committed 640x360, then the
  compositor sent configure 1920x1080, which the app clamped/used).
- **Owner visually confirmed:** a test pattern/solid color appeared full-screen, then the normal picture
  came back automatically after exit.
- So a custom native app can take over the screen on the stock signed kernel without touching any
  system partition, and it releases the screen cleanly when it exits.

## Still unknown
- Remote-control input (wl_seat / wl_webos_input_manager) is untested.
- Whether wl_webos_shell gives better focus, stacking or key routing.
- Behavior across standby/snapshot. GPU (EGL/mali_buffer_sharing) rendering is untested; this run used shm.
- Persistent or startup launch hasn't been attempted.

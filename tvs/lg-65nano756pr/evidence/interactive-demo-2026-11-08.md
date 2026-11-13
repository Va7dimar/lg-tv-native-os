# v0.6 interactive demo on the TV (2026-11-08 21:52Z)

IPK sha256 1132d137… and binary 54bcb2f2… were rebuilt on the box, and both hashes match PR #7. The app was installed via appInstallService and launched by SAM.

## Confirmed
- The full-screen checkerboard (1920x1080 configure) took focus at t=586 ms on all 4 seats. The owner photographed it.
- 11 RIGHT/arrow presses arrived on seat 1 (evdev 106). Each queued a redraw on an alternating spare buffer (gen 2/3), and each got a frame callback ~95 ms later. The owner confirmed the green square moves with the arrows.

## New limit found
- At t=31.67 s (21:53:09Z), about 9 s after the last key press and ~31.5 s after launch, SAM `last_input_handler` relaunched `com.webos.app.home`. Our surface lost focus and was hidden, but the process kept running until I killed it.
- Hypothesis: SAM expects a native app to register on the luna bus (applicationmanager registerApp / nativeLifeCycleInterfaceVersion) within ~30 s, and otherwise treats the launch as failed. The 30 s v0.5 run ended at the boundary, so it couldn't show this. The TV has /usr/lib/libluna-service2.so.3, libpbnjson_c.so.2 and libglib-2.0.so.0.

## Not yet tested
BACK/EXIT exit path, luna registration, EGL.

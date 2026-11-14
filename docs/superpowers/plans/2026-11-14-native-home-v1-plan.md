# Native Home v1 — plan (2026-11-14)

Spec: [`../specs/2026-11-14-native-home-v1.md`](../specs/2026-11-14-native-home-v1.md).
Every TV install, launch, push and merge needs the owner's yes in the session.
Never write kernel, rootfs or tvservice; userspace and `dev/install` only.
Host tests: `make test` in a Debian container (smoke checks only, one per new path).

## Step 1 — Gate: mode C (CARD + appId)

- `photo-frame` sidecar gains `C`: `wl_webos_shell`, `appId`, window type
  `_WEBOS_WINDOW_TYPE_CARD`, `set_state` fullscreen, same magenta frame.
- One mock-compositor check that mode C sends CARD and appId.
- TV run (yes needed): owner photographs at ~15 s and after 31 s, presses one
  arrow at ~20 s. Also read `getForegroundAppInfo` once during the first 20 s.
- Evidence note under `tvs/lg-65nano756pr/evidence/`.
- **Pass** (visible past 31 s and `keycode raw=` in log): continue. **Fail**: stop
  native; re-plan the same steps as a web app (hybrid), no more native tries.

## Step 2 — HDMI switch from our app

- Find the input-switch luna call on this firmware (read-only `ls-monitor` /
  service list), then call it from the app on OK.
- TV run: OK switches to the Apple TV input. Evidence note.
- If our role is refused, record it and decide in-session (permissions vs a
  root helper).

## Step 3 — Text and look

- Vendor `stb_truetype.h` (public domain) into `src/third_party/`.
- Convert the Impetus woff2 faces to TTF on the PC; ship them with licences
  under the app dir in the IPK.
- `draw_text()` with alpha blending into the shm buffer; Impetus colour tokens
  as constants in one header.
- One host check: a known string renders non-empty in the expected box.

## Step 4 — Home screen

- Clock (Syncopate) + date (Plex Mono), grid with the Apple TV tile first and
  focused; arrows move the off-white focus ring; OK on Apple TV calls step 2.
- Redraw once a second for the clock only.
- TV run: photo of the screen, focus moved by arrows.

## Step 5 — Watchdog and restore

- Launcher script: start the ELF; if it exits or writes no first-frame marker
  within 10 s, switch to the Apple TV input.
- README: the one-line SSH restore of LG Home.
- TV test: crash it on purpose (bad sidecar) and see the Apple TV appear.

## Step 6 — Replace Home

- Apply the Home Chooser method for our app id; read back what it set.
- TV test: power cycle, our Home comes up; then the SSH restore works.
- Milestone run: 10 minutes visible, arrows, OK to Apple TV. Photo or video
  plus log; evidence note; README status line.

## Step 7 — Lockdown (later, separate grilling)

Network block and LG daemon review, after v1 is in daily use.

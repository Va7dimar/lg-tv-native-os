# Native Home v1 — spec (2026-11-14)

Settled in a design grilling on 2026-11-14. The owner's goal: a fun project where
he designs the OS of his LG 65NANO756PR. LG's webOS stays underneath (custom-OS
boot stays no-go: no recovery route). What we build is the part he sees.

## Decisions (owner)

1. Output: this spec, a plan, then the build.
2. Goal: design the TV's OS as a shell on the stock base.
3. Route: native first; hybrid (web shell, same design) only if native fails the gate.
4. Gate: one TV run of **mode C** (`wl_webos_shell`, appId set,
   `_WEBOS_WINDOW_TYPE_CARD`). Pass = visible past 31 s **and** one arrow key in
   the log. Fail = switch to hybrid, no further native experiments.
5. Security lockdown (network block, stopping LG daemons) comes **last**.
6. v1 = home grid + clock in the Impetus look.
7. Text via `stb_truetype` compiled into the ELF; fonts shipped in the IPK.
8. v1 replaces LG Home.
9. Failsafe: watchdog switches to the Apple TV HDMI input if our app exits or
   shows no frame within 10 s; one-line SSH restore in the README.
10. Apple TV tile, first and focused; OK switches to that input.

## Milestone (recommendation taken)

Our Home comes up at boot, stays visible 10 minutes, arrow keys move focus and
OK on the Apple TV tile switches input. Proof: photo or video plus log.

## Look (from Impetus `src/app/globals.css`, ruled 2026-09-16)

| Token | Value | Use here |
|---|---|---|
| ground | `#000000` | background |
| pane | `#0D0E10` | tiles |
| line | `#34383E` | tile at rest |
| muted | `#8E959F` | secondary text |
| text | `#E6EAF1` | primary text, focus ring |
| violet | `#A394F5` | discovery only, never chrome or focus |

Fonts: IBM Plex Sans (body), IBM Plex Mono (status), Syncopate Bold (clock /
display). All are open-licensed; licence files ship next to them.

## Screen

- Clock top-left in Syncopate; date under it in Plex Mono, muted.
- Tile grid below: Apple TV (focused at start), then placeholder tiles.
- Focus = off-white ring; rest = line colour.

## Out of scope for v1

App launching, status bar, other HDMI inputs, the lockdown (decision 5).

## Open (decided in the plan's steps)

- Does the HDMI-switch luna call work from our app's role? Tested right after the gate.
- Does Home replacement (the Home Chooser method) work for a native app?

## Rejected

Hybrid now (owner wants native first); TV FreeType (ties to LG's ABI); glyph
atlas (fixed sizes); launch-only v1 (owner chose Home); CEC alone (unverified).

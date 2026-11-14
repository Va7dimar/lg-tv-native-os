# Impetus Home: design (2026-11-14)

The TV home in the Impetus system. Source of truth for tokens and rules is the
owner's Impetus repo (`.design-sync/guidelines`, `docs/impetus/design-vision/`);
this file only extends them to a 1920×1080 TV seen from about 3 m, driven by a
remote (arrows, OK, BACK) in webOS 6's Chromium 79.

Two rooms, the site's own idea: a **living room** at rest, and a **control
room** that turns over it on any key.

## Room 1: the living room

**Problem.** The TV's rest state should be ours and alive, not a launcher.
Owner's rule: "a dark, quiet place with one green thing alive inside it, too big
for the frame".

- **The sky.** True black, the one light at the upper left (`#E6EAF1` 10 % at
  22 %/18 %), and a horizon: one 2 px line in `--color-line` running the full
  width low in the frame (64 % down, leaving the ground below for the clock). Close and low, never a diagram view: no
  axis, no ticks, no labels on it.
- **The green thing.** The sun, computed on the TV for Reykjavík (no network).
  Today's path is a shallow arc drawn 1 px in `--color-line`, scaled so it spans
  wider than the screen and runs off both edges. The part already travelled
  since sunrise is in `--color-text`. The sun itself is a point of
  `--color-text` on the arc carrying the green halo (`--color-brand-light`,
  quiet fill `--color-brand-quiet`). Below the horizon (night) the point sinks
  under the line and only a dim green glow spills up over it.
- **Data.** The clock in Plex Mono, monumental (180 px), bottom left on the
  ground below the horizon. Under it the date in Unbounded, muted, and one line
  `sólarupprás 09:54 · sólsetur 16:31 · 6 klst. 37 mín.` (words in Unbounded,
  numbers in Plex Mono, case rule: mono is data).
- **Motion.** Still. The sun moves at the speed of the real sun; the redraw is
  once a minute. Nothing floats or pulses.

## Room 2: the control room

**Problem.** One press must reach the Apple TV, and the rest of the TV must be
one press further, without becoming a grid of equal cards (rejected by the
system: "a page is a few strong objects placed with intent").

- **Arrival.** Any key on the living room turns the page, the site's room turn
  (decision 40): the living room drifts up two thirds and tips back
  (`perspective(1400px) rotateX(10deg)`), the control room slides over it at
  full size, 1400 ms on the in-out curve `cubic-bezier(0.77,0,0.175,1)`. BACK,
  or 60 s with no key, turns it back. The key that opens the room does nothing
  else. The room is a full slab (top light, slab gradient) with the 140 px lead
  band of `--color-text` washing its top edge.
- **APPLE TV**: the focal object. A large pressable slab at the left, wider than
  everything else, `APPLE TV` in Syncopate 700 caps, 72 px, too big for its
  slab's comfort. It has focus when the room arrives, so OK goes straight to
  HDMI 2.
- **Shortcuts** (`STYTTINGAR`): a row of pressables under it, each a TV app
  opened at a set place (webOS deep link). Two lines per face: the app in
  Syncopate caps, the place in Unbounded muted. Listed in `config.js`.
- **Apps** (`FORRIT`): the rest as a column list, not a card grid. Each app is a
  long, low pressable bar, its name in Syncopate caps 26 px. Two columns of six;
  more scroll inside the column.
- **Connections** (`TENGINGAR`): a 340 px slab at the right edge (the site's
  found-slab width). The open count in Plex Mono 96 px, then the five newest as
  `process → host` in Plex Mono 20 px, muted; a new row comes in at the top in
  `--color-text` and settles to muted. It is read (flat, no wall), never
  focusable. Refreshed every 5 s, only while the room is open.

## Shared rules

| Rule | Value | Source |
|---|---|---|
| Pressable | 3 px wall in `--color-key-wall`, bottom right | decision 25 |
| Read-only | flat slab, no wall | decision 12 |
| Focus | green halo + 2 px `--color-text` ring set 2 px out; snaps, no transition | brand digest |
| Press (OK) | face drops 3 px onto its wall with no transition; a faint green halo flares | decision 14 (key actions do not animate), brand reading 9 |
| Slab gap | ground only, never a rule; 16 px at TV scale | inherited 8 px, ×2 |
| Text | Syncopate 700 caps for doors, Unbounded for reading, Plex Mono for data only | type.md |
| Navigation | arrows move to the nearest focusable in that direction (spatial) | new |

## Chromium 79 (webOS 6) notes

- No flexbox `gap` (Chromium 84+): spacing is margins.
- The page is laid out at 1920×1080 and scaled with `zoom`, not `transform`,
  so the layout box matches the window and nothing can scroll it.
- No `scrollIntoView` on focus: the v1 build scrolled the whole page down.

## Open

- Deep-link parameters for the shortcuts are unverified on this TV; the owner
  edits `config.js` after the first run.

## Default Home

Home Chooser is absent on this TV, so Impetus becomes the default through a
Homebrew boot hook (`boot/impetus-home`, installed as
`/var/lib/webosbrew/init.d/impetus-home`, mode 755). It opens Impetus once the
system is up and again whenever stock Home comes to the front, and it never
gives up. Pause: `touch /tmp/impetus-pause`. Way back: delete the hook and
restart the TV.

## Limits of this build

- Up to 3 shortcuts and 12 apps are shown; the rest are named in a note and
  ordered or hidden in `config.js`.
- The horizon sits at 64 % down (not 78 %) so the clock, date and sun line fit
  on the ground below it.

## Control room v2: grilling record (in progress, 2026-11-14)

Alignment grilling on wow, usefulness and uniqueness. Critique of the 1.1.0
render: the focal APPLE TV slab is empty, the 12 equal app bars read as a
launcher, and the side-feature connections panel holds the second-best spot.

Settled by the owner:

1. Output: this file gets the decisions; the build follows on this branch.
2. The APPLE TV slab shows a live still of HDMI 2 (video-plane capture through
   `com.webos.service.capture/executeOneShot`), refreshed about every 3 s while
   the room is open, dimmed under the APPLE TV type; plain slab on a black or
   failed capture. Test first on the TV: whether the HDMI picture keeps running
   while Impetus is in front (else the still is the last frame or black), DRM
   apps capturing black, and whether the page can show a file from `/tmp`.
3. This round builds TV controls and an engine room (a third room). Not this
   round: the room learning the hour (local open-log reorders apps), aurora and
   weather in the sky.
4. Layout: APPLE TV and shortcuts left, apps middle, a column of TV controls
   right (STJÓRN), ending with the engine room door (VÉLARRÚM). Connections,
   TV vitals and a live log move into the engine room.
5. SVEFN: OK cycles 30 / 60 / 90 min / off; the face shows the end time
   (SVEFN 23:40). The timer runs as a root job on the TV and ends in standby,
   never a reboot.
6. SKJÁR AF (screen off, sound on) is the first control.

Open, for the next grilling session:

- The third control slot. The owner rejected volume ("something else, think on
  it"). Put forward: SÓLARHAMUR (the computed sun drives backlight and colour
  temperature after sunset; recommended), HLJÓÐ Í HEYRNARTÓL (sound to
  Bluetooth headphones), APPLE TV VAKNA/SOFA (HDMI-CEC). Each needs a check on
  the TV first.
- Engine room content and how it is reached; pre-mortem, rollback, security
  of root exec from the page, cost.

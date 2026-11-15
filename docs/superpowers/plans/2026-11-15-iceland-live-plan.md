# Impetus Home: Iceland, live (#26). Build plan (2026-11-15)

Issue: [#26](https://github.com/Va7dimar/lg-tv-native-os/issues/26). The owner judged the
mock "build it" on 15.11.2026 (mock: claude.ai artifact `59dGTWGiMSMAtuawuqvLZc`, private).
App: `prototypes/impetus-home/`. Rules it extends: `prototypes/impetus-home/DESIGN.md`.

Every IPK install on the TV, every push, PR and merge needs the owner's yes in the session.
The bar from the issue holds for every step: the room ships only if it looks like the mock.

## What the room is

A fourth room, **ICELAND**, read only, one full 1920x1080 picture as in the mock:

- Black ground, the room's top light, the coast "shelf" (the coast echoed outward as faint
  depth lines), land as a dark slab, glaciers as a faint white wash, the volcanic-zone seam
  as a soft ember band (the mock's hand sketch, orientation only).
- Every earthquake of the last 48 h as warm light: size by magnitude, white-hot when fresh,
  ember after a day, fading to nothing at 48 h. The newest one ripples.
- Reykjanes in a round lens, 3.1x, bottom left, with its count line.
- Top left: `ICELAND · NOW`, the 48 h count in Saira 300 at 180 px, a few region rows.
- Bottom: the 48 h tick ribbon (taller = stronger), `48 h ago` to `now`.
- Top right: the source line (`Icelandic Met Office · updated 00:05`) and the magnitude and
  age legend. Bottom right: the map credit (CC BY 4.0 needs it on screen).
- Webcam window and flight tracks: real sources chosen below; until a step builds one, it is
  not drawn (no placeholders on the TV).

## 1. Reaching it and leaving it

- **In:** a new door `ICELAND` in the control room, in the scenes column under `ENGINE ROOM`.
  Both doors shrink from 98 px to 80 px tall so the column still ends above 1080 (measured in
  the preview in step 3; if it does not fit, the door goes under SHORTCUTS in the main column).
- **Turn:** the same room turn as the engine room (`body.deep`-style class `iceland`), 1400 ms.
- **Out:** BACK returns to the control room, focus on the `ICELAND` door. Any app opened by
  the keeper (sleep notice) wins as it does today.
- **No idle timeout** in this room (derived): it is a resting view like the living room, so the
  60 s "back to the living room" does not apply. The TV is LCD (no burn-in). Other keys do
  nothing; there is nothing to focus.
- The room only fetches while it is open (plus one fetch on the way in). Leaving it stops all
  its timers, as `setRoom` already does for the other rooms.

## 2. The quake feed

**Source (checked 15.11.2026 00:20 UTC).** `api.vedur.is/skjalftalisa/v1/quake/array` still
answers 404. `https://en.vedur.is/earthquakes-and-volcanism/earthquakes/` answers 200, UTF-8,
about 30 KB, `Cache-Control: max-age=88`, and carries one inline array:
`quakeInfo = [{'t':new Date(2026,11-1,15,0,4,18),'a':'…','lat':'63.910','lon':'-21.186','dep':'5.5','s':'0.4','q':'50.0','dL':'9.4','dD':'WSW','dR':'Selfoss'}, …]`.
Times are UTC, `s` is magnitude, `q` quality, `dR` the nearest place. The response has **no
`Access-Control-Allow-Origin` header**.

**Fetch path on the TV.** Two candidates, step 1 decides on the TV:

1. **Helper verb (default).** `impetus-ctl iceland quakes`: a fixed URL inside the helper
   (the page sends no URL, so nothing can be injected), fetched with whatever the TV has
   (`curl`, else busybox `wget`; step 1 reads which exist and whether busybox `wget` speaks
   https), 10 s cap like every other call, written to `/tmp/impetus/iceland/quakes.txt` with
   its fetch time, then printed. Read only: it never takes the helper's lock, so it can never
   delay a scene, the still or `restore`.
2. **Page XHR.** Only if step 1 shows the webOS web app (served from `file://`) is not held to
   CORS on this TV. Simpler, but unverified; the helper path is planned so nothing waits on it.

**Refresh.** On entering the room: draw the cached copy at once (with its own age in the
source line), then fetch. While open: every 120 s (the page's cache is 88 s; the IMO list
updates every few minutes). Never more than one fetch in flight.

**Parsing.** A pure function `parseQuakeInfo(text)` in `logic.js`, ES5, no `eval`: cut the
`quakeInfo = [ … ];` slice, match each `{…}` object with a regex, read `new Date(y,m-1,d,h,mi,s)`
as `Date.UTC`, numbers with `parseFloat`. An entry is kept only when lat is 62.5–67.5, lon is
-25.5 to -12.5, magnitude -1 to 8, and its time lies within the last 49 h. Host tests run it
against a saved fixture of the 15.11 page (public data, trimmed to the array).

**Feed down (the calm rule).** Any failure (no answer in 10 s, not 200, no `quakeInfo`, zero
valid entries while the page had some) is the same quiet state:

- the source line turns to `Icelandic Met Office · feed down since 14:02` in `--muted`;
- the quakes already drawn stay and keep ageing (they fade on their own clock), so after 48 h
  the room is the island and that line;
- never an error box, a spinner, a toast or a blink; retries continue at 120 s;
- the page never waits on a fetch before drawing or before handling a key, so nothing here
  can block Home, the control room or BACK.

## 3. The shield

Checked 15.11.2026: `app/shield/hosts.txt` holds 45 names, all LG ad, tracking and
content-recognition hosts (`lgads.tv`, `*.lgsmartad.com`, `*.lgtvcommon.com`, `*.lgtvsdp.com`,
`alphonso.tv`, `ad.lgappstv.com`). **None blocks `vedur.is`**, nor the flight or webcam hosts
below. Step 1 adds a host test that fails if any shield line matches a feed host this room
uses, so a later edit to the list cannot break the room silently.

## 4. Map assets

- **Coast:** geoBoundaries ISL ADM0, simplified (CC BY 4.0, Landmælingar Íslands).
- **Glaciers:** Natural Earth 10 m glaciated areas (public domain), from the GeoJSON in the
  `natural-earth-vector` repository, so the build needs no shapefile reader.
- **Build script** `scripts/build_iceland_map.py`, Python standard library only: download
  both, record URL, bytes and SHA-256 in the output's header, project as the mock does
  (equirectangular, `x = 600 + (lon + 24.6) * 250 * cos 64.9°`, `y = 120 + (66.6 - lat) * 250`),
  simplify with RDP at 0.45 px, a finer pass for the Reykjanes lens, one decimal per number.
- **Output** `app/iceland/map.js` (`window.ICELAND_MAP = {coast, glac, coastFine}`, about
  45 + 8 + 79 KB) plus `app/iceland/LICENSE-map.txt`. The generated file is committed; the raw
  downloads are not. Same input, same bytes (the IPK rule).

## 5. Webcam: options

| Option | What the owner sees | What it costs |
|---|---|---|
| **A. Still frames (recommended)** | One frame from a public camera near Reykjanes, refreshed every 60 s, dimmed like the APPLE TV still; hidden when the frame is dark (the existing `isDark`) or the source fails | One helper verb with a fixed JPEG URL, about 100-300 KB a minute while open. The source and its terms are picked and checked in step 6. In November it is dark most of the day, so the window is often absent |
| B. Live eruption stream (RÚV or Míla, YouTube or HLS) | Moving fire during an eruption | Video decode next to the map on Chromium 79 (frame-rate risk); a YouTube embed inside a webOS web app is untested; Míla's terms unclear; the stream exists only during eruptions |
| C. No webcam | The map gets the space | Nothing; loses the eruption moment |

## 6. Flights: options

| Option | What the owner sees | What it costs |
|---|---|---|
| **A. adsb.lol (recommended)** | Real aircraft as small arrows with short trails | No key, ODbL (credit on screen). Answered 200 on 15.11 00:20 UTC (one ground vehicle at night). One call per 60 s for 250 nm around 64.9 N 19 W, via a helper verb. Trails are built on the TV from the last ten positions. Community receivers: coverage over the sea may be thin |
| B. OpenSky Network, free account | The same | Answered 200 anonymously (empty at night). Anonymous credits allow one call every ~7 min; a free account allows ~60 s but needs an OAuth client secret kept on the TV (app folder, never in git). Non-commercial terms |
| C. Own ADS-B receiver (RTL-SDR on a Pi) | Local aircraft only, line of sight from home | About €40-60 and one more box to run; no third party |
| D. No flights | Map only | Nothing |

`airplanes.live` was tried and refused without contacting them (403): rejected.

## 7. Performance on the TV (Chromium 79)

- **Rules kept:** ES5 only, no flex `gap`, no `inset`, the stage scaled with `zoom` on body,
  no `perspective` on the zoomed stage (it goes inside the moving room's own transform).
- **Three layers**, so motion never repaints the map:
  1. `#iceland-base`: one SVG with the shelf, land, glaciers, seam, places, lens frame and
     credit. Drawn once per room open, never touched again.
  2. `#iceland-quakes`: one SVG with the quake lights, the lens contents, the ribbon and the
     counts. Redrawn only when data arrives (120 s) or once a minute for ageing.
  3. `#iceland-motion`: HTML elements over the SVG for the ripple and the "breathing" of quakes
     under 6 h old, animated with CSS `transform` and `opacity` only (composited, no repaint).
- **No `mix-blend-mode`** and no `feGaussianBlur` on anything that moves: the mock used both.
  The seam blur is drawn once in layer 1; the quake glow is a radial gradient fill, not a
  blend. Quake glows are capped at 400 drawn (the mock had 74).
- **Measured, not assumed:** a preview flag `?fps=1` shows frames per second; on the TV the
  target is 30 fps or better during the ripple, and the engine room's CPU temperature no
  higher after 10 min in the room than in the living room. If the target is missed, the
  ripple and breathing go first; the still picture stays.

## 8. Steps (one PR each)

Each step updates `DESIGN.md` (a "Room 4: Iceland" section), `TV-SESSION.md` (its own check)
and the README's query table for what it adds. A step that is installed on the TV bumps the
app's minor or patch version and is installed only with the owner's yes.

1. **Feed path and parser.** `parseQuakeInfo` in `logic.js` with tests on the 15.11 fixture
   (valid, bad entries, empty array, page without `quakeInfo`); helper verb `iceland quakes`
   with a stand-in in `tests/stubs/` and checks in `test_ctl.sh`; the shield-vs-feed host test.
   **TV check (SSH, no install):** which of `curl`/`wget` exist and speak https; `$CTL iceland
   quakes` prints the array in under 10 s; one XHR from the installed app's page to the IMO
   URL (via the Web Inspector or a one-line test page) to settle helper vs page fetch.
2. **Map assets.** `scripts/build_iceland_map.py`, `app/iceland/map.js`, the licence file;
   `test_ipk.py` checks the new files are in the package and the build gives the same bytes
   twice. **Check:** preview draws the island at 1920x1080; no TV step.
3. **The room, still.** `#iceland` in `index.html`, its CSS in `home.css`, drawing in a new
   `app/iceland.js` (layers 1 and 2, lens, ribbon, header, legend, credit) from the cache or a
   preview fixture (`?room=iceland&quakes=fixture`); the ICELAND door and BACK in `home.js`.
   **TV check (install, yes needed):** the owner opens it from the control room, BACK returns
   to the door, and judges it against the mock on the same 65" screen.
4. **The room, live.** 120 s refresh while open, cache-first entry, ageing each minute,
   layer 3 motion (ripple on a new quake, breathing), the feed-down line
   (`?feed=down` in the preview), `?fps=1`. **TV check:** 10 min in the room with the fps
   readout; pull the network cable for one refresh and see only the quiet line change,
   then plug it back and see the line recover; press BACK and open the Apple TV during a fetch:
   no delay.
5. **Flights** (the source chosen below): helper verb, trails, credit, its own quiet "down"
   state. **TV check:** arrows move over 5 min; the fps target still holds.
6. **Webcam** (the source chosen below): helper verb, window placed where the mock had it,
   hidden when dark or down. **TV check:** a frame shows in daylight and is gone after dark.

Steps 5 and 6 are independent of each other and can run in parallel after step 4.

## 9. Open (the owner decides)

- Webcam source (section 5) and flight source (section 6).
- The derived choice that the room has no idle timeout (section 1), if the owner wants one.

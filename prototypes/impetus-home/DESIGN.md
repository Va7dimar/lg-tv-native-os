# Impetus Home: design (2026-11-14)

The TV home in the Impetus system. Source of truth for tokens and rules is the
owner's Impetus repo (`.design-sync/guidelines`, `docs/impetus/design-vision/`);
this file only extends them to a 1920×1080 TV seen from about 3 m, driven by a
remote (arrows, OK, BACK) in webOS 6's Chromium 79.

Three rooms, the site's own idea taken one step down: a **living room** at
rest, a **control room** that turns over it on any key, and an **engine room**
behind a door in the control room. Every name on screen is English.

## Room 1: the living room

**Problem.** The TV's rest state should be ours and alive, not a launcher.
Owner's rule: "a dark, quiet place with one green thing alive inside it, too big
for the frame".

- **The sky.** True black, the one light at the upper left (`#E6EAF1` 10 % at
  22 %/18 %), and a horizon: one 2 px line in `--color-line` running the full
  width low in the frame (64 % down, leaving the ground below for the clock).
  Close and low, never a diagram view: no axis, no ticks, no labels on it.
- **The green thing.** The sun, computed on the TV for Reykjavík (no network).
  Today's path is a shallow arc drawn 1 px in `--color-line`, scaled so it spans
  wider than the screen and runs off both edges. The part already travelled
  since sunrise is in `--color-text`. The sun itself is a point of
  `--color-text` on the arc carrying the green halo (`--color-brand-light`,
  quiet fill `--color-brand-quiet`). Below the horizon (night) the point sinks
  under the line and only a dim green glow spills up over it.
- **Data.** The clock in Saira 300, monumental (180 px), bottom left on the
  ground below the horizon. Under it the date in Saira 400, muted
  (`Saturday 14 November`), and one line
  `sunrise 09:54 · sunset 16:31 · 6 h 37 min` (words in Saira 400, numbers in
  Saira 500 with figures of one width, so a changing number never shifts its
  line).
- **Motion.** Still. The sun moves at the speed of the real sun; the redraw is
  once a minute. Nothing floats or pulses.

## Room 2: the control room

**Problem.** One press must reach the Apple TV, and the rest of the TV must be
one press further, without becoming a grid of equal cards (rejected by the
system: "a page is a few strong objects placed with intent"). And it must do
something an Apple TV home screen does not: set the room, not only open apps.

- **Arrival.** Any key on the living room turns the page, the site's room turn
  (decision 40): the living room drifts up two thirds and tips back
  (`perspective(1400px) rotateX(10deg)`), the control room slides over it at
  full size, 1400 ms on the in-out curve `cubic-bezier(0.77,0,0.175,1)`. BACK,
  or 60 s with no key, turns it back. The key that opens the room does nothing
  else. The room is a full slab (top light, slab gradient) with the 140 px lead
  band of `--color-text` washing its top edge.
- **APPLE TV**: the focal object. A large pressable slab at the left, wider than
  everything else, `APPLE TV` in wide Saira 600 caps, 80 px, too big for its
  slab's comfort. It has focus when the room arrives, so OK goes straight to
  HDMI 2. Its face carries a **live still** of HDMI 2 under the type: a small
  capture of the video plane, refreshed about every 3 s while the room is open
  and dimmed so the type stays the loudest thing. When a live capture is black
  or fails, the last still seen while the Apple TV was in front is shown with
  its age in data figures (`12 MIN AGO`); with neither, the slab is plain.
- **SHORTCUTS**: a row of pressables under it, each a TV app opened at a set
  place (webOS deep link). Two lines per face: the app in wide Saira caps, the
  place in Saira 400 muted. Listed in `config.js`.
- **APPS**: the rest as a column list, not a card grid. Each app is a long, low
  pressable bar, its name in wide Saira caps. Two columns of six.
- **SCENES**: the right column, three tall keys. A scene sets the room in one
  press: it opens what you watch and changes the TV around it. Each is one
  entry in `config.js`.
  - `FILM NIGHT`: Apple TV, cinema picture, SUN MODE (after sunset the picture
    goes dimmer and warmer; at sunrise everything is put back and the scene
    ends).
  - `MUSIC`: Spotify, then the screen goes dark with the sound on.
  - `WIND DOWN`: back to what was on, picture dimmed, volume lowered, standby
    in 60 minutes.

  A scene key **latches**: while its scene is on, the face stays down on its
  wall with a steady quiet halo and a state line in data figures (`ON · UNTIL
  09:54`, `ON · SLEEPS 23:40`). Pressing a latched key turns the scene off and
  puts the TV back as it was. One scene at a time.
- **SHIELD**: under the scenes, read only: the count of blocked calls in data
  figures, or `OFF`.
- **ENGINE ROOM**: the last key in the column, a door.

## Room 3: the engine room

**Problem.** The owner wants to see the machine: what the TV is doing and who it
talks to. That is a side interest, so it lives behind a door, not on the main
wall.

- **Arrival.** The same room turn, from the control room. BACK returns to the
  control room; 60 s with no key returns to the living room.
- **VITALS** (read only): temperature as the one big number in Saira 300, then
  uptime, memory and storage as thin meters. Refreshed every 5 s while the room
  is open.
- **WHO TALKS THE MOST** (read only): open connections grouped by the program
  on the TV and by who owns the far end (LG, Google, Apple, Netflix, a cloud
  host, unknown), most first, as ranked bars with a count.
- **LOG** (read only): the newest lines of the system log in data figures,
  filtered. Device ids never reach the screen: hardware addresses, long hex
  ids, UUIDs and serial values are masked before a line is drawn.
- **SHIELD**: the one pressable in the room, a latching switch. On, it blocks
  LG's own advertising, tracking and content-recognition hosts and nothing
  else, and counts each blocked call. The list ships in the app
  (`shield/hosts.txt`), one host per line.

## Shared rules

| Rule | Value | Source |
|---|---|---|
| Pressable | 3 px wall in `--color-key-wall`, bottom right | decision 25 |
| Read-only | flat slab, no wall | decision 12 |
| Focus | green halo + 2 px `--color-text` ring set 2 px out; snaps, no transition | brand digest |
| Press (OK) | face drops 3 px onto its wall with no transition; a faint green halo flares | decision 14 (key actions do not animate), brand reading 9 |
| Latched | face stays down on its wall, steady quiet halo, state line in data figures | new, from the press rule |
| Slab gap | ground only, never a rule; 16 px at TV scale | inherited 8 px, ×2 |
| Text | one family, Saira: 600 at the wide width in caps for doors and labels, 400 for reading, 500 with figures of one width for data, 300 for the monumental numbers | owner's pick, 2026-11-14 |
| Navigation | arrows move to the nearest focusable in that direction (spatial) | new |
| Language | English on every face and label | owner, 2026-11-14 |

## Chromium 79 (webOS 6) notes

- No flexbox `gap` (Chromium 84+): spacing is margins.
- No CSS `inset` (Chromium 87+): left/top/width/height.
- The page is laid out at 1920×1080 and scaled with `zoom`, not `transform`,
  so the layout box matches the window and nothing can scroll it.
- `perspective` on the zoomed stage breaks the layout: it goes inside the
  moving element's own transform.
- No `scrollIntoView` on focus: the v1 build scrolled the whole page down.

## How it runs

The page cannot change the TV by itself, so the work is split in three:

| Part | File | Runs as | Does |
|---|---|---|---|
| Page | `app/*.js` | the web app | draws the rooms, decides nothing about the TV |
| Helper | `app/bin/impetus-ctl` | root, one call at a time through Homebrew Channel's exec service | a fixed list of verbs: `probe`, `start`, `state`, `still`, `scene`, `sleep`, `shield`, `spotify`, `engine`, `restore` |
| Keeper | `impetus-ctl keeper` | root, one background loop | the timed jobs: sleep timer, SUN MODE, scene end, the music piece, last-seen still, shield after a restart |

- Everything that changes the TV goes through the helper. The page sends a
  verb and `key=value` words, each checked against a strict pattern in the
  page and again in the helper; an id or value with any other character is
  refused. Two older calls still go straight to the exec service, built from
  fixed text: a `luna-send` to the app manager (the app list, and opening an
  app when the page's own call is refused; its JSON is refused if it holds a
  quote) and a name lookup for one address in the engine room (digits and
  dots only).
- State lives in `/tmp/impetus/` (memory; a restart clears it). A few small
  files are also kept in the app's own folder (`state/`), because they must
  survive a restart: the picture values and the volume from before a scene
  (so a restart in the middle of a scene can still put them back) the
  flag that the shield is wanted, and the Spotify sign-in (#22). They are written before the TV is changed:
  a value that cannot be written down is not changed. Nothing is written
  anywhere else.
- **One change at a time.** The helper, the keeper and a scene's background
  part take turns through a lock (`/tmp/impetus/lock`) that names its holder.
  Only the holder gives it back. It is taken over when the holder is no
  longer running or has held it for more than two minutes; a verb that waits
  16 s for a running holder goes on without the lock and leaves it alone.
- **A call that never answers.** Every single call to a TV service is given
  up after 10 s and counts as refused, so the put-back rules below apply to
  it and the lock is never held by a call that hangs.
- **Self-test.** At start the page asks the helper to `probe`. Each part that
  does not answer on this TV is hidden: no still means a plain slab, a scene
  whose parts are all missing is not drawn, the engine room door goes away if
  root exec is missing. Nothing is shown that does not work.
- **Scenes on the TV.** Picture values belong to an input, so a scene is
  applied after its target is in front, by the helper, not by the page (the
  page is in the background by then). Before the first change the helper
  writes down the values it is about to touch; turning the scene off, sunrise,
  the sleep timer ending and `impetus-ctl restore` all put them back. A
  put-back the TV refuses stays on record and is tried again on later turns
  (20 at most, then it waits for the next scene end or `restore`); the record
  is deleted only when the TV took every value (or already holds it). While a
  value is still refused the scene's mode stays too, so its values are never
  written into the mode from before. Values go back in the form they were
  read in, number or text.
- **Sleep.** Two minutes before standby the keeper brings Impetus to the front
  with a countdown. Any key cancels the timer and goes back to what was on. No
  key: the scene's app is brought back to the front, the picture values are
  put back and the TV goes to standby. Standby is a normal power-off, never a
  reboot; if the TV refuses it, it is asked on 5 turns and then left on.
- **Shield.** Name-based and in memory only. Homebrew Channel already keeps
  the TV's hosts file in memory (`/tmp/hosts`, mounted over `/etc/hosts`); the
  shield adds its lines to that file between two marker lines and takes them
  out again, so the system file is never changed. Where that mount is missing
  the helper mounts its own copy from `/tmp/impetus`. The listed names go to
  one dead local address. This TV's kernel has no firewall module, so the
  count comes from a small listener on that address (`bin/shield-count.js`):
  each connection that arrives is one blocked call. A restart clears it all;
  the keeper puts it back if the owner had the shield on. Known gaps: an app
  that uses a fixed address instead of a name is not stopped, and LG's own
  apps read the hosts file when they open, so one that was already open keeps
  its old answers until it is opened again. Off until tested on the TV with
  the owner watching.

## Default Home

Home Chooser is absent on this TV, so Impetus becomes the default through a
Homebrew boot hook (`boot/impetus-home`, installed as
`/var/lib/webosbrew/init.d/impetus-home`, mode 755). It starts the keeper,
opens Impetus once the system is up and again whenever stock Home comes to the
front, and it never gives up. One brake: more than 5 reopenings within a
minute means Impetus keeps closing, so stock Home is left alone for 2 minutes
before the next try (six presses of Home in a minute do the same). Only one watcher runs at a time (`/tmp/impetus-hook.pid`).
Pause: `touch /tmp/impetus-pause`.

**Way back** (in this order, over SSH):

1. `sh /media/developer/apps/usr/palm/applications/org.va7dimar.home/bin/impetus-ctl restore`
   puts the picture and volume back, takes the shield off and stops the keeper.
   It prints `ok=1`. Picture values belong to an input, so each set is put
   back with its own app in front; if an app will not open, its values are not
   written to another input, they stay on record, and the answer is
   `error=notrestored <app>`: run it again.
2. `rm /var/lib/webosbrew/init.d/impetus-home`, then restart the TV: stock Home
   is the default again.

## Limits of this build

- Up to 3 shortcuts, 12 apps and 3 scenes are shown; the rest are named in a
  note and ordered or hidden in `config.js`.
- The horizon sits at 64 % down (not 78 %) so the clock, date and sun line fit
  on the ground below it.
- Everything that touches the TV was built against stand-ins on a PC. The TV
  session checklist (`TV-SESSION.md`) lists what must be seen working on the
  TV before each part is trusted.

## Control room v2: grilling record (confirmed 2026-11-14)

Alignment grilling on wow, usefulness and uniqueness. Critique of the 1.1.0
render: the focal APPLE TV slab was empty, the 12 equal app bars read as a
launcher, and the side-feature connections panel held the second-best spot.

### 1. Settled by the owner

1. Output: the decisions go in this file; the build follows on the same branch.
2. The APPLE TV slab shows a live still of HDMI 2, refreshed about every 3 s
   while the room is open; a plain slab on a black or failed capture.
3. The main idea is **scenes**: FILM NIGHT (Apple TV, cinema picture, SUN MODE
   on), MUSIC (Spotify, screen off with sound on), WIND DOWN (dim picture,
   lower volume, 60 min sleep timer). Each is one entry in `config.js`.
4. Layout: APPLE TV and SHORTCUTS left, APPS middle, SCENES right (three tall
   keys), then a small shield count and the ENGINE ROOM door.
5. SUN MODE: after sunset the picture goes dimmer and warmer, back to normal
   at sunrise.
6. Engine room (a third room behind the door): TV vitals (temperature, uptime,
   memory, storage, 5 s refresh), who talks the most (connections grouped by
   program and owner), a filtered live system log (no device ids on screen),
   and the shield switch (the one pressable there).
7. Shield: LG's own ad, tracking and content-recognition hosts only; rules in
   memory only (a restart clears them, the boot hook puts them back); off
   until tested; the first run needs the owner's yes at the TV.
8. English names everywhere, the living room's date and sun line included.
9. Order: build everything now against stand-ins on the PC; the app tests each
   part on the TV at start and hides what fails; one TV session checks
   everything later.

### 2. Derived without asking

- Scenes replace separate SCREEN OFF, SLEEP and SUN MODE keys (from 3 and 4).
  The 30/60/90 sleep cycle is dropped; WIND DOWN sleeps after 60 min, set in
  `config.js`.
- Pressing an active scene turns it off and restores what it changed; one
  scene at a time (from 3).
- Safety (question 8 was not asked; the recommendation was taken): the
  original picture values are saved before the first change and restored when
  a scene goes off, at sunrise, when the sleep timer ends and by the way-back
  command; a notice 2 minutes before standby, any key cancels.
- Timed jobs (sleep, SUN MODE, shield after a restart) run in the keeper, a
  root loop outside the page, because the page sleeps when another app is in
  front. The boot hook starts it; so does the app at start, so the jobs work
  before the hook is installed.
- When a live capture is not possible while Impetus is in front, the slab
  falls back to the last still seen (from 2: a plain slab only when there is
  nothing honest to show).
- The boot hook and the shield's first run need the owner's yes at the TV
  (the brief's Home rule, and 7).

### 3. Facts established

- `com.webos.service.capture/executeOneShot` captured the video plane (the
  Apple TV on HDMI 2), not the UI, on this TV (2026-11-14, root `luna-send`).
- Homebrew Channel's exec service runs a command as root and returns its
  output to the page (2026-11-14, used by 1.0.0 to list apps).
- Sunrise 09:54, sunset 16:31 UTC for Reykjavík on 14 November 2026, from
  `logic.js` and the closed-form hour angle (`tests/test_logic.js`).
- The 1.1.0 rooms, navigation and BACK work in a PC preview at 1920×1080;
  nothing in this record has run on the TV yet.

### 4. Deliberately open (the TV session decides)

- Whether a capture is live while Impetus is in front, and under DRM.
- Whether picture values can be written through root, and land on the input
  they were meant for when Impetus is in front.
- Screen off with sound on, the sleep job and standby.
- The hosts lines and the counting listener; whether LG's services honour them.
- Deep-link parameters for the shortcuts.

### 5. Rejected on the way

- A volume key (owner: "something else, think on it").
- A DAYLIGHT scene, a wider ad list than LG's own hosts, an Impetus status
  panel.
- Icelandic labels (owner: English names).
- Parked as issues, not built: your TV day (a timeline), remote keys as direct
  doors, the room learning the hour, aurora and weather in the sky, Bluetooth
  headphones, Apple TV wake and sleep (CEC), Apple TV app control (pyatv).

## Music made visible (#22, built host-side 2026-11-15)

When music plays, the screen draws it: one full-screen generative piece in the
house shape. The **sky** is a deep colour field (five soft lights drawn at
320×180 and stretched) with a flow of light over it (about 560 strokes
following slow waves, drawn at 960×540, long trails). The **arc** is the
track's progress drawn as the living room draws the sun's day: the whole arc
faint, the part played bright, a glowing point at now. Under the **horizon**
the ground carries the cover, the title and the artist; the words dim after
15 s and come back at each new track. Files: `app/music.js` (drawing and the
Spotify feed), `app/music-logic.js` (pure, `tests/test_music.js`).

**Two drivers, one piece.** A beat source answers once a frame:
`read(nowMs) -> null | {energy: 0..1, beat: 0..1}`. With values (a sound
tap) the flow speeds with the energy, the lights swell and the point flares
on the beat. With `null` (the stand-in until the TV probe answers) the
cover drives it: the palette comes from the cover, the light drifts left to
right through the track as the sun does through the day, and the flow's
direction turns with the progress. A new track crossfades the palette over
3.5 s. Paused: everything slows to a third. A sound tap would feed the same
interface (`window.ImpetusBeat`); nothing else changes.

**Colours.** The cover is read from a 24 px drawing: hues are binned and
weighted by how much colour they carry, the strongest bins that sit apart
become four lights (kept bright enough to glow), the main hue at 7 % becomes
the ground. A grey cover takes its hue from the track id. When the picture
host does not allow reading (CORS), the palette comes from the track id alone.

**Calm failure.** No sign-in, a revoked sign-in, no network, nothing playing,
an ad: the same sky in the living room's teal, quieter, with no arc and no
words. Never an error box, never a spinner. Trouble keeps what is on the
screen and backs off (doubling, at most 2 min; a 429 waits as long as Spotify
says). A revoked sign-in stops the asking until the piece is opened again.

**How it is opened.** The MUSIC scene has `pieceAfterSeconds: 20` in place of
`screenOffAfterSeconds`: the helper writes the hour (`/tmp/impetus/piece.at`),
and the keeper's turn at that hour opens Impetus with
`{"show": "music", "at": <epoch>}`, but only while the scene's app (Spotify)
is still in front; someone who moved on is left alone. The scene stays on
(its key reads `ON · DRAWN FROM 21:04`). Params are taken once and only
within 2 minutes. Any key leaves the piece for the control room, as from the
living room. When another app comes to the front the piece stops (no drawing,
no asking). For the dark screen again, swap the key back in `config.js`.
Both keys set: the piece wins. `config.js` `music: {fps, particles}` lowers
the load if the TV stutters.

**The Spotify sign-in.** A PKCE sign-in: there is no client secret anywhere,
and nothing about the sign-in is in this repo. The TV keeps it in the app's
`state/spotify` (mode 600, survives restarts, same folder as the other kept
files):

```
v=1
client=<Spotify app client id>
refresh=<refresh token>
saved=<epoch s>
```

`impetus-ctl spotify get` answers `linked=1`, `client=`, `refresh=` (or
`linked=0`); `spotify set client=.. refresh=.. [was=..]` writes it atomically
under the lock; `spotify forget` drops it. Values are `[A-Za-z0-9._-]`, at
most 512 characters. The page turns the refresh token into an access token
itself (`POST accounts.spotify.com/api/token`, `grant_type=refresh_token`,
`client_id`) and keeps that in memory only. When Spotify hands out a new
refresh token, the page writes it back with `was=<old>`, so a token turn
never overwrites a new sign-in the phone wrote in the meantime. Scope needed:
`user-read-currently-playing`. Hosts: `accounts.spotify.com`,
`api.spotify.com`, `i.scdn.co` (covers); none is on the shield's list (a test
checks it).

**The phone sign-in (#21) writes the file**, with `spotify set client=..
refresh=..` through the phone page's API. One thing to settle there: Spotify
now accepts only HTTPS redirect addresses, or plain HTTP to the loopback
address `127.0.0.1` on the device doing the sign-in. A redirect to the
phone page at `http://<tv>:<port>` is refused. Ways through: a static HTTPS
return page (for example on GitHub Pages) that passes the code on to the
phone page; or the PKCE code exchange done on a laptop with a loopback
redirect and the result typed in. Owner's call when #21 builds the sign-in.

**Sound tap.** `scripts/probe_sound.sh`, run at the TV as root with music
playing, reads only: ALSA cards, PCM devices and capture devices, loopback,
sound servers and their sockets, PulseAudio sources and monitors, tools
(`parec`, `arecord`, `gst-launch-1.0`, ...), webOS audio services and their
capture-like methods. `sh probe_sound.sh try` also listens 2 s on each place
found and says whether real sound (not silence) came out: `tap=yes` with the
places, or `tap=no`. Its answer decides whether a beat source gets built.

**Open until the TV:** whether Spotify keeps playing with Impetus in front;
whether Spotify's endpoints answer a page whose origin is `file://` (CORS);
whether `i.scdn.co` lets the cover be read (else the id's palette); the frame
rate on the TV's chip; how it looks on the 65" panel.

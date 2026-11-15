# Impetus Home

A Home for a rooted LG webOS 6 TV, built as a web app: a **living room** at
rest (the sun's real path over Reykjavík, a clock), a **control room** on any
key (the Apple TV door with a live still, shortcuts, apps, scenes) and an
**engine room** behind a door (vitals, who the TV talks to, the log, a shield
against LG's own ad and tracking hosts).

| Status | 1.2.0 |
|---|---|
| On a PC | host-tested against a stand-in TV; all three rooms run in the preview |
| On the TV | 1.0.0 ran as an ordinary app. Everything since then is unverified until the [TV session](TV-SESSION.md) |

- [DESIGN.md](DESIGN.md): the rooms, the rules, how the page, the root helper
  and the keeper share the work, and the way back.
- [TV-SESSION.md](TV-SESSION.md): what must be seen working on the TV, step by
  step, before each part is trusted.

## Look at it on a PC

```sh
node preview/serve.js
```

Then open `http://localhost:8765/preview/dev.html` at 1920×1080. Arrow keys,
Enter (OK) and Backspace or Escape (BACK) drive it. The TV is a stand-in
(`preview/dev.html`), steered from the address:

| Query | Does |
|---|---|
| `t=2026-11-14T21:10:00Z` | sets the clock (the sun follows) |
| `room=control`, `room=engine` or `room=iceland` | opens in that room |
| `quakes=fixture` | Iceland gets the 15.11.2026 list (clock set to 00:20 UTC unless `t` is given); without it the feed has nothing yet |
| `feed=down` | the helper has only its last copy: the quiet `feed down since` line |
| `fps=1` | frames per second, top left |
| `flights=fixture` | two aircraft of 15.11.2026, a minute further on each call; without it the flight feed has nothing |
| `cam=fixture` | a stand-in road-camera frame; it shows only in daylight at the camera (try `t=2026-11-15T13:00:00Z`) |
| `scene=film`, `scene=winddown` | a scene is already on |
| `shield=on` | the shield is on and counting |
| `still=live`, `last`, `none`, `black` | what the Apple TV slab gets |
| `caps=capture,picture` | parts this TV cannot do (see `probe`) |
| `notice=sleep` | the two-minute notice before standby |
| `room=music` | the music piece (#22); with `np=demo` three made-up tracks, `np=paused` one held, none the quiet idle state; `beat=demo` a stand-in beat |
| `notice=bedtime` | the bedtime card (WIND DOWN or NOT TONIGHT) |
| `phone=on` | the phone remote's server is on (engine room) |
| `room=overhead` | opens the overhead room (#23); `t=2026-11-16T19:58:30Z` is mid-pass |
| `sky=down` | the orbit and plane feeds are down |
| `place=none` | no home position set (central Reykjavík) |

The phone remote's page: `http://localhost:8765/preview/phone.html` at phone
width (e.g. 390×844), with `paired=1`, `scene=`, `shield=on`, `caps=` and
`tv=down` (the TV does not answer).

## Test

```sh
node tests/test_logic.js      # the page's logic: 64 tests
node tests/test_music.js      # the music piece's logic and its scene words: 23 tests
sh tests/test_ctl.sh          # the root helper against a stand-in TV: 577 checks
python tests/test_ipk.py      # the package: layout, line ends, modes, same bytes twice
```

`test_ctl.sh` needs a POSIX shell (dash or busybox ash; on Windows, WSL).
It runs the real helper and keeper with stand-ins for `luna-send`, `mount`,
`umount`, `iptables`, `node` and `httpd` in `tests/stubs/`, in a scratch folder.

`scripts/probe_phone.sh` is run on the TV, not the PC: it reads (and changes
nothing) whether the TV can serve the phone remote (busybox httpd and CGI, nc,
node, free ports 8090–8093, a /tmp that can run a script).

`scripts/probe_wake.sh` is also run on the TV: it reads (and changes nothing)
whether root can wake the TV from sleep at a set time (issue #25). Its
`clock` mode, run before and after a sleep, tells whether anything runs
while the TV sleeps.

## Build

```sh
python scripts/build_ipk.py   # build/org.va7dimar.home_<version>_all.ipk and its SHA256
python scripts/build_iceland_map.py   # app/iceland/map.js from pinned, hash-checked sources (only when they change)
```

No LG SDK. The same files always give the same bytes.

## Make it yours

`app/config.js` is the one file to edit: the focal door, shortcuts, scenes,
app order, hidden apps and short names. `app/shield/hosts.txt` is the shield's
list, one host per line.

## Next

The TV session comes first: [#14](https://github.com/Va7dimar/lg-tv-native-os/issues/14).
Ideas that were wanted and parked, one issue each:

| Idea | Issue |
|---|---|
| Your TV day: a timeline of what was on | [#6](https://github.com/Va7dimar/lg-tv-native-os/issues/6) |
| Remote keys as direct doors | [#7](https://github.com/Va7dimar/lg-tv-native-os/issues/7) |
| The control room follows the hour | [#8](https://github.com/Va7dimar/lg-tv-native-os/issues/8) |
| Moon, aurora and weather in the sky | [#9](https://github.com/Va7dimar/lg-tv-native-os/issues/9) |
| Sound to Bluetooth headphones | [#10](https://github.com/Va7dimar/lg-tv-native-os/issues/10) |
| Wake and sleep the Apple TV over HDMI-CEC | [#11](https://github.com/Va7dimar/lg-tv-native-os/issues/11) |
| Apple TV app control and now playing | [#12](https://github.com/Va7dimar/lg-tv-native-os/issues/12) |
| Live HDMI video in the APPLE TV slab | [#13](https://github.com/Va7dimar/lg-tv-native-os/issues/13) |

## Layout

| Path | Holds |
|---|---|
| `app/` | the web app: `index.html`, `home.css`, `home.js` (rooms and keys), `logic.js` (pure functions), `luna.js` (the TV's services), `config.js`, `music.js` and `music-logic.js` (the music piece, #22) |
| `app/bin/impetus-ctl` | the root helper and the keeper |
| `app/bin/shield-count.js` | counts calls the shield stopped |
| `app/iceland/` | the Iceland room's map, generated (coast CC BY 4.0, see `LICENSE-map.txt`) |
| `app/bin/impetus-phone`, `app/bin/phone-serve.js`, `app/phone/` | the phone remote: its CGI door (pairing, tokens), the node fallback server, the phone page |
| `app/bin/impetus-sky`, `app/sky-logic.js`, `app/overhead.js`, `app/overhead.css`, `app/sky/` | the overhead room (#23): the feeds and the home position, the orbit math, the room, satellite.js |
| `boot/impetus-home` | the boot hook that makes Impetus the default Home |
| `preview/` | the PC preview |
| `tests/`, `scripts/` | host tests, the IPK build, and `probe_sound.sh` (run at the TV: can root read the sound?) |

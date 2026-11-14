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
| `room=control` or `room=engine` | opens in that room |
| `scene=film`, `scene=winddown` | a scene is already on |
| `shield=on` | the shield is on and counting |
| `still=live`, `last`, `none`, `black` | what the Apple TV slab gets |
| `caps=capture,picture` | parts this TV cannot do (see `probe`) |
| `notice=sleep` | the two-minute notice before standby |

## Test

```sh
node tests/test_logic.js      # the page's logic: 24 tests
sh tests/test_ctl.sh          # the root helper against a stand-in TV: 194 checks
python tests/test_ipk.py      # the package: layout, line ends, modes, same bytes twice
```

`test_ctl.sh` needs a POSIX shell (dash or busybox ash; on Windows, WSL).
It runs the real helper and keeper with stand-ins for `luna-send`, `mount`,
`umount`, `iptables` and `node` in `tests/stubs/`, in a scratch folder.

## Build

```sh
python scripts/build_ipk.py   # build/org.va7dimar.home_<version>_all.ipk and its SHA256
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
| `app/` | the web app: `index.html`, `home.css`, `home.js` (rooms and keys), `logic.js` (pure functions), `luna.js` (the TV's services), `config.js` |
| `app/bin/impetus-ctl` | the root helper and the keeper |
| `app/bin/shield-count.js` | counts calls the shield stopped |
| `boot/impetus-home` | the boot hook that makes Impetus the default Home |
| `preview/` | the PC preview |
| `tests/`, `scripts/` | host tests and the IPK build |

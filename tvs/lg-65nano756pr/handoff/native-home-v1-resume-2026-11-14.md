# native-home-v1: resume brief for the session that built Mode C

Written 2026-11-14 at about 06:50 Atlantic/Reykjavik (UTC) by a separate
session that cannot see your local branch or files. It holds the owner's
answers to a long round of questions, so you can run to the end without
stopping to ask. Where this brief and your own spec (`df6728e`) disagree on
**permissions or scope**, this brief wins: the answers are newer. On
**technical detail** your spec wins: you built it and this session has not
seen it.

Owner preference, stated plainly: *this is a fun side project, nothing
critical.* Keep tests to the useful ones. No review packets, no multi-model
reviews, no gate checklists, no extra evidence batteries. Be careful with
the TV and keep it moving.

## State you left (as you reported it)

- `native-home-v1`, local only: `df6728e` spec and plan, `2bdcb1c` Mode C
  (`wl_webos_shell`, appId, `_WEBOS_WINDOW_TYPE_CARD`, green fill). Host
  tests: 36, 0 failed. IPK tests: 0 failed.
- `wh-photo-c.ipk` was built with the TV toolchain, passes the ABI check, and
  sits in the folder next to the repo. Nothing is on the TV and nothing is
  pushed.

## What the owner has authorised

| Item | Answer |
|---|---|
| TV actions | Install `wh-photo-c.ipk`, launch it, read logs, ask for the foreground app once, then remove it. **One retry** is allowed if the first run is spoiled (photo missed, ssh drop, log missing), with no code change between runs. |
| Stale install | If `org.va7dimar.waylandhello` is already installed, `dev/remove` that id first. Remove nothing else. |
| Owner at the TV | Yes, with the remote and a phone, **from about 06:50 to about 14:50 UTC on 2026-11-14**. Inside that window, say in chat that you are launching and go; no "ready" handshake is needed. Outside it, post one message and wait for the owner. |
| Photos | The owner takes them and sends them to you in chat: one at **T≈15 s** and one at **T≥35 s** (after the 31 s mark). |
| Key press | The owner presses **RIGHT once** on the physical remote at **T≈20 s**. No SSAP key injection. |
| Host and login | Claude Code on the owner's Windows PC, on the TV's LAN. `ssh root@<tv>` already works with a key, no prompt. The TV's IP is **unchanged** from `evidence/ssh-access-2026-11-08.md` (owner confirmed). If a password prompt appears anyway, stop and say so; never type the default password. |
| Git | Commit, push `native-home-v1`, open a PR to `main` on **`lg-tv-native-os` (public)**, and **squash-merge it yourself**. Same flow as PR #1 for 0.10. |
| Public-repo rules | Same as `evidence/photo-frame-tv-run-2026-11-14.md`: no serial, nduid, MAC or IP, and no photos committed (describe them). **New: no personal name or email**, in notes or in commit trailers. The 0.10 squash carried a `Co-authored-by:` line with the owner's name and email; do not repeat that. |
| After the verdict | Plan the Home v1 below and **implement it**, as long as the plan stays inside that scope. Tests are fine; keep them light. |
| Later TV runs (Home v1) | Allowed: `dev/install`, launch and `dev/remove` of **our own app ids**, while the owner is at the TV. Setting our app as Home with Homebrew **Home Chooser** is allowed too (see the revert rule below). |

Unchanged hard rules: never write kernel, rootfs or tvservice partitions, no
reboot from a script, no flashing, nothing outside `/tmp` and the dev-install
app directory.

## Correcting one memory before the run

The owner remembers "one mode only loaded and never showed the magenta
screen". The 2026-11-14 note shows **Mode A was magenta and was shown**:
1920×1080, all four corners, focus at 0.6 s, Home back at about 31 s.
**Mode B was cyan and was never shown**: SAM's loading spinner, no
compositor events. Use the note's version.

## Expectation, recorded before the run

Mode C uses the same `wl_webos_shell` path that has failed twice on this TV:

- 2026-11-08, v0.5, SAM-launched `--webos-shell` **CARD**: a frame callback,
  but no configure, no focus and no LSM visible line, so not shown
  (`evidence/sam-launch-success-2026-11-08.md`).
- 2026-11-14, Mode B, SAM-launched lifecycle-2 **OVERLAY**: `registered` OK,
  committed, never mapped (`evidence/photo-frame-tv-run-2026-11-14.md`).

What's new in Mode C is CARD **together with** lifecycle-2 `registerApp`
**and** the correct installer-generated LS2 role. Estimate written before
the run: **about 20 % that Mode C is visible at all** (low confidence). If it
fails, that confirms the estimate; it is not a surprise to chase. The owner
said run it anyway: it's cheap.

## The Mode C run

1. Check the hash of `wh-photo-c.ipk` against the one you recorded at build
   time. `ssh` to the TV. If our id is installed, `dev/remove` it.
2. `scp` the IPK to `/tmp/`, check its sha256 on the TV, then
   `dev/install` with `</dev/null`, exactly as in the wayland-hello README
   quick start.
3. In chat: "Launching now. Photo at 15 s, press RIGHT once at about 20 s,
   photo again after 35 s." Then `applicationmanager/launch`.
4. At **T≈17 s**, before the key press so the two don't mix, run once:
   `luna-send-pub -n 1 -f luna://com.webos.service.applicationmanager/getForegroundAppInfo '{}' </dev/null`
   Record `appId`, minus any device-id fields.
5. Collect the same logs as the 2026-11-14 run: `/tmp/wh6.log`, plus the
   sam/LSM lines (`NL_VSC`, `last_input_handler`, `on_foreground_null`,
   `Transition is timeout`) around launch and around T≈31 s.
6. Let the process reach its own cap, then `dev/remove` our id.

## Verdict rule (decided by the owner)

| What the photos and logs show | Verdict |
|---|---|
| The T≥35 s photo still shows the green Mode C frame | **Native.** Record the foreground `appId`. Whether the key arrived is a bonus, not a requirement. |
| Green at 15 s, but Home has the screen at about 31 s (same as Mode A) | **Hybrid.** |
| Never shown (spinner, no compositor events, as in Mode B) | **Hybrid.** Record that `wl_webos_shell` (CARD and OVERLAY) does not map on this firmware. No more runs. |
| Run spoiled (photo missed, ssh drop, no log) | Use the one identical retry, then judge. |

**Hybrid** means a web Home plus native: a web app, properly registered with
SAM, is the Home and the launcher and owns the foreground. The native
Wayland renderer is for later heavy parts and is **not** in v1.

After the verdict, write the evidence note
(`evidence/photo-frame-c-tv-run-2026-11-14.md`, same shape as the A/B note,
without a personal name) and a project-log entry. Then commit, push, open
the PR and squash-merge.

## Home v1 scope (build this after the merge, whichever way the verdict goes)

Name **Impetus Home**, app id `org.va7dimar.home`, title `Impetus`. The UI
is in Icelandic with a 24-hour clock.

1. **App tiles**: every installed, visible app, taken from SAM's app list.
   Hide system and hidden entries; leave ourselves out. The owner will
   reorder or curate later, so keep the order in one small config list.
2. **Input tiles**: HDMI 1–4 and live TV (`SJÓNVARP`). Read the real app
   ids from the TV's app list (expect `com.webos.app.hdmi1`…`hdmi4` and
   `com.webos.app.livetv`, but check them on the TV).
3. **Clock and info bar** along the top: 24-hour time in Plex Mono and an
   Icelandic date, e.g. `laugardagur 14. nóvember`. No weather in v1.
4. **Brand**: the Impetus primary colourway, in
   [`impetus-home-brand-digest.md`](impetus-home-brand-digest.md). Focus is
   the green halo **plus** the 2 px `#E6EAF1` ring, and a press is a 60 ms
   snap.
5. Remote: arrows move focus, OK launches, BACK does nothing on Home. No
   pointer UI in v1.

Out of v1: weather, a photo or ambient screen, native rendering inside the
web Home, settings screens.

**If the verdict is hybrid** (the expected case): build it as a webOS web
app (`type: web`) with fonts bundled locally, so it never depends on network
fonts. Two things are **unverified** on this TV; check them first with one
quick dev-install:

- Can a dev-installed web app call the app-list and launch luna methods
  directly? If it is denied, add a tiny JS service and use Homebrew's
  service elevation, the way Homebrew Channel does. Read webosbrew's docs or
  sources first; don't guess.
- Does Home Chooser accept our app as Home, and does its reset to stock work?

**If the verdict is native**: the same scope, drawn by the native client.
Brand fonts become pre-rasterised glyph atlases in place of the 5×7 bitmap
font. Write that plan, keep it inside the same scope, then build.

### Home Chooser revert rule

Before setting `org.va7dimar.home` as Home: (1) confirm SSH works, (2) find
and write down the exact way back to stock Home (Home Chooser's reset, or
`dev/remove` of our id if SAM then falls back to `com.webos.app.home`), and
(3) test that way back **once** while the owner watches. Only then leave our
app set as Home. If our Home ever shows a blank screen or crash-loops, put
stock back at once over SSH.

## Done when

- The Mode C evidence and verdict are merged to public `main`.
- Impetus Home v1 is planned, built and host-tested, and was run on the TV
  as an ordinary app. If the revert test passed, it is set as Home.
- One short chat summary for the owner: verdict, what's on the TV now, and
  the command to go back to stock Home.

# Impetus Home 1.2.0: TV session checklist

Everything in 1.2.0 that touches the TV was built against stand-ins on a PC
(`tests/test_ctl.sh`). This list is the one sitting at the TV that turns
"built" into "seen working". Work it top to bottom; each step says what to
do, what to see, and where the fix goes when the TV answers differently.

**Rules for the session**

- The owner is at the TV with the remote for every step.
- `ssh root@<tv>` works with a key. If a password prompt appears, stop.
- Never reboot from a script, never flash, never write a system partition.
- Files go in `/tmp` and the app's own folder. The one exception is the boot
  hook in step 9, which the owner approves at that step.
- From Windows, put luna commands in a small `.sh` file with `</dev/null` on
  each `luna-send` line, `scp` it to `/tmp/` and run it there. Quoted JSON
  over ssh breaks.
- Nothing from the TV goes into the repo with a serial, nduid, MAC or IP in
  it, and no photos: describe them.

**Where it stands (2026-11-14).** Steps 1 to 9 were worked on the TV; the
results and what is still open are in
`tvs/lg-65nano756pr/evidence/impetus-home-1.2-tv-run-2026-11-14.md`. Three
things learned there change how this list reads:

- The remote's power button only puts this TV to sleep. "Restarts the TV"
  below means a cold start (power cord), which only the owner does.
- The TV's address is the one in the newest evidence note that names one,
  not the oldest. Check the host key against `known_hosts` before trusting it.
- busybox `ps` shows no command lines: find the helper's processes by their
  pid files and `kill -0`, or by reading `/proc/<pid>/cmdline`.

Short names used below:

```sh
APPDIR=/media/developer/apps/usr/palm/applications/org.va7dimar.home
CTL="sh $APPDIR/bin/impetus-ctl"
```

## 0. The way back, before anything else

Read it once now so it is at hand:

```sh
sh /media/developer/apps/usr/palm/applications/org.va7dimar.home/bin/impetus-ctl restore
```

puts the picture and volume back, takes the shield off and stops the keeper.
It prints `ok=1`. `error=notrestored <app>` means that app would not come to
the front, or the TV refused one of its values, so its picture values were
not all put back (they are never written to another input) and stay in
`state/orig.<app>`: open the app with the remote and run `restore` again. `error=notrestored hosts` means the shield's
own mount would not let go: run it again. If the helper itself is broken, the
same by hand:

```sh
kill "$(cat /tmp/impetus/keeper.pid)" 2>/dev/null
umount /etc/hosts 2>/dev/null     # only if step 8 said the helper made its own mount
rm -rf /tmp/impetus
rm -f /media/developer/apps/usr/palm/applications/org.va7dimar.home/state/shield.on
```

A restart of the TV (by the owner, with the remote) also clears everything
the shield and the keeper hold in memory. Picture values are the TV's own
settings and survive a restart, so `restore` comes first.

## 1. Install 1.2.0

On the TV now: 1.0.0 as an ordinary app, no boot hook.

1. Build on the PC: `python scripts/build_ipk.py`, note the SHA256 it prints.
2. `scp` the IPK to `/tmp/impetus.ipk`, check `sha256sum` on the TV.
3. Install over the old one:

   ```sh
   luna-send-pub -n 1 luna://com.webos.appInstallService/dev/install '{"id":"org.va7dimar.home","ipkUrl":"/tmp/impetus.ipk","subscribe":true}' </dev/null
   ```

4. See: `ls -l $APPDIR/bin/impetus-ctl` shows the file as executable and
   `head -c 9 $APPDIR/bin/impetus-ctl` prints `#!/bin/sh`.
5. The helper's lock names its holder by pid and gives up calls that hang.
   Both lean on the TV's own shell, which has only been tested as dash on a
   PC. On the TV:

   ```sh
   sh -c 'echo "$PPID"'; echo $$          # the same number twice
   ( sleep 30 & p=$!; kill $p; wait $p; echo "ended $?" )   # "ended 143" at once
   ( trap 'kill $s; echo cancelled; exit 0' TERM; sleep 30 & s=$!; wait $s; echo late ) & w=$!; sleep 1; kill $w; sleep 1; ps | grep '[s]leep 30'
                                          # "cancelled" at once, and no "sleep 30" line
   ln -s 1.2 /tmp/lk; ln -s 3.4 /tmp/lk; ls -ld /tmp/lk | sed -n 's/.* -> //p'; rm /tmp/lk
                                          # "File exists", then "1.2"
   read a b < /proc/uptime; echo "$a"     # seconds since the TV started, like 5123.45
   $CTL scene off; ls /tmp/impetus/lock   # ok=1, then "No such file"
   ```

   The lock is a symbolic link whose target is its holder's pid and the
   second it was taken. A different result on the first, fourth or fifth
   line goes to the lock (`lock_me`, `lock`, `lock_now` in `impetus-ctl`), on
   the second or third to `luna`.

**Later reinstalls:** an install replaces the app folder, and with it
`state/` (the picture values from before a scene, and the shield flag). Run
`$CTL restore` before every reinstall.

## 2. Probe (reads only, changes nothing)

```sh
$CTL probe
```

Expect ten lines, each `1` or `0`: `exec capture picture screenoff sleep
volume shield count log temp`. Write the answer down; a `0` means the page
hides that part, which is correct behaviour, and the matching step below
says what to look at.

| Line | `0` means | Look at |
|---|---|---|
| `capture` | the one-shot capture failed or gave a black frame | step 4 |
| `picture` | `getSystemSettings` for `picture`/`backlight` did not answer | step 5 |
| `screenoff`, `sleep` | `tvpower/power/getPowerState` did not answer | step 6 |
| `volume` | `audio/master/getVolume` gave no number | step 6 |
| `shield` | no writable in-memory hosts file and no bind mount | step 8 |
| `count` | no `node` on the TV (the kernel has no firewall module) | step 8 |
| `log` | none of the three log files is readable | step 7 |
| `temp` | no thermal file | step 7 |

## 3. The page

Open Impetus from the app list.

- Living room: horizon, sun arc, clock, English date and sun line. Any key
  turns the control room over it; BACK or 60 s turns it back.
- Control room: APPLE TV has focus; SHORTCUTS, APPS, three SCENES, the
  SHIELD count and the ENGINE ROOM door. Arrows move by position.
- A scene key or the door that is missing means its probe line was `0`.
- **Does the page get the still?** The page reads the helper's JPG from the
  exec answer's `stdoutBytes` (base64). If the APPLE TV slab stays plain
  while `capture=1`, that field is missing or the answer is cut. Check with
  the Homebrew Channel exec call from a script and look for `stdoutBytes`
  and its length. Fix in `app/luna.js` (`still`), or lower the capture size
  in `impetus-ctl` (`capture`, `STILL_MAX`).

## 4. Live still

1. Put the Apple TV on HDMI 2 with a picture on it. `$CTL still | head -c 40`
   prints `kind=live age=0`.
2. Open Impetus, open the control room: the still shows under `APPLE TV`
   and changes about every 3 s.
3. **Open question:** with Impetus in front, is the capture still the HDMI
   picture, or black? If black, the slab shows the last still with its age
   (`12 MIN AGO`), which is the designed fallback; write down which.
4. Play something protected (Netflix on the Apple TV): expect black, and the
   last-still fallback.

## 5. Picture: read, write one value, put it back

One value first, by hand, before any scene:

```sh
luna-send -n 1 luna://com.webos.settingsservice/getSystemSettings '{"category":"picture","keys":["backlight"]}' </dev/null
```

Note the number and whether it is quoted (`"80"` or `80`). Then press
**WIND DOWN** in the control room (it sets backlight 25, caps the volume at
12 and starts the 60 min timer):

- See: the picture dims on the app that was in front; the key stays down
  with `ON · SLEEPS hh:mm`.
- `cat $APPDIR/state/orig.*` lists the values from before, and
  `cat $APPDIR/state/vol` the volume from before and the cap.
- Press WIND DOWN again: backlight and volume are back, the read above gives
  the first number again.

Then **FILM NIGHT**:

- See: HDMI 2 in front, picture mode cinema.
- **Open question: the sign of `colorTemperature`.** After sunset the scene
  sets backlight 30 and colorTemperature -20. The picture should go warmer
  (more red). If it goes blue, flip the sign in `app/config.js` (`sunMode`).
  To test in daylight, set the TV's clock aside and run it by hand:

  ```sh
  $CTL scene on id=film launch=com.webos.app.hdmi2 mode=cinema night=backlight:30,colorTemperature:-20 nightstart=1 end=$(( $(date +%s) + 600 ))
  ```

- **Open question: which input the values land on.** Picture values belong
  to an input. Check HDMI 2 changed and the TV's own apps did not.
- **Open question: is "the app in front" the whole address of a value?** If
  the TV keeps separate values per picture mode or for HDR, a put-back could
  land in another set than it was read from. Run FILM NIGHT once over an HDR
  film, and once change the picture mode by hand while the scene is on; after
  `scene off` check the values in both modes.
- Turn it off (`$CTL scene off` or the key): mode and values are back.

If a write is refused, the answer names the reason; the call form lives in
`impetus-ctl` (`pic_put`, `pic_read`).

## 6. Screen off, volume, sleep

- **MUSIC:** Spotify opens, a toast says the screen goes off, 20 s later the
  screen is dark with the sound on. Any key brings the picture back. If the
  screen stays on, try the two forms in `screen_off` by hand and keep the
  one that works.
- **Volume:** in WIND DOWN the volume drops to 12 if it was higher, and is
  put back unless it was changed by hand meanwhile.
- **Sleep, short run:** do not wait 60 minutes.

  ```sh
  $CTL scene on id=winddown sleep=3
  ```

  After one minute Impetus comes to the front with a countdown. Press a key:
  the timer is gone and the app from before is back. Run it again and press
  nothing: at zero the app from before comes to the front for a moment, the
  picture values are put back and the TV goes to standby, a normal
  power-off (asked on 5 turns at most; after that the TV is left on). `standby` in `impetus-ctl` tries
  `tvpower/power/turnOff`, then `shutDown`, then
  `com.webos.service.power/shutdown/machineOff`. If the TV stays on at zero,
  run the three by hand, one at a time, and put the one that works first.

## 7. Engine room

Open the door. See: temperature as the big number, uptime, memory and
storage meters, moving every 5 s; WHO TALKS THE MOST with named owners; LOG
with new lines.

- Read ten log lines on the screen and check no hardware address, long hex
  id, UUID or serial shows. If one does, add its shape to `scrubLog` in
  `app/logic.js` (and a case in `tests/test_logic.js`).
- Many `unknown` owners: add the host endings to `ownerOf` in `logic.js`.

## 8. Shield first run (owner's yes at this step)

The shield is off until this step. It changes only memory.

1. Before: `cat /proc/self/mountinfo | grep hosts` and `wc -l /etc/hosts`.
   Homebrew Channel should show `/tmp/hosts` mounted over `/etc/hosts`.
   `awk 'BEGIN{exit}' && echo awk-ok` must print `awk-ok`: the shield
   rebuilds the hosts file with awk and refuses to turn on without it.
2. With the owner's yes: turn SHIELD on in the engine room (or
   `$CTL shield on`).
3. See: `grep -c 127.66.66.66 /etc/hosts` equals the count in
   `shield/hosts.txt`; the lines sit between the two `impetus-shield`
   markers; the room shows `ON`.
4. Open LG's Home and Content Store, come back: the count rises. Zero after
   that can mean (a) those LG apps were already open and keep old answers,
   (b) the names in the list are not the ones this TV calls. For (b), read
   WHO TALKS THE MOST and the log for the real names and edit
   `app/shield/hosts.txt`.
5. Check nothing else broke: Apple TV, Netflix, YouTube and Spotify play.
6. Off: the marker block is gone, `wc -l /etc/hosts` is the number from 1.
7. If `probe` said `count=0`: the shield still blocks, and the room shows
   `ON` with no number.

## 9. Default Home: boot hook, with the revert test

The boot hook is the one file outside `/tmp` and the app folder
(`/var/lib/webosbrew/init.d/impetus-home`, Homebrew Channel's own start-up
folder). It needs the owner's yes here, and the way back is tested once
before it is left in place.

1. SSH works. Steps 3 to 7 passed, or their parts are hidden.
2. Install: `scp boot/impetus-home` to `/tmp/`, then

   ```sh
   cp /tmp/impetus-home /var/lib/webosbrew/init.d/impetus-home
   chmod 755 /var/lib/webosbrew/init.d/impetus-home
   ```

3. The owner restarts the TV (a cold start; the remote only sleeps it). See: about 25 s after the
   system is up, Impetus is in front. Press Home on the remote: Impetus
   comes back. `touch /tmp/impetus-pause` stops that; `rm` it to resume.
   The hook has one brake: if it had to reopen Impetus more than 5 times
   within a minute, it leaves stock Home alone for 2 minutes
   (`rm /tmp/impetus-hook.pid.rest` ends that rest early). The running
   watcher's pid is in `/tmp/impetus-hook.pid`.
4. **Revert test, once, owner watching:**

   ```sh
   sh /media/developer/apps/usr/palm/applications/org.va7dimar.home/bin/impetus-ctl restore
   rm /var/lib/webosbrew/init.d/impetus-home
   ```

   The owner restarts the TV. See: stock Home, and it stays. Without a
   restart the watcher is still running: `touch /tmp/impetus-pause` first,
   then open stock Home (this form passed on 2026-11-14).
5. Only after that passes: install the hook again and leave it.
6. A blank screen or a crash loop at any time: do step 4 at once.
7. **Wake.** With the Apple TV in front, the owner turns the TV off and on
   with its own remote. See: Impetus comes up a few seconds after the
   picture. The boot file's second loop does this from the power state
   (`getPowerState` with a subscription) and the reason in the TV's log;
   it was built against the stand-in and the line shapes on the TV are
   not yet seen. Record them first:

   ```sh
   luna-send -i luna://com.webos.service.tvpower/power/getPowerState '{"subscribe":true}' </dev/null >/tmp/rec-power.log 2>&1 &
   ```

   then read `/tmp/rec-power.log` after the off and on, and fit `wake` in
   `boot/impetus-home` and `sub.power` in the tests to what it shows.
   Waking the TV with the Apple TV's remote should leave the Apple TV in
   front.

## 10. Smaller open points

- **Shortcuts:** each one should land at its place (YouTube Subscriptions,
  Watch later). One that lands on the app's start screen gets its `params`
  fixed or dropped in `app/config.js`.
- **`launch: "last"`:** WIND DOWN goes back to what was in front before
  Impetus. The keeper writes that app's id to `/tmp/impetus/last` as apps
  come to the front; with Netflix in front, `cat /tmp/impetus/last` prints
  its id. An empty file means the foreground subscription in `follow`
  (`impetus-ctl`) gives a different line shape on this TV.
- **Relaunch:** with Impetus already open in the background, opening it
  again shows the living room, not a stale room.

## 11. Write it down

One evidence note, `tvs/lg-65nano756pr/evidence/impetus-home-1.2-tv-run-<date>.md`,
same shape as the photo-frame notes: the probe answer, each open question
above with what the TV did, what was changed because of it, and what is left
on the TV. Then a project-log entry and the version that is installed. No
ids, no addresses, no photos, no personal name.

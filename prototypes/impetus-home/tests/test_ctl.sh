#!/bin/sh
# Host test of app/bin/impetus-ctl against a stand-in TV (tests/stubs).
# Run on Linux (or WSL): sh tests/test_ctl.sh
# Nothing here touches a real TV, /etc or a real mount: every path the helper
# uses is pointed into a scratch folder.

HERE=$(cd "$(dirname "$0")" && pwd)
CTL="$HERE/../app/bin/impetus-ctl"
W=$(mktemp -d)
FAKE=
trap 'kill "$FAKE" 2>/dev/null; sh "$CTL" restore >/dev/null 2>&1; rm -rf "$W"' EXIT

export STUB_TV="$W/tv" IMPETUS_RUN="$W/run" IMPETUS_KEEP="$W/keep"
export IMPETUS_ETC_HOSTS="$W/etc-hosts" IMPETUS_HBC_HOSTS="$W/hbc-hosts" IMPETUS_MOUNTINFO="$W/mountinfo"
export IMPETUS_THERMAL="$W/temp" IMPETUS_LOGS="$W/log" IMPETUS_DISK=/
export PATH="$HERE/stubs:$PATH"

US=org.va7dimar.home
HDMI=com.webos.app.hdmi2
RUN=$IMPETUS_RUN
KEEP=$IMPETUS_KEEP

n=0; failed=0
ok() { n=$((n + 1)); echo "ok  $1"; }
bad() { n=$((n + 1)); failed=$((failed + 1)); echo "FAIL $1"; }
is() { if [ "$2" = "$3" ]; then ok "$1"; else bad "$1 (got '$2', want '$3')"; fi; }
yes() { name=$1; shift; if "$@"; then ok "$name"; else bad "$name"; fi; }
no() { name=$1; shift; if "$@"; then bad "$name"; else ok "$name"; fi; }

pic() { sed -n "s/^$2=//p" "$STUB_TV/pic.$1" 2>/dev/null | tail -n 1; }
calls() { grep -c -F -- "$1" "$STUB_TV/calls"; }
st() { sh "$CTL" state | sed -n "s/^$1=//p"; }
wait_for() { i=0; while [ "$i" -lt 75 ]; do if eval "$1"; then return 0; fi; sleep 0.2; i=$((i + 1)); done; return 1; }
# The lock is a symbolic link; a folder in its place also counts as held.
held() { [ -L "$RUN/lock" ] || [ -d "$RUN/lock" ]; }
settle() { sleep 0.3; wait_for '! held'; }
# The app in front, as the TV and the keeper's follower both see it.
tv_front() { echo "$1" > "$STUB_TV/front"; echo "$1" > "$RUN/front"; }
# A fresh TV. A sleeping process stands in for the keeper, so the helper does
# not start a real one and every turn of it is run by hand with `tick`.
reset() {
  kill "$FAKE" 2>/dev/null
  rm -rf "$RUN" "$KEEP" "$STUB_TV"
  mkdir -p "$RUN" "$STUB_TV"
  : > "$STUB_TV/calls"
  echo 20 > "$STUB_TV/volume"
  printf 'pictureMode=standard\nbacklight=80\ncolorTemperature=0\n' > "$STUB_TV/pic.$HDMI"
  printf 'pictureMode=vivid\nbacklight=70\n' > "$STUB_TV/pic.netflix"
  printf '127.0.0.1 localhost\n10.0.0.1 keepme\n' > "$W/hbc-hosts"
  rm -f "$W/etc-hosts"; ln "$W/hbc-hosts" "$W/etc-hosts"
  echo "36 25 0:31 /hosts $W/etc-hosts rw - tmpfs tmpfs rw" > "$W/mountinfo"
  echo 47000 > "$W/temp"
  echo "2026-11-14T21:03:15.330001Z [5555.310] user.info audiod [] volume changed 14 -> 12" > "$W/log"
  sleep 600 & FAKE=$!
  echo "$FAKE" > "$RUN/keeper.pid"
  tv_front "$US"
}

# ---------- words ----------
reset
refused() { # name want words...
  name=$1; want=$2; shift 2
  out=$(sh "$CTL" "$@"); code=$?
  if [ "$out" = "error=$want" ] && [ "$code" = 2 ]; then ok "refused: $name"; else bad "refused: $name (got '$out' exit $code)"; fi
}
refused "a semicolon" word state 'a;b'
refused "a command substitution" word state '$(reboot)'
refused "a space" word scene on 'id=x y'
refused "a backtick" word scene on id=film 'mode=`reboot`'
refused "shell text in a value" word scene on id=film 'set=backlight:30;reboot'
refused "an unknown picture key" set scene on id=film set=evil:1
refused "an unknown word" word scene on id=film bogus=1
refused "no scene id" id scene on launch=netflix
refused "sleep of 0 minutes" sleep scene on id=film sleep=0
refused "sleep of 601 minutes" sleep scene on id=film sleep=601
refused "volume above 100" volmax scene on id=film volmax=101
refused "screen off after 601 s" screenoff scene on id=film screenoff=601
refused "sleep with a leading zero" sleep scene on id=film sleep=09
refused "an end hour with a leading zero" end scene on id=film end=08
refused "night values without their hours" night scene on id=film night=backlight:30
refused "an unknown verb" verb bogus
refused "an unknown shield word" shield shield maybe
is "a refused call reaches no TV service" "$(wc -l < "$STUB_TV/calls" | tr -d ' ')" 0
no "a refused call leaves no scene" test -e "$RUN/scene.id"

# ---------- probe ----------
reset
tv_front "$HDMI"
p=$(sh "$CTL" probe | tr '\n' ' ')
is "probe: a TV that can do everything" "$p" "exec=1 capture=1 picture=1 screenoff=1 sleep=1 volume=1 shield=1 count=1 log=1 temp=1 "
: > "$STUB_TV/black"; rm -f "$W/log" "$W/temp"; : > "$W/mountinfo"; : > "$STUB_TV/nomount"; tv_front tennis
p=$(sh "$CTL" probe | tr '\n' ' ')
is "probe: black capture, no picture service, no mount, no log" "$p" "exec=1 capture=0 picture=0 screenoff=1 sleep=1 volume=1 shield=0 count=1 log=0 temp=0 "
is "probe changes no picture value" "$(calls setSystemSettings)" 0

# ---------- FILM NIGHT: mode now, night values after sunset, back at sunrise ----------
reset
out=$(IMPETUS_NOW=1000 sh "$CTL" scene on id=film launch=$HDMI mode=cinema night=backlight:30,colorTemperature:-20 nightstart=2000 end=5000)
is "film: scene on answers at once" "$out" "ok=1"
yes "film: picture mode set once the input is in front" wait_for '[ "$(pic $HDMI pictureMode)" = cinema ]'
settle
is "film: the input was opened" "$(cat "$STUB_TV/front")" "$HDMI"
is "film: state names the scene" "$(st scene)" film
is "film: state names the end" "$(st end)" 5000
is "film: the old mode is written down" "$(grep -c '^mode|pictureMode|standard|1$' "$RUN/orig.$HDMI")" 1
yes "film: and mirrored where it survives a restart" cmp -s "$RUN/orig.$HDMI" "$KEEP/orig.$HDMI"
is "film: before sunset the backlight is untouched" "$(pic $HDMI backlight)" 80
IMPETUS_NOW=1500 sh "$CTL" tick >/dev/null
is "film: still untouched just before sunset" "$(pic $HDMI backlight)" 80
IMPETUS_NOW=2100 sh "$CTL" tick >/dev/null
is "film: after sunset the backlight is dimmed" "$(pic $HDMI backlight)" 30
is "film: and the picture is warmer" "$(pic $HDMI colorTemperature)" -20
c=$(calls setSystemSettings)
IMPETUS_NOW=2200 sh "$CTL" tick >/dev/null
is "film: night values are set once, not every turn" "$(calls setSystemSettings)" "$c"
IMPETUS_NOW=5001 sh "$CTL" tick >/dev/null
is "film: at sunrise the backlight is back" "$(pic $HDMI backlight)" 80
is "film: the colour is back" "$(pic $HDMI colorTemperature)" 0
is "film: the mode is back" "$(pic $HDMI pictureMode)" standard
is "film: the scene is over" "$(st scene)" ""
no "film: nothing is left to put back" test -e "$RUN/orig.$HDMI"
no "film: nor in the surviving copy" test -e "$KEEP/orig.$HDMI"

# ---------- WIND DOWN: dim and quiet now, notice, stay up, put back later ----------
reset
echo netflix > "$RUN/last"
out=$(IMPETUS_NOW=10000 sh "$CTL" scene on id=winddown launch=@last fallback=$HDMI set=backlight:25 volmax=12 sleep=60)
is "wind down: scene on answers at once" "$out" "ok=1"
yes "wind down: what was on before is dimmed" wait_for '[ "$(pic netflix backlight)" = 25 ]'
settle
is "wind down: what was on before is opened again" "$(cat "$STUB_TV/front")" netflix
is "wind down: the volume is lowered" "$(cat "$STUB_TV/volume")" 12
is "wind down: standby is set 60 minutes ahead" "$(st sleep)" 13600
is "wind down: the Apple TV picture is not touched" "$(pic $HDMI backlight)" 80
IMPETUS_NOW=13400 sh "$CTL" tick >/dev/null
no "wind down: no notice before the last 2 minutes" test -e "$RUN/sleep.noticed"
IMPETUS_NOW=13490 sh "$CTL" tick >/dev/null
is "wind down: the notice opens Impetus with the hour" "$(calls '"id":"org.va7dimar.home","params":{"notice":"sleep","until":13600}')" 1
IMPETUS_NOW=13493 sh "$CTL" tick >/dev/null
is "wind down: the notice is shown once" "$(calls '"notice":"sleep"')" 1
tv_front "$US"
is "wind down: a key press cancels and names what was on" "$(sh "$CTL" sleep cancel)" "prev=netflix"
is "wind down: no standby is waiting" "$(st sleep)" ""
IMPETUS_NOW=13700 sh "$CTL" tick >/dev/null
is "wind down: the TV stays up" "$(calls tvpower/power/turnOff)" 0
is "wind down: scene off answers" "$(sh "$CTL" scene off)" "ok=1"
is "wind down: the volume is back at once" "$(cat "$STUB_TV/volume")" 20
is "wind down: the picture waits while another app is in front" "$(pic netflix backlight)" 25
yes "wind down: the wait is written down" test -e "$RUN/pending.netflix"
tv_front netflix
sh "$CTL" tick >/dev/null
is "wind down: the picture is back once its app is in front" "$(pic netflix backlight)" 70
no "wind down: nothing is left waiting" test -e "$RUN/pending.netflix"

# A volume the owner changed in between is left alone.
reset
echo netflix > "$RUN/last"
IMPETUS_NOW=10000 sh "$CTL" scene on id=winddown launch=@last volmax=12 >/dev/null
wait_for '[ -s "$RUN/vol" ]'; settle
echo 15 > "$STUB_TV/volume"
sh "$CTL" scene off >/dev/null
is "wind down: a volume changed by hand is not overwritten" "$(cat "$STUB_TV/volume")" 15

# With nothing on before, the fallback is used.
reset
IMPETUS_NOW=10000 sh "$CTL" scene on id=winddown launch=@last fallback=$HDMI sleep=1 >/dev/null
wait_for '[ -s "$RUN/sleep.until" ]'; settle
is "wind down: with nothing on before, the fallback opens" "$(cat "$STUB_TV/front")" "$HDMI"

# ---------- the sleep timer ends in a normal power-off ----------
IMPETUS_NOW=10061 sh "$CTL" tick >/dev/null
is "sleep: the first power-off call is tried" "$(calls tvpower/power/turnOff)" 1
is "sleep: the next one is taken when the first is unknown" "$(calls tvpower/power/shutDown)" 1
is "sleep: no further call after one is accepted" "$(calls machineOff)" 0
is "sleep: never a reboot" "$(calls reboot)" 0
is "sleep: the scene is over" "$(st scene)" ""
c=$(calls tvpower/power/)
IMPETUS_NOW=10070 sh "$CTL" tick >/dev/null
is "sleep: power-off is asked once" "$(calls tvpower/power/)" "$c"

# ---------- MUSIC: screen off, sound on ----------
reset
out=$(IMPETUS_NOW=30000 sh "$CTL" scene on id=music launch=spotify-beehive screenoff=20)
wait_for '[ -s "$RUN/screenoff.at" ]'; settle
is "music: Spotify is opened" "$(cat "$STUB_TV/front")" spotify-beehive
is "music: the screen-off hour is set" "$(st screenoff)" 30020
is "music: a toast says so" "$(calls 'Screen off in 20 seconds')" 1
tv_front spotify-beehive
IMPETUS_NOW=30010 sh "$CTL" tick >/dev/null
is "music: the screen stays on until then" "$(calls turnOffScreen)" 0
IMPETUS_NOW=30021 sh "$CTL" tick >/dev/null
is "music: the screen goes off" "$(calls turnOffScreen)" 1
is "music: with nothing to undo the scene is over" "$(st scene)" ""
reset
IMPETUS_NOW=30000 sh "$CTL" scene on id=music launch=spotify-beehive screenoff=20 >/dev/null
wait_for '[ -s "$RUN/screenoff.at" ]'; settle
tv_front netflix
IMPETUS_NOW=30021 sh "$CTL" tick >/dev/null
is "music: the screen stays on when another app is in front" "$(calls turnOffScreen)" 0

# ---------- one scene replaces another ----------
reset
IMPETUS_NOW=1000 sh "$CTL" scene on id=film launch=$HDMI mode=cinema >/dev/null
wait_for '[ "$(pic $HDMI pictureMode)" = cinema ]'; settle
tv_front "$US"
IMPETUS_NOW=1100 sh "$CTL" scene on id=music launch=spotify-beehive screenoff=20 >/dev/null
wait_for '[ "$(cat "$RUN/scene.id" 2>/dev/null)" = music ]'; settle
is "switch: the new scene is on" "$(st scene)" music
yes "switch: the old scene's picture waits for its input" test -e "$RUN/pending.$HDMI"
tv_front "$HDMI"
sh "$CTL" tick >/dev/null
is "switch: and is put back when the input is in front" "$(pic $HDMI pictureMode)" standard

# ---------- the still ----------
reset
tv_front "$HDMI"
sh "$CTL" still > "$W/still"
is "still: a live frame says so" "$(head -n 1 "$W/still")" "kind=live age=0"
is "still: and carries the picture" "$(wc -c < "$W/still" | tr -d ' ')" 4016
: > "$STUB_TV/black"
is "still: a black frame with nothing kept is no still" "$(sh "$CTL" still | head -n 1)" "kind=none age=0"
head -c 3000 /dev/zero | tr '\0' 'y' > "$RUN/last.jpg"; echo 40000 > "$RUN/last.at"
IMPETUS_NOW=40720 sh "$CTL" still > "$W/still"
is "still: a black frame falls back to the kept one, with its age" "$(head -n 1 "$W/still")" "kind=last age=720"
is "still: the kept picture is the one sent" "$(tail -c 3000 "$W/still" | tr -d 'y' | wc -c | tr -d ' ')" 0
rm -f "$STUB_TV/black"
is "still: nolive skips the capture" "$(IMPETUS_NOW=40720 sh "$CTL" still nolive | head -n 1)" "kind=last age=720"
is "still: a kept one older than 6 hours is dropped" "$(IMPETUS_NOW=70000 sh "$CTL" still nolive | head -n 1)" "kind=none age=0"

# ---------- the shield, where Homebrew Channel already keeps hosts in memory ----------
reset
cp "$W/hbc-hosts" "$W/hosts.before"
is "shield: on answers" "$(sh "$CTL" shield on)" "ok=1"
is "shield: an LG ad host goes to the dead address" "$(grep -c '^127.66.66.66 lgads.tv$' "$W/etc-hosts")" 1
is "shield: on IPv6 too" "$(grep -c '^::1 lgads.tv$' "$W/etc-hosts")" 1
is "shield: the lines that were there stay" "$(grep -c '^10.0.0.1 keepme$' "$W/etc-hosts")" 1
is "shield: firmware update hosts are not in the list" "$(grep -c 'snu.lge.com' "$W/etc-hosts")" 0
is "shield: nothing but list lines between the markers" "$(sed -n '/^# impetus-shield begin/,/^# impetus-shield end/p' "$W/etc-hosts" | grep -v -c -e '^127.66.66.66 [a-z0-9.-]*$' -e '^::1 [a-z0-9.-]*$' -e '^# impetus-shield')" 0
yes "shield: the counter reports" wait_for '[ "$(st hits)" = 7 ]'
is "shield: state says on" "$(st shield)" on
yes "shield: on is remembered across a restart" test -e "$KEEP/shield.on"
sh "$CTL" shield on >/dev/null
is "shield: on twice adds the lines once" "$(grep -c '^# impetus-shield begin' "$W/etc-hosts")" 1
read -r _kind cpid < "$RUN/shield.count"
is "shield: off answers" "$(sh "$CTL" shield off)" "ok=1"
yes "shield: off leaves the hosts file as it was" cmp -s "$W/etc-hosts" "$W/hosts.before"
yes "shield: the counter is stopped" wait_for '! kill -0 "$cpid" 2>/dev/null'
is "shield: state says off" "$(st shield)" off
no "shield: off is remembered too" test -e "$KEEP/shield.on"
is "shield: no mount was made" "$(grep -c '^mount ' "$STUB_TV/calls")" 0

# ---------- the shield, with its own mount ----------
reset
rm -f "$W/etc-hosts"; printf '127.0.0.1 localhost\n' > "$W/etc-hosts"; : > "$W/mountinfo"
cp "$W/etc-hosts" "$W/hosts.before"
is "shield (own mount): on answers" "$(sh "$CTL" shield on)" "ok=1"
is "shield (own mount): the hosts file shows the list" "$(grep -c '^127.66.66.66 lgads.tv$' "$W/etc-hosts")" 1
is "shield (own mount): one mount" "$(grep -c '^mount ' "$STUB_TV/calls")" 1
sh "$CTL" shield off >/dev/null
yes "shield (own mount): off leaves the hosts file as it was" cmp -s "$W/etc-hosts" "$W/hosts.before"
: > "$STUB_TV/nomount"
out=$(sh "$CTL" shield on)
is "shield (own mount): a failed mount is reported" "$out" "error=nomount"
is "shield (own mount): and leaves the shield off" "$(st shield)" off
yes "shield (own mount): and the hosts file as it was" cmp -s "$W/etc-hosts" "$W/hosts.before"

# ---------- values go back in the form they were read in ----------
reset
: > "$STUB_TV/numeric"
IMPETUS_NOW=1000 sh "$CTL" scene on id=film launch=$HDMI set=backlight:30,colorTemperature:-20 >/dev/null
wait_for '[ "$(pic $HDMI colorTemperature)" = -20 ]'; settle
is "numbers: a TV that answers in numbers gets a number" "$(calls '"backlight":30}')" 1
is "numbers: a negative value is a number too" "$(calls '"colorTemperature":-20}')" 1
tv_front "$HDMI"
sh "$CTL" scene off >/dev/null
is "numbers: and the old value goes back as a number" "$(calls '"backlight":80}')" 1
reset
IMPETUS_NOW=1000 sh "$CTL" scene on id=film launch=$HDMI set=colorTemperature:-20 >/dev/null
wait_for '[ "$(pic $HDMI colorTemperature)" = -20 ]'; settle
is "numbers: a TV that answers in text gets text" "$(calls '"colorTemperature":"-20"')" 1

# ---------- a put-back the TV refuses is kept and tried again ----------
reset
IMPETUS_NOW=1000 sh "$CTL" scene on id=film launch=$HDMI mode=cinema >/dev/null
wait_for '[ "$(pic $HDMI pictureMode)" = cinema ]'; settle
tv_front "$HDMI"
: > "$STUB_TV/failset"
is "refused put-back: scene off still answers" "$(sh "$CTL" scene off)" "ok=1"
is "refused put-back: the picture is still the scene's" "$(pic $HDMI pictureMode)" cinema
yes "refused put-back: the old values are kept" test -s "$RUN/orig.$HDMI"
yes "refused put-back: on disk too" test -s "$KEEP/orig.$HDMI"
yes "refused put-back: and the put-back waits" test -e "$RUN/pending.$HDMI"
rm -f "$STUB_TV/failset"
sh "$CTL" tick >/dev/null
is "refused put-back: the next turn puts the picture back" "$(pic $HDMI pictureMode)" standard
no "refused put-back: nothing is left waiting" test -e "$RUN/pending.$HDMI"
no "refused put-back: nor on disk" test -e "$KEEP/orig.$HDMI"
# A TV that keeps refusing: the turns stop, the record stays for `restore`.
reset
IMPETUS_NOW=1000 sh "$CTL" scene on id=film launch=$HDMI mode=cinema >/dev/null
wait_for '[ "$(pic $HDMI pictureMode)" = cinema ]'; settle
tv_front "$HDMI"
: > "$STUB_TV/failset"
sh "$CTL" scene off >/dev/null
i=0; while [ "$i" -lt 19 ]; do sh "$CTL" tick >/dev/null; i=$((i + 1)); done
no "refused put-back: after 20 turns the keeper stops trying" test -e "$RUN/pending.$HDMI"
yes "refused put-back: but the record stays on disk" test -s "$KEEP/orig.$HDMI"
c=$(calls setSystemSettings)
sh "$CTL" tick >/dev/null
is "refused put-back: no further call once it stopped" "$(calls setSystemSettings)" "$c"
rm -f "$STUB_TV/failset"
is "refused put-back: restore still puts it back" "$(sh "$CTL" restore)" "ok=1"
is "refused put-back: the picture is back" "$(pic $HDMI pictureMode)" standard

# A key this TV never takes: nothing was changed, so nothing is left to put back.
reset
echo 'contrast=85' >> "$STUB_TV/pic.$HDMI"
echo contrast > "$STUB_TV/failkey"
IMPETUS_NOW=1000 sh "$CTL" scene on id=film launch=$HDMI mode=cinema set=backlight:30,contrast:50 >/dev/null
wait_for '[ "$(pic $HDMI backlight)" = 30 ]'; settle
tv_front "$HDMI"
sh "$CTL" scene off >/dev/null
is "refused key: the rest of the picture is back" "$(pic $HDMI backlight)$(pic $HDMI pictureMode)" 80standard
no "refused key: and no record is left to try again" test -e "$KEEP/orig.$HDMI"
# One value refused at put-back: the mode waits with it, and the values are
# never written into the mode from before.
reset
IMPETUS_NOW=1000 sh "$CTL" scene on id=film launch=$HDMI mode=cinema set=backlight:30 >/dev/null
wait_for '[ "$(pic $HDMI backlight)" = 30 ]'; settle
tv_front "$HDMI"
echo backlight > "$STUB_TV/failkey"
sh "$CTL" scene off >/dev/null
sh "$CTL" tick >/dev/null
is "refused value: the mode stays with its values" "$(pic $HDMI pictureMode)" cinema
is "refused value: the mode from before is not asked for yet" "$(calls '"pictureMode":"standard"')" 0
rm -f "$STUB_TV/failkey"
sh "$CTL" tick >/dev/null
is "refused value: once it is taken, value and mode go back" "$(pic $HDMI backlight)$(pic $HDMI pictureMode)" 80standard
is "refused value: the mode went back once" "$(calls '"pictureMode":"standard"')" 1

# ---------- a value that cannot be written down is not changed ----------
reset
: > "$KEEP"
echo netflix > "$RUN/last"
IMPETUS_NOW=10000 sh "$CTL" scene on id=winddown launch=@last volmax=12 >/dev/null
wait_for '[ -e "$RUN/scene.id" ]'; settle
is "no record, no change: the volume is untouched" "$(cat "$STUB_TV/volume")" 20
rm -f "$KEEP"
reset
: > "$KEEP"   # a file where the state folder should be
IMPETUS_NOW=1000 sh "$CTL" scene on id=film launch=$HDMI mode=cinema set=backlight:30 >/dev/null
wait_for '[ -e "$RUN/scene.apply" ]'; wait_for '[ ! -e "$RUN/scene.apply" ]'; settle
is "no record, no change: the mode is untouched" "$(pic $HDMI pictureMode)" standard
is "no record, no change: the backlight is untouched" "$(pic $HDMI backlight)" 80
is "no record, no change: the TV was not asked" "$(calls setSystemSettings)" 0
rm -f "$KEEP"

# ---------- restore never writes one input's picture to another ----------
reset
mkdir -p "$KEEP"
printf 'pic|backlight|70|1\n' > "$KEEP/orig.netflix"
printf 'pictureMode=vivid\nbacklight=25\n' > "$STUB_TV/pic.netflix"
: > "$STUB_TV/nolaunch"
out=$(IMPETUS_FRONTWAIT=1 sh "$CTL" restore); code=$?
is "restore: an app that will not open is named" "$out" "error=notrestored netflix"
is "restore: and the exit code says so" "$code" 1
is "restore: nothing was written to what is in front" "$(calls setSystemSettings)" 0
yes "restore: its record stays on disk" test -s "$KEEP/orig.netflix"
rm -f "$STUB_TV/nolaunch"
is "restore: a second try finishes the job" "$(sh "$CTL" restore)" "ok=1"
is "restore: the picture is back" "$(pic netflix backlight)" 70
no "restore: the record is gone" test -e "$KEEP/orig.netflix"

# ---------- the volume survives a restart ----------
reset
echo netflix > "$RUN/last"
IMPETUS_NOW=10000 sh "$CTL" scene on id=winddown launch=@last volmax=12 >/dev/null
wait_for '[ "$(cat "$STUB_TV/volume")" = 12 ]'; settle
is "volume: written down where it survives a restart" "$(cat "$KEEP/vol" 2>/dev/null)" "20 12"
kill "$FAKE" 2>/dev/null; rm -rf "$RUN"
sh "$CTL" start >/dev/null
yes "volume: put back after a restart" wait_for '[ "$(cat "$STUB_TV/volume")" = 20 ]'
yes "volume: and the record is gone" wait_for '[ ! -e "$KEEP/vol" ]'
sh "$CTL" restore >/dev/null
# A verb that runs before the keeper has looked: the record on disk still counts.
reset
mkdir -p "$KEEP"; echo "20 12" > "$KEEP/vol"; echo 12 > "$STUB_TV/volume"
sh "$CTL" scene off >/dev/null
is "volume: a record only on disk is used, not thrown away" "$(cat "$STUB_TV/volume")" 20
no "volume: and is gone once the volume is back" test -e "$KEEP/vol"
# A TV that does not answer at scene end: the record waits for the next turn.
reset
echo netflix > "$RUN/last"
IMPETUS_NOW=10000 sh "$CTL" scene on id=winddown launch=@last volmax=12 >/dev/null
wait_for '[ "$(cat "$STUB_TV/volume")" = 12 ]'; settle
: > "$STUB_TV/novolume"
sh "$CTL" scene off >/dev/null
is "volume: left alone while the TV does not answer" "$(cat "$STUB_TV/volume")" 12
yes "volume: the record waits" test -s "$RUN/vol"
rm -f "$STUB_TV/novolume"
sh "$CTL" tick >/dev/null
is "volume: back on the next turn" "$(cat "$STUB_TV/volume")" 20
no "volume: nothing is left waiting" test -e "$RUN/vol"

# ---------- the sleep timer puts the picture back before the power-off ----------
reset
echo netflix > "$RUN/last"
IMPETUS_NOW=10000 sh "$CTL" scene on id=winddown launch=@last set=backlight:25 sleep=1 >/dev/null
wait_for '[ "$(pic netflix backlight)" = 25 ]'; settle
IMPETUS_NOW=10000 sh "$CTL" tick >/dev/null
tv_front "$US"   # the notice put Impetus in front
IMPETUS_NOW=10061 sh "$CTL" tick >/dev/null
is "sleep: the picture is back before the TV goes off" "$(pic netflix backlight)" 70
a=$(grep -n -F '"backlight":"70"' "$STUB_TV/calls" | head -n 1 | cut -d: -f1)
b=$(grep -n -F 'power/shutDown' "$STUB_TV/calls" | head -n 1 | cut -d: -f1)
yes "sleep: the put-back comes first, then the power-off" test "${a:-9999}" -lt "${b:-0}"
no "sleep: nothing is left waiting" test -e "$RUN/pending.netflix"
no "sleep: nor on disk" test -e "$KEEP/orig.netflix"

# A timer cancelled while a turn waits for the lock: the TV stays on.
reset
IMPETUS_NOW=10000 sh "$CTL" scene on id=winddown launch=@last fallback=$HDMI sleep=1 >/dev/null
wait_for '[ -s "$RUN/sleep.until" ]'; settle
mkdir "$RUN/lock"
IMPETUS_NOW=10061 sh "$CTL" tick >/dev/null &
tp=$!
sleep 0.5; rm -f "$RUN/sleep.until"; rmdir "$RUN/lock"
wait "$tp"
is "sleep: a timer cancelled in the last second gives no power-off" "$(calls tvpower/power/)" 0
is "sleep: and the scene stays on" "$(st scene)" winddown

# A TV that takes no power call: asked 5 turns, then left on.
reset
IMPETUS_NOW=10000 sh "$CTL" scene on id=winddown launch=@last fallback=$HDMI sleep=1 >/dev/null
wait_for '[ -s "$RUN/sleep.until" ]'; settle
: > "$STUB_TV/nopower"
i=0; while [ "$i" -lt 7 ]; do IMPETUS_NOW=10061 sh "$CTL" tick >/dev/null; i=$((i + 1)); done
is "sleep: a refused power-off is asked 5 turns, no more" "$(calls machineOff)" 5
is "sleep: then no standby is waiting" "$(st sleep)" ""

# ---------- the shield: odd hosts files, refusals, one counter ----------
reset
printf '127.0.0.1 localhost\n10.0.0.1 keepme' > "$W/hbc-hosts"   # no newline at the end
sh "$CTL" shield on >/dev/null
is "shield: a last line without a newline stays whole" "$(grep -c '^10.0.0.1 keepme$' "$W/etc-hosts")" 1
is "shield: and the marker gets its own line" "$(grep -c '^# impetus-shield begin$' "$W/etc-hosts")" 1
sh "$CTL" shield off >/dev/null
is "shield: off leaves the two lines" "$(cat "$W/etc-hosts")" "127.0.0.1 localhost
10.0.0.1 keepme"
reset
printf '127.0.0.1 localhost\n# impetus-shield begin\n127.66.66.66 lgads.tv\n::1 lgads.tv\n127.66.66.66 old.example\n10.0.0.1 keepme\n::1 localhost6\n' > "$W/hbc-hosts"
sh "$CTL" shield on >/dev/null
is "shield: a block cut off earlier is replaced, not doubled" "$(grep -c '^# impetus-shield begin' "$W/etc-hosts")" 1
is "shield: its leftover lines are gone" "$(grep -c 'old.example' "$W/etc-hosts")" 0
is "shield: each host is there once" "$(grep -c '^127.66.66.66 lgads.tv$' "$W/etc-hosts")" 1
sh "$CTL" shield off >/dev/null
is "shield: off leaves only the lines that were not ours" "$(cat "$W/etc-hosts")" "127.0.0.1 localhost
10.0.0.1 keepme
::1 localhost6"
reset
sh "$CTL" shield on >/dev/null
wait_for '[ -s "$RUN/shield.count" ]'
read -r _kind cpid1 < "$RUN/shield.count"
sh "$CTL" shield on >/dev/null
read -r _kind cpid2 < "$RUN/shield.count"
yes "shield: on twice stops the first counter" wait_for '! kill -0 "$cpid1" 2>/dev/null'
yes "shield: and leaves one running" kill -0 "$cpid2"
sh "$CTL" shield off >/dev/null
# A TV whose awk fails: the hosts file is left alone rather than cut down.
reset
mkdir -p "$W/bin"; printf '#!/bin/sh\nexit 1\n' > "$W/bin/awk"; chmod 755 "$W/bin/awk"
cp "$W/hbc-hosts" "$W/hosts.before"
is "shield: without a working awk it stays off" "$(PATH="$W/bin:$PATH" sh "$CTL" shield on)" "error=nomount"
yes "shield: and the hosts file is untouched" cmp -s "$W/etc-hosts" "$W/hosts.before"
sh "$CTL" shield on >/dev/null
cp "$W/hbc-hosts" "$W/hosts.on"
is "shield: off without a working awk is reported" "$(PATH="$W/bin:$PATH" sh "$CTL" shield off)" "error=busy"
yes "shield: and the hosts file keeps every line" cmp -s "$W/etc-hosts" "$W/hosts.on"
is "shield: a later off finishes the job" "$(sh "$CTL" shield off)" "ok=1"
yes "shield: the hosts file is as it was" cmp -s "$W/etc-hosts" "$W/hosts.before"
rm -rf "$W/bin"
# A marker that cannot be written must not end the helper with the lock held.
reset
mkdir -p "$KEEP/shield.on"   # a folder where the marker file should be
is "shield: on still answers when its marker cannot be written" "$(sh "$CTL" shield on)" "ok=1"
no "shield: and the lock is free again" held
sh "$CTL" shield off >/dev/null 2>&1
# With its own mount: a mount that fails is not on record, one that will not
# let go keeps the shield on record.
reset
rm -f "$W/etc-hosts"; printf '127.0.0.1 localhost\n' > "$W/etc-hosts"; : > "$W/mountinfo"
: > "$STUB_TV/nomount"
sh "$CTL" shield on >/dev/null
no "shield (own mount): a failed mount is not on record" test -e "$RUN/shield.mode"
is "shield (own mount): so no unmount is tried" "$(grep -c '^umount ' "$STUB_TV/calls")" 0
no "shield (own mount): and it is not remembered" test -e "$KEEP/shield.on"
rm -f "$STUB_TV/nomount"
sh "$CTL" shield on >/dev/null
: > "$STUB_TV/noumount"
out=$(sh "$CTL" shield off); code=$?
is "shield (own mount): a mount that will not let go is reported" "$out exit $code" "error=busy exit 1"
is "shield (own mount): and the shield stays on record" "$(st shield)" on
yes "shield (own mount): across a restart too" test -e "$KEEP/shield.on"
rm -f "$STUB_TV/noumount"
is "shield (own mount): a later off finishes the job" "$(sh "$CTL" shield off)" "ok=1"
is "shield (own mount): the hosts file is as it was" "$(cat "$W/etc-hosts")" "127.0.0.1 localhost"

# ---------- the lock has an owner ----------
reset
owner() { ls -ld "$RUN/lock" 2>/dev/null | sed -n 's/.* -> //p' | cut -d. -f1; }
up() { cut -d. -f1 /proc/uptime; }
secs() { date +%s; }
# hold pid since: a lock in place, as that holder would have made it. The
# link is made aside and moved in, so there is no moment without a lock.
hold() { rm -rf "$RUN/lock.n"; ln -s "$1.$2" "$RUN/lock.n"; mv -f "$RUN/lock.n" "$RUN/lock"; }
# Its holder is running: a verb waits, goes on without it, and leaves it.
hold "$FAKE" "$(up)"
t0=$(secs); out=$(IMPETUS_LOCKWAIT=2 sh "$CTL" scene off); t1=$(secs)
is "lock: a verb that could not get it still answers" "$out" "ok=1"
yes "lock: after waiting for it" test $((t1 - t0)) -ge 1
is "lock: a running holder keeps its lock" "$(owner)" "$FAKE"
# Its holder is gone: taken over at once.
sleep 0 & gone=$!; wait "$gone"
hold "$gone" "$(up)"
t0=$(secs); out=$(sh "$CTL" scene off); t1=$(secs)
is "lock: one whose holder is gone is taken over" "$out" "ok=1"
yes "lock: and at once" test $((t1 - t0)) -le 2
no "lock: and given back afterwards" held
# The way back does not wait for a lock a stopped keeper left either.
hold "$gone" "$(up)"
t0=$(secs); out=$(sh "$CTL" restore); t1=$(secs)
is "lock: the way back takes a gone holder's lock" "$out" "ok=1"
yes "lock: and at once too" test $((t1 - t0)) -le 2
no "lock: and gives it back" held
reset
# Held longer than the limit, holder still running: taken over.
hold "$FAKE" "$(( $(up) - 5 ))"
IMPETUS_LOCKMAX=2 sh "$CTL" scene off >/dev/null
no "lock: one held far too long is taken over" held
# Something without a holder's name in its place: taken over after three tries.
mkdir "$RUN/lock"
t0=$(secs); sh "$CTL" scene off >/dev/null; t1=$(secs)
no "lock: a folder left in its place is taken over" held
yes "lock: after three tries, not at once" test $((t1 - t0)) -ge 2
is "lock: nothing is left of the old ones" "$(ls -d "$RUN"/lock.old.* 2>/dev/null | wc -l | tr -d ' ')" 0
# One or two tries without a name do not count once a holder's name is back.
ln -s nobody "$RUN/lock"
IMPETUS_LOCKWAIT=5 sh "$CTL" sleep cancel >/dev/null &
cp=$!
sleep 1.5; hold "$FAKE" "$(up)"
wait "$cp"
is "lock: a name that was missing for a moment is not a free lock" "$(owner)" "$FAKE"
rm -f "$RUN/lock"

# A call that never answers is given up; the holder that meanwhile lost its
# lock leaves the new holder's lock alone.
echo "30 10" > "$RUN/vol"; echo 10 > "$STUB_TV/volume"
echo getVolume > "$STUB_TV/hang"
t0=$(secs)
IMPETUS_LUNAWAIT=3 sh "$CTL" scene off > "$W/hang.out" &
hp=$!
wait_for '[ -n "$(owner)" ]'
is "lock: its holder is on record while it works" "$(owner)" "$hp"
hold "$FAKE" "$(up)"
wait "$hp"; t1=$(secs)
yes "no answer: the call is given up after its limit" test $((t1 - t0)) -le 8
is "no answer: the verb still answers" "$(cat "$W/hang.out")" "ok=1"
is "no answer: the volume record waits for the next turn" "$(cat "$RUN/vol")" "30 10"
is "lock: a holder that lost it leaves the new one" "$(owner)" "$FAKE"
rm -f "$RUN/lock" "$STUB_TV/hang"
sh "$CTL" tick >/dev/null
is "no answer: the next turn puts the volume back" "$(cat "$STUB_TV/volume")" 30

# A call the TV carries out but answers too late: the record stays, so the
# volume still goes back.
reset
: > "$STUB_TV/latevolume"
IMPETUS_LUNAWAIT=2 sh "$CTL" scene on id=music launch=$HDMI volmax=10 >/dev/null
yes "late answer: the volume was lowered all the same" wait_for '[ "$(cat "$STUB_TV/volume")" = 10 ]'
yes "late answer: the scene's background part ends" wait_for '[ "$(st scene)" = music ] && ! held'
settle
is "late answer: the volume from before is still on record" "$(cat "$RUN/vol" 2>/dev/null)" "20 10"
rm -f "$STUB_TV/latevolume"
sh "$CTL" scene off >/dev/null
is "late answer: and goes back when the scene ends" "$(cat "$STUB_TV/volume")" 20

# A scene's own background part holds the lock under a pid that is running.
reset
echo getVolume > "$STUB_TV/hang"
IMPETUS_LUNAWAIT=3 sh "$CTL" scene on id=music launch=$HDMI volmax=10 >/dev/null
yes "lock: the background part of a scene is on record" wait_for '[ -n "$(owner)" ]'
yes "lock: and counts as running" kill -0 "$(owner)"
rm -f "$STUB_TV/hang"
yes "lock: it gives the lock back when done" wait_for '! held'
settle

# The keeper starting during a verb leaves the verb's lock.
reset
kill "$FAKE" 2>/dev/null; rm -f "$RUN/keeper.pid"
sleep 600 & HOLD=$!
hold "$HOLD" "$(up)"
sh "$CTL" start >/dev/null
yes "lock: a keeper starts" wait_for '[ "$(st keeper)" = 1 ]'
sleep 1
is "lock: a starting keeper leaves a verb's lock" "$(owner)" "$HOLD"
kp=$(cat "$RUN/keeper.pid"); kill "$kp" 2>/dev/null
yes "lock: a stopped keeper ends" wait_for '! kill -0 "$kp" 2>/dev/null'
is "lock: and still leaves it" "$(owner)" "$HOLD"
kill "$HOLD" 2>/dev/null; rm -f "$RUN/lock"

# ---------- the engine room's one answer ----------
reset
e=$(sh "$CTL" engine)
is "engine: four sections in order" "$(echo "$e" | grep '^@' | tr '\n' ' ')" "@vitals @state @talk @log "
is "engine: the temperature" "$(echo "$e" | sed -n 's/^temp=//p')" 47000
is "engine: the log's last line" "$(echo "$e" | tail -n 1 | grep -c 'volume changed 14 -> 12')" 1

# ---------- after a restart: the real keeper puts things back ----------
reset
kill "$FAKE" 2>/dev/null; rm -rf "$RUN"
mkdir -p "$KEEP"
echo 'pic|backlight|80|1' > "$KEEP/orig.$HDMI"; : > "$KEEP/shield.on"
printf 'pictureMode=standard\nbacklight=30\n' > "$STUB_TV/pic.$HDMI"
echo "$HDMI" > "$STUB_TV/front"
is "restart: start answers" "$(sh "$CTL" start target=$HDMI)" "ok=1"
yes "restart: the keeper is running" wait_for '[ "$(st keeper)" = 1 ]'
yes "restart: the interrupted scene's picture is put back" wait_for '[ "$(pic $HDMI backlight)" = 80 ]'
yes "restart: the shield is back on" wait_for '[ "$(st shield)" = on ]'
yes "restart: the keeper notes the app in front" wait_for '[ "$(cat "$RUN/last" 2>/dev/null)" = "$HDMI" ]'
is "restart: the still's target is kept" "$(cat "$RUN/still.target")" "$HDMI"
yes "restart: the keeper keeps a still of the target at once" wait_for '[ -s "$RUN/last.jpg" ] && [ -s "$RUN/last.at" ]'
kpid=$(cat "$RUN/keeper.pid")
sh "$CTL" start >/dev/null
is "restart: a second start keeps the same keeper" "$(cat "$RUN/keeper.pid")" "$kpid"

# ---------- the way back ----------
IMPETUS_NOW=1000 sh "$CTL" scene on id=film launch=$HDMI mode=cinema >/dev/null
wait_for '[ "$(pic $HDMI pictureMode)" = cinema ]'; settle
printf 'pic|backlight|70|1\n' > "$KEEP/orig.netflix"
printf 'pictureMode=vivid\nbacklight=25\n' > "$STUB_TV/pic.netflix"
is "way back: restore answers" "$(sh "$CTL" restore)" "ok=1"
is "way back: the scene's picture is back" "$(pic $HDMI pictureMode)" standard
is "way back: a set that was only on disk is back too" "$(pic netflix backlight)" 70
is "way back: the shield is off" "$(grep -c 'impetus-shield' "$W/etc-hosts")" 0
is "way back: no scene" "$(st scene)" ""
yes "way back: the keeper is stopped" wait_for '! kill -0 "$kpid" 2>/dev/null'
# An old keeper that ends late must not remove a new keeper's record.
sh "$CTL" start >/dev/null
wait_for '[ "$(st keeper)" = 1 ]'
k1=$(cat "$RUN/keeper.pid")
echo 999999 > "$RUN/keeper.pid"
yes "keeper: one that is no longer on record ends by itself" wait_for '! kill -0 "$k1" 2>/dev/null'
is "keeper: and leaves the record of the other alone" "$(cat "$RUN/keeper.pid")" 999999
rm -f "$RUN/keeper.pid"
is "way back: nothing is kept on disk" "$(ls "$KEEP" | wc -l | tr -d ' ')" 0
is "way back: no power call, no reboot" "$(calls tvpower/power/turnOff)$(calls reboot)" 00

# ---------- the boot hook: one watcher, and a brake ----------
reset
HOOK="$HERE/../boot/impetus-home"
export IMPETUS_CTL="$W/no-helper" IMPETUS_PAUSE="$W/pause" IMPETUS_HOOK_PID="$W/hook.pid" IMPETUS_HOOK_WAIT=0
i=0; while [ "$i" -lt 8 ]; do echo '{"appId":"com.webos.app.home","returnValue":true}'; i=$((i + 1)); done > "$STUB_TV/sub.lines"
tv_front com.webos.app.home
sh "$HOOK"
yes "boot hook: a watcher is on record" wait_for '[ -s "$W/hook.pid" ]'
hp=$(cat "$W/hook.pid")
yes "boot hook: stock Home in front opens Impetus" wait_for '[ "$(calls "\"id\":\"$US\"")" -ge 1 ]'
yes "boot hook: Impetus closing over and over ends in a rest" wait_for '[ -s "$W/hook.pid.rest" ]'
is "boot hook: 5 reopenings before the rest, no more" "$(calls "\"id\":\"$US\"")" 5
sh "$HOOK"
is "boot hook: a second run keeps the first watcher" "$(cat "$W/hook.pid")" "$hp"
kill "$hp" 2>/dev/null
# Paused: stock Home is left alone.
reset
: > "$W/pause"; rm -f "$W/hook.pid" "$W/hook.pid.rest" "$W/hook.pid.count"
echo '{"appId":"com.webos.app.home","returnValue":true}' > "$STUB_TV/sub.lines"
sh "$HOOK"
wait_for '[ -s "$W/hook.pid" ]'; sleep 1
is "boot hook: paused, it opens nothing" "$(calls applicationmanager/launch)" 0
kill "$(cat "$W/hook.pid")" 2>/dev/null
# A wake: the TV shows its last input and stock Home never comes up. The
# hook opens Impetus once when it starts; a wake is one opening more.
export IMPETUS_HOOK_WAKE=0 IMPETUS_HOOK_LOG="$W/tvlog"
wake_run() {   # $1: the states the TV reports, one per line; $2: the log's last power line
  reset
  rm -f "$W/pause" "$W/hook.pid" "$W/hook.pid.rest" "$W/hook.pid.count"
  echo '{"appId":"com.webos.app.hdmi2","returnValue":true}' > "$STUB_TV/sub.lines"
  tv_front com.webos.app.hdmi2
  echo "$1" | while read -r s; do echo "{ \"returnValue\": true, \"state\": \"$s\" }"; done > "$STUB_TV/sub.power"
  echo "2026-11-14T15:29:37.3Z [1652.1] user.info tvpowerd [] tvpowerd NL_POWER_STATE $2" > "$W/tvlog"
  sh "$HOOK"
  wait_for '[ -s "$W/hook.pid" ]'
}
wake_run "Active
Suspend
Active" '{"old":"Suspend","new":"Active","PowerOnReason":"remoteKey"}'
yes "boot hook: a wake by the TV's remote opens Impetus" wait_for '[ "$(calls "\"id\":\"$US\"")" -ge 2 ]'
is "boot hook: once per wake" "$(calls "\"id\":\"$US\"")" 2
kill "$(cat "$W/hook.pid")" 2>/dev/null
wake_run "Active
Suspend
Active" '{"old":"Suspend","new":"Active","PowerOnReason":"hdmiCec"}'
sleep 1
is "boot hook: a wake by another device leaves it in front" "$(calls applicationmanager/launch)" 1
kill "$(cat "$W/hook.pid")" 2>/dev/null
wake_run "Active
Screen Off
Active" '{"old":"Screen Off","new":"Active"}'
sleep 1
is "boot hook: the screen coming back on is not a wake" "$(calls applicationmanager/launch)" 1
kill "$(cat "$W/hook.pid")" 2>/dev/null

# ---------- the phone remote (issue #21) ----------
# tests/stubs/httpd stands in for busybox httpd; the CGI door is run by hand
# the way httpd runs it: POST, CONTENT_LENGTH, the body on stdin.
reset
api() { # body lines...
  ap_b=$(printf '%s\n' "$@")
  printf '%s\n' "$ap_b" | REQUEST_METHOD=POST CONTENT_LENGTH=$((${#ap_b} + 1)) sh "$RUN/www/cgi-bin/api" | tr -d '\r' | sed '1,/^$/d'
}
kv() { echo "$1" | sed -n "s/^$2=//p" | head -n 1; }
is "phone: state says off when a server is here" "$(st phone)" off
is "phone: probe output has no phone line" "$(sh "$CTL" probe | grep -c '^phone')" 0
is "phone: start answers on the first port" "$(sh "$CTL" phone start | tr '\n' ' ')" "ok=1 port=8090 "
is "phone: state says on" "$(st phone)" on
is "phone: state names the port" "$(st phoneport)" 8090
is "phone: httpd serves the www copy with its conf" "$(cat "$STUB_TV/httpd.args")" "-f -p 8090 -h $RUN/www -c $RUN/phone-httpd.conf"
yes "phone: the www copy has the page" test -s "$RUN/www/index.html"
yes "phone: the www copy has logic.js and the font" test -s "$RUN/www/logic.js" -a -s "$RUN/www/fonts/Saira-Variable.woff2"
yes "phone: the CGI door is executable" test -x "$RUN/www/cgi-bin/api"
no "phone: the www copy holds no state" test -e "$RUN/www/state"
is "phone: httpd allows the home network only" "$(tail -n 2 "$RUN/phone-httpd.conf" | head -n 1)" "D:*"
yes "phone: the wish is kept for a restart" test -e "$KEEP/phone.on"
sp=$(cut -d' ' -f1 "$RUN/phone.server")
sh "$CTL" phone start >/dev/null
is "phone: a second start keeps the same server" "$(cut -d' ' -f1 "$RUN/phone.server")" "$sp"

is "phone cgi: GET is refused" "$(REQUEST_METHOD=GET sh "$RUN/www/cgi-bin/api" | tr -d '\r' | sed '1,/^$/d')" "error=method"
is "phone cgi: a body over 4096 bytes is refused" "$(REQUEST_METHOD=POST CONTENT_LENGTH=5000 sh "$RUN/www/cgi-bin/api" </dev/null | tr -d '\r' | sed '1,/^$/d')" "error=body"
is "phone cgi: shell text is refused" "$(api op=hello 't=$(reboot)')" "error=word"
is "phone cgi: an unknown key is refused" "$(api op=hello x=1)" "error=word"
is "phone cgi: an unknown op is refused" "$(api op=restore)" "error=op"
is "phone cgi: no token, not paired" "$(api op=hello)" "paired=0"
is "phone cgi: a made-up token, not paired" "$(api op=state t=0123456789abcdef0123456789abcdef)" "paired=0"
is "phone cgi: no token, no action" "$(api op=do w=scene w=off)" "paired=0"

: > "$STUB_TV/calls"
out=$(IMPETUS_NOW=1000 api op=pair)
is "pair: answers with the code's life" "$(echo "$out" | tr '\n' ' ')" "ok=1 life=120 "
code=$(cut -d' ' -f1 "$RUN/phone.code")
yes "pair: the code is six digits" sh -c "echo '$code' | grep -qx '[0-9][0-9][0-9][0-9][0-9][0-9]'"
is "pair: the code is shown on the TV" "$(grep -c "createToast.*Phone pairing code: ${code%???} ${code#???}" "$STUB_TV/calls")" 1
IMPETUS_NOW=1002 api op=pair >/dev/null
is "pair: asked again at once, no second toast" "$(calls createToast)" 1
IMPETUS_NOW=1010 api op=pair >/dev/null
is "pair: asked again later, the same code again" "$(cut -d' ' -f1 "$RUN/phone.code") $(calls createToast)" "$code 2"
wrong=$(echo "$code" | awk '{ printf "%06d", ($1 + 1) % 1000000 }')
is "confirm: a wrong code, four tries left" "$(IMPETUS_NOW=1020 api op=confirm code=$wrong | tr '\n' ' ')" "error=code left=4 "
is "confirm: letters are not a code" "$(IMPETUS_NOW=1020 api op=confirm code=12a45b)" "error=code"
out=$(IMPETUS_NOW=1030 api op=confirm code=$code n=iPhone)
tok=$(kv "$out" token); pid=$(kv "$out" id)
yes "confirm: a 32-hex token" sh -c "echo '$tok' | grep -qx '[0-9a-f]\{32\}'"
yes "confirm: a 6-hex id" sh -c "echo '$pid' | grep -qx '[0-9a-f]\{6\}'"
no "confirm: the code is used up" test -e "$RUN/phone.code"
is "confirm: the phones file is the owner's only" "$(ls -l "$KEEP/phones" | cut -c1-10)" "-rw-------"
is "confirm: the phone is listed with its name" "$(sh "$CTL" phone list)" "phone=$pid iPhone 1030"
is "confirm: paired toast" "$(calls 'Phone paired: iPhone')" 1
is "confirm: the same code twice does not pair again" "$(IMPETUS_NOW=1031 api op=confirm code=$code)" "error=expired"
IMPETUS_NOW=2000 api op=pair >/dev/null
is "confirm: an old code has expired" "$(IMPETUS_NOW=2200 api op=confirm code="$(cut -d' ' -f1 "$RUN/phone.code" 2>/dev/null || echo 000000)")" "error=expired"
IMPETUS_NOW=3000 api op=pair >/dev/null
c3=$(cut -d' ' -f1 "$RUN/phone.code"); w3=$(echo "$c3" | awk '{ printf "%06d", ($1 + 1) % 1000000 }')
for i in 1 2 3 4; do IMPETUS_NOW=3001 api op=confirm code=$w3 >/dev/null; done
is "confirm: the fifth wrong code drops the code" "$(IMPETUS_NOW=3001 api op=confirm code=$w3)" "error=expired"
is "confirm: and the right one is no good after it" "$(IMPETUS_NOW=3002 api op=confirm code=$c3)" "error=expired"
is "confirm: a name is cut to its safe letters" "$(IMPETUS_NOW=4000 api op=pair >/dev/null; IMPETUS_NOW=4001 api op=confirm code="$(cut -d' ' -f1 "$RUN/phone.code")" n=My.Phone:Pro >/dev/null; sh "$CTL" phone list | tail -n 1 | cut -d' ' -f2)" "MyPhonePro"

h=$(api op=hello t=$tok)
is "hello: paired, with the phone's id" "$(echo "$h" | head -n 2 | tr '\n' ' ')" "paired=1 id=$pid "
is "hello: caps and state sections" "$(echo "$h" | grep '^@' | tr '\n' ' ')" "@caps @state "
is "hello: the state says the phone server is on" "$(echo "$h" | sed -n 's/^phone=//p')" on
is "state: through the CGI door" "$(api op=state t=$tok | sed -n 's/^shield=//p')" off
is "apps: the TV's app list" "$(api op=apps t=$tok | grep -c returnValue)" 1
for v in "restore" "keeper" "phone stop" "phone revoke id=$pid" "start" "sleep cancel" "engine" "tick"; do
  # shellcheck disable=SC2086
  set -- $v; ws=; for x in "$@"; do ws="$ws w=$x"; done
  # shellcheck disable=SC2086
  is "do: a phone may not send '$v'" "$(api op=do t=$tok $ws)" "error=verb"
done
yes "do: the server still runs after the refusals" test -e "$RUN/phone.server"
: > "$STUB_TV/calls"
is "do: shield on" "$(api op=do t=$tok w=shield w=on)" "ok=1"
is "do: the shield is on" "$(st shield)" on
is "do: shield off" "$(api op=do t=$tok w=shield w=off)" "ok=1"
is "do: a word with shell text is refused before the helper" "$(api op=do t=$tok w=open 'w=id=x;reboot')" "error=word"
is "open: an app" "$(api op=do t=$tok w=open w=id=netflix)" "ok=1"
is "open: the launch call" "$(grep -c 'applicationmanager/launch {"id":"netflix"}' "$STUB_TV/calls")" 1
pj=$(printf '{"contentTarget":"x1"}' | base64 | tr -d '\n')
is "open: with deep-link params" "$(api op=do t=$tok w=open w=id=netflix w=params=$pj)" "ok=1"
is "open: the params reach the launch" "$(grep -c 'launch {"id":"netflix","params":{"contentTarget":"x1"}}' "$STUB_TV/calls")" 1
pb=$(printf 'not json' | base64 | tr -d '\n')
api op=do t=$tok w=open w=id=netflix w=params=$pb >/dev/null
is "open: params that are not an object are dropped" "$(tail -n 1 "$STUB_TV/calls")" 'luna://com.webos.service.applicationmanager/launch {"id":"netflix"}'
is "open: no id" "$(sh "$CTL" open)" "error=id"
: > "$STUB_TV/nolaunch"
is "open: the TV refuses" "$(api op=do t=$tok w=open w=id=netflix)" "error=refused"
rm -f "$STUB_TV/nolaunch"
: > "$STUB_TV/calls"
is "standby: answers" "$(api op=do t=$tok w=standby)" "ok=1"
is "standby: one power-off call" "$(calls 'power/turnOff {')" 1
: > "$STUB_TV/nopower"
is "standby: the TV refuses" "$(sh "$CTL" standby)" "error=refused"
rm -f "$STUB_TV/nopower"

eng=$(sh "$CTL" engine)
is "engine: the paired phones ride in the state part" "$(echo "$eng" | sed -n '/^@state/,/^@talk/p' | grep -c '^paired=')" 2
is "revoke: a bad id" "$(sh "$CTL" phone revoke id=xyz)" "error=id"
is "revoke: an unknown id" "$(sh "$CTL" phone revoke id=000000)" "error=unknown"
is "revoke: forgets the phone" "$(sh "$CTL" phone revoke id=$pid)" "ok=1"
is "revoke: its token no longer works" "$(api op=hello t=$tok)" "paired=0"
is "revoke: the other phone stays" "$(sh "$CTL" phone list | wc -l | tr -d ' ')" 1

# Eight phones at most.
i=0; while [ "$i" -lt 7 ]; do echo "a0000$i 0000000000000000000000000000000$i P$i 1" >> "$KEEP/phones"; i=$((i + 1)); done
is "pair: eight phones, no more" "$(api op=pair)" "error=full"

# The keeper brings the server back; restore and stop end it.
kill "$(cut -d' ' -f1 "$RUN/phone.server")" 2>/dev/null; sleep 0.2
IMPETUS_NOW=5000 sh "$CTL" tick >/dev/null
is "keeper: the server is back after it died" "$(st phone)" on
kill "$(cut -d' ' -f1 "$RUN/phone.server")" 2>/dev/null; sleep 0.2
IMPETUS_NOW=5010 sh "$CTL" tick >/dev/null
is "keeper: tries again once a minute at most" "$(st phone)" off
IMPETUS_NOW=5061 sh "$CTL" tick >/dev/null
is "keeper: and a minute later it is back" "$(st phone)" on
is "phone stop: answers" "$(sh "$CTL" phone stop)" "ok=1"
is "phone stop: off" "$(st phone)" off
no "phone stop: the wish is dropped" test -e "$KEEP/phone.on"
no "phone stop: the www copy is gone" test -e "$RUN/www"
yes "phone stop: paired phones stay" test -s "$KEEP/phones"
IMPETUS_NOW=6000 sh "$CTL" tick >/dev/null
is "phone stop: the keeper leaves it off" "$(st phone)" off
echo 8090 > "$STUB_TV/httpd.busy"
is "phone: a taken port, the next one" "$(sh "$CTL" phone start | tr '\n' ' ')" "ok=1 port=8091 "
sp=$(cut -d' ' -f1 "$RUN/phone.server")
sh "$CTL" restore >/dev/null
no "restore: the phone server ends" kill -0 "$sp" 2>/dev/null
no "restore: and is not wanted back" test -e "$KEEP/phone.on"
printf '8090\n8091\n8092\n8093\n' > "$STUB_TV/httpd.busy"
is "phone: every port taken" "$(sh "$CTL" phone start)" "error=noport"
is "phone: an unknown phone word" "$(sh "$CTL" phone maybe)" "error=phone"
is "phone helper: an unknown mode" "$(sh "$HERE/../app/bin/impetus-phone" bogus)" "error=mode"

echo "$n checks, $failed failed"
[ "$failed" = 0 ]

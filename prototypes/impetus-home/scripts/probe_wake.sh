#!/bin/sh
# probe_wake.sh: can root wake this TV from sleep at a set time (issue #25)?
# Reads only: it calls no power method other than getPowerState, sets no
# timer, writes no file and changes no setting. Run it as root on the TV
# (Homebrew Channel shell or ssh). Read the output before pasting any of it
# anywhere public: the settings and log parts are the TV's own words.
#
#   sh probe_wake.sh                 everything below
#   sh probe_wake.sh clock           one line: wall clock, uptime, suspends
#   sh probe_wake.sh clock <line>    the same, compared with an earlier line
#
# The sleep test (does anything run while the TV sleeps?):
#   1. sh probe_wake.sh clock        note the line
#   2. put the TV to sleep with the remote's power button, wait 3 minutes,
#      wake it with the remote
#   3. sh probe_wake.sh clock "<the line from 1>"
#   ran=yes: uptime kept pace with the clock, the system ran through the
#   sleep and the keeper can act at the set time (a screen-on call may be
#   all a wake needs). ran=no: the system was suspended; only a timer the TV
#   itself keeps (an On Timer, an RTC or micom alarm) can wake it, and
#   without one the morning view comes at the first power-on.
#
# Answers, as key=value lines in sections:
#   @power     the power state now
#   @methods   what tvpower and its neighbours say they offer (ls-monitor
#              introspection), and method names in the bus permission files
#   @services  bus services whose names speak of alarm, timer, wake or sleep
#   @settings  the TV's time settings (an On Timer lives here, if anywhere)
#   @rtc       the kernel's real-time clock and its wake alarm, suspend counts
#   @tools     programs on the TV whose names speak of micom, rtc or wake
#   @log       the last power-state lines of the TV's log (why it woke)

PWR=luna://com.webos.service.tvpower/power
SET=luna://com.webos.settingsservice
LOG=/var/log/messages
WAITS=8

say() { echo "$1=$2"; }
have() { command -v "$1" >/dev/null 2>&1; }

# One call that may hang, given up after $WAITS seconds.
capped() {
  if have timeout; then timeout "$WAITS" "$@" 2>/dev/null </dev/null
  else "$@" 2>/dev/null </dev/null & cp_p=$!; ( sleep "$WAITS"; kill "$cp_p" 2>/dev/null ) & cp_w=$!
    wait "$cp_p"; kill "$cp_w" 2>/dev/null
  fi
}

suspends() { cat /sys/power/suspend_stats/success 2>/dev/null || echo unknown; }
uptime_s() { cut -d. -f1 /proc/uptime 2>/dev/null; }

clock() {
  c_wall=$(date +%s); c_up=$(uptime_s); c_sus=$(suspends)
  echo "wall=$c_wall uptime=$c_up suspends=$c_sus"
  [ -n "$1" ] || return 0
  p_wall=$(echo "$1" | sed -n 's/.*wall=\([0-9]*\).*/\1/p')
  p_up=$(echo "$1" | sed -n 's/.*uptime=\([0-9]*\).*/\1/p')
  p_sus=$(echo "$1" | sed -n 's/.*suspends=\([0-9a-z]*\).*/\1/p')
  if [ -z "$p_wall" ] || [ -z "$p_up" ] || [ -z "$c_up" ]; then say verdict "the earlier line does not read"; return 1; fi
  d_wall=$((c_wall - p_wall)); d_up=$((c_up - p_up))
  say clock.passed "$d_wall"; say uptime.passed "$d_up"
  [ "$p_sus" != "$c_sus" ] && say suspends.changed "$p_sus->$c_sus"
  # Uptime stops while the kernel is suspended; 20 s of slack for the wake.
  if [ "$d_up" -ge $((d_wall - 20)) ]; then say ran yes; else say ran no; fi
}

if [ "$1" = clock ]; then shift; clock "$1"; exit $?; fi

echo "@shell"
say user "$(id -u 2>/dev/null)"
say date "$(date '+%Y-%m-%d %H:%M %Z')"
say tz "${TZ:-unset}"
say date.at "$(date -d @0 +%Y 2>/dev/null || echo no)"   # 1970: busybox date reads @epoch (the keeper needs it)

echo "@power"
say getPowerState "$(capped luna-send -n 1 "$PWR/getPowerState" '{}' | tr -d '\n' | cut -c1-300)"

echo "@methods"
for s in com.webos.service.tvpower com.webos.service.alarm com.palm.sleep com.webos.service.sleep \
         com.webos.service.micom com.webos.service.timer com.webos.service.tv.time; do
  out=$(capped ls-monitor -i "$s" | tr -s ' \t' ' ' | grep -v '^ *$' | head -n 60)
  if [ -n "$out" ]; then echo "$out" | sed "s|^|$s: |"; else say "introspect.$s" none; fi
done
for d in /usr/share/luna-service2/api-permissions.d /usr/share/luna-service2/client-permissions.d \
         /usr/share/luna-service2/roles.d /usr/share/luna-service2/services.d; do
  [ -d "$d" ] || { say "dir.$d" missing; continue; }
  grep -ho '"[A-Za-z0-9._/-]*\(tvpower\|alarm\|[Ww]ake\|[Tt]imer\|sleep\)[A-Za-z0-9._/-]*"' "$d"/* 2>/dev/null |
    sort -u | head -n 80 | sed "s|^|$(basename "$d"): |"
done

echo "@services"
for d in /usr/share/luna-service2/services.d /usr/share/dbus-1/system-services /usr/share/dbus-1/services; do
  [ -d "$d" ] || continue
  ls "$d" 2>/dev/null | grep -i 'alarm\|timer\|wake\|sleep\|power\|micom\|rtc' | sed "s|^|$d: |"
done

echo "@settings"
for c in time timer option; do
  say "settings.$c" "$(capped luna-send -n 1 "$SET/getSystemSettings" "{\"category\":\"$c\"}" | tr -d '\n' | cut -c1-1500)"
done
say settings.onTimer "$(capped luna-send -n 1 "$SET/getSystemSettings" '{"category":"time","keys":["onTimerEnable","onTimer","onTimerSchedule","powerOnTimer"]}' | tr -d '\n' | cut -c1-600)"

echo "@rtc"
for r in /sys/class/rtc/rtc*; do
  [ -e "$r" ] || { say rtc none; break; }
  say "$(basename "$r").name" "$(cat "$r/name" 2>/dev/null)"
  if [ -e "$r/wakealarm" ]; then say "$(basename "$r").wakealarm" "present:$(cat "$r/wakealarm" 2>/dev/null)"
    ls -l "$r/wakealarm" 2>/dev/null | awk '{print "'"$(basename "$r")"'.wakealarm.mode=" $1}'
  else say "$(basename "$r").wakealarm" missing; fi
done
grep -i 'alarm\|alrm' /proc/driver/rtc 2>/dev/null | sed 's/^/proc.rtc: /'
say power.state "$(cat /sys/power/state 2>/dev/null)"
say power.mem_sleep "$(cat /sys/power/mem_sleep 2>/dev/null)"
say suspends "$(suspends)"
say wakeup_sources "$(wc -l < /sys/kernel/debug/wakeup_sources 2>/dev/null || echo unreadable)"
clock

echo "@tools"
for d in /usr/bin /usr/sbin /bin /sbin /usr/lib/webos-service /usr/palm/services; do
  [ -d "$d" ] && ls "$d" 2>/dev/null | grep -i 'micom\|rtc\|wake\|alarm\|power\|timer' | sed "s|^|$d: |"
done
ls /dev 2>/dev/null | grep -i 'micom\|rtc\|mcu' | sed 's|^|/dev: |'

echo "@log"
grep -h 'NL_POWER_STATE\|PowerOnReason\|wakeup' "$LOG" 2>/dev/null | tail -n 12 | cut -c1-240

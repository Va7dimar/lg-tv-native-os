#!/bin/sh
# probe_sound.sh: can root read the sound the TV is playing? (#22)
#
# The answer decides how the music piece moves: on the beat (a sound tap) or
# from the cover's colours and the track's progress (no tap). Run it at the TV
# as root, with music playing (Spotify, or anything with sound):
#
#   sh probe_sound.sh          look only: devices, sound servers, tools, services
#   sh probe_sound.sh try      also listen 2 s on each place found, and say
#                              whether real sound (not silence) came out
#
# Reads only. It changes no setting, loads nothing, starts no server. `try`
# reads sound for 2 s per source into a scratch folder under /tmp that is
# removed at the end. The output names devices and programs only (no serial,
# address or account): safe to paste into an issue after a look.
#
# busybox ash and dash both run this file.

umask 077
TRY=0
[ "$1" = try ] && TRY=1
SECS=2
W=$(mktemp -d /tmp/probe-sound.XXXXXX 2>/dev/null) || W=/tmp/probe-sound.$$
mkdir -p "$W"
trap 'rm -rf "$W"' EXIT INT TERM

has() { command -v "$1" >/dev/null 2>&1; }
yn() { if "$@"; then echo 1; else echo 0; fi; }

# The command's output for $1 seconds, then it is stopped. The stopper writes
# nowhere, so a reader of the output never waits on it.
take() {
  tk_s=$1; shift
  "$@" 2>/dev/null </dev/null &
  tk_p=$!
  ( sleep "$tk_s"; kill "$tk_p" 2>/dev/null ) >/dev/null 2>&1 </dev/null &
  wait "$tk_p" 2>/dev/null
}

# One capture: bytes read and bytes that are not zero (silence is all zero).
# -> "bytes=<n> sound=<n>"
listen() { # name, then the command
  li_n=$1; shift
  # At most 2 MB kept: about 10 s of CD sound, never a full /tmp.
  take "$SECS" "$@" 2>/dev/null | head -c 2000000 > "$W/cap"
  li_b=$(wc -c < "$W/cap" | tr -d ' ')
  li_z=$(tr -d '\000' < "$W/cap" | wc -c | tr -d ' ')
  rm -f "$W/cap"
  echo "try.$li_n=bytes=$li_b sound=$li_z"
  [ "${li_z:-0}" -gt 1000 ] && FOUND="$FOUND $li_n"
}

FOUND=
echo "@about"
echo "probe=sound 1"
echo "user=$(id -u 2>/dev/null)"
echo "kernel=$(uname -r 2>/dev/null)"
[ -r /etc/os-release ] && sed -n -e 's/^PRETTY_NAME=/os.name=/p' -e 's/^VERSION_ID=/os.version=/p' /etc/os-release

# ---------- ALSA: the kernel's sound devices ----------
echo "@alsa"
echo "asound=$(yn test -d /proc/asound)"
if [ -r /proc/asound/cards ]; then sed 's/^/cards: /' /proc/asound/cards; fi
if [ -r /proc/asound/pcm ]; then
  sed 's/^/pcm: /' /proc/asound/pcm
  echo "pcm.capture=$(grep -c capture /proc/asound/pcm)"
fi
ls -l /dev/snd 2>/dev/null | sed 's/^/dev.snd: /'
echo "dev.snd.capture=$(ls /dev/snd 2>/dev/null | grep -c '^pcmC[0-9]*D[0-9]*c$')"
# Loopback devices copy what plays into a capture device.
grep -il loopback /proc/asound/cards >/dev/null 2>&1 && echo "loopback=1" || echo "loopback=0"
ls /dev 2>/dev/null | grep -i -E '^(audio|dsp|adec|aenc|lg.*(aud|snd)|mixer)' | sed 's/^/dev.other: /'
grep -i -E '^(snd|.*audio|.*sound|.*adec)' /proc/modules 2>/dev/null | cut -d' ' -f1 | sed 's/^/module: /'

# ---------- sound servers ----------
echo "@servers"
ps 2>/dev/null | grep -i -E 'pulse|pipewire|audiod|adec|alsa|sound|wireplumber|mediaserver|umediaserver|gst' |
  grep -v -E 'grep|probe_sound' | awk '{ $1=""; print "proc:" $0 }' | cut -c1-160
for d in /tmp /run /var/run /run/user /home/root /var/lib; do
  find "$d" -maxdepth 4 \( -name native -o -name 'pulse*' -o -name 'pipewire-*' \) 2>/dev/null
done | sort -u | sed 's/^/socket: /'
for f in /etc/pulse/default.pa /etc/pulse/system.pa /etc/pulse/client.conf /etc/asound.conf /usr/share/alsa/alsa.conf; do
  [ -r "$f" ] && echo "conf: $f"
done
[ -r /etc/pulse/system.pa ] && grep -n -E 'module-(native|loopback|null-sink|remap|combine)' /etc/pulse/system.pa | sed 's/^/system.pa: /'
[ -r /etc/pulse/default.pa ] && grep -n -E 'module-(native|loopback|null-sink|remap|combine)' /etc/pulse/default.pa | sed 's/^/default.pa: /'

# ---------- tools that could read sound ----------
echo "@tools"
for t in pactl pacmd parec parecord pw-cat pw-record arecord amixer ffmpeg gst-launch-1.0 gst-inspect-1.0 node; do
  echo "tool.$t=$(yn has "$t")"
done
if has gst-inspect-1.0; then
  for e in pulsesrc alsasrc autoaudiosrc; do echo "gst.$e=$(yn gst-inspect-1.0 "$e" >/dev/null 2>&1)"; done
fi
has arecord && arecord -l 2>/dev/null | sed 's/^/arecord: /'

# ---------- PulseAudio: sources, the monitors among them ----------
echo "@pulse"
SERVERS=
for s in $(find /tmp /run /var/run -maxdepth 4 -name native 2>/dev/null | sort -u); do SERVERS="$SERVERS unix:$s"; done
[ -n "$PULSE_SERVER" ] && SERVERS="$PULSE_SERVER $SERVERS"
echo "servers=$(echo $SERVERS)"
MONITORS=
if has pactl; then
  for s in "" $SERVERS; do
    if [ -n "$s" ]; then o=$(take 3 env PULSE_SERVER="$s" pactl list short sources); else o=$(take 3 pactl list short sources); fi
    [ -n "$o" ] || continue
    echo "$o" | sed "s|^|source[${s:-default}]: |"
    for m in $(echo "$o" | awk '{print $2}' | grep '\.monitor$'); do MONITORS="$MONITORS $s|$m"; done
    if [ -n "$s" ]; then o=$(take 3 env PULSE_SERVER="$s" pactl list short sinks); else o=$(take 3 pactl list short sinks); fi
    echo "$o" | grep . | sed "s|^|sink[${s:-default}]: |"
  done
fi
echo "monitors=$(echo $MONITORS | wc -w | tr -d ' ')"

# ---------- webOS services that touch sound ----------
echo "@services"
for d in /usr/share/luna-service2/services.d /usr/share/dbus-1/system-services /usr/share/luna-service2/roles.d; do
  ls "$d" 2>/dev/null | grep -i -E 'audio|sound|pulse|adec|media' | sed "s|^|$d: |"
done
if has ls-monitor; then
  take 3 ls-monitor -i com.webos.service.audio 2>/dev/null | grep -i -E 'capture|record|monitor|level|spectrum|loopback|input' |
    head -n 40 | sed 's/^/audio.method: /'
fi

# ---------- try: listen 2 s on each candidate ----------
if [ "$TRY" = 1 ]; then
  echo "@try"
  echo "note=play music now; silence reads as sound=0"
  if has parec; then
    for sm in $MONITORS; do
      s=${sm%%|*}; m=${sm#*|}
      if [ -n "$s" ]; then listen "parec.$m" env PULSE_SERVER="$s" parec -d "$m" --raw --format=s16le --rate=44100 --channels=2
      else listen "parec.$m" parec -d "$m" --raw --format=s16le --rate=44100 --channels=2; fi
    done
  fi
  if has arecord; then
    for c in $(ls /dev/snd 2>/dev/null | sed -n 's/^pcmC\([0-9]*\)D\([0-9]*\)c$/\1,\2/p'); do
      listen "arecord.hw$c" arecord -q -D "hw:$c" -f S16_LE -r 48000 -c 2 -t raw
    done
  elif [ -r /dev/snd/pcmC0D0c ]; then
    echo "try.alsa=no arecord: a capture device exists but there is no tool here to read it"
  fi
  if has gst-launch-1.0; then
    listen "gst.pulsesrc" gst-launch-1.0 -q pulsesrc ! audioconvert ! audio/x-raw,format=S16LE ! fdsink fd=1
    listen "gst.alsasrc" gst-launch-1.0 -q alsasrc ! audioconvert ! audio/x-raw,format=S16LE ! fdsink fd=1
  fi
fi

# ---------- the answer ----------
echo "@verdict"
if [ "$TRY" = 1 ]; then
  if [ -n "$FOUND" ]; then echo "tap=yes"; echo "tap.where=$(echo $FOUND)"
  else echo "tap=no"; echo "tap.why=no source gave sound in $SECS s (was music playing?)"; fi
else
  echo "tap=unknown"
  echo "next=sh probe_sound.sh try   (with music playing)"
fi
